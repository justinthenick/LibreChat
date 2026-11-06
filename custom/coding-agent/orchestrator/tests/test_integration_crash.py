"""Abrupt process exits against disposable SQLite fixtures, never power-loss proof."""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4

from coding_orchestrator.integration import IntegrationMapping
from coding_orchestrator.job_store import JobStore, StoreBusy, StoreError


# The child uses the actual store/transaction implementation. Hooks exist only in
# this fixture process; os._exit skips close(), finally blocks and Python cleanup.
CHILD = r"""
from contextlib import contextmanager
from pathlib import Path
import json
import os
import sys
sys.path.insert(0, sys.argv[1])
from coding_orchestrator.integration import IntegrationMapping
from coding_orchestrator.job_store import JobStore
config = json.loads(sys.argv[2])
point, operation = config['point'], config['operation']
mapping = IntegrationMapping(**config['mapping'])
store = JobStore(Path(config['path']), integration_namespace=config['namespace'])
def crash():
    print(point, flush=True)
    os._exit(73)
if point == 'hot':
    store._connection.execute("UPDATE jobs SET state='running'")
    if config.get('damage_schema'):
        store._connection.execute('ALTER TABLE jobs DROP COLUMN request')
    store._connection.execute('PRAGMA cache_size=5')
    store._connection.execute('BEGIN IMMEDIATE')
    store._connection.execute('CREATE TABLE uncommitted_fixture (value TEXT)')
    # Force dirty pages to spill into the main file while retaining undo records.
    store._connection.execute('UPDATE jobs SET metadata=?', ('x' * (2 * 1024 * 1024),))
    crash()
if operation != 'admit':
    store.integration.admit(mapping, config['admission'], owner_epoch=1, expected_version=0)
original = store._transaction
@contextmanager
def interrupted_transaction():
    targeted = False
    with original() as database:
        yield database
        targeted = database.execute('SELECT 1 FROM integration_operations WHERE operation_id=?',
                                    (config['operation_id'],)).fetchone() is not None
        if targeted and point == 'before_commit':
            crash()
    # The actual COMMIT returned, but the operation has not returned to its caller.
    if targeted and point == 'after_commit':
        crash()
store._transaction = interrupted_transaction
if point == 'after_blob':
    retain = store.integration._retain
    def retained(data):
        result = retain(data)
        crash()
        return result
    store.integration._retain = retained
arguments = dict(owner_epoch=1, expected_version=0 if operation == 'admit' else 1)
if operation == 'admit':
    store.integration.admit(mapping, config['operation_id'], **arguments)
elif operation == 'cancel':
    store.integration.request_cancel(mapping, config['operation_id'], **arguments)
else:
    binding = store._connection.execute('SELECT binding_head FROM integration_mappings').fetchone()[0]
    store.integration.observe(mapping, config['operation_id'], **arguments,
        evidence_id=config['evidence_id'], producer='guest', producer_epoch=config['producer_epoch'],
        sequence=1, prior_binding_head=binding, data=b'fabricated crash observation')
raise AssertionError('Crash point was not reached')
"""


