"""Stage 4 adversarial regressions using real Git and the pinned SDK."""

import json
import unittest
from unittest.mock import patch

from openhands.sdk.llm import Message, MessageToolCall, TextContent
from openhands.sdk.testing import TestLLM

from coding_orchestrator.backend import BackendContractError
from coding_orchestrator.pr_review import (
    ReviewError, collect_diff, extract_added_lines, validate_findings,
)
from coding_orchestrator.review_backend import ReviewBackend
from coding_orchestrator.review_limits import (
    MAX_RESPONSE_BYTES, parse_report, validate_input,
)
import test_review_backend as fixtures
from test_review_backend import scripted


class ReportLimitsTests(unittest.TestCase):
    def test_oversized_json_rejected_before_decode(self):
        with patch("coding_orchestrator.review_limits.json.loads") as decode:
            with self.assertRaises(ReviewError):
                parse_report(" " * (MAX_RESPONSE_BYTES + 1))
            decode.assert_not_called()

    def test_multibyte_response_uses_bytes(self):
        with self.assertRaises(ReviewError):
            parse_report('"' + "界" * 22000 + '"')

    def test_exact_response_limit(self):
        answer = '{"findings": []}'
        self.assertEqual(parse_report(answer.ljust(MAX_RESPONSE_BYTES)),
                         {"findings": []})

    def test_deep_json_rejected_before_decode(self):
        with patch("coding_orchestrator.review_limits.json.loads") as decode:
            with self.assertRaises(ReviewError):
                parse_report("[" * 2000 + "]" * 2000)
            decode.assert_not_called()

    def test_duplicate_keys_and_nonfinite_values(self):
        for answer in ('{"findings": [1], "findings": []}',
                       '{"findings": [{"line": 1, "line": 2}]}',
                       '{"findings": NaN}', '{"findings": Infinity}',
                       '{"findings": -Infinity}'):
            with self.subTest(answer=answer), self.assertRaises(ReviewError):
                parse_report(answer)

    def test_brackets_and_escapes_in_strings(self):
        content = '[' * 50 + '"' + chr(92) + '}' * 50
        self.assertEqual(parse_report(json.dumps({"text": content})),
                         {"text": content})

    def test_input_limit_is_utf8_bytes(self):
        validate_input("a" * 20000)
        with self.assertRaises(ReviewError):
            validate_input("界" * 7000)

    def test_invalid_unicode_response(self):
        with self.assertRaises(ReviewError):
            parse_report(chr(0xd800))

    def test_control_characters_and_escaped_surrogates_in_findings(self):
        for text in ("bad" + chr(27) + "[2J", chr(0xd800), "two\nlines"):
            finding = {"severity": "minor", "path": "a.py", "line": 1,
                       "title": text, "evidence": "x", "recommendation": "Inspect"}
            with self.subTest(text=repr(text)), self.assertRaises(ReviewError):
                validate_findings([{"path": "a.py", "line": 1, "text": "x"}],
                                  {"findings": [finding]})


