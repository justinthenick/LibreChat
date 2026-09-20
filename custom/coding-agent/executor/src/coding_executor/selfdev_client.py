from __future__ import annotations

import json
import re
import socket
from pathlib import Path

SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
MAX_RESPONSE_BYTES = 1_048_576


class SelfDevClient:
    def __init__(self, socket_path: Path, timeout_seconds: int = 900) -> None:
        self.socket_path = Path(socket_path)
        self.timeout_seconds = timeout_seconds

    def build_candidate(self, task_id: str) -> dict[str, object]:
        return self._task_call("build_candidate", task_id)

    def test_candidate(self, task_id: str) -> dict[str, object]:
        return self._task_call("test_candidate", task_id)

    def start_candidate(self, task_id: str) -> dict[str, object]:
        return self._task_call("start_candidate", task_id)

    def candidate_status(self) -> dict[str, object]:
        return self._call("candidate_status", {})

    def destroy_candidate(self) -> dict[str, object]:
        return self._call("destroy_candidate", {})

    def _task_call(self, action: str, task_id: str) -> dict[str, object]:
        if not SAFE_TASK_ID.fullmatch(task_id):
            raise ValueError("invalid task id")
        return self._call(action, {"task_id": task_id})

    def _call(self, action: str, params: dict[str, object]) -> dict[str, object]:
        request = json.dumps(
            {"action": action, "params": params},
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"

        if len(request) > 65_536:
            raise ValueError("self-development request is too large")

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(self.timeout_seconds)
            client.connect(str(self.socket_path))
            client.sendall(request)

            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = client.recv(65_536)
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    raise RuntimeError("self-development worker response exceeded limit")
                if b"\n" in chunk:
                    break

        raw = b"".join(chunks).split(b"\n", 1)[0]
        if not raw:
            raise RuntimeError("self-development worker returned no response")

        response = json.loads(raw.decode("utf-8"))
        if not isinstance(response, dict):
            raise RuntimeError("self-development worker returned an invalid response")
        if response.get("ok") is not True:
            raise RuntimeError(str(response.get("error") or "self-development worker failed"))

        result = response.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("self-development worker returned an invalid result")
        return result
