import importlib.util
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



if __name__ == "__main__":
    unittest.main()
