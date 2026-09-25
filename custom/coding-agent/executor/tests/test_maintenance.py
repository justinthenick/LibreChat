from __future__ import annotations

import json
import os
import subprocess
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_executor.bounded import run
from coding_executor.coordination import coordinated, maintenance_lock
from coding_executor.maintenance import INDEX_SCAN_LIMIT, fresh_repository_status, git, inventory, refresh, remove_task, repository_status, task_snapshot
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

    def test_status_reports_cached_ahead_behind_divergence_and_missing_upstream(self):
        self.assertIsNone(repository_status(self.repos, "demo", "main")["ahead"])
        self.command(self.repo, "remote", "add", "origin", "https://github.com/example/demo.git")
        self.command(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        self.command(self.repo, "branch", "--set-upstream-to=origin/main", "main")
        self.command(self.repo, "commit", "--allow-empty", "-m", "ahead")
        status = repository_status(self.repos, "demo", "main")
        self.assertEqual((status["ahead"], status["behind"], status["diverged"]), (1, 0, False))
        self.command(self.repo, "checkout", "--detach", "HEAD~1")
        self.command(self.repo, "commit", "--allow-empty", "-m", "upstream")
        self.command(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        self.command(self.repo, "checkout", "main")
        status = repository_status(self.repos, "demo", "main")
        self.assertEqual((status["ahead"], status["behind"], status["diverged"]), (1, 1, True))
        self.assertEqual(status["freshness"], "not_fetched")

    def test_version_inspection_does_not_acquire_worktree_lock(self):
        from coding_executor import __version__
        with maintenance_lock(self.tasks, exclusive=True):
            result = subprocess.run([sys.executable, "-B", "-m", "coding_executor.maintenance", "health"],
                                    capture_output=True, text=True, check=True,
                                    env={**os.environ, "CODING_REPOSITORY_ROOT": str(self.repos),
                                         "CODING_TASK_ROOT": str(self.tasks)})
        self.assertEqual(json.loads(result.stdout), {"version": __version__})

    def test_inventory_reports_clean_dirty_and_stale_without_pruning(self):
        clean, dirty, stale = self.task(), self.task(), self.task()
        (self.tasks / dirty / "untracked").write_text("retain")
        shutil.rmtree(self.tasks / stale)
        result = inventory(self.repos, self.tasks)
        states = {item["task_id"]: item["state"] for item in result["tasks"]}
        self.assertEqual(states, {clean: "clean", dirty: "dirty"})
        self.assertEqual(result["stale_registrations"][0]["task_id"], stale)
        self.assertFalse(result["automatically_pruned"])
        self.assertIn(stale, self.command(self.repo, "worktree", "list", "--porcelain"))

    def fresh_fixture(self):
        remote = self.root / "upstream.git"
        self.command(self.root, "clone", "--bare", str(self.repo), str(remote))
        url = "https://github.com/example/demo.git"
        self.command(self.repo, "remote", "add", "origin", url)
        self.command(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        self.command(self.repo, "branch", "--set-upstream-to=origin/main", "main")
        self.command(remote, "config", "user.email", "test@example.invalid")
        self.command(remote, "config", "user.name", "Test")
        commit = self.command(remote, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "remote advance").strip()
        self.command(remote, "update-ref", "refs/heads/main", commit)
        original_git = git
        def transport(path, *args):
            if "fetch" in args:
                args = tuple(str(remote) if arg == url else arg for arg in args)
                return original_git(path, "-c", "protocol.file.allow=always", *args)
            return original_git(path, *args)
        return url, commit, transport

    def test_fresh_fetch_reports_remote_without_modifying_source_or_cached_upstream(self):
        url, commit, transport = self.fresh_fixture()
        head = self.command(self.repo, "rev-parse", "HEAD").strip()
        index = (self.repo / ".git/index").read_bytes()
        (self.repo / ".git/FETCH_HEAD").write_text("previous fetch marker\n")
        with patch("coding_executor.maintenance.git", side_effect=transport):
            result = fresh_repository_status(self.repos, "demo", "main", url)
        self.assertTrue(result["ok"], result)
        self.assertEqual((result["upstream_sha"], result["ahead"], result["behind"]), (commit, 0, 1))
        self.assertEqual(result["comparison_basis"], "fresh_remote_ref")
        self.assertEqual(result["fetch_result"], "success")
        self.assertIsNotNone(result["fetched_at"])
        self.assertEqual(self.command(self.repo, "rev-parse", "HEAD").strip(), head)
        self.assertEqual(self.command(self.repo, "rev-parse", "origin/main").strip(), head)
        self.assertEqual((self.repo / ".git/index").read_bytes(), index)
        self.assertEqual((self.repo / ".git/FETCH_HEAD").read_text(), "previous fetch marker\n")
        self.assertEqual((self.repo / "file").read_text(), "initial\n")
        self.assertEqual(repository_status(self.repos, "demo", "main")["freshness"], "not_fetched")

    def test_fresh_fetch_reports_divergence_and_never_falls_back_after_fetch_error(self):
        url, commit, transport = self.fresh_fixture()
        self.command(self.repo, "commit", "--allow-empty", "-m", "local advance")
        with patch("coding_executor.maintenance.git", side_effect=transport):
            result = fresh_repository_status(self.repos, "demo", "main", url)
        self.assertEqual((result["ahead"], result["behind"], result["diverged"]), (1, 1, True))
        def failed_fetch(path, *args):
            if "fetch" in args:
                raise RuntimeError("network failed")
            return transport(path, *args)
        with patch("coding_executor.maintenance.git", side_effect=failed_fetch):
            result = fresh_repository_status(self.repos, "demo", "main", url)
        self.assertFalse(result["ok"])
        self.assertEqual(result["fetch_result"], "fetch_or_comparison_failed")
        self.assertNotIn("upstream_sha", result)
        self.assertIsNone(result["fetched_at"])

    def test_fresh_status_refuses_dirty_detached_wrong_upstream_and_url_rewrite(self):
        url, _, _ = self.fresh_fixture()
        (self.repo / "untracked").write_text("retain")
        self.assertFalse(fresh_repository_status(self.repos, "demo", "main", url)["ok"])
        (self.repo / "untracked").unlink()
        self.command(self.repo, "checkout", "--detach")
        self.assertFalse(fresh_repository_status(self.repos, "demo", "main", url)["ok"])
        self.command(self.repo, "checkout", "main")
        self.command(self.repo, "branch", "--unset-upstream")
        self.assertFalse(fresh_repository_status(self.repos, "demo", "main", url)["ok"])
        self.command(self.repo, "branch", "--set-upstream-to=origin/main", "main")
        self.command(self.repo, "config", "url.https://evil.invalid/.insteadOf", "https://github.com/")
        self.assertEqual(fresh_repository_status(self.repos, "demo", "main", url)["fetch_result"], "refused_remote_identity")

    def test_snapshot_checks_staged_untracked_ignored_and_git_locks(self):
        task = self.task()
        path = self.tasks / task
        self.assertTrue(all(task_snapshot(self.repos, self.tasks, task)["checks"].values()))
        (path / "file").write_text("staged change")
        self.command(path, "add", "file")
        snapshot = task_snapshot(self.repos, self.tasks, task)
        self.assertFalse(snapshot["checks"]["tracked_clean"])
        self.assertFalse(snapshot["checks"]["index_clean"])
        (path / "extra").write_text("untracked")
        (path / "keep.ignored").write_text("ignored")
        snapshot = task_snapshot(self.repos, self.tasks, task)
        self.assertFalse(snapshot["checks"]["no_untracked"])
        self.assertFalse(snapshot["checks"]["no_ignored"])
        admin = Path(self.command(path, "rev-parse", "--absolute-git-dir").strip())
        (admin / "index.lock").touch()
        with self.assertRaisesRegex(ValueError, "active Git lock"):
            task_snapshot(self.repos, self.tasks, task)

    def test_large_index_scan_uses_a_larger_bounded_output_limit(self):
        task = self.task()
        large_clean_index = "".join(f"H tracked-{index:05d}.txt\0" for index in range(6000))
        self.assertGreater(len(large_clean_index.encode()), 65536)
        observed_limits = []
        original_run = run

        def traced(argv, **kwargs):
            if "ls-files" in argv:
                observed_limits.append(kwargs.get("limit"))
                self.assertGreaterEqual(kwargs.get("limit", 0), len(large_clean_index.encode()))
                return large_clean_index
            return original_run(argv, **kwargs)

        with patch("coding_executor.maintenance.run", side_effect=traced):
            snapshot = task_snapshot(self.repos, self.tasks, task)

        self.assertFalse(snapshot["dirty"])
        self.assertTrue(snapshot["checks"]["no_hidden_index_flags"])
        self.assertEqual(observed_limits, [INDEX_SCAN_LIMIT])
        self.assertGreater(INDEX_SCAN_LIMIT, 65536)

    def test_hidden_index_flags_are_dirty_and_cleanup_rechecks_them(self):
        for flag in ("--assume-unchanged", "--skip-worktree"):
            with self.subTest(flag=flag):
                task = self.task()
                path = self.tasks / task
                fingerprint = task_snapshot(self.repos, self.tasks, task)["fingerprint"]
                self.command(path, "update-index", flag, "file")
                (path / "file").write_text("hidden local change\n")
                self.assertEqual(self.command(path, "status", "--porcelain=v1", "--untracked-files=all"), "")
                snapshot = task_snapshot(self.repos, self.tasks, task)
                self.assertTrue(snapshot["dirty"])
                self.assertEqual(snapshot["state"], "dirty")
                self.assertFalse(snapshot["checks"]["no_hidden_index_flags"])
                with self.assertRaises(ValueError):
                    remove_task(self.repos, self.tasks, task, fingerprint)
                self.assertTrue((path / "file").exists())
                self.assertEqual((path / "file").read_text(), "hidden local change\n")

    def test_clean_worktree_with_unfinished_git_operation_is_refused(self):
        task = self.task()
        path = self.tasks / task
        admin = Path(self.command(path, "rev-parse", "--absolute-git-dir").strip())
        for marker in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-apply", "rebase-merge", "sequencer", "BISECT_LOG"):
            with self.subTest(marker=marker):
                (admin / marker).touch()
                with self.assertRaisesRegex(ValueError, "unfinished Git operation"):
                    task_snapshot(self.repos, self.tasks, task)
                (admin / marker).unlink()

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
