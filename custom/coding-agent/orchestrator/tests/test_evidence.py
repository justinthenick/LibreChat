from __future__ import annotations

import hashlib
import json
import unittest

from coding_orchestrator.evidence import EvidenceCollector, EvidenceError


TASK_ID = "fix-fixture-1234abcd"
BRANCH = "agent/" + TASK_ID
COMMAND = "python -m unittest"


def metadata(**overrides):
    return {"task_id": TASK_ID, "branch": BRANCH, "task_branch": BRANCH,
            "task_mode": "modification", "source_repository": "fixture", "source_ref": "HEAD",
            "source_branch": "main", "source_commit": "a" * 40, "source_status": "",
            "path": "/private/auth/task/path", **overrides}


def status(**overrides):
    return {"task_id": TASK_ID, "branch": BRANCH, "status": " M calculator.py\n", **overrides}


def check(exit_code=0, **overrides):
    return {"command": COMMAND, "exit_code": exit_code, "stdout": "private file content",
            "stderr": "private diagnostic", "truncated": False, **overrides}


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.collector = EvidenceCollector("fixture")
        self.count = 0

    def action(self, tool, **arguments):
        self.count += 1
        action_id, call_id = f"action-{self.count}", f"call-{self.count}"
        if tool not in {"create_task", "list_repositories", "finish"}:
            arguments = {"task_id": TASK_ID, **arguments}
        self.collector.record_action(action_id, call_id, tool, arguments)
        return action_id, call_id, tool

    def observe(self, identity, result, is_error=False):
        self.collector.record_observation(*identity, is_error=is_error, result=result)

    def call(self, tool, result, **arguments):
        identity = self.action(tool, **arguments)
        self.observe(identity, result)
        return identity

    def create(self):
        return self.call("create_task", metadata(), repository="fixture", task_name="fix fixture")

    def finals(self):
        self.call("git_diff", "diff --git a/calculator.py b/calculator.py\n+fixed\n")
        self.call("task_status", status())

    def test_empty_and_finish_prose_cannot_prove_checks(self):
        self.assertEqual(self.collector.snapshot()["observed_checks_status"], "not_run")
        self.call("finish", None, message="All tests passed. source_commit=secret")
        snapshot = self.collector.snapshot()
        self.assertEqual(snapshot["observed_checks_status"], "not_run")
        self.assertFalse(snapshot["evidence_complete"])
        self.assertNotIn("secret", json.dumps(snapshot))

    def test_matched_flow_retains_only_bounded_evidence(self):
        self.call("list_repositories", ["fixture", "private-repository"])
        self.create()
        self.call("read_file", "SECRET_READ", path="calculator.py")
        self.call("search_text", "SECRET_SEARCH", query="add")
        self.call("list_files", ["SECRET_LIST"])
        self.call("run_check", check(1), command=COMMAND)
        self.call("apply_patch", status(), patch="some bounded patch")
        self.call("run_check", check(), command=COMMAND)
        self.finals()
        snapshot = self.collector.snapshot()
        self.assertEqual(snapshot["observed_checks_status"], "passed")
        self.assertTrue(snapshot["evidence_complete"])
        self.assertEqual(snapshot["checks"][1]["stdout_sha256"], hashlib.sha256(b"private file content").hexdigest())
        self.assertEqual(snapshot["final_diff"]["sha256"], hashlib.sha256(snapshot["final_diff"]["text"].encode()).hexdigest())
        serialized = json.dumps(snapshot)
        for secret in ("SECRET_", "private file content", "private diagnostic", "/private/auth", "private-repository"):
            self.assertNotIn(secret, serialized)
        snapshot["task"]["source_commit"] = "changed"
        snapshot["checks"].clear()
        self.assertEqual(len(self.collector.snapshot()["checks"]), 2)
        self.assertEqual(self.collector.snapshot()["task"]["source_commit"], "a" * 40)

    def test_final_artifacts_do_not_imply_checks_or_task_success(self):
        self.create()
        self.finals()
        snapshot = self.collector.snapshot()
        self.assertTrue(snapshot["evidence_complete"])
        self.assertEqual(snapshot["observed_checks_status"], "not_run")
        self.assertNotIn("success", snapshot)
        self.call("run_check", check(1), command=COMMAND)
        self.assertEqual(self.collector.snapshot()["observed_checks_status"], "failed")
        self.assertTrue(self.collector.snapshot()["evidence_complete"])

    def test_patch_invalidates_checks_and_both_final_artifacts(self):
        self.create()
        self.call("run_check", check(), command=COMMAND)
        self.finals()
        self.call("apply_patch", status(), patch="patch")
        snapshot = self.collector.snapshot()
        self.assertEqual(snapshot["observed_checks_status"], "incomplete")
        self.assertFalse(snapshot["evidence_complete"])
        self.call("run_check", check(), command=COMMAND)
        self.finals()
        self.assertTrue(self.collector.snapshot()["evidence_complete"])
        self.assertEqual(self.collector.snapshot()["observed_checks_status"], "passed")

    def test_checks_and_final_reads_started_during_patch_are_stale(self):
        self.create()
        patch = self.action("apply_patch", patch="patch")
        checking = self.action("run_check", command=COMMAND)
        diff = self.action("git_diff")
        final_status = self.action("task_status")
        self.observe(patch, status())
        self.observe(checking, check())
        self.observe(diff, "diff")
        self.observe(final_status, status())
        self.assertEqual(self.collector.snapshot()["observed_checks_status"], "incomplete")
        self.assertFalse(self.collector.snapshot()["evidence_complete"])

    def test_checks_started_before_patch_cannot_validate_later(self):
        self.create()
        checking = self.action("run_check", command=COMMAND)
        self.call("apply_patch", status(), patch="patch")
        self.observe(checking, check())
        self.assertEqual(self.collector.snapshot()["observed_checks_status"], "incomplete")

    def test_late_older_check_does_not_override_newer_failure(self):
        self.create()
        older = self.action("run_check", command=COMMAND)
        newer = self.action("run_check", command=COMMAND)
        self.observe(newer, check(1))
        self.observe(older, check())
        self.assertEqual(self.collector.snapshot()["observed_checks_status"], "failed")

    def test_all_distinct_checks_must_be_current(self):
        self.create()
        self.call("run_check", check(), command=COMMAND)
        self.call("apply_patch", status(), patch="patch")
        self.call("run_check", check(command="git diff --check"), command="git diff --check")
        self.assertEqual(self.collector.snapshot()["observed_checks_status"], "incomplete")

    def test_pending_and_tool_errors_cannot_complete(self):
        self.create()
        self.finals()
        identity = self.action("read_file", path="file")
        self.assertFalse(self.collector.snapshot()["evidence_complete"])
        self.observe(identity, "SECRET_RAW_ERROR", is_error=True)
        snapshot = self.collector.snapshot()
        self.assertFalse(snapshot["evidence_complete"])
        self.assertEqual(snapshot["errors"], ["tool_error"])
        self.assertNotIn("SECRET", json.dumps(snapshot))

    def test_truncation_and_check_tool_error_are_incomplete(self):
        self.create()
        self.call("run_check", check(truncated=True), command=COMMAND)
        self.assertEqual(self.collector.snapshot()["observed_checks_status"], "incomplete")
        identity = self.action("run_check", command=COMMAND)
        self.observe(identity, "raw error", is_error=True)
        self.assertEqual(self.collector.snapshot()["observed_checks_status"], "incomplete")

    def test_action_and_observation_identity_validation(self):
        self.create()
        identity = self.action("read_file", path="file")
        for args in (("unknown", identity[1], identity[2]), (identity[0], "other", identity[2]),
                     (identity[0], identity[1], "git_diff")):
            with self.assertRaises(EvidenceError):
                self.observe(args, "secret")
        self.observe(identity, "okay")
        with self.assertRaisesRegex(EvidenceError, "^duplicate_observation$"):
            self.observe(identity, "secret")
        for args in ((identity[0], "new-call"), ("new-action", identity[1])):
            with self.assertRaisesRegex(EvidenceError, "^duplicate_action$"):
                self.collector.record_action(*args, "list_repositories", {})
        self.assertNotIn("secret", json.dumps(self.collector.snapshot()))

    def test_task_scope_cannot_change(self):
        with self.assertRaises(EvidenceError):
            self.action("git_diff")
        self.create()
        with self.assertRaises(EvidenceError):
            self.action("read_file", task_id="other-task", path="file")
        with self.assertRaises(EvidenceError):
            self.action("create_task", repository="fixture", task_name="second")
        with self.assertRaises(EvidenceError):
            self.call("task_status", status(task_id="other-task"))

    def test_creation_validates_source_and_branch(self):
        for change in ({"source_repository": "other"}, {"source_commit": "not-a-sha"},
                       {"source_status": " M file"}, {"task_id": "../escape"},
                       {"branch": "main"}, {"task_branch": "main"}, {"task_mode": "read_only"},
                       {"source_ref": "elsewhere"}, {"source_branch": "/private/auth"}):
            with self.subTest(change=change):
                collector = EvidenceCollector("fixture")
                collector.record_action("a", "c", "create_task", {"repository": "fixture", "task_name": "fix"})
                with self.assertRaises(EvidenceError):
                    collector.record_observation("a", "c", "create_task", is_error=False, result=metadata(**change))
                self.assertIsNone(collector.snapshot()["task"])

    def test_rejects_malformed_and_oversized_payloads_without_exposing_them(self):
        self.create()
        for result in (check(exit_code=True), check(stdout=None), check(truncated="false"),
                       check(command="wrong"), check(stdout="x" * 65537)):
            identity = self.action("run_check", command=COMMAND)
            with self.assertRaises(EvidenceError) as raised:
                self.observe(identity, result)
            self.assertRegex(str(raised.exception), r"^[a-z_]+$")
        for result in ("é" * 32769, "\ud800", {"secret": "value"}):
            with self.assertRaises(EvidenceError):
                self.call("git_diff", result)
        with self.assertRaises(EvidenceError):
            self.action("docker", secret="not-persisted")
        with self.assertRaises(EvidenceError):
            self.action("read_file", path="file", token="not-persisted")
        for tool, arguments in (("read_file", {"path": {"secret": "value"}}),
                                ("read_file", {"path": "file", "start_line": True}),
                                ("read_file", {"path": "file", "start_line": 5, "end_line": 2}),
                                ("search_text", {"query": None})):
            with self.assertRaises(EvidenceError):
                self.action(tool, **arguments)

    def test_action_limit_and_snapshot_bound(self):
        self.create()
        for _ in range(29):
            self.call("run_check", check(command="a" * 512), command="a" * 512)
        self.call("git_diff", "é" * 32768)
        self.call("task_status", status(status="x" * 4096))
        snapshot = self.collector.snapshot()
        self.assertEqual(snapshot["action_count"], 32)
        self.assertLessEqual(len(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode()), 131072)
        with self.assertRaisesRegex(EvidenceError, "^action_limit$"):
            self.action("finish", message="done")
        self.assertFalse(self.collector.snapshot()["evidence_complete"])
        for maximum in (0, 33, True):
            with self.assertRaises(EvidenceError):
                EvidenceCollector("fixture", maximum)


class SDKEventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from openhands.sdk.event import ActionEvent, ObservationEvent
            from openhands.sdk.llm import MessageToolCall
            from openhands.sdk.mcp.definition import MCPToolAction, MCPToolObservation
            import mcp.types
        except ImportError:
            raise unittest.SkipTest("Pinned OpenHands SDK is optional")
        cls.ActionEvent, cls.ObservationEvent, cls.MessageToolCall = ActionEvent, ObservationEvent, MessageToolCall
        cls.MCPToolAction, cls.MCPToolObservation, cls.mcp = MCPToolAction, MCPToolObservation, mcp.types

    def pair(self, collector, name, arguments, result):
        action = self.ActionEvent(thought=[], action=self.MCPToolAction(data=arguments), tool_name=name,
                                  tool_call_id="call-" + name, llm_response_id="response-id",
                                  tool_call=self.MessageToolCall(id="call-" + name, name=name,
                                                               arguments=json.dumps(arguments), origin="completion"))
        collector.on_event(action)
        text = result if type(result) is str else json.dumps(result)
        observation = self.MCPToolObservation.from_call_tool_result(name, self.mcp.CallToolResult(
            content=[self.mcp.TextContent(type="text", text=text)]))
        collector.on_event(self.ObservationEvent(action_id=action.id, tool_call_id=action.tool_call_id,
                                                tool_name=name, observation=observation))
        return action

    def test_real_sdk_event_pairs_use_action_data_and_mcp_prefix(self):
        collector = EvidenceCollector("fixture")
        collector.on_event(object())
        self.pair(collector, "list_repositories", {}, ["fixture"])
        self.pair(collector, "create_task", {"repository": "fixture", "task_name": "fix"}, metadata())
        self.pair(collector, "run_check", {"task_id": TASK_ID, "command": COMMAND}, check())
        self.pair(collector, "git_diff", {"task_id": TASK_ID}, "diff --git a/file b/file\n+fixed\n")
        self.pair(collector, "task_status", {"task_id": TASK_ID}, status())
        self.assertTrue(collector.snapshot()["evidence_complete"])
        self.assertEqual(collector.snapshot()["observed_checks_status"], "passed")

    def test_real_sdk_finish_and_untrusted_prose_are_not_evidence(self):
        from openhands.sdk.tool.builtins.finish import FinishAction, FinishObservation
        collector = EvidenceCollector("fixture")
        action = self.ActionEvent(thought=[], action=FinishAction(message="all checks passed"), tool_name="finish",
                                  tool_call_id="finish-call", llm_response_id="response-id",
                                  tool_call=self.MessageToolCall(id="finish-call", name="finish", arguments="{}", origin="completion"))
        collector.on_event(action)
        collector.on_event(self.ObservationEvent(action_id=action.id, tool_call_id="finish-call", tool_name="finish",
                                                observation=FinishObservation.from_text("all checks passed")))
        self.assertEqual(collector.snapshot()["observed_checks_status"], "not_run")
        self.assertFalse(collector.snapshot()["evidence_complete"])
        self.assertNotIn("all checks passed", json.dumps(collector.snapshot()))

    def test_real_sdk_rejects_wrong_inner_tool_name_and_duplicate_json_fields(self):
        from openhands.sdk.llm import TextContent
        collector = EvidenceCollector("fixture")
        action = self.pair(collector, "list_repositories", {}, ["fixture"])
        bad = self.MCPToolObservation(tool_name="docker", content=[TextContent(text="secret")])
        with self.assertRaisesRegex(EvidenceError, "^observation_mismatch$"):
            collector.on_event(self.ObservationEvent(action_id=action.id, tool_call_id=action.tool_call_id,
                                                    tool_name="list_repositories", observation=bad))
        collector = EvidenceCollector("fixture")
        with self.assertRaises(EvidenceError):
            self.pair(collector, "create_task", {"repository": "fixture", "task_name": "fix"}, '{"task_id":"a","task_id":"b"}')

    def test_real_sdk_lists_accept_multiple_text_blocks_and_scalar_names(self):
        from openhands.sdk.llm import TextContent
        for texts in (["fixture", "another"], ["true"], ['{"result":["fixture"]}']):
            with self.subTest(texts=texts):
                collector = EvidenceCollector("fixture")
                collector.record_action("a", "c", "list_repositories", {})
                observation = self.MCPToolObservation.from_call_tool_result("list_repositories", self.mcp.CallToolResult(
                    content=[self.mcp.TextContent(type="text", text=text) for text in texts]))
                collector.on_event(self.ObservationEvent(action_id="a", tool_call_id="c", tool_name="list_repositories",
                                                        observation=observation))
                self.assertEqual(collector.snapshot()["pending_count"], 0)
        collector = EvidenceCollector("fixture")
        collector.record_action("a", "c", "list_repositories", {})
        observation = self.MCPToolObservation(tool_name="list_repositories", content=[TextContent(text="missing prefix")])
        with self.assertRaisesRegex(EvidenceError, "^malformed_observation$"):
            collector.on_event(self.ObservationEvent(action_id="a", tool_call_id="c", tool_name="list_repositories",
                                                    observation=observation))

    def test_real_sdk_missing_action_and_mismatched_call_are_rejected(self):
        for action, call_name in ((None, "list_repositories"), (self.MCPToolAction(data={}), "other")):
            collector = EvidenceCollector("fixture")
            event = self.ActionEvent(thought=[], action=action, tool_name="list_repositories", tool_call_id="call",
                                     llm_response_id="response-id", tool_call=self.MessageToolCall(
                                         id="call", name=call_name, arguments="{}", origin="completion"))
            with self.assertRaises(EvidenceError):
                collector.on_event(event)
            self.assertFalse(collector.snapshot()["evidence_complete"])


if __name__ == "__main__":
    unittest.main()
