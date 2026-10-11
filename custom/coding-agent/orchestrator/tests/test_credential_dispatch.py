"""Real custody/ledger/SDK/runner with fixture-only transport, no network."""
from contextlib import contextmanager, redirect_stderr
from dataclasses import replace
import io
import gc
import json
from pathlib import Path
import pickle
import socket
import tempfile
import threading
import time
import traceback
import unittest
import uuid
from unittest.mock import patch

import httpx
import test_auth_custody as custody_fixtures
from test_bounded_llm import synthetic_llm, function_call_response
from test_openhands_profile import unused_factory
from coding_executor.executions import ExecutionService, Observation
from coding_orchestrator.auth_custody import CustodyError, SyntheticCredentialCustodian
from coding_orchestrator.bounded_llm import BoundedResponses, RESPONSES_URL
from coding_orchestrator.credential_dispatch import SyntheticCredentialDispatch
from coding_orchestrator.job_worker import RunContext, WorkerCancelled, WorkerDeadline, WorkerLimit
from coding_orchestrator.openhands_profile import OpenHandsJobRunner
from coding_orchestrator.sdk_dispatch import ClaimDispatch


class Authority:
    authority_id = 'fixture-authority'

    def launch(self, claim):
        return Observation(claim, 'running', False)

    def stop(self, claim):
        pass  # Seal is authoritative for future admission, never remote stop.

    def observe(self, claim):
        return Observation(claim, 'unknown', False)


