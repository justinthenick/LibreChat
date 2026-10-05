import importlib.util
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


panel = load("timeout_panel", "admin-settings-panel.py")


class TransportTests(unittest.TestCase):
    def test_panel_waits_for_full_transaction_only_for_apply(self):
        real_socket = socket.socket
        for action, minimum in (("apply", 1800), ("state", 180)):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as tmp:
                path = str(Path(tmp) / "worker.sock")
                listener = real_socket(socket.AF_UNIX, socket.SOCK_STREAM)
                listener.bind(path)
                listener.listen(1)
                observed = []

                def serve():
                    conn, _ = listener.accept()
                    with conn:
                        conn.recv(4096)
                        conn.sendall(b'{"ok":true}\n')

                class ObservedSocket(real_socket):
                    def settimeout(self, value):
                        observed.append(value)
                        return super().settimeout(value)

                thread = threading.Thread(target=serve)
                thread.start()
                try:
                    with patch.object(panel, "SOCKET_PATH", path), patch.object(panel.socket, "socket", ObservedSocket):
                        result = panel.worker_call({"action": action})
                    self.assertTrue(result["ok"])
                    self.assertGreaterEqual(observed[0], minimum)
                    if action == "state":
                        self.assertEqual(observed[0], 180)
                finally:
                    listener.close()
                    thread.join(2)

    def test_gateway_allows_apply_budget_without_expanding_other_routes(self):
        os.environ.setdefault("DEPLOYMENT_GATEWAY_FRAME_ANCESTOR", "http://admin.example.test:3220")
        import io
        gateway = load("timeout_gateway", "deployment-frame-proxy.py")
        # Exercise the handler's upstream request seam. No external HTTP request.
        class Connection:
            def __init__(self, host, port, timeout):
                self.timeout = timeout
                observed.append(timeout)
            def request(self, *args, **kwargs):
                pass
            def getresponse(self):
                class Response:
                    status = 200
                    def read(self): return b'{"ok":true}'
                    def getheaders(self): return []
                return Response()
            def close(self):
                pass
        for method, route, minimum in (("POST", "/api/apply", 1860), ("GET", "/health", 30), ("POST", "/api/preview", 30)):
            observed = []
            handler = object.__new__(gateway.Handler)
            handler.command, handler.path = method, route
            handler.headers = {}
            handler.rfile, handler.wfile = io.BytesIO(), io.BytesIO()
            handler.send_response = lambda *args: None
            handler.send_header = lambda *args: None
            handler.end_headers = lambda: None
            with patch.object(gateway, "HTTPConnection", Connection):
                handler._proxy()
            self.assertEqual(json.loads(handler.wfile.getvalue()), {"ok": True})
            self.assertGreaterEqual(observed[0], minimum)
            if route != "/api/apply":
                self.assertEqual(observed[0], 30)


if __name__ == "__main__":
    unittest.main()
