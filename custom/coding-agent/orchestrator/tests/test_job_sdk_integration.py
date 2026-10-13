"""Real job process, SDK and loopback MCP; deterministic TestLLM only."""
from __future__ import annotations

from functools import partial
import json
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from urllib.parse import urlsplit
from unittest.mock import patch

from coding_orchestrator.job_store import JobStore, StopEvidence
from coding_orchestrator.jobs import ExecutionProfile, JobRequest, JobService, Principal, RunScope


def scripted_sdk_run(context, control, *, endpoint):
    """Trusted test profile, with a socket guard installed before SDK import."""
    allowed = ("127.0.0.1", urlsplit(endpoint).port)
    original_connect = socket.socket.connect
    def connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6) and tuple(address[:2]) != allowed:
            raise RuntimeError("unexpected_test_network")
        return original_connect(sock, address)
    with patch.object(socket.socket, "connect", connect):
        from openhands.sdk.llm import Message, MessageToolCall, TextContent
        from openhands.sdk.testing import TestLLM
        from coding_orchestrator import OpenHandsBackend, BackendRunRequest
        from coding_orchestrator.evidence import EvidenceCollector
        messages = [Message(role="assistant", content=[TextContent(text="")], tool_calls=[
            MessageToolCall(id="call-" + tool, name=tool, arguments=json.dumps(args), origin="completion")])
            for tool, args in (("list_repositories", {}), ("finish", {"message": "Fixture listed."}))]
        collector = EvidenceCollector(context.repository_alias)
        def event(value):
            collector.on_event(value)
            control.emit_progress({"evidence": collector.snapshot()})
        with tempfile.TemporaryDirectory() as scratch:
            backend = OpenHandsBackend(endpoint, "synthetic-token", scratch_root=scratch,
                llm=TestLLM.from_messages(messages, model="test-model"))
            completed = backend.run(BackendRunRequest(context.prompt, max_iterations=2), on_event=event)
        return {"execution_status": completed.execution_status, "final_response": completed.final_response,
                "evidence": collector.snapshot()}


class JobSDKIntegrationTests(unittest.TestCase):
    def test_job_uses_actual_sdk_observations_without_provider_requests(self):
        import uvicorn
        from fastmcp import FastMCP
        from coding_orchestrator import EXPECTED_CODING_EXECUTOR_TOOLS
        calls = []
        mcp = FastMCP("offline-job-fixture")
        def register(name):
            def tool() -> list[str]:
                calls.append(name)
                return ["fixture"]
            mcp.tool(name=name)(tool)
        for name in EXPECTED_CODING_EXECUTOR_TOOLS:
            register(name)
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0)); listener.listen(128)
        endpoint = "http://127.0.0.1:%d/mcp" % listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(mcp.http_app(path="/mcp", stateless_http=True),
                                              log_level="critical", lifespan="on"))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(server.started)
            profile = ExecutionProfile("offline-sdk", frozenset({"fixture"}),
                partial(scripted_sdk_run, endpoint=endpoint), lambda *_: True,
                lambda identity: StopEvidence(identity, True))
            with tempfile.TemporaryDirectory() as directory, JobStore(Path(directory) / "jobs.sqlite") as store:
                with JobService(store, profile=profile, enabled=True) as service:
                    owner = Principal("owner", "tenant")
                    run = service.start_run(owner, JobRequest("List the fixture and finish.", "sdk-test", "generation", 1,
                        RunScope("fixture"), timeout_seconds=30))
                    deadline = time.monotonic() + 35
                    while run["state"] in {"queued", "running", "cancelling"} and time.monotonic() < deadline:
                        time.sleep(.05)
                        run = service.get_run(owner, run["job_id"])
                    self.assertEqual(run["state"], "completed", run)
                    self.assertEqual(run["request_count"], 0)
                    self.assertEqual(calls, ["list_repositories"])
                    self.assertEqual(run["result"]["evidence"]["action_count"], 2)
                    self.assertEqual(run["result"]["evidence"]["pending_count"], 0)
                    self.assertEqual(run["result"]["evidence"]["observed_checks_status"], "not_run")
                    self.assertFalse(run["result"]["evidence"]["evidence_complete"])
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()
            self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
