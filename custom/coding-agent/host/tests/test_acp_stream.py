from __future__ import annotations

import copy
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from host_maintenance.acp_stream import AcpInput, BUFFER_BYTES, _interrupted, attach_argv, relay


class AcpInputPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = AcpInput(Path('/approved/tasks/task-one'))

    def message(self, method, params):
        return json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode() + b'\n'

    def test_maps_exact_task_root_across_fragmented_input(self):
        raw = self.message('session/new', {'cwd': '/approved/tasks/task-one', 'mcpServers': []})
        self.assertEqual(self.policy.feed(raw[:20]), b'')
        result = json.loads(self.policy.feed(raw[20:]))
        self.assertEqual(result['params']['cwd'], '/workspace')
        self.assertEqual(result['id'], 1)

    def test_accepts_workspace_root_for_session_operations(self):
        for method in ('session/new', 'session/load', 'session/resume', 'session/fork'):
            result = json.loads(self.policy.feed(self.message(method, {'cwd': '/workspace', 'mcpServers': []})))
            self.assertEqual(result['params']['cwd'], '/workspace')

    def test_rejects_other_host_paths_and_task_subdirectories(self):
        for cwd in ('/', '/home/node', '/approved/tasks/task-two', '/approved/tasks/task-one/subdir', '/workspace/../etc'):
            with self.subTest(cwd=cwd), self.assertRaisesRegex(RuntimeError, 'authorized task'):
                self.policy.feed(self.message('session/new', {'cwd': cwd}))

    def test_rejects_client_mcp_servers(self):
        with self.assertRaisesRegex(RuntimeError, 'MCP servers'):
            self.policy.feed(self.message('session/new', {'cwd': '/workspace', 'mcpServers': [{'command': 'sh'}]}))

    def test_rejects_host_callback_capabilities(self):
        for capabilities in ({'terminal': True}, {'fs': {'readTextFile': True}}, {'fs': {'writeTextFile': True}}):
            with self.subTest(capabilities=capabilities), self.assertRaisesRegex(RuntimeError, 'callbacks'):
                self.policy.feed(self.message('initialize', {'clientCapabilities': capabilities}))

    def test_accepts_explicitly_disabled_callbacks(self):
        raw = self.message('initialize', {'clientCapabilities': {'terminal': False, 'fs': {'readTextFile': False, 'writeTextFile': False}}})
        self.assertEqual(self.policy.feed(raw), raw)

    def test_preserves_prompt_content_and_client_responses(self):
        raw = self.message('session/prompt', {'sessionId': 's1', 'prompt': [{'type': 'text', 'text': 'Keep /approved/tasks/task-one literal'}]})
        raw += b'{"jsonrpc":"2.0","id":7,"result":{"outcome":{"outcome":"cancelled"}}}\n'
        self.assertEqual(self.policy.feed(raw), raw)

    def test_rejects_oversized_or_incomplete_frames(self):
        with self.assertRaisesRegex(RuntimeError, 'frame limit'):
            self.policy.feed(b'x' * BUFFER_BYTES)
        policy = AcpInput(Path('/approved/tasks/task-one'))
        policy.feed(b'{"jsonrpc":')
        with self.assertRaisesRegex(RuntimeError, 'inside a JSON frame'):
            policy.finish()

    def test_rejects_non_json_rpc_input(self):
        for raw in (b'not-json\n', b'[]\n', b'{"method":"session/new"}\n'):
            with self.subTest(raw=raw), self.assertRaises(RuntimeError):
                self.policy.feed(raw)
from host_maintenance.broker import Broker


