"""Actual SDK -> synthetic HTTP -> persisted claim -> real disposable workspace."""
from contextlib import contextmanager
from dataclasses import dataclass, replace
from functools import partial
import asyncio
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import threading
import time
import unittest

from test_worker_supervisor import FencedFixture, attempt_token
from test_profile_sdk_integration import FixtureTransport, GuardedFixtureRunner, fixture_llm, fixture_token, COMMAND as ORIGINAL_COMMAND, BEFORE
from coding_executor.dispatch import FencedWorkspace
from coding_executor.executions import ExecutionConflict, ExecutionService
from coding_executor.sdk import SDKWorkspace
from coding_executor.workspaces import WorkspaceManager
from coding_orchestrator.job_store import JobStore
from coding_orchestrator.jobs import JobService, JobRequest, Principal, RunScope
from coding_orchestrator.openhands_profile import create_openhands_profile
from coding_orchestrator.sdk_dispatch import bind_sdk_runner
from coding_orchestrator.worker_supervisor import LedgerWorkerSupervisor

COMMAND = "git diff --check"


@dataclass(frozen=True)
class DispatchFactory:
    endpoint: str

    def __call__(self, claim, control):
        def dispatch(action_id, operation, arguments, *, timeout_seconds):
            import httpx
            with httpx.Client(trust_env=False, timeout=timeout_seconds) as client:
                response = client.post(self.endpoint.replace('/mcp', '/dispatch'),
                    headers={"Authorization": "Bearer " + attempt_token(claim)},
                    json={"action_id": action_id, "operation": operation, "arguments": arguments})
                response.raise_for_status()
                return response.json()
        return dispatch


@dataclass(frozen=True)
class WorkspaceTransport:
    def __call__(self):
        import httpx
        transport = FixtureTransport("readonly", "read_only")()
        task = None
        def respond(request):
            nonlocal task
            match = re.search(r"preview-[a-f0-9]+-[a-f0-9]{8}", request.content.decode())
            if match:
                task = match.group()
            response = transport.handle_request(request)
            response.read()
            body = response.json()
            if task:
                for call in body['output']:
                    call['arguments'] = call['arguments'].replace('fix-fixture', task).replace(ORIGINAL_COMMAND, COMMAND)
            return httpx.Response(200, json=body)
        return httpx.MockTransport(respond)


@dataclass(frozen=True)
class DiagnosticRunner:
    runner: object
    path: str

    def __call__(self, context, control):
        import sys
        errors = []
        def trace(frame, event, arg):
            if event == 'exception' and '/coding_orchestrator/' in frame.f_code.co_filename:
                errors.append([frame.f_code.co_name, type(arg[1]).__name__, str(arg[1])])
            return trace
        sys.settrace(trace)
        try:
            return self.runner(context, control)
        finally:
            sys.settrace(None)
            Path(self.path).write_text(json.dumps(errors[-20:]))


class DispatchFixture(FencedFixture):
    lost_reply = False
    delay = 0

    def application(self, app):
        async def combined(scope, receive, send):
            if scope['type'] != 'http' or scope['path'] != '/dispatch':
                return await app(scope, receive, send)
            from starlette.requests import Request
            from starlette.responses import JSONResponse
            body = await Request(scope, receive).json()
            try:
                if self.delay:
                    await asyncio.sleep(self.delay)
                result = await asyncio.to_thread(self.sdk.dispatch, self.claim,
                    body['action_id'], body['operation'], body['arguments'])
                self.frames.append(body)
                response = JSONResponse(result, status_code=503 if self.lost_reply else 200)
            except Exception:
                response = JSONResponse({'error': 'unconfirmed'}, status_code=409)
            await response(scope, receive, send)
        return combined


