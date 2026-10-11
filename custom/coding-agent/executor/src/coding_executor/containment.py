"""Dormant gated executor helper; no platform, listener or privilege activation.

A trusted platform must contain the helper before attachment acknowledgement,
prevent escape/migration, revoke future attachments on seal, and independently
observe the exact resource including descendants. No platform is supplied by
default. Synthetic platforms test ordering, not real OS containment.
"""
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from .executions import Claim, ExecutionConflict, ExecutorResource

MAX_FRAME = 64 * 1024
MAX_RESULT = 512 * 1024
_BOOTSTRAP = """import os, sys
gate = int(sys.argv[1])
released = os.read(gate, 1) == b'1'
os.close(gate)
if not released:
    sys.exit(1)
sys.path.insert(0, sys.argv[2])
from coding_executor.containment import _workspace_main
_workspace_main()
"""


@dataclass(frozen=True)
class ExecutorSnapshot:
    claim: Claim
    resource: ExecutorResource
    admission_closed: bool
    quiescent: bool


@dataclass(frozen=True)
class ExecutorQuiescence:
    """Executor-only proof. Deliberately not an executions.Observation."""

    claim: Claim
    resource: ExecutorResource


class GatedExecutor:
    """Trusted platform methods are bounded; request data cannot choose a platform.

    prepare(claim) allocates a fresh identity; attach(claim, resource, pid)
    returns that exact resource only after containing a still-gated helper.
    seal(claim, resource) durably forbids subsequent attachment, including delayed
    requests; stop kills all owned work; inspect returns ExecutorSnapshot from
    independent platform evidence. Boot/root/resource/policy drift is unknown.
    Acknowledgement loss never authorizes a release or automatic retry.
    """

    def __init__(self, ledger, *, platform=None, enabled=False):
        if type(enabled) is not bool:
            raise ValueError("explicit containment policy required")
        self.ledger, self.platform, self.enabled = ledger, platform, enabled
        self._pid = os.getpid()

    def _available(self):
        if (not self.enabled or self.platform is None or os.getpid() != self._pid
                or not all(callable(getattr(self.platform, method, None))
                           for method in ("prepare", "attach", "seal", "stop", "inspect"))):
            raise ExecutionConflict("executor containment unavailable")

    def admit(self, claim):
        self._available()
        previous = self.ledger.reserve_executor(claim)
        if previous is not None:
            self.ledger.bind_executor(claim, previous)
            return
        try:
            resource = self.platform.prepare(claim)
            if type(resource) is not ExecutorResource:
                raise ExecutionConflict("executor resource unconfirmed")
            self.ledger.bind_executor(claim, resource)
        except Exception:
            self.ledger.seal_executor(claim)
            raise ExecutionConflict("executor allocation unknown") from None

    def run(self, claim, frame, remaining):
        self._available()
        resource = self.ledger.executor_resource(claim)
        if resource is None:
            raise ExecutionConflict("executor resource missing")
        payload = json.dumps(frame, allow_nan=False, separators=(",", ":")).encode()
        if len(payload) > MAX_FRAME:
            raise ValueError("executor frame exceeds bound")
        deadline = time.monotonic() + remaining
        read_fd, write_fd = os.pipe()
        process = None
        try:
            with tempfile.TemporaryDirectory(prefix="executor-gate-") as scratch:
                process = subprocess.Popen(
                    [sys.executable, "-I", "-c", _BOOTSTRAP, str(read_fd), str(Path(__file__).resolve().parents[1])],
                    cwd=scratch, env={"PATH": os.defpath, "HOME": scratch, "LANG": "C.UTF-8"},
                    pass_fds=(read_fd,), close_fds=True, start_new_session=True,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                os.close(read_fd)
                read_fd = None
                attached = self.platform.attach(claim, resource, process.pid)
                if type(attached) is not ExecutorResource or attached != resource:
                    raise ExecutionConflict("executor attachment unconfirmed")
                self.ledger.release_executor(claim, resource, write_fd)
                os.close(write_fd)
                write_fd = None
                output, _ = process.communicate(payload, timeout=max(.001, deadline - time.monotonic()))
                if process.returncode != 0 or len(output) > MAX_RESULT or time.monotonic() >= deadline:
                    raise ExecutionConflict("executor result unconfirmed")
                return json.loads(output)
        except Exception:
            self.ledger.seal_executor(claim)
            self.stop(claim)
            raise ExecutionConflict("executor outcome unknown") from None
        finally:
            for descriptor in (read_fd, write_fd):
                if descriptor is not None:
                    os.close(descriptor)
            if process is not None:
                if process.poll() is None:
                    process.kill()
                try:
                    process.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    pass
                for stream in (process.stdin, process.stdout):
                    if stream is not None:
                        stream.close()

    def stop(self, claim):
        self._available()
        resource = self.ledger.executor_resource(claim)
        if resource is None or not self.ledger.status(claim.identity).sealed:
            return
        self.platform.seal(claim, resource)
        self.platform.stop(claim, resource)

    def observe(self, claim):
        """No local exit/thread state can substitute for independent evidence."""
        try:
            self._available()
            resource = self.ledger.executor_resource(claim)
            if resource is None or not self.ledger.executor_fenced(claim, resource):
                return None
            snapshot = self.platform.inspect(claim, resource)
            if (type(snapshot) is not ExecutorSnapshot or type(snapshot.claim) is not Claim
                    or snapshot.claim != claim or type(snapshot.resource) is not ExecutorResource
                    or snapshot.resource != resource or snapshot.admission_closed is not True
                    or snapshot.quiescent is not True):
                return None
            return ExecutorQuiescence(claim, resource)
        except Exception:
            return None


def _workspace_main():
    """Fixed helper entry point. All workspace subprocesses descend from this helper."""
    from .coordination import maintenance_lock
    from .workspaces import WorkspaceManager
    frame = json.loads(sys.stdin.buffer.read(MAX_FRAME + 1))
    manager = WorkspaceManager(Path(frame["repository_root"]), Path(frame["task_root"]),
                               command_timeout_seconds=frame["command_timeout_seconds"],
                               max_output_bytes=frame["max_output_bytes"])
    operation, arguments = frame["operation"], frame["arguments"]
    with maintenance_lock(manager.task_root, lock_path=frame["maintenance_lock"]):
        if operation == "create_task":
            result = manager.create_task(frame["repository"], frame["task_name"], task_mode="read_only")
        elif operation == "run_check":
            result = asdict(manager.run_check(frame["task_id"], frame["command"],
                                             timeout_seconds=frame["remaining"]))
        else:
            if operation not in {"task_status", "git_diff", "list_files", "read_file", "search_text"}:
                raise ValueError("unsupported contained operation")
            method = "diff" if operation == "git_diff" else operation
            result = getattr(manager, method)(frame["task_id"], **arguments)
    output = json.dumps(result, allow_nan=False).encode()
    if len(output) > MAX_RESULT:
        raise ValueError("executor result exceeds bound")
    sys.stdout.buffer.write(output)
