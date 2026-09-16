import importlib.util
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("DEPLOYMENT_GATEWAY_FRAME_ANCESTOR", "http://admin.example.test:3220")
SPEC = importlib.util.spec_from_file_location("deployment_frame_proxy", ROOT / "deployment-frame-proxy.py")
proxy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proxy)


class UpstreamHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        payload = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Set-Cookie", "librechat_admin_settings=test; Path=/; HttpOnly; SameSite=Strict")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class FrameAncestorTests(unittest.TestCase):
    def test_normalizes_configured_url_to_origin(self):
        self.assertEqual(
            proxy.normalize_frame_ancestor("https://admin.example.test:8443/some/path?x=1#fragment"),
            "https://admin.example.test:8443",
        )

    def test_rejects_credentials_and_non_http_schemes(self):
        for value in ("https://user:secret@admin.example.test", "file:///tmp/admin"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    proxy.normalize_frame_ancestor(value)


class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
        upstream_port = cls.upstream.server_address[1]
        proxy.upstream = urlsplit(f"http://127.0.0.1:{upstream_port}")
        proxy.FRAME_ANCESTOR = "http://admin.example.test:3220"
        cls.gateway = ThreadingHTTPServer(("127.0.0.1", 0), proxy.Handler)
        cls.threads = [
            threading.Thread(target=cls.upstream.serve_forever, daemon=True),
            threading.Thread(target=cls.gateway.serve_forever, daemon=True),
        ]
        for thread in cls.threads:
            thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.gateway.shutdown()
        cls.upstream.shutdown()
        cls.gateway.server_close()
        cls.upstream.server_close()

    def test_gateway_replaces_upstream_frame_policy_and_preserves_response(self):
        port = self.gateway.server_address[1]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"http://127.0.0.1:{port}/health", timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b'{"ok":true}')
            self.assertIsNone(response.headers.get("X-Frame-Options"))
            csp = response.headers.get("Content-Security-Policy") or ""
            self.assertIn("frame-ancestors http://admin.example.test:3220", csp)
            self.assertNotIn("frame-ancestors 'none'", csp)
            self.assertIn("librechat_admin_settings=test", response.headers.get("Set-Cookie") or "")
            self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(response.headers.get("Referrer-Policy"), "no-referrer")


if __name__ == "__main__":
    unittest.main()
