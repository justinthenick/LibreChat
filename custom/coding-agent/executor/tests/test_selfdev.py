from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from coding_executor.config import Settings
from coding_executor.selfdev_client import SelfDevClient
from coding_executor.selfdev_host import SelfDevWorker


class SelfDevClientTest(unittest.TestCase):
    def test_rejects_invalid_task_id_before_socket_access(self) -> None:
        client = SelfDevClient(Path("/tmp/does-not-exist.sock"))
        with self.assertRaisesRegex(ValueError, "invalid task id"):
            client.build_candidate("../escape")
        with self.assertRaisesRegex(ValueError, "invalid task id"):
            client.run_candidate_gate("../escape")


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

        with self.assertRaisesRegex(ValueError, "requires only task_id"):
            self.worker.handle(
                "run_candidate_gate",
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


    def test_candidate_compile_uses_tmpfs_for_bytecode(self) -> None:
        self.worker._write_state(
            {
                "task_id": "selfdev-demo-12345678",
                "image": "candidate:test",
            }
        )

        commands: list[list[str]] = []

        def fake_run(args: list[str], **_kwargs: object) -> dict[str, object]:
            commands.append(args)
            return {
                "exit_code": 0,
                "stdout": "",
                "stderr": "",
                "truncated": False,
            }

        with patch.object(self.worker, "_run", side_effect=fake_run):
            result = self.worker.test_candidate("selfdev-demo-12345678")

        self.assertTrue(result["passed"])
        self.assertGreaterEqual(len(commands), 2)
        compile_command = commands[0]
        self.assertIn("PYTHONPYCACHEPREFIX=/tmp/pycache", compile_command)
        self.assertIn("--read-only", compile_command)
        self.assertIn("/tmp:rw,noexec,nosuid,size=256m", compile_command)

    def test_candidate_validation_returns_failure_without_raising(self) -> None:
        self.worker._write_state(
            {
                "task_id": "selfdev-demo-12345678",
                "image": "candidate:test",
            }
        )

        results = iter(
            [
                {
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": "compile failed",
                    "truncated": False,
                },
                {
                    "exit_code": 0,
                    "stdout": "tests passed",
                    "stderr": "",
                    "truncated": False,
                },
            ]
        )

        with patch.object(self.worker, "_run", side_effect=lambda *_args, **_kwargs: next(results)):
            result = self.worker.test_candidate("selfdev-demo-12345678")

        self.assertFalse(result["passed"])
        self.assertEqual(result["compileall"]["exit_code"], 1)
        self.assertEqual(result["unit_tests"]["exit_code"], 0)

    def test_candidate_gate_cleans_up_after_success(self) -> None:
        with (
            patch.object(self.worker, "_read_state", return_value=None),
            patch.object(self.worker, "_container_exists", return_value=False),
            patch.object(
                self.worker,
                "build_candidate",
                return_value={"task_id": "selfdev-demo-12345678", "exit_code": 0},
            ),
            patch.object(
                self.worker,
                "test_candidate",
                return_value={"passed": True},
            ),
            patch.object(
                self.worker,
                "start_candidate",
                return_value={"health": {"ok": True}},
            ),
            patch.object(
                self.worker,
                "_mcp_smoke",
                return_value={"ok": True},
            ),
            patch.object(
                self.worker,
                "candidate_status",
                return_value={"container_exists": True},
            ),
            patch.object(
                self.worker,
                "destroy_candidate",
                return_value={"removed_container": True, "removed_image": True},
            ) as cleanup,
        ):
            result = self.worker.run_candidate_gate("selfdev-demo-12345678")

        self.assertTrue(result["passed"])
        self.assertEqual(result["stage"], "complete")
        self.assertEqual(
            result["cleanup"],
            {"removed_container": True, "removed_image": True},
        )
        cleanup.assert_called_once_with()

    def test_candidate_gate_cleans_up_after_validation_failure(self) -> None:
        with (
            patch.object(self.worker, "_read_state", return_value=None),
            patch.object(self.worker, "_container_exists", return_value=False),
            patch.object(
                self.worker,
                "build_candidate",
                return_value={"task_id": "selfdev-demo-12345678", "exit_code": 0},
            ),
            patch.object(
                self.worker,
                "test_candidate",
                return_value={"passed": False},
            ),
            patch.object(self.worker, "start_candidate") as start,
            patch.object(
                self.worker,
                "destroy_candidate",
                return_value={"removed_container": False, "removed_image": True},
            ) as cleanup,
        ):
            result = self.worker.run_candidate_gate("selfdev-demo-12345678")

        self.assertFalse(result["passed"])
        self.assertEqual(result["stage"], "test")
        self.assertEqual(result["error"], "candidate validation failed")
        start.assert_not_called()
        cleanup.assert_called_once_with()

    def test_candidate_image_name_is_fixed_from_task_id(self) -> None:
        first = self.worker._image_name("selfdev-demo-12345678")
        second = self.worker._image_name("selfdev-demo-12345678")
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("librechat-coding-executor-candidate:selfdev-"))
        self.assertNotIn("selfdev-demo-12345678", first)


