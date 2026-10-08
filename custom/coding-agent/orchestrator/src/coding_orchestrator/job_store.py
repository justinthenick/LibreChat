"""Private, durable job state; no execution or transport capabilities."""
from __future__ import annotations

from contextlib import contextmanager
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
            now = self._now()
            job_id = uuid4().hex
            database.execute("""INSERT INTO jobs (job_id, user_id, tenant_id,
                idempotency_key, fingerprint, generation_id, generation_epoch, state,
                created_at, updated_at, deadline_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?, ?)""",
                (job_id, *owner, idempotency_key, fingerprint, generation_id,
                 generation_epoch, now, now, deadline_at, metadata_json))
            record = self._decode(self._find(database, *owner, job_id))
        return record, True

    def get(self, user_id, tenant_id, job_id):
        with self._transaction() as database:
            return self._decode(self._find(database, user_id, tenant_id, job_id))

    @staticmethod
    def _progress(result, request_count):
        result_json = _json_object(result) if result is not None else None
        if request_count is not None:
            _counter(request_count, "request_count", 10)
        return result_json

    def transition(self, user_id, tenant_id, job_id, expected_states, new_state, *,
                   error_code=None, result=None, request_count=None):
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
