"""Dormant composition of the job worker, executor ledger and stop-proof adapter.

Import explicitly with both packages installed. No server, transport, credential
or profile registration is performed. The injected authority and runner binder
are trusted bounded capabilities, never request data.
"""
from dataclasses import asdict
import hashlib
import json
import math
import os
import threading
import time

from coding_executor.executions import Claim, ExecutionBusy, ExecutionIdentity, ExecutionService, Observation

from .executor_adapter import ExecutorStopAdapter
from .job_store import ExecutionIdentity as JobIdentity
from .job_worker import ProcessWorker, RunContext, WorkerOutcome


def _matches(observation, claim):
    return (type(observation) is Observation and type(observation.claim) is Claim
            and type(observation.claim.identity) is ExecutionIdentity and observation.claim == claim
            and type(observation.state) is str and type(observation.fenced) is bool)


class _Worker:
    def __init__(self, owner, identity, runner, context, maximum, timeout, deadline, progress):
        self.owner, self.identity, self.runner, self.context = owner, identity, runner, context
        self.maximum, self.timeout, self.progress = maximum, timeout, progress
        self.deadline = deadline
        payload = {"identity": asdict(identity), "prompt": context.prompt,
                   "max_requests": maximum, "deadline_monotonic": self.deadline}
        self.digest = hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False,
                                               separators=(",", ":")).encode()).hexdigest()
        self.claim = None
        self.local = None
        self.outcome = None
        self.started = False
        self.preparing = False
        self.closed = False
        self.cancelled = threading.Event()
        self.lock = threading.RLock()

    @property
    def request_count(self):
        return 0 if self.local is None else self.local.request_count

    def start(self):
        self.owner._check()
        with self.lock:
            if self.started or self.closed:
                raise RuntimeError("worker already consumed")
            self.started = True
        self.preparing = True
        try:
            self.owner.ledger.advance(self.identity)
            status = self.owner.ledger.start(self.identity, "job-worker", self.digest)
        except Exception:
            self.preparing = False
            raise
        try:
            if (status.sealed or status.state != "running" or self.claim is None
                    or len(status.operations) != 1 or status.operations[0].claim != self.claim):
                self.outcome = WorkerOutcome("interrupted", None, "executor_start_unconfirmed", 0)
                return
            if self.owner._prepare is not None:
                self.owner._prepare(self.claim, max_requests=self.maximum,
                    timeout_seconds=self.timeout, deadline_monotonic=self.deadline)
            runner = self.owner._bind(self.runner, self.claim)
            with self.lock:
                if self.closed or self.cancelled.is_set():
                    self.outcome = WorkerOutcome("cancelled", None, "cancelled", 0)
                    return
                if time.monotonic() >= self.deadline:
                    self.outcome = WorkerOutcome("timed_out", None, "deadline_exceeded", 0)
                    return
                self.local = ProcessWorker(runner, self.context, max_requests=self.maximum,
                    timeout_seconds=self.timeout, deadline_monotonic=self.deadline, on_progress=self.progress)
                self.local.start()
        except Exception:
            with self.lock:
                if self.local is not None:
                    self.local.close()
                self.outcome = WorkerOutcome("failed", None, "worker_start_failed", self.request_count)
        finally:
            self.preparing = False

    def poll(self):
        self.owner._check()
        with self.lock:
            if self.outcome is not None:
                return self.outcome
            if self.local is not None:
                if self.cancelled.is_set():
                    self.local.cancel()
                self.outcome = self.local.poll()
            return self.outcome

    def cancel(self):
        # No ledger or external callback while JobService holds its lock.
        self.cancelled.set()

    def close(self):
        self.owner._check()
        with self.lock:
            if self.closed:
                return
            self.cancelled.set()
            if self.local is not None:
                self.local.close()
                self.outcome = self.local.poll()
            self.closed = True
            self.runner = self.progress = None


