from __future__ import annotations

import hashlib
import fcntl
import stat
from contextlib import contextmanager
import math
import json
import os
import re
import secrets
import threading
import time
from pathlib import Path

from coding_executor.bounded import run
from coding_executor.coordination import maintenance_lock


LOCK_DESTINATION = "/run/coding-agent/maintenance.lock"
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}")
DEFAULT_DOCKER_OUTPUT_LIMIT = 65536
VALIDATION_DOCKER_OUTPUT_LIMIT = 64 * 1024 * 1024
VALIDATION_PATH_PREVIEW_LIMIT = 100


def _is_wsl_environment() -> bool:
    if os.environ.get("WSL_DISTRO_NAME") or os.environ.get("WSL_INTEROP"):
        return True

    for path in (Path("/proc/sys/kernel/osrelease"), Path("/proc/version")):
        try:
            if "microsoft" in path.read_text(encoding="utf-8").lower():
                return True
        except OSError:
            continue

    return False


class Broker:
    def __init__(self, config: dict, *, runner=run):
        self.config = config
        self.runner = runner
        self.container = config["container"]
        if not NAME.fullmatch(self.container):
            raise ValueError("invalid configured container")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", config["image_id"]):
            raise ValueError("pin the validated executor image ID")
        self.acp_image_id = config.get("acp_image_id", "")
        if self.acp_image_id and not re.fullmatch(
            r"sha256:[0-9a-f]{64}",
            self.acp_image_id,
        ):
            raise ValueError("pin the validated ACP sandbox image ID")
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
        self._acp_mutex = threading.Lock()
        self._tickets: dict[str, tuple[float, str, str, str]] = {}
        self._last_restart = float("-inf")

    def _docker(self, *args: str, timeout: int = 60, limit: int = DEFAULT_DOCKER_OUTPUT_LIMIT) -> str:
        return self.runner(["/usr/bin/docker", *args], timeout=timeout, limit=limit)

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

    def _helper(self, operation: str, *args: str, output_limit: int = DEFAULT_DOCKER_OUTPUT_LIMIT) -> dict:
        # MCP dispatches tools concurrently. Queue once before starting a helper;
        # never replay a command after failure or wait on an active coding task.
        if not self._helper_mutex.acquire(timeout=15):
            raise RuntimeError("maintenance_queue_full: no operation started")
        try:
            return self._run_helper(operation, *args, output_limit=output_limit)
        finally:
            self._helper_mutex.release()

    def _run_helper(self, operation: str, *args: str, output_limit: int = DEFAULT_DOCKER_OUTPUT_LIMIT) -> dict:
        container = self._inspect()
        if not container["State"]["Running"]:
            raise RuntimeError("executor is not running")
        output = self._docker("exec", container["Id"], "python3", "-I", "-B", "-m",
                              "coding_executor.maintenance", operation, *args, timeout=180,
                              limit=output_limit)
        return json.loads(output)

    def _repository(self, repository: str) -> dict:
        if repository not in self.config["repositories"]:
            raise ValueError("repository is not allowlisted")
        return self.config["repositories"][repository]

    def _enabled(self, operation: str) -> None:
        if self.config.get("enabled_mutations", {}).get(operation) is not True:
            raise ValueError(f"{operation} is disabled by operator policy")

    def host_integrations(self) -> dict[str, str]:
        try:
            self._docker(
                "info",
                "--format",
                "{{.ServerVersion}}",
                timeout=5,
                limit=1024,
            )
            docker = "available"
        except Exception:
            docker = "unavailable"

        return {
            "docker": docker,
            "wsl": "available" if _is_wsl_environment() else "not_detected",
        }

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

    def task_identity(self, task_id: str) -> dict:
        """Return executor-validated identity for one managed task."""
        if not NAME.fullmatch(task_id):
            raise ValueError("invalid task identifier")

        result = self._helper(
            "task-identity",
            "--task",
            task_id,
        )

        if result.get("task_id") != task_id:
            raise RuntimeError("task identity mismatch")

        repository = result.get("repository")
        if repository not in self.config["repositories"]:
            raise RuntimeError("task repository is not allowlisted")

        if result.get("branch") != f"agent/{task_id}":
            raise RuntimeError("task branch identity mismatch")

        fingerprint = result.get("fingerprint")
        if not isinstance(fingerprint, str) or not re.fullmatch(
            r"[0-9a-f]{64}",
            fingerprint,
        ):
            raise RuntimeError("task fingerprint is invalid")

        if result.get("exclusive_gate_verified") is not True:
            raise RuntimeError("task identity gate evidence is missing")

        checks = result.get("checks")
        if not isinstance(checks, dict):
            raise RuntimeError("task identity checks are missing")

        required_checks = (
            "expected_identity",
            "registered_nonbroken",
            "no_git_locks",
            "no_git_operation",
        )
        if any(checks.get(name) is not True for name in required_checks):
            raise RuntimeError("task identity checks failed")

        return result

    def _authorize_acp_task(self, task_id: str, path: Path) -> bool:
        """Authorize only the exact host path backed by a managed task."""
        try:
            if not NAME.fullmatch(task_id):
                return False

            expected = self.tasks / task_id

            if (
                path != expected
                or path.is_symlink()
                or not path.is_dir()
                or path.resolve() != expected
            ):
                return False

            identity = self.task_identity(task_id)

            return (
                identity["task_id"] == task_id
                and identity["repository"] in self.config["repositories"]
                and identity["branch"] == f"agent/{task_id}"
            )
        except (OSError, RuntimeError, ValueError):
            return False

    def _acp_manager(self):
        """Construct the fixed-policy ACP sandbox manager internally."""
        if not self.acp_image_id:
            raise ValueError("ACP sandbox image is not configured")

        from host_maintenance.acp_sandbox import AcpSandboxManager

        def docker_runner(argv, **_kwargs):
            if (
                not isinstance(argv, (list, tuple))
                or not argv
                or argv[0] != "/usr/bin/docker"
            ):
                raise ValueError("ACP sandbox runner accepts only Docker")

            return self._docker(*argv[1:])

        return AcpSandboxManager(
            task_root=self.tasks,
            image=self.acp_image_id,
            runner=docker_runner,
            task_authorizer=self._authorize_acp_task,
        )

    @contextmanager
    def _acp_operation(self, task_id: str):
        if not NAME.fullmatch(task_id):
            raise ValueError("invalid task identifier")
        if not self._acp_mutex.acquire(timeout=15):
            raise RuntimeError("acp_sandbox_queue_full: no operation started")
        descriptor = None
        try:
            lock_path = self.lock.with_name(f"acp-{task_id}.lock")
            descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            info = os.fstat(descriptor)
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600):
                raise RuntimeError("invalid ACP session lock")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError("ACP task already has an active operation") from exc
            yield
        finally:
            if descriptor is not None:
                os.close(descriptor)
            self._acp_mutex.release()

    def acp_sandbox_stream(self, task_id: str, stdin, stdout, stderr) -> int:
        """Own one disposable ACP session; accept no container or command selector."""
        from host_maintenance.acp_stream import attach, cleanup_signals

        with self._acp_operation(task_id):
            manager = self._acp_manager()
            workspace = manager.task_path(task_id)
            identity = workspace.stat()
            container_id = manager.create(task_id)
            info = manager.inspect(task_id)
            if (info.get("Id") != container_id
                    or info.get("State", {}).get("Status") != "created"
                    or info.get("State", {}).get("Running") is not False):
                raise RuntimeError("new ACP sandbox failed validation; left for operator inspection")
            try:
                manager.start(task_id)
                info = manager.inspect(task_id)
                if info.get("Id") != container_id:
                    raise RuntimeError("ACP container identity changed before attach")
                with maintenance_lock(self.tasks, lock_path=self.lock):
                    current = workspace.lstat()
                    if (not stat.S_ISDIR(current.st_mode)
                            or (current.st_dev, current.st_ino) != (identity.st_dev, identity.st_ino)):
                        raise RuntimeError("ACP task identity changed before attach")
                    return attach(info, self.acp_image_id, stdin, stdout, stderr, workspace=workspace)
            finally:
                with cleanup_signals():
                    info = manager.inspect(task_id)
                    if info.get("Id") != container_id:
                        raise RuntimeError("ACP container identity changed; cleanup refused")
                    manager.remove(task_id)

    def _acp_summary(
        self,
        manager,
        task_id: str,
        info: dict,
    ) -> dict:
        state = info.get("State", {})
        config = info.get("Config", {})
        host = info.get("HostConfig", {})

        return {
            "task_id": task_id,
            "container": manager.container_name(task_id),
            "status": state.get("Status"),
            "running": state.get("Running"),
            "image": config.get("Image"),
            "open_stdin": config.get("OpenStdin"),
            "stdin_once": config.get("StdinOnce"),
            "network": host.get("NetworkMode"),
            "read_only_root": host.get("ReadonlyRootfs"),
        }

    def acp_sandbox_create(self, task_id: str) -> dict:
        """Create and immediately revalidate one stopped task sandbox."""
        with self._acp_operation(task_id):
            manager = self._acp_manager()
            container_id = manager.create(task_id)

            try:
                info = manager.inspect(task_id)
            except Exception as exc:
                raise RuntimeError(
                    "ACP sandbox was created but failed policy revalidation; "
                    "left stopped for operator inspection"
                ) from exc

            state = info.get("State", {})
            if (
                state.get("Status") != "created"
                or state.get("Running") is not False
            ):
                raise RuntimeError(
                    "new ACP sandbox is not in the expected stopped state"
                )

            result = self._acp_summary(manager, task_id, info)
            result["container_id"] = container_id
            return result

    def acp_sandbox_inspect(self, task_id: str) -> dict:
        """Revalidate and report one existing ACP sandbox."""
        with self._acp_operation(task_id):
            manager = self._acp_manager()
            info = manager.inspect(task_id)
            return self._acp_summary(manager, task_id, info)

    def acp_sandbox_start(self, task_id: str) -> dict:
        """Start only a validated sandbox and prove it remains running."""
        with self._acp_operation(task_id):
            manager = self._acp_manager()

            # manager.start() itself performs pre-start policy validation.
            manager.start(task_id)

            # Revalidate the real object after Docker changes its state.
            info = manager.inspect(task_id)

            if info.get("State", {}).get("Running") is not True:
                raise RuntimeError(
                    "ACP sandbox failed to remain running after start"
                )

            return self._acp_summary(manager, task_id, info)

    def acp_sandbox_remove(self, task_id: str) -> dict:
        """Remove only a sandbox that still matches the fixed policy."""
        with self._acp_operation(task_id):
            manager = self._acp_manager()

            # manager.remove() revalidates identity and policy first.
            manager.remove(task_id)

            return {
                "task_id": task_id,
                "container": manager.container_name(task_id),
                "removed": True,
            }

    def validate_promotion_candidate(self, task_id: str) -> dict:
        if not NAME.fullmatch(task_id):
            raise ValueError("invalid task identifier")
        result = self._helper(
            "validate-promotion-candidate", "--task", task_id,
            output_limit=VALIDATION_DOCKER_OUTPUT_LIMIT,
        )
        paths = result.get("changed_paths")
        if not isinstance(paths, list) or result.get("change_count") != len(paths):
            raise RuntimeError("promotion validator returned inconsistent changed-path evidence")
        omitted = max(0, len(paths) - VALIDATION_PATH_PREVIEW_LIMIT)
        return {
            **result,
            "changed_paths": paths[:VALIDATION_PATH_PREVIEW_LIMIT],
            "changed_paths_truncated": omitted > 0,
            "changed_paths_omitted": omitted,
        }

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
