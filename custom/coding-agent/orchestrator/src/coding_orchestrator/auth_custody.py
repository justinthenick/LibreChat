"""Default-off disposable custody experiment. No production enrollment or routing.

Only explicit synthetic fixture creation and httpx.MockTransport are supported.
SQLite durability is not credential isolation, authorization or remote stop proof.
Trusted callers must establish the supplied execution Claim independently.
"""
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import fcntl
import json
import os
from pathlib import Path
import sqlite3

from .auth_exchange import BoundedAuthExchange, MAX_REPLY
from .auth_validation import _json, _text, validate_identity
from .job_worker import WorkerCancelled, WorkerDeadline, WorkerLimit


class CustodyError(RuntimeError):
    def __init__(self):
        super().__init__('Synthetic credential custody unavailable')


@dataclass(frozen=True)
class RotationOutcome:
    state: str
    revision: int
    epoch: int


def _require(condition):
    if not condition:
        raise CustodyError()


def _counter(value):
    _require(type(value) is int and 0 <= value < 2**62)
    return value


def _fixture_refresh(value):
    _text(value, 8192)
    _require(value.startswith('synthetic-'))
    return value


def _claim(claim):
    from coding_executor.executions import Claim, ExecutionIdentity

    _require(type(claim) is Claim and type(claim.identity) is ExecutionIdentity)
    for value in (claim.operation_id, claim.request_sha256, claim.attempt_id, claim.authority_id):
        _text(value)
    return json.dumps(asdict(claim), sort_keys=True, separators=(',', ':'))


def _raise(category):
    if category in (WorkerCancelled, WorkerDeadline, WorkerLimit):
        raise category() from None
    raise CustodyError() from None


def _failure(control, error, primary=None):
    native = (WorkerCancelled, WorkerDeadline, WorkerLimit)
    if primary in native:
        return primary
    if type(error) in native:
        return type(error)
    try:
        control.remaining_seconds()
    except native as stopped:
        return type(stopped)
    except Exception:
        pass
    return CustodyError


