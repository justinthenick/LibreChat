from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "coding_orchestrator"))
from job_store import JobStore, JobNotFound, StoreBusy, IdempotencyConflict
from review_journal import dispatch, validate_stored_identity

LOWER = "550e8400-e29b-41d4-a716-446655440000"
UPPER = LOWER.upper()
OTHER = "550e8400-e29b-41d4-a716-446655440001"


class JournalIdentityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "private" / "reviews.sqlite"
        self.payload = {"request": {"repository": "fixture", "base": "a"*40,
                        "head": "b"*40, "pullRequest": {"number": 7, "repositoryId": 123}},
                        "model": "fixture-model"}
        self.open()

    def open(self):
        self.store = JobStore(self.path, validate_identity=validate_stored_identity)
        self.addCleanup(self.store.close)

    def restart(self):
        self.store.close()
        self.open()

    def command(self, operation, key=LOWER, principal=None, **extra):
        return dispatch(self.store, {"operation": operation, "id": key,
            "principal": principal or {"userId": "Alice", "tenantId": "Tenant"}, **extra})

    def admit(self, key=LOWER, **extra):
        return self.command("admit", key, payload=self.payload, **extra)

    def test_mixed_case_admission_completion_and_restart_never_replay(self):
        self.assertTrue(self.admit(UPPER)["created"])
        identity = self.store.execution_identity("Alice", "Tenant", LOWER)
        self.assertFalse(self.admit(LOWER)["created"])
        self.assertEqual(self.command("get", UPPER)["record"]["id"], LOWER)
        result = {**self.payload["request"], "model": "fixture-model", "findings": []}
        self.assertEqual(self.command("finish", UPPER, result=result)["record"]["state"], "completed")
        self.assertEqual(self.store.execution_identity("Alice", "Tenant", LOWER), identity)
        self.restart()
        self.assertFalse(self.admit(UPPER)["created"])
        self.assertEqual(self.command("get", LOWER)["record"]["result"], result)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT job_id,idempotency_key,generation_id FROM jobs").fetchall(), [(LOWER, LOWER, LOWER)])
            self.assertEqual(db.execute("SELECT count(*) FROM reservations").fetchone()[0], 1)

    def test_precancel_and_active_cancel_survive_case_changes_and_restart(self):
        self.command("cancel", UPPER)
        self.restart()
        self.assertFalse(self.admit()["created"])
        self.assertEqual(self.command("get", UPPER)["record"]["state"], "cancelled")
        self.assertTrue(self.admit(OTHER)["created"])
        self.command("cancel", OTHER.upper())
        self.restart()
        row = self.command("get", OTHER.upper())["record"]
        self.assertEqual(row["state"], "interrupted")
        self.assertTrue(row["cancelRequested"])
        self.assertFalse(self.admit(OTHER.upper())["created"])
        with self.assertRaises(StoreBusy):
            self.admit("550e8400-e29b-41d4-a716-446655440002")

    def test_exact_principal_request_and_result_identity_preserved(self):
        self.admit(UPPER)
        for principal in [{"userId": "alice", "tenantId": "Tenant"},
                          {"userId": "Alice", "tenantId": "tenant"}, {"userId": "Alice"}]:
            self.assertIsNone(self.command("get", UPPER, principal)["record"])
            for operation in ["cancel", "finish", "admit"]:
                with self.assertRaises(JobNotFound):
                    self.command(operation, UPPER, principal, payload=self.payload)
        for field, value in [("base", "c"*40), ("head", "d"*40),
                              ("repository", "other"), ("pullRequest", {"number": 8, "repositoryId": 123})]:
            changed = {**self.payload, "request": {**self.payload["request"], field: value}}
            with self.assertRaises(IdempotencyConflict):
                self.command("admit", LOWER, payload=changed)
            with self.assertRaises(ValueError):
                self.command("finish", UPPER, result={**changed["request"], "model": "fixture-model"})
        with self.assertRaises(ValueError):
            self.command("finish", UPPER, result={**self.payload["request"], "model": "other"})

    def test_invalid_ids_do_not_mutate_store(self):
        for key in [LOWER.replace("-", ""), "{"+LOWER+"}", "not-a-uuid", 1]:
            for operation in ["get", "admit", "cancel", "finish"]:
                with self.assertRaises(ValueError):
                    self.command(operation, key, payload=self.payload)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM jobs").fetchone()[0], 0)

    def test_noncanonical_legacy_rows_fail_closed_without_rewriting_quarantine(self):
        self.admit()
        self.store.close()
        for table, column in [("jobs", "job_id"), ("jobs", "idempotency_key"),
                              ("jobs", "generation_id"), ("reservations", "job_id")]:
            with self.subTest(table=table, column=column):
                with sqlite3.connect(self.path) as db:
                    db.execute(f"UPDATE {table} SET {column}=?", (UPPER,))
                    before = list(db.iterdump())
                with self.assertRaises(ValueError):
                    JobStore(self.path, validate_identity=validate_stored_identity)
                with sqlite3.connect(self.path) as db:
                    self.assertEqual(list(db.iterdump()), before)
                    db.execute(f"UPDATE {table} SET {column}=?", (LOWER,))


if __name__ == "__main__":
    unittest.main()
