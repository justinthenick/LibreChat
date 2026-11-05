"""Unregistered integration records in JobStore's existing SQLite transaction domain.

Storage receipts acknowledge only unverified observations or durable intent.
There is no dispatch, completion, reservation release, or quarantine-clear API.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
import re
import stat
from uuid import UUID, uuid4

from .job_store import (
    IdempotencyConflict, JobNotFound, StoreBusy, StoreError, _counter, _identifier,
)

MAX_BLOB_BYTES = 128 * 1024
MAX_COUNTER = (1 << 63) - 1


def _uuid(value):
    if type(value) is not str or str(UUID(value)) != value:
        raise ValueError("Expected a canonical UUID")
    return value


def _digest(value, length=64):
    if type(value) is not str or not re.fullmatch("[0-9a-f]{" + str(length) + "}", value):
        raise ValueError("Invalid digest")
    return value


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _hash(value):
    return hashlib.sha256(_encoded(value).encode()).hexdigest()


def _schema_digest(database):
    return _hash([tuple(row) for row in database.execute(
        "SELECT type,name,sql FROM sqlite_master ORDER BY type,name"
    )])


@dataclass(frozen=True)
class IntegrationMapping:
    review_id: str
    attempt_id: str
    logical_generation: int
    user_id: str
    tenant_id: str
    repository_alias: str
    base: str
    head: str
    profile_id: str
    model: str

    def __post_init__(self):
        _uuid(self.review_id)
        _uuid(self.attempt_id)
        if _counter(self.logical_generation, "logical_generation", MAX_COUNTER) == 0:
            raise ValueError("Generation must be positive")
        for key in ("user_id", "repository_alias", "profile_id", "model"):
            _identifier(getattr(self, key), key)
        _identifier(self.tenant_id, "tenant_id", empty=True)
        _digest(self.base, 40)
        _digest(self.head, 40)


def check_mode(database, namespace):
    """An empty SQLite schema is fresh; existing unmarked schemas never migrate."""
    if namespace is not None:
        _uuid(namespace)
    tables = {row[0] for row in database.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    if "integration_meta" not in tables:
        if namespace is not None and database.execute("SELECT 1 FROM sqlite_master").fetchone():
            raise StoreError("Integration requires a new, empty database")
        if any(name.startswith("integration_") for name in tables):
            raise StoreError("Partial integration metadata")
        return
    if namespace is None:
        raise StoreError("Integration database cannot open as legacy")
    rows = database.execute("SELECT * FROM integration_meta").fetchall()
    fields = {"singleton", "namespace", "schema_version", "backend", "owner_epoch",
              "version", "recovery", "embargo", "quarantine", "schema_digest"}
    if len(rows) != 1 or set(rows[0].keys()) != fields:
        raise StoreError("Incomplete integration metadata")
    if (rows[0]["namespace"] != namespace
            or rows[0]["schema_version"] != 1 or rows[0]["backend"] != "supervisor"):
        raise StoreError("Integration namespace or schema mismatch")
    if rows[0]["schema_digest"] != _schema_digest(database):
        raise StoreError("Integration schema changed; migration is unavailable")
    required = {
        "jobs", "reservations", "integration_mappings", "integration_operations",
        "integration_evidence", "integration_cursors", "integration_intents",
    }
    if not required <= tables:
        raise StoreError("Incomplete integration schema")
    if database.execute("PRAGMA foreign_key_check").fetchone():
        raise StoreError("Broken integration relationships")
    if database.execute("""SELECT 1 FROM jobs WHERE job_id NOT IN
            (SELECT review_id FROM integration_mappings)""").fetchone():
        raise StoreError("Untagged job in integration namespace")


def initialize(database, namespace):
    database.execute("""CREATE TABLE IF NOT EXISTS integration_meta (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),
        namespace TEXT NOT NULL UNIQUE, schema_version INTEGER NOT NULL CHECK(schema_version=1),
        backend TEXT NOT NULL CHECK(backend='supervisor'),
        owner_epoch INTEGER NOT NULL CHECK(owner_epoch>0),
        version INTEGER NOT NULL CHECK(version>=0),
        recovery INTEGER NOT NULL CHECK(recovery IN (0,1)),
        embargo INTEGER NOT NULL CHECK(embargo IN (0,1)),
        quarantine INTEGER NOT NULL CHECK(quarantine IN (0,1)),
        schema_digest TEXT NOT NULL)""")
    database.execute("""CREATE TABLE IF NOT EXISTS integration_mappings (
        review_id TEXT PRIMARY KEY REFERENCES jobs(job_id),
        attempt_id TEXT NOT NULL UNIQUE, logical_generation INTEGER NOT NULL CHECK(logical_generation>0),
        mapping TEXT NOT NULL, digest TEXT NOT NULL, binding_head TEXT NOT NULL,
        execution_id TEXT NOT NULL UNIQUE REFERENCES reservations(execution_id),
        backend TEXT NOT NULL CHECK(backend='supervisor'))""")
    database.execute("""CREATE TABLE IF NOT EXISTS integration_operations (
        operation_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, receipt TEXT NOT NULL)""")
    database.execute("""CREATE TABLE IF NOT EXISTS integration_cursors (
        review_id TEXT NOT NULL REFERENCES integration_mappings(review_id),
        producer TEXT NOT NULL CHECK(producer IN ('guest','host')),
        producer_epoch TEXT NOT NULL, sequence INTEGER NOT NULL CHECK(sequence>0),
        PRIMARY KEY(review_id,producer))""")
    database.execute("""CREATE TABLE IF NOT EXISTS integration_evidence (
        evidence_id TEXT PRIMARY KEY, review_id TEXT NOT NULL REFERENCES integration_mappings(review_id),
        producer TEXT NOT NULL CHECK(producer IN ('guest','host')), producer_epoch TEXT NOT NULL,
        sequence INTEGER NOT NULL CHECK(sequence>0), digest TEXT NOT NULL,
        byte_length INTEGER NOT NULL CHECK(byte_length>0), storage_name TEXT NOT NULL,
        UNIQUE(review_id,producer,producer_epoch,sequence))""")
    database.execute("""CREATE TABLE IF NOT EXISTS integration_intents (
        review_id TEXT PRIMARY KEY REFERENCES integration_mappings(review_id),
        intent TEXT NOT NULL CHECK(intent='cancel'), fingerprint TEXT NOT NULL)""")
    row = database.execute("SELECT * FROM integration_meta").fetchone()
    if row is None:
        database.execute("INSERT INTO integration_meta VALUES (1,?,1,'supervisor',1,0,0,0,0,?)",
                         (namespace, _schema_digest(database)))
    else:
        if row["owner_epoch"] >= MAX_COUNTER or row["version"] >= MAX_COUNTER:
            raise StoreError("Integration counter exhausted")
        database.execute("""UPDATE integration_meta SET owner_epoch=owner_epoch+1,
            version=version+1, recovery=1 WHERE singleton=1""")


class IntegrationRecords:
    """Private storage methods; callers must not interpret receipts as authority."""

    def __init__(self, store):
        self._store = store
        self._blob_root = store.path.with_name(store.path.name + ".evidence")
        with store._transaction() as database:
            row = database.execute("SELECT * FROM integration_meta").fetchone()
            self.namespace = row["namespace"]
            self.owner_epoch = row["owner_epoch"]

    def _meta(self, database):
        row = database.execute("SELECT * FROM integration_meta").fetchone()
        if row is None or row["namespace"] != self.namespace or row["backend"] != "supervisor":
            raise StoreError("Integration namespace is unavailable")
        return row

    def _fence(self, database, epoch, version):
        _counter(epoch, "owner_epoch", MAX_COUNTER)
        _counter(version, "version", MAX_COUNTER)
        row = self._meta(database)
        if epoch != row["owner_epoch"] or epoch != self.owner_epoch:
            raise StoreError("Stale owner epoch")
        if row["quarantine"]:
            raise StoreError("Integration evidence is quarantined")
        return row

    @staticmethod
    def _version(row, version):
        if version != row["version"] or version >= MAX_COUNTER:
            raise StoreError("Stale or exhausted version")

    def _receipt(self, database, operation_id, fingerprint):
        _uuid(operation_id)
        row = database.execute("SELECT * FROM integration_operations WHERE operation_id=?",
                               (operation_id,)).fetchone()
        if row is None:
            return None
        if row["fingerprint"] != fingerprint:
            raise IdempotencyConflict("Operation ID was reused")
        return json.loads(row["receipt"])

    def _commit_receipt(self, database, operation_id, fingerprint, kind, review_id):
        database.execute("UPDATE integration_meta SET version=version+1 WHERE singleton=1")
        meta = self._meta(database)
        receipt = {
            "operation_id": operation_id, "namespace": self.namespace,
            "review_id": review_id, "kind": kind, "version": meta["version"],
            "owner_epoch": meta["owner_epoch"], "live_authority": False,
            "stop_confirmed": False, "reservation_released": False,
        }
        database.execute("INSERT INTO integration_operations VALUES (?,?,?)",
                         (operation_id, fingerprint, _encoded(receipt)))
        return receipt

    def _binding(self, database, mapping):
        if type(mapping) is not IntegrationMapping:
            raise ValueError("Expected integration mapping")
        row = database.execute("SELECT * FROM integration_mappings WHERE review_id=?",
                               (mapping.review_id,)).fetchone()
        if row is None or row["mapping"] != _encoded(asdict(mapping)):
            raise JobNotFound("Integration mapping not found")
        return row

    def _read_blob(self, name, digest, length):
        _digest(digest)
        if name != digest + ".blob":
            raise StoreError("Invalid evidence storage identity")
        info = self._blob_root.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077):
            raise StoreError("Evidence directory is not private")
        descriptor = os.open(self._blob_root / name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(descriptor)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or info.st_mode & 0o077 or info.st_nlink != 1
                    or info.st_size != length or not 0 < length <= MAX_BLOB_BYTES):
                raise StoreError("Invalid retained evidence file")
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                data = stream.read(MAX_BLOB_BYTES + 1)
            if len(data) != length or hashlib.sha256(data).hexdigest() != digest:
                raise StoreError("Retained evidence digest mismatch")
        finally:
            os.close(descriptor)

    def _integrity(self, *, refuse=True):
        failed = False
        with self._store._transaction() as database:
            meta = self._meta(database)
            for row in database.execute("SELECT * FROM integration_evidence"):
                try:
                    self._read_blob(row["storage_name"], row["digest"], row["byte_length"])
                except (OSError, ValueError, StoreError):
                    failed = True
                    break
            if failed and not meta["quarantine"]:
                if meta["version"] >= MAX_COUNTER:
                    raise StoreError("Evidence invalid; quarantine version exhausted")
                database.execute("""UPDATE integration_meta SET quarantine=1, embargo=1,
                    recovery=1, version=version+1 WHERE singleton=1""")
        if failed and refuse:
            raise StoreError("Referenced evidence unavailable; quarantine committed")
        return not failed

    def _retain(self, data):
        if type(data) is not bytes or not 0 < len(data) <= MAX_BLOB_BYTES:
            raise ValueError("Evidence must be bounded, nonempty bytes")
        digest = hashlib.sha256(data).hexdigest()
        name = digest + ".blob"
        self._blob_root.mkdir(mode=0o700, exist_ok=True)
        directory = self._blob_root.lstat()
        if (not stat.S_ISDIR(directory.st_mode) or directory.st_uid != os.getuid()
                or directory.st_mode & 0o077):
            raise StoreError("Evidence directory is not private")
        try:
            descriptor = os.open(self._blob_root / name,
                                 os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            self._read_blob(name, digest, len(data))
            descriptor = os.open(self._blob_root / name, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        else:
            try:
                with os.fdopen(descriptor, "wb", closefd=False) as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(descriptor)
            finally:
                os.close(descriptor)
        # Both the blob entry and its containing directory precede the DB reference.
        for path in (self._blob_root, self._blob_root.parent):
            descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        return digest, name

    def snapshot(self):
        intact = self._integrity(refuse=False)
        with self._store._transaction() as database:
            return dict(self._meta(database)) | {"evidence_intact": intact}

    def query_operation(self, operation_id):
        """Return a historical storage receipt, never permission to retry an effect."""
        _uuid(operation_id)
        self._integrity(refuse=False)
        with self._store._transaction() as database:
            self._meta(database)
            row = database.execute("SELECT receipt FROM integration_operations WHERE operation_id=?",
                                   (operation_id,)).fetchone()
            return json.loads(row[0]) if row else None

    def admit(self, mapping, operation_id, *, owner_epoch, expected_version):
        if type(mapping) is not IntegrationMapping:
            raise ValueError("Expected integration mapping")
        _uuid(operation_id)
        payload = {"kind": "admit", "mapping": asdict(mapping), "namespace": self.namespace}
        fingerprint = _hash(payload)
        self._integrity()
        with self._store._transaction() as database:
            meta = self._fence(database, owner_epoch, expected_version)
            prior = self._receipt(database, operation_id, fingerprint)
            if prior is not None:
                return prior
            self._version(meta, expected_version)
            if meta["recovery"] or meta["embargo"]:
                raise StoreBusy("Integration admission is embargoed")
            if database.execute("SELECT 1 FROM reservations WHERE resolved_at IS NULL").fetchone():
                raise StoreBusy("Predecessor execution remains unresolved")
            now = self._store._now()
            execution_id = uuid4().hex
            database.execute("""INSERT INTO jobs (job_id,user_id,tenant_id,idempotency_key,
                fingerprint,generation_id,generation_epoch,state,created_at,updated_at,
                deadline_at,metadata) VALUES (?,?,?,?,?,?,0,'queued',?,?,?,'{}')""",
                (mapping.review_id, mapping.user_id, mapping.tenant_id, mapping.review_id,
                 fingerprint, mapping.review_id, now, now, now))
            database.execute("INSERT INTO reservations (job_id,execution_id) VALUES (?,?)",
                             (mapping.review_id, execution_id))
            encoded = _encoded(asdict(mapping))
            digest = _hash(asdict(mapping))
            database.execute("INSERT INTO integration_mappings VALUES (?,?,?,?,?,?,?,'supervisor')",
                             (mapping.review_id, mapping.attempt_id, mapping.logical_generation,
                              encoded, digest, digest, execution_id))
            database.execute("UPDATE integration_meta SET embargo=1 WHERE singleton=1")
            return self._commit_receipt(database, operation_id, fingerprint,
                                        "admission_recorded", mapping.review_id)

    def request_cancel(self, mapping, operation_id, *, owner_epoch, expected_version):
        if type(mapping) is not IntegrationMapping:
            raise ValueError("Expected integration mapping")
        _uuid(operation_id)
        fingerprint = _hash({"kind": "cancel", "mapping": asdict(mapping),
                             "namespace": self.namespace})
        self._integrity()
        with self._store._transaction() as database:
            meta = self._fence(database, owner_epoch, expected_version)
            self._binding(database, mapping)
            prior = self._receipt(database, operation_id, fingerprint)
            if prior is not None:
                return prior
            self._version(meta, expected_version)
            intent = database.execute("SELECT fingerprint FROM integration_intents WHERE review_id=?",
                                      (mapping.review_id,)).fetchone()
            if intent is None:
                database.execute("INSERT INTO integration_intents VALUES (?,'cancel',?)",
                                 (mapping.review_id, fingerprint))
            elif intent[0] != fingerprint:
                raise IdempotencyConflict("Cancellation intent changed")
            database.execute("UPDATE jobs SET cancel_requested=1 WHERE job_id=?",
                             (mapping.review_id,))
            return self._commit_receipt(database, operation_id, fingerprint,
                                        "cancellation_intent_only", mapping.review_id)

    def observe(self, mapping, operation_id, *, owner_epoch, expected_version,
                evidence_id, producer, producer_epoch, sequence, prior_binding_head, data):
        if type(mapping) is not IntegrationMapping:
            raise ValueError("Expected integration mapping")
        _uuid(operation_id)
        _uuid(evidence_id)
        _uuid(producer_epoch)
        if type(producer) is not str or producer not in {"guest", "host"}:
            raise ValueError("Unsupported evidence producer")
        if _counter(sequence, "sequence", MAX_COUNTER) == 0:
            raise ValueError("Sequence must be positive")
        _digest(prior_binding_head)
        if type(data) is not bytes or not 0 < len(data) <= MAX_BLOB_BYTES:
            raise ValueError("Evidence must be bounded, nonempty bytes")
        digest = hashlib.sha256(data).hexdigest()
        payload = {
            "kind": "observe", "mapping": asdict(mapping), "namespace": self.namespace,
            "evidence_id": evidence_id, "producer": producer, "producer_epoch": producer_epoch,
            "sequence": sequence, "prior_binding_head": prior_binding_head,
            "digest": digest, "byte_length": len(data),
        }
        fingerprint = _hash(payload)
        self._integrity()
        with self._store._transaction() as database:
            meta = self._fence(database, owner_epoch, expected_version)
            binding = self._binding(database, mapping)
            prior = self._receipt(database, operation_id, fingerprint)
            if prior is not None:
                return prior
            self._version(meta, expected_version)
            if binding["binding_head"] != prior_binding_head:
                raise StoreError("Observed binding head is stale")
            cursor = database.execute("""SELECT * FROM integration_cursors
                WHERE review_id=? AND producer=?""", (mapping.review_id, producer)).fetchone()
            if ((cursor is None and sequence != 1) or (cursor is not None and
                    (cursor["producer_epoch"] != producer_epoch or sequence != cursor["sequence"] + 1))):
                raise StoreError("Evidence cursor is stale or discontinuous")
            if database.execute("SELECT 1 FROM integration_evidence WHERE evidence_id=?",
                                (evidence_id,)).fetchone():
                raise IdempotencyConflict("Evidence ID was reused")
            digest, name = self._retain(data)
            database.execute("INSERT INTO integration_evidence VALUES (?,?,?,?,?,?,?,?)",
                             (evidence_id, mapping.review_id, producer, producer_epoch,
                              sequence, digest, len(data), name))
            if cursor is None:
                database.execute("INSERT INTO integration_cursors VALUES (?,?,?,?)",
                                 (mapping.review_id, producer, producer_epoch, sequence))
            else:
                database.execute("""UPDATE integration_cursors SET sequence=?
                    WHERE review_id=? AND producer=?""", (sequence, mapping.review_id, producer))
            database.execute("UPDATE integration_mappings SET binding_head=? WHERE review_id=?",
                             (_hash(payload), mapping.review_id))
            return self._commit_receipt(database, operation_id, fingerprint,
                                        "unverified_observation_recorded", mapping.review_id)
