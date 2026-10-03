from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_orchestrator import (
    BackendContractError,
    BackendRunResult,
    EXPECTED_OPENHANDS_RUNTIME_TOOLS,
    OpenHandsBackend,
    OpenHandsProviderConfig,
)
from coding_orchestrator.cli import main


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        environment = patch.dict(os.environ, {
            "CODING_OPENHANDS_PROVIDER": "chatgpt_subscription",
            "CODING_OPENHANDS_MODEL": "gpt-5.6-sol",
            "CODING_OPENHANDS_EXECUTOR_URL": "http://127.0.0.1:8765/mcp",
            "CODING_EXECUTOR_TOKEN": "executor-secret",
            "CODING_OPENHANDS_SCRATCH_ROOT": str(self.root / "scratch"),
        }, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def invoke(self, arguments: list[str], stdin: str = ""):
        output, error = io.StringIO(), io.StringIO()
        with patch("sys.argv", ["coding-agent-backend", *arguments]), patch(
            "sys.stdin", io.StringIO(stdin),
        ), contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            try:
                status = main()
            except SystemExit as exit_error:
                status = exit_error.code
        return status, output.getvalue(), error.getvalue()

    def test_run_reads_stdin_and_emits_provider_evidence(self) -> None:
        result = BackendRunResult(
            backend="openhands", execution_status="finished",
            final_response="done",
            runtime_tool_names=tuple(sorted(EXPECTED_OPENHANDS_RUNTIME_TOOLS)),
            action_tools=("list_repositories", "finish"),
        )
        with patch.object(OpenHandsBackend, "run", return_value=result) as run:
            status, output, error = self.invoke(
                ["run", "openhands", "--prompt-file", "-", "--max-iterations", "4"],
                "List approved repositories and finish.",
            )
        self.assertEqual(status, 0, error)
        request = run.call_args.args[0]
        self.assertEqual(request.max_iterations, 4)
        self.assertEqual(request.prompt, "List approved repositories and finish.")
        evidence = json.loads(output)
        self.assertTrue(evidence["ok"])
        self.assertEqual(evidence["model"], "gpt-5.6-sol")
        self.assertEqual(evidence["provider"], "chatgpt_subscription")
        self.assertEqual(evidence["action_tools"], ["list_repositories", "finish"])
        self.assertNotIn("executor-secret", output + error)

    def test_run_reads_utf8_file(self) -> None:
        prompt = self.root / "prompt.txt"
        prompt.write_text("Check café.", encoding="utf-8")
        result = BackendRunResult("openhands", "finished", "done", (), ())
        with patch.object(OpenHandsBackend, "run", return_value=result) as run:
            status, _, error = self.invoke(
                ["run", "openhands", "--prompt-file", str(prompt)],
            )
        self.assertEqual(status, 0, error)
        self.assertEqual(run.call_args.args[0].prompt, "Check café.")

    def test_invalid_iterations_never_start_backend(self) -> None:
        for value in ("0", "101", "-1", "abc"):
            with self.subTest(value=value), patch.object(OpenHandsBackend, "run") as run:
                status, output, _ = self.invoke([
                    "run", "openhands", "--prompt-file", "-", "--max-iterations", value,
                ])
                self.assertEqual(status, 2)
                self.assertEqual(output, "")
                run.assert_not_called()

    def test_blank_or_missing_prompt_fails_before_run(self) -> None:
        for path in ("-", str(self.root / "missing.txt")):
            with self.subTest(path=path), patch.object(OpenHandsBackend, "run") as run:
                status, output, _ = self.invoke(
                    ["run", "openhands", "--prompt-file", path], "  ",
                )
                self.assertEqual(status, 1)
                self.assertEqual(output, "")
                run.assert_not_called()

    def test_missing_provider_fails_before_run(self) -> None:
        del os.environ["CODING_OPENHANDS_PROVIDER"]
        with patch.object(OpenHandsBackend, "run") as run:
            status, output, error = self.invoke(
                ["run", "openhands", "--prompt-file", "-"], "test",
            )
        self.assertEqual(status, 1)
        self.assertEqual(output, "")
        self.assertIn("CODING_OPENHANDS_PROVIDER is required", error)
        run.assert_not_called()

    def test_runtime_errors_cannot_leak_provider_response(self) -> None:
        for exception in (RuntimeError, ValueError):
            with self.subTest(exception=exception), patch.object(
                OpenHandsBackend, "run",
                side_effect=exception("private-token-response"),
            ):
                status, output, error = self.invoke(
                    ["run", "openhands", "--prompt-file", "-"], "test",
                )
                self.assertEqual(status, 1)
                self.assertEqual(output, "")
                self.assertNotIn("private-token-response", error)
                self.assertIn("no fallback", error)

    def test_contract_failure_has_no_success_output(self) -> None:
        with patch.object(
            OpenHandsBackend, "run",
            side_effect=BackendContractError("runtime tool contract mismatch"),
        ):
            status, output, error = self.invoke(
                ["run", "openhands", "--prompt-file", "-"], "test",
            )
        self.assertEqual(status, 1)
        self.assertEqual(output, "")
        self.assertIn("contract mismatch", error)

    def test_explicit_login_does_not_require_executor(self) -> None:
        del os.environ["CODING_EXECUTOR_TOKEN"]
        del os.environ["CODING_OPENHANDS_EXECUTOR_URL"]
        with patch.object(OpenHandsProviderConfig, "login") as login:
            status, output, error = self.invoke(["login", "openhands"])
        self.assertEqual(status, 0, error)
        login.assert_called_once()
        self.assertEqual(json.loads(output)["model"], "gpt-5.6-sol")

    def test_probe_does_not_require_provider(self) -> None:
        del os.environ["CODING_OPENHANDS_PROVIDER"]
        del os.environ["CODING_OPENHANDS_MODEL"]
        from coding_orchestrator import BackendProbe, EXPECTED_CODING_EXECUTOR_TOOLS
        with patch.object(
            OpenHandsBackend, "probe",
            return_value=BackendProbe("openhands", tuple(EXPECTED_CODING_EXECUTOR_TOOLS)),
        ):
            status, output, error = self.invoke(["probe", "openhands"])
        self.assertEqual(status, 0, error)
        self.assertEqual(json.loads(output)["tool_count"], 9)


if __name__ == "__main__":
    unittest.main()
