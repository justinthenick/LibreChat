"""Real SQLite fixtures only; no provider, Supervisor, or historical store access."""
from dataclasses import replace
from pathlib import Path
import hashlib
import os
import sqlite3
import tempfile
import unittest
from uuid import uuid4

from coding_orchestrator.integration import IntegrationMapping, MAX_BLOB_BYTES
from coding_orchestrator.job_store import (
    IdempotencyConflict, JobNotFound, JobStore, StopEvidence, StoreBusy, StoreError,
)


class IntegrationStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="integration-store-")
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "private" / "jobs.sqlite"
        self.namespace = str(uuid4())
        self.store = self.open()
        self.mapping = IntegrationMapping(
            str(uuid4()), str(uuid4()), 1, "fixture-user", "fixture-tenant",
            "fixture-repository", "a" * 40, "b" * 40, "fixture-profile", "fixture-model",
        )

    def open(self):
        store = JobStore(self.path, integration_namespace=self.namespace)
        self.addCleanup(store.close)
        return store

    def metadata(self):
        return self.store.integration.snapshot()

    def arguments(self):
        row = self.metadata()
        return dict(owner_epoch=row["owner_epoch"], expected_version=row["version"])

    def admit(self, mapping=None, operation_id=None, **overrides):
        return self.store.integration.admit(
            mapping or self.mapping, operation_id or str(uuid4()),
            **(self.arguments() | overrides),
        )

    def rows(self, table):
        with sqlite3.connect(self.path) as database:
            return database.execute("SELECT * FROM " + table).fetchall()

    def head(self):
        return self.rows("integration_mappings")[0][5]

    def observe(self, **overrides):
        arguments = dict(
            evidence_id=str(uuid4()), producer="guest", producer_epoch=str(uuid4()),
            sequence=1, prior_binding_head=self.head(), data=b"fabricated observation",
        )
        return self.store.integration.observe(
            self.mapping, str(uuid4()), **self.arguments(), **(arguments | overrides),
        )

    def test_new_namespace_schema_and_foreign_keys(self):
        self.assertEqual(self.metadata()["backend"], "supervisor")
        self.assertEqual(self.metadata()["owner_epoch"], 1)
        self.assertEqual(self.store._connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(self.rows("jobs"), [])
        self.assertEqual(self.rows("reservations"), [])

    def test_admission_groups_mapping_reservation_receipt_and_embargo(self):
        operation = str(uuid4())
        receipt = self.admit(operation_id=operation)
        for table in ("jobs", "reservations", "integration_mappings", "integration_operations"):
            self.assertEqual(len(self.rows(table)), 1)
        self.assertEqual(self.metadata()["version"], 1)
        self.assertEqual(self.metadata()["embargo"], 1)
        self.assertFalse(receipt["live_authority"])
        self.assertFalse(receipt["stop_confirmed"])
        self.assertFalse(receipt["reservation_released"])
        self.assertEqual(self.store.integration.query_operation(operation), receipt)
        self.assertEqual(self.admit(operation_id=operation, expected_version=0), receipt)
        self.assertEqual(self.metadata()["version"], 1)

    def test_reused_operation_payload_conflicts(self):
        operation = str(uuid4())
        self.admit(operation_id=operation)
        with self.assertRaises(IdempotencyConflict):
            self.admit(mapping=replace(self.mapping, model="different"), operation_id=operation)
        self.assertEqual(self.metadata()["version"], 1)

    def test_embargo_blocks_every_admission_alias(self):
        self.admit()
        for mapping in (
            self.mapping,
            replace(self.mapping, attempt_id=str(uuid4())),
            replace(self.mapping, logical_generation=2),
            replace(self.mapping, review_id=str(uuid4()), attempt_id=str(uuid4()),
                    user_id="other-user", tenant_id="other-tenant"),
        ):
            with self.subTest(mapping=mapping), self.assertRaises(StoreBusy):
                self.admit(mapping=mapping)
        self.assertEqual(len(self.rows("reservations")), 1)

    def test_admission_failure_rolls_back_all_rows(self):
        self.store._connection.execute("""CREATE TEMP TRIGGER fail_receipt
            BEFORE INSERT ON integration_operations BEGIN SELECT RAISE(ABORT,'fixture'); END""")
        with self.assertRaises(StoreError):
            self.admit()
        for table in ("jobs", "reservations", "integration_mappings", "integration_operations"):
            self.assertEqual(self.rows(table), [])
        self.assertEqual(self.metadata()["version"], 0)
        self.assertEqual(self.metadata()["embargo"], 0)
        self.store._connection.execute("DROP TRIGGER fail_receipt")
        self.admit()

    def test_lost_response_query_survives_reopen_without_reapplication(self):
        operation = str(uuid4())
        receipt = self.admit(operation_id=operation)
        old_epoch = self.metadata()["owner_epoch"]
        old = self.store.integration
        self.store.close()
        self.store = self.open()
        self.assertEqual(self.store.integration.query_operation(operation), receipt)
        self.assertEqual(self.metadata()["owner_epoch"], old_epoch + 1)
        self.assertEqual(self.metadata()["recovery"], 1)
        self.assertEqual(self.store.get("fixture-user", "fixture-tenant",
                                      self.mapping.review_id)["state"], "interrupted")
        with self.assertRaises(StoreError):
            self.admit(owner_epoch=old_epoch)
        with self.assertRaises(StoreError):
            old.admit(self.mapping, operation, owner_epoch=old_epoch, expected_version=1)
        with self.assertRaises(StoreBusy):
            self.admit(mapping=replace(self.mapping, review_id=str(uuid4())))
        self.assertEqual(len(self.rows("reservations")), 1)

    def test_live_connection_checks_persisted_epoch_and_version(self):
        self.store._connection.execute("UPDATE integration_meta SET owner_epoch=2")
        with self.assertRaises(StoreError):
            self.admit(owner_epoch=1)
        self.assertEqual(self.rows("jobs"), [])
        self.store._connection.execute("UPDATE integration_meta SET owner_epoch=1")
        self.admit()
        with self.assertRaises(StoreError):
            self.store.integration.request_cancel(
                self.mapping, str(uuid4()), owner_epoch=1, expected_version=0,
            )

    def test_legacy_open_cannot_reconcile_integration_store(self):
        self.admit()
        before = self.rows("jobs")
        self.store.close()
        with self.assertRaises(StoreError):
            JobStore(self.path)
        self.assertEqual(self.rows("jobs"), before)

    def test_integration_open_never_migrates_legacy_store(self):
        self.store.close()
        path = Path(self.directory.name) / "legacy" / "jobs.sqlite"
        with JobStore(path) as legacy:
            legacy.admit(user_id="fixture", tenant_id="", idempotency_key="key",
                         fingerprint="request", generation_id="generation",
                         generation_epoch=0, deadline_at=100)
        before = path.read_bytes()
        with self.assertRaises(StoreError):
            JobStore(path, integration_namespace=str(uuid4()))
        self.assertEqual(path.read_bytes(), before)

    def test_wrong_namespace_and_partial_metadata_refuse(self):
        self.admit()
        self.store.close()
        with self.assertRaises(StoreError):
            JobStore(self.path, integration_namespace=str(uuid4()))
        with sqlite3.connect(self.path) as database:
            database.execute("DROP TABLE integration_cursors")
        with self.assertRaises(StoreError):
            self.open()

    def test_altered_marked_schema_refuses_without_migration(self):
        self.admit()
        self.store.close()
        with sqlite3.connect(self.path) as database:
            database.execute("ALTER TABLE jobs DROP COLUMN request")
        before = self.path.read_bytes()
        with self.assertRaises(StoreError):
            self.open()
        self.assertEqual(self.path.read_bytes(), before)

    def test_empty_existing_database_is_fresh(self):
        self.store.close()
        path = Path(self.directory.name) / "empty" / "jobs.sqlite"
        path.parent.mkdir(mode=0o700)
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        os.close(descriptor)
        with JobStore(path, integration_namespace=str(uuid4())) as store:
            self.assertEqual(store.integration.snapshot()["version"], 0)

    def test_legacy_mutators_cannot_release_or_change_integration_records(self):
        self.admit()
        owner = ("fixture-user", "fixture-tenant", self.mapping.review_id)
        identity = self.store.execution_identity(*owner)
        operations = (
            lambda: self.store.admit(user_id="x", tenant_id="", idempotency_key="x",
                                    fingerprint="x", generation_id="x",
                                    generation_epoch=0, deadline_at=100),
            lambda: self.store.cancel_external(*owner),
            lambda: self.store.discard_terminal_results(100),
            lambda: self.store.transition(*owner, {"queued"}, "cancelled"),
            lambda: self.store.update_progress(*owner, result={"success": True}),
            lambda: self.store.resolve_execution(*owner, StopEvidence(identity, True)),
        )
        before = self.rows("jobs")
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(StoreError):
                operation()
        self.assertEqual(self.rows("jobs"), before)
        self.assertIsNone(self.rows("reservations")[0][2])

    def test_cancel_aliases_are_intent_only_and_durable(self):
        self.admit()
        receipts = []
        for _ in range(2):
            receipts.append(self.store.integration.request_cancel(
                self.mapping, str(uuid4()), **self.arguments(),
            ))
        self.assertEqual(len(self.rows("integration_intents")), 1)
        self.assertNotEqual(receipts[0]["operation_id"], receipts[1]["operation_id"])
        self.assertTrue(all(r["kind"] == "cancellation_intent_only" for r in receipts))
        self.assertTrue(all(not r["stop_confirmed"] for r in receipts))
        self.assertIsNone(self.rows("reservations")[0][2])
        self.store.close()
        self.store = self.open()
        self.assertEqual(self.store.integration.query_operation(receipts[0]["operation_id"]),
                         receipts[0])

    def test_mapping_mutation_cannot_cancel(self):
        self.admit()
        for altered in (replace(self.mapping, logical_generation=2),
                        replace(self.mapping, user_id="other"),
                        replace(self.mapping, attempt_id=str(uuid4()))):
            with self.assertRaises(JobNotFound):
                self.store.integration.request_cancel(altered, str(uuid4()), **self.arguments())

    def test_observation_commits_cursor_binding_reference_and_receipt(self):
        self.admit()
        previous = self.head()
        receipt = self.observe()
        self.assertEqual(receipt["kind"], "unverified_observation_recorded")
        self.assertFalse(receipt["stop_confirmed"])
        self.assertNotEqual(self.head(), previous)
        self.assertEqual(self.metadata()["version"], 2)
        self.assertEqual(len(self.rows("integration_evidence")), 1)
        self.assertEqual(len(self.rows("integration_cursors")), 1)
        self.assertEqual(len(self.rows("integration_operations")), 2)
        self.assertIsNone(self.rows("reservations")[0][2])

    def test_evidence_exact_retry_uses_original_arguments(self):
        self.admit()
        operation_id = str(uuid4())
        arguments = self.arguments() | dict(
            evidence_id=str(uuid4()), producer="guest", producer_epoch=str(uuid4()),
            sequence=1, prior_binding_head=self.head(), data=b"fabricated observation",
        )
        receipt = self.store.integration.observe(self.mapping, operation_id, **arguments)
        self.assertEqual(self.store.integration.observe(self.mapping, operation_id, **arguments),
                         receipt)
        self.assertEqual(len(self.rows("integration_evidence")), 1)
        self.assertEqual(self.metadata()["version"], 2)

    def test_observation_rollback_leaves_only_non_authoritative_orphan(self):
        self.admit()
        previous = self.head()
        self.store._connection.execute("""CREATE TEMP TRIGGER fail_cursor
            BEFORE INSERT ON integration_cursors BEGIN SELECT RAISE(ABORT,'fixture'); END""")
        with self.assertRaises(StoreError):
            self.observe()
        self.assertEqual(self.rows("integration_evidence"), [])
        self.assertEqual(self.rows("integration_cursors"), [])
        self.assertEqual(len(self.rows("integration_operations")), 1)
        self.assertEqual(self.head(), previous)
        self.assertEqual(self.metadata()["version"], 1)
        self.assertEqual(len(list(self.store.integration._blob_root.iterdir())), 1)
        self.store._connection.execute("DROP TRIGGER fail_cursor")
        self.observe()

    def test_evidence_sequence_and_producer_epoch_cannot_roll_back(self):
        self.admit()
        epoch = str(uuid4())
        self.observe(producer_epoch=epoch)
        for sequence, producer_epoch in ((1, epoch), (3, epoch), (2, str(uuid4()))):
            with self.subTest(sequence=sequence), self.assertRaises(StoreError):
                self.observe(sequence=sequence, producer_epoch=producer_epoch)
        self.observe(sequence=2, producer_epoch=epoch)
        self.assertEqual(self.rows("integration_cursors")[0][3], 2)

    def test_stale_binding_and_evidence_id_conflict(self):
        self.admit()
        before = self.head()
        evidence_id = str(uuid4())
        epoch = str(uuid4())
        self.observe(evidence_id=evidence_id, producer_epoch=epoch)
        with self.assertRaises(StoreError):
            self.observe(sequence=2, producer_epoch=epoch, prior_binding_head=before)
        with self.assertRaises(IdempotencyConflict):
            self.observe(sequence=2, producer_epoch=epoch, evidence_id=evidence_id)

    def test_same_bytes_can_be_referenced_by_both_producers(self):
        self.admit()
        self.observe()
        self.observe(producer="host")
        self.assertEqual(len(self.rows("integration_evidence")), 2)
        self.assertEqual(len(list(self.store.integration._blob_root.iterdir())), 1)

    def test_missing_committed_blob_latches_quarantine_and_blocks_mutation(self):
        admission = self.admit()
        self.observe()
        next(self.store.integration._blob_root.iterdir()).unlink()
        with self.assertRaises(StoreError):
            self.store.integration.request_cancel(self.mapping, str(uuid4()), **self.arguments())
        self.assertEqual(self.metadata()["quarantine"], 1)
        self.assertEqual(self.metadata()["embargo"], 1)
        self.assertFalse(self.metadata()["evidence_intact"])
        self.assertEqual(self.store.integration.query_operation(admission["operation_id"]), admission)
        self.store.close()
        self.store = self.open()
        self.assertEqual(self.metadata()["quarantine"], 1)

    def test_corrupt_committed_blob_never_becomes_trusted(self):
        self.admit()
        self.observe()
        path = next(self.store.integration._blob_root.iterdir())
        path.write_bytes(b"x" * path.stat().st_size)
        self.assertEqual(self.metadata()["quarantine"], 1)
        self.assertEqual(self.metadata()["version"], 3)
        self.assertEqual(self.metadata()["version"], 3)
        with self.assertRaises(StoreError):
            self.observe()

    def test_quarantine_exhaustion_refuses_without_claiming_persistence(self):
        self.admit()
        self.observe()
        next(self.store.integration._blob_root.iterdir()).unlink()
        self.store._connection.execute("UPDATE integration_meta SET version=?", ((1 << 63) - 1,))
        with self.assertRaisesRegex(StoreError, "quarantine version exhausted"):
            self.metadata()
        self.assertEqual(self.store._connection.execute(
            "SELECT quarantine FROM integration_meta").fetchone()[0], 0)

    def test_symlink_blob_refuses_without_following_target(self):
        self.admit()
        root = self.store.integration._blob_root
        root.mkdir(mode=0o700)
        data = b"fixture"
        target = Path(self.directory.name) / "untouched"
        target.write_bytes(b"preserve")
        (root / (hashlib.sha256(data).hexdigest() + ".blob")).symlink_to(target)
        with self.assertRaises(OSError):
            self.observe(data=data)
        self.assertEqual(target.read_bytes(), b"preserve")
        self.assertEqual(self.rows("integration_evidence"), [])

    def test_bounds_and_canonical_identities(self):
        for field, value in (("review_id", "UPPER"), ("logical_generation", True),
                             ("logical_generation", 0), ("base", "A" * 40)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                replace(self.mapping, **{field: value})
        self.admit()
        for value in (b"", b"x" * (MAX_BLOB_BYTES + 1), "text", {"success": True}):
            with self.subTest(value_type=type(value)), self.assertRaises(ValueError):
                self.observe(data=value)
        self.assertEqual(self.rows("integration_evidence"), [])

    def test_observation_after_reopen_is_unverified_and_embargo_remains(self):
        self.admit()
        self.store.close()
        self.store = self.open()
        receipt = self.observe(data=b'{"success":true,"stopped":true}')
        self.assertFalse(receipt["stop_confirmed"])
        self.assertEqual(self.metadata()["recovery"], 1)
        self.assertEqual(self.metadata()["embargo"], 1)
        self.assertIsNone(self.rows("reservations")[0][2])


if __name__ == "__main__":
    unittest.main()
