"""Offline contract tests: SQLite is real; only the supervisor is synthetic."""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path


class ExecutionTests(unittest.TestCase):
    def test_lost_launch_reply_is_durable_and_never_replayed(self):
        try:
            contract = importlib.import_module("coding_executor.executions")
        except ModuleNotFoundError:
            self.fail("durable executor execution contract is missing")
        identity = contract.ExecutionIdentity("job", "execution", "user", "tenant", "generation", 1,
                                              "profile", "repo", "modification")

        class Supervisor:
            authority_id = "synthetic-supervisor"
            launches = 0

            def launch(self, claim):
                self.launches += 1
                raise TimeoutError("reply lost after dispatch")

            def observe(self, claim):
                return None

            def stop(self, claim):
                return None

        supervisor = Supervisor()
        with tempfile.TemporaryDirectory() as root:
            ledger = contract.ExecutionService(Path(root) / "ledger", supervisor)
            try:
                ledger.advance(identity)
                first = ledger.start(identity, "operation", "a" * 64)
                self.assertEqual(first.state, "unknown")
                self.assertEqual(ledger.start(identity, "operation", "a" * 64), first)
            finally:
                ledger.close()
            ledger = contract.ExecutionService(Path(root) / "ledger", supervisor)
            try:
                self.assertEqual(ledger.start(identity, "operation", "a" * 64).operations,
                                 first.operations)
                self.assertEqual(supervisor.launches, 1)
                self.assertEqual(ledger.status(identity).state, "unknown")
            finally:
                ledger.close()


