from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_executor.bounded import run
from coding_executor.coordination import coordinated, maintenance_lock
from coding_executor.maintenance import git, refresh, remove_task, repository_status, task_snapshot
from coding_executor.workspaces import WorkspaceManager


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repos = self.root / "repos"
        self.tasks = self.root / "tasks"
        self.repo = self.repos / "demo"
        self.repo.mkdir(parents=True)
        self.tasks.mkdir()
        self.command(self.repo, "init", "-b", "main")
        self.command(self.repo, "config", "user.email", "test@example.invalid")
        self.command(self.repo, "config", "user.name", "Test")
        (self.repo / "file").write_text("initial\n")
        (self.repo / ".gitignore").write_text("*.ignored\n")
        self.command(self.repo, "add", ".")
        self.command(self.repo, "commit", "-m", "initial")
        self.manager = WorkspaceManager(self.repos, self.tasks)

    def tearDown(self):
        self.temp.cleanup()

    def command(self, path, *args):
        return subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True).stdout

    def task(self, mode="modification"):
        return self.manager.create_task("demo", "test", "main", mode)["task_id"]

    def test_cleanup_retains_branch_and_rejects_replay(self):
        task = self.task()
        snapshot = task_snapshot(self.repos, self.tasks, task)
        result = remove_task(self.repos, self.tasks, task, snapshot["fingerprint"])
        self.assertFalse((self.tasks / task).exists())
        self.assertEqual(result["branch_retained"], f"agent/{task}")
        self.assertIn(f"agent/{task}", self.command(self.repo, "branch", "--list"))
        with self.assertRaises(ValueError):
            remove_task(self.repos, self.tasks, task, snapshot["fingerprint"])

    def test_cleanup_rechecks_tracked_untracked_and_ignored_changes(self):
        for filename in ("file", "new-file", "build.ignored"):
            with self.subTest(filename=filename):
                task = self.task()
                fingerprint = task_snapshot(self.repos, self.tasks, task)["fingerprint"]
                (self.tasks / task / filename).write_text("keep this work\n")
                with self.assertRaises(ValueError):
                    remove_task(self.repos, self.tasks, task, fingerprint)
                self.assertTrue((self.tasks / task / filename).exists())

    def test_cleanup_refuses_changed_head_locked_release_and_detached_worktrees(self):
        task = self.task()
        fingerprint = task_snapshot(self.repos, self.tasks, task)["fingerprint"]
        self.command(self.tasks / task, "commit", "--allow-empty", "-m", "new head")
        with self.assertRaises(ValueError):
            remove_task(self.repos, self.tasks, task, fingerprint)
        self.command(self.repo, "worktree", "lock", str(self.tasks / task))
        with self.assertRaises(ValueError):
            task_snapshot(self.repos, self.tasks, task)
        self.command(self.repo, "worktree", "unlock", str(self.tasks / task))
        self.command(self.tasks / task, "checkout", "-b", "release/keep")
        with self.assertRaises(ValueError):
            task_snapshot(self.repos, self.tasks, task)
        self.command(self.tasks / task, "checkout", "--detach")
        with self.assertRaises(ValueError):
            task_snapshot(self.repos, self.tasks, task)

    def test_traversal_symlinks_and_wrong_repository_are_rejected(self):
        task = self.task()
        (self.tasks / "linked").symlink_to(self.tasks / task)
        for name in ("../repo", "--help", "linked", "task;id", "/tmp"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                task_snapshot(self.repos, self.tasks, name)
        with self.assertRaises(ValueError):
            task_snapshot(self.root, self.tasks, task)

    def test_shared_operations_block_exclusive_maintenance_and_vice_versa(self):
        @coordinated(self.tasks)
        def call():
            return True
        with maintenance_lock(self.tasks):
            self.assertTrue(call())
            with self.assertRaisesRegex(RuntimeError, "executor_busy"):
                with maintenance_lock(self.tasks, exclusive=True):
                    self.fail("exclusive lock acquired")
        with maintenance_lock(self.tasks, exclusive=True):
            with self.assertRaisesRegex(RuntimeError, "executor_busy"):
                call()

    def test_lock_symlink_is_rejected(self):
        (self.tasks / ".maintenance.lock").symlink_to(self.repo / "file")
        with self.assertRaises(OSError):
            with maintenance_lock(self.tasks):
                self.fail("symlink accepted")

    def test_restart_preserves_mode_and_budget_and_fails_closed_without_state(self):
        task = self.task("read_only")
        self.manager.read_file(task, "file")
        restarted = WorkspaceManager(self.repos, self.tasks)
        budget = restarted.task_status(task)["exploration_budget"]
        self.assertEqual(budget["task_mode"], "read_only")
        self.assertEqual(budget["exploration_calls"], 1)
        with self.assertRaisesRegex(RuntimeError, "read_only"):
            restarted.apply_patch(task, "anything")
        (self.tasks / f".state-{task}.json").unlink()
        legacy = WorkspaceManager(self.repos, self.tasks)
        self.assertTrue(legacy.task_status(task)["exploration_budget"]["exploration_exhausted"])
        with self.assertRaisesRegex(RuntimeError, "read_only"):
            legacy.apply_patch(task, "anything")

    def test_persisted_modification_budget_cannot_reset_on_restart(self):
        task = self.task()
        for _ in range(16):
            self.manager.read_file(task, "file")
        restarted = WorkspaceManager(self.repos, self.tasks)
        with self.assertRaisesRegex(RuntimeError, "exploration_budget_exhausted"):
            restarted.read_file(task, "file")

    def test_corrupt_or_fifo_state_fails_closed_without_blocking(self):
        task = self.task()
        state = self.tasks / f".state-{task}.json"
        state.write_text('{"mode": "modification", "calls": -1}')
        self.assertEqual(WorkspaceManager(self.repos, self.tasks)._task_mode(task), "read_only")
        state.unlink()
        os.mkfifo(state)
        self.assertEqual(WorkspaceManager(self.repos, self.tasks)._task_mode(task), "read_only")

    def test_check_reaps_background_descendants_before_releasing_gate(self):
        task = self.task()
        path = self.tasks / task
        (path / "test_background.py").write_text(
            "import subprocess, sys, unittest\n"
            "class Background(unittest.TestCase):\n"
            " def test_child(self):\n"
            "  subprocess.Popen([sys.executable, '-c', \"import time; from pathlib import Path; time.sleep(1); Path('leaked').write_text('bad')\"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
        self.assertEqual(self.manager.run_check(task, "python3 -m unittest test_background").exit_code, 0)
        time.sleep(1.2)
        self.assertFalse((path / "leaked").exists())

    def test_runner_bounds_output_time_and_does_not_return_stderr_secrets(self):
        with self.assertRaisesRegex(RuntimeError, "output limit"):
            run(["python3", "-c", "print('x'*10000)"], limit=100)
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            run(["python3", "-c", "import time; time.sleep(10)"], timeout=1)
        with self.assertRaisesRegex(RuntimeError, "command failed") as error:
            run(["python3", "-c", "import sys; print('SECRET'); sys.exit(1)"])
        self.assertNotIn("SECRET", str(error.exception))

    def test_refresh_fast_forward_dirty_diverged_and_detached(self):
        remote = self.root / "upstream.git"
        self.command(self.root, "clone", "--bare", str(self.repo), str(remote))
        self.command(self.repo, "remote", "add", "origin", str(remote))
        self.command(self.repo, "fetch", "origin")
        self.command(self.repo, "branch", "--set-upstream-to", "origin/main")
        other = self.root / "other"
        self.command(self.root, "clone", str(remote), str(other))
        self.command(other, "config", "user.email", "test@example.invalid")
        self.command(other, "config", "user.name", "Test")
        (other / "new").write_text("upstream\n")
        self.command(other, "add", ".")
        self.command(other, "commit", "-m", "update")
        self.command(other, "push")

        def local_transport(path, *args):
            if args[0] == "fetch":
                return self.command(path, "fetch", "--no-tags", str(remote), "refs/heads/main")
            return git(path, *args)

        with patch("coding_executor.maintenance.git", side_effect=local_transport):
            result = refresh(self.repos, "demo", "main", "https://github.com/example/demo.git")
            self.assertTrue(result["fast_forwarded"])
            self.assertTrue((self.repo / "new").exists())
            self.assertFalse(refresh(self.repos, "demo", "main", "https://github.com/example/demo.git")["fast_forwarded"])
            (other / "build.ignored").write_text("tracked upstream\n")
            self.command(other, "add", "--force", "build.ignored")
            self.command(other, "commit", "-m", "tracked ignored name")
            self.command(other, "push")
            (self.repo / "build.ignored").write_text("preserve local ignored data\n")
            head_before = self.command(self.repo, "rev-parse", "HEAD")
            with self.assertRaises(RuntimeError):
                refresh(self.repos, "demo", "main", "https://github.com/example/demo.git")
            self.assertEqual(self.command(self.repo, "rev-parse", "HEAD"), head_before)
            self.assertEqual((self.repo / "build.ignored").read_text(), "preserve local ignored data\n")
            (self.repo / "build.ignored").unlink()
            refresh(self.repos, "demo", "main", "https://github.com/example/demo.git")
            (self.repo / "dirty").write_text("keep\n")
            with self.assertRaises(ValueError):
                refresh(self.repos, "demo", "main", "https://github.com/example/demo.git")
            (self.repo / "dirty").unlink()
            self.command(self.repo, "commit", "--allow-empty", "-m", "local")
            with self.assertRaisesRegex(ValueError, "ahead or diverged"):
                refresh(self.repos, "demo", "main", "https://github.com/example/demo.git")
            self.command(other, "commit", "--allow-empty", "-m", "remote")
            self.command(other, "push")
            with self.assertRaisesRegex(ValueError, "ahead or diverged"):
                refresh(self.repos, "demo", "main", "https://github.com/example/demo.git")
            self.command(self.repo, "checkout", "--detach")
            with self.assertRaises(ValueError):
                refresh(self.repos, "demo", "main", "https://github.com/example/demo.git")

    def test_status_does_not_claim_freshness_and_invalid_fetch_sources_are_rejected(self):
        self.assertEqual(repository_status(self.repos, "demo", "main")["freshness"], "not_fetched")
        for url in ("file:///tmp/repo", "https://user:secret@github.com/example/demo.git", "https://evil.invalid/repo.git"):
            with self.assertRaises(ValueError):
                refresh(self.repos, "demo", "main", url)
