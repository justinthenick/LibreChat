from __future__ import annotations

import json
import pickle
import unittest

from coding_orchestrator.job_worker import RunContext, WorkerCancelled, WorkerDeadline, WorkerLimit
from coding_orchestrator.openhands_profile import (
    OpenHandsJobRunner, OpenHandsProfileError, _ScopedEvents, _raise_run_failure, create_openhands_profile,
)


def unused_factory():
    raise AssertionError("Factories must only run inside the worker")


class Control:
    def __init__(self):
        self.progress = []
        self.failure = None

    def _check(self):
        if self.failure:
            raise self.failure

    def emit_progress(self, value):
        self._check()
        self.progress.append(value)


class ScopedEventTests(unittest.TestCase):
    def setUp(self):
        self.control = Control()
        self.events = _ScopedEvents(RunContext("job", "prompt", "fixture", "modification"), self.control)
        self.index = 0

    def action(self, tool, **arguments):
        from openhands.sdk.event import ActionEvent
        from openhands.sdk.llm import MessageToolCall
        from openhands.sdk.mcp.definition import MCPToolAction
        from openhands.sdk.tool.builtins.finish import FinishAction
        self.index += 1
        call = MessageToolCall(id=f"call-{self.index}", name=tool, arguments=json.dumps(arguments), origin="responses")
        value = (FinishAction(message=arguments["message"]) if tool == "finish"
                 else MCPToolAction(data=arguments))
        return ActionEvent(thought=[], action=value, tool_name=tool, tool_call_id=call.id,
                           llm_response_id="response", tool_call=call)

    def observe(self, action, result):
        import mcp.types
        from openhands.sdk.event import ObservationEvent
        from openhands.sdk.mcp.definition import MCPToolObservation
        observation = MCPToolObservation.from_call_tool_result(action.tool_name, mcp.types.CallToolResult(
            content=[mcp.types.TextContent(type="text", text=json.dumps(result))]))
        self.events(ObservationEvent(action_id=action.id, tool_call_id=action.tool_call_id,
                                     tool_name=action.tool_name, observation=observation))

    def create(self, mode="modification"):
        action = self.action("create_task", repository="fixture", task_name="fix", task_mode=mode)
        self.events(action)
        self.observe(action, {"task_id": "observed-task", "branch": "agent/observed-task",
                             "task_branch": "agent/observed-task", "task_mode": mode,
                             "source_repository": "fixture", "source_ref": "HEAD", "source_branch": "main",
                             "source_commit": "a" * 40, "source_status": ""})

    def test_wrong_scope_and_mode_and_discovery_are_sticky_denials(self):
        for tool, arguments in (("list_repositories", {}),
                ("create_task", {"repository": "foreign", "task_name": "fix", "task_mode": "modification"}),
                ("create_task", {"repository": "fixture", "task_name": "fix", "task_mode": "read_only"}),
                ("create_task", {"repository": "fixture", "task_name": "fix"})):
            with self.subTest(tool=tool, arguments=arguments):
                self.setUp()
                with self.assertRaisesRegex(OpenHandsProfileError, "^action_scope_denied$"):
                    self.events(self.action(tool, **arguments))
                with self.assertRaises(OpenHandsProfileError):
                    self.events(self.action("finish", message="done"))
                self.assertEqual(self.control.progress, [])

    def test_task_identity_must_come_from_matched_creation_observation(self):
        with self.assertRaises(OpenHandsProfileError):
            self.events(self.action("read_file", task_id="claimed-task", path="fixture.py"))
        self.setUp()
        self.create()
        self.assertEqual(self.events.collector.snapshot()["task"]["task_id"], "observed-task")
        with self.assertRaises(OpenHandsProfileError):
            self.events(self.action("read_file", task_id="claimed-task", path="fixture.py"))
        self.assertEqual(len(self.control.progress), 2)

    def test_readonly_patch_and_second_pending_action_are_denied(self):
        self.events = _ScopedEvents(RunContext("job", "prompt", "fixture", "read_only"), self.control)
        self.create("read_only")
        with self.assertRaises(OpenHandsProfileError):
            self.events(self.action("apply_patch", task_id="observed-task", patch="patch"))
        self.setUp()
        self.create()
        self.events(self.action("read_file", task_id="observed-task", path="fixture.py"))
        with self.assertRaises(OpenHandsProfileError):
            self.events(self.action("git_diff", task_id="observed-task"))
        self.assertEqual(self.events.collector.snapshot()["pending_count"], 1)

    def test_only_actions_and_observations_emit_progress_and_controls_win(self):
        self.events(object())
        self.assertEqual(self.control.progress, [])
        for failure in (WorkerCancelled(), WorkerDeadline()):
            self.control.failure = failure
            with self.assertRaises(type(failure)):
                self.events(self.action("list_repositories"))
        self.assertFalse(self.events.denied)

    def test_unmatched_observation_latches_guard(self):
        action = self.action("create_task", repository="fixture", task_name="fix", task_mode="modification")
        with self.assertRaises(ValueError):
            self.observe(action, {})
        with self.assertRaises(OpenHandsProfileError):
            self.events(self.action("finish", message="done"))


class DormantConfigurationTests(unittest.TestCase):
    def test_sdk_error_causes_keep_only_owned_worker_classifications(self):
        from openhands.sdk.conversation.exceptions import ConversationRunError
        for failure in (WorkerCancelled(), WorkerDeadline(), WorkerLimit()):
            inner = RuntimeError("private intermediate detail")
            inner.__cause__ = failure
            wrapped = ConversationRunError("synthetic-conversation", inner)
            wrapped.__cause__ = inner
            with self.assertRaises(type(failure)) as raised:
                _raise_run_failure(wrapped)
            self.assertIs(raised.exception, failure)
        private = RuntimeError("private provider detail")
        private.__cause__ = private
        wrapped = ConversationRunError("synthetic-conversation", private)
        wrapped.__cause__ = private
        with self.assertRaisesRegex(OpenHandsProfileError, "^openhands_profile_failed$"):
            _raise_run_failure(wrapped)

    def test_factories_are_lazy_picklable_and_remote_stop_defaults_unconfirmed(self):
        profile = create_openhands_profile(profile_id="fixture", repository_aliases=frozenset({"fixture"}),
            endpoint="https://fixture.invalid/mcp", token_factory=unused_factory, llm_factory=unused_factory,
            authorize=lambda *_: True)
        runner = pickle.loads(pickle.dumps(profile.runner))
        self.assertIsInstance(runner, OpenHandsJobRunner)
        self.assertIs(runner.token_factory, unused_factory)
        self.assertFalse(profile.confirm_stopped(RunContext("job", "prompt", "fixture", "modification")))

    def test_invalid_factories_and_static_endpoint_rejected(self):
        for values in (("https://fixture.invalid/not-mcp", unused_factory, unused_factory),
                       ("https://fixture.invalid/mcp", "token", unused_factory),
                       ("https://fixture.invalid/mcp", unused_factory, "model")):
            with self.assertRaises(ValueError):
                OpenHandsJobRunner(*values)


if __name__ == "__main__":
    unittest.main()
