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
MODIFICATION_EXPLORATION_SOFT_LIMIT = workspaces_module.MODIFICATION_EXPLORATION_SOFT_LIMIT
MODIFICATION_EXPLORATION_HARD_LIMIT = workspaces_module.MODIFICATION_EXPLORATION_HARD_LIMIT
MODIFICATION_POST_PATCH_EXPLORATION_LIMIT = (
    workspaces_module.MODIFICATION_POST_PATCH_EXPLORATION_LIMIT
)


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

    def _pass_modification_checkpoint(self, manager: WorkspaceManager, task_id: str) -> str:
        warning = ""
        for _ in range(MODIFICATION_EXPLORATION_SOFT_LIMIT):
            warning = manager.read_file(task_id, "example.txt")
        self.assertIn("Mutation checkpoint reached", warning)

        manager.apply_patch(
            task_id,
            "--- a/clean.txt\n+++ b/clean.txt\n@@ -1 +1 @@\n-clean\n+checkpoint\n",
        )
        (self.tasks / task_id / "clean.txt").write_text("clean\n", encoding="utf-8")
        return warning

    def _exhaust_modification(self, manager: WorkspaceManager, task_id: str) -> str:
        self._pass_modification_checkpoint(manager, task_id)
        warning = ""
        for _ in range(
            MODIFICATION_EXPLORATION_HARD_LIMIT - MODIFICATION_EXPLORATION_SOFT_LIMIT
        ):
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

    def test_apply_patch_reports_git_check_failure_context(self) -> None:
        task = self.manager.create_task("demo", "bad patch context", "main")
        task_id = task["task_id"]

        with self.assertRaisesRegex(RuntimeError, "patch_check_failed:"):
            self.manager.apply_patch(
                task_id,
                "--- a/example.txt\n+++ b/example.txt\n@@ -1,2 +1,2 @@\n alpha\n-not-beta\n+gamma\n",
            )

        self.assertEqual(
            (Path(task["path"]) / "example.txt").read_text(encoding="utf-8"),
            "alpha\nbeta\n",
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

    def test_child_environment_disables_python_bytecode(self) -> None:
        environment = self.manager._child_environment()
        self.assertEqual(environment["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertNotIn("CODING_EXECUTOR_TOKEN", environment)

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

    def test_modification_checkpoint_blocks_exploration_until_first_patch(self) -> None:
        task = self.manager.create_task("demo", "checkpoint gate", "main")
        task_id = task["task_id"]

        warning = ""
        for _ in range(MODIFICATION_EXPLORATION_SOFT_LIMIT):
            warning = self.manager.read_file(task_id, "example.txt")

        self.assertIn("Mutation checkpoint reached", warning)
        budget = self.manager.task_status(task_id)["exploration_budget"]
        self.assertTrue(budget["mutation_checkpoint_reached"])
        self.assertFalse(budget["first_patch_applied"])
        self.assertEqual(budget["pre_patch_exploration_remaining"], 0)
        self.assertEqual(budget["post_patch_exploration_remaining"], 0)

        with self.assertRaisesRegex(RuntimeError, "mutation_checkpoint_required"):
            self.manager.read_file(task_id, "example.txt")

        self.manager.apply_patch(
            task_id,
            self._example_patch("beta", "gamma"),
        )
        budget = self.manager.task_status(task_id)["exploration_budget"]
        self.assertFalse(budget["mutation_checkpoint_reached"])
        self.assertTrue(budget["first_patch_applied"])
        self.assertEqual(
            budget["post_patch_exploration_remaining"],
            MODIFICATION_POST_PATCH_EXPLORATION_LIMIT,
        )

        output = self.manager.read_file(task_id, "example.txt")
        self.assertIn("gamma", output)
        self.assertEqual(
            self.manager.task_status(task_id)["exploration_budget"]["exploration_calls"],
            MODIFICATION_EXPLORATION_SOFT_LIMIT + 1,
        )

    def test_early_patch_still_allows_only_four_followup_exploration_calls(self) -> None:
        task = self.manager.create_task("demo", "early patch allowance", "main")
        task_id = task["task_id"]

        for _ in range(3):
            self.manager.read_file(task_id, "example.txt")
        self.manager.apply_patch(task_id, self._example_patch("beta", "gamma"))

        for index in range(MODIFICATION_POST_PATCH_EXPLORATION_LIMIT):
            output = self.manager.read_file(task_id, "example.txt")
            self.assertIn("gamma", output)
            if index == MODIFICATION_POST_PATCH_EXPLORATION_LIMIT - 1:
                self.assertIn("post-patch exploration allowance is now exhausted", output)

        budget = self.manager.task_status(task_id)["exploration_budget"]
        self.assertEqual(
            budget["post_patch_exploration_calls"],
            MODIFICATION_POST_PATCH_EXPLORATION_LIMIT,
        )
        self.assertEqual(budget["post_patch_exploration_remaining"], 0)
        self.assertTrue(budget["exploration_exhausted"])
        self.assertEqual(
            budget["exploration_calls"],
            3 + MODIFICATION_POST_PATCH_EXPLORATION_LIMIT,
        )

        with self.assertRaisesRegex(RuntimeError, "exploration_budget_exhausted"):
            self.manager.read_file(task_id, "example.txt")

        status = self.manager.apply_patch(
            task_id,
            "--- a/clean.txt\n+++ b/clean.txt\n@@ -1 +1 @@\n-clean\n+completed\n",
        )
        self.assertIn("clean.txt", status["status"])
        self.assertEqual(
            (Path(task["path"]) / "clean.txt").read_text(encoding="utf-8"),
            "completed\n",
        )

    def test_first_patch_checkpoint_state_persists_across_reload(self) -> None:
        task = self.manager.create_task("demo", "checkpoint persistence", "main")
        task_id = task["task_id"]

        for _ in range(MODIFICATION_EXPLORATION_SOFT_LIMIT):
            self.manager.read_file(task_id, "example.txt")
        self.manager.apply_patch(task_id, self._example_patch("beta", "gamma"))

        reloaded = WorkspaceManager(self.repositories, self.tasks)
        budget = reloaded.task_status(task_id)["exploration_budget"]
        self.assertTrue(budget["first_patch_applied"])
        self.assertFalse(budget["mutation_checkpoint_reached"])
        self.assertIn("gamma", reloaded.read_file(task_id, "example.txt"))

    def test_post_patch_exhaustion_keeps_mutation_available_after_checkpoint(self) -> None:
        task = self.manager.create_task("demo", "post patch completion", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])

        warning = ""
        for _ in range(MODIFICATION_EXPLORATION_SOFT_LIMIT):
            warning = self.manager.read_file(task_id, "example.txt")
        self.assertIn("Mutation checkpoint reached", warning)

        self.manager.apply_patch(task_id, self._example_patch("beta", "gamma"))

        for _ in range(MODIFICATION_POST_PATCH_EXPLORATION_LIMIT):
            warning = self.manager.read_file(task_id, "example.txt")

        self.assertIn("post-patch exploration allowance is now exhausted", warning)
        self.assertIn("Proceed with apply_patch", warning)
        self.assertNotIn("apply_patch is restricted to paths", warning)

        exhausted = self.manager.task_status(task_id)["exploration_budget"]
        self.assertEqual(exhausted["exploration_calls"], MODIFICATION_EXPLORATION_HARD_LIMIT)
        self.assertEqual(exhausted["exploration_remaining"], 0)
        self.assertTrue(exhausted["exploration_exhausted"])

        state = json.loads(self._state_path(task_id).read_text(encoding="utf-8"))
        self.assertIsNone(state["exhaustion_paths"])

        with self.assertRaisesRegex(RuntimeError, "exploration_budget_exhausted"):
            self.manager.list_files(task_id)

        status = self.manager.apply_patch(
            task_id,
            "--- a/clean.txt\n+++ b/clean.txt\n@@ -1 +1 @@\n-clean\n+completed\n",
        )
        self.assertIn("clean.txt", status["status"])
        self.assertEqual((task_path / "clean.txt").read_text(encoding="utf-8"), "completed\n")

        with self.assertRaisesRegex(RuntimeError, "exploration_budget_exhausted"):
            self.manager.read_file(task_id, "clean.txt")

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

    def test_legacy_exhausted_boundary_still_restricts_uncaptured_paths(self) -> None:
        task = self.manager.create_task("demo", "legacy captured boundary", "main")
        task_id = task["task_id"]
        task_path = Path(task["path"])
        self._state_path(task_id).write_text(
            json.dumps(
                {
                    "mode": "modification",
                    "calls": MODIFICATION_EXPLORATION_HARD_LIMIT,
                    "initial_patch_applied": False,
                    "post_patch_exploration_calls": 0,
                    "exhaustion_paths": ["example.txt"],
                }
            ),
            encoding="utf-8",
        )

        reloaded = WorkspaceManager(self.repositories, self.tasks)
        with self.assertRaisesRegex(RuntimeError, "exploration_mutation_scope_exceeded"):
            reloaded.apply_patch(
                task_id,
                "--- a/clean.txt\n+++ b/clean.txt\n@@ -1 +1 @@\n-clean\n+changed\n",
            )

        status = reloaded.apply_patch(task_id, self._example_patch("beta", "gamma"))
        self.assertIn("example.txt", status["status"])
        self.assertEqual(
            (task_path / "example.txt").read_text(encoding="utf-8"),
            "alpha\ngamma\n",
        )

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