class AcpAttachPolicyTests(unittest.TestCase):
    def setUp(self):
        self.image = 'sha256:' + 'a' * 64
        self.info = {'Id': 'b' * 64, 'Image': self.image, 'Config': {
            'Tty': False, 'Entrypoint': ['docker-entrypoint.sh']}, 'State': {'Running': True}}

    def test_fixed_attach_uses_immutable_id_without_signal_proxy(self):
        self.assertEqual(attach_argv(self.info, self.image), [
            '/usr/bin/docker', 'attach', '--sig-proxy=false', '--detach-keys=', 'b' * 64])

    def test_rejects_name_instead_of_container_id(self):
        self.info['Id'] = 'librechat-coding-executor'
        with self.assertRaisesRegex(RuntimeError, 'immutable'):
            attach_argv(self.info, self.image)

    def test_rejects_runtime_image_drift(self):
        self.info['Image'] = 'sha256:' + 'c' * 64
        with self.assertRaisesRegex(RuntimeError, 'image mismatch'):
            attach_argv(self.info, self.image)

    def test_rejects_tty_missing_or_enabled(self):
        for value in (None, True):
            self.info['Config']['Tty'] = value
            with self.assertRaisesRegex(RuntimeError, 'TTY'):
                attach_argv(self.info, self.image)

    def test_rejects_entrypoint_override(self):
        self.info['Config']['Entrypoint'] = ['/bin/sh']
        with self.assertRaisesRegex(RuntimeError, 'entry point'):
            attach_argv(self.info, self.image)

    def test_rejects_stopped_sandbox(self):
        self.info['State']['Running'] = False
        with self.assertRaisesRegex(RuntimeError, 'running'):
            attach_argv(self.info, self.image)


class AcpRelayTests(unittest.TestCase):
    def child(self, code):
        process = subprocess.Popen([sys.executable, '-I', '-B', '-c', code],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, bufsize=0)
        def cleanup():
            if process.poll() is None:
                process.kill()
            process.wait()
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
        self.addCleanup(cleanup)
        return process

    def test_binary_roundtrip_separates_stderr_and_preserves_exit_status(self):
        process = self.child('import sys; data=sys.stdin.buffer.read(); sys.stdout.buffer.write(data); sys.stderr.buffer.write(b"diagnostics"); sys.exit(7)')
        data = bytes(range(256)) * 1024
        with tempfile.TemporaryFile() as source, tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as error:
            source.write(data)
            source.seek(0)
            self.assertEqual(relay(process, source, output, error, timeout=10), 7)
            output.seek(0)
            error.seek(0)
            self.assertEqual(output.read(), data)
            self.assertEqual(error.read(), b'diagnostics')
            self.assertTrue(os.get_blocking(source.fileno()))

    def test_bidirectional_backpressure_with_output_before_input(self):
        process = self.child('import sys; sys.stdout.buffer.write(b"x"*1000000); sys.stdout.buffer.flush(); data=sys.stdin.buffer.read(); sys.stdout.buffer.write(data)')
        with tempfile.TemporaryFile() as source, tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as error:
            source.write(b'y' * 1000000)
            source.seek(0)
            self.assertEqual(relay(process, source, output, error, timeout=10), 0)
            output.seek(0)
            self.assertEqual(output.read(), b'x' * 1000000 + b'y' * 1000000)

    def test_client_eof_has_bounded_drain(self):
        process = self.child('import sys,time; sys.stdin.buffer.read(); time.sleep(30)')
        with tempfile.TemporaryFile() as source, tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as error:
            with self.assertRaisesRegex(RuntimeError, 'disconnect deadline'):
                relay(process, source, output, error, timeout=5, disconnect_timeout=0.2)

    def test_session_deadline_with_client_still_connected(self):
        process = self.child('import time; time.sleep(30)')
        reader, writer = os.pipe()
        with os.fdopen(reader, 'rb', buffering=0) as source, os.fdopen(writer, 'wb', buffering=0), tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as error:
            with self.assertRaisesRegex(RuntimeError, 'session deadline'):
                relay(process, source, output, error, timeout=0.2)

    def test_stderr_flood_is_bounded(self):
        process = self.child('import sys; sys.stderr.buffer.write(b"x"*100000)')
        with tempfile.TemporaryFile() as source, tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as error:
            with patch('host_maintenance.acp_stream.STDERR_BYTES', 1024):
                with self.assertRaisesRegex(RuntimeError, 'byte limit'):
                    relay(process, source, output, error, timeout=5)

    def test_signal_interrupt_is_not_swallowed_by_selector(self):
        process = self.child('import time; time.sleep(30)')
        reader, writer = os.pipe()
        previous = signal.signal(signal.SIGALRM, _interrupted)
        try:
            with os.fdopen(reader, 'rb', buffering=0) as source, os.fdopen(writer, 'wb', buffering=0), tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as error:
                signal.setitimer(signal.ITIMER_REAL, 0.1)
                with self.assertRaisesRegex(RuntimeError, 'stream interrupted'):
                    relay(process, source, output, error, timeout=2)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)

    def test_closed_output_fails_without_hanging(self):
        process = self.child('import sys; sys.stdout.buffer.write(b"reply"); sys.stdout.buffer.flush(); sys.stdin.buffer.read()')
        reader, writer = os.pipe()
        os.close(reader)
        with tempfile.TemporaryFile() as source, os.fdopen(writer, 'wb', buffering=0) as output, tempfile.TemporaryFile() as error:
            with self.assertRaises(BrokenPipeError):
                relay(process, source, output, error, timeout=5)


class AcpSessionLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config = {'container': 'candidate', 'image_id': 'sha256:' + 'a' * 64,
                       'task_root': str(self.root / 'tasks'), 'repository_root': str(self.root / 'repos'),
                       'lock_path': str(self.root / 'maintenance.lock'), 'repositories': {}}
        self.broker = Broker(self.config)

    def test_separate_broker_cannot_operate_on_active_task(self):
        other = Broker(copy.deepcopy(self.config))
        with self.broker._acp_operation('task-one'):
            with self.assertRaisesRegex(RuntimeError, 'active operation'):
                with other._acp_operation('task-one'):
                    self.fail('duplicate session admitted')
        with other._acp_operation('task-one'):
            pass

    def test_different_task_is_not_blocked(self):
        other = Broker(copy.deepcopy(self.config))
        with self.broker._acp_operation('task-one'):
            with other._acp_operation('task-two'):
                pass

    def test_lock_symlink_is_rejected(self):
        target = self.root / 'target'
        target.write_text('preserved')
        (self.root / 'acp-task-one.lock').symlink_to(target)
        with self.assertRaises(OSError):
            with self.broker._acp_operation('task-one'):
                self.fail('symlink lock admitted')
        self.assertEqual(target.read_text(), 'preserved')

    def test_lock_with_unsafe_permissions_is_rejected(self):
        lock = self.root / 'acp-task-one.lock'
        lock.touch(mode=0o600)
        lock.chmod(0o644)
        with self.assertRaisesRegex(RuntimeError, 'invalid ACP session lock'):
            with self.broker._acp_operation('task-one'):
                self.fail('unsafe lock admitted')

    def prepare_stream(self):
        task = self.root / 'tasks' / 'task-one'
        task.mkdir(parents=True)
        (self.root / 'maintenance.lock').touch(mode=0o600)
        manager = Mock()
        manager.task_path.return_value = task
        manager.create.return_value = 'b' * 64
        created = {'Id': 'b' * 64, 'State': {'Status': 'created', 'Running': False}}
        running = {'Id': 'b' * 64, 'State': {'Status': 'running', 'Running': True}}
        manager.inspect.side_effect = [created, running, running]
        self.broker._acp_manager = lambda: manager
        return manager, created, running

    def test_client_sigterm_during_cleanup_cannot_skip_validated_removal(self):
        manager, created, running = self.prepare_stream()
        calls = []
        def inspect(_task):
            calls.append(True)
            if len(calls) == 3:
                signal.raise_signal(signal.SIGTERM)
            return created if len(calls) == 1 else running
        manager.inspect.side_effect = inspect
        previous = signal.signal(signal.SIGTERM, _interrupted)
        try:
            with patch('host_maintenance.acp_stream.attach', return_value=0):
                self.assertEqual(self.broker.acp_sandbox_stream('task-one', None, None, None), 0)
            manager.remove.assert_called_once_with('task-one')
            self.assertIs(signal.getsignal(signal.SIGTERM), _interrupted)
        finally:
            signal.signal(signal.SIGTERM, previous)

    def test_stream_failure_still_validates_and_removes_owned_sandbox(self):
        manager, _, _ = self.prepare_stream()
        with patch('host_maintenance.acp_stream.attach', side_effect=RuntimeError('transport failed')):
            with self.assertRaisesRegex(RuntimeError, 'transport failed'):
                self.broker.acp_sandbox_stream('task-one', None, None, None)
        self.assertEqual(manager.inspect.call_count, 3)
        manager.remove.assert_called_once_with('task-one')

    def test_cleanup_refuses_replacement_container_even_after_stream_success(self):
        manager, created, running = self.prepare_stream()
        manager.inspect.side_effect = [created, running, {'Id': 'c' * 64}]
        with patch('host_maintenance.acp_stream.attach', return_value=0):
            with self.assertRaisesRegex(RuntimeError, 'cleanup refused'):
                self.broker.acp_sandbox_stream('task-one', None, None, None)
        manager.remove.assert_not_called()


if __name__ == '__main__':
    unittest.main()
