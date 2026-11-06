from pathlib import Path
import sqlite3
import tempfile
import unittest

from coding_orchestrator.job_store import JobStore, JobNotFound, StoreBusy, StopEvidence


class ReviewStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "private" / "reviews.sqlite"
        self.now = 1000.0
        self.store = JobStore(self.path, clock=lambda: self.now)
        self.addCleanup(self.store.close)
        self.payload = {"request": {"repository": "fixture", "base": "a"*40, "head": "b"*40,
                         "pullRequest": {"number": 7, "repositoryId": 123}}, "model": "fixture-model"}

    def admit(self, key="one", **options):
        return self.store.admit(user_id="alice", tenant_id="tenant-a", job_id=key,
            idempotency_key=key, fingerprint=key, generation_id=key, generation_epoch=0,
            deadline_at=1200, request=self.payload, **options)

    def reopen(self):
        self.store.close()
        self.store = JobStore(self.path, clock=lambda: self.now)
        self.addCleanup(self.store.close)

    def test_external_id_and_full_identity_commit_atomically_and_survive_restart(self):
        row, created = self.admit()
        self.assertTrue(created)
        with sqlite3.connect(self.path) as database:
            stored = database.execute("SELECT job_id,request FROM jobs").fetchone()
        self.assertEqual(stored[0], "one")
        self.assertIn('"repositoryId":123', stored[1])
        self.reopen()
        recovered = self.store.get("alice", "tenant-a", "one")
        self.assertEqual(recovered["request"], self.payload)
        self.assertEqual(recovered["state"], "interrupted")
        self.assertFalse(self.admit()[1])
        with self.assertRaises(StoreBusy):
            self.admit("two")
        for user, tenant in [("bob", "tenant-a"), ("alice", "tenant-b")]:
            with self.assertRaises(JobNotFound):
                self.store.get(user, tenant, "one")

    def test_cancellation_tombstone_survives_restart_without_reserving_execution(self):
        self.store.cancel_external("alice", "tenant-a", "one")
        with self.assertRaises(JobNotFound):
            self.store.cancel_external("bob", "tenant-a", "one")
        self.reopen()
        row, created = self.admit()
        self.assertFalse(created)
        self.assertEqual(row["state"], "cancelled")
        self.assertIsNone(row["request"])
        with sqlite3.connect(self.path) as database:
            self.assertEqual(database.execute("SELECT count(*) FROM reservations").fetchone()[0], 0)
        self.assertTrue(self.admit("two")[1])

    def test_interrupted_cancellation_never_releases_unconfirmed_execution(self):
        self.admit()
        self.store.cancel_external("alice", "tenant-a", "one")
        self.reopen()
        self.assertEqual(self.store.get("alice", "tenant-a", "one")["cancel_requested"], 1)
        self.store.cancel_external("alice", "tenant-a", "one")
        self.store.discard_terminal_results(self.now)
        with self.assertRaises(StoreBusy):
            self.admit("two")

    def complete(self, key):
        self.store.transition("alice", "tenant-a", key, {"queued"}, "running")
        identity = self.store.execution_identity("alice", "tenant-a", key)
        self.store.transition("alice", "tenant-a", key, {"running"}, "completed",
            result={"findings": ["fixture"]}, stop_evidence=StopEvidence(identity, True))

    def test_result_expiry_never_removes_request_or_replay_fence(self):
        self.admit()
        self.complete("one")
        self.now += 601
        self.store.discard_terminal_results(self.now-600)
        self.reopen()
        row, created = self.admit()
        self.assertFalse(created)
        self.assertIsNone(row["result"])
        self.assertEqual(row["request"], self.payload)
        self.assertTrue(self.admit("two")[1])

    def test_capacity_fails_closed_without_evicting_history(self):
        self.store.cancel_external("alice", "tenant-a", "one", max_records=2)
        self.store.cancel_external("alice", "tenant-a", "two", max_records=2)
        with self.assertRaises(StoreBusy):
            self.store.cancel_external("alice", "tenant-a", "three", max_records=2)
        with self.assertRaises(StoreBusy):
            self.admit("three", max_records=2)
        self.assertFalse(self.admit()[1])

    def test_result_capacity_releases_only_after_payload_expiry(self):
        self.admit(max_results=1)
        self.complete("one")
        with self.assertRaises(StoreBusy):
            self.admit("two", max_results=1)
        self.store.discard_terminal_results(self.now)
        self.assertTrue(self.admit("two", max_results=1)[1])

    def test_existing_database_migrates_without_losing_identity_or_quarantine(self):
        self.admit()
        self.store.close()
        with sqlite3.connect(self.path) as database:
            database.execute("ALTER TABLE jobs DROP COLUMN request")
            database.execute("ALTER TABLE jobs DROP COLUMN cancel_requested")
        self.reopen()
        row = self.store.get("alice", "tenant-a", "one")
        self.assertEqual(row["fingerprint"], "one")
        self.assertEqual(row["state"], "interrupted")
        self.assertIsNone(row["request"])
        with self.assertRaises(StoreBusy):
            self.admit("two")


if __name__ == "__main__":
    unittest.main()
