"""Real job/execution ledgers, synthetic supervisor; no network or providers."""
from dataclasses import asdict, replace
from concurrent.futures import ThreadPoolExecutor
import importlib
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "executor" / "src"))
from coding_executor.executions import ExecutionIdentity as RemoteIdentity, ExecutionService, Observation
from coding_orchestrator.job_store import ExecutionIdentity, JobStore, StoreBusy
from coding_orchestrator.jobs import ExecutionProfile, JobRequest, JobService, Principal, RunScope
from test_jobs import FakeWorker, result


class AdapterTests(unittest.TestCase):
    def adapter(self, control, *, timeout_seconds=.2):
        try:
            module = importlib.import_module("coding_orchestrator.executor_adapter")
        except ModuleNotFoundError:
            self.fail("bounded executor stop adapter is missing")
        return module.ExecutorStopAdapter(control, authority_id="fixture", timeout_seconds=timeout_seconds)

    def identity(self):
        return ExecutionIdentity("job", "execution", "user", "", "generation", 1,
                                 "profile", "repo", "read_only")

    def proof(self, identity):
        return {"authority_id": "fixture", "status": {
            "identity": asdict(identity), "state": "stopped", "sealed": True,
            "operations": [{"state": "stopped", "claim": {
                "identity": asdict(identity), "operation_id": "op", "request_sha256": "a" * 64,
                "attempt_id": "attempt", "authority_id": "fixture"}}]}}

    def test_exact_sealed_proof_becomes_bound_stop_evidence(self):
        identity = self.identity()
        calls = []
        def control(value, *, timeout_seconds):
            calls.append((value, timeout_seconds))
            return self.proof(identity)
        adapter = self.adapter(control)
        self.assertTrue(adapter.confirm_stopped(identity).confirms(identity))
        self.assertEqual(calls, [(asdict(identity), .2)])

    def test_timeout_is_unknown_and_never_queues_more_callbacks(self):
        identity = self.identity()
        entered, release = threading.Event(), threading.Event()
        calls = []
        def control(value, **kwargs):
            calls.append(value)
            entered.set()
            release.wait(5)
            return self.proof(identity)
        adapter = self.adapter(control, timeout_seconds=.02)
        try:
            start = time.monotonic()
            self.assertIsNone(adapter.confirm_stopped(identity))
            self.assertLess(time.monotonic() - start, .5)
            self.assertTrue(entered.is_set())
            for _ in range(3):
                self.assertIsNone(adapter.confirm_stopped(identity))
                self.assertIsNone(adapter.confirm_stopped(replace(identity, execution_id="other")))
            self.assertEqual(len(calls), 1)
            release.set()
            self.assertIsNone(adapter.confirm_stopped(replace(identity, execution_id="other")))
            end = time.monotonic() + 2
            evidence = None
            while evidence is None and time.monotonic() < end:
                evidence = adapter.confirm_stopped(identity)
            self.assertTrue(evidence.confirms(identity))
            self.assertEqual(len(calls), 1)
        finally:
            release.set()

    def test_wrong_identity_authority_unsealed_or_malformed_proof_is_unknown(self):
        from copy import deepcopy
        identity = self.identity()
        valid = self.proof(identity)
        variants = [None, True, {}, {**valid, "authority_id": "other"}]
        for path, value in [(("status", "sealed"), 1), (("status", "sealed"), False),
                            (("status", "state"), "open"), (("status", "identity", "user_id"), "other"),
                            (("status", "identity", "generation_epoch"), True)]:
            changed = deepcopy(valid)
            target = changed
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            variants.append(changed)
        for field, value in [("authority_id", "other"), ("request_sha256", "invalid"),
                             ("operation_id", ""), ("attempt_id", "")]:
            changed = deepcopy(valid)
            changed["status"]["operations"][0]["claim"][field] = value
            variants.append(changed)
        for field in asdict(identity):
            changed = deepcopy(valid)
            changed["status"]["operations"][0]["claim"]["identity"][field] = "wrong"
            variants.append(changed)
        changed = deepcopy(valid)
        changed["status"]["operations"][0]["state"] = "running"
        variants.append(changed)
        changed = deepcopy(valid)
        changed["status"]["operations"] *= 2
        variants.append(changed)
        for value in variants:
            with self.subTest(value=value):
                self.assertIsNone(self.adapter(lambda *a, **k: value).confirm_stopped(identity))

    def test_callback_exception_is_unknown_without_error_detail(self):
        def control(*args, **kwargs):
            raise RuntimeError("private transport details")
        self.assertIsNone(self.adapter(control).confirm_stopped(self.identity()))

    def test_concurrent_calls_never_queue_or_consume_another_identity(self):
        identity = self.identity()
        release, entered = threading.Event(), threading.Event()
        calls = []
        def control(value, **kwargs):
            calls.append(value)
            entered.set()
            release.wait(5)
            return self.proof(identity)
        adapter = self.adapter(control, timeout_seconds=.02)
        try:
            self.assertIsNone(adapter.confirm_stopped(identity))
            self.assertTrue(entered.is_set())
            with ThreadPoolExecutor(max_workers=8) as pool:
                replies = list(pool.map(adapter.confirm_stopped,
                                       [identity, replace(identity, execution_id="other")] * 8))
            self.assertEqual(replies, [None] * 16)
            self.assertEqual(len(calls), 1)
        finally:
            release.set()

    def test_control_cannot_mutate_the_expected_identity(self):
        identity = self.identity()
        def control(value, **kwargs):
            value["user_id"] = "other"
            return self.proof(ExecutionIdentity(**value))
        self.assertIsNone(self.adapter(control).confirm_stopped(identity))

    def test_empty_sealed_tombstone_is_valid_but_oversized_evidence_is_unknown(self):
        identity = self.identity()
        proof = self.proof(identity)
        proof["status"]["operations"] *= 65
        self.assertIsNone(self.adapter(lambda *a, **k: proof).confirm_stopped(identity))
        proof["status"]["operations"] = ()
        self.assertTrue(self.adapter(lambda *a, **k: proof).confirm_stopped(identity).confirms(identity))

    def test_invalid_budgets_are_rejected(self):
        for budget in (True, 0, -1, float("nan"), float("inf"), 1.1):
            with self.assertRaises(ValueError):
                self.adapter(lambda *a, **k: None, timeout_seconds=budget)

    def test_job_cancel_retains_quarantine_until_real_executor_fence(self):
        adapter_type = self.adapter  # Assert missing implementation before fixture setup.
        adapter_type(lambda *a, **k: None)

        class Supervisor:
            authority_id = "fixture"
            stopped = False
            claims = []
            def launch(self, claim):
                self.claims.append(claim)
                return Observation(claim, "running", False)
            def stop(self, claim):
                pass  # Stop delivery alone cannot establish quiescence.
            def observe(self, claim):
                return Observation(claim, "quiescent", True) if self.stopped else None

        with tempfile.TemporaryDirectory() as root:
            supervisor = Supervisor()
            executor = ExecutionService(Path(root) / "executor", supervisor)
            store = JobStore(Path(root) / "jobs" / "state.sqlite")
            owner = Principal("user", "")
            def control(identity, **kwargs):
                return {"authority_id": "fixture", "status": asdict(executor.stop(RemoteIdentity(**identity)))}
            adapter = adapter_type(control)
            request = JobRequest("synthetic", "key", "generation", 1, RunScope("repo"))
            def factory(runner, context, **kwargs):
                identity = store.execution_identity("user", "", context.job_id)
                remote = RemoteIdentity(**asdict(identity))
                executor.advance(remote)
                executor.start(remote, "op", "a" * 64)
                return FakeWorker(runner, context, **kwargs)
            profile = ExecutionProfile("profile", frozenset({"repo"}), lambda *a: result(),
                                       lambda *a: True, adapter.confirm_stopped)
            service = JobService(store, enabled=True, profile=profile, worker_factory=factory)
            try:
                job = service.start_run(owner, request)
                start = time.monotonic()
                service.cancel_run(owner, job["job_id"], generation_id="generation", generation_epoch=1)
                self.assertLess(time.monotonic() - start, .5)
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    with service._lock:
                        if service._active is None:
                            break
                    time.sleep(.01)
                self.assertIsNone(service._active)
                terminal = service.get_run(owner, job["job_id"])
                self.assertEqual(terminal["error_code"], "execution_stop_unconfirmed")
                with self.assertRaises(StoreBusy):
                    service.start_run(owner, replace(request, idempotency_key="next"))
                self.assertFalse(service.reconcile_run(owner, job["job_id"]))
                supervisor.stopped = True
                deadline = time.monotonic() + 3
                reconciled = False
                while not reconciled and time.monotonic() < deadline:
                    reconciled = service.reconcile_run(owner, job["job_id"])
                self.assertTrue(reconciled)
                self.assertEqual(service.get_run(owner, job["job_id"]), terminal)
                self.assertEqual(service.start_run(owner, request), terminal)
                self.assertEqual(len(supervisor.claims), 1)
                remote = RemoteIdentity(**asdict(store.execution_identity("user", "", job["job_id"])))
                self.assertEqual(executor.status(remote).state, "stopped")
                self.assertNotEqual(service.start_run(owner, replace(request, idempotency_key="next",
                                    generation_epoch=2))["job_id"], job["job_id"])
            finally:
                service.close()
                store.close()
                executor.close()
