"""Unregistered archive of two pinned public fixtures, never verification authority."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3

if __package__:
    from .integration import IntegrationRecords, _schema_digest, _uuid
    from .job_store import StoreError
else:
    from integration import IntegrationRecords, _schema_digest, _uuid
    from job_store import StoreError

CLASS = "S6_FIXED_SYNTHETIC_ARCHIVE"
CATALOG_SHA = "855860970e67db44582ba342f552c48554932437a1ffe0e95f184ed15590dd6e"
MAX_SAFE = (1 << 53) - 1
CATALOG = (Path(__file__).resolve().parents[5] / "packages/api/src/coding/review/evidence"
           / "fixtures/signed-profile.json")


class ArchiveError(StoreError):
    def __init__(self, code, original_operation_id=None):
        super().__init__(code)
        self.code = code
        self.original_operation_id = original_operation_id


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(domain, value):
    return digest(domain.encode("ascii") + b"\0" + canonical(value))


def receipt_for(namespace, operation_id, index, sha, epoch, version):
    return {"version": 1, "kind": "synthetic_bundle_archived", "class": CLASS,
            "namespace": namespace, "operation_id": operation_id,
            "bundle_digest": sha, "catalog_sha256": CATALOG_SHA, "bundle_index": index,
            "committed_version": version, "accepted_owner_epoch": epoch, "synthetic_only": True,
            "live_authority": False, "stop_confirmed": False, "reservation_released": False,
            "quarantine_clearance": False, "result_publication_authority": False}


def counter(value, positive=False):
    if type(value) is not int or not int(positive) <= value <= MAX_SAFE:
        raise ArchiveError("INVALID_REQUEST")


def catalog_bundles():
    # The caller cannot supply a path, verdict, key, payload or replacement catalog.
    with CATALOG.open("rb") as stream:
        data = stream.read(131073)
    if len(data) > 131072 or digest(data) != CATALOG_SHA:
        raise ArchiveError("CATALOG_MISMATCH")
    bundles = []
    for index, bundle in enumerate(json.loads(data)["bundles"]):
        context = canonical(bundle["expectedContext"])
        blobs = [(digest(context), context)]
        records = []
        for record in bundle["records"]:
            frame = bytes.fromhex(record["frameHex"])
            signature = bytes.fromhex(record["signatureHex"])
            artifacts = [bytes.fromhex(a["bytesHex"]) for a in record["artifacts"]]
            blobs.extend((digest(b), b) for b in [frame, signature, *artifacts])
            records.append({"frame_sha256": digest(frame), "frame_bytes": len(frame),
                            "signature_sha256": digest(signature), "signature_bytes": len(signature),
                            "artifacts": [{"sha256": digest(b), "bytes": len(b)} for b in artifacts]})
        manifest = {"version": 1, "class": CLASS, "catalog_sha256": CATALOG_SHA,
                    "bundle_index": index, "context_sha256": digest(context),
                    "context_bytes": len(context), "records": records}
        if (not 0 < len(context) <= 8192 or len(canonical(manifest)) > 16384
                or len(blobs) > 97 or any(not 0 < len(b) <= 131072 for _, b in blobs)):
            raise ArchiveError("LIMIT_EXCEEDED")
        bundles.append((identity("LibreChat/Supervisor/S6-fixed-fixture-bundle/1", manifest),
                        canonical(manifest).decode("ascii"), tuple(blobs)))
    if len(bundles) != 2:
        raise ArchiveError("CATALOG_MISMATCH")
    return tuple(bundles)


def check_fixture_mode(database, namespace, integration_namespace):
    tables = {r[0] for r in database.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    present = any(t.startswith("fixture_") for t in tables)
    if namespace is None:
        if present:
            raise ArchiveError("WRONG_MODE")
        return False
    _uuid(namespace)
    if integration_namespace is not None:
        raise ArchiveError("WRONG_MODE")
    if not tables and not database.execute("SELECT 1 FROM sqlite_master").fetchone():
        return True
    if tables != {"integration_meta", "fixture_meta", "fixture_bundles", "fixture_operations"}:
        raise ArchiveError("WRONG_MODE")
    marker = database.execute("SELECT * FROM fixture_meta").fetchall()
    meta = database.execute("SELECT * FROM integration_meta").fetchall()
    if (len(marker) != 1 or tuple(marker[0]) != (1, CLASS, CATALOG_SHA)
            or len(meta) != 1 or meta[0]["namespace"] != namespace
            or meta[0]["backend"] != "supervisor" or meta[0]["schema_version"] != 1
            or meta[0]["schema_digest"] != _schema_digest(database)):
        raise ArchiveError("WRONG_MODE")
    return True


def initialize_fixture(database, namespace):
    database.execute("""CREATE TABLE IF NOT EXISTS integration_meta (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1), namespace TEXT NOT NULL UNIQUE,
        schema_version INTEGER NOT NULL CHECK(schema_version=1),
        backend TEXT NOT NULL CHECK(backend='supervisor'), owner_epoch INTEGER NOT NULL,
        version INTEGER NOT NULL, recovery INTEGER NOT NULL, embargo INTEGER NOT NULL,
        quarantine INTEGER NOT NULL, schema_digest TEXT NOT NULL)""")
    database.execute("""CREATE TABLE IF NOT EXISTS fixture_meta (
        schema INTEGER PRIMARY KEY CHECK(schema=1),
        class TEXT NOT NULL CHECK(class='S6_FIXED_SYNTHETIC_ARCHIVE'), catalog_sha256 TEXT NOT NULL)""")
    database.execute("""CREATE TABLE IF NOT EXISTS fixture_bundles (
        bundle_digest TEXT PRIMARY KEY, bundle_index INTEGER NOT NULL UNIQUE CHECK(bundle_index IN (0,1)),
        manifest TEXT NOT NULL, operation_id TEXT NOT NULL UNIQUE,
        accepted_owner_epoch INTEGER NOT NULL, committed_version INTEGER NOT NULL,
        class TEXT NOT NULL CHECK(class='S6_FIXED_SYNTHETIC_ARCHIVE'))""")
    database.execute("""CREATE TABLE IF NOT EXISTS fixture_operations (
        operation_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
        bundle_digest TEXT NOT NULL UNIQUE, receipt TEXT NOT NULL)""")
    row = database.execute("SELECT * FROM integration_meta").fetchone()
    if row is None:
        database.execute("INSERT INTO fixture_meta VALUES (1,?,?)", (CLASS, CATALOG_SHA))
        database.execute("INSERT INTO integration_meta VALUES (1,?,1,'supervisor',1,0,0,0,0,?)",
                         (namespace, _schema_digest(database)))
    else:
        if row["owner_epoch"] >= MAX_SAFE or row["version"] >= MAX_SAFE:
            raise ArchiveError("CAPACITY_EXHAUSTED")
        database.execute("UPDATE integration_meta SET owner_epoch=owner_epoch+1,version=version+1,recovery=1")


class FixtureArchive:
    # Reuse byte retention primitives without inheriting any integration mutation API.
    _retain = IntegrationRecords._retain
    _read_blob = IntegrationRecords._read_blob

    def __init__(self, store):
        self._store = store
        self._blob_root = store.path.with_name(store.path.name + ".evidence")
        self._bundles = catalog_bundles()
        with store._transaction() as db:
            meta = db.execute("SELECT * FROM integration_meta").fetchone()
            self.namespace = meta["namespace"]
            self.owner_epoch = meta["owner_epoch"]

    def _meta(self, db):
        check_fixture_mode(db, self.namespace, None)
        return db.execute("SELECT * FROM integration_meta").fetchone()

    def _valid_operation(self, db, row, operation):
        try:
            _uuid(row["operation_id"])
            counter(row["accepted_owner_epoch"], True)
            counter(row["committed_version"], True)
            meta = self._meta(db)
            if (row["accepted_owner_epoch"] > meta["owner_epoch"]
                    or row["committed_version"] > meta["version"]):
                return False
            semantic = dict(version=1, kind="fixture_bundle_append", namespace=self.namespace,
                            operation_id=row["operation_id"], catalog_sha256=CATALOG_SHA,
                            bundle_index=row["bundle_index"], bundle_digest=row["bundle_digest"])
            expected = receipt_for(self.namespace, row["operation_id"], row["bundle_index"],
                                   row["bundle_digest"], row["accepted_owner_epoch"], row["committed_version"])
            return (operation is not None and operation["bundle_digest"] == row["bundle_digest"]
                    and operation["fingerprint"] == identity(
                        "LibreChat/Supervisor/S6-fixed-fixture-operation/1", semantic)
                    and operation["receipt"] == canonical(expected).decode("ascii"))
        except (ValueError, TypeError, KeyError, StoreError):
            return False

    def _intact(self, db):
        rows = db.execute("SELECT * FROM fixture_bundles").fetchall()
        operations = db.execute("SELECT * FROM fixture_operations").fetchall()
        if len(rows) != len(operations) or len(rows) > 2:
            return False
        for row in rows:
            if type(row["bundle_index"]) is not int or row["bundle_index"] not in (0, 1):
                return False
            expected, manifest, blobs = self._bundles[row["bundle_index"]]
            if row["bundle_digest"] != expected or row["manifest"] != manifest or row["class"] != CLASS:
                return False
            operation = next((o for o in operations if o["operation_id"] == row["operation_id"]), None)
            if not self._valid_operation(db, row, operation):
                return False
            for sha, data in blobs:
                try:
                    self._read_blob(sha + ".blob", sha, len(data))
                except (OSError, ValueError, StoreError):
                    return False
        return True

    def _state(self, db, intact):
        meta = self._meta(db)
        return {"owner_epoch": meta["owner_epoch"], "version": meta["version"],
                "integrity": intact, "quarantine": bool(meta["quarantine"]),
                "recovery": bool(meta["recovery"])}

    def state(self):
        # Protective latch commits separately from any subsequently rejected append.
        try:
            with self._store._transaction() as db:
                meta = self._meta(db)
                intact = self._intact(db)
                if not intact and not meta["quarantine"]:
                    if meta["version"] >= MAX_SAFE:
                        raise ArchiveError("STORE_UNAVAILABLE")
                    db.execute("UPDATE integration_meta SET quarantine=1,embargo=1,recovery=1,version=version+1")
                result = self._state(db, intact)
            return result
        except (StoreError, sqlite3.Error, OSError) as exc:
            raise ArchiveError("STORE_UNAVAILABLE") from exc

    def _parse(self, raw):
        if type(raw) is not bytes or len(raw) > 2048:
            raise ArchiveError("LIMIT_EXCEEDED")
        try:
            request = json.loads(raw)
            if canonical(request) != raw or type(request) is not dict:
                raise ValueError()
            common = {"version", "kind", "namespace", "operation_id"}
            kind = request["kind"]
            fields = common if kind == "fixture_operation_query" else common | {
                "owner_epoch", "expected_version", "catalog_sha256", "bundle_index", "bundle_digest"}
            if (set(request) != fields or request["version"] != 1 or type(request["version"]) is not int
                    or kind not in {"fixture_operation_query", "fixture_bundle_append"}):
                raise ValueError()
            _uuid(request["namespace"])
            _uuid(request["operation_id"])
            if request["namespace"] != self.namespace:
                raise ArchiveError("WRONG_MODE")
            if kind == "fixture_bundle_append":
                counter(request["owner_epoch"], True)
                counter(request["expected_version"])
                if request["catalog_sha256"] != CATALOG_SHA:
                    raise ArchiveError("CATALOG_MISMATCH")
                index = request["bundle_index"]
                if type(index) is not int or index not in (0, 1):
                    raise ValueError()
                if request["bundle_digest"] != self._bundles[index][0]:
                    raise ArchiveError("BUNDLE_MISMATCH")
            return request
        except (ValueError, KeyError, TypeError, RecursionError) as exc:
            raise ArchiveError("INVALID_REQUEST") from exc

    def dispatch(self, raw):
        try:
            return self._dispatch(raw)
        except ArchiveError:
            raise
        except (StoreError, sqlite3.Error, OSError, ValueError, TypeError, KeyError, IndexError) as exc:
            raise ArchiveError("STORE_UNAVAILABLE") from exc

    def _dispatch(self, raw):
        request = self._parse(raw)
        state = self.state()
        if request["kind"] == "fixture_operation_query":
            with self._store._transaction() as db:
                row = db.execute("SELECT * FROM fixture_operations WHERE operation_id=?",
                                 (request["operation_id"],)).fetchone()
                result = {"status": "FOUND" if row else "NOT_FOUND", "state": self._state(db, state["integrity"])}
                if row:
                    bundle = db.execute("SELECT * FROM fixture_bundles WHERE operation_id=?",
                                        (request["operation_id"],)).fetchone()
                    if bundle is None or not self._valid_operation(db, bundle, row):
                        raise ArchiveError("STORE_UNAVAILABLE")
                    result["receipt"] = json.loads(row["receipt"])
        else:
            result = self._append(request)
        if len(canonical(result)) > 4096:
            raise ArchiveError("STORE_UNAVAILABLE")
        return deepcopy(result)

    def _append(self, request):
        semantic = {k: v for k, v in request.items() if k not in {"owner_epoch", "expected_version"}}
        fingerprint = identity("LibreChat/Supervisor/S6-fixed-fixture-operation/1", semantic)
        try:
            with self._store._transaction() as db:
                meta = self._meta(db)
                if request["owner_epoch"] != meta["owner_epoch"] or self.owner_epoch != meta["owner_epoch"]:
                    raise ArchiveError("STALE_OWNER")
                if meta["quarantine"]:
                    raise ArchiveError("QUARANTINED")
                if not self._intact(db):
                    raise ArchiveError("INTEGRITY_FAILURE")
                prior = db.execute("SELECT * FROM fixture_operations WHERE operation_id=?",
                                   (request["operation_id"],)).fetchone()
                if prior:
                    if prior["fingerprint"] != fingerprint:
                        raise ArchiveError("OPERATION_CONFLICT")
                    return {"status": "FOUND", "receipt": json.loads(prior["receipt"])}
                if meta["version"] >= MAX_SAFE:
                    raise ArchiveError("CAPACITY_EXHAUSTED")
                if request["expected_version"] != meta["version"]:
                    raise ArchiveError("STALE_VERSION")
                duplicate = db.execute("SELECT operation_id FROM fixture_bundles WHERE bundle_digest=?",
                                       (request["bundle_digest"],)).fetchone()
                if duplicate:
                    raise ArchiveError("DUPLICATE_BUNDLE", duplicate[0])
                sha, manifest, blobs = self._bundles[request["bundle_index"]]
                for blob_sha, data in blobs:
                    self._retain(data)
                    self._read_blob(blob_sha + ".blob", blob_sha, len(data))
                receipt = receipt_for(self.namespace, request["operation_id"], request["bundle_index"],
                                      sha, meta["owner_epoch"], meta["version"] + 1)
                db.execute("INSERT INTO fixture_bundles VALUES (?,?,?,?,?,?,?)",
                           (sha, request["bundle_index"], manifest, request["operation_id"],
                            meta["owner_epoch"], meta["version"] + 1, CLASS))
                db.execute("INSERT INTO fixture_operations VALUES (?,?,?,?)",
                           (request["operation_id"], fingerprint, sha, canonical(receipt).decode("ascii")))
                db.execute("UPDATE integration_meta SET version=version+1")
            return {"status": "RECORDED", "receipt": receipt}
        except ArchiveError as exc:
            if exc.code == "INTEGRITY_FAILURE":
                self.state()
            raise
        except (StoreError, sqlite3.Error, OSError) as exc:
            # Never infer non-commit from a storage/COMMIT exception; query original ID.
            raise ArchiveError("UNKNOWN_COMMIT") from exc
