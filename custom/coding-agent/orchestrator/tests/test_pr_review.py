"""Offline tests for PR review evidence."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from coding_orchestrator.pr_review import ReviewError, validate_commits


class CommitValidationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)

        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")

        file = self.repo / "example.py"
        file.write_text("value = 1\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")

        file.write_text("value = 2\n")
        self.git("commit", "-qam", "head")
        self.head = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args],
            text=True,
        ).strip()

    def test_valid_ancestry(self):
        validate_commits(self.repo, self.base, self.head)

    def test_reversed_ancestry_rejected(self):
        with self.assertRaises(ReviewError):
            validate_commits(self.repo, self.head, self.base)

    def test_short_revision_rejected(self):
        with self.assertRaises(ReviewError):
            validate_commits(self.repo, "HEAD", self.head)

    def test_unknown_commit_rejected(self):
        with self.assertRaises(ReviewError):
            validate_commits(self.repo, "0" * 40, self.head)


    def test_inherited_git_environment_is_ignored(self):
        import os
        from unittest.mock import patch

        poisoned = {
            "GIT_DIR": "/nonexistent/poisoned-repository",
            "GIT_WORK_TREE": "/nonexistent/poisoned-worktree",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.repositoryformatversion",
            "GIT_CONFIG_VALUE_0": "-1",
        }
        with patch.dict(os.environ, poisoned):
            validate_commits(self.repo, self.base, self.head)

    def test_forbidden_git_operation_never_executes(self):
        from unittest.mock import patch
        from coding_orchestrator.pr_review import git_read

        with patch(
            "coding_orchestrator.pr_review.subprocess.Popen"
        ) as execute:
            with self.assertRaises(ReviewError):
                git_read(self.repo, "reset", "--hard")
            execute.assert_not_called()


    def test_deleted_file_diff(self):
        from coding_orchestrator.pr_review import collect_diff

        (self.repo / "example.py").unlink()
        self.git("add", "-A")
        self.git("commit", "-qm", "delete file")
        deleted_head = self.git("rev-parse", "HEAD")

        diff = collect_diff(self.repo, self.head, deleted_head)
        self.assertIn("deleted file mode", diff)

    def test_binary_diff_rejected(self):
        from coding_orchestrator.pr_review import collect_diff

        (self.repo / "binary.dat").write_bytes(
            b"binary" + bytes([0]) + b"payload"
        )
        self.git("add", "binary.dat")
        self.git("commit", "-qm", "add binary")
        binary_head = self.git("rev-parse", "HEAD")

        with self.assertRaises(ReviewError):
            collect_diff(self.repo, self.head, binary_head)

    def test_unauthorized_diff_options_rejected(self):
        from unittest.mock import patch
        from coding_orchestrator.pr_review import git_read

        with patch(
            "coding_orchestrator.pr_review.subprocess.Popen"
        ) as execute:
            with self.assertRaises(ReviewError):
                git_read(
                    self.repo,
                    "diff", "--binary", self.base, self.head
                )
            execute.assert_not_called()


    def test_extract_exact_added_line(self):
        from coding_orchestrator.pr_review import (
            collect_diff, extract_added_lines
        )
        diff = collect_diff(self.repo, self.base, self.head)
        self.assertEqual(extract_added_lines(diff), [
            {"path": "example.py", "line": 1, "text": "value = 2"}
        ])

    def test_extract_rejects_unusual_path(self):
        from coding_orchestrator.pr_review import extract_added_lines
        diff = "diff --git a/space name b/space name\\n"
        with self.assertRaises(ReviewError):
            extract_added_lines(diff)

    def test_extract_rejects_malformed_hunk(self):
        from coding_orchestrator.pr_review import extract_added_lines
        diff = (
            "diff --git a/a.py b/a.py\\n"
            "--- a/a.py\\n+++ b/a.py\\n"
            "@@ malformed @@\\n+value = 2\\n"
        )
        with self.assertRaises(ReviewError):
            extract_added_lines(diff)

    def test_extract_rejects_missing_target(self):
        from coding_orchestrator.pr_review import extract_added_lines
        diff = (
            "diff --git a/a.py b/a.py\\n"
            "@@ -1 +1 @@\\n+value = 2\\n"
        )
        with self.assertRaises(ReviewError):
            extract_added_lines(diff)


    def test_rejects_mismatched_diff_paths(self):
        from coding_orchestrator.pr_review import extract_added_lines
        diff = (
            "diff --git a/old.py b/new.py\n"
            "--- a/old.py\n+++ b/new.py\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        )
        with self.assertRaises(ReviewError):
            extract_added_lines(diff)

    def test_rejects_incomplete_hunk(self):
        from coding_orchestrator.pr_review import extract_added_lines
        diff = (
            "diff --git a/a.py b/a.py\n"
            "--- a/a.py\n+++ b/a.py\n"
            "@@ -1 +1,2 @@\n-old\n+new\n"
        )
        with self.assertRaises(ReviewError):
            extract_added_lines(diff)



class FindingValidationTests(unittest.TestCase):
    def setUp(self):
        from coding_orchestrator.pr_review import validate_findings
        self.validate = validate_findings
        self.lines = [
            {"path": "example.py", "line": 7, "text": "return 2"}
        ]
        self.finding = {
            "severity": "major",
            "path": "example.py",
            "line": 7,
            "title": "Unexpected return value",
            "evidence": "return 2",
            "recommendation": "Verify expected behavior",
        }

    def test_valid_finding(self):
        result = self.validate(
            self.lines, {"findings": [self.finding]}
        )
        self.assertEqual(result["finding_count"], 1)
        self.assertEqual(result["status"], "human_review_required")

    def test_forged_evidence_rejected(self):
        bad = dict(self.finding, evidence="return 999")
        with self.assertRaises(ReviewError):
            self.validate(self.lines, {"findings": [bad]})

    def test_forged_location_rejected(self):
        bad = dict(self.finding, line=999)
        with self.assertRaises(ReviewError):
            self.validate(self.lines, {"findings": [bad]})

    def test_invalid_severity_rejected(self):
        bad = dict(self.finding, severity="critical")
        with self.assertRaises(ReviewError):
            self.validate(self.lines, {"findings": [bad]})

    def test_empty_report_never_approves(self):
        result = self.validate(self.lines, {"findings": []})
        self.assertEqual(result["status"], "human_review_required")



class HeaderValidationTests(unittest.TestCase):
    def test_forged_old_file_header(self):
        from coding_orchestrator.pr_review import extract_added_lines

        diff = chr(10).join([
            "diff --git a/a.py b/a.py",
            "--- a/other.py",
            "+++ b/a.py",
            "@@ -1 +1 @@",
            "-old",
            "+new",
            "",
        ])
        with self.assertRaises(ReviewError):
            extract_added_lines(diff)

    def test_missing_old_file_header(self):
        from coding_orchestrator.pr_review import extract_added_lines

        diff = chr(10).join([
            "diff --git a/a.py b/a.py",
            "+++ b/a.py",
            "@@ -1 +1 @@",
            "-old",
            "+new",
            "",
        ])
        with self.assertRaises(ReviewError):
            extract_added_lines(diff)



class AdversarialInputTests(unittest.TestCase):
    def test_unknown_diff_metadata_rejected(self):
        from coding_orchestrator.pr_review import extract_added_lines
        diff = chr(10).join([
            "diff --git a/a.py b/a.py",
            "UNRECOGNIZED METADATA",
            "--- a/a.py", "+++ b/a.py",
            "@@ -1 +1 @@", "-old", "+new", "",
        ])
        with self.assertRaises(ReviewError):
            extract_added_lines(diff)

    def test_malformed_evidence_rows_rejected(self):
        from coding_orchestrator.pr_review import validate_findings
        cases = [
            ["invalid-row"],
            [{"path": [], "line": 1, "text": "new"}],
            [{"path": "a.py", "line": [], "text": "new"}],
        ]
        for rows in cases:
            with self.subTest(rows=rows):
                with self.assertRaises(ReviewError):
                    validate_findings(rows, {"findings": []})


if __name__ == "__main__":
    unittest.main()
