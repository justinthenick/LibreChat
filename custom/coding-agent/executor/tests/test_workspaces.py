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
        with self.assertRaises(ValueError):
            self.manager.run_check(task["task_id"], "sh -c 'echo unsafe'")


if __name__ == "__main__":
    unittest.main()
