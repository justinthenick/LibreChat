from __future__ import annotations

import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from coding_orchestrator import BackendRunRequest, OpenHandsBackend
from coding_orchestrator.openhands_backend import _build_mcp_server


class ProxySafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_proxy_variants_reject_loopback_even_with_no_proxy(self) -> None:
        for name in ("HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy",
                     "HTTPS_PROXY", "https_proxy"):
            for bypass in ("", "*", "127.0.0.1,::1"):
                with self.subTest(name=name, bypass=bypass), patch.dict(os.environ, {
                    name: "http://user:proxy-secret@192.0.2.1:8080",
                    "NO_PROXY": bypass,
                }):
                    for endpoint in ("http://127.0.0.1:8765/mcp", "http://[::1]:8765/mcp"):
                        with self.assertRaisesRegex(ValueError, "no configured proxies") as error:
                            OpenHandsBackend(endpoint, "executor-secret")
                        self.assertNotIn("proxy-secret", str(error.exception))
                        self.assertNotIn("executor-secret", str(error.exception))

    def test_https_remains_available_with_proxy(self) -> None:
        with patch.dict(os.environ, {"HTTP_PROXY": "http://192.0.2.1:8080"}):
            backend = OpenHandsBackend("https://executor.example.test/mcp", "secret")
            self.assertEqual(backend.name, "openhands")

    def test_no_proxy_alone_does_not_reject_direct_loopback(self) -> None:
        with patch.dict(os.environ, {"NO_PROXY": "*"}):
            server = _build_mcp_server("http://127.0.0.1:8765/mcp", "secret")
        self.assertEqual(str(server.url), "http://127.0.0.1:8765/mcp")

    def test_system_proxy_discovery_is_also_rejected(self) -> None:
        with patch(
            "coding_orchestrator.openhands_backend.getproxies",
            return_value={"http": "http://system-proxy.test:8080"},
        ), self.assertRaisesRegex(ValueError, "no configured proxies"):
            OpenHandsBackend("http://127.0.0.1:8765/mcp", "secret")

    def test_probe_rechecks_proxy_before_discovery(self) -> None:
        calls = []
        backend = OpenHandsBackend(
            "http://127.0.0.1:8765/mcp", "secret",
            discover_tools=lambda *_: calls.append("discovered"),
        )
        with patch.dict(os.environ, {"ALL_PROXY": "http://192.0.2.1:8080"}):
            with self.assertRaisesRegex(ValueError, "no configured proxies"):
                backend.probe()
        self.assertEqual(calls, [])

    def test_mcp_construction_rechecks_proxy_after_probe(self) -> None:
        with patch.dict(os.environ, {"http_proxy": "http://192.0.2.1:8080"}):
            with self.assertRaisesRegex(ValueError, "no configured proxies"):
                _build_mcp_server("http://127.0.0.1:8765/mcp", "secret")

    def test_late_proxy_never_receives_bearer_during_run(self) -> None:
        requests = []

        class ProxyHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append(self.headers.get("Authorization"))
                self.send_error(502)

            do_GET = do_POST

            def log_message(self, *args):
                pass

        with ThreadingHTTPServer(("127.0.0.1", 0), ProxyHandler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with tempfile.TemporaryDirectory() as scratch:
                    backend = OpenHandsBackend(
                        "http://127.0.0.1:8765/mcp", "executor-secret",
                        scratch_root=scratch,
                    )
                    with patch.dict(os.environ, {
                        "HTTP_PROXY": f"http://127.0.0.1:{server.server_port}",
                    }), self.assertRaisesRegex(ValueError, "no configured proxies"):
                        backend.run(BackendRunRequest(prompt="List repositories."))
                self.assertEqual(requests, [])
            finally:
                server.shutdown()
                thread.join()


if __name__ == "__main__":
    unittest.main()
