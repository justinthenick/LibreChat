import tempfile
import unittest
from pathlib import Path

from host_maintenance.acp_sandbox import ACP_NETWORK
from host_maintenance.broker import Broker


IMAGE = "sha256:" + "a" * 64
ACP_IMAGE = "sha256:" + "b" * 64


class FakeAcpManager:
    def __init__(self):
        self.calls = []
        self.inspect_info = {
            "State": {
                "Status": "created",
                "Running": False,
            },
            "Config": {
                "Image": ACP_IMAGE,
                "OpenStdin": True,
                "StdinOnce": True,
            },
            "HostConfig": {
                "NetworkMode": ACP_NETWORK,
                "ReadonlyRootfs": True,
            },
        }

    def container_name(self, task_id):
        return f"librechat-acp-{task_id}"

    def create(self, task_id):
        self.calls.append(("create", task_id))
        return "e" * 64

    def inspect(self, task_id):
        self.calls.append(("inspect", task_id))
        return self.inspect_info

    def start(self, task_id):
        self.calls.append(("start", task_id))
        self.inspect_info["State"] = {
            "Status": "running",
            "Running": True,
        }

    def remove(self, task_id):
        self.calls.append(("remove", task_id))


class AcpBrokerAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name).resolve()

        self.tasks = root / "tasks"
        self.repositories = root / "repositories"
        self.state = root / "state"

        self.tasks.mkdir()
        self.repositories.mkdir()
        self.state.mkdir()

        self.task_id = "contained-acp-test"
        self.task = self.tasks / self.task_id
        self.task.mkdir()

        # AcpSandboxManager independently requires linked-worktree evidence.
        (self.task / ".git").write_text(
            "gitdir: /tmp/example\n",
            encoding="utf-8",
        )

        self.config = {
            "container": "executor-test",
            "image_id": IMAGE,
            "acp_image_id": ACP_IMAGE,
            "acp_relay_image_id": "sha256:" + "e" * 64,
            "acp_relay_signing_key": "c" * 64,
            "task_root": str(self.tasks),
            "repository_root": str(self.repositories),
            "lock_path": str(self.state / "maintenance.lock"),
            "repositories": {
                "LibreChat": {
                    "branch": "server/synology",
                    "url": "https://github.com/example/LibreChat.git",
                },
            },
            "enabled_mutations": {},
        }

        self.broker = Broker(
            self.config,
            runner=lambda *_args, **_kwargs: "",
        )

        self.identity = {
            "task_id": self.task_id,
            "repository": "LibreChat",
            "branch": f"agent/{self.task_id}",
            "head": "c" * 40,
            "dirty": True,
            "device": 1,
            "inode": 2,
            "fingerprint": "d" * 64,
            "state": "dirty",
            "checks": {
                "expected_identity": True,
                "registered_nonbroken": True,
                "no_git_locks": True,
                "no_git_operation": True,
            },
            "exclusive_gate_verified": True,
        }

        def helper(operation, *args, **_kwargs):
            self.assertEqual(operation, "task-identity")
            self.assertEqual(args, ("--task", self.task_id))
            return dict(self.identity)

        self.broker._helper = helper

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_task_identity_accepts_authoritative_evidence(self) -> None:
        result = self.broker.task_identity(self.task_id)

        self.assertEqual(result["task_id"], self.task_id)
        self.assertEqual(result["repository"], "LibreChat")
        self.assertEqual(
            result["branch"],
            f"agent/{self.task_id}",
        )

    def test_task_identity_rejects_wrong_branch(self) -> None:
        self.identity["branch"] = "agent/something-else"

        with self.assertRaisesRegex(
            RuntimeError,
            "branch identity mismatch",
        ):
            self.broker.task_identity(self.task_id)

    def test_task_identity_rejects_unapproved_repository(self) -> None:
        self.identity["repository"] = "OtherRepo"

        with self.assertRaisesRegex(
            RuntimeError,
            "not allowlisted",
        ):
            self.broker.task_identity(self.task_id)

    def test_task_identity_requires_exclusive_gate_evidence(self) -> None:
        self.identity["exclusive_gate_verified"] = False

        with self.assertRaisesRegex(
            RuntimeError,
            "gate evidence",
        ):
            self.broker.task_identity(self.task_id)

    def test_task_identity_rejects_failed_identity_checks(self) -> None:
        self.identity["checks"]["registered_nonbroken"] = False

        with self.assertRaisesRegex(
            RuntimeError,
            "identity checks failed",
        ):
            self.broker.task_identity(self.task_id)

    def test_acp_authorizer_accepts_only_exact_task_path(self) -> None:
        self.assertTrue(
            self.broker._authorize_acp_task(
                self.task_id,
                self.task,
            )
        )

        self.assertFalse(
            self.broker._authorize_acp_task(
                self.task_id,
                self.tasks,
            )
        )

    def test_acp_manager_is_internally_pinned(self) -> None:
        import json
        from test_relay_policy import specimen
        info = specimen()
        info["Image"] = self.config["acp_relay_image_id"]
        info["Mounts"][0]["Source"] = str(Path.home() / ".local/share/coding-maintenance/codex-adapter/run")
        self.broker._docker = lambda *args, **kwargs: json.dumps([info])
        manager = self.broker._acp_manager()

        self.assertEqual(manager.image, ACP_IMAGE)
        self.assertEqual(manager.task_root, self.tasks)

        resolved = manager.task_path(self.task_id)
        self.assertEqual(resolved, self.task)

    def test_acp_create_revalidates_before_success(self) -> None:
        manager = FakeAcpManager()
        self.broker._acp_manager = lambda: manager

        result = self.broker.acp_sandbox_create(self.task_id)

        self.assertEqual(
            manager.calls,
            [
                ("create", self.task_id),
                ("inspect", self.task_id),
            ],
        )
        self.assertEqual(result["status"], "created")
        self.assertFalse(result["running"])
        self.assertEqual(
            result["network"],
            ACP_NETWORK,
        )
        self.assertTrue(result["read_only_root"])

    def test_acp_start_revalidates_after_start(self) -> None:
        manager = FakeAcpManager()
        self.broker._acp_manager = lambda: manager

        result = self.broker.acp_sandbox_start(self.task_id)

        self.assertEqual(
            manager.calls,
            [
                ("start", self.task_id),
                ("inspect", self.task_id),
            ],
        )
        self.assertEqual(result["status"], "running")
        self.assertTrue(result["running"])

    def test_acp_remove_uses_validating_manager(self) -> None:
        manager = FakeAcpManager()
        self.broker._acp_manager = lambda: manager

        result = self.broker.acp_sandbox_remove(self.task_id)

        self.assertEqual(
            manager.calls,
            [("remove", self.task_id)],
        )
        self.assertTrue(result["removed"])
        self.assertEqual(
            result["container"],
            f"librechat-acp-{self.task_id}",
        )

    def test_acp_relay_signing_key_is_required(self) -> None:
        config = dict(self.config)
        config.pop(
            "acp_relay_signing_key"
        )

        with self.assertRaisesRegex(
            ValueError,
            "relay signing key",
        ):
            Broker(
                config,
                runner=lambda *_args, **_kwargs: "",
            )

    def test_mutable_acp_relay_image_is_rejected(self) -> None:
        config = dict(self.config)
        config["acp_relay_image_id"] = (
            "librechat-acp-provider-relay:latest"
        )

        with self.assertRaisesRegex(
            ValueError,
            "pin the validated ACP relay image ID",
        ):
            Broker(
                config,
                runner=lambda *_args, **_kwargs: "",
            )

    def test_mutable_acp_image_is_rejected(self) -> None:
        config = dict(self.config)
        config["acp_image_id"] = "librechat-opencode-acp:latest"

        with self.assertRaisesRegex(
            ValueError,
            "pin the validated ACP sandbox image ID",
        ):
            Broker(config, runner=lambda *_args, **_kwargs: "")


if __name__ == "__main__":
    unittest.main()
