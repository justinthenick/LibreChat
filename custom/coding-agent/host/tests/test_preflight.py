from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from unittest.mock import patch
from source_preflight.cli import main as cli_main
from source_preflight.preflight import _build_git_env, _run_git, refresh_preflight


class SourcePreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

        # Bare upstream remote repository
        self.upstream_dir = self.root / "upstream.git"
        subprocess.run(["git", "init", "--bare", str(self.upstream_dir)], check=True, capture_output=True)

        # Initial local repository cloned/pushed
        self.repo_dir = self.root / "local_repo"
        self.repo_dir.mkdir()
        self._git(self.repo_dir, "init", "-b", "main")
        self._git(self.repo_dir, "config", "user.email", "preflight-test@example.invalid")
        self._git(self.repo_dir, "config", "user.name", "Preflight Test")
        (self.repo_dir / "README.md").write_text("initial content\n", encoding="utf-8")
        self._git(self.repo_dir, "add", "README.md")
        self._git(self.repo_dir, "commit", "-m", "initial commit")
        self._git(self.repo_dir, "remote", "add", "origin", str(self.upstream_dir))
        self._git(self.repo_dir, "push", "-u", "origin", "main")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )

    def _create_upstream_commit(self, filename: str, content: str, message: str) -> str:
        other_clone = self.root / "other_clone"
        if not other_clone.exists():
            subprocess.run(["git", "clone", "-b", "main", str(self.upstream_dir), str(other_clone)], check=True, capture_output=True)
            self._git(other_clone, "config", "user.email", "upstream@example.invalid")
            self._git(other_clone, "config", "user.name", "Upstream User")
        else:
            self._git(other_clone, "pull", "origin", "main")

        (other_clone / filename).write_text(content, encoding="utf-8")
        self._git(other_clone, "add", filename)
        self._git(other_clone, "commit", "-m", message)
        self._git(other_clone, "push", "origin", "main")
        return self._git(other_clone, "rev-parse", "HEAD").stdout.strip()

    def test_clean_and_already_current(self) -> None:
        head_before = self._git(self.repo_dir, "rev-parse", "HEAD").stdout.strip()
        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.branch, "main")
        self.assertEqual(result.upstream, "origin/main")
        self.assertEqual(result.sha_before, head_before)
        self.assertEqual(result.fetched_upstream_sha, head_before)
        self.assertEqual(result.sha_after, head_before)
        self.assertEqual(result.ahead_count, 0)
        self.assertEqual(result.behind_count, 0)
        self.assertFalse(result.fast_forwarded)
        self.assertIn("up to date", result.reason)

    def test_clean_and_one_commit_behind(self) -> None:
        head_before = self._git(self.repo_dir, "rev-parse", "HEAD").stdout.strip()
        upstream_sha = self._create_upstream_commit("feature.txt", "feature-content\n", "upstream feature")

        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.branch, "main")
        self.assertEqual(result.upstream, "origin/main")
        self.assertEqual(result.sha_before, head_before)
        self.assertEqual(result.fetched_upstream_sha, upstream_sha)
        self.assertEqual(result.sha_after, upstream_sha)
        self.assertEqual(result.ahead_count, 0)
        self.assertEqual(result.behind_count, 1)
        self.assertTrue(result.fast_forwarded)
        self.assertIn("fast-forwarded 1 commit", result.reason)

        # Verify file exists locally after ff
        self.assertEqual((self.repo_dir / "feature.txt").read_text(encoding="utf-8"), "feature-content\n")
        # Verify working directory is clean
        status = self._git(self.repo_dir, "status", "--porcelain").stdout.strip()
        self.assertEqual(status, "")

    def test_clean_and_multiple_commits_behind(self) -> None:
        self._create_upstream_commit("file1.txt", "1\n", "first")
        upstream_sha = self._create_upstream_commit("file2.txt", "2\n", "second")

        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.sha_after, upstream_sha)
        self.assertEqual(result.behind_count, 2)
        self.assertTrue(result.fast_forwarded)
        self.assertIn("fast-forwarded 2 commits", result.reason)

    def test_tracked_dirty(self) -> None:
        (self.repo_dir / "README.md").write_text("modified tracked content\n", encoding="utf-8")
        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("tracked, staged, or untracked changes", result.reason)

    def test_staged_dirty(self) -> None:
        (self.repo_dir / "staged.txt").write_text("staged content\n", encoding="utf-8")
        self._git(self.repo_dir, "add", "staged.txt")
        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("tracked, staged, or untracked changes", result.reason)

    def test_untracked_dirty(self) -> None:
        (self.repo_dir / "untracked.txt").write_text("untracked content\n", encoding="utf-8")
        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("tracked, staged, or untracked changes", result.reason)

    def test_local_ahead(self) -> None:
        (self.repo_dir / "local.txt").write_text("local only\n", encoding="utf-8")
        self._git(self.repo_dir, "add", "local.txt")
        self._git(self.repo_dir, "commit", "-m", "local commit")

        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.ahead_count, 1)
        self.assertEqual(result.behind_count, 0)
        self.assertIn("ahead of upstream", result.reason)
        self.assertIn("refusing to push or rewrite", result.reason)

    def test_diverged(self) -> None:
        # Local commit
        (self.repo_dir / "local.txt").write_text("local\n", encoding="utf-8")
        self._git(self.repo_dir, "add", "local.txt")
        self._git(self.repo_dir, "commit", "-m", "local change")

        # Upstream commit
        self._create_upstream_commit("remote.txt", "remote\n", "remote change")

        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.ahead_count, 1)
        self.assertEqual(result.behind_count, 1)
        self.assertIn("diverged from upstream", result.reason)

    def test_missing_upstream(self) -> None:
        self._git(self.repo_dir, "checkout", "-b", "local-branch-no-upstream")
        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("has no configured upstream tracking branch", result.reason)

    def test_mismatched_upstream(self) -> None:
        # Expected upstream origin/develop does not match actual origin/main
        result = refresh_preflight(self.repo_dir, expected_upstream="origin/develop")

        self.assertEqual(result.status, "FAIL")
        self.assertIn("does not match expected upstream 'origin/develop'", result.reason)

    def test_explicit_matching_expected_upstream(self) -> None:
        result = refresh_preflight(self.repo_dir, expected_upstream="origin/main")

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.upstream, "origin/main")
        self.assertFalse(result.fast_forwarded)

    def test_detached_head(self) -> None:
        head_sha = self._git(self.repo_dir, "rev-parse", "HEAD").stdout.strip()
        self._git(self.repo_dir, "checkout", head_sha)
        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("detached HEAD is not supported", result.reason)

    def test_fetch_failure(self) -> None:
        # Point remote to non-existent location
        self._git(self.repo_dir, "remote", "set-url", "origin", "/nonexistent/path.git")
        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("fetch failed", result.reason)

    def test_non_git_target(self) -> None:
        not_git = self.root / "not_git"
        not_git.mkdir()
        result = refresh_preflight(not_git)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("not a valid Git working tree", result.reason)

    def test_subdirectory_target_rejected(self) -> None:
        sub_dir = self.repo_dir / "subdir"
        sub_dir.mkdir()
        result = refresh_preflight(sub_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("is a subdirectory of", result.reason)
        self.assertIn("not the repository root", result.reason)

    def test_fetch_timeout_produces_structured_fail(self) -> None:
        head_before = self._git(self.repo_dir, "rev-parse", "HEAD").stdout.strip()
        self._create_upstream_commit("remote.txt", "remote\n", "remote update")

        real_run = _run_git

        def mock_run_git(cwd: Path, args: list[str], **kwargs):
            if len(args) >= 2 and args[0] == "fetch" and args[1] == "--prune":
                return subprocess.CompletedProcess(
                    args=["git", *args],
                    returncode=124,
                    stdout="",
                    stderr="command timed out after 60 seconds: git fetch --prune origin",
                )
            return real_run(cwd, args, **kwargs)

        with patch("source_preflight.preflight._run_git", side_effect=mock_run_git):
            result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("fetch failed", result.reason)
        self.assertIn("timed out", result.reason)
        self.assertFalse(result.fast_forwarded)
        head_after = self._git(self.repo_dir, "rev-parse", "HEAD").stdout.strip()
        self.assertEqual(head_before, head_after)

    def test_status_command_failure_produces_accurate_reason(self) -> None:
        real_run = _run_git

        def mock_run_git(cwd: Path, args: list[str], **kwargs):
            if len(args) >= 2 and args[0] == "status" and args[1].startswith("--porcelain"):
                return subprocess.CompletedProcess(
                    args=["git", *args],
                    returncode=128,
                    stdout="",
                    stderr="fatal: internal git error during status",
                )
            return real_run(cwd, args, **kwargs)

        with patch("source_preflight.preflight._run_git", side_effect=mock_run_git):
            result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("failed to check working tree status", result.reason)
        self.assertIn("fatal: internal git error during status", result.reason)
        self.assertNotIn("source repository contains tracked, staged, or untracked changes", result.reason)

    def test_trusted_host_environment_preserved_and_redirection_stripped(self) -> None:
        saved_env = dict(os.environ)
        try:
            os.environ["HOME"] = "/home/testuser"
            os.environ["SSH_AUTH_SOCK"] = "/run/user/1000/ssh.socket"
            os.environ["GIT_DIR"] = "/tmp/bad-git-dir"
            os.environ["GIT_WORK_TREE"] = "/tmp/bad-worktree"
            os.environ["GIT_COMMON_DIR"] = "/tmp/bad-common-dir"

            override = {
                "GIT_DIR": "/override/bad-git-dir",
                "GIT_WORK_TREE": "/override/bad-worktree",
                "CUSTOM_TEST_VAR": "preserved",
            }
            env = _build_git_env(override)
            self.assertEqual(env.get("HOME"), "/home/testuser")
            self.assertEqual(env.get("SSH_AUTH_SOCK"), "/run/user/1000/ssh.socket")
            self.assertEqual(env.get("GIT_TERMINAL_PROMPT"), "0")
            self.assertEqual(env.get("NO_COLOR"), "1")
            self.assertEqual(env.get("CUSTOM_TEST_VAR"), "preserved")
            self.assertNotIn("GIT_DIR", env)
            self.assertNotIn("GIT_WORK_TREE", env)
            self.assertNotIn("GIT_COMMON_DIR", env)
        finally:
            os.environ.clear()
            os.environ.update(saved_env)

    def test_confirm_no_destructive_git_operation_needed(self) -> None:
        # Verify that uncommitted work on dirty branches is NEVER lost or reset
        (self.repo_dir / "sensitive.txt").write_text("important user work\n", encoding="utf-8")
        result = refresh_preflight(self.repo_dir)

        self.assertEqual(result.status, "FAIL")
        # The dirty file is untouched and preserved
        self.assertTrue((self.repo_dir / "sensitive.txt").exists())
        self.assertEqual((self.repo_dir / "sensitive.txt").read_text(encoding="utf-8"), "important user work\n")

    def test_cli_human_and_json_modes(self) -> None:
        # Human readable mode
        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            code = cli_main([str(self.repo_dir), "--expected-upstream", "origin/main"])
        self.assertEqual(code, 0)
        human_out = stdout_buf.getvalue()
        self.assertIn("Status:           PASS", human_out)
        self.assertIn("Branch:           main", human_out)
        self.assertIn("Fast-Forwarded:   no", human_out)

        # JSON mode
        stdout_buf_json = io.StringIO()
        with redirect_stdout(stdout_buf_json):
            code = cli_main([str(self.repo_dir), "--expected-upstream", "origin/main", "--json"])
        self.assertEqual(code, 0)
        parsed = json.loads(stdout_buf_json.getvalue())
        self.assertEqual(parsed["status"], "PASS")
        self.assertEqual(parsed["branch"], "main")
        self.assertEqual(parsed["upstream"], "origin/main")
        self.assertFalse(parsed["fast_forwarded"])

        # CLI expected-upstream mismatch
        stdout_buf_mismatch = io.StringIO()
        with redirect_stdout(stdout_buf_mismatch):
            code = cli_main([str(self.repo_dir), "--expected-upstream", "origin/wrong", "--json"])
        self.assertEqual(code, 1)
        parsed_mismatch = json.loads(stdout_buf_mismatch.getvalue())
        self.assertEqual(parsed_mismatch["status"], "FAIL")

        # CLI failure returns non-zero
        (self.repo_dir / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        stdout_buf_fail = io.StringIO()
        with redirect_stdout(stdout_buf_fail):
            code = cli_main([str(self.repo_dir), "--json"])
        self.assertEqual(code, 1)
        parsed_fail = json.loads(stdout_buf_fail.getvalue())
        self.assertEqual(parsed_fail["status"], "FAIL")
        self.assertIn("tracked, staged, or untracked", parsed_fail["reason"])


if __name__ == "__main__":
    unittest.main()
