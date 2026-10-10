"""Durable admission against a synthetic remote execution ledger; no transport."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest

from coding_orchestrator.job_store import JobNotFound, JobStore, StopEvidence, StoreBusy, StoreError
from coding_orchestrator.jobs import ExecutionProfile, JobError, JobRequest, JobService, Principal, RunScope
from test_jobs import FakeWorker, result


class QuarantineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "jobs.sqlite"
        self.store = JobStore(self.path)
        self.addCleanup(lambda: self.store.close())
        self.owner = Principal("owner", "tenant")
        self.request = JobRequest("Synthetic task", "request", "generation", 7, RunScope("fixture"))
        self.workers = []
        self.ledger = {}
        self.observed = []
        self.allowed = True
        self.profile = ExecutionProfile("fixture-profile", frozenset({"fixture"}), lambda *_: result(),
            lambda *_: self.allowed, self.confirm)
        self.service = self.make_service()
        self.addCleanup(lambda: self.service.close())

    def make_service(self):
        return JobService(self.store, profile=self.profile, enabled=True, worker_factory=self.worker)

    def worker(self, runner, context, **kwargs):
        identity = self.store.execution_identity(self.owner.user_id, self.owner.tenant_id, context.job_id)
        self.assertEqual(context.execution_id, identity.execution_id)
        with sqlite3.connect(self.path) as database:
            self.assertEqual(database.execute(
                "SELECT execution_id FROM reservations WHERE job_id=? AND resolved_at IS NULL",
                (context.job_id,)).fetchone(), (identity.execution_id,))
        worker = FakeWorker(runner, context, **kwargs)
        self.workers.append(worker)
        self.ledger[identity] = "running"
        return worker

    def confirm(self, identity):
        self.observed.append(identity)
        return StopEvidence(identity, self.ledger.get(identity) == "stopped")

    def identity(self, job):
        return self.store.execution_identity("owner", "tenant", job["job_id"])

    def terminal(self, job):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            record = self.service.get_run(self.owner, job["job_id"])
            if record["state"] not in {"queued", "running", "cancelling"}:
                return record
            time.sleep(.01)
        self.fail("job did not become terminal")

    def start(self, key="request"):
        return self.service.start_run(self.owner, replace(self.request, idempotency_key=key))

    def interrupt(self):
        job = self.start()
        self.service.cancel_run(self.owner, job["job_id"], generation_id="generation", generation_epoch=7)
        self.assertEqual(self.terminal(job)["error_code"], "execution_stop_unconfirmed")
        return job

    def assert_blocked(self):
        with self.assertRaises(StoreBusy):
            self.start("next")

    def test_reservation_is_committed_before_dispatch_and_not_public(self):
        job = self.start()
        self.assertEqual(len(self.workers), 1)
        self.assertFalse({"execution_id", "user_id", "tenant_id", "reservation"} & job.keys())
        self.assertNotIn("Synthetic task", str(self.identity(job)))

    def test_local_exit_does_not_clear_remote_running_reservation(self):
        for state in ("completed", "failed", "timed_out", "interrupted"):
            with self.subTest(state=state):
                job = self.start(state)
                worker = self.workers[-1]
                worker.outcome = SimpleNamespace(state=state, result=result() if state == "completed" else None,
                                                error_code=None, request_count=0)
                self.assertEqual(self.terminal(job)["state"], "interrupted")
                self.assert_blocked()
                self.ledger[self.identity(job)] = "stopped"
                self.assertTrue(self.service.reconcile_run(self.owner, job["job_id"]))

    def test_reconciliation_preserves_outcome_and_idempotency(self):
        job = self.interrupt()
        before = self.service.get_run(self.owner, job["job_id"])
        self.assertFalse(self.service.reconcile_run(self.owner, job["job_id"]))
        self.assert_blocked()
        self.ledger[self.identity(job)] = "stopped"
        self.assertTrue(self.service.reconcile_run(self.owner, job["job_id"]))
        self.assertTrue(self.service.reconcile_run(self.owner, job["job_id"]))
        self.assertEqual(self.start(), before)
        self.assertEqual(self.service.get_run(self.owner, job["job_id"]), before)
        self.assertNotEqual(self.start("next")["job_id"], job["job_id"])

    def test_restart_preserves_identity_and_quarantine_without_replay(self):
        job = self.interrupt()
        identity = self.identity(job)
        self.service.close()
        self.store.close()
        self.store = JobStore(self.path)
        self.service = self.make_service()
        self.assertEqual(self.identity(job), identity)
        self.assertEqual(len(self.workers), 1)
        self.assert_blocked()
        self.ledger[identity] = "stopped"
        self.assertTrue(self.service.reconcile_run(self.owner, job["job_id"]))
        self.start("next")

    def test_restart_of_active_records_never_replays_or_releases(self):
        for state in ("queued", "running", "cancelling"):
            with self.subTest(state=state):
                job, _ = self.store.admit(user_id="owner", tenant_id="tenant", idempotency_key=state,
                    fingerprint=state, generation_id="generation", generation_epoch=7,
                    deadline_at=100, metadata={"profile_id": "fixture-profile",
                        "repository_alias": "fixture", "task_mode": "read_only"})
                if state != "queued":
                    self.store.transition("owner", "tenant", job["job_id"], {"queued"}, "running")
                if state == "cancelling":
                    self.store.transition("owner", "tenant", job["job_id"], {"running"}, "cancelling")
                identity = self.identity(job)
                self.service.close()
                self.store.close()
                self.store = JobStore(self.path)
                self.service = self.make_service()
                self.assertEqual(self.identity(job), identity)
                self.assertEqual(self.service.get_run(self.owner, job["job_id"])["error_code"],
                                 "restart_interrupted")
                self.assertEqual(self.workers, [])
                self.assert_blocked()
                self.ledger[identity] = "stopped"
                self.assertTrue(self.service.reconcile_run(self.owner, job["job_id"]))

    def test_legacy_records_are_quarantined_and_resolved_tombstones_survive_restart(self):
        job = self.interrupt()
        self.service.close()
        self.store.close()
        with sqlite3.connect(self.path) as database:
            database.execute("DROP TABLE reservations")
        self.store = JobStore(self.path)
        self.service = self.make_service()
        self.assert_blocked()
        identity = self.identity(job)
        self.ledger[identity] = "stopped"
        self.assertTrue(self.service.reconcile_run(self.owner, job["job_id"]))
        self.service.close()
        self.store.close()
        self.store = JobStore(self.path)
        self.service = self.make_service()
        self.assertEqual(self.identity(job), identity)
        self.assertNotEqual(self.start("next")["job_id"], job["job_id"])

    def test_wrong_owner_and_profile_cannot_query_or_release(self):
        job = self.interrupt()
        self.ledger[self.identity(job)] = "stopped"
        count = len(self.observed)
        for owner in (Principal("other", "tenant"), Principal("owner", "other")):
            with self.assertRaises(JobNotFound):
                self.service.reconcile_run(owner, job["job_id"])
        self.service.profile = replace(self.profile, profile_id="replacement")
        with self.assertRaisesRegex(JobError, "scope_not_authorized"):
            self.service.reconcile_run(self.owner, job["job_id"])
        self.service.profile = self.profile
        self.allowed = False
        with self.assertRaisesRegex(JobError, "scope_not_authorized"):
            self.service.reconcile_run(self.owner, job["job_id"])
        self.assertEqual(len(self.observed), count)
        self.allowed = True
        self.assert_blocked()

    def test_unbound_or_mismatched_evidence_never_releases(self):
        job = self.interrupt()
        identity = self.identity(job)
        proofs = [None, True, {"stopped": True}, StopEvidence(identity, False)]
        for field, value in (("job_id", "other"), ("execution_id", "other"),
                ("user_id", "other"), ("tenant_id", "other"), ("generation_id", "other"),
                ("generation_epoch", 8), ("profile_id", "other"),
                ("repository_alias", "other"), ("task_mode", "modification")):
            proofs.append(StopEvidence(replace(identity, **{field: value}), True))
        for proof in proofs:
            self.service.profile = replace(self.profile, confirm_stopped=lambda _, proof=proof: proof)
            self.assertFalse(self.service.reconcile_run(self.owner, job["job_id"]))
            self.assert_blocked()
        def unavailable(_):
            raise RuntimeError("private transport failure")
        self.service.profile = replace(self.profile, confirm_stopped=unavailable)
        self.assertFalse(self.service.reconcile_run(self.owner, job["job_id"]))
        self.assert_blocked()

    def test_boolean_epoch_and_truthy_stop_flags_are_not_evidence(self):
        job = self.interrupt()
        identity = self.identity(job)
        with self.assertRaises(ValueError):
            replace(identity, generation_epoch=True)
        for stopped in (1, "true", object()):
            with self.assertRaises(ValueError):
                StopEvidence(identity, stopped)
        self.assert_blocked()

    def test_active_job_cannot_be_reconciled_even_with_stop_evidence(self):
        job = self.start()
        self.ledger[self.identity(job)] = "stopped"
        self.assertFalse(self.service.reconcile_run(self.owner, job["job_id"]))
        self.assert_blocked()

    def test_disabled_service_cannot_reconcile_and_callers_cannot_supply_evidence(self):
        from coding_orchestrator.dispatch import dispatch_job
        job = self.interrupt()
        self.ledger[self.identity(job)] = "stopped"
        self.service.enabled = False
        with self.assertRaisesRegex(JobError, "preview_jobs_disabled"):
            self.service.reconcile_run(self.owner, job["job_id"])
        self.service.enabled = True
        reply = dispatch_job(self.service, self.owner, {"version": 1, "operation": "reconcile",
            "request": {"job_id": job["job_id"], "stopped": True}})
        self.assertEqual(reply, {"version": 1, "ok": False, "error": "invalid_job_message"})
        self.assert_blocked()

    def test_stale_proof_does_not_clear_subsequent_execution(self):
        first = self.interrupt()
        old = StopEvidence(self.identity(first), True)
        self.ledger[old.identity] = "stopped"
        self.assertTrue(self.service.reconcile_run(self.owner, first["job_id"]))
        second = self.start("second")
        self.service.cancel_run(self.owner, second["job_id"], generation_id="generation", generation_epoch=7)
        self.terminal(second)
        self.service.profile = replace(self.profile, confirm_stopped=lambda _: old)
        self.assertFalse(self.service.reconcile_run(self.owner, second["job_id"]))
        self.assertTrue(self.service.reconcile_run(self.owner, first["job_id"]))
        self.assert_blocked()

    def test_concurrent_duplicate_reconciliation_and_admission(self):
        job = self.interrupt()
        self.ledger[self.identity(job)] = "stopped"
        barrier = threading.Barrier(8)
        def reconcile(_):
            barrier.wait()
            return self.service.reconcile_run(self.owner, job["job_id"])
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(list(pool.map(reconcile, range(8))), [True] * 8)
        barrier = threading.Barrier(8)
        def admit(index):
            barrier.wait()
            try:
                return self.start(f"concurrent-{index}")["job_id"]
            except StoreBusy:
                return None
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(value is not None for value in pool.map(admit, range(8))), 1)

    def test_admission_stays_blocked_while_reconciliation_is_in_flight(self):
        job = self.interrupt()
        entered, release = threading.Event(), threading.Event()
        def confirm(identity):
            entered.set()
            return StopEvidence(identity, release.wait(3))
        self.service.profile = replace(self.profile, confirm_stopped=confirm)
        with ThreadPoolExecutor(max_workers=2) as pool:
            future = pool.submit(self.service.reconcile_run, self.owner, job["job_id"])
            try:
                self.assertTrue(entered.wait(2))
                self.assert_blocked()
                repeated = self.start()
                self.assertEqual(repeated["state"], "interrupted")
            finally:
                release.set()
            self.assertTrue(future.result(timeout=3))
        self.start("next")

    def test_normal_completion_releases_only_its_confirmed_reservation(self):
        job = self.start()
        self.ledger[self.identity(job)] = "stopped"
        self.workers[-1].outcome = SimpleNamespace(state="completed", result=result(), error_code=None, request_count=0)
        self.assertEqual(self.terminal(job)["state"], "completed")
        self.assertNotEqual(self.start("next")["job_id"], job["job_id"])

    def test_failed_reservation_write_rolls_back_job_before_dispatch(self):
        with sqlite3.connect(self.path) as database:
            database.execute("""CREATE TRIGGER reject_reservation AFTER INSERT ON reservations
                BEGIN SELECT RAISE(ABORT, 'synthetic persistence failure'); END""")
        with self.assertRaises(StoreError):
            self.start()
        self.assertEqual(self.workers, [])
        with sqlite3.connect(self.path) as database:
            self.assertEqual(database.execute("SELECT count(*) FROM jobs").fetchone()[0], 0)
            database.execute("DROP TRIGGER reject_reservation")
        self.start()

    def test_failed_resolution_write_keeps_quarantine(self):
        job = self.interrupt()
        self.ledger[self.identity(job)] = "stopped"
        with sqlite3.connect(self.path) as database:
            database.execute("""CREATE TRIGGER reject_resolution AFTER UPDATE ON reservations
                BEGIN SELECT RAISE(ABORT, 'synthetic persistence failure'); END""")
        with self.assertRaises(StoreError):
            self.service.reconcile_run(self.owner, job["job_id"])
        self.assert_blocked()
        with sqlite3.connect(self.path) as database:
            database.execute("DROP TRIGGER reject_resolution")
        self.assertTrue(self.service.reconcile_run(self.owner, job["job_id"]))

    def test_monitor_persistence_failure_cannot_release_reservation(self):
        job = self.start()
        self.ledger[self.identity(job)] = "stopped"
        with sqlite3.connect(self.path) as database:
            database.execute("""CREATE TRIGGER reject_resolution AFTER UPDATE ON reservations
                BEGIN SELECT RAISE(ABORT, 'synthetic persistence failure'); END""")
        self.workers[-1].outcome = SimpleNamespace(state="completed", result=result(), error_code=None, request_count=0)
        self.assertEqual(self.terminal(job)["error_code"], "job_monitor_interrupted")
        self.assert_blocked()

    def test_monitor_poll_failure_keeps_quarantine(self):
        job = self.start()
        def broken():
            raise RuntimeError("private polling failure")
        self.workers[-1].poll = broken
        terminal = self.terminal(job)
        self.assertEqual(terminal["state"], "interrupted")
        self.assertEqual(terminal["error_code"], "job_monitor_interrupted")
        self.assertNotIn("private polling failure", str(terminal))
        self.assert_blocked()

    def test_start_failure_after_possible_dispatch_keeps_reservation(self):
        def ambiguous(runner, context, **kwargs):
            worker = self.worker(runner, context, **kwargs)
            def start():
                raise RuntimeError("reply lost after synthetic dispatch")
            worker.start = start
            return worker
        self.service._worker_factory = ambiguous
        with self.assertRaisesRegex(JobError, "worker_start_failed"):
            self.start()
        self.assertEqual(self.start()["state"], "failed")
        self.assert_blocked()


if __name__ == "__main__":
    unittest.main()
