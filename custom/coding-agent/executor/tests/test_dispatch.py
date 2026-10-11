"""Real durable admission and disposable workspaces; synthetic stop authority only."""
from dataclasses import replace
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from coding_executor.dispatch import FencedWorkspace
from coding_executor.executions import ExecutionService, ExecutionIdentity, ExecutionConflict, ExecutionBusy, Observation
from coding_executor.workspaces import WorkspaceManager


class Authority:
    authority_id = "fixture-authority"
    proof = None

    def launch(self, claim):
        return Observation(claim, "running", False)

    def stop(self, claim):
        pass

    def observe(self, claim):
        return self.proof


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.authority = Authority()
        self.ledger = ExecutionService(self.root / "ledger", self.authority)
        self.addCleanup(lambda: self.ledger.close())
        self.identity = ExecutionIdentity("job", "execution", "owner", "tenant", "generation", 1,
                                          "profile", "demo", "read_only")
        self.ledger.advance(self.identity)
        self.claim = self.ledger.start(self.identity, "job-worker", "a" * 64).operations[0].claim

    def admit(self, maximum=4, timeout=3):
        self.ledger.configure_dispatch(self.claim, max_requests=maximum, timeout_seconds=timeout)

    def call(self, action=lambda _: "done", action_id="one", digest="b" * 64, claim=None):
        return self.ledger.dispatch(claim or self.claim, action_id, digest, action)

    def test_commit_precedes_action_and_replay_never_reexecutes(self):
        self.admit()
        seen = []
        def action(_):
            with sqlite3.connect(self.root / "ledger" / "executions.sqlite3") as db:
                seen.append(db.execute("SELECT state FROM dispatch_actions").fetchone()[0])
            return "result"
        self.assertEqual(self.call(action), "result")
        for digest in ("b" * 64, "c" * 64):
            with self.assertRaises(ExecutionConflict):
                self.call(action, digest=digest)
        self.assertEqual(seen, ["unknown"])
        self.assertNotEqual(self.ledger.stop(self.identity).state, "stopped")

    def test_exact_claim_and_identity_required(self):
        self.admit()
        changes = [{"attempt_id": "old"}, {"authority_id": "other"}, {"request_sha256": "d" * 64},
                   {"operation_id": "other"}]
        for field in ("user_id", "tenant_id", "generation_id", "profile_id", "repository_alias", "execution_id"):
            changes.append({"identity": replace(self.identity, **{field: "other"})})
        changes.append({"identity": replace(self.identity, generation_epoch=2)})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ExecutionConflict):
                self.call(claim=replace(self.claim, **change))

    def test_request_limit_and_deadline_cannot_be_renewed(self):
        self.admit(maximum=1)
        self.call()
        self.admit(maximum=1)
        with self.assertRaises(ExecutionConflict):
            self.call(action_id="two")
        with self.assertRaises(ExecutionConflict):
            self.admit(maximum=2)

    def test_commit_failure_never_starts_action(self):
        self.admit()
        seen = []
        self.ledger._db.set_authorizer(lambda code, value, *rest:
            sqlite3.SQLITE_DENY if code == sqlite3.SQLITE_TRANSACTION and value == "COMMIT" else sqlite3.SQLITE_OK)
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                self.call(lambda _: seen.append(True))
        finally:
            self.ledger._db.set_authorizer(None)
        self.assertEqual(seen, [])
        self.assertEqual(self.ledger._active_actions, set())

    def test_identical_admission_does_not_extend_original_deadline(self):
        with patch("coding_executor.executions.time.monotonic", return_value=100):
            self.admit(timeout=10)
        with patch("coding_executor.executions.time.monotonic", return_value=105):
            self.admit(timeout=10)
        with patch("coding_executor.executions.time.monotonic", return_value=111):
            with self.assertRaises(ExecutionConflict):
                self.call()

    def test_absolute_deadline_includes_time_before_admission_and_never_renews(self):
        with patch("coding_executor.executions.time.monotonic", return_value=100):
            self.ledger.configure_dispatch(self.claim, max_requests=4, timeout_seconds=30,
                                           deadline_monotonic=110)
        with patch("coding_executor.executions.time.monotonic", return_value=105):
            self.ledger.configure_dispatch(self.claim, max_requests=4, timeout_seconds=30,
                                           deadline_monotonic=135)
        with patch("coding_executor.executions.time.monotonic", return_value=111):
            with self.assertRaises(ExecutionConflict):
                self.call()

    def test_stop_seals_without_waiting_for_action_and_needs_exact_proof(self):
        self.admit()
        entered, release = threading.Event(), threading.Event()
        result = []
        def action(_):
            entered.set()
            release.wait(2)
            return "done"
        thread = threading.Thread(target=lambda: result.append(self.call(action)))
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            with self.assertRaises(ExecutionConflict):
                self.call()
            self.authority.proof = Observation(self.claim, "quiescent", True)
            started = time.monotonic()
            self.assertNotEqual(self.ledger.stop(self.identity).state, "stopped")
            self.assertLess(time.monotonic() - started, .5)
            with self.assertRaises(ExecutionConflict):
                self.call(action_id="late")
        finally:
            release.set()
            thread.join(2)
        self.assertEqual(result, ["done"])
        self.authority.proof = Observation(replace(self.claim, attempt_id="wrong"), "quiescent", True)
        self.assertEqual(self.ledger.reconcile(self.identity).state, "unknown")
        self.authority.proof = Observation(self.claim, "quiescent", True)
        self.assertEqual(self.ledger.reconcile(self.identity).state, "stopped")

    def test_stop_proof_resolves_quarantine_without_claiming_action_success(self):
        self.admit()
        def fail(_):
            raise RuntimeError("unknown result")
        with self.assertRaises(ExecutionConflict):
            self.call(fail)
        self.authority.proof = Observation(self.claim, "quiescent", True)
        self.assertEqual(self.ledger.stop(self.identity).state, "stopped")
        row = self.ledger._db.execute("SELECT state FROM dispatch_actions").fetchone()
        self.assertEqual(row["state"], "resolved_unknown")

    def test_deadline_returns_unknown_and_tracks_late_work(self):
        self.admit(timeout=.05)
        entered, release = threading.Event(), threading.Event()
        def action(_):
            entered.set()
            release.wait(2)
        started = time.monotonic()
        try:
            with self.assertRaisesRegex(ExecutionConflict, "outcome unknown"):
                self.call(action)
            self.assertTrue(entered.is_set())
            self.assertLess(time.monotonic() - started, .5)
            self.authority.proof = Observation(self.claim, "quiescent", True)
            self.assertNotEqual(self.ledger.stop(self.identity).state, "stopped")
            with self.assertRaises(ExecutionConflict):
                self.call(action_id="late")
        finally:
            release.set()
            for _ in range(100):
                if not self.ledger._active_actions:
                    break
                time.sleep(.01)
        self.authority.proof = None
        self.assertEqual(self.ledger.reconcile(self.identity).state, "unknown")

    def test_uncertain_result_and_restart_do_not_replay(self):
        self.admit()
        def fail(_):
            raise TimeoutError("synthetic private detail")
        with self.assertRaisesRegex(ExecutionConflict, "outcome unknown"):
            self.call(fail)
        self.ledger.close()
        self.ledger = ExecutionService(self.root / "ledger", self.authority)
        for action_id in ("one", "late"):
            with self.assertRaises(ExecutionConflict):
                self.call(action_id=action_id)
        self.assertEqual(self.ledger.reconcile(self.identity).state, "unknown")

    def test_advance_seals_old_claim_and_delayed_dispatch(self):
        self.admit()
        newer = replace(self.identity, job_id="new", execution_id="new", generation_epoch=2)
        self.ledger.advance(newer)
        with self.assertRaises(ExecutionConflict):
            self.call()
        with self.assertRaises(ExecutionBusy):
            self.ledger.start(newer, "job-worker", "a" * 64)

    def test_workspace_default_off_and_binding_reuses_real_path_checks(self):
        repositories, tasks = self.root / "repos", self.root / "tasks"
        repositories.mkdir(); tasks.mkdir()
        repository = repositories / "demo"
        repository.mkdir()
        for args in (("init", "-b", "main"), ("config", "user.name", "Fixture"),
                     ("config", "user.email", "fixture@example.invalid")):
            subprocess.run(["git", *args], cwd=repository, check=True, capture_output=True)
        (repository / "example.txt").write_text("fixture\n")
        for args in (("add", "."), ("commit", "-m", "fixture")):
            subprocess.run(["git", *args], cwd=repository, check=True, capture_output=True)
        manager = WorkspaceManager(repositories, tasks)
        kwargs = {"authorize": lambda identity: identity == self.identity}
        dormant = FencedWorkspace(self.ledger, manager, **kwargs)
        with self.assertRaises(ExecutionConflict):
            dormant.admit(self.claim, max_requests=4, timeout_seconds=3)
        dispatch = FencedWorkspace(self.ledger, manager, **kwargs, enabled=True, testing_uncontained=True)
        dispatch.admit(self.claim, max_requests=4, timeout_seconds=3)
        created = dispatch.dispatch(self.claim, "create", "create_task", {})
        self.assertEqual(self.ledger.task_for(self.claim), created["task_id"])
        result = dispatch.dispatch(self.claim, "read", "read_file", {"path": "example.txt"})
        self.assertIn("fixture", result)
        for operation, arguments in (("read_file", {"path": "example.txt", "task_id": "foreign"}),
                                     ("run_check", {"command": "anything"}), ("apply_patch", {"patch": "x"})):
            with self.assertRaises(ValueError):
                dispatch.dispatch(self.claim, "invalid", operation, arguments)
        with self.assertRaises(ExecutionConflict):
            dispatch.dispatch(self.claim, "escape", "read_file", {"path": "../outside"})
        self.assertEqual((repository / "example.txt").read_text(), "fixture\n")


if __name__ == "__main__":
    unittest.main()
