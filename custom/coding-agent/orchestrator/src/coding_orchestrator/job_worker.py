"""Local supervision for an explicitly supplied, trusted Python runner.

This is not a sandbox and does not load profiles, SDKs, credentials, commands, or
request-selected modules. Runners must be picklable trusted server callables. Their
provider adapter must call ``before_provider_request`` immediately before EVERY
physical HTTP dispatch, including any explicitly implemented retry. Stopping this
local process says nothing about remote work; the service must confirm that itself.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import mmap
import os
import pickle
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import Callable

from .openhands_backend import _validate_run_workspace, _validate_scratch_root

MAX_JSON_BYTES = 128 * 1024
MAX_PROGRESS_MESSAGES = 64
_CANCEL_GRACE = 0.15
_TERM_GRACE = 0.15


@dataclass(frozen=True)
class RunContext:
    job_id: str
    prompt: str
    repository_alias: str
    task_mode: str
    execution_id: str = ""


@dataclass(frozen=True)
class WorkerOutcome:
    state: str
    result: dict | None
    error_code: str | None
    request_count: int


class WorkerCancelled(RuntimeError):
    def __init__(self):
        super().__init__("Worker cancelled")


class WorkerDeadline(RuntimeError):
    def __init__(self):
        super().__init__("Worker deadline exceeded")


class WorkerLimit(RuntimeError):
    def __init__(self):
        super().__init__("Worker limit exceeded")


def _json_bytes(value):
    if not isinstance(value, dict):
        raise ValueError("Worker data must be a JSON object")
    try:
        payload = json.dumps(value, ensure_ascii=False, allow_nan=False,
                             separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, RecursionError):
        raise ValueError("Invalid worker JSON") from None
    if len(payload) > MAX_JSON_BYTES:
        raise WorkerLimit()
    return payload


class _Flag:
    def __init__(self, state, offset):
        self._state, self._offset = state, offset

    def is_set(self):
        return bool(self._state[self._offset])

    def set(self):
        self._state[self._offset] = 1


class _Counter:
    def __init__(self, state):
        self._state = state
        self._lock = threading.Lock()

    @property
    def value(self):
        return self._state[0]

    @value.setter
    def value(self, value):
        self._state[0] = value

    def get_lock(self):
        return self._lock

    def get_obj(self):
        return self


class _OwnedProcess:
    """Keep the child unreaped until its session group has been stopped.

    An exited, unreaped leader reserves its PID. Status checks must never call
    Popen.poll()/wait() before group cleanup, because those release that identity.
    """

    def __init__(self, *args, **kwargs):
        self._process = subprocess.Popen(*args, **kwargs)
        self.pid = self._process.pid
        self.owns_pid = True

    def is_alive(self):
        if not self.owns_pid:
            return False
        try:
            return os.waitid(os.P_PID, self.pid,
                             os.WEXITED | os.WNOHANG | os.WNOWAIT) is None
        except ChildProcessError:
            # Another reaper invalidated ownership. Never signal a reused PID.
            self.owns_pid = False
            return False

    @property
    def exitcode(self):
        return self._process.returncode

    def join(self, timeout=None):
        # Wait without releasing the owned PID; only reap() does that.
        deadline = None if timeout is None else time.monotonic() + timeout
        while self.is_alive():
            if deadline is not None and time.monotonic() >= deadline:
                return
            time.sleep(0.005)

    def reap(self):
        if self.owns_pid:
            self._process.wait()
            self.owns_pid = False

    def close(self):
        if self.owns_pid:
            raise RuntimeError("Worker has not been reaped")



def _environment(directory):
    return {
        "HOME": directory,
        "OH_PERSISTENCE_DIR": os.path.join(directory, "openhands"),
        "XDG_CONFIG_HOME": os.path.join(directory, "config"),
        "XDG_CACHE_HOME": os.path.join(directory, "cache"),
        "XDG_DATA_HOME": os.path.join(directory, "data"),
        "TMPDIR": directory,
        "OTEL_SDK_DISABLED": "true",
        "LITELLM_LOCAL_MODEL_COST_MAP": "True",
        "LITELLM_MODE": "PRODUCTION",
        "PYTHON_DOTENV_DISABLED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        # Import locations belong to the server, never to request fields.
        "PYTHONPATH": os.pathsep.join(os.path.abspath(item) for item in sys.path),
    }


def _bootstrap():
    runner_path, context_path, output_fd, state_fd, deadline, maximum = sys.argv[1:]
    # A kernel-delivered default signal bounds this local child even if its
    # supervisor disappears. Trusted runners must not change this watchdog.
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, max(float(deadline) - time.monotonic(), 0.000001))
    state = mmap.mmap(int(state_fd), 3)
    os.close(int(state_fd))
    output = os.fdopen(int(output_fd), "wb", buffering=0)
    with open(context_path, "rb") as source:
        context_data = source.read(MAX_JSON_BYTES + 1)
    if len(context_data) > MAX_JSON_BYTES:
        raise WorkerLimit()
    os.unlink(context_path)
    context = RunContext(**json.loads(context_data))
    _child_main(context, runner_path, output, _Counter(state), _Flag(state, 1),
                _Flag(state, 2), float(deadline), int(maximum))
    state.close()


class WorkerControl:
    """Child-side physical-request accounting and bounded progress delivery."""

    def __init__(self, counter, cancelled, limited, deadline, maximum, output):
        self._counter = counter
        self._cancelled = cancelled
        self._limited = limited
        self._deadline = deadline
        self._maximum = maximum
        self._output = output
        self._progress_count = 0
        self._output_lock = threading.Lock()

    def _check(self):
        if self._cancelled.is_set():
            raise WorkerCancelled()
        if time.monotonic() >= self._deadline:
            raise WorkerDeadline()

    def before_provider_request(self):
        # This lock protects the check-and-increment even for threaded adapters.
        with self._counter.get_lock():
            self._check()
            if self._counter.value >= self._maximum:
                self._limited.set()
                raise WorkerLimit()
            self._counter.value += 1

    def _write(self, message):
        remaining = memoryview(message + b"\n")
        while remaining:
            remaining = remaining[os.write(self._output.fileno(), remaining):]

    def emit_progress(self, value):
        payload = _json_bytes(value)
        with self._output_lock:
            self._check()
            if self._progress_count >= MAX_PROGRESS_MESSAGES:
                raise WorkerLimit()
            self._progress_count += 1
            self._write(b'{"kind":"progress","data":' + payload + b"}")

    def _finish(self, state, result=None, error_code=None):
        payload = (b"null" if result is None else _json_bytes(result))
        header = json.dumps({"kind": "outcome", "state": state,
                             "error_code": error_code}, separators=(",", ":"))
        with self._output_lock:
            self._write(header[:-1].encode("ascii") + b',"result":' + payload + b"}")


def _child_main(context, runner_path, output, counter, cancelled, limited,
                deadline, maximum):
    # Popen established the isolated environment, cwd, stdio, and session before
    # Python imported anything. No ambient credentials reach the trusted runner.
    os.umask(0o077)
    tempfile.tempdir = os.environ["HOME"]
    control = WorkerControl(counter, cancelled, limited, deadline, maximum, output)
    try:
        control._check()
        # Only the server-supplied callable is pickled. Child output and all
        # request/result/progress data use bounded JSON, never pickle.
        with open(runner_path, "rb") as source:
            serialized = source.read(MAX_JSON_BYTES + 1)
        if len(serialized) > MAX_JSON_BYTES:
            raise WorkerLimit()
        os.unlink(runner_path)
        runner = pickle.loads(serialized)
        control._check()
        result = runner(context, control)
        _json_bytes(result)
        control._check()
        if limited.is_set():
            raise WorkerLimit()
        control._finish("completed", result)
    except WorkerCancelled:
        control._finish("cancelled", error_code="cancelled")
    except WorkerDeadline:
        control._finish("timed_out", error_code="deadline_exceeded")
    except WorkerLimit:
        control._finish("failed", error_code="worker_limit")
    except BaseException:
        # Never serialize exception messages or tracebacks from trusted adapters.
        try:
            control._finish("failed", error_code="worker_failed")
        except BaseException:
            pass
    finally:
        output.close()


class ProcessWorker:
    """A poll-driven supervisor. Terminal outcomes mean the child was reaped.

    ``cancel`` sets the cooperative flag immediately; subsequent ``poll`` calls
    enforce a short grace, SIGTERM and SIGKILL. ``close`` performs that sequence
    itself and reaps the owned child. A child SIGALRM watchdog also bounds its
    own lifetime if the parent disappears; it does not reconcile remote work or
    escaped sessions. Service/profile lease reconciliation remains mandatory.
    Neither operation claims remote cancellation.
    """

    def __init__(self, runner: Callable, context: RunContext, *, max_requests=10,
                 timeout_seconds=300, on_progress=None, deadline_monotonic=None):
        if not callable(runner) or not isinstance(context, RunContext):
            raise ValueError("Invalid worker runner or context")
        if any(not isinstance(getattr(context, name), str)
               for name in ("job_id", "prompt", "repository_alias", "task_mode")):
            raise ValueError("Invalid worker context")
        if type(max_requests) is not int or not 1 <= max_requests <= 10:
            raise ValueError("Invalid maximum request count")
        if (isinstance(timeout_seconds, bool)
                or not isinstance(timeout_seconds, (int, float))
                or not math.isfinite(timeout_seconds)
                or not 0 < timeout_seconds <= 300):
            raise ValueError("Invalid worker timeout")
        if on_progress is not None and not callable(on_progress):
            raise ValueError("Invalid progress callback")
        if (deadline_monotonic is not None and (type(deadline_monotonic) not in (int, float)
                or not math.isfinite(deadline_monotonic))):
            raise ValueError("Invalid absolute deadline")
        self._runner = runner
        self._context = context
        self._maximum = max_requests
        self._timeout = timeout_seconds
        self._absolute_deadline = deadline_monotonic
        self._callback = on_progress
        self._temp_root = _validate_scratch_root(tempfile.gettempdir())
        self._state_file = tempfile.TemporaryFile(dir=self._temp_root)
        self._state_file.truncate(3)
        self._state = mmap.mmap(self._state_file.fileno(), 3)
        self._counter = _Counter(self._state)
        self._cancelled = _Flag(self._state, 1)
        self._limited = _Flag(self._state, 2)
        self._process = None
        self._input = None
        self._directory = None
        self._buffer = bytearray()
        self._pending = None
        self._outcome = None
        self._stop_reason = None
        self._stop_at = None
        self._signal_stage = 0
        self._deadline = None
        self._started = False
        self._closed = False
        self._progress_received = 0
        self._last_count = 0
        self._mutex = threading.RLock()

    @property
    def request_count(self):
        # A shared byte can be read without a lock, even when a hard stop
        # interrupted a child while it held the accounting lock.
        return self._last_count if self._counter is None else self._counter.get_obj().value

    def start(self):
        with self._mutex:
            if self._closed or self._started:
                raise RuntimeError("Worker cannot be started")
            self._started = True
            if self._cancelled.is_set():
                self._outcome = WorkerOutcome("cancelled", None, "cancelled", 0)
                return
            child_output = None
            try:
                serialized_runner = pickle.dumps(self._runner)
                if len(serialized_runner) > MAX_JSON_BYTES:
                    raise ValueError("Trusted runner exceeds size limit")
                root = _validate_scratch_root(self._temp_root)
                self._directory = tempfile.TemporaryDirectory(prefix="coding-worker-", dir=root)
                _validate_run_workspace(self._directory.name, root)
                runner_path = os.path.join(self._directory.name, "runner.pickle")
                descriptor = os.open(runner_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "wb") as destination:
                    destination.write(serialized_runner)
                context_path = os.path.join(self._directory.name, "context.json")
                descriptor = os.open(context_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "wb") as destination:
                    destination.write(_json_bytes(self._context.__dict__))
                read_fd, write_fd = os.pipe()
                self._input = os.fdopen(read_fd, "rb", buffering=0)
                child_output = os.fdopen(write_fd, "wb", buffering=0)
                os.set_blocking(read_fd, False)
                self._deadline = time.monotonic() + self._timeout
                if self._absolute_deadline is not None:
                    self._deadline = min(self._deadline, self._absolute_deadline)
                if time.monotonic() >= self._deadline:
                    self._outcome = WorkerOutcome("timed_out", None, "deadline_exceeded", 0)
                    return
                self._process = _OwnedProcess(
                    [sys.executable, "-B", "-c",
                     "from coding_orchestrator.job_worker import _bootstrap; _bootstrap()",
                     runner_path, context_path, str(write_fd),
                     str(self._state_file.fileno()), str(self._deadline), str(self._maximum)],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, cwd=self._directory.name,
                    env=_environment(self._directory.name), start_new_session=True,
                    pass_fds=(write_fd, self._state_file.fileno()),
                )
            except Exception:
                self._begin_stop("failed", "worker_start_failed", immediate=True)
                if self._process is None or self._process.pid is None:
                    self._outcome = WorkerOutcome("failed", None, "worker_start_failed", 0)
            finally:
                if child_output is not None:
                    child_output.close()

    def _begin_stop(self, state, code, *, immediate=False):
        if self._stop_reason is None:
            self._stop_reason = (state, code)
            self._stop_at = time.monotonic() - (_CANCEL_GRACE if immediate else 0)
        self._cancelled.set()

    def cancel(self):
        with self._mutex:
            if not self._closed and self._outcome is None:
                self._begin_stop("cancelled", "cancelled")

    def _signal(self, signum, *, include_exited=False):
        process = self._process
        if process is None or not process.owns_pid:
            return
        if not include_exited and not process.is_alive():
            return
        if not process.owns_pid:
            return
        try:
            if os.getpgid(process.pid) == process.pid:
                os.killpg(process.pid, signum)
            else:
                # A trusted runner may have changed its group. Signal only our child.
                os.kill(process.pid, signum)
        except ProcessLookupError:
            pass

    def _drain(self):
        if self._input is None:
            return
        while True:
            try:
                block = os.read(self._input.fileno(), 65536)
            except BlockingIOError:
                break
            if not block:
                break
            self._buffer.extend(block)
            while b"\n" in self._buffer:
                line, _, remainder = self._buffer.partition(b"\n")
                self._buffer = bytearray(remainder)
                if len(line) > MAX_JSON_BYTES + 256:
                    self._begin_stop("failed", "worker_failed", immediate=True)
                    return
                try:
                    message = json.loads(line)
                    if message["kind"] == "progress":
                        self._progress_received += 1
                        if (self._progress_received > MAX_PROGRESS_MESSAGES
                                or not isinstance(message["data"], dict)):
                            raise ValueError()
                        if self._callback is not None:
                            self._callback(message["data"])
                    elif message["kind"] == "outcome" and self._pending is None:
                        self._pending = message
                    else:
                        raise ValueError()
                except Exception:
                    self._begin_stop("failed", "worker_failed", immediate=True)
                    return
            if len(self._buffer) > MAX_JSON_BYTES + 256:
                self._begin_stop("failed", "worker_failed", immediate=True)
                return

    def poll(self):
        with self._mutex:
            if self._outcome is not None:
                return self._outcome
            if not self._started:
                return None
            self._drain()
            process = self._process
            if process is None or process.pid is None:
                return self._outcome
            alive = process.is_alive()
            now = time.monotonic()
            if alive and now >= self._deadline:
                self._begin_stop("timed_out", "deadline_exceeded", immediate=True)
            elif self._limited.is_set():
                self._begin_stop("failed", "worker_limit", immediate=True)
            if self._stop_reason is not None:
                elapsed = now - self._stop_at
                if elapsed >= _CANCEL_GRACE + _TERM_GRACE and self._signal_stage < 2:
                    self._signal(signal.SIGKILL)
                    self._signal_stage = 2
                elif elapsed >= _CANCEL_GRACE and self._signal_stage < 1:
                    self._signal(signal.SIGTERM)
                    self._signal_stage = 1
            if alive and process.is_alive():
                return None
            # The leader is still an owned zombie here. Kill remaining members
            # before reaping releases its PID, including TERM-ignoring children
            # left behind by a normally completed or cooperatively stopped runner.
            self._signal(signal.SIGKILL, include_exited=True)
            process.reap()
            self._drain()
            if self._stop_reason is not None:
                state, code = self._stop_reason
                result = None
            elif process.exitcode == -signal.SIGALRM and now >= self._deadline:
                state, code, result = "timed_out", "deadline_exceeded", None
            elif process.exitcode != 0 or self._pending is None:
                state, code, result = "interrupted", "worker_interrupted", None
            else:
                state = self._pending["state"]
                code = self._pending["error_code"]
                result = self._pending["result"]
            self._outcome = WorkerOutcome(state, result, code, self.request_count)
            return self._outcome

    def close(self):
        with self._mutex:
            if self._closed:
                return
            try:
                if self._process is not None and self._process.pid is not None:
                    self.cancel()
                    while self.poll() is None:
                        self._process.join(timeout=0.02)
                    self._process.join()
                if self._input is not None:
                    self._input.close()
                if self._process is not None:
                    self._process.close()
            finally:
                try:
                    if self._directory is not None:
                        self._directory.cleanup()
                finally:
                    self._last_count = self.request_count
                    self._counter = None
                    self._cancelled = self._limited = None
                    self._state.close()
                    self._state_file.close()
                    self._runner = self._callback = None
                    self._closed = True
