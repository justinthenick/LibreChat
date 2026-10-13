"""Synthetic private-pipe host. Real job/attempt ledgers and supervised child; no providers."""
from dataclasses import replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "executor" / "src"))
from coding_executor.executions import Observation
from coding_orchestrator.job_store import JobStore
from coding_orchestrator.jobs import ExecutionProfile, JobService, Principal
from coding_orchestrator.preview_pipe import PreviewPipe
from coding_orchestrator.worker_supervisor import LedgerWorkerSupervisor
from fixture_runner import BoundRunner, run

OWNER = Principal("owner", "tenant")
GRANTS = {OWNER: frozenset({"fixture"})}


def bind(runner, claim):
    return BoundRunner(runner, claim)


class Authority:
    authority_id = "synthetic-pipe-authority"

    def __init__(self, directory, mode):
        self.directory, self.mode = directory, mode
        self.claim, self.sealed = None, False
        self.inspect = None

    def launch(self, claim):
        if not any(operation.claim == claim for operation in self.inspect(claim.identity).operations):
            raise AssertionError("dispatch preceded durable claim")
        self.claim, self.sealed = claim, False
        with (self.directory / "launches.jsonl").open("a") as stream:
            stream.write(json.dumps({"attempt": claim.attempt_id, "job": claim.identity.job_id}) + "\n")
        if self.mode == "mismatch":
            return Observation(replace(claim, attempt_id="wrong-attempt"), "running", False)
        return Observation(claim, "running", False)

    def stop(self, claim):
        if claim != self.claim:
            raise AssertionError("wrong stop claim")
        self.sealed = True

    def observe(self, claim):
        if self.mode in {"unknown", "mismatch"} or claim != self.claim:
            return None
        return Observation(claim, "quiescent" if self.sealed else "running", self.sealed)


def main():
    directory, mode = Path(sys.argv[1]), sys.argv[2]
    if mode.startswith("sdk-"):
        from sdk_fixture import serve
        return serve(directory, mode)
    with JobStore(directory / "jobs.sqlite") as store:
        authority = Authority(directory, mode)
        supervisor = LedgerWorkerSupervisor(directory / "executor", authority=authority,
            identity_for=lambda context: store.execution_identity(OWNER.user_id, OWNER.tenant_id, context.job_id),
            bind_runner=bind)
        authority.inspect = supervisor.ledger.status
        profile = ExecutionProfile("pipe-fixture", GRANTS[OWNER], run,
            lambda principal, scope: scope.repository_alias in GRANTS.get(principal, ()) and scope.task_mode == "read_only",
            supervisor.confirm_stopped)
        service = JobService(store, profile=profile, enabled=True, worker_factory=supervisor.worker_factory)
        pipe = PreviewPipe(service, grants=GRANTS,
                           admit_start=lambda principal, request: request.get("prompt") != "denied",
                           enabled=mode != "disabled")
        try:
            pipe.serve(sys.stdin.buffer, sys.stdout.buffer)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            service.close()
            supervisor.close()


if __name__ == "__main__":
    main()
