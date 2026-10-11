"""Real httpcore HTTP/1 parsing; only DNS, sockets and TLS wire I/O are synthetic."""
import io
import socket
import ssl
import threading
import time
import unittest
from unittest.mock import patch

import httpx

from coding_orchestrator.auth_exchange import KEYS_URL, MAX_REPLY
from coding_orchestrator.auth_transport import MAX_WIRE, create_auth_exchange
from coding_orchestrator.backend import BackendContractError
from coding_orchestrator.job_worker import WorkerControl, WorkerCancelled, WorkerDeadline, WorkerLimit
from test_bounded_llm import Counter


def response(body=b'{}', headers=b'', status=b'200 OK'):
    return (b'HTTP/1.1 ' + status + b'\r\nContent-Type: application/json\r\n'
            + b'Content-Length: ' + str(len(body)).encode() + b'\r\n' + headers + b'\r\n' + body)


class Wire:
    def __init__(self, payload, hook):
        self.payload, self.hook = payload, hook
        self.sent = bytearray()
        self.timeouts = []
        self.events = []
        self.close_error = False

    def event(self, name):
        self.events.append(name)
        self.hook(name)

    def settimeout(self, value):
        self.timeouts.append(value)

    def connect(self, address):
        self.event('connect')

    def do_handshake(self):
        self.event('tls')

    def send(self, data):
        self.event('send')
        count = min(17, len(data))
        self.sent.extend(data[:count])
        return count

    def recv(self, count):
        self.event('recv')
        count = min(count, 257)
        result, self.payload = self.payload[:count], self.payload[count:]
        return result

    def shutdown(self, how):
        self.event('shutdown')

    def close(self):
        self.events.append('close')
        if self.close_error:
            raise OSError('synthetic-close-secret')


