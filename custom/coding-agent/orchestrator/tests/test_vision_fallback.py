from __future__ import annotations

import json
import os
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import uvicorn
from fastmcp import FastMCP
from openhands.sdk import Agent, LLM
from openhands.sdk.context import AgentContext
from openhands.sdk.tool import Tool
from openhands.sdk.llm import Message, MessageToolCall, TextContent
from openhands.sdk.llm.llm_profile_store import LLMProfileStore
from openhands.sdk.testing import TestLLM
from openhands.sdk.tool.builtins import FinishTool, ThinkTool
from openhands.sdk.tool.builtins.vision_inspect import (
    VisionInspectTool,
    has_vision_profile_available,
)

from coding_orchestrator import (
    BackendContractError,
    BackendRunRequest,
    EXPECTED_CODING_EXECUTOR_TOOLS,
    EXPECTED_OPENHANDS_RUNTIME_TOOLS,
    OPENHANDS_RUNTIME_TOOL_REGEX,
    OpenHandsBackend,
)
from coding_orchestrator.restricted_agent import RestrictedOpenHandsAgent


def response(tool: str, arguments: dict[str, str]) -> Message:
    return Message(
        role="assistant",
        content=[TextContent(text="")],
        tool_calls=[MessageToolCall(
            id=f"call-{tool}", name=tool,
            arguments=json.dumps(arguments), origin="completion",
        )],
    )


class VisionFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        # Isolate the real profile store even under plain unittest discovery.
        profiles = tempfile.TemporaryDirectory()
        self.addCleanup(profiles.cleanup)
        profile_root = patch(
            "openhands.sdk.llm.llm_profile_store._DEFAULT_PROFILE_DIR",
            Path(profiles.name) / "profiles",
        )
        profile_root.start()
        self.addCleanup(profile_root.stop)
        store = LLMProfileStore()
        profile = "orchestrator-test-vision"
        self.assertNotIn(f"{profile}.json", store.list())
        store.save(profile, LLM(model="openai/gpt-4o", usage_id="vision-test"))
        self.addCleanup(store.delete, profile)
        self.assertTrue(has_vision_profile_available())

    def test_upstream_reproduces_profile_driven_injection(self) -> None:
        llm = TestLLM.from_messages([], disable_vision=True)
        self.assertFalse(llm.vision_is_active())
        agent = Agent(
            llm=llm, tools=[], include_default_tools=["FinishTool"],
            filter_tools_regex=OPENHANDS_RUNTIME_TOOL_REGEX,
        )
        agent._initialize(None)
        self.addCleanup(agent.close)
        self.assertEqual(set(agent.tools_map), {"finish", VisionInspectTool.name})

    def test_restricted_initializer_does_not_scan_profiles(self) -> None:
        backend = OpenHandsBackend(
            "https://executor.example.test/mcp", "test-token",
            llm=TestLLM.from_messages([], disable_vision=True),
        )
        agent = backend._build_agent()
        with patch(
            "openhands.sdk.agent.base.has_vision_profile_available",
            side_effect=AssertionError("Restricted agent scanned saved profiles"),
        ):
            agent._initialize(None)
            first = agent.tools_map["finish"]
            agent._initialize(None)
        self.assertEqual(set(agent.tools_map), {"finish"})
        self.assertIs(type(first), FinishTool)
        self.assertIs(agent.tools_map["finish"], first)

    def test_restricted_initializer_rejects_expanded_configuration(self) -> None:
        cases = (
            {"include_default_tools": ["FinishTool", "ThinkTool"]},
            {"tools": [Tool(name="TerminalTool")]},
            {"agent_context": AgentContext()},
        )
        for update in cases:
            with self.subTest(update=update):
                values = {
                    "llm": TestLLM.from_messages([]),
                    "tools": [], "include_default_tools": ["FinishTool"],
                    **update,
                }
                agent = RestrictedOpenHandsAgent(**values)
                with self.assertRaisesRegex(BackendContractError, "only the FinishTool"):
                    agent._initialize(None)

    def _start_mcp(self) -> str:
        mcp = FastMCP("credential-free-orchestrator-test")
        self.calls: list[str] = []

        def register(name: str) -> None:
            def tool() -> dict[str, bool]:
                self.calls.append(name)
                return {"ok": True}
            mcp.tool(name=name)(tool)

        for name in sorted(EXPECTED_CODING_EXECUTOR_TOOLS):
            register(name)
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        self.addCleanup(listener.close)
        server = uvicorn.Server(uvicorn.Config(
            mcp.http_app(path="/mcp"), log_level="error", lifespan="on",
        ))
        thread = threading.Thread(
            target=server.run, kwargs={"sockets": [listener]}, daemon=True,
        )
        thread.start()

        def stop() -> None:
            server.should_exit = True
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive(), "MCP test server did not stop")

        self.addCleanup(stop)
        deadline = time.monotonic() + 10
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(server.started, "MCP test server did not start")
        return f"http://127.0.0.1:{listener.getsockname()[1]}/mcp"

    def _backend(self, llm: TestLLM) -> OpenHandsBackend:
        return OpenHandsBackend(
            self._start_mcp(), "synthetic-test-token", llm=llm,
            scratch_root=self.scratch.name,
        )

    def test_real_loop_remains_exact_with_saved_vision_profile(self) -> None:
        llm = TestLLM.from_messages([
            response("list_repositories", {}),
            response("finish", {"message": "Restricted loop complete."}),
        ] * 2, disable_vision=True)
        backend = self._backend(llm)
        for run in range(2):
            with self.subTest(run=run):
                result = backend.run(BackendRunRequest(prompt="List repositories."))
                self.assertEqual(set(result.runtime_tool_names), EXPECTED_OPENHANDS_RUNTIME_TOOLS)
                self.assertEqual(result.action_tools, ("list_repositories", "finish"))
                self.assertEqual(result.execution_status, "finished")
                self.assertEqual(list(Path(self.scratch.name).iterdir()), [])
        self.assertEqual(self.calls, ["list_repositories", "list_repositories"])

    def test_unexpected_runtime_tool_still_fails_before_llm(self) -> None:
        llm = TestLLM.from_messages([], disable_vision=True)
        backend = self._backend(llm)
        initialize = RestrictedOpenHandsAgent._initialize

        def inject_extra(agent, state):
            initialize(agent, state)
            with agent._tools_lock:
                agent._tools["think"] = ThinkTool.create(state)[0]

        with patch.object(RestrictedOpenHandsAgent, "_initialize", inject_extra):
            with self.assertRaisesRegex(BackendContractError, "runtime tool contract mismatch"):
                backend.run(BackendRunRequest(prompt="Must not run."))
        self.assertEqual(llm.call_count, 0)
        self.assertEqual(self.calls, [])
        self.assertEqual(list(Path(self.scratch.name).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