class SDKDispatchTests(unittest.TestCase):
    @contextmanager
    def job(self, *, lost=False, prepare=None):
        with tempfile.TemporaryDirectory() as root, DispatchFixture(root) as fixture, \
                JobStore(Path(root) / 'jobs.sqlite') as store:
            owner = Principal('owner', 'tenant')
            adapter = LedgerWorkerSupervisor(Path(root) / 'ledger', authority=fixture,
                identity_for=lambda context: store.execution_identity(owner.user_id, owner.tenant_id, context.job_id),
                bind_runner=lambda runner, claim: DiagnosticRunner(GuardedFixtureRunner(
                    bind_sdk_runner(replace(runner, token_factory=partial(attempt_token, claim)),
                                    claim, DispatchFactory(fixture.endpoint)), fixture.endpoint), str(Path(root) / "diagnostic.json")),
                prepare_dispatch=lambda claim, **limits: (prepare(claim) if prepare else None,
                                                         fixture.workspace.admit(claim, **limits)))
            fixture.inspect = adapter.ledger.status
            repositories = Path(root) / 'repositories'
            repositories.mkdir()
            fixture.source.rename(repositories / 'fixture')
            fixture.source = repositories / 'fixture'
            tasks = Path(root) / 'tasks'
            tasks.mkdir()
            fixture.workspace = FencedWorkspace(adapter.ledger, WorkspaceManager(repositories, tasks),
                enabled=True, authorize=lambda identity: identity.user_id == owner.user_id
                    and identity.tenant_id == owner.tenant_id and identity.repository_alias == 'fixture',
                checks={'fixture': COMMAND})
            fixture.sdk = SDKWorkspace(fixture.workspace)
            fixture.frames, fixture.lost_reply = [], lost
            profile = create_openhands_profile(profile_id='fixture-sdk-dispatch', repository_aliases=frozenset({'fixture'}),
                endpoint=fixture.endpoint, token_factory=fixture_token, llm_factory=fixture_llm,
                transport_factory=WorkspaceTransport(), authorize=lambda *_: True,
                confirm_stopped=adapter.confirm_stopped)
            service = JobService(store, profile=profile, enabled=True, worker_factory=adapter.worker_factory)
            try:
                yield service, fixture, owner, adapter
            finally:
                service.close()
                adapter.close()

    def request(self):
        return JobRequest('Inspect the fixture.', 'key', 'generation', 1,
                          RunScope('fixture', 'read_only'), timeout_seconds=60)

    def wait(self, service, owner, run):
        deadline = time.monotonic() + 70
        while run['state'] in {'queued', 'running', 'cancelling'} and time.monotonic() < deadline:
            time.sleep(.02)
            run = service.get_run(owner, run['job_id'])
        self.assertNotIn(run['state'], {'queued', 'running', 'cancelling'}, run)
        return run

    def test_real_sdk_actions_use_durable_receipts_and_host_owned_task(self):
        with self.job() as (service, fixture, owner, adapter):
            run = self.wait(service, owner, service.start_run(owner, self.request()))
            self.assertEqual(run['state'], 'completed', (run, (fixture.source.parent.parent / 'diagnostic.json').read_text()))
            self.assertTrue(run['result']['evidence']['evidence_complete'])
            self.assertEqual([c['exit_code'] for c in run['result']['evidence']['checks']], [0])
            self.assertEqual(fixture.calls, [])  # None of the legacy MCP methods executed.
            self.assertEqual([f['operation'] for f in fixture.frames],
                             ['create_task', 'read_file', 'run_check', 'git_diff', 'task_status'])
            self.assertEqual(fixture.frames[0]['action_id'], hashlib.sha256(b'call_1_0').hexdigest())
            rows = adapter.ledger._db.execute('SELECT state FROM dispatch_actions').fetchall()
            self.assertEqual([r['state'] for r in rows], ['complete'] * 5)
            task = adapter.ledger.task_for(fixture.claim)
            self.assertEqual(run['result']['evidence']['task']['task_id'], task)
            self.assertEqual((fixture.source / 'calculator.py').read_text(), BEFORE)
            self.assertEqual(service.start_run(owner, self.request()), run)

    def test_lost_dispatch_reply_never_replays_and_restart_rejects_old_claim(self):
        with self.job(lost=True) as (service, fixture, owner, adapter):
            fixture.proof_available = False
            run = self.wait(service, owner, service.start_run(owner, self.request()))
            self.assertNotEqual(run['state'], 'completed')
            self.assertEqual(len(fixture.frames), 1)
            self.assertIsNotNone(adapter.ledger.task_for(fixture.claim))
            self.assertNotEqual(adapter.ledger.status(fixture.claim.identity).state, 'stopped')
            frame = fixture.frames[0]
            with self.assertRaises(ExecutionConflict):
                fixture.sdk.dispatch(fixture.claim, **frame)
            service.close()
            adapter.close()
            with_ledger = ExecutionService(fixture.source.parent.parent / 'ledger', fixture)
            try:
                workspace = FencedWorkspace(with_ledger, fixture.workspace.manager, enabled=True,
                                            authorize=lambda _: True)
                with self.assertRaises(ExecutionConflict):
                    SDKWorkspace(workspace).dispatch(fixture.claim, **frame)
                self.assertNotEqual(with_ledger.status(fixture.claim.identity).state, 'stopped')
            finally:
                with_ledger.close()

    def test_stop_during_admission_never_proves_stop_or_starts_child(self):
        entered, release = threading.Event(), threading.Event()
        def prepare(claim):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('fixture gate timeout')
        with self.job(prepare=prepare) as (service, fixture, owner, adapter):
            request = self.request()
            result = []
            thread = threading.Thread(target=lambda: result.append(service.start_run(owner, request)))
            thread.start()
            try:
                self.assertTrue(entered.wait(3))
                status = adapter.ledger.stop(fixture.claim.identity)
                self.assertTrue(status.sealed)
                self.assertNotEqual(status.state, 'stopped')
                self.assertIsNone(adapter._worker.local)
            finally:
                release.set()
                thread.join(5)
            self.assertFalse(thread.is_alive())
            self.assertEqual(len(result), 1)
            run = self.wait(service, owner, result[0])
            self.assertNotEqual(run['state'], 'completed')
            self.assertEqual(fixture.frames, [])
            self.assertIsNone(adapter._worker.local)

    def test_sdk_translation_rejects_foreign_scope_and_check_commands(self):
        with self.job(lost=True) as (service, fixture, owner, adapter):
            fixture.proof_available = False
            self.wait(service, owner, service.start_run(owner, self.request()))
            claim = fixture.claim
            task = adapter.ledger.task_for(claim)
            for operation, arguments in (
                ('create_task', {'repository': 'other', 'task_name': 'test', 'task_mode': 'read_only'}),
                ('create_task', {'repository': 'fixture', 'task_name': 'test', 'task_mode': 'modification'}),
                ('create_task', {'repository': 'fixture', 'task_name': 'test', 'task_mode': 'read_only', 'base_ref': 'other'}),
                ('read_file', {'task_id': 'other', 'path': 'calculator.py'}),
                ('run_check', {'task_id': task, 'command': 'python attacker.py'}),
                ('read_file', {'task_id': task, 'path': 'calculator.py', 'claim': 'injected'})):
                with self.subTest(operation=operation, arguments=arguments), self.assertRaises((ExecutionConflict, ValueError)):
                    fixture.sdk.dispatch(claim, 'denied', operation, arguments)
            for field in ('user_id', 'tenant_id', 'generation_id', 'repository_alias', 'execution_id'):
                wrong = replace(claim, identity=replace(claim.identity, **{field: 'other'}))
                with self.subTest(field=field), self.assertRaises(ExecutionConflict):
                    fixture.sdk.dispatch(wrong, 'denied', 'read_file', {'task_id': task, 'path': 'calculator.py'})
            self.assertEqual(len(fixture.frames), 1)

    def test_delayed_http_delivery_after_absolute_deadline_has_no_receipt_or_task(self):
        import httpx
        from coding_executor.executions import ExecutionIdentity
        with tempfile.TemporaryDirectory() as root, DispatchFixture(root) as fixture:
            ledger = ExecutionService(Path(root) / 'ledger', fixture)
            fixture.inspect = ledger.status
            identity = ExecutionIdentity('job', 'execution', 'owner', 'tenant', 'generation', 1,
                                         'profile', 'source', 'read_only')
            try:
                ledger.advance(identity)
                claim = ledger.start(identity, 'job-worker', 'a' * 64).operations[0].claim
                tasks = Path(root) / 'tasks'
                tasks.mkdir()
                workspace = FencedWorkspace(ledger, WorkspaceManager(Path(root), tasks),
                                            enabled=True, authorize=lambda value: value == identity)
                workspace.admit(claim, max_requests=4, timeout_seconds=10,
                                deadline_monotonic=time.monotonic() + .1)
                fixture.sdk, fixture.frames, fixture.delay = SDKWorkspace(workspace), [], .2
                response = httpx.post(fixture.endpoint.replace('/mcp', '/dispatch'),
                    headers={'Authorization': 'Bearer ' + attempt_token(claim)},
                    json={'action_id': 'late', 'operation': 'create_task', 'arguments':
                          {'repository': 'source', 'task_name': 'fixture', 'task_mode': 'read_only'}})
                self.assertEqual(response.status_code, 409)
                self.assertEqual(fixture.frames, [])
                self.assertIsNone(ledger.task_for(claim))
                self.assertEqual(ledger._db.execute('SELECT count(*) FROM dispatch_actions').fetchone()[0], 0)
                self.assertNotEqual(ledger.status(identity).state, 'stopped')
            finally:
                ledger.close()