class AuthTransportTests(unittest.TestCase):
    def setUp(self):
        self.counter = Counter()
        self.cancelled = threading.Event()
        self.control = WorkerControl(self.counter, self.cancelled, threading.Event(),
                                     time.monotonic() + 60, 3, io.BytesIO())
        self.hook = lambda name: None
        self.wires = []
        self.payload = response()
        def resolve(*args, **kwargs):
            self.hook('dns')
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.0.2.1', 443)),
                    (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.0.2.2', 443))]
        def connect(*args, **kwargs):
            wire = Wire(self.payload, lambda name: self.hook(name))
            self.wires.append(wire)
            return wire
        def wrap(context, wire, *, server_hostname, do_handshake_on_connect):
            self.assertEqual(server_hostname, 'auth.openai.com')
            self.assertFalse(do_handshake_on_connect)
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertGreaterEqual(context.minimum_version, ssl.TLSVersion.TLSv1_2)
            return wire
        for target, replacement in (('socket.getaddrinfo', resolve), ('socket.socket', connect),
                                     ('ssl.SSLContext.wrap_socket', wrap)):
            guard = patch(target, replacement)
            guard.start()
            self.addCleanup(guard.stop)

    def bind(self):
        return create_auth_exchange(self.control, enabled=True)

    def test_default_off_has_no_socket_or_tls_setup(self):
        with patch('ssl.SSLContext', side_effect=AssertionError('Unexpected TLS setup')):
            with self.assertRaises(BackendContractError):
                create_auth_exchange(self.control).signing_keys()
        self.assertEqual(self.wires, [])
        self.assertEqual(self.counter.value, 0)

    def test_enabled_factory_loads_only_explicit_certifi_trust(self):
        import certifi
        original = ssl.SSLContext.load_verify_locations
        loaded = []
        def load(context, cafile=None, capath=None, cadata=None):
            loaded.append((cafile, capath, cadata))
            return original(context, cafile=cafile, capath=capath, cadata=cadata)
        with patch('ssl.create_default_context', side_effect=AssertionError('Ambient trust forbidden')), \
                patch.object(ssl.SSLContext, 'load_default_certs', side_effect=AssertionError('Ambient trust forbidden')), \
                patch.object(ssl.SSLContext, 'load_verify_locations', load):
            self.bind().signing_keys()
        self.assertEqual(loaded, [(certifi.where(), None, None)])

    def test_fixed_wire_framing_shared_accounting_and_no_environment_proxy(self):
        with patch.dict('os.environ', {'HTTPS_PROXY': 'http://invalid.test',
                                      'SSL_CERT_FILE': '/missing', 'OPENAI_API_KEY': 'ambient-secret'}):
            exchange = self.bind()
            self.assertEqual(exchange.refresh('synthetic-token').body, b'{}')
            self.assertEqual(exchange.signing_keys().body, b'{}')
        self.assertEqual(self.counter.value, 2)
        self.assertEqual(len(self.wires), 2)
        for wire, route in zip(self.wires, (b'POST /oauth/token HTTP/1.1', b'GET /.well-known/jwks.json HTTP/1.1')):
            self.assertTrue(wire.sent.startswith(route))
            self.assertIn(b'Host: auth.openai.com\r\n', wire.sent)
            self.assertIn(b'Accept-Encoding: identity\r\n', wire.sent)
            self.assertNotIn(b'ambient-secret', wire.sent)
            self.assertNotIn(b'Authorization:', wire.sent)
            self.assertIn('close', wire.events)
        self.assertIn(b'refresh_token=synthetic-token', self.wires[0].sent)

    def test_each_io_receives_shrinking_deadline(self):
        self.payload = response(b'x' * 1500)
        self.hook = lambda name: setattr(self.control, '_deadline', self.control._deadline - 0.01)
        self.bind().signing_keys()
        values = self.wires[0].timeouts
        self.assertGreater(len(values), 10)
        self.assertTrue(all(0 < later <= earlier for earlier, later in zip(values, values[1:])))
        self.assertLess(values[-1], values[0] - 0.1)

    def test_wire_failures_never_retry_or_fall_back_to_second_address(self):
        for stage in ('dns', 'connect', 'tls', 'send', 'recv'):
            with self.subTest(stage=stage):
                self.wires.clear()
                self.counter.value = 0
                def fail(name):
                    if name == stage:
                        raise OSError('synthetic-secret')
                self.hook = fail
                exchange = self.bind()
                for operation in (lambda: exchange.refresh('synthetic-token'), exchange.signing_keys):
                    with self.assertRaises(BackendContractError):
                        operation()
                self.assertEqual(self.counter.value, 1)
                self.assertEqual(len(self.wires), 0 if stage == 'dns' else 1)

    def test_cancel_deadline_or_close_during_connection_prevents_http_write(self):
        for stage in ('dns', 'connect', 'tls'):
            for mode in ('cancel', 'deadline', 'close'):
                with self.subTest(stage=stage, mode=mode):
                    self.wires.clear()
                    self.cancelled.clear()
                    self.counter.value = 0
                    self.control._deadline = time.monotonic() + 60
                    exchange = self.bind()
                    def interrupt(name):
                        if name == stage:
                            if mode == 'cancel':
                                self.cancelled.set()
                            elif mode == 'deadline':
                                self.control._deadline = time.monotonic() - 1
                            else:
                                exchange.close()
                    self.hook = interrupt
                    expected = {'cancel': WorkerCancelled, 'deadline': WorkerDeadline,
                                'close': BackendContractError}[mode]
                    with self.assertRaises(expected):
                        exchange.signing_keys()
                    self.assertTrue(all(not wire.sent for wire in self.wires))

    def test_compressed_or_duplicate_headers_rejected_before_httpx_construction(self):
        for headers in (b'Content-Encoding: gzip\r\n',
                        b'Content-Encoding: identity\r\nContent-Encoding: gzip\r\n',
                        b'Content-Encoding: identity\r\nContent-Encoding: identity\r\n',
                        b'Content-Type: text/html\r\n'):
            self.counter.value = 0
            self.payload = response(b'compressed-bomb-placeholder', headers)
            with patch('httpx.Response', side_effect=AssertionError('Must reject raw headers first')) as construct:
                with self.assertRaises(BackendContractError):
                    self.bind().signing_keys()
            construct.assert_not_called()

    def test_redirect_is_not_followed_and_body_limit_is_enforced(self):
        for payload, expected in ((response(status=b'302 Found', headers=b'Location: https://invalid.test\r\n'), BackendContractError),
                                  (response(b'x' * (MAX_REPLY + 1)), WorkerLimit),
                                  (b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 10\r\n\r\n{}', BackendContractError)):
            self.payload = payload
            self.wires.clear()
            self.counter.value = 0
            with self.assertRaises(expected):
                self.bind().signing_keys()
            self.assertEqual(len(self.wires), 1)

    def test_socket_cleanup_failure_releases_transport_lock(self):
        exchange = self.bind()
        self.hook = lambda name: setattr(self.wires[0], 'close_error', True) if name == 'recv' else None
        with self.assertRaises(BackendContractError):
            exchange.signing_keys()
        self.assertFalse(exchange._transport.lock.locked())
        self.assertIsNone(exchange._transport.stream)

    def test_chunked_body_is_parsed_and_framing_overhead_is_bounded(self):
        head = b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nTransfer-Encoding: chunked\r\n\r\n'
        self.payload = head + b'1\r\n{\r\n1\r\n}\r\n0\r\n\r\n'
        self.assertEqual(self.bind().signing_keys().body, b'{}')
        # Large valid chunk extensions consume wire budget, not payload budget.
        self.payload = head + (b'1;' + b'x' * 1000 + b'\r\na\r\n') * (MAX_WIRE // 1000 + 1) + b'0\r\n\r\n'
        with self.assertRaises(WorkerLimit):
            self.bind().signing_keys()

    def test_malformed_chunk_is_terminal_without_retaining_parser_error_frames(self):
        self.payload = (b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n'
                        b'Transfer-Encoding: chunked\r\n\r\nsynthetic-invalid-chunk\r\n')
        exchange = self.bind()
        # Keep the live traceback; unittest.assertRaises clears its frames.
        try:
            exchange.refresh('synthetic-retention-token')
        except BackendContractError as error:
            self.assertIsNone(error.__context__)
            self.assertIsNone(error.__cause__)
            self.assertNotIn('synthetic', str(error))
            trace = error.__traceback__
            while trace is not None:
                frame = trace.tb_frame
                module = frame.f_globals.get('__name__', '')
                self.assertNotEqual(module, 'coding_orchestrator.auth_transport')
                self.assertFalse(module.startswith('httpcore'))
                if module == 'coding_orchestrator.auth_exchange':
                    self.assertIn(frame.f_code.co_name, ('refresh', '_raise_failure'))
                    for name, value in frame.f_locals.items():
                        if name in ('category', 'failure'):
                            self.assertIs(value, BackendContractError)
                        else:
                            self.assertIsNone(value)
                trace = trace.tb_next
        else:
            self.fail('Malformed chunk must fail')
        with self.assertRaises(BackendContractError):
            exchange.signing_keys()
        self.assertEqual(len(self.wires), 1)

    def test_late_read_is_discarded_and_never_retried(self):
        exchange = self.bind()
        self.hook = lambda name: self.cancelled.set() if name == 'recv' else None
        for operation in (exchange.signing_keys, lambda: exchange.refresh('synthetic-token')):
            with self.assertRaises(WorkerCancelled):
                operation()
        self.assertEqual(len(self.wires), 1)
        self.assertEqual(self.counter.value, 1)

    def test_certificate_failure_cannot_send_request_or_retry(self):
        def fail(name):
            if name == 'tls':
                raise ssl.SSLCertVerificationError('synthetic certificate failure')
        self.hook = fail
        exchange = self.bind()
        for _ in range(2):
            with self.assertRaises(BackendContractError):
                exchange.signing_keys()
        self.assertEqual(len(self.wires), 1)
        self.assertEqual(self.wires[0].sent, b'')

    def test_caller_headers_and_extensions_cannot_change_wire_policy(self):
        transport = self.bind()._transport
        reply = transport.handle_request(httpx.Request('GET', KEYS_URL,
            headers={'Host': 'invalid.test', 'Authorization': 'synthetic-secret',
                     'Cookie': 'synthetic-cookie'},
            extensions={'timeout': {'read': None}, 'sni_hostname': 'invalid.test'}))
        reply.close()
        wire = self.wires[0]
        for forbidden in (b'invalid.test', b'synthetic-secret', b'synthetic-cookie'):
            self.assertNotIn(forbidden, wire.sent)
        self.assertTrue(all(0 < value <= 60 for value in wire.timeouts))

    def test_private_transport_rejects_origin_and_tls_downgrade_before_dns(self):
        transport = self.bind()._transport
        for url in ('https://invalid.test/', KEYS_URL + '?redirect=1'):
            with self.assertRaises(BackendContractError):
                transport.handle_request(httpx.Request('GET', url))
        transport.context.check_hostname = False
        with self.assertRaises(BackendContractError):
            transport.handle_request(httpx.Request('GET', KEYS_URL))
        self.assertEqual(self.wires, [])


if __name__ == '__main__':
    unittest.main()