class CredentialDispatchTests(unittest.TestCase):
    token = custody_fixtures.CustodyTests.token
    payload = custody_fixtures.CustodyTests.payload
    create = custody_fixtures.CustodyTests.create

    @classmethod
    def setUpClass(cls):
        custody_fixtures.CustodyTests.setUpClass.__func__(cls)

    def setUp(self):
        import litellm
        from openhands.sdk.llm.auth import CredentialStore, OpenAISubscriptionAuth
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.control = custody_fixtures.control()
        self.control._maximum = 10
        self.control._deadline = time.monotonic() + 60
        self.ledger = ExecutionService(self.root / 'ledger', Authority())
        self.addCleanup(self.ledger.close)
        identity = custody_fixtures.claim().identity
        self.ledger.advance(identity)
        self.claim = self.ledger.start(identity, 'operation', 'a' * 64).operations[0].claim
        self.ledger.configure_dispatch(self.claim, max_requests=10, timeout_seconds=60,
                                       deadline_monotonic=self.control._deadline)
        self.path = self.root / 'custody.sqlite'
        self.store = self.create(self.path)
        self.access = self.token()
        self.store.rotate(self.control, self.claim, 0, 0, 'rotation',
            transport=httpx.MockTransport(lambda _: httpx.Response(200,
                headers={'content-type': 'application/json'}, json=self.payload(access_token=self.access))),
            jwks=self.jwks)
        self.calls = []
        self.guards = []
        for owner, method in ((socket, 'getaddrinfo'), (socket.socket, 'connect'),
                              (socket.socket, 'connect_ex'), (CredentialStore, 'get'),
                              (CredentialStore, 'save'), (OpenAISubscriptionAuth, 'refresh_if_needed_sync')):
            guard = patch.object(owner, method, side_effect=AssertionError('No network or credentials'))
            self.guards.append(guard.start())
            self.addCleanup(guard.stop)
        retry = patch.object(litellm, 'num_retries', None)
        retry.start()
        self.addCleanup(retry.stop)

    def tearDown(self):
        for guard in self.guards:
            guard.assert_not_called()

    def adapter(self, **changes):
        return SyntheticCredentialDispatch(**{
            'custody': self.store, 'ledger': self.ledger, 'claim': self.claim,
            'revision': 1, 'epoch': 0, 'control': self.control, 'enabled': True, **changes})

    def new_execution(self, owner='owner'):
        self.ledger.close()
        self.ledger = ExecutionService(self.root / uuid.uuid4().hex, Authority())
        self.addCleanup(self.ledger.close)
        identity = custody_fixtures.claim(owner).identity
        self.ledger.advance(identity)
        self.claim = self.ledger.start(identity, 'operation', 'a' * 64).operations[0].claim
        self.ledger.configure_dispatch(self.claim, max_requests=10, timeout_seconds=60,
                                       deadline_monotonic=self.control._deadline)

    def request(self):
        return httpx.Request('POST', RESPONSES_URL, json={'model': 'gpt-5.6-sol'},
                             headers={'authorization': 'Bearer synthetic-placeholder'})

    def transport(self, handler=None):
        def send(request):
            self.assertEqual(request.headers['authorization'], 'Bearer ' + self.access)
            self.assertEqual(request.headers['chatgpt-account-id'], 'account')
            self.calls.append(request)
            return handler(request) if handler else function_call_response(('finish', {'message': 'Done.'}))
        return httpx.MockTransport(send)

    def messages(self):
        from openhands.sdk.llm import Message, TextContent
        return [Message(role='user', content=[TextContent(text='Synthetic fixture only.')])]

    def test_real_sdk_uses_committed_pair_and_durable_actions_without_token_export(self):
        request = self.request()
        dispatch = self.adapter()
        response = dispatch(request, self.transport())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.headers['authorization'], 'Bearer synthetic-placeholder')
        self.assertNotIn('authorization', self.calls[0].headers)
        llm = synthetic_llm()
        with BoundedResponses(llm, self.control, transport=self.transport(),
                              synthetic_dispatch=dispatch) as bounded:
            result = llm.generate(self.messages())
            self.assertEqual(result.message.tool_calls[0].name, 'finish')
            bounded.assert_bound(llm)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.control._counter.value, 3)  # rotation + two model requests
        rows = self.ledger._db.execute('SELECT action_id,state FROM dispatch_actions').fetchall()
        self.assertEqual([tuple(r) for r in rows], [('model-0', 'complete'), ('model-1', 'complete')])
        for value in (repr(llm), repr(rows), repr(response), repr(self.calls)):
            self.assertNotIn(self.access, value)
        with self.assertRaises(TypeError):
            pickle.dumps(dispatch)
        with self.assertRaises(TypeError):
            pickle.dumps(self.store)

    def test_default_off_live_transport_and_forged_claims_do_not_dispatch(self):
        with self.assertRaises(CustodyError):
            self.adapter(enabled=False)
        with self.assertRaises(CustodyError):
            self.adapter()(self.request(), object())
        changes = [
            {'claim': replace(self.claim, identity=replace(self.claim.identity, user_id='other'))},
            {'claim': replace(self.claim, identity=replace(self.claim.identity, tenant_id='other'))},
            {'claim': replace(self.claim, attempt_id='forged')},
            {'claim': replace(self.claim, authority_id='forged')},
            {'revision': 0}, {'epoch': 1},
        ]
        for change in changes:
            if 'claim' not in change:
                self.new_execution()
            with self.subTest(change=change), self.assertRaises(CustodyError):
                self.adapter(**change)(self.request(), self.transport())
        self.assertEqual(self.calls, [])
        self.assertEqual(self.control._counter.value, 1)

    def test_expired_access_and_revoked_execution_or_credential_block_wire(self):
        with patch('coding_orchestrator.credential_dispatch.time.time', return_value=time.time() + 1000):
            with self.assertRaises(CustodyError):
                self.adapter()(self.request(), self.transport())
        # A fresh claim uses its own fixture, so an earlier consumed action cannot mask revocation.
        self.new_execution()
        self.ledger.stop(self.claim.identity)
        with self.assertRaises(CustodyError):
            self.adapter()(self.request(), self.transport())
        result = self.store.revoke_fixture(self.claim, 1, 0)
        self.assertEqual((result.state, result.revision, result.epoch), ('revoked', 2, 1))
        self.assertEqual(self.calls, [])

    def test_admitted_claim_for_another_owner_cannot_use_custody(self):
        self.new_execution(owner='other')
        with self.assertRaises(CustodyError):
            self.adapter()(self.request(), self.transport())
        self.assertEqual(self.calls, [])

    def test_credential_revocation_before_first_admission_blocks_stale_revision_and_epoch(self):
        self.store.revoke_fixture(self.claim, 1, 0)
        for revision, epoch in ((1, 0), (2, 1)):
            self.new_execution()
            with self.assertRaises(CustodyError):
                self.adapter(revision=revision, epoch=epoch)(self.request(), self.transport())
        self.assertEqual(self.calls, [])

    def test_cancel_deadline_and_budget_remain_native_and_never_dispatch(self):
        for category in (WorkerCancelled, WorkerDeadline, WorkerLimit):
            value = custody_fixtures.control()
            if category is WorkerCancelled:
                value._cancelled.set()
            elif category is WorkerDeadline:
                value._deadline = time.monotonic() - 1
            else:
                value._maximum = 0
            with self.subTest(category=category), self.assertRaises(category):
                self.adapter(control=value)(self.request(), self.transport())
        self.assertEqual(self.calls, [])

    def test_ledger_deadline_expires_before_model_admission(self):
        self.ledger._dispatch_deadlines[self.claim.attempt_id] = time.monotonic() - 1
        with self.assertRaises(CustodyError):
            self.adapter()(self.request(), self.transport())
        self.assertEqual(self.calls, [])

    def test_delayed_dispatch_loses_to_revocation_before_final_fence(self):
        entered, release = threading.Event(), threading.Event()
        original = self.ledger.synthetic_dispatch_fence

        @contextmanager
        def delayed(*args, **kwargs):
            entered.set()
            self.assertTrue(release.wait(5))
            with original(*args, **kwargs) as deadline:
                yield deadline

        errors = []
        def run():
            try:
                self.adapter()(self.request(), self.transport())
            except CustodyError:
                errors.append(True)
        with patch.object(self.ledger, 'synthetic_dispatch_fence', delayed):
            worker = threading.Thread(target=run)
            worker.start()
            try:
                self.assertTrue(entered.wait(5))
                state = self.ledger.stop(self.claim.identity)
                self.assertTrue(state.sealed)
            finally:
                release.set()
                worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [True])
        self.assertEqual(self.calls, [])

    def test_dispatch_winning_fence_orders_revocation_ack_and_two_worker_duplicate(self):
        entered, release, revoked = threading.Event(), threading.Event(), threading.Event()
        results, errors = [], []
        def send(_):
            entered.set()
            self.assertTrue(release.wait(5))
            return function_call_response(('finish', {'message': 'Done.'}))
        def run(dispatch):
            try:
                results.append(dispatch(self.request(), self.transport(send)).status_code)
            except CustodyError:
                errors.append(True)
        first = threading.Thread(target=run, args=(self.adapter(),))
        second = threading.Thread(target=run, args=(self.adapter(),))
        seal = threading.Thread(target=lambda: (self.ledger.stop(self.claim.identity), revoked.set()))
        first.start()
        try:
            self.assertTrue(entered.wait(5))
            second.start()
            seal.start()
            self.assertFalse(revoked.wait(.05))
            with self.assertRaises(CustodyError):
                self.store.revoke_fixture(self.claim, 1, 0)
        finally:
            release.set()
            first.join(5)
            if second.ident is not None:
                second.join(5)
            if seal.ident is not None:
                seal.join(5)
        self.assertTrue(revoked.is_set())
        self.assertEqual(results, [200])
        self.assertEqual(errors, [True])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.control._counter.value, 2)

    def test_cancelled_after_action_admission_before_wire_stays_native(self):
        original = self.ledger.synthetic_dispatch_fence
        @contextmanager
        def cancel(*args, **kwargs):
            self.control._cancelled.set()
            with original(*args, **kwargs) as deadline:
                yield deadline
        with patch.object(self.ledger, 'synthetic_dispatch_fence', cancel), self.assertRaises(WorkerCancelled):
            self.adapter()(self.request(), self.transport())
        self.assertEqual(self.calls, [])

    def test_post_dispatch_cancellation_preserves_single_use_and_scrubs_wire(self):
        def cancel(_):
            self.control._cancelled.set()
            return function_call_response(('finish', {'message': 'Done.'}))
        with self.assertRaises(WorkerCancelled):
            self.adapter()(self.request(), self.transport(cancel))
        self.assertEqual(len(self.calls), 1)
        self.assertNotIn('authorization', self.calls[0].headers)
        self.assertTrue(self.ledger.status(self.claim.identity).sealed)

    def test_ledger_deadline_expiring_during_custody_read_blocks_physical_dispatch(self):
        original = self.store._transaction
        now = time.monotonic()
        self.control._deadline = now + 600
        with patch('coding_orchestrator.credential_dispatch.time.monotonic', return_value=now) as clock:
            @contextmanager
            def delayed():
                with original() as db:
                    yield db
                clock.return_value = now + 61
            with patch.object(self.store, '_transaction', delayed), self.assertRaises(CustodyError):
                self.adapter()(self.request(), self.transport())
        self.assertEqual(self.calls, [])
        self.assertEqual(self.control._counter.value, 1)

    def test_failed_wire_is_terminal_across_adapter_recreation_and_sanitized(self):
        def fail(request):
            raise RuntimeError(request.headers['authorization'])
        dispatch = self.adapter()
        for attempt in (dispatch, dispatch, self.adapter()):
            try:
                attempt(self.request(), self.transport(fail))
            except CustodyError as error:
                self.assertIsNone(error.__context__)
                self.assertIsNone(error.__cause__)
                trace = error.__traceback__
                while trace:
                    if trace.tb_frame.f_globals.get('__name__') == 'coding_orchestrator.credential_dispatch':
                        self.assertEqual(trace.tb_frame.f_code.co_name, '__call__')
                        self.assertNotIn(self.access, repr(trace.tb_frame.f_locals))
                    trace = trace.tb_next
            else:
                self.fail('Expected sanitized denial')
        self.assertEqual(len(self.calls), 1)

        self.assertNotIn('authorization', self.calls[0].headers)
        state = self.ledger.status(self.claim.identity)
        self.assertTrue(state.sealed)
        self.assertEqual(state.operations[0].state, 'unknown')
        self.assertEqual(self.ledger._db.execute('SELECT state FROM dispatch_actions').fetchone()[0], 'unknown')
        recreated = self.adapter()
        recreated._sequence = 1  # Even a different action cannot follow an ambiguous outcome.
        with self.assertRaises(CustodyError):
            recreated(self.request(), self.transport())
        self.assertEqual(len(self.calls), 1)

    def test_counter_lock_wait_cannot_outlive_the_shorter_ledger_deadline(self):
        now = time.monotonic()
        self.control._deadline = now + 600
        entered = threading.Event()
        original = self.control.before_provider_request
        errors = []
        def account():
            entered.set()
            original()
        def run():
            try:
                self.adapter()(self.request(), self.transport())
            except CustodyError:
                errors.append(True)
        with patch('coding_orchestrator.credential_dispatch.time.monotonic', return_value=now) as clock, \
                patch.object(self.control, 'before_provider_request', account):
            lock = self.control._counter.get_lock()
            lock.acquire()
            worker = threading.Thread(target=run)
            worker.start()
            try:
                self.assertTrue(entered.wait(5))
                clock.return_value = now + 61
            finally:
                lock.release()
                worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [True])
        self.assertEqual(self.calls, [])
        self.assertEqual(self.control._counter.value, 2)  # Reservation is conservative; no wire request.

    def test_compressed_or_oversized_reply_is_rejected_without_decode_or_retry(self):
        from coding_orchestrator.credential_dispatch import MAX_FIXTURE_RESPONSE
        for compressed in (True, False):
            self.new_execution()
            read = []
            class Stream(httpx.SyncByteStream):
                def __iter__(stream):
                    read.append(True)
                    yield b'x' * (MAX_FIXTURE_RESPONSE + 1)
            response = httpx.Response(200, stream=Stream(),
                headers={'content-encoding': 'gzip'} if compressed else {})
            with self.assertRaises(CustodyError):
                self.adapter()(self.request(), self.transport(lambda _: response))
            self.assertEqual(read, [] if compressed else [True])

    def test_stream_control_failure_survives_failing_close(self):
        for category in (WorkerCancelled, WorkerDeadline, WorkerLimit):
            self.new_execution()
            class Stream(httpx.SyncByteStream):
                def __iter__(stream):
                    raise category()
                    yield b''
                def close(stream):
                    raise RuntimeError('synthetic close failure')
            response = httpx.Response(200, stream=Stream())
            with self.assertRaises(category):
                self.adapter()(self.request(), self.transport(lambda _: response))

    def test_generator_finalization_is_owned_sanitized_and_preserves_control(self):
        from coding_orchestrator.credential_dispatch import MAX_FIXTURE_RESPONSE
        for cancelled in (False, True):
            self.new_execution()
            closed, unraisable = [], []
            stderr = io.StringIO()
            class Stream(httpx.SyncByteStream):
                def __iter__(stream):
                    try:
                        if cancelled:
                            self.control._cancelled.set()
                        yield b'x' * (MAX_FIXTURE_RESPONSE + 1)
                    finally:
                        closed.append(True)
                        raise RuntimeError('Bearer ' + self.access)
            response = httpx.Response(200, stream=Stream())
            with patch('sys.unraisablehook', lambda event: unraisable.append(event)), redirect_stderr(stderr):
                with self.assertRaises(WorkerCancelled if cancelled else CustodyError):
                    self.adapter()(self.request(), self.transport(lambda _: response))
                gc.collect()
            self.control._cancelled.clear()
            self.assertEqual(closed, [True])
            self.assertEqual(unraisable, [])
            self.assertNotIn(self.access, stderr.getvalue())

    def test_reflected_credential_is_rejected_before_sdk_consumes_response(self):
        with self.assertRaises(CustodyError):
            self.adapter()(self.request(), self.transport(lambda _: httpx.Response(200, content=self.access)))
        self.assertEqual(len(self.calls), 1)

    def test_sensitive_response_headers_cannot_hide_reflected_credentials(self):
        for header in ('Authorization', 'Proxy-Authorization', 'x-fixture'):
            self.new_execution()
            response = httpx.Response(200, headers={header: 'Bearer ' + self.access}, content=b'{}')
            with self.subTest(header=header), self.assertRaises(CustodyError):
                self.adapter()(self.request(), self.transport(lambda _: response))

    def test_runner_sdk_loop_rotation_and_progress_are_secret_free(self):
        from test_profile_sdk_integration import fixture_llm, FixtureTransport
        from coding_orchestrator.openhands_backend import OpenHandsBackend
        from coding_orchestrator.restricted_agent import RestrictedOpenHandsAgent
        # Substitute only the executor tool catalog: this slice performs a real
        # SDK finish-only loop without MCP discovery or any socket connection.
        def agent(backend):
            return RestrictedOpenHandsAgent(llm=backend._llm, tools=[],
                include_default_tools=['FinishTool'], mcp_config={})
        runner = OpenHandsJobRunner('https://fixture.invalid/mcp', unused_factory, fixture_llm,
            synthetic_model_factory=ClaimDispatch(self.claim, unused_factory))
        encoded = pickle.dumps(runner)
        self.assertNotIn(self.access.encode(), encoded)
        self.assertNotIn(b'synthetic-original', encoded)
        fixture = FixtureTransport('finish', 'read_only')()
        runner = replace(runner, token_factory=lambda: 'synthetic-executor',
            transport_factory=lambda: self.transport(fixture.handle_request),
            synthetic_model_factory=ClaimDispatch(self.claim, lambda claim, control: self.adapter(
                claim=claim, control=control)))
        context = RunContext(self.claim.identity.job_id, 'Finish this synthetic fixture.',
                             'repo', 'read_only', self.claim.identity.execution_id)
        progress = []
        with patch.object(OpenHandsBackend, 'probe'), \
                patch.object(OpenHandsBackend, '_build_agent', agent), \
                patch('coding_orchestrator.openhands_backend.EXPECTED_OPENHANDS_RUNTIME_TOOLS', {'finish'}), \
                patch.object(self.control, 'emit_progress', lambda value: progress.append(value)):
            try:
                result = runner(context, self.control)
            except Exception as error:
                source = error.__context__ or error
                locations = [(frame.name, frame.lineno) for frame in traceback.extract_tb(source.__traceback__)]
                self.fail(f'Runner fixture failed: {type(source).__name__} at {locations}')
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.control._counter.value, 2)
        self.assertIn('Fixture complete.', result['final_response'])
        self.assertNotIn(self.access, json.dumps({'result': result, 'progress': progress}))
        self.assertNotIn('synthetic-replacement', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
