from __future__ import annotations

import argparse
import json
import os
import re
import selectors
import signal
import subprocess
import sys
import time
import threading
from contextlib import contextmanager
from pathlib import Path

from coding_executor.bounded import _environment


BUFFER_BYTES = 65536
SESSION_SECONDS = 3600
DISCONNECT_SECONDS = 10
STREAM_BYTES = 64 * 1024 * 1024
STDERR_BYTES = 1024 * 1024


class AcpInput:
    """Map only the authorized session root; never enable host-side execution."""

    def __init__(self, workspace: Path):
        self.workspace = str(workspace)
        self.pending = bytearray()

    def feed(self, chunk: bytes) -> bytes:
        self.pending.extend(chunk)
        output = bytearray()
        while b'\n' in self.pending:
            line, _, remaining = self.pending.partition(b'\n')
            self.pending = bytearray(remaining)
            if len(line) >= BUFFER_BYTES:
                raise RuntimeError('ACP request frame limit exceeded')
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except (ValueError, UnicodeError) as exc:
                raise RuntimeError('ACP input must be newline-delimited JSON') from exc
            if not isinstance(message, dict) or message.get('jsonrpc') != '2.0':
                raise RuntimeError('ACP input must be a JSON-RPC 2.0 object')
            method = message.get('method')
            params = message.get('params', {})
            if method == 'initialize':
                if not isinstance(params, dict):
                    raise RuntimeError('invalid ACP initialize parameters')
                capabilities = params.get('clientCapabilities', {})
                if not isinstance(capabilities, dict):
                    raise RuntimeError('invalid ACP client capabilities')
                filesystem = capabilities.get('fs', {})
                if (capabilities.get('terminal') not in (None, False)
                        or not isinstance(filesystem, dict)
                        or any(value is not False for value in filesystem.values())):
                    raise RuntimeError('contained ACP forbids host filesystem and terminal callbacks')
            if isinstance(params, dict) and ('cwd' in params or method in ('session/new', 'session/load', 'session/resume', 'session/fork')):
                if params.get('cwd') not in (self.workspace, '/workspace'):
                    raise RuntimeError('ACP session cwd must match the authorized task')
                if params.get('mcpServers', []) != []:
                    raise RuntimeError('contained ACP forbids client-supplied MCP servers')
                params['cwd'] = '/workspace'
                line = json.dumps(message, ensure_ascii=False, separators=(',', ':')).encode()
            elif method in ('session/new', 'session/load', 'session/resume', 'session/fork'):
                raise RuntimeError('invalid ACP session parameters')
            if len(line) >= BUFFER_BYTES:
                raise RuntimeError('ACP request frame limit exceeded')
            output.extend(line + b'\n')
        if len(self.pending) >= BUFFER_BYTES:
            raise RuntimeError('ACP request frame limit exceeded')
        return bytes(output)

    def finish(self):
        if self.pending.strip():
            raise RuntimeError('ACP input ended inside a JSON frame')