class IntegrationCrashTests(unittest.TestCase):
    def fixture(self):
        directory = tempfile.TemporaryDirectory(prefix="integration-crash-")
        self.addCleanup(directory.cleanup)
        return dict(
            path=str(Path(directory.name) / "private" / "jobs.sqlite"),
            namespace=str(uuid4()), operation_id=str(uuid4()), admission=str(uuid4()),
            evidence_id=str(uuid4()), producer_epoch=str(uuid4()),
            mapping=dict(review_id=str(uuid4()), attempt_id=str(uuid4()), logical_generation=1,
                         user_id="fixture", tenant_id="", repository_alias="fixture",
                         base="a" * 40, head="b" * 40, profile_id="fixture", model="fixture"),
        )

    def crash(self, config, operation, point):
        source = Path(__file__).resolve().parents[1] / "src"
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", CHILD, str(source),
             json.dumps(config | dict(operation=operation, point=point))],
            capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 73, result.stderr)
        self.assertEqual(result.stdout.strip(), point)

    def boundary(self, operation, point):
        config = self.fixture()
        self.crash(config, operation, point)
        committed = point == "after_commit"
        admitted = operation != "admit" or committed
        with JobStore(config["path"], integration_namespace=config["namespace"]) as store:
            meta = store.integration.snapshot()
            self.assertEqual(meta["owner_epoch"], 2)
            self.assertEqual(meta["recovery"], 1)
            self.assertEqual(meta["embargo"], int(admitted))
            self.assertEqual(meta["version"], 1 + int(operation != "admit") + int(committed))
            receipt = store.integration.query_operation(config["operation_id"])
            self.assertEqual(receipt is not None, committed)
            if receipt:
                self.assertEqual(receipt["owner_epoch"], 1)
                for flag in ("live_authority", "stop_confirmed", "reservation_released"):
                    self.assertFalse(receipt[flag])
            database = store._connection
            self.assertEqual(database.execute('SELECT count(*) FROM jobs').fetchone()[0], int(admitted))
            self.assertEqual(database.execute('SELECT count(*) FROM reservations WHERE resolved_at IS NULL').fetchone()[0], int(admitted))
            self.assertEqual(database.execute('SELECT count(*) FROM integration_operations').fetchone()[0],
                             int(operation != "admit") + int(committed))
            if admitted:
                self.assertEqual(database.execute('SELECT state FROM jobs').fetchone()[0], 'interrupted')
            if operation == "cancel":
                self.assertEqual(database.execute('SELECT cancel_requested FROM jobs').fetchone()[0], int(committed))
                self.assertEqual(database.execute('SELECT count(*) FROM integration_intents').fetchone()[0], int(committed))
            if operation == "observe":
                self.assertEqual(database.execute('SELECT count(*) FROM integration_evidence').fetchone()[0], int(committed))
                self.assertEqual(database.execute('SELECT count(*) FROM integration_cursors').fetchone()[0], int(committed))
                binding = database.execute('SELECT digest,binding_head FROM integration_mappings').fetchone()
                self.assertEqual(binding[0] == binding[1], not committed)
                blobs = list(Path(config['path'] + '.evidence').iterdir())
                self.assertEqual(len(blobs), 1)
                self.assertEqual(blobs[0].read_bytes(), b'fabricated crash observation')
                if committed:
                    self.assertEqual(database.execute('SELECT sequence FROM integration_cursors').fetchone()[0], 1)
            # Retained receipt lookup is reconciliation, never mutation replay.
            before = meta["version"]
            self.assertEqual(store.integration.query_operation(config["operation_id"]), receipt)
            self.assertEqual(store.integration.snapshot()["version"], before)
            with self.assertRaises(StoreError):
                store.integration.admit(IntegrationMapping(**config["mapping"]), config["operation_id"],
                                        owner_epoch=1, expected_version=0)
            with self.assertRaises(StoreBusy):
                store.integration.admit(IntegrationMapping(**config["mapping"]), str(uuid4()),
                                        owner_epoch=2, expected_version=before)

    def test_admission_exit_before_commit(self):
        self.boundary("admit", "before_commit")

    def test_admission_exit_after_commit_before_return(self):
        self.boundary("admit", "after_commit")

    def test_cancellation_exit_before_commit(self):
        self.boundary("cancel", "before_commit")

    def test_cancellation_exit_after_commit_before_return(self):
        self.boundary("cancel", "after_commit")

    def test_evidence_exit_after_blob_before_reference(self):
        self.boundary("observe", "after_blob")

    def test_evidence_exit_before_commit(self):
        self.boundary("observe", "before_commit")

    def test_evidence_exit_after_commit_before_return(self):
        self.boundary("observe", "after_commit")

    def hot_fixture(self, integrated, *, damage_schema=False):
        config = self.fixture()
        config['damage_schema'] = damage_schema
        if not integrated:
            config["namespace"] = None
        with JobStore(config["path"], integration_namespace=config["namespace"]) as store:
            if integrated:
                store.integration.admit(IntegrationMapping(**config["mapping"]), config["admission"],
                                        owner_epoch=1, expected_version=0)
            else:
                store.admit(user_id="fixture", tenant_id="", idempotency_key="fixture",
                            fingerprint="fixture", generation_id="fixture", generation_epoch=0,
                            deadline_at=100)
        self.crash(config, "admit", "hot")
        path = Path(config["path"])
        journal = path.with_name(path.name + '-journal')
        self.assertGreater(journal.stat().st_size, 512)
        self.assertNotEqual(journal.read_bytes()[:8], bytes(8))
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as probe:
            with self.assertRaises(sqlite3.OperationalError) as failure:
                probe.execute('SELECT * FROM jobs').fetchall()
            self.assertEqual(failure.exception.sqlite_errorname, 'SQLITE_READONLY_ROLLBACK')
        return config

    def test_legacy_hot_journal_recovery(self):
        config = self.hot_fixture(False)
        with JobStore(config["path"]) as store:
            row = store._connection.execute('SELECT metadata,state FROM jobs').fetchone()
            self.assertEqual(row[0], '{}')
            self.assertEqual(row[1], 'interrupted')
            self.assertEqual(store._connection.execute('SELECT count(*) FROM reservations WHERE resolved_at IS NULL').fetchone()[0], 1)

    def test_integrated_hot_journal_recovery(self):
        config = self.hot_fixture(True)
        with JobStore(config["path"], integration_namespace=config["namespace"]) as store:
            meta = store.integration.snapshot()
            self.assertEqual(meta['owner_epoch'], 3)
            self.assertEqual(meta['version'], 3)
            self.assertEqual((meta['embargo'], meta['recovery']), (1, 1))
            self.assertIsNotNone(store.integration.query_operation(config['admission']))
            self.assertEqual(store._connection.execute('SELECT metadata FROM jobs').fetchone()[0], '{}')
            self.assertIsNone(store._connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name='uncommitted_fixture'").fetchone())

    def refused_hot_open(self, *, integrated=True, wrong_mode=False, damage_schema=False):
        config = self.hot_fixture(integrated, damage_schema=damage_schema)
        namespace = None if wrong_mode else str(uuid4())
        if damage_schema:
            namespace = config['namespace']
        with self.assertRaises(StoreError):
            JobStore(config['path'], integration_namespace=namespace)
        # Native rollback is allowed; application initialization/reconciliation is not.
        with closing(sqlite3.connect(Path(config['path']).as_uri() + '?mode=ro', uri=True)) as database:
            row = database.execute('SELECT metadata,state FROM jobs').fetchone()
            self.assertEqual(row, ('{}', 'running'))
            self.assertEqual(database.execute('SELECT count(*) FROM reservations WHERE resolved_at IS NULL').fetchone()[0], 1)
            self.assertIsNone(database.execute(
                "SELECT 1 FROM sqlite_master WHERE name='uncommitted_fixture'").fetchone())
            if integrated:
                self.assertEqual(database.execute('SELECT owner_epoch,version FROM integration_meta').fetchone(), (2, 2))
                self.assertEqual(database.execute('SELECT count(*) FROM integration_operations').fetchone()[0], 1)
            else:
                self.assertIsNone(database.execute(
                    "SELECT 1 FROM sqlite_master WHERE name='integration_meta'").fetchone())
            if damage_schema:
                self.assertNotIn('request', {row[1] for row in database.execute('PRAGMA table_info(jobs)')})

    def test_hot_wrong_namespace_refuses_before_application_mutation(self):
        self.refused_hot_open()

    def test_hot_integrated_store_refuses_legacy_mode(self):
        self.refused_hot_open(wrong_mode=True)

    def test_hot_legacy_store_refuses_integration_mode(self):
        self.refused_hot_open(integrated=False)

    def test_hot_malformed_schema_refuses_without_migration(self):
        self.refused_hot_open(damage_schema=True)


if __name__ == "__main__":
    unittest.main()
