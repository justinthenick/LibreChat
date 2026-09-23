from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from coding_executor.workspaces import WorkspaceManager


class WorkspaceManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.repositories = root / "repos"
        self.tasks = root / "tasks"
        self.repositories.mkdir()
        self.tasks.mkdir()
        self.repository = self.repositories / "demo"
        self.repository.mkdir()
        self._git("init", "-b", "main")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Executor Test")
        (self.repository / "example.txt").write_text("alpha\nbeta\n", encoding="utf-8")
        self._git("add", "example.txt")
        self._git("commit", "-m", "initial")
        self.manager = WorkspaceManager(self.repositories, self.tasks)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.repository, check=True, capture_output=True, text=True)

    def _setup_upstream(self) -> Path:
        upstream_dir = Path(self.temporary.name) / "upstream.git"
        subprocess.run(["git", "init", "--bare", str(upstream_dir)], check=True, capture_output=True)
        self._git("remote", "add", "origin", str(upstream_dir))
        self._git("push", "-u", "origin", "main")
        return upstream_dir

    def test_create_read_patch_and_diff(self) -> None:
        task = self.manager.create_task("demo", "fix greeting", "main")
        task_id = task["task_id"]
        self.assertEqual(self.manager.read_file(task_id, "example.txt"), "1: alpha\n2: beta")
        result = self.manager.apply_patch(
            task_id,
            "--- a/example.txt\n+++ b/example.txt\n@@ -1,2 +1,2 @@\n alpha\n-beta\n+gamma\n",
        )
        self.assertIn("example.txt", result["status"])
        self.assertIn("+gamma", self.manager.diff(task_id))

    def test_apply_patch_recounts_incorrect_hunk_lengths(self) -> None:
        task = self.manager.create_task("demo", "recount patch", "main")
        task_id = task["task_id"]

        patch = """--- a/example.txt
+++ b/example.txt
@@ -1,2 +1,3 @@
 alpha
-beta
+gamma
"""

        result = self.manager.apply_patch(task_id, patch)

        self.assertIn("example.txt", result["status"])
        self.assertEqual(
            self.manager.read_file(task_id, "example.txt"),
            "1: alpha\n2: gamma",
        )

    def test_diff_includes_untracked_regular_files(self) -> None:
        task = self.manager.create_task("demo", "add notes", "main")
        task_id = task["task_id"]
        self.manager.apply_patch(
            task_id,
            "--- /dev/null\n+++ b/notes.txt\n@@ -0,0 +1,2 @@\n+first\n+second\n",
        )

        complete = self.manager.diff(task_id)

        self.assertIn("new file mode 100644", complete)
        self.assertIn("+++ b/notes.txt", complete)
        self.assertIn("+first", complete)
        self.assertIn("+second", complete)

    def test_diff_rejects_untracked_symbolic_links(self) -> None:
        task = self.manager.create_task("demo", "unsafe untracked", "main")
        (Path(task["path"]) / "unsafe-link").symlink_to("/tmp")

        with self.assertRaises(ValueError):
            self.manager.diff(task["task_id"])

    def test_diff_fails_closed_instead_of_truncating(self) -> None:
        manager = WorkspaceManager(
            self.repositories,
            self.tasks,
            max_output_bytes=32,
        )
        task = manager.create_task("demo", "large diff", "main")
        manager.apply_patch(
            task["task_id"],
            "--- a/example.txt\n+++ b/example.txt\n@@ -1,2 +1,2 @@\n alpha\n-beta\n+replacement-value\n",
        )

        with self.assertRaisesRegex(ValueError, "complete diff exceeds"):
            manager.diff(task["task_id"])

    def test_rejects_path_escape(self) -> None:
        task = self.manager.create_task("demo", "safe path", "main")
        with self.assertRaises(ValueError):
            self.manager.read_file(task["task_id"], "../secret")

    def test_rejects_unsafe_patch(self) -> None:
        task = self.manager.create_task("demo", "safe patch", "main")
        with self.assertRaises(ValueError):
            self.manager.apply_patch(
                task["task_id"],
                "--- a/../../secret\n+++ b/../../secret\n@@ -0,0 +1 @@\n+bad\n",
            )

        with self.assertRaises(ValueError):
            self.manager.apply_patch(
                task["task_id"],
                "--- a/.git\n+++ b/.git\n@@ -1 +1 @@\n-unsafe\n+still-unsafe\n",
            )

    def test_rejects_unsafe_base_ref(self) -> None:
        with self.assertRaises(ValueError):
            self.manager.create_task("demo", "unsafe ref", "--help")

    def test_command_allowlist(self) -> None:
        task = self.manager.create_task("demo", "checks", "main")
        result = self.manager.run_check(task["task_id"], "git diff --check")
        self.assertEqual(result.exit_code, 0)

        unittest_result = self.manager.run_check(
            task["task_id"], "python3 -m unittest --help"
        )
        self.assertEqual(unittest_result.exit_code, 0)

        marker = Path(task["path"]) / "unsafe-marker"
        rejected = self.manager.run_check(
            task["task_id"],
            "sh -c 'touch unsafe-marker'",
        )
        self.assertEqual(rejected.exit_code, 126)
        self.assertIn("command_not_allowed", rejected.stderr)
        self.assertFalse(marker.exists())

    def test_modification_exploration_budget_warns_blocks_and_preserves_completion_tools(self) -> None:
        task = self.manager.create_task("demo", "budgeted modification", "main")
        task_id = task["task_id"]

        self.assertEqual(task["task_mode"], "modification")

        for _ in range(11):
            output = self.manager.read_file(task_id, "example.txt")
            self.assertNotIn("executor_budget_warning", output)

        warning = self.manager.read_file(task_id, "example.txt")
        self.assertIn("executor_budget_warning", warning)
        self.assertIn("remaining=4", warning)

        budget = self.manager.task_status(task_id)["exploration_budget"]
        self.assertEqual(budget["exploration_calls"], 12)
        self.assertEqual(budget["exploration_soft_limit"], 12)
        self.assertEqual(budget["exploration_hard_limit"], 16)
        self.assertEqual(budget["exploration_remaining"], 4)
        self.assertFalse(budget["exploration_exhausted"])

        for _ in range(4):
            self.assertIn(
                "executor_budget_warning",
                self.manager.read_file(task_id, "example.txt"),
            )

        exhausted = self.manager.task_status(task_id)["exploration_budget"]
        self.assertEqual(exhausted["exploration_calls"], 16)
        self.assertEqual(exhausted["exploration_remaining"], 0)
        self.assertTrue(exhausted["exploration_exhausted"])

        with self.assertRaisesRegex(RuntimeError, "exploration_budget_exhausted"):
            self.manager.list_files(task_id)

        patch_status = self.manager.apply_patch(
            task_id,
            "--- a/example.txt\n+++ b/example.txt\n@@ -1,2 +1,2 @@\n alpha\n-beta\n+gamma\n",
        )
        self.assertIn("example.txt", patch_status["status"])
        self.assertEqual(self.manager.run_check(task_id, "git diff --check").exit_code, 0)
        self.assertIn("+gamma", self.manager.diff(task_id))

    def test_read_only_task_has_larger_budget_and_cannot_patch(self) -> None:
        task = self.manager.create_task(
            "demo",
            "read only review",
            "main",
            task_mode="read_only",
        )
        task_id = task["task_id"]

        for _ in range(16):
            self.manager.read_file(task_id, "example.txt")

        budget = self.manager.task_status(task_id)["exploration_budget"]
        self.assertEqual(budget["task_mode"], "read_only")
        self.assertEqual(budget["exploration_calls"], 16)
        self.assertEqual(budget["exploration_soft_limit"], 24)
        self.assertEqual(budget["exploration_hard_limit"], 32)
        self.assertEqual(budget["exploration_remaining"], 16)

        with self.assertRaisesRegex(RuntimeError, "read_only_task"):
            self.manager.apply_patch(
                task_id,
                "--- a/example.txt\n+++ b/example.txt\n@@ -1,2 +1,2 @@\n alpha\n-beta\n+gamma\n",
            )

    def test_create_task_succeeds_when_clean_and_current_with_upstream(self) -> None:
        self._setup_upstream()
        expected_source_commit = subprocess.run(
            ["git", "rev-parse", "main"],
            cwd=self.repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        task = self.manager.create_task("demo", "clean task", "main")

        self.assertTrue(task["task_id"].startswith("clean-task-"))
        self.assertTrue(Path(task["path"]).is_dir())
        self.assertEqual(task["source_repository"], "demo")
        self.assertEqual(task["source_ref"], "main")
        self.assertEqual(task["source_branch"], "main")
        self.assertEqual(task["source_commit"], expected_source_commit)
        self.assertEqual(task["source_status"], "")
        self.assertEqual(task["task_branch"], task["branch"])
        self.assertTrue(task["task_branch"].startswith("agent/clean-task-"))
        source_sync_lock = self.tasks / ".source-sync.lock"
        self.assertTrue(source_sync_lock.is_file())
        self.assertFalse(source_sync_lock.is_symlink())

    def test_create_task_rejects_when_behind_upstream(self) -> None:
        upstream_dir = self._setup_upstream()
        other_repo = Path(self.temporary.name) / "other_clone"
        subprocess.run(["git", "clone", "-b", "main", str(upstream_dir), str(other_repo)], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=other_repo, check=True)
        subprocess.run(["git", "config", "user.name", "Executor Test"], cwd=other_repo, check=True)
        (other_repo / "upstream_change.txt").write_text("remote update\n", encoding="utf-8")
        subprocess.run(["git", "add", "upstream_change.txt"], cwd=other_repo, check=True)
        subprocess.run(["git", "commit", "-m", "upstream commit"], cwd=other_repo, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=other_repo, check=True)

        # Fetch in source repository to update local remote-tracking metadata without merging
        self._git("fetch", "origin")

        with self.assertRaisesRegex(ValueError, "behind its configured upstream"):
            self.manager.create_task("demo", "stale task", "main")

    def test_create_task_rejects_when_source_has_tracked_changes(self) -> None:
        (self.repository / "example.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(
            ValueError,
            r"is not clean \(contains tracked, staged, or untracked changes\)",
        ):
            self.manager.create_task("demo", "dirty task", "main")

    def test_create_task_rejects_when_source_has_staged_changes(self) -> None:
        (self.repository / "staged.txt").write_text("staged\n", encoding="utf-8")
        self._git("add", "staged.txt")
        with self.assertRaisesRegex(
            ValueError,
            r"is not clean \(contains tracked, staged, or untracked changes\)",
        ):
            self.manager.create_task("demo", "staged task", "main")

    def test_create_task_rejects_when_source_has_untracked_files(self) -> None:
        (self.repository / "untracked.txt").write_text("untracked\n", encoding="utf-8")
        with self.assertRaisesRegex(
            ValueError,
            r"is not clean \(contains tracked, staged, or untracked changes\)",
        ):
            self.manager.create_task("demo", "untracked task", "main")

    def test_create_task_succeeds_when_source_has_no_configured_upstream(self) -> None:
        task = self.manager.create_task("demo", "no upstream task", "main")
        self.assertTrue(task["task_id"].startswith("no-upstream-task-"))
        self.assertTrue(Path(task["path"]).is_dir())


if __name__ == "__main__":
    unittest.main()
