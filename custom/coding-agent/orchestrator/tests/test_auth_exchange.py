"""Real worker accounting and HTTP frames with synthetic auth-only wire I/O."""
import io
import os
import pickle
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs

import httpx

from coding_orchestrator.auth_exchange import (
    AuthReply, BoundedAuthExchange, CLIENT_ID, KEYS_URL, MAX_REPLY, TOKEN_URL,
)
from coding_orchestrator.backend import BackendContractError
from coding_orchestrator.job_worker import WorkerControl, WorkerCancelled, WorkerDeadline, WorkerLimit
from test_bounded_llm import Counter


class AuthExchangeTests(unittest.TestCase):
    def setUp(self):
        self.counter = Counter()
        self.cancelled, self.limited = threading.Event(), threading.Event()
        self.control = WorkerControl(self.counter, self.cancelled, self.limited,
                                     time.monotonic() + 10, 3, io.BytesIO())
        self.requests = []
        from openhands.sdk.llm.auth import CredentialStore, OpenAISubscriptionAuth
        self.forbidden = []
        for owner, name in ((CredentialStore, "get"), (CredentialStore, "save"),
                            (OpenAISubscriptionAuth, "refresh_if_needed_sync")):
            guard = patch.object(owner, name, side_effect=AssertionError("No credential lifecycle allowed"))
            self.forbidden.append(guard.start())
            self.addCleanup(guard.stop)

    def tearDown(self):
        for guard in self.forbidden:
            guard.assert_not_called()

    def bind(self, handler=None):
        def send(request):
            self.requests.append(request)
            self.assertEqual(self.counter.value, len(self.requests))
            return handler(request) if handler else httpx.Response(200,
                headers={"content-type": "application/json"}, content=b'{"synthetic":"secret"}')
        exchange = BoundedAuthExchange(self.control, transport=httpx.MockTransport(send), enabled=True)
        self.addCleanup(exchange.close)
        return exchange

    def test_default_and_missing_transport_are_unavailable(self):
        for exchange in (BoundedAuthExchange(self.control),
                         BoundedAuthExchange(self.control, enabled=True),
                         BoundedAuthExchange(self.control, transport=httpx.MockTransport(lambda _: self.fail()))):
            with self.assertRaises(BackendContractError):
                exchange.refresh("synthetic-secret")
        self.assertEqual(self.counter.value, 0)

    def test_exact_pinned_sdk_routes_shared_budget_and_no_ambient_credentials(self):
        from openhands.sdk.llm.auth.openai import CLIENT_ID as SDK_CLIENT_ID, JWKS_URL, ISSUER
        self.assertEqual((CLIENT_ID, KEYS_URL, TOKEN_URL), (SDK_CLIENT_ID, JWKS_URL, ISSUER + "/oauth/token"))
        exchange = self.bind()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "ambient-secret", "HTTP_PROXY": "http://invalid.test"}):
            reply = exchange.refresh("synthetic-refresh")
            exchange.signing_keys()
        self.assertEqual(reply.body, b'{"synthetic":"secret"}')
        self.assertNotIn("secret", repr(reply))
        request, keys = self.requests
        self.assertEqual((request.method, str(request.url)), ("POST", TOKEN_URL))
        self.assertEqual(parse_qs(request.content.decode()), {
            "grant_type": ["refresh_token"], "refresh_token": ["synthetic-refresh"], "client_id": [CLIENT_ID]})
        self.assertEqual((keys.method, str(keys.url), keys.content), ("GET", KEYS_URL, b""))
        for request in self.requests:
            self.assertNotIn("authorization", request.headers)
            self.assertNotIn("cookie", request.headers)
            self.assertTrue(all(0 < value <= 10 for value in request.extensions["timeout"].values()))
        self.control.before_provider_request()  # Inference consumes the same counter.
        with self.assertRaises(WorkerLimit):
            self.control.before_provider_request()

    def test_neither_exchange_nor_sensitive_reply_can_be_pickled(self):
        for value in (self.bind(), AuthReply(b"synthetic-secret")):
            with self.assertRaises(TypeError) as caught:
                pickle.dumps(value)
            self.assertNotIn("synthetic-secret", str(caught.exception))

    def test_invalid_secret_is_terminal_without_dispatch(self):
        for secret in (None, "", "has space", "line\nsecret", "x" * 8193):
            exchange = self.bind()
            with self.assertRaises(BackendContractError):
                exchange.refresh(secret)
            with self.assertRaises(BackendContractError):
                exchange.signing_keys()
        self.assertEqual(self.requests, [])

    def test_repeat_refresh_is_blocked_even_after_success(self):
        exchange = self.bind()
        exchange.refresh("synthetic-refresh")
        for operation in (lambda: exchange.refresh("synthetic-refresh"), exchange.signing_keys):
            with self.assertRaises(BackendContractError):
                operation()
        self.assertEqual(len(self.requests), 1)

    def test_uncertain_rotation_is_sanitized_and_never_retried(self):
        def lost(request):
            raise RuntimeError("synthetic-rotated-secret " + request.content.decode())
        exchange = self.bind(lost)
        for _ in range(2):
            with self.assertRaises(BackendContractError) as caught:
                exchange.refresh("synthetic-refresh")
            self.assertNotIn("synthetic", str(caught.exception))
            self.assertTrue(caught.exception.__suppress_context__)
        self.assertEqual(len(self.requests), 1)

    def test_cancellation_deadline_and_budget_before_dispatch_remain_typed(self):
        for error in (WorkerCancelled, WorkerDeadline, WorkerLimit):
            with self.subTest(error=error):
                exchange = self.bind()
                if error is WorkerCancelled:
                    self.cancelled.set()
                elif error is WorkerDeadline:
                    self.control._deadline = time.monotonic() - 1
                else:
                    self.control._maximum = 0
                with self.assertRaises(error):
                    exchange.refresh("synthetic-refresh")
                self.cancelled.clear()
                self.control._deadline = time.monotonic() + 10
                self.control._maximum = 3
                with self.assertRaises(error):
                    exchange.signing_keys()
        self.assertEqual(self.requests, [])

    def test_late_response_after_cancel_or_deadline_is_discarded(self):
        for error in (WorkerCancelled, WorkerDeadline):
            with self.subTest(error=error):
                def late(_):
                    if error is WorkerCancelled:
                        self.cancelled.set()
                    else:
                        self.control._deadline = time.monotonic() - 1
                    return httpx.Response(200, headers={"content-type": "application/json"}, content=b"{}")
                exchange = self.bind(late)
                with self.assertRaises(error):
                    exchange.refresh("synthetic-refresh")
                self.cancelled.clear()
                self.control._deadline = time.monotonic() + 10
                with self.assertRaises(error):
                    exchange.signing_keys()
        self.assertEqual(len(self.requests), 2)

    def test_redirect_error_or_compression_is_never_followed(self):
        for status, headers in ((302, {"location": "https://invalid.test/secret"}),
                                (401, {}), (200, {"content-encoding": "gzip"}),
                                (200, {"content-type": "text/html"})):
            self.counter.value = 0
            self.requests.clear()
            exchange = self.bind(lambda _: httpx.Response(status, headers=headers, content=b"secret"))
            with self.assertRaises(BackendContractError):
                exchange.signing_keys()
            with self.assertRaises(BackendContractError):
                exchange.signing_keys()
            self.assertEqual(len(self.requests), 1)

    def test_stream_size_deadline_and_close_are_checked(self):
        for mode in ("size", "deadline", "close"):
            self.counter.value = 0
            self.requests.clear()
            self.control._deadline = time.monotonic() + 10
            closed = []
            control = self.control
            class Stream(httpx.SyncByteStream):
                def __iter__(self):
                    yield b"{" * (MAX_REPLY + 1 if mode == "size" else 1)
                    if mode == "deadline":
                        control._deadline = time.monotonic() - 1
                    yield b"}"
                def close(self):
                    closed.append(True)
                    if mode == "close":
                        raise RuntimeError("synthetic-secret")
            exchange = self.bind(lambda _: httpx.Response(200,
                headers={"content-type": "application/json"}, stream=Stream()))
            expected = {"size": WorkerLimit, "deadline": WorkerDeadline, "close": BackendContractError}[mode]
            with self.assertRaises(expected):
                exchange.signing_keys()
            self.assertTrue(closed)
            with self.assertRaises(expected):
                exchange.refresh("synthetic-refresh")
            self.assertEqual(len(self.requests), 1)

    def test_concurrent_call_poison_discards_inflight_reply(self):
        entered, release = threading.Event(), threading.Event()
        errors = []
        def delayed(_):
            entered.set()
            self.assertTrue(release.wait(3))
            return httpx.Response(200, headers={"content-type": "application/json"}, content=b"{}")
        exchange = self.bind(delayed)
        def run():
            try:
                exchange.refresh("synthetic-refresh")
            except BackendContractError:
                errors.append(True)
        thread = threading.Thread(target=run)
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            with self.assertRaises(BackendContractError):
                exchange.signing_keys()
        finally:
            release.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [True])
        self.assertEqual(len(self.requests), 1)

    def test_closed_or_wrong_process_never_dispatches(self):
        exchange = self.bind()
        with patch("coding_orchestrator.auth_exchange.os.getpid", return_value=-1):
            with self.assertRaises(BackendContractError):
                exchange.signing_keys()
        exchange.close()
        with self.assertRaises(BackendContractError):
            exchange.refresh("synthetic-refresh")
        self.assertEqual(self.requests, [])

    def test_close_during_dispatch_discards_reply_without_retry(self):
        entered, release = threading.Event(), threading.Event()
        outcomes = []
        def delayed(_):
            entered.set()
            release.wait(3)
            return httpx.Response(200, headers={"content-type": "application/json"}, content=b"{}")
        exchange = self.bind(delayed)
        def run():
            try:
                outcomes.append(exchange.refresh("synthetic-refresh"))
            except BackendContractError:
                outcomes.append("unknown")
        thread = threading.Thread(target=run)
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            exchange.close()
        finally:
            release.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcomes, ["unknown"])
        with self.assertRaises(BackendContractError):
            exchange.signing_keys()
        self.assertEqual(len(self.requests), 1)


if __name__ == "__main__":
    unittest.main()
