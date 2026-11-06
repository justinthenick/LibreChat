"""Disposable fixed-fixture archive controls; no real trust or power-loss proof."""
from contextlib import contextmanager
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from coding_orchestrator.fixture_archive import (
    ArchiveError, CATALOG_SHA, CLASS, MAX_SAFE, canonical, catalog_bundles,
)
from coding_orchestrator.job_store import JobStore, StoreError


CHILD = r"""
import os, sys, json
from pathlib import Path
from contextlib import contextmanager
sys.path.insert(0, sys.argv[1])
from coding_orchestrator.job_store import JobStore
from coding_orchestrator.fixture_archive import canonical
config = json.loads(sys.argv[2])
with JobStore(Path(config['path']), fixture_namespace=config['namespace']) as store:
    request = config['request']
    request.update(owner_epoch=store.fixtures.owner_epoch, expected_version=store.fixtures.state()['version'])
    point = config['point']
    def crash():
        print(point, flush=True)
        os._exit(73)
    if point == 'before_transaction':
        crash()
    original = store._transaction
    @contextmanager
    def transaction():
        targeted = False
        with original() as db:
            yield db
            targeted = db.execute('SELECT 1 FROM fixture_operations').fetchone() is not None
            if targeted and point == 'before_commit':
                crash()
        if targeted and point == 'after_commit':
            crash()
    store._transaction = transaction
    if point == 'after_blob':
        retain = store.fixtures._retain
        def retained(data):
            retain(data)
            crash()
        store.fixtures._retain = retained
    store.fixtures.dispatch(canonical(request))
raise AssertionError('Crash point not reached')
"""


class FixtureArchiveTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="s6-fixture-")
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "private" / "fixture.sqlite"
        self.namespace = str(uuid4())

    def open(self):
        store = JobStore(self.path, fixture_namespace=self.namespace)
        self.addCleanup(store.close)
        return store

    def request(self, store, index=0, operation=None):
        state = store.fixtures.state()
        return dict(version=1, kind="fixture_bundle_append", namespace=self.namespace,
                    operation_id=operation or str(uuid4()), owner_epoch=state["owner_epoch"],
                    expected_version=state["version"], catalog_sha256=CATALOG_SHA,
                    bundle_index=index, bundle_digest=catalog_bundles()[index][0])

    def query(self, store, operation):
        return store.fixtures.dispatch(canonical(dict(version=1, kind="fixture_operation_query",
                                                     namespace=self.namespace, operation_id=operation)))

    def error(self, code, store, request):
        with self.assertRaises(ArchiveError) as error:
            store.fixtures.dispatch(canonical(request))
        self.assertEqual(error.exception.code, code)
        return error.exception

    def test_both_bundles_atomic_and_inert(self):
        store = self.open()
        for index in range(2):
            request = self.request(store, index)
            result = store.fixtures.dispatch(canonical(request))
            receipt = result["receipt"]
            self.assertEqual(receipt["committed_version"], index + 1)
            self.assertEqual(receipt["class"], CLASS)
            self.assertTrue(receipt["synthetic_only"])
            for key in ("live_authority", "stop_confirmed", "reservation_released",
                        "quarantine_clearance", "result_publication_authority"):
                self.assertIs(receipt[key], False)
            self.assertEqual(self.query(store, request["operation_id"])["receipt"], receipt)
        self.assertEqual(store.fixtures.state()["version"], 2)
        tables = {r[0] for r in store._connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables, {"integration_meta", "fixture_meta", "fixture_bundles", "fixture_operations"})
        self.assertIsNone(store.integration)

    def test_retry_conflict_and_duplicate(self):
        store = self.open()
        request = self.request(store)
        original = store.fixtures.dispatch(canonical(request))["receipt"]
        with patch.object(store.fixtures, "_retain", side_effect=AssertionError("retry wrote")):
            self.assertEqual(store.fixtures.dispatch(canonical(request))["receipt"], original)
        self.assertEqual(store.fixtures.state()["version"], 1)
        self.error("OPERATION_CONFLICT", store, self.request(store, 1, request["operation_id"]))
        duplicate = self.error("DUPLICATE_BUNDLE", store, self.request(store))
        self.assertEqual(duplicate.original_operation_id, request["operation_id"])
        self.assertEqual(store._connection.execute("SELECT count(*) FROM fixture_operations").fetchone()[0], 1)

    def test_fences_and_reopen(self):
        store = self.open()
        request = self.request(store)
        receipt = store.fixtures.dispatch(canonical(request))["receipt"]
        self.error("STALE_VERSION", store, self.request(store, 1) | {"expected_version": 0})
        store.close()
        reopened = self.open()
        found = self.query(reopened, request["operation_id"])
        self.assertEqual(found["receipt"], receipt)
        self.assertEqual(found["state"]["owner_epoch"], 2)
        self.assertTrue(found["state"]["recovery"])
        self.error("STALE_OWNER", reopened, request)
        retry = request | {"owner_epoch": 2}
        self.assertEqual(reopened.fixtures.dispatch(canonical(retry))["receipt"], receipt)
        reopened.fixtures.dispatch(canonical(self.request(reopened, 1)))

    def test_strict_inputs_and_modes(self):
        store = self.open()
        request = self.request(store)
        cases = [("INVALID_REQUEST", {"verdict": True}), ("WRONG_MODE", {"namespace": str(uuid4())}),
                 ("CATALOG_MISMATCH", {"catalog_sha256": "a" * 64}),
                 ("BUNDLE_MISMATCH", {"bundle_digest": "a" * 64}),
                 ("INVALID_REQUEST", {"bundle_index": True}),
                 ("INVALID_REQUEST", {"owner_epoch": 1.0})]
        for code, delta in cases:
            with self.subTest(delta=delta):
                self.error(code, store, request | delta)
        for kind in ("finish", "observe", "admit", "cancel"):
            self.error("INVALID_REQUEST", store, request | {"kind": kind})
        for raw in (b"{} " , b'{"version":1,"version":1}', b"x" * 2049):
            with self.assertRaises(ArchiveError):
                store.fixtures.dispatch(raw)
        with self.assertRaises(StoreError):
            store.cancel_external("fixture", "", str(uuid4()))
        with self.assertRaises(StoreError):
            store.resolve_execution("fixture", "", str(uuid4()), None)

    def test_cross_mode_rejection_before_application_mutation(self):
        for mode in ("legacy", "integration", "fixture"):
            with self.subTest(mode=mode):
                path = self.path.with_name(mode + ".sqlite")
                kwargs = {} if mode == "legacy" else {mode + "_namespace": self.namespace}
                with JobStore(path, **kwargs):
                    pass
                before = path.read_bytes()
                others = [{"fixture_namespace": self.namespace}] if mode != "fixture" else [
                    {}, {"integration_namespace": self.namespace}]
                for other in others:
                    with self.assertRaises(StoreError):
                        JobStore(path, **other)
                    self.assertEqual(path.read_bytes(), before)

    def test_missing_context_latches_even_after_restore(self):
        store = self.open()
        request = self.request(store)
        store.fixtures.dispatch(canonical(request))
        sha, data = catalog_bundles()[0][2][0]
        blob = store.fixtures._blob_root / (sha + ".blob")
        blob.unlink()
        self.error("QUARANTINED", store, self.request_without_state(request))
        state = self.query(store, request["operation_id"])["state"]
        self.assertFalse(state["integrity"])
        self.assertTrue(state["quarantine"])
        self.assertEqual(state["version"], 2)
        blob.write_bytes(data)
        blob.chmod(0o600)
        state = store.fixtures.state()
        self.assertTrue(state["integrity"])
        self.assertTrue(state["quarantine"])
        self.assertEqual(state["version"], 2)
        self.error("QUARANTINED", store, request)

    @staticmethod
    def request_without_state(request):
        return request | {"expected_version": 1}

    def test_failed_latch_never_claims_protection(self):
        store = self.open()
        request = self.request(store)
        store.fixtures.dispatch(canonical(request))
        sha, _ = catalog_bundles()[0][2][0]
        (store.fixtures._blob_root / (sha + ".blob")).unlink()
        original = store._transaction
        @contextmanager
        def aborted():
            with original() as db:
                yield db
                raise StoreError("injected rollback")
        with patch.object(store, "_transaction", aborted):
            with self.assertRaises(ArchiveError) as error:
                store.fixtures.state()
            self.assertEqual(error.exception.code, "STORE_UNAVAILABLE")
        self.assertEqual(store._connection.execute("SELECT quarantine FROM integration_meta").fetchone()[0], 0)

    def test_catalog_substitution_and_snapshot(self):
        store = self.open()
        request = self.request(store)
        with patch("coding_orchestrator.fixture_archive.CATALOG", self.path):
            with self.assertRaises(ArchiveError):
                catalog_bundles()
            # Already loaded immutable catalog remains the same bytes.
            store.fixtures.dispatch(canonical(request))
        self.assertTrue(store.fixtures.state()["integrity"])

    def test_unknown_commit_resolves_original_operation(self):
        store = self.open()
        request = self.request(store)
        original = store._transaction
        @contextmanager
        def lost_ack():
            targeted = False
            with original() as db:
                yield db
                targeted = db.execute("SELECT 1 FROM fixture_operations").fetchone() is not None
            if targeted:
                raise StoreError("injected lost commit acknowledgement")
        with patch.object(store, "_transaction", lost_ack):
            self.error("UNKNOWN_COMMIT", store, request)
        found = self.query(store, request["operation_id"])
        self.assertEqual(found["status"], "FOUND")
        self.assertEqual(found["receipt"]["committed_version"], 1)

    def test_exhausted_version(self):
        store = self.open()
        request = self.request(store)
        store._connection.execute("UPDATE integration_meta SET version=?", (MAX_SAFE,))
        self.error("CAPACITY_EXHAUSTED", store, request | {"expected_version": MAX_SAFE})

    def test_closed_store_query_is_bounded_unavailable(self):
        store = self.open()
        store.close()
        with self.assertRaises(ArchiveError) as error:
            self.query(store, str(uuid4()))
        self.assertEqual(error.exception.code, "STORE_UNAVAILABLE")

    def test_corrupt_receipt_fingerprint_or_fences_closes_archive(self):
        mutations = [
            ("UPDATE fixture_operations SET receipt=?", ('{"live_authority":true}',)),
            ("UPDATE fixture_operations SET fingerprint=?", ("a" * 64,)),
            ("UPDATE fixture_bundles SET committed_version=?", (999,)),
            ("UPDATE fixture_bundles SET accepted_owner_epoch=?", (0,)),
        ]
        for index, (sql, arguments) in enumerate(mutations):
            with self.subTest(index=index):
                self.path = self.path.with_name("corrupt-" + str(index) + ".sqlite")
                store = self.open()
                request = self.request(store)
                store.fixtures.dispatch(canonical(request))
                store._connection.execute(sql, arguments)
                with self.assertRaises(ArchiveError) as error:
                    self.query(store, request["operation_id"])
                self.assertEqual(error.exception.code, "STORE_UNAVAILABLE")
                self.assertTrue(store.fixtures.state()["quarantine"])
                self.error("QUARANTINED", store, request)
                store.close()

    def test_integrity_discovered_in_append_survives_rollback(self):
        store = self.open()
        request = self.request(store)
        store.fixtures.dispatch(canonical(request))
        second = self.request(store, 1)
        sha, _ = catalog_bundles()[0][2][0]
        blob = store.fixtures._blob_root / (sha + ".blob")
        original = store.fixtures._intact
        calls = 0
        def changed(db):
            nonlocal calls
            calls += 1
            if calls == 2:
                blob.unlink()
            return original(db)
        with patch.object(store.fixtures, "_intact", changed):
            self.error("INTEGRITY_FAILURE", store, second)
        self.assertTrue(store.fixtures.state()["quarantine"])
        self.assertEqual(store._connection.execute("SELECT count(*) FROM fixture_bundles").fetchone()[0], 1)

    def test_crash_boundaries(self):
        for point in ("before_transaction", "after_blob", "before_commit", "after_commit"):
            with self.subTest(point=point):
                self.path = self.path.with_name(point + ".sqlite")
                store = self.open()
                request = self.request(store)
                store.close()
                config = dict(path=str(self.path), namespace=self.namespace, request=request, point=point)
                result = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD,
                                         str(Path(__file__).resolve().parents[1] / "src"), json.dumps(config)],
                                        capture_output=True, text=True, timeout=20, check=False)
                self.assertEqual(result.returncode, 73, result.stderr)
                self.assertEqual(result.stdout.strip(), point)
                reopened = self.open()
                found = self.query(reopened, request["operation_id"])
                self.assertEqual(found["status"], "FOUND" if point == "after_commit" else "NOT_FOUND")
                count = int(point == "after_commit")
                for table in ("fixture_bundles", "fixture_operations"):
                    self.assertEqual(reopened._connection.execute("SELECT count(*) FROM " + table).fetchone()[0], count)
                self.assertTrue(found["state"]["integrity"])
                if point == "after_blob":
                    self.assertTrue(list(reopened.fixtures._blob_root.glob("*.blob")))
                reopened.close()


if __name__ == "__main__":
    unittest.main()