class LedgerTests(unittest.TestCase):
    def setUp(self):
        try:
            self.c = importlib.import_module("coding_executor.executions")
        except ModuleNotFoundError:
            self.fail("durable executor execution contract is missing")
        self.root = tempfile.TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        self.path = Path(self.root.name) / "ledger"
        self.identity = self.c.ExecutionIdentity("job", "execution", "user", "tenant", "generation",
                                                 1, "profile", "repo", "modification")
        contract = self.c

        class Supervisor:
            authority_id = "authority"

            def __init__(self):
                self.launches = []
                self.stops = []
                self.proof = None
                self.on_launch = None
                self.on_stop = None

            def launch(self, claim):
                self.launches.append(claim)
                if self.on_launch:
                    self.on_launch(claim)
                return contract.Observation(claim, "running", False)

            def stop(self, claim):
                self.stops.append(claim)
                if self.on_stop:
                    self.on_stop(claim)

            def observe(self, claim):
                return self.proof

        self.supervisor = Supervisor()
        self.service = self.c.ExecutionService(self.path, self.supervisor)
        self.addCleanup(lambda: self.service.close())

    def start(self):
        self.service.advance(self.identity)
        return self.service.start(self.identity, "op", "a" * 64)

    def stopped_proof(self):
        return self.c.Observation(self.supervisor.launches[-1], "quiescent", True)

    def restart(self, supervisor=None):
        self.service.close()
        self.service = self.c.ExecutionService(self.path, supervisor or self.supervisor)

    def test_missing_record_does_not_prove_stop(self):
        self.assertEqual(self.service.status(self.identity).state, "unknown")
        self.assertEqual(self.service.reconcile(self.identity).state, "unknown")

    def test_claim_is_committed_before_launch_and_status_can_reenter(self):
        def check(claim):
            with sqlite3.connect(self.path / "executions.sqlite3") as db:
                self.assertEqual(db.execute("SELECT attempt_id FROM operations").fetchone()[0], claim.attempt_id)
            self.assertEqual(self.service.status(self.identity).state, "unknown")
        self.supervisor.on_launch = check
        self.assertEqual(self.start().state, "running")

    def test_stop_before_start_is_a_durable_tombstone(self):
        self.assertEqual(self.service.stop(self.identity).state, "stopped")
        self.restart()
        self.service.advance(self.identity)
        with self.assertRaises(self.c.ExecutionConflict):
            self.service.start(self.identity, "op", "a" * 64)
        self.assertEqual(self.supervisor.launches, [])

    def test_completed_operation_does_not_release_open_execution(self):
        self.start()
        self.supervisor.proof = self.stopped_proof()
        self.assertEqual(self.service.reconcile(self.identity).state, "open")
        self.assertEqual(self.service.start(self.identity, "op2", "b" * 64).state, "running")
        self.assertEqual(len(self.supervisor.launches), 2)
        self.assertNotEqual(self.service.stop(self.identity).state, "stopped")
        self.supervisor.proof = self.stopped_proof()
        self.assertEqual(self.service.reconcile(self.identity).state, "stopped")

    def test_replay_after_seal_never_dispatches_and_digest_conflicts(self):
        self.start()
        self.supervisor.proof = self.stopped_proof()
        expected = self.service.stop(self.identity)
        self.assertEqual(expected.state, "stopped")
        self.assertEqual(self.service.start(self.identity, "op", "a" * 64), expected)
        with self.assertRaises(self.c.ExecutionConflict):
            self.service.start(self.identity, "op", "b" * 64)
        self.assertEqual(len(self.supervisor.launches), 1)

    def test_mismatched_or_unfenced_proof_cannot_release(self):
        self.start()
        self.service.stop(self.identity)
        proof = self.stopped_proof()
        wrong_identities = [replace(self.identity, **{key: value}) for key, value in
                            [("job_id", "other"), ("execution_id", "other"), ("user_id", "other"),
                             ("tenant_id", "other"), ("generation_id", "other"), ("generation_epoch", 2),
                             ("profile_id", "other"), ("repository_alias", "other"), ("task_mode", "read_only")]]
        bad = [None, True, replace(proof, fenced=False), replace(proof, fenced=1),
               replace(proof, state="running"), replace(proof, claim=replace(proof.claim, attempt_id="old")),
               replace(proof, claim=replace(proof.claim, authority_id="other")),
               replace(proof, claim=replace(proof.claim, operation_id="other")),
               replace(proof, claim=replace(proof.claim, request_sha256="b" * 64))]
        bad.extend(replace(proof, claim=replace(proof.claim, identity=value)) for value in wrong_identities)
        for value in bad:
            with self.subTest(value=value):
                self.supervisor.proof = value
                self.assertNotEqual(self.service.reconcile(self.identity).state, "stopped")
        self.supervisor.proof = proof
        self.assertEqual(self.service.reconcile(self.identity).state, "stopped")
        self.restart()
        self.assertEqual(self.service.status(self.identity).state, "stopped")

    def test_restart_seals_running_record_and_never_calls_supervisor(self):
        self.start()
        self.restart()
        status = self.service.status(self.identity)
        self.assertTrue(status.sealed)
        self.assertEqual(status.state, "unknown")
        self.assertEqual(len(self.supervisor.launches), 1)
        self.assertEqual(self.supervisor.stops, [])
        with self.assertRaises(self.c.ExecutionConflict):
            self.service.start(self.identity, "new", "b" * 64)

    def test_changed_supervisor_authority_cannot_resolve_old_claim(self):
        self.start()
        self.supervisor.proof = self.stopped_proof()
        self.supervisor.authority_id = "replacement"
        self.restart()
        self.assertEqual(self.service.stop(self.identity).state, "unknown")
        self.assertEqual(self.supervisor.stops, [])

    def test_new_generation_fences_old_even_while_dispatch_is_busy(self):
        self.start()
        newer = replace(self.identity, job_id="job2", execution_id="execution2", generation_epoch=2)
        self.service.advance(newer)
        self.assertTrue(self.service.status(self.identity).sealed)
        with self.assertRaises(self.c.ExecutionBusy):
            self.service.start(newer, "new", "b" * 64)
        with self.assertRaises(self.c.ExecutionConflict):
            self.service.start(self.identity, "late", "c" * 64)
        with self.assertRaises(self.c.ExecutionConflict):
            self.service.advance(replace(newer, execution_id="collision"))
        with self.assertRaises(self.c.ExecutionConflict):
            self.service.advance(replace(self.identity, execution_id="stale"))
        self.supervisor.proof = self.stopped_proof()
        self.assertEqual(self.service.stop(self.identity).state, "stopped")
        self.assertEqual(self.service.start(newer, "new", "b" * 64).state, "running")

    def test_fences_are_scoped_to_owner_and_generation_lineage(self):
        self.service.advance(self.identity)
        for key in ("user_id", "tenant_id", "generation_id", "profile_id", "repository_alias", "task_mode"):
            other = replace(self.identity, execution_id=key, job_id=key, generation_epoch=100,
                            **{key: "read_only" if key == "task_mode" else "other"})
            self.service.advance(other)
        self.assertFalse(self.service.status(self.identity).sealed)

    def test_identity_mismatch_is_rejected_without_observing_or_stopping(self):
        self.start()
        for call in (self.service.status, self.service.stop, self.service.reconcile, self.service.advance):
            with self.assertRaises(self.c.ExecutionConflict):
                call(replace(self.identity, user_id="attacker"))
        self.assertEqual(self.supervisor.stops, [])

    def test_failed_claim_persistence_causes_no_launch(self):
        self.service.advance(self.identity)
        with sqlite3.connect(self.path / "executions.sqlite3") as db:
            db.execute("CREATE TRIGGER deny_claim BEFORE INSERT ON operations BEGIN SELECT RAISE(ABORT, 'disk'); END")
        with self.assertRaises(sqlite3.DatabaseError):
            self.service.start(self.identity, "op", "a" * 64)
        self.assertEqual(self.supervisor.launches, [])

    def test_failed_seal_persistence_causes_no_stop(self):
        self.start()
        with sqlite3.connect(self.path / "executions.sqlite3") as db:
            db.execute("CREATE TRIGGER deny_seal BEFORE UPDATE ON executions BEGIN SELECT RAISE(ABORT, 'disk'); END")
        with self.assertRaises(sqlite3.DatabaseError):
            self.service.stop(self.identity)
        self.assertEqual(self.supervisor.stops, [])

    def test_failed_proof_persistence_never_reports_stopped(self):
        self.start()
        self.service.stop(self.identity)
        self.supervisor.proof = self.stopped_proof()
        with sqlite3.connect(self.path / "executions.sqlite3") as db:
            db.execute("CREATE TRIGGER deny_proof BEFORE UPDATE ON operations BEGIN SELECT RAISE(ABORT, 'disk'); END")
        with self.assertRaises(sqlite3.DatabaseError):
            self.service.reconcile(self.identity)
        self.assertNotEqual(self.service.status(self.identity).state, "stopped")

    def test_failed_stop_retains_seal(self):
        self.start()
        def fail(claim):
            self.assertTrue(self.service.status(self.identity).sealed)
            raise TimeoutError("stop reply lost")
        self.supervisor.on_stop = fail
        self.assertNotEqual(self.service.stop(self.identity).state, "stopped")
        with self.assertRaises(self.c.ExecutionConflict):
            self.service.start(self.identity, "new", "b" * 64)

    def test_stop_serializes_with_launch_and_seal_rejects_late_operations(self):
        entered, release = threading.Event(), threading.Event()
        self.supervisor.on_launch = lambda claim: (entered.set(), release.wait(5))
        self.service.advance(self.identity)
        errors = []
        def start():
            try:
                self.service.start(self.identity, "op", "a" * 64)
            except Exception as error:
                errors.append(error)
        starter = threading.Thread(target=start)
        starter.start()
        self.assertTrue(entered.wait(5))
        result = []
        stopper = threading.Thread(target=lambda: result.append(self.service.stop(self.identity)))
        stopper.start()
        release.set()
        starter.join(5)
        stopper.join(5)
        self.assertFalse(starter.is_alive() or stopper.is_alive())
        self.assertEqual(errors, [])
        self.assertTrue(result[0].sealed)
        self.assertEqual(self.supervisor.stops, self.supervisor.launches)
        with self.assertRaises(self.c.ExecutionConflict):
            self.service.start(self.identity, "delayed", "b" * 64)

    def test_exclusive_store_owner_and_private_paths(self):
        with self.assertRaises(self.c.ExecutionBusy):
            self.c.ExecutionService(self.path, self.supervisor)
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o700)
        self.assertEqual(os.stat(self.path / "executions.sqlite3").st_mode & 0o777, 0o600)
        link = Path(self.root.name) / "alias"
        link.symlink_to(self.path, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.c.ExecutionService(link, self.supervisor)

    def test_orchestrator_identity_vocabulary_roundtrips_without_translation(self):
        from dataclasses import asdict
        fixture = {"job_id": "job:123", "execution_id": "execution:123", "user_id": "user@example.com",
                   "tenant_id": "", "generation_id": "preview:abc", "generation_epoch": 1,
                   "profile_id": "profile", "repository_alias": "repo", "task_mode": "modification"}
        identity = self.c.ExecutionIdentity(**fixture)
        self.assertEqual(asdict(self.service.stop(identity).identity), fixture)
        readonly = replace(identity, execution_id="readonly", generation_id="readonly", task_mode="read_only")
        self.assertEqual(self.service.stop(readonly).state, "stopped")

    def test_commit_failure_prevents_dispatch(self):
        self.service.advance(self.identity)
        self.service._db.set_authorizer(lambda action, value, *unused:
                                        sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_TRANSACTION and value == "COMMIT"
                                        else sqlite3.SQLITE_OK)
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                self.service.start(self.identity, "op", "a" * 64)
        finally:
            self.service._db.set_authorizer(None)
        self.assertEqual(self.service.status(self.identity).operations, ())
        self.assertEqual(self.supervisor.launches, [])

    def test_supervisor_fence_rejects_delivery_after_lost_launch_reply(self):
        queued, fenced, executed = [], set(), []
        def queue(claim):
            queued.append(claim)
            raise TimeoutError("queued but reply lost")
        def fence(claim):
            fenced.add(claim.attempt_id)
            self.supervisor.proof = self.c.Observation(claim, "quiescent", True)
        self.supervisor.on_launch, self.supervisor.on_stop = queue, fence
        self.assertEqual(self.start().state, "unknown")
        self.assertEqual(self.service.stop(self.identity).state, "stopped")
        for claim in queued:
            if claim.attempt_id not in fenced:
                executed.append(claim)
        self.assertEqual(executed, [])
        self.assertEqual(self.service.status(self.identity).state, "stopped")

    def test_callback_mutation_reentry_is_rejected(self):
        rejected = []
        def reenter(claim):
            for call in (lambda: self.service.stop(self.identity), self.service.close):
                try:
                    call()
                except RuntimeError:
                    rejected.append(True)
        self.supervisor.on_launch = reenter
        self.assertEqual(self.start().state, "running")
        self.assertEqual(rejected, [True, True])
        self.assertFalse(self.service.status(self.identity).sealed)

    def test_planted_sqlite_sidecar_symlink_is_rejected(self):
        self.service.close()
        sentinel = Path(self.root.name) / "sentinel"
        sentinel.write_text("preserve")
        (self.path / "executions.sqlite3-journal").symlink_to(sentinel)
        with self.assertRaises((ValueError, OSError)):
            self.c.ExecutionService(self.path, self.supervisor)
        self.assertEqual(sentinel.read_text(), "preserve")

    def test_unknown_observation_invalidates_previous_running_status(self):
        self.start()
        self.assertEqual(self.service.reconcile(self.identity).state, "unknown")

    def test_forked_instance_cannot_read_or_mutate_ledger(self):
        self.start()
        child = os.fork()
        if child == 0:
            try:
                self.service.status(self.identity)
            except RuntimeError:
                os._exit(0)
            os._exit(1)
        _, status = os.waitpid(child, 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        self.assertEqual(self.service.status(self.identity).state, "running")

    def test_operation_budget_bounds_status_and_blocks_dispatch(self):
        self.service.advance(self.identity)
        for number in range(64):
            self.service.start(self.identity, f"op{number}", "a" * 64)
            self.supervisor.proof = self.stopped_proof()
            self.service.reconcile(self.identity)
        with self.assertRaises(self.c.ExecutionConflict):
            self.service.start(self.identity, "overflow", "a" * 64)
        self.assertEqual(len(self.service.status(self.identity).operations), 64)
        self.assertEqual(len(self.supervisor.launches), 64)

    def test_invalid_request_identity_never_dispatches(self):
        for change in ({"generation_epoch": True}, {"generation_epoch": -1},
                       {"user_id": ""}, {"task_mode": "shell"}):
            with self.assertRaises(ValueError):
                replace(self.identity, **change)
        self.service.advance(self.identity)
        for operation, digest in (("../bad", "a" * 64), ("op", "A" * 64), ("op", "prompt")):
            with self.assertRaises(ValueError):
                self.service.start(self.identity, operation, digest)
        self.assertEqual(self.supervisor.launches, [])


if __name__ == "__main__":
    unittest.main()