class SelfDevRuntimeContractTest(unittest.TestCase):
    def test_mcp_smoke_uses_modern_wire_contract_and_validates_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tasks = root / "tasks"
            candidates = root / "candidates"
            tasks.mkdir()
            worker = SelfDevWorker(tasks, candidates, 8767)
            worker._write_state({"token": "candidate-secret"})

            calls: list[tuple[str, dict[str, object]]] = []

            def response(body: dict[str, object]) -> MagicMock:
                value = MagicMock()
                value.status = 200
                value.read.return_value = json.dumps(body).encode("utf-8")
                value.__enter__.return_value = value
                value.__exit__.return_value = False
                return value

            def urlopen(request: object, timeout: int = 0) -> MagicMock:
                self.assertEqual(timeout, 10)
                headers = {
                    key.lower(): value
                    for key, value in request.header_items()
                }
                payload = json.loads(request.data.decode("utf-8"))
                method = payload["method"]
                calls.append((method, payload))

                self.assertEqual(
                    headers["mcp-protocol-version"],
                    "2026-07-28",
                )
                self.assertEqual(headers["mcp-method"], method)
                self.assertEqual(
                    headers["authorization"],
                    "Bearer candidate-secret",
                )
                meta = payload["params"]["_meta"]
                self.assertEqual(
                    meta["io.modelcontextprotocol/protocolVersion"],
                    "2026-07-28",
                )
                self.assertEqual(
                    meta["io.modelcontextprotocol/clientCapabilities"],
                    {},
                )
                self.assertEqual(
                    meta["io.modelcontextprotocol/clientInfo"]["name"],
                    "librechat-selfdev-worker",
                )

                if method == "server/discover":
                    return response(
                        {
                            "jsonrpc": "2.0",
                            "id": payload["id"],
                            "result": {
                                "supportedVersions": ["2026-07-28"],
                                "capabilities": {"tools": {}},
                            },
                        }
                    )
                if method == "tools/list":
                    return response(
                        {
                            "jsonrpc": "2.0",
                            "id": payload["id"],
                            "result": {
                                "tools": [
                                    {"name": name}
                                    for name in (
                                        "list_repositories",
                                        "create_task",
                                        "task_status",
                                        "list_files",
                                        "read_file",
                                        "search_text",
                                        "apply_patch",
                                        "run_check",
                                        "git_diff",
                                    )
                                ]
                            },
                        }
                    )
                self.fail(f"unexpected MCP method: {method}")

            with patch("urllib.request.urlopen", side_effect=urlopen):
                result = worker._mcp_smoke()

            self.assertTrue(result["ok"])
            self.assertEqual(result["discover_http_status"], 200)
            self.assertEqual(result["tools_http_status"], 200)
            self.assertTrue(result["selfdev_tools_absent"])
            self.assertEqual(
                [method for method, _payload in calls],
                ["server/discover", "tools/list"],
            )

    def test_mcp_smoke_rejects_selfdev_tool_leak(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tasks = root / "tasks"
            candidates = root / "candidates"
            tasks.mkdir()
            worker = SelfDevWorker(tasks, candidates, 8767)
            worker._write_state({"token": "candidate-secret"})

            discover = MagicMock()
            discover.status = 200
            discover.read.return_value = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "discover",
                    "result": {
                        "supportedVersions": ["2026-07-28"],
                        "capabilities": {"tools": {}},
                    },
                }
            ).encode("utf-8")
            discover.__enter__.return_value = discover
            discover.__exit__.return_value = False

            tools = MagicMock()
            tools.status = 200
            tools.read.return_value = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "tools",
                    "result": {
                        "tools": [
                            {"name": name}
                            for name in (
                                "list_repositories",
                                "create_task",
                                "task_status",
                                "list_files",
                                "read_file",
                                "search_text",
                                "apply_patch",
                                "run_check",
                                "git_diff",
                                "run_candidate_gate",
                            )
                        ]
                    },
                }
            ).encode("utf-8")
            tools.__enter__.return_value = tools
            tools.__exit__.return_value = False

            with patch(
                "urllib.request.urlopen",
                side_effect=[discover, tools],
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "unexpectedly exposed self-development tools",
                ):
                    worker._mcp_smoke()

    def test_systemd_unit_keeps_worker_unprivileged_and_no_docker_socket_mount(self) -> None:
        executor_root = Path(__file__).resolve().parents[1]
        unit = (
            executor_root
            / "systemd"
            / "librechat-coding-selfdev-worker.service"
        ).read_text(encoding="utf-8")
        installer = (
            executor_root
            / "systemd"
            / "install-user-service.sh"
        ).read_text(encoding="utf-8")

        self.assertIn("NoNewPrivileges=true", unit)
        self.assertIn("Restart=on-failure", unit)
        self.assertIn("worker.sock", unit)
        self.assertNotIn("/var/run/docker.sock", unit)
        self.assertNotIn("sudo ", installer)
        self.assertIn("systemctl --user", installer)


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
