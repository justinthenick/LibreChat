"""Offline operator CLI tests."""

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_orchestrator.review_cli import main


class ReviewCliTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        source = self.repo / "example.py"
        source.write_text("value = 1\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")
        source.write_text("value = 2\n")
        self.git("commit", "-qam", "head")
        self.head = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args],
            text=True,
        ).strip()

    def invoke(self, mode, base=None, head=None):
        output, errors = io.StringIO(), io.StringIO()
        args = [
            mode, "--repo", str(self.repo),
            "--base", base or self.base,
            "--head", head or self.head,
        ]
        with contextlib.redirect_stdout(output):
            with contextlib.redirect_stderr(errors):
                code = main(args)
        return code, output.getvalue(), errors.getvalue()

    def test_preview_real_commit_pair(self):
        with patch(
            "coding_orchestrator.provider.OpenHandsProviderConfig.build_llm"
        ) as model:
            code, output, error = self.invoke("preview")
        self.assertEqual(code, 0, error)
        result = json.loads(output)
        self.assertEqual(result["added_lines"], 1)
        self.assertEqual(result["status"], "not_reviewed")
        model.assert_not_called()

    def test_preview_ignores_broken_diagnostic_writer(self):
        import os

        with patch.dict(os.environ, {"CODING_REVIEW_STAGE_FD": "3"}):
            with patch(
                "coding_orchestrator.review_cli.os.write",
                side_effect=RuntimeError("PRIVATE_DIAGNOSTIC_VALUE"),
            ):
                code, output, errors = self.invoke("preview")
        self.assertEqual(code, 0, errors)
        self.assertEqual(json.loads(output)["status"], "not_reviewed")
        self.assertNotIn("PRIVATE_DIAGNOSTIC_VALUE", output + errors)

    def test_preview_rejects_invalid_revision(self):
        code, output, _ = self.invoke("preview", base="HEAD")
        self.assertEqual(code, 1)
        self.assertEqual(output, "")

    def test_preview_deleted_only_file(self):
        (self.repo / "example.py").unlink()
        self.git("add", "-A")
        self.git("commit", "-qm", "delete")
        deleted = self.git("rev-parse", "HEAD")
        code, output, error = self.invoke(
            "preview", base=self.head, head=deleted
        )
        self.assertEqual(code, 0, error)
        result = json.loads(output)
        self.assertEqual(result["added_lines"], 0)
        self.assertEqual(result["status"], "not_reviewed")

    def test_deleted_file_appears_in_changed_files(self):
        (self.repo / "example.py").unlink()
        self.git("add", "-A")
        self.git("commit", "-qm", "delete")
        deleted = self.git("rev-parse", "HEAD")

        code, output, error = self.invoke(
            "preview", base=self.head, head=deleted
        )
        self.assertEqual(code, 0, error)
        result = json.loads(output)
        self.assertEqual(result["changed_files"], ["example.py"])

    def test_invalid_review_never_initializes_provider(self):
        import os

        with patch.dict(os.environ, {
            "CODING_OPENHANDS_SCRATCH_ROOT":
                str(self.repo.parent / "review-scratch"),
        }):
            with patch(
                "coding_orchestrator.provider."
                "OpenHandsProviderConfig.from_environment"
            ) as provider:
                code, output, _ = self.invoke(
                    "review", base="HEAD"
                )

        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        provider.assert_not_called()

    def test_provider_failure_is_sanitized(self):
        import os
        with patch.dict(os.environ, {
            "CODING_OPENHANDS_SCRATCH_ROOT":
                str(self.repo.parent / "review-scratch"),
        }):
            with patch(
                "coding_orchestrator.provider."
                "OpenHandsProviderConfig.from_environment",
                side_effect=RuntimeError("PRIVATE_PROVIDER_DETAIL"),
            ):
                code, output, error = self.invoke("review")

        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertNotIn("PRIVATE_PROVIDER_DETAIL", error)

    def test_oversized_review_never_calls_provider(self):
        import os
        source = self.repo / "example.py"
        source.write_text("value = 3\\n" + "x" * 21000 + "\\n")
        self.git("commit", "-qam", "oversized diff")
        oversized = self.git("rev-parse", "HEAD")

        with patch.dict(os.environ, {
            "CODING_OPENHANDS_SCRATCH_ROOT":
                str(self.repo.parent / "review-scratch"),
        }):
            with patch(
                "coding_orchestrator.provider."
                "OpenHandsProviderConfig.from_environment"
            ) as provider:
                code, output, _ = self.invoke(
                    "review", base=self.head, head=oversized
                )

        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        provider.assert_not_called()

    def test_successful_review_stdout_is_only_json(self):
        import os
        from openhands.sdk.testing import TestLLM
        from test_review_backend import scripted

        llm = TestLLM.from_messages([scripted('{"findings": []}')], disable_vision=True)
        def build():
            print("Provider diagnostic is not protocol output")
            return llm

        with patch.dict(os.environ, {
            "CODING_OPENHANDS_PROVIDER": "chatgpt_subscription",
            "CODING_OPENHANDS_MODEL": "gpt-5.6-sol",
            "CODING_OPENHANDS_SCRATCH_ROOT": str(self.repo.parent / "review-cli-scratch"),
        }), patch("coding_orchestrator.provider.OpenHandsProviderConfig.build_llm", side_effect=build):
            code, output, errors = self.invoke("review")
        self.assertEqual(code, 0, errors)
        self.assertEqual(json.loads(output)["status"], "human_review_required")
        self.assertNotIn("Provider diagnostic", output)
        self.assertIn("Provider diagnostic", errors)
