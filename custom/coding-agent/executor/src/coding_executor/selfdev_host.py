from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import socket
import socketserver
import stat
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
OUTPUT_LIMIT_BYTES = 65_536
REQUEST_LIMIT_BYTES = 65_536
CANDIDATE_CONTAINER = "librechat-coding-executor-candidate"
EXPECTED_CANDIDATE_TOOLS = (
    "list_repositories",
    "create_task",
    "task_status",
    "list_files",
    "read_file",
    "search_text",
    "apply_patch",
    "run_check",
    "git_diff",
)
SELFDEV_ONLY_TOOLS = (
    "build_candidate",
    "test_candidate",
    "start_candidate",
    "run_candidate_gate",
    "candidate_status",
    "destroy_candidate",
)


def _bounded(value: str) -> tuple[str, bool]:
    encoded = value.encode("utf-8")
    if len(encoded) <= OUTPUT_LIMIT_BYTES:
        return value, False
    return (
        encoded[:OUTPUT_LIMIT_BYTES].decode("utf-8", errors="ignore") + "\n[output truncated]",
        True,
    )


class SelfDevWorker:
    def __init__(
        self,
        task_root: Path,
        candidate_root: Path,
        candidate_port: int = 8767,
    ) -> None:
        self.task_root = task_root.expanduser().resolve()
        self.candidate_root = candidate_root.expanduser().resolve()
        if self.task_root == self.candidate_root:
            raise ValueError("task root and candidate root must differ")
        if not 1024 <= candidate_port <= 65535:
            raise ValueError("candidate port must be between 1024 and 65535")
        self.candidate_port = candidate_port
        self.candidate_root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.candidate_root, 0o700)
        self.state_path = self.candidate_root / "state.json"
        self.repo_root = self.candidate_root / "repos"
        self.runtime_task_root = self.candidate_root / "tasks"
        self.repo_root.mkdir(exist_ok=True)
        self.runtime_task_root.mkdir(exist_ok=True)

    def handle(self, action: str, params: dict[str, object]) -> dict[str, object]:
        allowed = {
            "build_candidate": self.build_candidate,
            "test_candidate": self.test_candidate,
            "start_candidate": self.start_candidate,
            "run_candidate_gate": self.run_candidate_gate,
            "candidate_status": self.candidate_status,
            "destroy_candidate": self.destroy_candidate,
        }
        handler = allowed.get(action)
        if handler is None:
            raise ValueError("unsupported self-development action")
        if action in {"candidate_status", "destroy_candidate"}:
            if params:
                raise ValueError(f"{action} does not accept parameters")
            return handler()
        if set(params) != {"task_id"} or not isinstance(params.get("task_id"), str):
            raise ValueError(f"{action} requires only task_id")
        return handler(str(params["task_id"]))

    def build_candidate(self, task_id: str) -> dict[str, object]:
        task, executor = self._task_executor(task_id)
        image = self._image_name(task_id)
        result = self._run(
            ["docker", "build", "--pull=false", "-t", image, str(executor)],
            timeout=900,
        )
        self._write_state(
            {
                "task_id": task_id,
                "task_path": str(task),
                "image": image,
                "container": CANDIDATE_CONTAINER,
                "port": self.candidate_port,
                "built_at": int(time.time()),
            }
        )
        return {
            "task_id": task_id,
            "image": image,
            "exit_code": result["exit_code"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "truncated": result["truncated"],
        }

    def test_candidate(self, task_id: str) -> dict[str, object]:
        task, _ = self._task_executor(task_id)
        state = self._require_state(task_id)
        image = str(state["image"])

        compile_result = self._run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=256m",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--pids-limit",
                "256",
                "--memory",
                "2g",
                "--cpus",
                "2",
                "-e",
                "PYTHONPYCACHEPREFIX=/tmp/pycache",
                image,
                "python3",
                "-m",
                "compileall",
                "-q",
                "/app/src",
            ],
            timeout=180,
            check=False,
        )

        test_result = self._run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=256m",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--pids-limit",
                "256",
                "--memory",
                "2g",
                "--cpus",
                "2",
                "-v",
                f"{task}:/candidate:ro",
                image,
                "python3",
                "-m",
                "unittest",
                "discover",
                "-s",
                "/candidate/custom/coding-agent/executor/tests",
                "-p",
                "test_*.py",
                "-v",
            ],
            timeout=600,
            check=False,
        )

        return {
            "task_id": task_id,
            "compileall": compile_result,
            "unit_tests": test_result,
            "passed": compile_result["exit_code"] == 0 and test_result["exit_code"] == 0,
        }

    def run_candidate_gate(self, task_id: str) -> dict[str, object]:
        self._task_executor(task_id)
        if self._read_state() is not None or self._container_exists():
            raise RuntimeError("candidate state already exists; destroy it before running the gate")

        result: dict[str, object] = {
            "task_id": task_id,
            "passed": False,
            "stage": "build",
        }
        try:
            result["build"] = self.build_candidate(task_id)

            result["stage"] = "test"
            tests = self.test_candidate(task_id)
            result["tests"] = tests
            if tests.get("passed") is not True:
                result["error"] = "candidate validation failed"
                return result

            result["stage"] = "start"
            result["start"] = self.start_candidate(task_id)

            result["stage"] = "mcp_smoke"
            smoke = self._mcp_smoke()
            result["mcp_smoke"] = smoke
            if smoke.get("ok") is not True:
                result["error"] = "candidate MCP smoke failed"
                return result

            result["stage"] = "status"
            status = self.candidate_status()
            result["status"] = status
            if status.get("container_exists") is not True:
                result["error"] = "candidate container disappeared during gate"
                return result

            result["passed"] = True
            result["stage"] = "complete"
            return result
        except Exception as error:
            result["error"] = str(error)
            return result
        finally:
            try:
                result["cleanup"] = self.destroy_candidate()
            except Exception as error:
                result["cleanup"] = {"error": str(error)}
                result["passed"] = False
                result["stage"] = "cleanup"

    def start_candidate(self, task_id: str) -> dict[str, object]:
        self._task_executor(task_id)
        state = self._require_state(task_id)
        if self._container_exists():
            raise RuntimeError(
                f"{CANDIDATE_CONTAINER} already exists; destroy it before starting another candidate"
            )

        self._ensure_fixture_repository()
        token = secrets.token_urlsafe(48)
        image = str(state["image"])

        result = self._run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                CANDIDATE_CONTAINER,
                "--restart",
                "no",
                "--read-only",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=256m",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--pids-limit",
                "256",
                "--memory",
                "2g",
                "--cpus",
                "2",
                "-p",
                f"127.0.0.1:{self.candidate_port}:{self.candidate_port}",
                "-e",
                f"CODING_EXECUTOR_TOKEN={token}",
                "-e",
                f"CODING_EXECUTOR_PUBLIC_URL=http://127.0.0.1:{self.candidate_port}/mcp",
                "-e",
                (
                    "CODING_EXECUTOR_ALLOWED_HOSTS="
                    f"127.0.0.1:{self.candidate_port},localhost:{self.candidate_port}"
                ),
                "-e",
                f"CODING_EXECUTOR_PORT={self.candidate_port}",
                "-e",
                f"CODING_REPOSITORY_ROOT={self.repo_root}",
                "-e",
                f"CODING_TASK_ROOT={self.runtime_task_root}",
                "-v",
                f"{self.repo_root}:{self.repo_root}:rw",
                "-v",
                f"{self.runtime_task_root}:{self.runtime_task_root}:rw",
                image,
            ],
            timeout=60,
        )
        state["token"] = token
        state["started_at"] = int(time.time())
        self._write_state(state)

        health = self._wait_for_health()
        return {
            "task_id": task_id,
            "container": CANDIDATE_CONTAINER,
            "port": self.candidate_port,
            "docker": result,
            "health": health,
        }

    def candidate_status(self) -> dict[str, object]:
        state = self._read_state()
        exists = self._container_exists()
        inspect = None
        if exists:
            inspect = self._run(
                [
                    "docker",
                    "inspect",
                    CANDIDATE_CONTAINER,
                    "--format",
                    "status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} restarts={{.RestartCount}}",
                ],
                timeout=30,
                check=False,
            )
        return {
            "state": self._public_state(state),
            "container_exists": exists,
            "inspect": inspect,
        }

    def destroy_candidate(self) -> dict[str, object]:
        state = self._read_state()
        removed_container = False
        if self._container_exists():
            self._run(["docker", "rm", "-f", CANDIDATE_CONTAINER], timeout=60)
            removed_container = True

        removed_image = False
        if state and isinstance(state.get("image"), str):
            image = str(state["image"])
            result = self._run(["docker", "image", "rm", image], timeout=120, check=False)
            removed_image = result["exit_code"] == 0

        if self.state_path.exists():
            self.state_path.unlink()

        return {
            "removed_container": removed_container,
            "removed_image": removed_image,
        }

    def _task_executor(self, task_id: str) -> tuple[Path, Path]:
        if not SAFE_TASK_ID.fullmatch(task_id):
            raise ValueError("invalid task id")
        candidate = self.task_root / task_id
        if candidate.is_symlink():
            raise ValueError("task path may not be a symlink")
        task = candidate.resolve(strict=True)
        if task.parent != self.task_root or not task.is_dir():
            raise ValueError("task does not exist under configured task root")
        if not (task / ".git").exists():
            raise ValueError("task is not a Git worktree")
        executor = task / "custom/coding-agent/executor"
        if (
            executor.is_symlink()
            or not (executor / "Dockerfile").is_file()
            or not (executor / "pyproject.toml").is_file()
        ):
            raise ValueError("task does not contain the coding executor build context")
        return task, executor

    @staticmethod
    def _image_name(task_id: str) -> str:
        digest = hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:12]
        return f"librechat-coding-executor-candidate:selfdev-{digest}"

    def _require_state(self, task_id: str) -> dict[str, object]:
        state = self._read_state()
        if not state or state.get("task_id") != task_id:
            raise ValueError("candidate has not been built for this task")
        return state

    def _read_state(self) -> dict[str, object] | None:
        if not self.state_path.exists():
            return None
        value = json.loads(self.state_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise RuntimeError("candidate state is invalid")
        return value

    def _write_state(self, state: dict[str, object]) -> None:
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        temporary.replace(self.state_path)

    @staticmethod
    def _public_state(state: dict[str, object] | None) -> dict[str, object] | None:
        if state is None:
            return None
        return {key: value for key, value in state.items() if key != "token"}

    def _container_exists(self) -> bool:
        result = self._run(
            ["docker", "inspect", CANDIDATE_CONTAINER],
            timeout=30,
            check=False,
        )
        return result["exit_code"] == 0

    def _ensure_fixture_repository(self) -> None:
        repository = self.repo_root / "selfdev-fixture"
        if (repository / ".git").exists():
            return
        repository.mkdir(parents=True, exist_ok=True)
        self._run(["git", "init", "-b", "main"], cwd=repository, timeout=30)
        self._run(
            ["git", "config", "user.email", "selfdev@example.invalid"],
            cwd=repository,
            timeout=30,
        )
        self._run(
            ["git", "config", "user.name", "SelfDev Harness"],
            cwd=repository,
            timeout=30,
        )
        (repository / "example.txt").write_text("alpha\nbeta\n", encoding="utf-8")
        self._run(["git", "add", "example.txt"], cwd=repository, timeout=30)
        self._run(["git", "commit", "-m", "initial fixture"], cwd=repository, timeout=30)

    def _mcp_request(self, method: str) -> tuple[int, dict[str, object]]:
        state = self._read_state()
        if not state or not isinstance(state.get("token"), str):
            raise RuntimeError("candidate runtime token is unavailable")

        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": f"selfdev-{method.replace('/', '-')}",
                "method": method,
                "params": {
                    "_meta": {
                        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                        "io.modelcontextprotocol/clientCapabilities": {},
                        "io.modelcontextprotocol/clientInfo": {
                            "name": "librechat-selfdev-worker",
                            "version": "1.0",
                        },
                    }
                },
            },
            separators=(",", ":"),
        ).encode("utf-8")

        request = urllib.request.Request(
            f"http://127.0.0.1:{self.candidate_port}/mcp",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {state['token']}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2026-07-28",
                "Mcp-Method": method,
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                raw = response.read(262_144).decode("utf-8", errors="replace")
                status = response.status
        except urllib.error.HTTPError as error:
            raw = error.read(65_536).decode("utf-8", errors="replace")
            detail = raw.strip() or error.reason
            raise RuntimeError(
                f"candidate MCP {method} returned HTTP {error.code}: {detail}"
            ) from error

        try:
            body = json.loads(raw)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"candidate MCP {method} returned non-JSON response"
            ) from error

        if not isinstance(body, dict):
            raise RuntimeError(f"candidate MCP {method} returned invalid response")
        if status < 200 or status >= 300:
            raise RuntimeError(f"candidate MCP {method} returned HTTP {status}")
        if "error" in body:
            raise RuntimeError(
                f"candidate MCP {method} returned protocol error: {body['error']}"
            )
        return status, body

    def _mcp_smoke(self) -> dict[str, object]:
        discover_status, discover = self._mcp_request("server/discover")
        discover_result = discover.get("result")
        if not isinstance(discover_result, dict):
            raise RuntimeError("candidate MCP discovery result is invalid")

        supported = discover_result.get("supportedVersions")
        if not isinstance(supported, list) or "2026-07-28" not in supported:
            raise RuntimeError(
                "candidate MCP discovery did not advertise protocol 2026-07-28"
            )

        tools_status, tools_response = self._mcp_request("tools/list")
        tools_result = tools_response.get("result")
        if not isinstance(tools_result, dict):
            raise RuntimeError("candidate MCP tools/list result is invalid")
        tools = tools_result.get("tools")
        if not isinstance(tools, list):
            raise RuntimeError("candidate MCP tools/list omitted tool catalogue")

        names = {
            item.get("name")
            for item in tools
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
        missing = [name for name in EXPECTED_CANDIDATE_TOOLS if name not in names]
        leaked = [name for name in SELFDEV_ONLY_TOOLS if name in names]
        if missing:
            raise RuntimeError(
                "candidate MCP tools/list omitted expected tools: " + ", ".join(missing)
            )
        if leaked:
            raise RuntimeError(
                "candidate unexpectedly exposed self-development tools: " + ", ".join(leaked)
            )

        return {
            "ok": True,
            "discover_http_status": discover_status,
            "tools_http_status": tools_status,
            "supported_versions": supported,
            "expected_tools_present": list(EXPECTED_CANDIDATE_TOOLS),
            "selfdev_tools_absent": True,
        }

    def _wait_for_health(self) -> dict[str, object]:
        url = f"http://127.0.0.1:{self.candidate_port}/health"
        last_error = ""
        for _ in range(30):
            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    body = response.read(16_384).decode("utf-8")
                    if 200 <= response.status < 300:
                        return {"ok": True, "body": body}
            except Exception as error:
                last_error = str(error)
            time.sleep(1)
        raise RuntimeError(f"candidate health check failed: {last_error}")

    @staticmethod
    def _run(
        args: list[str],
        *,
        timeout: int,
        cwd: Path | None = None,
        check: bool = True,
    ) -> dict[str, object]:
        result = subprocess.run(
            args,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "HOME": os.environ.get("HOME", "/tmp"),
                "LANG": "C.UTF-8",
            },
        )
        stdout, stdout_cut = _bounded(result.stdout)
        stderr, stderr_cut = _bounded(result.stderr)
        value = {
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "truncated": stdout_cut or stderr_cut,
        }
        if check and result.returncode != 0:
            raise RuntimeError(stderr.strip() or stdout.strip() or f"command failed: {args[0]}")
        return value


