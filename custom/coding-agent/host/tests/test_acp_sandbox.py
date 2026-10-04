from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from host_maintenance.acp_sandbox import AcpSandboxManager


class AcpSandboxManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name).resolve()
        self.tasks = root / "tasks"
        self.tasks.mkdir()

        self.task_id = "contained-acp-runtime-test"
        self.task = self.tasks / self.task_id
        self.task.mkdir()
        (self.task / ".git").write_text("gitdir: /tmp/example\n", encoding="utf-8")

        self.calls: list[list[str]] = []

        def runner(argv, **_kwargs):
            self.calls.append(list(argv))
            return ""

        self.authorized = {self.task_id: self.task}

        def task_authorizer(task_id: str, path: Path) -> bool:
            return self.authorized.get(task_id) == path

        self.manager = AcpSandboxManager(
            task_root=self.tasks,
            image="sha256:" + "a" * 64,
            runner=runner,
            task_authorizer=task_authorizer,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_requires_immutable_image_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "immutable sha256"):
            AcpSandboxManager(
                task_root=self.tasks,
                image="opencode:test",
                runner=lambda *_args, **_kwargs: "",
                task_authorizer=lambda *_args: True,
            )

    def test_rejects_invalid_task_identifier(self) -> None:
        for task_id in ("", "../escape", "/absolute", "bad task", "a" * 81):
            with self.subTest(task_id=task_id):
                with self.assertRaises(ValueError):
                    self.manager.task_path(task_id)

    def test_rejects_missing_task(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.manager.task_path("missing-task")

    def test_rejects_symlink_task(self) -> None:
        real = self.tasks / "real-task"
        real.mkdir()
        (real / ".git").write_text("gitdir: /tmp/example\n", encoding="utf-8")
        (self.tasks / "linked-task").symlink_to(real, target_is_directory=True)

        with self.assertRaisesRegex(ValueError, "symlink"):
            self.manager.task_path("linked-task")

    def test_rejects_non_worktree_directory(self) -> None:
        plain = self.tasks / "plain-task"
        plain.mkdir()

        with self.assertRaisesRegex(ValueError, "Git worktree"):
            self.manager.task_path("plain-task")

    def test_rejects_unregistered_git_worktree(self) -> None:
        rogue = self.tasks / "rogue-task"
        rogue.mkdir()
        (rogue / ".git").write_text(
            "gitdir: /tmp/example\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "authorized managed worktree"):
            self.manager.task_path("rogue-task")

    def test_create_policy_is_fixed_and_task_scoped(self) -> None:
        argv = self.manager.create_argv(self.task_id)
        joined = " ".join(argv)

        self.assertEqual(argv[:2], ["/usr/bin/docker", "create"])
        self.assertIn("--read-only", argv)
        self.assertIn("--network", argv)
        self.assertEqual(argv[argv.index("--network") + 1], "none")
        self.assertEqual(argv[argv.index("--user") + 1], "1000:1000")
        self.assertEqual(argv[argv.index("--cap-drop") + 1], "ALL")
        self.assertEqual(
            argv[argv.index("--security-opt") + 1],
            "no-new-privileges",
        )
        self.assertEqual(argv[argv.index("--pids-limit") + 1], "256")
        self.assertEqual(argv[argv.index("--memory") + 1], "1g")
        self.assertEqual(argv[argv.index("--memory-swap") + 1], "1g")
        self.assertEqual(argv[argv.index("--cpus") + 1], "2")

        mount = argv[argv.index("--mount") + 1]
        self.assertEqual(
            mount,
            f"type=bind,src={self.task},dst=/workspace",
        )

        self.assertNotIn("/var/run/docker.sock", joined)
        self.assertNotIn(".ssh", joined)
        self.assertNotIn(".codex", joined)

        self.assertEqual(
            argv[-5:],
            ["opencode", "acp", "--pure", "--cwd", "/workspace"],
        )

    def test_caller_cannot_supply_mount_command_or_network(self) -> None:
        with self.assertRaises(TypeError):
            self.manager.create_argv(
                self.task_id,
                network="host",
                command=["sh"],
                mounts=["/:/host"],
            )


if __name__ == "__main__":
    unittest.main()


class AcpSandboxLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name).resolve()
        self.tasks = root / "tasks"
        self.tasks.mkdir()

        self.task_id = "lifecycle-task"
        self.task = self.tasks / self.task_id
        self.task.mkdir()
        (self.task / ".git").write_text(
            "gitdir: /tmp/example\n",
            encoding="utf-8",
        )

        self.calls = []
        self.inspect_data = {
            "Name": "/librechat-acp-lifecycle-task",
            "Config": {
                "Image": "sha256:" + "a" * 64,
                "OpenStdin": True,
                "StdinOnce": True,
                "User": "1000:1000",
                "WorkingDir": "/workspace",
                "Cmd": [
                    "opencode",
                    "acp",
                    "--pure",
                    "--cwd",
                    "/workspace",
                ],
                "Labels": {
                    "com.librechat.coding-agent.kind": "acp-sandbox",
                    "com.librechat.coding-agent.task": self.task_id,
                },
            },
            "HostConfig": {
                "ReadonlyRootfs": True,
                "NetworkMode": "none",
                "PidMode": "",
                "IpcMode": "private",
                "UTSMode": "",
                "Privileged": False,
                "CapAdd": None,
                "CapDrop": ["ALL"],
                "SecurityOpt": ["no-new-privileges"],
                "PidsLimit": 256,
                "Memory": 1073741824,
                "MemorySwap": 1073741824,
                "NanoCpus": 2000000000,
                "Tmpfs": {
                    "/tmp": "rw,nosuid,nodev,noexec,size=256m",
                    "/home/node": "rw,nosuid,nodev,noexec,size=256m,uid=1000,gid=1000,mode=0700",
                },
                "RestartPolicy": {
                    "Name": "no",
                    "MaximumRetryCount": 0,
                },
            },
            "Mounts": [{
                "Type": "bind",
                "Source": str(self.task),
                "Destination": "/workspace",
                "RW": True,
            }],
        }

        def runner(argv, **_kwargs):
            import json

            argv = list(argv)
            self.calls.append(argv)

            if argv[1] == "inspect":
                return json.dumps([self.inspect_data])

            if argv[1] == "create":
                return "container-id\n"

            return ""

        self.manager = AcpSandboxManager(
            task_root=self.tasks,
            image="sha256:" + "a" * 64,
            runner=runner,
            task_authorizer=lambda task_id, path: (
                task_id == self.task_id and path == self.task
            ),
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_create_keeps_acp_stdin_open(self) -> None:
        self.manager.create(self.task_id)

        argv = self.calls[-1]
        self.assertIn("--interactive", argv)

    def test_inspect_rejects_closed_stdin(self) -> None:
        self.inspect_data["Config"]["OpenStdin"] = False

        with self.assertRaisesRegex(RuntimeError, "stdin must remain open"):
            self.manager.inspect(self.task_id)

    def test_inspect_rejects_stdin_once_drift(self) -> None:
        self.inspect_data["Config"]["StdinOnce"] = False

        with self.assertRaisesRegex(RuntimeError, "stdin-once policy"):
            self.manager.inspect(self.task_id)

    def test_create_adds_fixed_identity_labels(self) -> None:
        result = self.manager.create(self.task_id)

        self.assertEqual(result, "container-id")
        argv = self.calls[-1]

        self.assertIn(
            "com.librechat.coding-agent.kind=acp-sandbox",
            argv,
        )
        self.assertIn(
            f"com.librechat.coding-agent.task={self.task_id}",
            argv,
        )

    def test_start_revalidates_before_mutation(self) -> None:
        self.manager.start(self.task_id)

        self.assertEqual(self.calls[-2][1], "inspect")
        self.assertEqual(
            self.calls[-1],
            [
                "/usr/bin/docker",
                "start",
                "librechat-acp-lifecycle-task",
            ],
        )

    def test_remove_revalidates_before_mutation(self) -> None:
        self.manager.remove(self.task_id)

        self.assertEqual(self.calls[-2][1], "inspect")
        self.assertEqual(
            self.calls[-1],
            [
                "/usr/bin/docker",
                "rm",
                "--force",
                "librechat-acp-lifecycle-task",
            ],
        )

    def test_start_fails_closed_on_network_drift(self) -> None:
        self.inspect_data["HostConfig"]["NetworkMode"] = "bridge"

        with self.assertRaisesRegex(RuntimeError, "network policy"):
            self.manager.start(self.task_id)

        self.assertEqual(self.calls[-1][1], "inspect")
        self.assertFalse(any(call[1] == "start" for call in self.calls))

    def test_remove_fails_closed_on_mount_drift(self) -> None:
        self.inspect_data["Mounts"].append({
            "Type": "bind",
            "Source": "/home/example/.ssh",
            "Destination": "/host-ssh",
            "RW": True,
        })

        with self.assertRaisesRegex(RuntimeError, "exactly one host mount"):
            self.manager.remove(self.task_id)

        self.assertEqual(self.calls[-1][1], "inspect")
        self.assertFalse(any(call[1] == "rm" for call in self.calls))

    def test_inspect_rejects_image_drift(self) -> None:
        self.inspect_data["Config"]["Image"] = "sha256:" + "b" * 64

        with self.assertRaisesRegex(RuntimeError, "image mismatch"):
            self.manager.inspect(self.task_id)

    def test_inspect_rejects_workdir_drift(self) -> None:
        self.inspect_data["Config"]["WorkingDir"] = "/"

        with self.assertRaisesRegex(RuntimeError, "working directory"):
            self.manager.inspect(self.task_id)

    def test_inspect_rejects_tmpfs_drift(self) -> None:
        self.inspect_data["HostConfig"]["Tmpfs"]["/tmp"] = "rw"

        with self.assertRaisesRegex(RuntimeError, "tmpfs policy"):
            self.manager.inspect(self.task_id)

    def test_inspect_rejects_privileged_container(self) -> None:
        self.inspect_data["HostConfig"]["Privileged"] = True

        with self.assertRaisesRegex(RuntimeError, "must not be privileged"):
            self.manager.inspect(self.task_id)

    def test_inspect_rejects_added_capabilities(self) -> None:
        self.inspect_data["HostConfig"]["CapAdd"] = ["SYS_ADMIN"]

        with self.assertRaisesRegex(RuntimeError, "added capabilities"):
            self.manager.inspect(self.task_id)
