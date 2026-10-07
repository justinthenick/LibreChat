"""Run the complete SDK suite with isolated state and loopback-only networking."""
from __future__ import annotations

import os
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def main() -> int:
    attempted_external_connections: list[str] = []
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex

    def check_address(sock, address) -> None:
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            if address[0] not in {"127.0.0.1", "::1"}:
                attempted_external_connections.append(str(address[0]))
                raise AssertionError("Tests may connect only to the loopback MCP fixture")

    def local_connect(sock, address):
        check_address(sock, address)
        return connect(sock, address)

    def local_connect_ex(sock, address):
        check_address(sock, address)
        return connect_ex(sock, address)

    with tempfile.TemporaryDirectory(prefix="orchestrator-tests-") as root:
        environment = {
            "HOME": root,
            "OH_PERSISTENCE_DIR": str(Path(root) / "openhands"),
            "LITELLM_LOCAL_MODEL_COST_MAP": "True",
            "OTEL_SDK_DISABLED": "true",
        }
        with patch.dict(os.environ, environment, clear=True), \
                patch.object(socket.socket, "connect", local_connect), \
                patch.object(socket.socket, "connect_ex", local_connect_ex):
            # Import before test cases clear their environments: SDK profile
            # defaults and the model cost map are selected at import time.
            import openhands.sdk  # noqa: F401

            suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent))
            result = unittest.TextTestRunner(verbosity=2).run(suite)
        if attempted_external_connections:
            raise AssertionError("External network access attempted during tests")
        return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
