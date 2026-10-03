from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from coding_executor.task_maintenance import (
    LIBRECHAT_WORKSPACE_LINKS,
    _child_environment,
    _require_librechat_repository,
    _run_operator_command,
    deprovision_task_dependencies,
    inventory,
    provision_task_dependencies,
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
        self.repository = self.repositories / "LibreChat"
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

    def _configure_librechat_workspace(self) -> None:
        (self.repository / ".gitignore").write_text(
            "*.tmp\n"
            "node_modules/\n"
            "packages/*/dist/\n",
            encoding="utf-8",
        )
        (self.repository / "package.json").write_text(
            json.dumps(
                {
                    "name": "LibreChat",
                    "packageManager": "npm@11.13.0",
                    "workspaces": [
                        "api",
                        "client",
                        "packages/*",
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (self.repository / "package-lock.json").write_text(
            json.dumps(
                {
                    "name": "LibreChat",
                    "lockfileVersion": 3,
                    "packages": {},
                }
            )
            + "\n",
            encoding="utf-8",
        )

        self._git(
            "add",
            ".gitignore",
            "package.json",
            "package-lock.json",
        )
        self._git(
            "commit",
            "-m",
            "add LibreChat workspace fixture",
        )

    def _dependency_runner(
        self,
        commands: list[list[str]],
        *,
        dirty_after_build: bool = False,
    ):
        def runner(
            cwd: Path,
            argv: list[str],
            timeout: int,
        ) -> None:
            commands.append(list(argv))
            self.assertEqual(timeout, 1800)

            if argv[:2] == ["npm", "ci"]:
                for relative, (
                    workspace,
                    _entrypoint,
                ) in LIBRECHAT_WORKSPACE_LINKS.items():
                    link = cwd / relative
                    target = cwd / workspace

                    link.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    link.symlink_to(
                        os.path.relpath(
                            target,
                            link.parent,
                        )
                    )

                return

            if argv == [
                "npm",
                "run",
                "build:packages",
            ]:
                for _relative, (
                    workspace,
                    entrypoint,
                ) in LIBRECHAT_WORKSPACE_LINKS.items():
                    target = cwd / workspace / entrypoint

                    target.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    target.write_text(
                        "module.exports = {};\n",
                        encoding="utf-8",
                    )

                if dirty_after_build:
                    (cwd / "unexpected.txt").write_text(
                        "unexpected\n",
                        encoding="utf-8",
                    )

                return

            raise AssertionError(argv)

        return runner

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

    def test_dependency_repository_is_restricted_to_librechat(self) -> None:
        with self.assertRaisesRegex(ValueError, "restricted"):
            _require_librechat_repository(
                self.repositories / "not-librechat"
            )

    def test_dependency_provision_and_deprovision_are_task_local(self) -> None:
        self._configure_librechat_workspace()
        task = self._worktree("dependency-task")
        commands: list[list[str]] = []

        result = provision_task_dependencies(
            self.repositories,
            self.tasks,
            "dependency-task",
            runner=self._dependency_runner(commands),
        )

        self.assertTrue(result["provisioned"])
        self.assertEqual(commands[0][:2], ["npm", "ci"])
        self.assertEqual(
            commands[1],
            ["npm", "run", "build:packages"],
        )

        for relative, (workspace, entrypoint) in (
            LIBRECHAT_WORKSPACE_LINKS.items()
        ):
            self.assertEqual(
                (task / relative).resolve(strict=True),
                (task / workspace).resolve(strict=True),
            )
            self.assertTrue(
                (task / workspace / entrypoint).is_file()
            )

        states = {
            item["task_id"]: item["state"]
            for item in inventory(
                self.repositories,
                self.tasks,
            )["tasks"]
        }
        self.assertEqual(states["dependency-task"], "dirty")

        result = deprovision_task_dependencies(
            self.repositories,
            self.tasks,
            "dependency-task",
        )

        self.assertTrue(result["deprovisioned"])
        self.assertFalse((task / "node_modules").exists())

        states = {
            item["task_id"]: item["state"]
            for item in inventory(
                self.repositories,
                self.tasks,
            )["tasks"]
        }
        self.assertEqual(states["dependency-task"], "clean")

    def test_dependency_mutations_use_exclusive_maintenance_lock(self) -> None:
        self._configure_librechat_workspace()
        self._worktree("dependency-lock-task")
        locks: list[tuple[Path, bool]] = []

        @contextmanager
        def fake_lock(
            task_root: Path,
            *,
            exclusive: bool = False,
            lock_path: Path | None = None,
        ):
            del lock_path
            locks.append(
                (
                    task_root.resolve(),
                    exclusive,
                )
            )
            yield

        with mock.patch(
            "coding_executor.task_maintenance.maintenance_lock",
            fake_lock,
        ):
            provision_task_dependencies(
                self.repositories,
                self.tasks,
                "dependency-lock-task",
                runner=self._dependency_runner([]),
            )

            deprovision_task_dependencies(
                self.repositories,
                self.tasks,
                "dependency-lock-task",
            )

        self.assertEqual(
            locks,
            [
                (self.tasks.resolve(), True),
                (self.tasks.resolve(), True),
            ],
        )

    def test_dependency_provision_rejects_workspace_symlink_escape(self) -> None:
        self._configure_librechat_workspace()

        outside = self.tasks.parent / "outside-workspace"
        outside.mkdir()

        packages = self.repository / "packages"
        packages.mkdir()

        (packages / "api").symlink_to(
            outside,
            target_is_directory=True,
        )

        self._git(
            "add",
            "packages/api",
        )
        self._git(
            "commit",
            "-m",
            "add escaped workspace fixture",
        )

        self._worktree(
            "dependency-workspace-escape-task"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "workspace package root must not be a symbolic link",
        ):
            provision_task_dependencies(
                self.repositories,
                self.tasks,
                "dependency-workspace-escape-task",
                runner=self._dependency_runner([]),
            )

    def test_operator_command_kills_process_group_on_timeout(self) -> None:
        process = mock.Mock()
        process.pid = 4242
        process.wait.side_effect = [
            subprocess.TimeoutExpired(
                ["npm", "ci"],
                1,
            ),
            -signal.SIGKILL,
        ]

        with (
            mock.patch(
                "coding_executor.task_maintenance.subprocess.Popen",
                return_value=process,
            ) as popen,
            mock.patch(
                "coding_executor.task_maintenance.os.killpg",
            ) as killpg,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "exceeded 1 second timeout",
            ):
                _run_operator_command(
                    Path("/tmp"),
                    ["npm", "ci"],
                    1,
                )

        self.assertTrue(
            popen.call_args.kwargs["start_new_session"]
        )

        killpg.assert_called_once_with(
            4242,
            signal.SIGKILL,
        )

    def test_dependency_provision_requires_pristine_task(self) -> None:
        self._configure_librechat_workspace()
        task = self._worktree("dependency-dirty-task")
        (task / "build.tmp").write_text(
            "ignored\\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "no ignored files"):
            provision_task_dependencies(
                self.repositories,
                self.tasks,
                "dependency-dirty-task",
                runner=self._dependency_runner([]),
            )

    def test_dependency_provision_rejects_symlink_cache(self) -> None:
        self._configure_librechat_workspace()
        self._worktree("dependency-cache-task")

        outside = self.tasks.parent / "outside-cache"
        outside.mkdir()
        (self.tasks / ".npm-cache").symlink_to(
            outside,
            target_is_directory=True,
        )

        with self.assertRaisesRegex(
            ValueError,
            "must not be a symbolic link",
        ):
            provision_task_dependencies(
                self.repositories,
                self.tasks,
                "dependency-cache-task",
                runner=self._dependency_runner([]),
            )

    def test_dependency_provision_rejects_non_generated_changes(self) -> None:
        self._configure_librechat_workspace()
        self._worktree("dependency-output-task")

        with self.assertRaisesRegex(
            RuntimeError,
            "modified tracked or non-ignored untracked",
        ):
            provision_task_dependencies(
                self.repositories,
                self.tasks,
                "dependency-output-task",
                runner=self._dependency_runner(
                    [],
                    dirty_after_build=True,
                ),
            )

    def test_dependency_deprovision_refuses_unexpected_ignored_content(self) -> None:
        self._configure_librechat_workspace()
        task = self._worktree("dependency-guard-task")

        provision_task_dependencies(
            self.repositories,
            self.tasks,
            "dependency-guard-task",
            runner=self._dependency_runner([]),
        )

        (task / "operator-note.tmp").write_text(
            "retain me\\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the dependency allowlist",
        ):
            deprovision_task_dependencies(
                self.repositories,
                self.tasks,
                "dependency-guard-task",
            )

        self.assertTrue((task / "node_modules").exists())
        self.assertTrue((task / "operator-note.tmp").exists())

    def test_dependency_deprovision_refuses_nonignored_generated_content(self) -> None:
        self._configure_librechat_workspace()
        task = self._worktree("dependency-protected-task")

        provision_task_dependencies(
            self.repositories,
            self.tasks,
            "dependency-protected-task",
            runner=self._dependency_runner([]),
        )

        protected = task / ".turbo" / "keep.txt"
        protected.parent.mkdir()
        protected.write_text(
            "preserve\n",
            encoding="utf-8",
        )

        self.assertIn(
            ".turbo/keep.txt",
            subprocess.run(
                [
                    "git",
                    "ls-files",
                    "--others",
                    "--exclude-standard",
                ],
                cwd=task,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines(),
        )

        with self.assertRaisesRegex(
            ValueError,
            "non-ignored untracked",
        ):
            deprovision_task_dependencies(
                self.repositories,
                self.tasks,
                "dependency-protected-task",
            )

        self.assertTrue(protected.is_file())

    def test_dependency_deprovision_without_artifacts_is_noop(self) -> None:
        self._configure_librechat_workspace()
        self._worktree("dependency-clean-task")

        result = deprovision_task_dependencies(
            self.repositories,
            self.tasks,
            "dependency-clean-task",
        )

        self.assertFalse(result["deprovisioned"])

    def test_inventory_reports_stale_worktree_registration(self) -> None:
        stale = self._worktree("stale-task")
        shutil.rmtree(stale)

        result = inventory(self.repositories, self.tasks)

        self.assertEqual(
            result["stale_registrations"],
            [{"repository": "LibreChat", "task_id": "stale-task"}],
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