class LedgerWorkerSupervisor:
    """Explicit trusted worker factory and confirm_stopped hook for one job.

    authority implements the executor Supervisor contract. Its launch must
    establish an attempt-specific remote admission fence; bind_runner must
    return picklable child configuration whose EVERY external dispatch uses
    that claim. Neither is inferred from a token, process exit or idle socket.
    The authority must fence delayed requests and observe all external work.

    identity_for resolves the admitted JobStore identity from trusted state.
    Both launch/binding callbacks must be bounded and must not call back into
    JobService. Stop/observation uses ExecutorStopAdapter's bounded caller wait.
    Restart deliberately cannot prove local quiescence from missing handles.
    Close JobService before this resource owner; never close during a callback.
    """

    def __init__(self, directory, *, authority, identity_for, bind_runner, prepare_dispatch=None):
        if not callable(identity_for) or not callable(bind_runner) or not all(
                callable(getattr(authority, name, None)) for name in ("launch", "stop", "observe")):
            raise ValueError("trusted supervisor capabilities required")
        if prepare_dispatch is not None and not callable(prepare_dispatch):
            raise ValueError("trusted dispatch admission required")
        self._prepare = prepare_dispatch
        self.authority_id = authority.authority_id
        self._authority, self._identity_for, self._bind = authority, identity_for, bind_runner
        self._pid = os.getpid()
        self._closed = False
        self._factory_lock = threading.Lock()
        self._worker = None
        self.ledger = ExecutionService(directory, self)
        self._stop = ExecutorStopAdapter(self._control, authority_id=self.authority_id)

    def _check(self):
        if self._closed or os.getpid() != self._pid:
            raise RuntimeError("supervisor closed or inherited across fork")

    def worker_factory(self, runner, context, *, max_requests=10, timeout_seconds=300, on_progress=None):
        entered = time.monotonic()
        self._check()
        if (not callable(runner) or type(context) is not RunContext
                or type(max_requests) is not int or not 1 <= max_requests <= 10
                or type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
                or not 0 < timeout_seconds <= 300
                or (on_progress is not None and not callable(on_progress))):
            raise ValueError("invalid worker configuration")
        identity = self._identity_for(context)
        if (type(identity) is not JobIdentity or identity.job_id != context.job_id
                or identity.execution_id != context.execution_id
                or identity.repository_alias != context.repository_alias or identity.task_mode != context.task_mode):
            raise ValueError("worker identity mismatch")
        remote = ExecutionIdentity(**asdict(identity))
        with self._factory_lock:
            previous = self._worker
            if previous is not None and (not previous.closed or self.ledger.status(previous.identity).state != "stopped"):
                raise ExecutionBusy("previous worker unresolved")
            self._worker = _Worker(self, remote, runner, context, max_requests, timeout_seconds,
                                   entered + timeout_seconds, on_progress)
            return self._worker

    def _bound(self, claim):
        self._check()
        worker = self._worker
        if (self._authority.authority_id != self.authority_id or worker is None
                or worker.identity != claim.identity or worker.claim != claim):
            return None
        return worker

    def launch(self, claim):
        self._check()
        worker = self._worker
        if (worker is None or worker.claim is not None or not worker.started or worker.closed
                or worker.identity != claim.identity or worker.digest != claim.request_sha256
                or claim.operation_id != "job-worker" or claim.authority_id != self.authority_id
                or self._authority.authority_id != self.authority_id):
            return None
        worker.claim = claim
        # Commit is owned by ExecutionService before this callback. Unknown
        # launch acknowledgements must never start the child or replay launch.
        acknowledgement = self._authority.launch(claim)
        if not _matches(acknowledgement, claim) or acknowledgement.state != "running":
            return None
        return Observation(claim, "running", False)

    def stop(self, claim):
        worker = self._bound(claim)
        if worker is not None:
            worker.cancel()
            self._authority.stop(claim)

    def observe(self, claim):
        worker = self._bound(claim)
        if worker is None:
            return None
        with worker.lock:
            local_stopped = not worker.preparing and (worker.local is None or worker.outcome is not None)
        if not local_stopped:
            return None
        observation = self._authority.observe(claim)
        if (_matches(observation, claim) and observation.state == "quiescent"
                and observation.fenced is True):
            return Observation(claim, "quiescent", True)
        return None

    def _control(self, identity, *, timeout_seconds):
        self._check()
        remote = ExecutionIdentity(**identity)
        status = self.ledger.status(remote)
        worker = self._worker
        if status.state == "stopped" and status.sealed:
            return {"authority_id": self.authority_id, "status": asdict(status)}
        if worker is None or worker.identity != remote:
            return None
        # Only owned local history permits minting a stop tombstone. Missing
        # records/handles alone cannot prove that a worker never dispatched.
        return {"authority_id": self.authority_id,
                "status": asdict(self.ledger.stop(remote))}

    def confirm_stopped(self, identity):
        self._check()
        return self._stop.confirm_stopped(identity)

    def close(self):
        if self._closed:
            return
        self._check()
        if self._worker is not None:
            self._worker.close()
        self.ledger.close()
        self._closed = True
