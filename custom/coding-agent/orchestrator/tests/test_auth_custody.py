"""Actual SQLite, RSA verification and bounded HTTP; credentials are synthetic."""
from dataclasses import replace
from contextlib import contextmanager
import base64
import io
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs

import httpx
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'executor' / 'src'))
from coding_executor.executions import Claim, ExecutionIdentity
from coding_orchestrator.auth_custody import CustodyError, SyntheticCredentialCustodian
from coding_orchestrator.auth_validation import AUTH_CLAIM, ISSUER
from coding_orchestrator.auth_exchange import CLIENT_ID, TOKEN_URL
from coding_orchestrator.job_worker import WorkerControl, WorkerCancelled, WorkerDeadline, WorkerLimit
from test_bounded_llm import Counter


def control():
    return WorkerControl(Counter(), threading.Event(), threading.Event(),
                         time.monotonic() + 30, 3, io.BytesIO())


def b64(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode()


def claim(owner='owner', attempt='execution-attempt'):
    identity = ExecutionIdentity('job', 'execution', owner, 'tenant', 'generation',
                                 1, 'profile', 'repo', 'read_only')
    return Claim(identity, 'operation', 'a' * 64, attempt, 'authority')


def read_state(path):
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        credential = dict(db.execute('SELECT * FROM credential').fetchone())
        rotations = [dict(row) for row in db.execute('SELECT * FROM rotation ORDER BY attempt')]
        return credential, rotations


class CustodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        n = cls.key.public_key().public_numbers().n.to_bytes(256, 'big')
        cls.jwks = json.dumps({'keys': [{'kty': 'RSA', 'kid': 'fixture', 'n': b64(n), 'e': 'AQAB'}]}).encode()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'custody.sqlite'
        self.store = self.create(self.path)
        self.control = control()
        self.calls = []
        self.guards = []
        from openhands.sdk.llm.auth import CredentialStore, OpenAISubscriptionAuth
        for target in ('socket.getaddrinfo', 'socket.create_connection', 'httpx.Client.send'):
            guard = patch(target, side_effect=AssertionError('Synthetic only'))
            self.guards.append(guard.start())
            self.addCleanup(guard.stop)
        for owner, method in ((CredentialStore, 'get'), (CredentialStore, 'save'),
                              (OpenAISubscriptionAuth, 'refresh_if_needed_sync')):
            guard = patch.object(owner, method, side_effect=AssertionError('No real credential lifecycle'))
            self.guards.append(guard.start())
            self.addCleanup(guard.stop)

    def tearDown(self):
        for guard in self.guards:
            guard.assert_not_called()

    def create(self, path, **changes):
        return SyntheticCredentialCustodian.create_fixture(path, **{
            'owner': 'owner', 'tenant': 'tenant', 'subject': 'subject', 'account': 'account',
            'audience': 'audience', 'refresh_token': 'synthetic-original', 'enabled': True,
            **changes})

    def token(self, **changes):
        now = int(time.time())
        claims = {'iss': ISSUER, 'sub': 'subject', 'aud': 'audience', 'iat': now - 1,
                  'exp': now + 600, AUTH_CLAIM: {'chatgpt_account_id': 'account'}, **changes}
        data = b64(b'{"alg":"RS256","kid":"fixture","typ":"JWT"}') + '.' + b64(json.dumps(claims).encode())
        return data + '.' + b64(self.key.sign(data.encode(), padding.PKCS1v15(), hashes.SHA256()))

    def payload(self, **changes):
        return {'access_token': self.token(), 'refresh_token': 'synthetic-replacement',
                'token_type': 'Bearer', **changes}

    def transport(self, handler=None):
        def send(request):
            self.calls.append(request)
            self.assertEqual((request.method, str(request.url)), ('POST', TOKEN_URL))
            fields = parse_qs(request.content.decode())
            self.assertEqual(fields['client_id'], [CLIENT_ID])
            return handler(request) if handler else httpx.Response(200,
                headers={'content-type': 'application/json'}, json=self.payload())
        return httpx.MockTransport(send)

    def rotate(self, **options):
        values = {'control': self.control, 'claim': claim(), 'revision': 0, 'epoch': 0,
                  'attempt': 'rotation', 'transport': self.transport(), 'jwks': self.jwks, **options}
        return self.store.rotate(**values)

    def test_atomic_success_receipt_recovery_and_no_replay(self):
        def send(request):
            row, receipts = read_state(self.path)
            self.assertEqual((row['state'], receipts[0]['state']), ('pending', 'pending'))
            self.assertEqual(self.control._counter.value, 1)
            self.assertEqual(parse_qs(request.content.decode())['refresh_token'], ['synthetic-original'])
            return httpx.Response(200, headers={'content-type': 'application/json'}, json=self.payload())
        result = self.rotate(transport=self.transport(send))
        self.assertEqual((result.state, result.revision, result.epoch), ('committed', 1, 0))
        reopened = SyntheticCredentialCustodian(self.path, enabled=True)
        self.assertEqual(reopened.recover(claim(), 0, 0, 'rotation'), result)
        self.assertEqual(self.rotate(), result)
        self.assertEqual(len(self.calls), 1)
        row, receipts = read_state(self.path)
        self.assertEqual((row['revision'], row['refresh_token'], receipts[0]['result_revision']),
                         (1, 'synthetic-replacement', 1))
        self.assertTrue(row['access_token'])
        self.assertFalse(hasattr(result, 'access_token'))

    def test_default_off_exclusive_creation_and_fixture_only_transport(self):
        with self.assertRaises(CustodyError):
            SyntheticCredentialCustodian(self.path)
        with self.assertRaises(CustodyError):
            self.create(self.path)
        for value in ('not-a-fixture', '', None):
            with self.assertRaises(CustodyError):
                self.create(Path(self.temp.name) / 'absent.sqlite', refresh_token=value)
        self.assertFalse((Path(self.temp.name) / 'absent.sqlite').exists())
        with self.assertRaises(CustodyError):
            self.rotate(transport=object())
        self.assertEqual(read_state(self.path)[0]['state'], 'ready')
        self.assertEqual(self.calls, [])

    def test_failed_fixture_initialization_removes_only_new_file_and_allows_retry(self):
        connect = sqlite3.connect
        for stage in ('CREATE TABLE', 'INSERT INTO', 'COMMIT', 'commit-ack'):
            with self.subTest(stage=stage):
                path = Path(self.temp.name) / f'failed-{stage}.sqlite'
                closed = []

                class FailingConnection(sqlite3.Connection):
                    def execute(self, sql, *args, **kwargs):
                        if sql.startswith(stage):
                            raise sqlite3.OperationalError('synthetic initialization failure')
                        result = super().execute(sql, *args, **kwargs)
                        if stage == 'commit-ack' and sql == 'COMMIT':
                            raise sqlite3.OperationalError('synthetic lost commit acknowledgment')
                        return result

                    def close(self):
                        super().close()
                        closed.append(True)

                with patch('coding_orchestrator.auth_custody.sqlite3.connect',
                           side_effect=lambda *a, **kw: connect(*a, factory=FailingConnection, **kw)):
                    with self.assertRaises(CustodyError):
                        self.create(path)
                self.assertEqual(closed, [True])
                self.assertFalse(path.exists())
                self.create(path)
                self.assertEqual(read_state(path)[0]['state'], 'ready')
        before = self.path.read_bytes()
        with self.assertRaises(CustodyError):
            self.create(self.path)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.calls, [])

    def test_owner_revision_epoch_and_exact_claim_binding(self):
        for changes in ({'claim': claim('other')}, {'revision': 1}, {'epoch': 1},
                        {'revision': True}, {'epoch': -1}):
            with self.subTest(changes=changes), self.assertRaises(CustodyError):
                self.rotate(**changes)
        self.rotate()
        for changed in (claim('other'), claim(attempt='other-attempt'),
                        replace(claim(), authority_id='other-authority')):
            with self.assertRaises(CustodyError):
                self.store.recover(changed, 0, 0, 'rotation')
        with self.assertRaises(CustodyError):
            self.rotate(attempt='new-with-stale-revision')
        self.assertEqual(len(self.calls), 1)

    def test_invalid_replacement_blocks_until_explicit_fake_reauthentication(self):
        token = self.token(sub='wrong-subject')
        response = self.transport(lambda _: httpx.Response(200,
            headers={'content-type': 'application/json'}, json=self.payload(access_token=token)))
        with self.assertRaises(CustodyError):
            self.rotate(transport=response)
        self.assertEqual(read_state(self.path)[0]['state'], 'reauthentication_required')
        with self.assertRaises(CustodyError):
            self.rotate(attempt='retry')
        self.assertEqual(self.rotate().state, 'reauthentication_required')
        ready = self.store.reauthenticate_fixture(claim(), 0, 0, 'synthetic-user-reauthenticated')
        self.assertEqual((ready.revision, ready.epoch), (1, 1))
        with self.assertRaises(CustodyError):
            self.rotate()
        result = self.rotate(revision=1, epoch=1, attempt='fresh-after-reauth')
        self.assertEqual(result.revision, 2)
        self.assertEqual(len(self.calls), 2)

    def test_missing_duplicate_and_ambiguous_refresh_fields_do_not_reuse_old_token(self):
        cases = [b'{"access_token":"x","token_type":"Bearer"}',
                 b'{"access_token":"x","access_token":"y","refresh_token":"synthetic-x","token_type":"Bearer"}',
                 json.dumps(self.payload(refresh_token='')).encode(),
                 json.dumps(self.payload(token_type='bearer')).encode(),
                 json.dumps(self.payload(unexpected=True)).encode()]
        for index, raw in enumerate(cases):
            self.store = self.create(Path(self.temp.name) / f'bad-{index}.sqlite')
            self.control = control()
            with self.assertRaises(CustodyError):
                self.rotate(transport=self.transport(lambda _, data=raw: httpx.Response(200,
                    headers={'content-type': 'application/json'}, content=data)))
            row, receipts = read_state(self.store.path)
            self.assertEqual((row['refresh_token'], row['access_token'], receipts[0]['state']),
                             ('synthetic-original', None, 'reauthentication_required'))

    def test_paused_before_dispatch_excludes_recovery_and_reauthentication(self):
        from coding_orchestrator.auth_exchange import BoundedAuthExchange
        context = multiprocessing.get_context('fork')
        paused, release = context.Event(), context.Event()
        marker = Path(self.temp.name) / 'delayed.sent'
        def worker():
            original = BoundedAuthExchange.refresh
            def delayed(exchange, token):
                paused.set()
                if not release.wait(10):
                    raise AssertionError('Fixture release missing')
                return original(exchange, token)
            def send(_):
                marker.write_text('sent')
                return httpx.Response(200, headers={'content-type': 'application/json'}, json=self.payload())
            with patch.object(BoundedAuthExchange, 'refresh', delayed):
                SyntheticCredentialCustodian(self.path, enabled=True).rotate(control(), claim(), 0, 0,
                    'rotation', transport=httpx.MockTransport(send), jwks=self.jwks)
        child = context.Process(target=worker)
        child.start()
        try:
            self.assertTrue(paused.wait(10))
            self.assertFalse(marker.exists())
            with self.assertRaises(CustodyError):
                self.store.recover(claim(), 0, 0, 'rotation')
            with self.assertRaises(CustodyError):
                self.store.reauthenticate_fixture(claim(), 0, 0, 'synthetic-new')
            row, _ = read_state(self.path)
            self.assertEqual((row['epoch'], row['state']), (0, 'pending'))
            release.set()
            child.join(10)
            self.assertEqual(child.exitcode, 0)
            self.assertEqual(marker.read_text(), 'sent')
            self.assertEqual(self.store.recover(claim(), 0, 0, 'rotation').state, 'committed')
        finally:
            release.set()
            if child.is_alive():
                child.kill()
            child.join(5)

    def test_sqlite_commit_failures_and_lost_acknowledgement(self):
        for stage in ('reserve', 'replacement', 'acknowledgement'):
            self.store = self.create(Path(self.temp.name) / f'failure-{stage}.sqlite')
            self.calls.clear()
            commits = 0
            class FaultConnection(sqlite3.Connection):
                def execute(inner, sql, parameters=(), /):
                    nonlocal commits
                    if sql == 'COMMIT':
                        commits += 1
                        if ((commits == 1 and stage == 'reserve')
                                or (commits == 2 and stage == 'replacement')):
                            raise sqlite3.OperationalError('synthetic-storage-failure')
                    result = super().execute(sql, parameters)
                    if sql == 'COMMIT' and commits == 2 and stage == 'acknowledgement':
                        raise sqlite3.OperationalError('synthetic-ack-lost')
                    return result
            connect = sqlite3.connect
            def connection(*args, **kwargs):
                return connect(*args, **kwargs, factory=FaultConnection)
            with patch('sqlite3.connect', connection), self.assertRaises(CustodyError):
                self.rotate()
            row, receipts = read_state(self.store.path)
            with self.subTest(stage=stage):
                if stage == 'reserve':
                    self.assertEqual((row['state'], receipts, len(self.calls)), ('ready', [], 0))
                    continue
                state = 'committed' if stage == 'acknowledgement' else 'reauthentication_required'
                recovered = self.store.recover(claim(), 0, 0, 'rotation')
                self.assertEqual(recovered.state, state)
                self.assertEqual(self.rotate(), recovered)
                self.assertEqual(len(self.calls), 1)
                self.assertEqual(row['refresh_token'], 'synthetic-replacement' if stage == 'acknowledgement' else 'synthetic-original')

    def test_control_failures_and_live_traceback_never_expose_credentials(self):
        for index, category in enumerate((WorkerCancelled, WorkerDeadline, WorkerLimit, CustodyError)):
            self.store = self.create(Path(self.temp.name) / f'control-{index}.sqlite')
            self.control = control()
            def fail(_):
                raise category()
            try:
                self.rotate(transport=self.transport(fail))
            except category as error:
                self.assertIsNone(error.__context__)
                self.assertIsNone(error.__cause__)
                trace = error.__traceback__
                while trace:
                    if trace.tb_frame.f_globals.get('__name__') == 'coding_orchestrator.auth_custody':
                        self.assertIn(trace.tb_frame.f_code.co_name, ('rotate', '_raise'))
                        self.assertNotIn('synthetic-original', repr(trace.tb_frame.f_locals))
                        self.assertNotIn('synthetic-replacement', repr(trace.tb_frame.f_locals))
                    trace = trace.tb_next
            else:
                self.fail('Expected sanitized failure')
            self.assertEqual(read_state(self.store.path)[0]['state'], 'reauthentication_required')

    def test_two_process_contention_has_one_dispatch(self):
        context = multiprocessing.get_context('fork')
        entered, release = context.Event(), context.Event()
        outcome = context.Queue()
        def first():
            def send(_):
                entered.set()
                if not release.wait(10):
                    raise AssertionError('Fixture release missing')
                return httpx.Response(200, headers={'content-type': 'application/json'}, json=self.payload())
            result = SyntheticCredentialCustodian(self.path, enabled=True).rotate(
                control(), claim(), 0, 0, 'first', transport=httpx.MockTransport(send), jwks=self.jwks)
            outcome.put(result.state)
        child = context.Process(target=first)
        child.start()
        try:
            self.assertTrue(entered.wait(10))
            with self.assertRaises(CustodyError):
                self.rotate(attempt='contender')
            self.control._cancelled.set()
            with self.assertRaises(WorkerCancelled):
                self.rotate(attempt='cancelled-contender')
            self.control._cancelled.clear()
            self.control._deadline = time.monotonic() - 1
            with self.assertRaises(WorkerDeadline):
                self.rotate(attempt='expired-contender')
            self.control._deadline = time.monotonic() + 30
            with self.assertRaises(CustodyError):
                self.rotate(attempt='first')
            self.assertEqual(self.calls, [])
            release.set()
            child.join(10)
            self.assertEqual(child.exitcode, 0)
            self.assertEqual(outcome.get(timeout=2), 'committed')
            self.assertEqual(len(read_state(self.path)[1]), 1)
        finally:
            release.set()
            if child.is_alive():
                child.kill()
            child.join(5)
            outcome.close()

    def test_lock_cleanup_preserves_primary_control_and_committed_outcome(self):
        for index, category in enumerate((WorkerCancelled, WorkerDeadline, WorkerLimit, CustodyError)):
            self.store = self.create(Path(self.temp.name) / f'cleanup-{index}.sqlite')
            self.control = control()
            original = self.store._guard
            @contextmanager
            def broken_cleanup():
                with original():
                    yield
                raise OSError('synthetic-cleanup-canary')
            def send(_):
                if category is not CustodyError:
                    raise category()
                return httpx.Response(200, headers={'content-type': 'application/json'}, json=self.payload())
            with patch.object(self.store, '_guard', broken_cleanup):
                with self.assertRaises(category):
                    self.rotate(transport=self.transport(send))
            recovered = self.store.recover(claim(), 0, 0, 'rotation')
            self.assertEqual(recovered.state,
                'committed' if category is CustodyError else 'reauthentication_required')

    def test_real_budget_exhaustion_blocks_pending_without_physical_dispatch(self):
        self.control._maximum = 0
        with self.assertRaises(WorkerLimit):
            self.rotate()
        self.assertEqual(self.calls, [])
        self.assertEqual(self.control._counter.value, 0)
        self.assertEqual(self.store.recover(claim(), 0, 0, 'rotation').state,
                         'reauthentication_required')

    def test_control_after_commit_or_cleanup_preserves_recoverable_commit(self):
        for stage in ('commit', 'cleanup'):
            for category in (WorkerCancelled, WorkerDeadline):
                self.store = self.create(Path(self.temp.name) / f'post-{stage}-{category.__name__}.sqlite')
                self.control = control()
                self.calls.clear()
                original_commit, original_guard = self.store._commit, self.store._guard
                def stop():
                    if category is WorkerCancelled:
                        self.control._cancelled.set()
                    else:
                        self.control._deadline = time.monotonic() - 1
                def commit(*args):
                    result = original_commit(*args)
                    if stage == 'commit':
                        stop()
                    return result
                @contextmanager
                def guard():
                    with original_guard():
                        yield
                    if stage == 'cleanup':
                        stop()
                with patch.object(self.store, '_commit', commit), patch.object(self.store, '_guard', guard):
                    with self.assertRaises(category):
                        self.rotate()
                result = self.store.recover(claim(), 0, 0, 'rotation')
                self.assertEqual((result.state, result.revision), ('committed', 1))
                self.assertEqual(self.rotate(control=control()), result)
                self.assertEqual(len(self.calls), 1)
                row, receipts = read_state(self.store.path)
                self.assertEqual(row['refresh_token'], 'synthetic-replacement')
                self.assertTrue(row['access_token'])
                self.assertEqual(receipts[0]['state'], 'committed')

    def test_real_process_crash_intervals_preserve_atomicity_and_never_replay(self):
        context = multiprocessing.get_context('fork')
        for stage in ('reserved', 'response', 'before_commit', 'after_commit'):
            path = Path(self.temp.name) / f'{stage}.sqlite'
            self.create(path)
            marker = Path(self.temp.name) / f'{stage}.sent'
            token = self.token()
            def crash():
                commits = 0
                class CrashConnection(sqlite3.Connection):
                    def execute(inner, sql, parameters=(), /):
                        nonlocal commits
                        if sql == 'COMMIT':
                            commits += 1
                            if commits == 2 and stage == 'before_commit':
                                os._exit(91)
                        result = super().execute(sql, parameters)
                        if sql == 'COMMIT' and ((commits == 1 and stage == 'reserved')
                                               or (commits == 2 and stage == 'after_commit')):
                            os._exit(91)
                        return result
                connect = sqlite3.connect
                def connection(*args, **kwargs):
                    return connect(*args, **kwargs, factory=CrashConnection)
                def send(_):
                    with marker.open('ab') as out:
                        out.write(b'one\n')
                        out.flush()
                        os.fsync(out.fileno())
                    if stage == 'response':
                        os._exit(91)
                    return httpx.Response(200, headers={'content-type': 'application/json'},
                        json=self.payload(access_token=token))
                with patch('sqlite3.connect', connection):
                    SyntheticCredentialCustodian(path, enabled=True).rotate(control(), claim(), 0, 0,
                        'crash', transport=httpx.MockTransport(send), jwks=self.jwks)
            child = context.Process(target=crash)
            child.start()
            child.join(15)
            if child.is_alive():
                child.kill()
                child.join(5)
            with self.subTest(stage=stage):
                self.assertEqual(child.exitcode, 91)
                row, receipts = read_state(path)
                committed = stage == 'after_commit'
                self.assertEqual(row['access_token'], token if committed else None)
                self.assertEqual(row['refresh_token'], 'synthetic-replacement' if committed else 'synthetic-original')
                self.assertEqual(receipts[0]['state'], 'committed' if committed else 'pending')
                reopened = SyntheticCredentialCustodian(path, enabled=True)
                recovered = reopened.recover(claim(), 0, 0, 'crash')
                self.assertEqual(recovered.state, 'committed' if committed else 'reauthentication_required')
                result = reopened.rotate(control(), claim(), 0, 0, 'crash',
                    transport=httpx.MockTransport(lambda _: self.fail('No crash replay')), jwks=self.jwks)
                self.assertEqual(result, recovered)
                self.assertEqual(marker.read_bytes() if marker.exists() else b'', b'' if stage == 'reserved' else b'one\n')


if __name__ == '__main__':
    unittest.main()