class ReviewIsolationTests(unittest.TestCase):
    setUp = fixtures.ReviewBackendTests.setUp
    git = fixtures.ReviewBackendTests.git
    run_review = fixtures.ReviewBackendTests.run_review

    def test_ambient_plugins_never_discovered(self):
        with patch(
            "openhands.sdk.conversation.impl.local_conversation.load_available_plugins",
            side_effect=AssertionError("Ambient plugin discovery forbidden"),
        ) as discover:
            result = self.run_review('{"findings": []}')
            self.assertEqual(result["status"], "human_review_required")
            discover.assert_not_called()

    def test_mcp_registration_never_runs(self):
        from coding_orchestrator.review_conversation import ReviewConversation
        with patch.object(ReviewConversation, "_runtime_mcp_tools",
                          side_effect=AssertionError("MCP forbidden")) as mcp:
            self.run_review('{"findings": []}')
            mcp.assert_not_called()

    def test_explicit_mcp_rejected_before_provider_call(self):
        from coding_orchestrator.review_conversation import ReviewConversation
        from coding_orchestrator.restricted_agent import RestrictedOpenHandsAgent
        from openhands.sdk.mcp import MCPServer
        agent = RestrictedOpenHandsAgent(
            llm=TestLLM.from_messages([], disable_vision=True), tools=[],
            include_default_tools=["FinishTool"],
            mcp_config={"forbidden": MCPServer(transport="streamable-http",
                                               url="http://127.0.0.1:1/mcp")},
        )
        self.scratch.mkdir()
        conversation = ReviewConversation(agent=agent, workspace=self.scratch,
                                          visualizer=None)
        try:
            with self.assertRaises(BackendContractError):
                conversation.send_message("review")
            self.assertEqual(agent.llm.call_count, 0)
        finally:
            conversation.close()

    def test_oversized_response_cleanup(self):
        with self.assertRaises(ReviewError):
            self.run_review(" " * (MAX_RESPONSE_BYTES + 1))

    def test_duplicate_response_cleanup(self):
        with self.assertRaises(ReviewError):
            self.run_review('{"findings": [1], "findings": []}')

    def test_nonfinishing_response_rejected(self):
        llm = TestLLM.from_messages([
            Message(role="assistant", content=[TextContent(text="Looks fine")]),
        ], disable_vision=True)
        with self.assertRaises(BackendContractError):
            ReviewBackend(llm, self.scratch).run(self.repo, self.base, self.head)
        self.assertEqual(list(self.scratch.glob("review-*")), [])

    def test_forbidden_tool_attempt_followed_by_finish_rejected(self):
        llm = TestLLM.from_messages([
            Message(role="assistant", content=[], tool_calls=[MessageToolCall(
                id="forbidden", name="run_check", arguments="{}", origin="completion",
            )]),
            scripted('{"findings": []}'),
        ], disable_vision=True)
        with self.assertRaises(BackendContractError):
            ReviewBackend(llm, self.scratch).run(self.repo, self.base, self.head)
        self.assertEqual(list(self.scratch.glob("review-*")), [])

    def test_multibyte_input_never_calls_llm(self):
        (self.repo / "example.py").write_text("界" * 7000 + "\n")
        self.git("commit", "-qam", "large UTF-8 diff")
        llm = TestLLM.from_messages([], disable_vision=True)
        with self.assertRaises(ReviewError):
            ReviewBackend(llm, self.scratch).run(
                self.repo, self.head, self.git("rev-parse", "HEAD"))
        self.assertEqual(llm.call_count, 0)

    def test_header_like_source_lines_are_evidence(self):
        (self.repo / "example.py").write_text("-- old\n")
        self.git("commit", "-qam", "old header-like source")
        base = self.git("rev-parse", "HEAD")
        (self.repo / "example.py").write_text("++ new\n")
        self.git("commit", "-qam", "new header-like source")
        diff = collect_diff(self.repo, base, self.git("rev-parse", "HEAD"))
        self.assertEqual(extract_added_lines(diff), [
            {"path": "example.py", "line": 1, "text": "++ new"}])

    def test_unicode_line_separator_keeps_git_line_number(self):
        text = "first" + chr(0x2028) + "second"
        (self.repo / "example.py").write_text(text + "\n")
        self.git("commit", "-qam", "unicode separator")
        diff = collect_diff(self.repo, self.head, self.git("rev-parse", "HEAD"))
        self.assertEqual(extract_added_lines(diff), [
            {"path": "example.py", "line": 1, "text": text}])

    def test_literal_backslash_zero_is_not_binary(self):
        text = 'value = "' + chr(92) + '0"'
        (self.repo / "example.py").write_text(text + "\n")
        self.git("commit", "-qam", "escaped zero")
        diff = collect_diff(self.repo, self.head, self.git("rev-parse", "HEAD"))
        self.assertEqual(extract_added_lines(diff)[0]["text"], text)

    def test_large_git_output_rejected(self):
        (self.repo / "example.py").write_text("x" * 300000 + "\n")
        self.git("commit", "-qam", "oversized evidence")
        with self.assertRaisesRegex(ReviewError, "size limit"):
            collect_diff(self.repo, self.head, self.git("rev-parse", "HEAD"))

    def test_request_limits_applied_to_direct_backend(self):
        llm = TestLLM.from_messages([], disable_vision=True)
        llm.timeout = None
        llm.stream_idle_timeout = None
        llm.num_retries = 5
        ReviewBackend(llm, self.scratch)
        self.assertEqual(llm.timeout, 60)
        self.assertEqual(llm.stream_idle_timeout, 30)
        self.assertEqual(llm.num_retries, 0)

    def test_ambient_agents_never_registered(self):
        with patch(
            "openhands.sdk.conversation.impl.local_conversation.register_file_agents",
            side_effect=AssertionError("Ambient agent discovery forbidden"),
        ) as register:
            self.run_review('{"findings": []}')
            register.assert_not_called()

    def test_git_timeout_fails_closed(self):
        with patch("coding_orchestrator.pr_review.selectors.DefaultSelector.select",
                   return_value=[]):
            with self.assertRaisesRegex(ReviewError, "timed out"):
                collect_diff(self.repo, self.base, self.head)
        self.assertEqual(self.git("status", "--porcelain"), "")
