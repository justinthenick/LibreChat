"""Operator-only disposable Docker smoke test; never mounts existing executor data.

Usage: PYTHONPATH=executor/src:host/src python3 staging_smoke.py VALIDATED_CANDIDATE_IMAGE
"""
from __future__ import annotations

import json
import concurrent.futures
import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from coding_executor.coordination import maintenance_lock
from host_maintenance.broker import Broker


def command(*argv: str) -> str:
    return subprocess.run(argv, check=True, capture_output=True, text=True, timeout=120).stdout.strip()


def main(image: str) -> None:
    name = "codex-maintenance-smoke-" + secrets.token_hex(4)
    image_id = command("docker", "image", "inspect", "--format", "{{.Id}}", image)
    with tempfile.TemporaryDirectory(prefix="codex-maintenance-fixture-") as directory:
        root = Path(directory)
        root.chmod(0o755)
        repos, tasks, lock = root / "repos", root / "tasks", root / "maintenance.lock"
        repos.mkdir()
        tasks.mkdir()
        lock.touch(mode=0o644)
        repo = repos / "demo"
        repo.mkdir()
        command("git", "-C", str(repo), "init", "-b", "main")
        command("git", "-C", str(repo), "config", "user.name", "Disposable Smoke")
        command("git", "-C", str(repo), "config", "user.email", "smoke@example.invalid")
        (repo / "file").write_text("fixture\n")
        command("git", "-C", str(repo), "add", ".")
        command("git", "-C", str(repo), "commit", "-m", "fixture")
        config = {"container": name, "image_id": image_id, "repository_root": str(repos),
                  "task_root": str(tasks), "lock_path": str(lock),
                  "repositories": {"demo": {"branch": "main", "url": "https://github.com/example/demo.git"}},
                  "enabled_mutations": {"cleanup": True, "restart": True}, "retired_tasks": {}}
        try:
            command("docker", "run", "-d", "--name", name, "--network", "none", "--read-only",
                    "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "64",
                    "--memory", "256m", "--user", f"{os.getuid()}:{os.getgid()}",
                    "--tmpfs", "/tmp:rw,nosuid,size=64m",
                    "--mount", f"type=bind,source={repos},target={repos}",
                    "--mount", f"type=bind,source={tasks},target={tasks}",
                    "--mount", f"type=bind,source={lock},target=/run/coding-agent/maintenance.lock,readonly",
                    "-e", f"CODING_REPOSITORY_ROOT={repos}", "-e", f"CODING_TASK_ROOT={tasks}",
                    "-e", "CODING_MAINTENANCE_LOCK=/run/coding-agent/maintenance.lock",
                    "-e", f"CODING_EXECUTOR_TOKEN={secrets.token_urlsafe(48)}",
                    "-e", "CODING_EXECUTOR_PUBLIC_URL=http://127.0.0.1:8765/mcp",
                    "-e", "CODING_EXECUTOR_ALLOWED_HOSTS=127.0.0.1:8765",
                    "--health-cmd", "python3 -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health',timeout=2)\"",
                    "--health-interval", "1s", "--health-timeout", "3s", image)
            broker = Broker(config)
            for _ in range(30):
                if broker.health()["health"] == "healthy":
                    break
                time.sleep(1)
            assert broker.health()["health"] == "healthy"
            assert broker.repository_status("demo")["freshness"] == "not_fetched"
            creation = "from pathlib import Path; from coding_executor.workspaces import WorkspaceManager; import os,json; m=WorkspaceManager(Path(os.environ['CODING_REPOSITORY_ROOT']),Path(os.environ['CODING_TASK_ROOT'])); t=m.create_task('demo','smoke','main','read_only'); m.read_file(t['task_id'],'file'); print(json.dumps(t))"
            task = json.loads(command("docker", "exec", name, "python3", "-I", "-B", "-c", creation))["task_id"]
            assert len(broker.task_inventory()["tasks"]) == 1
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
                results = list(pool.map(lambda index: broker.task_inventory() if index % 2 else broker.repository_status("demo"), range(6)))
            assert len(results) == 6
            with maintenance_lock(tasks, lock_path=lock):
                try:
                    broker.restart_executor(broker.preview_restart()["ticket"])
                    raise AssertionError("restart accepted while gate was held")
                except RuntimeError as error:
                    assert "executor_busy" in str(error)
            assert broker.restart_executor(broker.preview_restart()["ticket"])["restarted"]
            state_check = "from pathlib import Path; from coding_executor.workspaces import WorkspaceManager; import os,json,sys; print(json.dumps(WorkspaceManager(Path(os.environ['CODING_REPOSITORY_ROOT']),Path(os.environ['CODING_TASK_ROOT'])).task_status(sys.argv[1])))"
            state = json.loads(command("docker", "exec", name, "python3", "-I", "-B", "-c", state_check, task))
            assert state["exploration_budget"]["task_mode"] == "read_only"
            assert state["exploration_budget"]["exploration_calls"] == 1
            config["retired_tasks"][task] = {**broker._helper("preview", "--task", task), "retired_at": time.time() - 90000}
            preview = broker.preview_cleanup(task)
            (tasks / task / "file").write_text("keep this change\n")
            try:
                broker.cleanup_task(preview["ticket"], task)
                raise AssertionError("dirty task removed")
            except RuntimeError:
                assert (tasks / task / "file").read_text() == "keep this change\n"
            # Restore only the disposable fixture this test created.
            (tasks / task / "file").write_text("fixture\n")
            result = broker.cleanup_task(broker.preview_cleanup(task)["ticket"], task)
            assert result["branch_retained"] == f"agent/{task}"
            assert not (tasks / task).exists()
            assert f"agent/{task}" in command("git", "-C", str(repo), "branch", "--list")
            assert broker.logs()["raw_logs_exposed"] is False
            print(json.dumps({"passed": True, "checks": ["pinned image/mounts", "health", "repository status",
                "task inventory", "six concurrent maintenance calls", "busy restart refusal", "real restart with health recovery", "mode/budget persistence",
                "dirty cleanup refusal", "clean cleanup with branch retention", "filtered logs"], "production_touched": False}))
        finally:
            # Exact unique test-owned name; never a user/production container selector.
            subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True, timeout=30)


if __name__ == "__main__":
    main(sys.argv[1])
