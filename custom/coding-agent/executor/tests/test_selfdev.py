from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_executor.config import Settings
from coding_executor.selfdev_client import SelfDevClient
from coding_executor.selfdev_host import SelfDevWorker


class SelfDevClientTest(unittest.TestCase):
    def test_rejects_invalid_task_id_before_socket_access(self) -> None:
        client = SelfDevClient(Path("/tmp/does-not-exist.sock"))
        with self.assertRaisesRegex(ValueError, "invalid task id"):
            client.build_candidate("../escape")


class SelfDevWorkerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.tasks = root / "tasks"
        self.candidates = root / "candidates"
        self.tasks.mkdir()
        self.task = self.tasks / "selfdev-demo-12345678"
        executor = self.task / "custom/coding-agent/executor"
        executor.mkdir(parents=True)
        (self.task / ".git").write_text("gitdir: /tmp/fake-worktree\n", encoding="utf-8")
        (executor / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
        (executor / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
        self.worker = SelfDevWorker(self.tasks, self.candidates, 8767)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_task_boundary_accepts_only_configured_task_root(self) -> None:
        task, executor = self.worker._task_executor("selfdev-demo-12345678")
        self.assertEqual(task, self.task)
        self.assertEqual(executor, self.task / "custom/coding-agent/executor")

        with self.assertRaisesRegex(ValueError, "invalid task id"):
            self.worker._task_executor("../escape")

    def test_action_contract_rejects_arbitrary_parameters(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires only task_id"):
            self.worker.handle(
                "build_candidate",
                {"task_id": "selfdev-demo-12345678", "command": "docker ps"},
            )

        with self.assertRaisesRegex(ValueError, "unsupported"):
            self.worker.handle("run_shell", {"task_id": "selfdev-demo-12345678"})

    def test_public_state_never_returns_candidate_token(self) -> None:
        state = {
            "task_id": "selfdev-demo-12345678",
            "image": "candidate:test",
            "token": "secret-value",
        }
        public = self.worker._public_state(state)
        self.assertIsNotNone(public)
        self.assertNotIn("token", public or {})
        self.assertEqual(public["task_id"], state["task_id"])

    def test_candidate_image_name_is_fixed_from_task_id(self) -> None:
        first = self.worker._image_name("selfdev-demo-12345678")
        second = self.worker._image_name("selfdev-demo-12345678")
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("librechat-coding-executor-candidate:selfdev-"))
        self.assertNotIn("selfdev-demo-12345678", first)


class SelfDevSettingsTest(unittest.TestCase):
    def _base_env(self) -> dict[str, str]:
        return {
            "CODING_EXECUTOR_TOKEN": "x" * 40,
            "CODING_EXECUTOR_PUBLIC_URL": "http://127.0.0.1:8766/mcp",
            "CODING_EXECUTOR_ALLOWED_HOSTS": "127.0.0.1:8766",
            "CODING_EXECUTOR_PORT": "8766",
        }

    def test_selfdev_disabled_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            env = self._base_env() | {
                "CODING_REPOSITORY_ROOT": str(root / "repos"),
                "CODING_TASK_ROOT": str(root / "tasks"),
            }
            with patch.dict(os.environ, env, clear=True):
                settings = Settings.from_environment()
        self.assertIsNone(settings.selfdev_socket)

    def test_selfdev_requires_absolute_socket_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            env = self._base_env() | {
                "CODING_REPOSITORY_ROOT": str(root / "repos"),
                "CODING_TASK_ROOT": str(root / "tasks"),
                "CODING_SELF_DEV_SOCKET": "relative/worker.sock",
            }
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaisesRegex(ValueError, "must be an absolute path"):
                    Settings.from_environment()

    def test_selfdev_absolute_socket_is_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "worker.sock"
            env = self._base_env() | {
                "CODING_REPOSITORY_ROOT": str(root / "repos"),
                "CODING_TASK_ROOT": str(root / "tasks"),
                "CODING_SELF_DEV_SOCKET": str(socket_path),
            }
            with patch.dict(os.environ, env, clear=True):
                settings = Settings.from_environment()
        self.assertEqual(settings.selfdev_socket, socket_path)


if __name__ == "__main__":
    unittest.main()
