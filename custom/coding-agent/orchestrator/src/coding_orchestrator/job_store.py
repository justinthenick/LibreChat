"""Private, durable job state; no execution or transport capabilities."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import json
import math
import os
from pathlib import Path
import sqlite3
import stat
import threading
import time
from uuid import uuid4


ACTIVE_STATES = frozenset({"queued", "running", "cancelling"})
TERMINAL_STATES = frozenset({
    "completed", "failed", "cancelled", "timed_out", "interrupted",
})
_TRANSITIONS = {
    "queued": {"running", "cancelled", "failed", "timed_out"},
    "running": {"cancelling", "completed", "failed", "timed_out", "interrupted"},
    "cancelling": {"cancelled", "failed", "timed_out", "interrupted"},
}
MAX_JSON_BYTES = 128 * 1024
_METADATA_STRINGS = frozenset({"profile_id", "repository_alias", "task_mode", "model"})
_METADATA_NUMBERS = frozenset({"max_requests", "timeout_seconds"})


class StoreError(RuntimeError):
    """The private job store could not complete an operation."""


class StoreBusy(StoreError):
    """Another instance or active job holds the single execution slot."""


class IdempotencyConflict(StoreError):
    """An owner reused a key with a different request fingerprint."""


class JobNotFound(StoreError):
    """A job is absent or not owned by the caller."""


@dataclass(frozen=True)
class ExecutionIdentity:
    """Private durable identity used by a trusted execution reconciler."""

    job_id: str
    execution_id: str
    user_id: str
    tenant_id: str
    generation_id: str
    generation_epoch: int
    profile_id: str
    repository_alias: str
    task_mode: str

    def __post_init__(self):
        for name in ("job_id", "execution_id", "user_id", "generation_id"):
            _identifier(getattr(self, name), name)
        for name in ("tenant_id", "profile_id", "repository_alias", "task_mode"):
            _identifier(getattr(self, name), name, empty=True)
        _counter(self.generation_epoch, "generation_epoch", (1 << 63) - 1)


@dataclass(frozen=True)
class StopEvidence:
    """A trusted observation of quiescence, never accepted from request JSON.

    stopped means no owned remote execution remains AND no delayed dispatch
    for this identity can start later. A local process exit is not this proof.
    """

    identity: ExecutionIdentity
    stopped: bool

    def __post_init__(self):
        if type(self.identity) is not ExecutionIdentity or type(self.stopped) is not bool:
            raise ValueError("Invalid execution stop evidence")

    def confirms(self, identity):
        return self.stopped is True and self.identity == identity


def _identifier(value, name, *, empty=False):
    if (not isinstance(value, str) or len(value) > 256
            or (not value and not empty) or value != value.strip()
            or (value and not value.isprintable())):
        raise ValueError(f"Invalid {name}")
    return value


def _number(value, name):
    try:
        valid = (type(value) in (int, float) and math.isfinite(value) and value >= 0)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"Invalid {name}")
    return float(value)


def _counter(value, name, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f"Invalid {name}")
    return value


def _json_value(value, depth=0):
    if depth > 32:
        raise ValueError("Job JSON is too deeply nested")
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("Job JSON keys must be strings")
            _json_value(child, depth + 1)
    elif type(value) is list:
        for child in value:
            _json_value(child, depth + 1)
    elif value is not None and type(value) not in (str, bool, int, float):
        raise ValueError("Invalid job JSON value")


def _json_object(value):
    if type(value) is not dict:
        raise ValueError("Job data must be a JSON object")
    _json_value(value)
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                             separators=(",", ":"))
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError("Invalid job JSON") from exc
    if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
        raise ValueError("Job JSON exceeds size limit")
    return encoded


def _private_file(path):
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077 or info.st_nlink != 1):
            raise StoreError("Job state files must be private, owned regular files")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


class JobStore:
    """One service instance and one active job, scoped by user and tenant.

    ``path`` is an absolute canonical database filename inside a dedicated
    owner-only directory. An absent final directory is created with mode 0700.
    Opening after a restart interrupts active records; work is never replayed.
    """

    def __init__(self, path, clock=time.time):
        self._mutex = threading.RLock()
        self._clock = clock
        self._connection = None
        self._lock_fd = None
        self.path = Path(path)
        try:
            if not self.path.is_absolute() or self.path.resolve() != self.path:
                raise StoreError("Job store path must be absolute and canonical")
            self.path.parent.mkdir(mode=0o700, exist_ok=True)
            directory = self.path.parent.lstat()
            if (not stat.S_ISDIR(directory.st_mode) or directory.st_uid != os.getuid()
                    or directory.st_mode & 0o077):
                raise StoreError("Job store directory must be private and owned")
            self._lock_fd = _private_file(self.path.with_name(self.path.name + ".lock"))
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise StoreBusy("Job store is already in use") from exc
            os.close(_private_file(self.path))
            # SQLite may recover a journal after a crash. Never follow a planted
            # journal/WAL/SHM symlink, even though this store uses DELETE mode.
            for suffix in ("-journal", "-wal", "-shm"):
                sidecar = self.path.with_name(self.path.name + suffix)
                if os.path.lexists(sidecar):
                    os.close(_private_file(sidecar))
            self._connection = sqlite3.connect(
                str(self.path), timeout=5, isolation_level=None, check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=DELETE")
            self._connection.execute("PRAGMA synchronous=FULL")
            with self._transaction() as database:
                database.execute("""CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, tenant_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    generation_id TEXT NOT NULL, generation_epoch INTEGER NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('queued','running','cancelling',
                        'completed','failed','cancelled','timed_out','interrupted')),
                    created_at REAL NOT NULL, updated_at REAL NOT NULL,
                    deadline_at REAL NOT NULL, metadata TEXT NOT NULL,
                    result TEXT, error_code TEXT, request_count INTEGER NOT NULL DEFAULT 0,
                    UNIQUE (user_id, tenant_id, idempotency_key))""")
                database.execute("""CREATE UNIQUE INDEX IF NOT EXISTS one_active_job
                    ON jobs ((1)) WHERE state IN ('queued','running','cancelling')""")
                database.execute("""CREATE TABLE IF NOT EXISTS reservations (
                    job_id TEXT PRIMARY KEY, execution_id TEXT NOT NULL UNIQUE,
                    resolved_at REAL)""")
                # Legacy history has no durable stop proof. Keep resolved rows
                # as tombstones so reopening cannot resurrect their quarantine.
                database.execute("""INSERT INTO reservations (job_id, execution_id)
                    SELECT job_id, lower(hex(randomblob(16))) FROM jobs
                    WHERE job_id NOT IN (SELECT job_id FROM reservations)""")
                database.execute("""UPDATE jobs SET state='interrupted',
                    error_code='restart_interrupted', updated_at=?
                    WHERE state IN ('queued','running','cancelling')""", (self._now(),))
        except BaseException as exc:
            self.close()
            if isinstance(exc, (OSError, sqlite3.Error)):
                raise StoreError("Unable to open private job store") from exc
            raise

    def _now(self):
        return _number(self._clock(), "clock")

    @contextmanager
    def _transaction(self):
        with self._mutex:
            if self._connection is None:
                raise StoreError("Job store is closed")
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                yield self._connection
                self._connection.execute("COMMIT")
            except BaseException as exc:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                if isinstance(exc, sqlite3.Error):
                    raise StoreError("Job store operation failed") from exc
                raise

    @staticmethod
    def _decode(row):
        record = dict(row)
        record["metadata"] = json.loads(record["metadata"])
        record["result"] = json.loads(record["result"]) if record["result"] else None
        return record

    @staticmethod
    def _owner(user_id, tenant_id):
        return (_identifier(user_id, "user_id"),
                _identifier(tenant_id, "tenant_id", empty=True))

    def _find(self, database, user_id, tenant_id, job_id):
        owner = self._owner(user_id, tenant_id)
        _identifier(job_id, "job_id")
        row = database.execute(
            "SELECT * FROM jobs WHERE user_id=? AND tenant_id=? AND job_id=?",
            (*owner, job_id),
        ).fetchone()
        if row is None:
            raise JobNotFound("Job not found")
        return row

    def admit(self, *, user_id, tenant_id, idempotency_key, fingerprint,
              generation_id, generation_epoch, deadline_at, metadata=None):
        owner = self._owner(user_id, tenant_id)
        _identifier(idempotency_key, "idempotency_key")
        _identifier(fingerprint, "fingerprint")
        _identifier(generation_id, "generation_id")
        _counter(generation_epoch, "generation_epoch", (1 << 63) - 1)
        deadline_at = _number(deadline_at, "deadline_at")
        metadata = {} if metadata is None else metadata
        metadata_json = _json_object(metadata)
        if not metadata.keys() <= _METADATA_STRINGS | _METADATA_NUMBERS:
            raise ValueError("Unsupported job metadata field")
        for key, value in metadata.items():
            if key in _METADATA_STRINGS:
                _identifier(value, key)
            elif key == "max_requests":
                if _counter(value, key, 10) == 0:
                    raise ValueError("Invalid max_requests")
            elif not 0 < _number(value, key) <= 300:
                raise ValueError("Invalid timeout_seconds")
        with self._transaction() as database:
            existing = database.execute(
                "SELECT * FROM jobs WHERE user_id=? AND tenant_id=? AND idempotency_key=?",
                (*owner, idempotency_key),
            ).fetchone()
            if existing is not None:
                if existing["fingerprint"] != fingerprint:
                    raise IdempotencyConflict("Idempotency key was reused")
                return self._decode(existing), False
            if database.execute("""SELECT 1 FROM jobs
                    WHERE state IN ('queued','running','cancelling')""").fetchone():
                raise StoreBusy("An active job already exists")
            if database.execute("SELECT 1 FROM reservations WHERE resolved_at IS NULL").fetchone():
                raise StoreBusy("Execution stop remains unconfirmed")
            now = self._now()
            job_id = uuid4().hex
            database.execute("""INSERT INTO jobs (job_id, user_id, tenant_id,
                idempotency_key, fingerprint, generation_id, generation_epoch, state,
                created_at, updated_at, deadline_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?, ?)""",
                (job_id, *owner, idempotency_key, fingerprint, generation_id,
                 generation_epoch, now, now, deadline_at, metadata_json))
            database.execute("INSERT INTO reservations (job_id, execution_id) VALUES (?, ?)",
                             (job_id, uuid4().hex))
            record = self._decode(self._find(database, *owner, job_id))
        return record, True

    def get(self, user_id, tenant_id, job_id):
        with self._transaction() as database:
            return self._decode(self._find(database, user_id, tenant_id, job_id))

    @staticmethod
    def _identity(database, row):
        reservation = database.execute("SELECT execution_id FROM reservations WHERE job_id=?",
                                       (row["job_id"],)).fetchone()
        if reservation is None:
            raise StoreError("Execution reservation is missing")
        metadata = json.loads(row["metadata"])
        return ExecutionIdentity(row["job_id"], reservation["execution_id"],
            row["user_id"], row["tenant_id"], row["generation_id"], row["generation_epoch"],
            metadata.get("profile_id", ""), metadata.get("repository_alias", ""),
            metadata.get("task_mode", ""))

    def execution_identity(self, user_id, tenant_id, job_id):
        with self._transaction() as database:
            return self._identity(database, self._find(database, user_id, tenant_id, job_id))

    def _resolve(self, database, row, evidence):
        if (row["state"] not in TERMINAL_STATES or type(evidence) is not StopEvidence
                or not evidence.confirms(self._identity(database, row))):
            return False
        database.execute("""UPDATE reservations SET resolved_at=?
            WHERE job_id=? AND execution_id=? AND resolved_at IS NULL""",
            (self._now(), row["job_id"], evidence.identity.execution_id))
        return True

    def resolve_execution(self, user_id, tenant_id, job_id, evidence):
        """Release only this terminal reservation; preserve its public history."""
        with self._transaction() as database:
            return self._resolve(database, self._find(database, user_id, tenant_id, job_id), evidence)

    @staticmethod
    def _progress(result, request_count):
        result_json = _json_object(result) if result is not None else None
        if request_count is not None:
            _counter(request_count, "request_count", 10)
        return result_json

    def transition(self, user_id, tenant_id, job_id, expected_states, new_state, *,
                   error_code=None, result=None, request_count=None, stop_evidence=None):
        if isinstance(expected_states, str):
            raise ValueError("Expected states must be a collection")
        expected_states = frozenset(expected_states)
        if (not expected_states or not expected_states <= ACTIVE_STATES | TERMINAL_STATES
                or new_state not in ACTIVE_STATES | TERMINAL_STATES):
            raise ValueError("Invalid job state")
        if error_code is not None:
            _identifier(error_code, "error_code")
        result_json = self._progress(result, request_count)
        with self._transaction() as database:
            row = self._find(database, user_id, tenant_id, job_id)
            if (row["state"] not in expected_states
                    or new_state not in _TRANSITIONS.get(row["state"], ())):
                return False
            database.execute("""UPDATE jobs SET state=?, updated_at=?, error_code=?,
                result=COALESCE(?, result), request_count=COALESCE(?, request_count)
                WHERE job_id=? AND state=?""",
                (new_state, self._now(), error_code, result_json, request_count,
                 job_id, row["state"]))
            if stop_evidence is not None:
                self._resolve(database, self._find(database, user_id, tenant_id, job_id), stop_evidence)
        return True

    def update_progress(self, user_id, tenant_id, job_id, *, result=None, request_count=None):
        result_json = self._progress(result, request_count)
        with self._transaction() as database:
            row = self._find(database, user_id, tenant_id, job_id)
            if row["state"] not in ACTIVE_STATES:
                return False
            database.execute("""UPDATE jobs SET updated_at=?, result=COALESCE(?, result),
                request_count=COALESCE(?, request_count) WHERE job_id=?""",
                (self._now(), result_json, request_count, job_id))
        return True

    def close(self):
        with self._mutex:
            try:
                if self._connection is not None:
                    self._connection.close()
            finally:
                self._connection = None
                if self._lock_fd is not None:
                    os.close(self._lock_fd)
                    self._lock_fd = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
