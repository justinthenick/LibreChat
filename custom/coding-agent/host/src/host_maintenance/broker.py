from __future__ import annotations

import hashlib
import math
import json
import re
import secrets
import threading
import time
from pathlib import Path

from coding_executor.bounded import run
from coding_executor.coordination import maintenance_lock


LOCK_DESTINATION = "/run/coding-agent/maintenance.lock"
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}")


class Broker:
    def __init__(self, config: dict, *, runner=run):
        self.config = config
        self.runner = runner
        self.container = config["container"]
        if not NAME.fullmatch(self.container):
            raise ValueError("invalid configured container")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", config["image_id"]):
            raise ValueError("pin the validated executor image ID")
        self.tasks = Path(config["task_root"])
        self.repositories = Path(config["repository_root"])
        self.lock = Path(config["lock_path"])
        for path in (self.tasks, self.repositories, self.lock):
            if not path.is_absolute() or path.is_symlink() or path.resolve() != path:
                raise ValueError("use canonical absolute host paths")
        if self.tasks == self.repositories or self.tasks in self.repositories.parents or self.repositories in self.tasks.parents:
            raise ValueError("repository and task roots must be disjoint")
        if any(root == self.lock or root in self.lock.parents for root in (self.tasks, self.repositories)):
            raise ValueError("lock must live outside executor-writable mounts")
        for name, policy in config["repositories"].items():
            if not NAME.fullmatch(name):
                raise ValueError("invalid repository alias")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,150}", policy["branch"]) or ".." in policy["branch"]:
                raise ValueError("invalid configured branch")
            if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", policy["url"]):
                raise ValueError("invalid configured repository URL")
        self._mutex = threading.Lock()
        self._helper_mutex = threading.Lock()
        self._tickets: dict[str, tuple[float, str, str, str]] = {}
        self._last_restart = float("-inf")

    def _docker(self, *args: str, timeout: int = 60) -> str:
        return self.runner(["/usr/bin/docker", *args], timeout=timeout, limit=65536)

    def _inspect(self) -> dict:
        data = json.loads(self._docker("inspect", "--type", "container", self.container, timeout=5))[0]
        if data["Image"] != self.config["image_id"]:
            raise RuntimeError("executor image differs from validated image")
        host = data["HostConfig"]
        if not host["ReadonlyRootfs"] or host["Privileged"] or "ALL" not in host.get("CapDrop", []):
            raise RuntimeError("executor isolation requirements are not satisfied")
        if data["Config"]["User"].split(":")[0] in ("", "root", "0"):
            raise RuntimeError("executor must run as non-root")
        if host.get("CapAdd") or host.get("Devices") or any(host.get(key) == "host" for key in ("PidMode", "IpcMode", "NetworkMode")):
            raise RuntimeError("executor must not have added host privileges")
        if not any(value in {"no-new-privileges", "no-new-privileges:true", "no-new-privileges=true"} for value in host.get("SecurityOpt", [])):
            raise RuntimeError("executor requires no-new-privileges")
        if data["Config"].get("Cmd") != ["python3", "-m", "coding_executor.server"] or data["Config"].get("Entrypoint") not in (None, [], ["docker-entrypoint.sh"]):
            raise RuntimeError("executor entry point differs from reviewed service")
        expected = {
            str(self.tasks): (str(self.tasks), True),
            str(self.repositories): (str(self.repositories), True),
            LOCK_DESTINATION: (str(self.lock), False),
        }
        mounts = {item["Destination"]: (item["Source"], item["RW"])
                  for item in data["Mounts"] if item["Type"] != "tmpfs"}
        if mounts != expected:
            raise RuntimeError("executor mounts differ from reviewed repository/task/lock mounts")
        environment = dict(item.split("=", 1) for item in data["Config"].get("Env", []) if "=" in item)
        if (environment.get("CODING_MAINTENANCE_LOCK") != LOCK_DESTINATION
                or environment.get("CODING_REPOSITORY_ROOT") != str(self.repositories)
                or environment.get("CODING_TASK_ROOT") != str(self.tasks)):
            raise RuntimeError("executor maintenance paths differ from host configuration")
        return data

    def _helper(self, operation: str, *args: str) -> dict:
        # MCP dispatches tools concurrently. Queue once before starting a helper;
        # never replay a command after failure or wait on an active coding task.
        if not self._helper_mutex.acquire(timeout=15):
            raise RuntimeError("maintenance_queue_full: no operation started")
        try:
            return self._run_helper(operation, *args)
        finally:
            self._helper_mutex.release()

    def _run_helper(self, operation: str, *args: str) -> dict:
        container = self._inspect()
        if not container["State"]["Running"]:
            raise RuntimeError("executor is not running")
        output = self._docker("exec", container["Id"], "python3", "-I", "-B", "-m",
                              "coding_executor.maintenance", operation, *args, timeout=180)
        return json.loads(output)

    def _repository(self, repository: str) -> dict:
        if repository not in self.config["repositories"]:
            raise ValueError("repository is not allowlisted")
        return self.config["repositories"][repository]

    def _enabled(self, operation: str) -> None:
        if self.config.get("enabled_mutations", {}).get(operation) is not True:
            raise ValueError(f"{operation} is disabled by operator policy")

    def health(self) -> dict:
        data = self._inspect()
        state = data["State"]
        return {"container_id": data["Id"], "image_id": data["Image"], "status": state["Status"],
                "started_at": state["StartedAt"], "health": state.get("Health", {}).get("Status", "unconfigured"),
                "version": self._helper("health")["version"] if state["Running"] else None}

    def repository_status(self, repository: str) -> dict:
        policy = self._repository(repository)
        return self._helper("status", "--repository", repository, "--branch", policy["branch"])

    def refresh_repository(self, repository: str) -> dict:
        self._enabled("refresh")
        policy = self._repository(repository)
        return self._helper("refresh", "--repository", repository, "--branch", policy["branch"], "--url", policy["url"])

    def fresh_repository_status(self, repository: str) -> dict:
        policy = self._repository(repository)
        return self._helper("fresh-status", "--repository", repository, "--branch", policy["branch"], "--url", policy["url"])

    def task_inventory(self) -> dict:
        return self._helper("inventory")

    def _retired(self, task_id: str) -> dict:
        if not NAME.fullmatch(task_id):
            raise ValueError("invalid task identifier")
        record = self.config.get("retired_tasks", {}).get(task_id)
        if not isinstance(record, dict):
            raise ValueError("task requires an operator retirement record bound to its identity")
        retired_at = record.get("retired_at")
        minimum = self.config.get("minimum_retirement_age_seconds", 86400)
        if type(minimum) is not int or not 0 <= minimum <= 31536000:
            raise ValueError("invalid retirement age policy")
        if isinstance(retired_at, bool) or not isinstance(retired_at, (int, float)) or not math.isfinite(retired_at):
            raise ValueError("invalid retirement time")
        if not 0 < retired_at <= time.time() - minimum:
            raise ValueError("task has not reached the required retirement age")
        if (record.get("branch") != f"agent/{task_id}"
                or not re.fullmatch(r"[0-9a-f]{40,64}", str(record.get("head", "")))
                or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("fingerprint", "")))
                or record.get("repository") not in self.config["repositories"]):
            raise ValueError("invalid retirement identity")
        return record

    def _ticket(self, operation: str, subject: str, fingerprint: str) -> dict:
        with self._mutex:
            now = time.monotonic()
            self._tickets = {key: value for key, value in self._tickets.items() if value[0] > now}
            if len(self._tickets) >= 100:
                raise RuntimeError("too many pending previews")
            ticket = secrets.token_urlsafe(32)
            self._tickets[ticket] = (now + 60, operation, subject, fingerprint)
        return {"ticket": ticket, "expires_in_seconds": 60, "operation": operation, "subject": subject}

    def _consume(self, ticket: str, operation: str) -> tuple[str, str]:
        with self._mutex:
            pending = self._tickets.pop(ticket, None)
        if not pending or pending[0] <= time.monotonic() or pending[1] != operation:
            raise ValueError("invalid, expired or already used preview ticket")
        return pending[2], pending[3]

    def preview_cleanup(self, task_id: str) -> dict:
        self._enabled("cleanup")
        retirement = self._retired(task_id)
        snapshot = self._helper("preview", "--task", task_id)
        if snapshot["dirty"]:
            raise ValueError("task contains tracked, untracked or ignored changes")
        if any(snapshot.get(key) != retirement[key] for key in ("repository", "branch", "head", "fingerprint")):
            raise ValueError("task identity changed since operator retirement")
        required = {"tracked_clean", "index_clean", "no_untracked", "no_ignored", "no_hidden_index_flags",
                    "expected_identity", "registered_nonbroken", "no_git_locks", "no_git_operation"}
        checks = snapshot.get("checks", {})
        if snapshot.get("exclusive_gate_verified") is not True or any(checks.get(key) is not True for key in required):
            raise ValueError("cleanup eligibility was not proven")
        return {"eligible": True, "retirement": retirement, "snapshot": snapshot,
                "confirmation_task_id": task_id, **self._ticket("cleanup", task_id, snapshot["fingerprint"])}

    def cleanup_task(self, ticket: str, confirm_task_id: str) -> dict:
        self._enabled("cleanup")
        task_id, fingerprint = self._consume(ticket, "cleanup")
        if confirm_task_id != task_id:
            raise ValueError("confirmation must match the exact previewed task")
        if self._retired(task_id)["fingerprint"] != fingerprint:
            raise ValueError("retirement changed since preview")
        return self._helper("remove", "--task", task_id, "--fingerprint", fingerprint)

    @staticmethod
    def _identity(health: dict) -> str:
        return hashlib.sha256(json.dumps(health, sort_keys=True).encode()).hexdigest()

    def preview_restart(self) -> dict:
        health = self.health()
        return {"health": health, **self._ticket("restart", health["container_id"], self._identity(health))}

    def restart_executor(self, ticket: str) -> dict:
        self._enabled("restart")
        container_id, fingerprint = self._consume(ticket, "restart")
        with maintenance_lock(self.tasks, exclusive=True, lock_path=self.lock):
            with self._mutex:
                if time.monotonic() - self._last_restart < 300:
                    raise ValueError("restart cooldown is five minutes")
                before = self.health()
                if before["container_id"] != container_id or self._identity(before) != fingerprint:
                    raise ValueError("executor changed since preview")
                self._last_restart = time.monotonic()
            self._docker("restart", "--time", "10", container_id, timeout=30)
            for _ in range(20):
                result = self.health()
                if result["status"] == "running" and result["health"] == "healthy":
                    return {"restarted": True, **result}
                time.sleep(1)
            raise RuntimeError("restart requested but executor did not become healthy; operator action required")

    def logs(self) -> dict:
        container = self._inspect()
        raw = self._docker("logs", "--tail", "100", "--since", "10m", container["Id"])
        # Export event categories only. Raw request paths, tokens and exception text stay on host.
        events = []
        for line in raw.splitlines():
            if re.fullmatch(r"INFO:\s+(Application startup complete\.|Application shutdown complete\.|Waiting for application startup\.|Waiting for application shutdown\.|Shutting down)", line):
                events.append(line.strip())
            elif line.startswith("ERROR:"):
                events.append("ERROR: details available to operator on host")
            else:
                events.append("log content suppressed")
        return {"window": "last 10 minutes, at most 100 lines", "events": events[-100:], "raw_logs_exposed": False}