@contextmanager
def cleanup_signals():
    """Finish bounded, validating cleanup after the client begins termination."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = {sig: signal.signal(sig, signal.SIG_IGN) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def attach_argv(info: dict, image: str) -> list[str]:
    container_id = info.get('Id', '')
    config = info.get('Config', {})
    if not isinstance(container_id, str) or not re.fullmatch(r'[0-9a-f]{64}', container_id):
        raise RuntimeError('ACP stream requires an immutable container ID')
    if info.get('Image') != image:
        raise RuntimeError('ACP stream runtime image mismatch')
    if config.get('Tty') is not False:
        raise RuntimeError('ACP stream must not allocate a TTY')
    if config.get('Entrypoint') != ['docker-entrypoint.sh']:
        raise RuntimeError('ACP stream entry point mismatch')
    if info.get('State', {}).get('Running') is not True:
        raise RuntimeError('ACP stream requires a running sandbox')
    return ['/usr/bin/docker', 'attach', '--sig-proxy=false', '--detach-keys=', container_id]


def relay(process, stdin, stdout, stderr, *, timeout=SESSION_SECONDS, disconnect_timeout=DISCONNECT_SECONDS, input_policy=None):
    """Forward separate byte streams with backpressure and bounded EOF draining."""
    lanes = [
        dict(source=stdin, sink=process.stdin, buffer=bytearray(), eof=False, total=0, limit=STREAM_BYTES),
        dict(source=process.stdout, sink=stdout, buffer=bytearray(), eof=False, total=0, limit=STREAM_BYTES),
        dict(source=process.stderr, sink=stderr, buffer=bytearray(), eof=False, total=0, limit=STDERR_BYTES),
    ]
    modes = {}
    deadline = time.monotonic() + timeout
    disconnect_deadline = None
    try:
        for lane in lanes:
            for stream in (lane['source'], lane['sink']):
                fd = stream.fileno()
                if fd not in modes:
                    modes[fd] = os.get_blocking(fd)
                    os.set_blocking(fd, False)
        while True:
            now = time.monotonic()
            if now >= deadline:
                raise RuntimeError('ACP stream session deadline exceeded')
            if disconnect_deadline is not None and now >= disconnect_deadline:
                raise RuntimeError('ACP stream disconnect deadline exceeded')
            if lanes[0]['eof'] and not lanes[0]['buffer'] and not process.stdin.closed:
                process.stdin.close()
            if all(lane['eof'] and not lane['buffer'] for lane in lanes[1:]):
                return process.wait(timeout=max(0.01, min(1, deadline - now)))
            with selectors.SelectSelector() as selector:
                for lane in lanes:
                    pending = len(input_policy.pending) if lane is lanes[0] and input_policy else 0
                    if not lane['eof'] and len(lane['buffer']) + pending < BUFFER_BYTES:
                        selector.register(lane['source'], selectors.EVENT_READ, (lane, 'read'))
                    if lane['buffer']:
                        selector.register(lane['sink'], selectors.EVENT_WRITE, (lane, 'write'))
                for key, _ in selector.select(0.1):
                    lane, action = key.data
                    try:
                        if action == 'write':
                            written = os.write(key.fd, lane['buffer'])
                            del lane['buffer'][:written]
                            continue
                        pending = len(input_policy.pending) if lane is lanes[0] and input_policy else 0
                        chunk = os.read(key.fd, min(8192, BUFFER_BYTES - len(lane['buffer']) - pending))
                    except BlockingIOError:
                        continue
                    if not chunk:
                        lane['eof'] = True
                        if lane is lanes[0]:
                            if input_policy:
                                input_policy.finish()
                            disconnect_deadline = time.monotonic() + disconnect_timeout
                        continue
                    lane['total'] += len(chunk)
                    if lane['total'] > lane['limit']:
                        raise RuntimeError('ACP stream byte limit exceeded')
                    if lane is lanes[0] and input_policy:
                        chunk = input_policy.feed(chunk)
                    lane['buffer'].extend(chunk)
    finally:
        for fd, blocking in modes.items():
            try:
                os.set_blocking(fd, blocking)
            except OSError:
                pass


def attach(info: dict, image: str, stdin, stdout, stderr, *, workspace: Path) -> int:
    argv = attach_argv(info, image)
    process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=_environment(None),
                               start_new_session=True, bufsize=0)
    try:
        return relay(process, stdin, stdout, stderr, input_policy=AcpInput(workspace))
    finally:
        with cleanup_signals():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()


def _interrupted(_signum, _frame):
    raise RuntimeError('ACP stream interrupted')


def main() -> None:
    parser = argparse.ArgumentParser(description='Run a broker-owned, contained ACP stdio session.')
    parser.add_argument('--task', required=True)
    args = parser.parse_args()
    from host_maintenance.broker import Broker

    previous = {sig: signal.signal(sig, _interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        config_path = Path(os.environ['CODING_MAINTENANCE_CONFIG']).resolve(strict=True)
        broker = Broker(json.loads(config_path.read_text()))
        if any(root == config_path or root in config_path.parents for root in (broker.tasks, broker.repositories)):
            raise ValueError('maintenance policy must live outside executor mounts')
        if sys.stdin.isatty() or sys.stdout.isatty():
            raise ValueError('ACP stream requires piped stdio')
        result = broker.acp_sandbox_stream(args.task, sys.stdin.buffer, sys.stdout.buffer, sys.stderr.buffer)
    except (OSError, RuntimeError, ValueError, KeyError):
        print('ACP session failed; inspect operator candidate diagnostics.', file=sys.stderr)
        result = 1
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    raise SystemExit(result)


if __name__ == '__main__':
    main()
