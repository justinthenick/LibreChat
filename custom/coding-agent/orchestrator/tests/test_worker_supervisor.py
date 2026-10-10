"""Real ledgers, child worker and SDK; only external authority/provider are fixtures."""
from contextlib import contextmanager
from dataclasses import replace
from functools import partial
import importlib
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "executor" / "src"))
from coding_executor.executions import Observation
from coding_orchestrator.job_store import JobStore, StoreBusy
from coding_orchestrator.jobs import JobRequest, JobService, Principal, RunScope
from coding_orchestrator.openhands_profile import create_openhands_profile
from test_profile_sdk_integration import (ExecutorFixture, FixtureTransport, GuardedFixtureRunner,
                                         fixture_llm, fixture_token, BEFORE, AFTER)


def attempt_token(claim):
    return "synthetic-attempt-" + claim.attempt_id


def bind_fixture_runner(runner, claim):
    return GuardedFixtureRunner(replace(runner, token_factory=partial(attempt_token, claim)), runner.endpoint)


class FencedFixture(ExecutorFixture):
    authority_id = "synthetic-supervisor"

    def __init__(self, root):
        super().__init__(root)
        self.claim = None
        self.sealed = False
        self.requests = 0
        self.proof_available = True
        self.launch_mode = "running"
        self.inspect = None

    def launch(self, claim):
        persisted = self.inspect(claim.identity)
        if not any(op.claim == claim for op in persisted.operations):
            raise AssertionError("launch occurred before durable claim")
        with self.lock:
            if self.claim is not None:
                raise AssertionError("attempt replayed")
            self.claim = claim
        if self.launch_mode == "raise":
            raise RuntimeError("synthetic lost launch reply")
        if self.launch_mode == "mismatch":
            return Observation(replace(claim, attempt_id="foreign"), "running", False)
        return Observation(claim, "running", False)

    def stop(self, claim):
        with self.lock:
            if claim != self.claim:
                raise AssertionError("wrong stop identity")
            self.sealed = True

    def observe(self, claim):
        with self.lock:
            if claim != self.claim or not self.proof_available:
                return None
            stopped = self.sealed and self.requests == 0 and self.in_flight == 0
            return Observation(claim, "quiescent" if stopped else "running", stopped)

    def __enter__(self):
        import uvicorn
        from fastmcp import FastMCP
        from coding_orchestrator.openhands_backend import EXPECTED_CODING_EXECUTOR_TOOLS
        mcp = FastMCP("fenced-offline-fixture")
        for name in EXPECTED_CODING_EXECUTOR_TOOLS:
            mcp.tool(name=name)(getattr(self, name))
        app = mcp.http_app(path="/mcp", stateless_http=True)
        async def guarded(scope, receive, send):
            if scope["type"] != "http":
                return await app(scope, receive, send)
            with self.lock:
                headers = dict(scope.get("headers", []))
                allowed = (self.claim is not None and not self.sealed
                           and headers.get(b"authorization") == ("Bearer " + attempt_token(self.claim)).encode())
                if allowed:
                    self.requests += 1
            if not allowed:
                await send({"type": "http.response.start", "status": 403, "headers": []})
                return await send({"type": "http.response.body", "body": b"fenced"})
            try:
                await app(scope, receive, send)
            finally:
                with self.lock:
                    self.requests -= 1
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(128)
        self.endpoint = "http://127.0.0.1:%d/mcp" % self.listener.getsockname()[1]
        self.server = uvicorn.Server(uvicorn.Config(guarded, log_level="critical", lifespan="on"))
        self.thread = threading.Thread(target=self.server.run, kwargs={"sockets": [self.listener]}, daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 10
        while not self.server.started and time.monotonic() < deadline:
            time.sleep(.01)
        if not self.server.started:
            raise RuntimeError("fixture did not start")
        return self


class WorkerSupervisorTests(unittest.TestCase):
    def adapter_type(self):
        try:
            return importlib.import_module("coding_orchestrator.worker_supervisor").LedgerWorkerSupervisor
        except ModuleNotFoundError:
            self.fail("trusted worker supervisor is missing")

    @contextmanager
    def job(self, *, scenario="flow", bind=bind_fixture_runner, **options):
        adapter_type = self.adapter_type()
        with tempfile.TemporaryDirectory() as root, FencedFixture(root) as fixture, \
                JobStore(Path(root) / "jobs.sqlite") as store:
            owner = Principal("owner", "tenant")
            adapter = adapter_type(Path(root) / "executor", authority=fixture,
                identity_for=lambda context: store.execution_identity(owner.user_id, owner.tenant_id, context.job_id),
                bind_runner=bind)
            fixture.inspect = adapter.ledger.status
            for key, value in options.items():
                setattr(fixture, key, value)
            profile = create_openhands_profile(profile_id="synthetic-supervised", repository_aliases=frozenset({"fixture"}),
                endpoint=fixture.endpoint, token_factory=fixture_token, llm_factory=fixture_llm,
                transport_factory=FixtureTransport(scenario), authorize=lambda *_: True,
                confirm_stopped=adapter.confirm_stopped)
            service = JobService(store, profile=profile, enabled=True, worker_factory=adapter.worker_factory)
            try:
                yield service, fixture, owner, adapter
            finally:
                service.close()
                adapter.close()

    def request(self, **limits):
        return JobRequest("Fix the disposable fixture.", "key", "generation", 1,
                          RunScope("fixture", "modification"), **{"timeout_seconds": 60, **limits})

    def wait(self, service, owner, run):
        deadline = time.monotonic() + 70
        while run["state"] in {"queued", "running", "cancelling"} and time.monotonic() < deadline:
            time.sleep(.02)
            run = service.get_run(owner, run["job_id"])
        self.assertNotIn(run["state"], {"queued", "running", "cancelling"}, run)
        return run

    def test_actual_sdk_failing_check_patch_passing_check_is_bound_to_durable_attempt(self):
        import httpx
        with self.job() as (service, fixture, owner, adapter):
            request = self.request()
            run = self.wait(service, owner, service.start_run(owner, request))
            self.assertEqual(run["state"], "completed", run)
            self.assertEqual(run["request_count"], 8)
            self.assertEqual([c["exit_code"] for c in run["result"]["evidence"]["checks"]], [1, 0])
            self.assertTrue(run["result"]["evidence"]["evidence_complete"])
            self.assertEqual((fixture.source / "calculator.py").read_text(), BEFORE)
            self.assertEqual((fixture.task / "calculator.py").read_text(), AFTER)
            status = adapter.ledger.status(fixture.claim.identity)
            self.assertTrue(status.sealed)
            self.assertEqual(status.state, "stopped")
            self.assertEqual(len(status.operations), 1)
            self.assertEqual(service.start_run(owner, request), run)
            self.assertEqual(len(fixture.checks), 2)
            response = httpx.post(fixture.endpoint, headers={"Authorization": "Bearer " + attempt_token(fixture.claim)},
                                  json={"jsonrpc": "2.0", "id": 99, "method": "tools/list"})
            self.assertEqual(response.status_code, 403)

    def test_ambiguous_external_stop_keeps_quarantine_until_explicit_exact_proof(self):
        with self.job(scenario="finish", proof_available=False) as (service, fixture, owner, adapter):
            request = self.request()
            run = self.wait(service, owner, service.start_run(owner, request))
            self.assertEqual(run["error_code"], "execution_stop_unconfirmed")
            with self.assertRaises(StoreBusy):
                service.start_run(owner, replace(request, idempotency_key="next", generation_epoch=2))
            self.assertFalse(service.reconcile_run(owner, run["job_id"]))
            fixture.proof_available = True
            self.assertTrue(service.reconcile_run(owner, run["job_id"]))
            self.assertEqual(service.get_run(owner, run["job_id"]), run)
            self.assertEqual(adapter.ledger.status(fixture.claim.identity).state, "stopped")

    def test_uncertain_launch_never_runs_the_child_and_can_reconcile_known_nonstart(self):
        for mode in ("raise", "mismatch"):
            with self.subTest(mode=mode), self.job(launch_mode=mode, proof_available=False) as (service, fixture, owner, adapter):
                run = self.wait(service, owner, service.start_run(owner, self.request()))
                self.assertEqual(run["request_count"], 0)
                self.assertEqual(fixture.calls, [])
                self.assertEqual(run["error_code"], "execution_stop_unconfirmed")
                fixture.proof_available = True
                self.assertTrue(service.reconcile_run(owner, run["job_id"]))

    def test_request_limit_is_preserved_through_supervised_worker(self):
        with self.job() as (service, fixture, owner, adapter):
            run = self.wait(service, owner, service.start_run(owner, self.request(max_requests=1)))
            self.assertEqual(run["state"], "failed", run)
            self.assertEqual(run["error_code"], "worker_limit")
            self.assertEqual(run["request_count"], 1)
            self.assertEqual(fixture.calls, ["create_task"])

    def test_binding_delay_cannot_reset_job_deadline(self):
        def delayed(runner, claim):
            time.sleep(.1)
            return bind_fixture_runner(runner, claim)
        with self.job(bind=delayed) as (service, fixture, owner, adapter):
            run = self.wait(service, owner, service.start_run(owner, self.request(timeout_seconds=.05)))
            self.assertEqual(run["state"], "timed_out", run)
            self.assertEqual(run["request_count"], 0)
            self.assertEqual(fixture.calls, [])
