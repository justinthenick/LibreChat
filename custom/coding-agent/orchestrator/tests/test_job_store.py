from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from coding_orchestrator.job_store import (
    IdempotencyConflict, JobNotFound, JobStore, MAX_JSON_BYTES, StopEvidence, StoreBusy, StoreError,
)


class JobStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "private" / "jobs.sqlite"
        self.now = 100.0
        self.store = JobStore(self.path, clock=lambda: self.now)
        self.addCleanup(self.store.close)

    def admit(self, **overrides):
        arguments = dict(user_id="alice", tenant_id="tenant-a", idempotency_key="key",
                         fingerprint="fingerprint", generation_id="generation",
                         generation_epoch=1, deadline_at=400.0)
        return self.store.admit(**(arguments | overrides))

    def transition(self, record, expected, state, **updates):
        return self.store.transition(record["user_id"], record["tenant_id"],
                                     record["job_id"], expected, state, **updates)

    def get(self, record):
        return self.store.get(record["user_id"], record["tenant_id"], record["job_id"])

    def confirm_stop(self, record):
        owner = (record["user_id"], record["tenant_id"], record["job_id"])
        identity = self.store.execution_identity(*owner)
        self.assertTrue(self.store.resolve_execution(*owner, StopEvidence(identity, True)))

    def test_admission_is_durable_and_idempotent_even_after_completion(self):
        record, created = self.admit()
        self.assertTrue(created)
        self.assertEqual(record["state"], "queued")
        with sqlite3.connect(self.path) as database:
            persisted = database.execute("SELECT job_id, state FROM jobs").fetchone()
        self.assertEqual(persisted, (record["job_id"], "queued"))
        repeated, created = self.admit()
        self.assertFalse(created)
        self.assertEqual(repeated, record)
        self.assertTrue(self.transition(record, {"queued"}, "running"))
        self.assertTrue(self.transition(record, {"running"}, "completed", result={"ok": True}))
        repeated, created = self.admit()
        self.assertFalse(created)
        self.assertEqual(repeated["state"], "completed")
        self.assertEqual(repeated["job_id"], record["job_id"])
        with self.assertRaises(IdempotencyConflict):
            self.admit(fingerprint="changed")

    def test_owner_and_tenant_scoped_keys_and_uniform_not_found(self):
        first, _ = self.admit()
        for user, tenant, job in (
            ("bob", "tenant-a", first["job_id"]),
            ("alice", "tenant-b", first["job_id"]),
            ("alice", "tenant-a", "missing"),
        ):
            for operation in (
                lambda: self.store.get(user, tenant, job),
                lambda: self.store.transition(user, tenant, job, {"queued"}, "cancelled"),
                lambda: self.store.update_progress(user, tenant, job, request_count=1),
            ):
                with self.assertRaisesRegex(JobNotFound, "^Job not found$"):
                    operation()
        self.assertTrue(self.transition(first, {"queued"}, "cancelled"))
        self.confirm_stop(first)
        second, created = self.admit(user_id="bob")
        self.assertTrue(created)
        self.assertTrue(self.transition(second, {"queued"}, "cancelled"))
        self.confirm_stop(second)
        third, created = self.admit(tenant_id="tenant-b")
        self.assertTrue(created)
        self.assertEqual(len({first["job_id"], second["job_id"], third["job_id"]}), 3)

    def test_one_slot_includes_cancelling_and_all_owners(self):
        record, _ = self.admit(tenant_id="")
        for state in ("queued", "running", "cancelling"):
            self.assertEqual(self.get(record)["state"], state)
            with self.assertRaises(StoreBusy):
                self.admit(user_id="bob", tenant_id="")
            if state == "queued":
                self.transition(record, {state}, "running")
            elif state == "running":
                self.transition(record, {state}, "cancelling")
        self.transition(record, {"cancelling"}, "cancelled")
        self.confirm_stop(record)
        self.assertTrue(self.admit(user_id="bob")[1])

    def test_concurrent_admissions_create_exactly_one_job(self):
        barrier = threading.Barrier(8)

        def admit(index):
            barrier.wait()
            try:
                return self.admit(idempotency_key=f"key-{index}")[0]["job_id"]
            except StoreBusy:
                return None

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(admit, range(8)))
        self.assertEqual(sum(value is not None for value in results), 1)

    def test_concurrent_idempotent_admission_returns_one_record(self):
        barrier = threading.Barrier(8)

        def admit(_):
            barrier.wait()
            return self.admit()

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(admit, range(8)))
        self.assertEqual(sum(created for _, created in results), 1)
        self.assertEqual(len({record["job_id"] for record, _ in results}), 1)

    def test_transition_compare_and_set_and_terminal_immutability(self):
        record, _ = self.admit()
        self.assertFalse(self.transition(record, {"running"}, "completed"))
        self.assertFalse(self.transition(record, {"queued"}, "completed"))
        self.assertTrue(self.transition(record, {"queued"}, "running"))
        self.assertFalse(self.transition(record, {"queued"}, "cancelled"))
        self.assertTrue(self.transition(record, {"running"}, "completed", request_count=2))
        terminal = self.get(record)
        self.assertFalse(self.transition(record, {"completed"}, "failed", error_code="late"))
        self.assertFalse(self.store.update_progress(
            "alice", "tenant-a", record["job_id"], result={"late": True}, request_count=3,
        ))
        self.assertEqual(self.get(record), terminal)

    def test_restart_interrupts_all_active_states_and_preserves_partial_result(self):
        for state in ("queued", "running", "cancelling"):
            with self.subTest(state=state):
                record, _ = self.admit(idempotency_key=state)
                if state != "queued":
                    self.transition(record, {"queued"}, "running")
                if state == "cancelling":
                    self.transition(record, {"running"}, "cancelling")
                partial = {"steps": [{"status": "done"}], "message": "partial"}
                self.store.update_progress("alice", "tenant-a", record["job_id"],
                                           result=partial, request_count=2)
                self.store.close()
                self.now += 1
                self.store = JobStore(self.path, clock=lambda: self.now)
                self.addCleanup(self.store.close)
                recovered = self.get(record)
                self.assertEqual(recovered["state"], "interrupted")
                self.assertEqual(recovered["error_code"], "restart_interrupted")
                self.assertEqual(recovered["result"], partial)
                self.assertEqual(recovered["request_count"], 2)
                self.assertEqual(recovered["updated_at"], self.now)
                repeated, created = self.admit(idempotency_key=state)
                self.assertFalse(created)
                self.assertEqual(repeated, recovered)
                self.confirm_stop(record)

    def test_second_instance_is_blocked_without_interrupting_first(self):
        record, _ = self.admit()
        with self.assertRaises(StoreBusy):
            JobStore(self.path)
        self.assertEqual(self.get(record)["state"], "queued")
        self.store.close()
        with JobStore(self.path) as reopened:
            self.assertEqual(reopened.get("alice", "tenant-a", record["job_id"])["state"],
                             "interrupted")
        self.assertTrue(self.path.exists())

    def test_progress_is_bounded_and_results_are_detached(self):
        record, _ = self.admit(metadata={"profile_id": "profile"})
        record["metadata"]["profile_id"] = "changed"
        self.assertEqual(self.get(record)["metadata"], {"profile_id": "profile"})
        result = {"nested": [1]}
        self.store.update_progress("alice", "tenant-a", record["job_id"], result=result)
        result["nested"].append(2)
        detached = self.get(record)
        detached["result"]["nested"].append(3)
        self.assertEqual(self.get(record)["result"], {"nested": [1]})
        for invalid in ({"text": "x" * MAX_JSON_BYTES}, {"value": float("nan")},
                        {"x": object()}, {1: "integer key"}, {"x": ("tuple",)}):
            with self.assertRaises(ValueError):
                self.store.update_progress("alice", "tenant-a", record["job_id"], result=invalid)
        for count in (-1, 11, True, 1.0, "1"):
            with self.assertRaises(ValueError):
                self.store.update_progress("alice", "tenant-a", record["job_id"],
                                           request_count=count)
        self.assertEqual(self.get(record)["result"], {"nested": [1]})

    def test_invalid_admission_does_not_reserve_slot(self):
        for arguments in (
            {"user_id": ""}, {"tenant_id": None}, {"idempotency_key": "key\n"},
            {"fingerprint": "x" * 257}, {"generation_id": ""},
            {"generation_epoch": True}, {"generation_epoch": -1},
            {"generation_epoch": 1.5}, {"deadline_at": float("inf")},
            {"deadline_at": True}, {"deadline_at": 10 ** 400},
            {"metadata": {"model": "x" * MAX_JSON_BYTES}},
            {"metadata": {"prompt": "must not be saved"}},
            {"metadata": {"token": "must not be saved"}},
            {"metadata": {"endpoint": "must not be saved"}},
            {"metadata": {"max_requests": True}},
        ):
            with self.subTest(arguments=list(arguments)), self.assertRaises(ValueError):
                self.admit(**arguments)
        self.assertTrue(self.admit()[1])

    def test_metadata_request_and_timeout_limits(self):
        for field, values in (
            ("max_requests", (0, -1, 11, True, 1.0, "1")),
            ("timeout_seconds", (0, -1, 300.01, True, "1", float("inf"), float("nan"))),
        ):
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.admit(metadata={field: value})
        for timeout in (0.01, 1, 300):
            record, created = self.admit(idempotency_key=str(timeout), metadata={
                "max_requests": 10, "timeout_seconds": timeout,
            })
            self.assertTrue(created)
            self.assertEqual(record["metadata"], {"max_requests": 10, "timeout_seconds": timeout})
            self.transition(record, {"queued"}, "cancelled")
            self.confirm_stop(record)

    def test_private_paths_reject_symlinks_and_shared_permissions(self):
        self.store.close()
        self.assertEqual(self.path.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        for suffix in ("", ".lock", "-journal", "-wal", "-shm"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                target = root / "target"
                target.write_text("untouched")
                candidate = root / "jobs.sqlite"
                (root / (candidate.name + suffix)).symlink_to(target)
                with self.assertRaises(StoreError):
                    JobStore(candidate)
                self.assertEqual(target.read_text(), "untouched")
        alias = Path(self.directory.name) / "alias"
        alias.symlink_to(self.path.parent, target_is_directory=True)
        with self.assertRaises(StoreError):
            JobStore(alias / "jobs.sqlite")
        self.path.parent.chmod(0o755)
        with self.assertRaises(StoreError):
            JobStore(self.path)

    def test_close_is_idempotent_and_rejects_further_operations(self):
        record, _ = self.admit()
        self.store.close()
        self.store.close()
        with self.assertRaises(StoreError):
            self.get(record)

    def test_unicode_result_uses_the_same_utf8_budget_as_evidence(self):
        record, _ = self.admit()
        self.transition(record, {"queued"}, "running")
        payload = {"diff": "é" * 32768}
        self.assertTrue(self.store.update_progress("alice", "tenant-a", record["job_id"], result=payload))
        self.assertEqual(self.get(record)["result"], payload)


if __name__ == "__main__":
    unittest.main()