class BoundActionTests(unittest.TestCase):
    def event(self, arguments=None, call_id='call_1'):
        from openhands.sdk.event import ActionEvent
        from openhands.sdk.llm import MessageToolCall
        from openhands.sdk.mcp.definition import MCPToolAction
        arguments = arguments or {'task_id': 'task', 'path': 'example.txt'}
        return ActionEvent(thought=[], tool_name='read_file', tool_call_id=call_id,
            tool_call=MessageToolCall(id=call_id, name='read_file', arguments=json.dumps(arguments), origin='responses'),
            action=MCPToolAction(data=arguments), llm_response_id='response')

    @contextmanager
    def binding(self):
        from coding_orchestrator.job_worker import WorkerControl
        from coding_orchestrator.sdk_dispatch import BoundActions
        with tempfile.TemporaryFile() as output:
            control = WorkerControl(None, threading.Event(), threading.Event(), time.monotonic() + 5, 4, output)
            calls = []
            def dispatch(*args, **kwargs):
                calls.append((args, kwargs))
                return 'fixture'
            yield BoundActions(dispatch, control), calls

    def test_changed_arguments_latch_failure_before_delivery(self):
        from coding_orchestrator.openhands_profile import OpenHandsProfileError
        event = self.event()
        with self.binding() as (actions, calls):
            actions.capture(event)
            changed = self.event({'task_id': 'task', 'path': 'other.txt'})
            with self.assertRaises(OpenHandsProfileError):
                actions.execute('read_file', changed.action)
            with self.assertRaises(OpenHandsProfileError):
                actions.execute('read_file', event.action)
            with self.assertRaises(OpenHandsProfileError):
                actions.capture(self.event(call_id='new'))
            self.assertEqual(calls, [])

    def test_consumed_action_is_never_delivered_twice(self):
        from coding_orchestrator.openhands_profile import OpenHandsProfileError
        event = self.event()
        with self.binding() as (actions, calls):
            actions.capture(event)
            actions.execute('read_file', event.action)
            with self.assertRaises(OpenHandsProfileError):
                actions.execute('read_file', event.action)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0][0], hashlib.sha256(b'call_1').hexdigest())

    def test_expired_worker_deadline_does_not_deliver(self):
        from coding_orchestrator.openhands_profile import OpenHandsProfileError
        with self.binding() as (actions, calls):
            event = self.event()
            actions.capture(event)
            actions.control._deadline = time.monotonic() - 1
            with self.assertRaises(OpenHandsProfileError):
                actions.execute('read_file', event.action)
            self.assertEqual(calls, [])
