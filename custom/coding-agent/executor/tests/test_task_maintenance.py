from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from coding_executor.task_maintenance import (
    _child_environment,
    inventory,
    remove_clean_task,
)


class TaskMaintenanceTest(unittest.TestCase):
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
        (self.repository / ".gitignore").write_text("*.tmp\n", encoding="utf-8")
        (self.repository / "example.txt").write_text("alpha\n", encoding="utf-8")
        self._git("add", ".gitignore", "example.txt")
        self._git("commit", "-m", "initial")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.repository,
            check=True,
            capture_output=True,
            text=True,
        )

    def _worktree(self, task_id: str) -> Path:
        task = self.tasks / task_id
        self._git("worktree", "add", "-b", f"agent/{task_id}", str(task), "main")
        return task

    def test_child_environment_excludes_executor_secrets(self) -> None:
        environment = _child_environment()

        self.assertEqual(
            set(environment),
            {"PATH", "HOME", "CI", "NO_COLOR", "LANG"},
        )
        self.assertNotIn("CODING_EXECUTOR_TOKEN", environment)

    def test_inventory_reports_clean_dirty_and_broken_tasks(self) -> None:
        self._worktree("clean-task")
        dirty = self._worktree("dirty-task")
        (dirty / "example.txt").write_text("changed\n", encoding="utf-8")
        (self.tasks / "broken-task").mkdir()

        result = inventory(self.repositories, self.tasks)
        states = {task["task_id"]: task["state"] for task in result["tasks"]}

        self.assertEqual(states["clean-task"], "clean")
        self.assertEqual(states["dirty-task"], "dirty")
        self.assertEqual(states["broken-task"], "broken")

    def test_inventory_reports_stale_worktree_registration(self) -> None:
        stale = self._worktree("stale-task")
        shutil.rmtree(stale)

        result = inventory(self.repositories, self.tasks)

        self.assertEqual(
            result["stale_registrations"],
            [{"repository": "demo", "task_id": "stale-task"}],
        )

    def test_remove_clean_task_retains_branch(self) -> None:
        task = self._worktree("finished-task")

        result = remove_clean_task(self.repositories, self.tasks, "finished-task")

        self.assertFalse(task.exists())
        self.assertEqual(result["branch_retained"], "agent/finished-task")
        branches = self._git("branch", "--list", "agent/finished-task").stdout
        self.assertIn("agent/finished-task", branches)

    def test_remove_clean_task_rejects_changes(self) -> None:
        task = self._worktree("changed-task")
        (task / "example.txt").write_text("changed\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "tracked or untracked changes"):
            remove_clean_task(self.repositories, self.tasks, "changed-task")

        self.assertTrue(task.exists())

    def test_remove_clean_task_rejects_ignored_files(self) -> None:
        task = self._worktree("ignored-task")
        (task / "build.tmp").write_text("generated\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "ignored files"):
            remove_clean_task(self.repositories, self.tasks, "ignored-task")

        self.assertTrue(task.exists())

    def test_remove_clean_task_rejects_symlink_task_path(self) -> None:
        (self.tasks / "linked-task").symlink_to(self.repository)

        with self.assertRaisesRegex(ValueError, "symbolic link"):
            remove_clean_task(self.repositories, self.tasks, "linked-task")


if __name__ == "__main__":
    unittest.main()