class SyntheticCredentialCustodian:
    """One owner, one active rotation, no credential-returning public interface.

    An existing fixture is reopened explicitly; startup never resets pending state.
    Read-only outcomes are not grants to use credentials or dispatch a model.
    """

    def __init__(self, path, *, enabled=False):
        _require(enabled is True)
        self.path = Path(path).resolve()
        _require(self.path.is_file())

    def __reduce__(self):
        raise TypeError('Custodian must not cross worker serialization')

    @classmethod
    def create_fixture(cls, path, *, owner, tenant, subject, account, audience,
                       refresh_token, enabled=False):
        error = None
        result = None
        db = descriptor = None
        created = False
        try:
            _require(enabled is True)
            for value in (owner, subject, account, audience):
                _text(value)
            _require(type(tenant) is str and (tenant == '' or _text(tenant)))
            _fixture_refresh(refresh_token)
            path = Path(path).resolve()
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            created = True
            os.close(descriptor)
            descriptor = None
            result = cls(path, enabled=True)
            with result._transaction() as db:
                db.execute('CREATE TABLE credential (id INTEGER PRIMARY KEY CHECK(id=1), '
                           'owner TEXT NOT NULL, tenant TEXT NOT NULL, subject TEXT NOT NULL, '
                           'account TEXT NOT NULL, audience TEXT NOT NULL, revision INTEGER NOT NULL, '
                           'epoch INTEGER NOT NULL, state TEXT NOT NULL, access_token TEXT, '
                           'refresh_token TEXT NOT NULL, expires_at INTEGER)')
                db.execute('CREATE TABLE rotation (attempt TEXT PRIMARY KEY, claim TEXT NOT NULL, '
                           'revision INTEGER NOT NULL, epoch INTEGER NOT NULL, state TEXT NOT NULL, '
                           'result_revision INTEGER NOT NULL)')
                db.execute('INSERT INTO credential VALUES (1,?,?,?,?,?,0,0,?,NULL,?,NULL)',
                           (owner, tenant, subject, account, audience, 'ready', refresh_token))
        except Exception:
            error = CustodyError
            # Only this invocation's exclusive fixture may be removed. The
            # transaction context has closed SQLite before cleanup is attempted.
            try:
                if descriptor is not None:
                    os.close(descriptor)
                if created:
                    path.unlink()
            except Exception:
                pass
        cls = path = owner = tenant = subject = account = audience = refresh_token = enabled = None
        db = descriptor = None
        if error:
            result = None
            _raise(error)
        return result

    @contextmanager
    def _guard(self):
        # Local fixture directory and lock inode must remain exclusively owned.
        # Never unlink a live lock file: kernel ownership ends on process death.
        with open(str(self.path) + '.lock', 'a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    @contextmanager
    def _transaction(self):
        db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True,
                             timeout=0, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.execute('COMMIT')
        finally:
            db.close()

    def _bound(self, db, claim, revision, epoch):
        _counter(revision)
        _counter(epoch)
        canonical = _claim(claim)
        row = db.execute('SELECT * FROM credential WHERE id=1').fetchone()
        _require(row is not None and row['owner'] == claim.identity.user_id
                 and row['tenant'] == claim.identity.tenant_id and row['epoch'] == epoch)
        return row, canonical

    def _receipt(self, db, attempt, canonical, revision, epoch):
        _text(attempt, 128)
        row = db.execute('SELECT * FROM rotation WHERE attempt=?', (attempt,)).fetchone()
        if row is not None:
            _require((row['claim'], row['revision'], row['epoch']) == (canonical, revision, epoch))
        return row

    def _reserve(self, claim, revision, epoch, attempt):
        with self._transaction() as db:
            row, canonical = self._bound(db, claim, revision, epoch)
            prior = self._receipt(db, attempt, canonical, revision, epoch)
            if prior is not None:
                return None, RotationOutcome(prior['state'], prior['result_revision'], epoch)
            _require(row['revision'] == revision and row['state'] == 'ready')
            db.execute('INSERT INTO rotation VALUES (?,?,?,?,?,?)',
                       (attempt, canonical, revision, epoch, 'pending', revision))
            db.execute("UPDATE credential SET state='pending' WHERE id=1")
            return dict(row), None

    def _commit(self, claim, revision, epoch, attempt, token, refresh, identity):
        with self._transaction() as db:
            row, canonical = self._bound(db, claim, revision, epoch)
            receipt = self._receipt(db, attempt, canonical, revision, epoch)
            _require(row['state'] == 'pending' and row['revision'] == revision
                     and receipt is not None and receipt['state'] == 'pending')
            db.execute("UPDATE credential SET state='ready', revision=?, access_token=?, "
                       'refresh_token=?, expires_at=? WHERE id=1',
                       (revision + 1, token, refresh, identity.expires_at))
            db.execute("UPDATE rotation SET state='committed', result_revision=? WHERE attempt=?",
                       (revision + 1, attempt))
        return RotationOutcome('committed', revision + 1, epoch)

    def _recover(self, claim, revision, epoch, attempt):
        with self._transaction() as db:
            row, canonical = self._bound(db, claim, revision, epoch)
            receipt = self._receipt(db, attempt, canonical, revision, epoch)
            _require(receipt is not None)
            if receipt['state'] == 'pending':
                _require(row['revision'] == revision and row['state'] == 'pending')
                db.execute("UPDATE credential SET state='reauthentication_required' WHERE id=1")
                db.execute("UPDATE rotation SET state='reauthentication_required' WHERE attempt=?", (attempt,))
                return RotationOutcome('reauthentication_required', revision, epoch)
            return RotationOutcome(receipt['state'], receipt['result_revision'], epoch)

    def recover(self, claim, revision, epoch, attempt):
        """Conservatively fence an uncertain attempt, even if its old worker lives."""
        outcome = error = None
        try:
            with self._guard():
                outcome = self._recover(claim, revision, epoch, attempt)
        except Exception:
            error = CustodyError
        self = claim = revision = epoch = attempt = None
        if error:
            _raise(error)
        return outcome

    def rotate(self, control, claim, revision, epoch, attempt, *, transport, jwks):
        outcome, category = self._rotate(control, claim, revision, epoch, attempt, transport, jwks)
        self = control = claim = revision = epoch = attempt = transport = jwks = None
        if category:
            outcome = None
            _raise(category)
        return outcome

    def _rotate(self, control, claim, revision, epoch, attempt, transport, jwks):
        outcome = category = None
        try:
            with self._guard():
                outcome, category = self._rotate_locked(control, claim, revision, epoch, attempt, transport, jwks)
            if category is None:
                control.remaining_seconds()
        except Exception as error:
            outcome, category = None, _failure(control, error, category)
        return outcome, category

    def _rotate_locked(self, control, claim, revision, epoch, attempt, transport, jwks):
        reserved = False
        try:
            import httpx

            _require(type(transport) is httpx.MockTransport)
            control.remaining_seconds()
            row, prior = self._reserve(claim, revision, epoch, attempt)
            if prior is not None:
                return prior, None
            reserved = True
            control.remaining_seconds()
            exchange = BoundedAuthExchange(control, transport=transport, enabled=True)
            try:
                raw = exchange.refresh(row['refresh_token']).body
            except Exception:
                try:
                    exchange.close()
                except Exception:
                    pass
                raise
            else:
                exchange.close()
            _require(type(raw) is bytes and len(raw) <= MAX_REPLY)
            reply = _json(raw)
            _require(set(reply) == {'access_token', 'refresh_token', 'token_type'})
            _require(reply['token_type'] == 'Bearer')
            refresh = _fixture_refresh(reply['refresh_token'])
            identity = validate_identity(control, reply['access_token'], jwks,
                expected_subject=row['subject'], expected_account_id=row['account'],
                expected_audience=row['audience'], enabled=True)
            control.remaining_seconds()
            return self._commit(claim, revision, epoch, attempt,
                                reply['access_token'], refresh, identity), None
        except Exception as error:
            category = _failure(control, error)
            if reserved:
                try:
                    self._recover(claim, revision, epoch, attempt)
                except Exception:
                    # A failed recovery leaves durable pending ownership, never ready.
                    pass
            return None, category

    def revoke_fixture(self, claim, revision, epoch):
        """Fence future synthetic credential use; does not prove remote stop."""
        result = error = None
        row = db = None
        try:
            with self._guard(), self._transaction() as db:
                row, _ = self._bound(db, claim, revision, epoch)
                _require(row['revision'] == revision)
                db.execute("UPDATE credential SET state='revoked', revision=?, epoch=?, "
                           'access_token=NULL, expires_at=NULL WHERE id=1',
                           (revision + 1, epoch + 1))
                result = RotationOutcome('revoked', revision + 1, epoch + 1)
        except Exception:
            error = CustodyError
        self = claim = revision = epoch = row = db = None
        if error:
            _raise(error)
        return result

    def reauthenticate_fixture(self, claim, revision, epoch, refresh_token):
        """Explicit fake enrollment only; no login, discovery or provider call."""
        result = error = None
        row = db = None
        try:
            _fixture_refresh(refresh_token)
            with self._guard(), self._transaction() as db:
                row, _ = self._bound(db, claim, revision, epoch)
                _require(row['revision'] == revision and row['state'] != 'ready')
                db.execute("UPDATE rotation SET state='reauthentication_required' WHERE state='pending'")
                db.execute("UPDATE credential SET state='ready', revision=?, epoch=?, "
                           'access_token=NULL, expires_at=NULL, refresh_token=? WHERE id=1',
                           (revision + 1, epoch + 1, refresh_token))
                result = RotationOutcome('ready', revision + 1, epoch + 1)
        except Exception:
            error = CustodyError
        self = claim = revision = epoch = refresh_token = None
        row = db = None
        if error:
            _raise(error)
        return result
