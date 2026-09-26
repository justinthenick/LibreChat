from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WORKSPACES_PATH = (
    Path(__file__).resolve().parent.parent / "src" / "coding_executor" / "workspaces.py"
).resolve()
WORKSPACES_SPEC = importlib.util.spec_from_file_location(
    "task_local_coding_executor_workspaces",
    WORKSPACES_PATH,
)
if WORKSPACES_SPEC is None or WORKSPACES_SPEC.loader is None:
    raise RuntimeError("could not load task-local workspaces.py")
workspaces_module = importlib.util.module_from_spec(WORKSPACES_SPEC)
sys.modules[WORKSPACES_SPEC.name] = workspaces_module
WORKSPACES_SPEC.loader.exec_module(workspaces_module)

WorkspaceManager = workspaces_module.WorkspaceManager
MODIFICATION_EXPLORATION_HARD_LIMIT = workspaces_module.MODIFICATION_EXPLORATION_HARD_LIMIT


class WorkspaceManagerTest(unittest.TestCase):
    def test_loaded_module_is_task_local(self) -> None:
        self.assertEqual(Path(workspaces_module.__file__).resolve(), WORKSPACES_PATH)

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
        (self.repository / "clean.txt").write_text("clean\n", encoding="utf-8")
        self._git("add", "example.txt", "clean.txt")
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

    def _exhaust_modification(self, manager: WorkspaceManager, task_id: str) -> str:
        warning = ""
        for _ in range(MODIFICATION_EXPLORATION_HARD_LIMIT):
            warning = manager.read_file(task_id, "example.txt")
        return warning

    def _state_path(self, task_id: str) -> Path:
        return self.tasks / f".state-{task_id}.json"

    @staticmethod
    def _example_patch(old: str, new: str) -> str:
        return (
            "--- a/example.txt\n"
            "+++ b/example.txt\n"
            "@@ -1,2 +1,2 @@\n"
            " alpha\n"
            f"-{old}\n"
            f"+{new}\n"
        )

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

    def test_modification_exhaustion_message_reports_restricted_mutation_scope(self) -> None:
        task = self.manager.create_task("demo", "budgeted modification", "main")
        task_id = task["task_id"]

        warning = self._exhaust_modification(self.manager, task_id)
        self.assertIn("executor_budget_warning", warning)
        self.assertIn("remaining=0", warning)
        self.assertIn("apply_patch is restricted to paths", warning)
        self.assertIn("already dirty or untracked", warning)

        exhausted = self.manager.task_status(task_id)["exploration_budget"]
        self.assertEqual(exhausted["exploration_calls"], MODIFICATION_EXPLORATION_HARD_LIMIT)
        self.assertEqual(exhausted["exploration_remaining"], 0)
        self.assertTrue(exhausted["exploration_exhausted"])

        with self.assertRaisesRegex(
            RuntimeError,
            r"exploration_budget_exhausted.*apply_patch is restricted to paths",
        ):
            self.manager.list_files(task_id)

    def test_exhaustion_captures_dirty_tracked_path(self) -> None:
        task = self.manager.create_task("demo", "capture tracked", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        (task_path / "example.txt").write_text("alpha\ndirty\n", encoding="utf-8")

        self._exhaust_modification(self.manager, task_id)

        state = json.loads(self._state_path(task_id).read_text(encoding="utf-8"))
        self.assertEqual(state["exhaustion_paths"], ["example.txt"])

    def test_exhaustion_captures_untracked_nonignored_path(self) -> None:
        task = self.manager.create_task("demo", "capture untracked", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        (task_path / "notes.txt").write_text("first\nsecond\n", encoding="utf-8")

        self._exhaust_modification(self.manager, task_id)

        state = json.loads(self._state_path(task_id).read_text(encoding="utf-8"))
        self.assertEqual(state["exhaustion_paths"], ["notes.txt"])

    def test_exhaustion_paths_persist_across_manager_reload(self) -> None:
        task = self.manager.create_task("demo", "persist boundary", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        (task_path / "example.txt").write_text("alpha\ndirty\n", encoding="utf-8")

        self._exhaust_modification(self.manager, task_id)

        reloaded = WorkspaceManager(self.repositories, self.tasks)
        reloaded.task_status(task_id)
        self.assertEqual(reloaded._exhaustion_paths[task_id], ("example.txt",))

    def test_post_exhaustion_patch_allows_captured_dirty_tracked_path(self) -> None:
        task = self.manager.create_task("demo", "repair tracked", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        (task_path / "example.txt").write_text("alpha\ndirty\n", encoding="utf-8")
        self._exhaust_modification(self.manager, task_id)

        status = self.manager.apply_patch(task_id, self._example_patch("dirty", "fixed"))

        self.assertIn("example.txt", status["status"])
        self.assertEqual(
            (task_path / "example.txt").read_text(encoding="utf-8"),
            "alpha\nfixed\n",
        )

    def test_post_exhaustion_patch_allows_captured_untracked_path(self) -> None:
        task = self.manager.create_task("demo", "repair untracked", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        (task_path / "notes.txt").write_text("first\nsecond\n", encoding="utf-8")
        self._exhaust_modification(self.manager, task_id)

        patch = (
            "--- a/notes.txt\n"
            "+++ b/notes.txt\n"
            "@@ -1,2 +1,2 @@\n"
            " first\n"
            "-second\n"
            "+changed\n"
        )
        status = self.manager.apply_patch(task_id, patch)

        self.assertIn("notes.txt", status["status"])
        self.assertEqual(
            (task_path / "notes.txt").read_text(encoding="utf-8"),
            "first\nchanged\n",
        )

    def test_post_exhaustion_patch_refuses_clean_tracked_path(self) -> None:
        task = self.manager.create_task("demo", "refuse clean tracked", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        (task_path / "example.txt").write_text("alpha\ndirty\n", encoding="utf-8")
        self._exhaust_modification(self.manager, task_id)

        patch = "--- a/clean.txt\n+++ b/clean.txt\n@@ -1 +1 @@\n-clean\n+changed\n"
        with self.assertRaisesRegex(RuntimeError, "exploration_mutation_scope_exceeded"):
            self.manager.apply_patch(task_id, patch)

        self.assertEqual((task_path / "clean.txt").read_text(encoding="utf-8"), "clean\n")

    def test_post_exhaustion_patch_refuses_new_path(self) -> None:
        task = self.manager.create_task("demo", "refuse new path", "main")
        task_id = task["task_id"]
        self._exhaust_modification(self.manager, task_id)

        patch = "--- /dev/null\n+++ b/new.txt\n@@ -0,0 +1 @@\n+new\n"
        with self.assertRaisesRegex(RuntimeError, "exploration_mutation_scope_exceeded"):
            self.manager.apply_patch(task_id, patch)

        self.assertFalse((Path(task["path"]) / "new.txt").exists())

    def test_post_exhaustion_mixed_patch_is_rejected_atomically(self) -> None:
        task = self.manager.create_task("demo", "mixed patch", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        (task_path / "example.txt").write_text("alpha\ndirty\n", encoding="utf-8")
        self._exhaust_modification(self.manager, task_id)

        patch = (
            "--- a/example.txt\n"
            "+++ b/example.txt\n"
            "@@ -1,2 +1,2 @@\n"
            " alpha\n"
            "-dirty\n"
            "+fixed\n"
            "--- a/clean.txt\n"
            "+++ b/clean.txt\n"
            "@@ -1 +1 @@\n"
            "-clean\n"
            "+changed\n"
        )
        with self.assertRaisesRegex(RuntimeError, "exploration_mutation_scope_exceeded"):
            self.manager.apply_patch(task_id, patch)

        self.assertEqual(
            (task_path / "example.txt").read_text(encoding="utf-8"),
            "alpha\ndirty\n",
        )
        self.assertEqual((task_path / "clean.txt").read_text(encoding="utf-8"), "clean\n")

    def test_validate_patch_paths_returns_both_old_and_new_paths(self) -> None:
        task = self.manager.create_task("demo", "patch paths", "main")
        touched = self.manager._validate_patch_paths(
            Path(task["path"]),
            "--- a/example.txt\n+++ b/clean.txt\n@@ -1 +1 @@\n-alpha\n+clean\n",
        )
        self.assertEqual(touched, ("clean.txt", "example.txt"))

    def test_malformed_persisted_exhaustion_paths_fail_closed(self) -> None:
        task = self.manager.create_task("demo", "malformed state", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        patch = self._example_patch("beta", "gamma")
        malformed_values = [
            "not-a-list",
            [1],
            ["z.txt", "a.txt"],
            ["a.txt", "a.txt"],
            [""],
            ["/absolute"],
            ["../escape"],
            [".git/config"],
            ["./example.txt"],
            ["dir//file.txt"],
            ["nul\x00path"],
        ]

        for value in malformed_values:
            with self.subTest(value=value):
                self._state_path(task_id).write_text(
                    json.dumps(
                        {
                            "mode": "modification",
                            "calls": MODIFICATION_EXPLORATION_HARD_LIMIT,
                            "exhaustion_paths": value,
                        }
                    ),
                    encoding="utf-8",
                )
                reloaded = WorkspaceManager(self.repositories, self.tasks)
                with self.assertRaises(RuntimeError):
                    reloaded.apply_patch(task_id, patch)
                self.assertEqual(
                    (task_path / "example.txt").read_text(encoding="utf-8"),
                    "alpha\nbeta\n",
                )

    def test_legacy_exhausted_modification_state_without_boundary_fails_closed(self) -> None:
        task = self.manager.create_task("demo", "legacy exhausted", "main")
        task_id = task["task_id"]
        self._state_path(task_id).write_text(
            json.dumps(
                {
                    "mode": "modification",
                    "calls": MODIFICATION_EXPLORATION_HARD_LIMIT,
                }
            ),
            encoding="utf-8",
        )

        reloaded = WorkspaceManager(self.repositories, self.tasks)
        with self.assertRaisesRegex(RuntimeError, "exploration_mutation_scope_exceeded"):
            reloaded.apply_patch(task_id, self._example_patch("beta", "gamma"))

    def test_boundary_capture_failure_leaves_task_fail_closed(self) -> None:
        task = self.manager.create_task("demo", "capture failure", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        (task_path / "example.txt").write_text("alpha\ndirty\n", encoding="utf-8")

        for _ in range(MODIFICATION_EXPLORATION_HARD_LIMIT - 1):
            self.manager.read_file(task_id, "example.txt")

        def fail_capture(_task: Path) -> tuple[str, ...]:
            raise RuntimeError("simulated capture failure")

        self.manager._capture_exhaustion_paths = fail_capture
        with self.assertRaisesRegex(RuntimeError, "exploration_boundary_capture_failed"):
            self.manager.read_file(task_id, "example.txt")

        reloaded = WorkspaceManager(self.repositories, self.tasks)
        with self.assertRaisesRegex(RuntimeError, "exploration_mutation_scope_exceeded"):
            reloaded.apply_patch(task_id, self._example_patch("dirty", "fixed"))

    def test_boundary_persistence_failure_leaves_task_fail_closed(self) -> None:
        task = self.manager.create_task("demo", "state failure", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        (task_path / "example.txt").write_text("alpha\ndirty\n", encoding="utf-8")

        for _ in range(MODIFICATION_EXPLORATION_HARD_LIMIT - 1):
            self.manager.read_file(task_id, "example.txt")

        original_save = self.manager._save_state
        calls = 0

        def fail_final_save(current_task_id: str) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated persistence failure")
            original_save(current_task_id)

        self.manager._save_state = fail_final_save
        with self.assertRaisesRegex(RuntimeError, "exploration_boundary_state_failed"):
            self.manager.read_file(task_id, "example.txt")

        reloaded = WorkspaceManager(self.repositories, self.tasks)
        with self.assertRaisesRegex(RuntimeError, "exploration_mutation_scope_exceeded"):
            reloaded.apply_patch(task_id, self._example_patch("dirty", "fixed"))

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
