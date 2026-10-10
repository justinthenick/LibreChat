"""Offline composition only: actual preview/job/SDK stack, synthetic fenced MCP."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coding_orchestrator.job_store import JobStore
from coding_orchestrator.jobs import JobService, Principal
from coding_orchestrator.openhands_profile import create_openhands_profile
from coding_orchestrator.preview_pipe import PreviewPipe
from coding_orchestrator.worker_supervisor import LedgerWorkerSupervisor
from test_profile_sdk_integration import BEFORE, FixtureTransport, fixture_llm, fixture_token
from test_worker_supervisor import FencedFixture, attempt_token, bind_fixture_runner


def serve(directory, mode):
    owner = Principal("owner", "tenant")
    grants = {owner: frozenset({"fixture"})}
    with FencedFixture(directory) as executor, JobStore(directory / "jobs.sqlite") as store, ExitStack() as cleanup:
        supervisor = LedgerWorkerSupervisor(directory / "executor", authority=executor,
            identity_for=lambda context: store.execution_identity(owner.user_id, owner.tenant_id, context.job_id),
            bind_runner=bind_fixture_runner)
        cleanup.callback(supervisor.close)
        executor.inspect = supervisor.ledger.status
        executor.proof_available = mode != "sdk-unknown"
        profile = create_openhands_profile(profile_id="offline-preview-sdk", repository_aliases=grants[owner],
            endpoint=executor.endpoint, token_factory=fixture_token, llm_factory=fixture_llm,
            transport_factory=FixtureTransport("readonly", "read_only", delay_second=10 if mode == "sdk-timeout" else 0),
            authorize=lambda principal, scope: scope.task_mode == "read_only" and scope.repository_alias in grants.get(principal, ()),
            confirm_stopped=supervisor.confirm_stopped)
        service = JobService(store, profile=profile, enabled=True, worker_factory=supervisor.worker_factory)
        cleanup.callback(service.close)
        pipe = PreviewPipe(service, grants=grants, admit_start=lambda *_: True, enabled=True)
        try:
            pipe.serve(sys.stdin.buffer, sys.stdout.buffer)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            service.close()
            # A real stale MCP request must be rejected by the fixture's fence.
            import httpx
            late = httpx.post(executor.endpoint,
                headers={"Authorization": "Bearer " + attempt_token(executor.claim)},
                json={"jsonrpc": "2.0", "id": 99, "method": "tools/list"}, timeout=3)
            proof = {"calls": executor.calls,
                     "sourceUnchanged": (executor.source / "calculator.py").read_text() == BEFORE,
                     "taskUnchanged": not executor.task.exists() or (executor.task / "calculator.py").read_text() == BEFORE,
                     "stopped": supervisor.ledger.status(executor.claim.identity).state == "stopped",
                     "lateRequestStatus": late.status_code}
            (directory / "sdk-proof.json").write_text(json.dumps(proof))