class _UnixServer(socketserver.UnixStreamServer):
    allow_reuse_address = False


class _Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        raw = self.rfile.readline(REQUEST_LIMIT_BYTES + 1)
        if len(raw) > REQUEST_LIMIT_BYTES:
            response = {"ok": False, "error": "request exceeded limit"}
        else:
            try:
                payload = json.loads(raw.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("request must be an object")
                action = payload.get("action")
                params = payload.get("params", {})
                if not isinstance(action, str) or not isinstance(params, dict):
                    raise ValueError("request requires string action and object params")
                result = self.server.worker.handle(action, params)  # type: ignore[attr-defined]
                response = {"ok": True, "result": result}
            except Exception as error:
                response = {"ok": False, "error": str(error)}
        self.wfile.write(json.dumps(response, separators=(",", ":")).encode("utf-8") + b"\n")


def serve(worker: SelfDevWorker, socket_path: Path) -> None:
    socket_path = socket_path.expanduser()
    if not socket_path.is_absolute():
        raise ValueError("socket path must be absolute")
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(socket_path.parent, 0o700)
    if socket_path.exists():
        mode = socket_path.lstat().st_mode
        if not stat.S_ISSOCK(mode):
            raise ValueError("refusing to replace a non-socket path")
        socket_path.unlink()

    old_umask = os.umask(0o077)
    try:
        server = _UnixServer(str(socket_path), _Handler)
    finally:
        os.umask(old_umask)
    server.worker = worker  # type: ignore[attr-defined]
    os.chmod(socket_path, 0o600)
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        server.server_close()
        if socket_path.exists() and stat.S_ISSOCK(socket_path.lstat().st_mode):
            socket_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Restricted host worker for coding-agent self-development")
    parser.add_argument("--task-root", required=True)
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--candidate-port", type=int, default=8767)
    args = parser.parse_args()

    worker = SelfDevWorker(
        Path(args.task_root),
        Path(args.candidate_root),
        args.candidate_port,
    )
    serve(worker, Path(args.socket))


if __name__ == "__main__":
    main()
