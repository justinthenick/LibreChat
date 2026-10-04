from __future__ import annotations

import re
from pathlib import Path
from typing import Callable


TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}")
CONTAINER_PREFIX = "librechat-acp-"

DEFAULT_PIDS_LIMIT = 256
DEFAULT_MEMORY = "1g"
DEFAULT_CPUS = "2"


class AcpSandboxManager:
    """Construct a fixed-policy disposable ACP sandbox.

    Callers provide task identity only. Image, command, mounts, privileges,
    network and resource limits are controlled by reviewed configuration/code.
    """

    def __init__(
        self,
        *,
        task_root: Path,
        image: str,
        runner: Callable[..., str],
        task_authorizer: Callable[[str, Path], bool],
    ) -> None:
        self.task_root = Path(task_root)
        self.image = image
        self.runner = runner
        self.task_authorizer = task_authorizer

        if (
            not self.task_root.is_absolute()
            or self.task_root.is_symlink()
            or self.task_root.resolve() != self.task_root
        ):
            raise ValueError("task_root must be a canonical absolute host path")

        if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.image):
            raise ValueError(
                "ACP sandbox image must be pinned by immutable sha256 image ID"
            )

    def task_path(self, task_id: str) -> Path:
        if not TASK_ID.fullmatch(task_id):
            raise ValueError("invalid task identifier")

        candidate = self.task_root / task_id

        if not candidate.exists() or not candidate.is_dir():
            raise ValueError("task worktree does not exist")

        if candidate.is_symlink():
            raise ValueError("task worktree must not be a symlink")

        resolved = candidate.resolve()

        if resolved.parent != self.task_root:
            raise ValueError("task worktree escapes configured task root")

        git_marker = resolved / ".git"
        if not git_marker.exists():
            raise ValueError("task path is not a Git worktree")

        if not self.task_authorizer(task_id, resolved):
            raise ValueError("task is not an authorized managed worktree")

        return resolved

    @staticmethod
    def container_name(task_id: str) -> str:
        if not TASK_ID.fullmatch(task_id):
            raise ValueError("invalid task identifier")
        return f"{CONTAINER_PREFIX}{task_id}"

    def create_argv(self, task_id: str) -> list[str]:
        workspace = self.task_path(task_id)
        name = self.container_name(task_id)

        return [
            "/usr/bin/docker",
            "create",
            "--name",
            name,
            "--interactive",
            "--read-only",
            "--network",
            "none",
            "--user",
            "1000:1000",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            str(DEFAULT_PIDS_LIMIT),
            "--memory",
            DEFAULT_MEMORY,
            "--memory-swap",
            DEFAULT_MEMORY,
            "--cpus",
            DEFAULT_CPUS,
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,noexec,size=256m",
            "--tmpfs",
            "/home/node:rw,nosuid,nodev,noexec,size=256m,uid=1000,gid=1000,mode=0700",
            "--mount",
            f"type=bind,src={workspace},dst=/workspace",
            "--workdir",
            "/workspace",
            self.image,
            "opencode",
            "acp",
            "--pure",
            "--cwd",
            "/workspace",
        ]


    def create(self, task_id: str) -> str:
        """Create, but do not start, the fixed-policy sandbox."""
        argv = self.create_argv(task_id)

        insert_at = argv.index("--read-only")
        argv[insert_at:insert_at] = [
            "--label",
            "com.librechat.coding-agent.kind=acp-sandbox",
            "--label",
            f"com.librechat.coding-agent.task={task_id}",
        ]

        return self.runner(argv).strip()

    def inspect(self, task_id: str) -> dict:
        """Inspect and validate an existing sandbox before trusting it."""
        import json

        name = self.container_name(task_id)
        raw = self.runner([
            "/usr/bin/docker",
            "inspect",
            name,
        ])

        data = json.loads(raw)
        if not isinstance(data, list) or len(data) != 1:
            raise RuntimeError("unexpected Docker inspect response")

        info = data[0]
        self._validate_inspect(task_id, info)
        return info

    def _validate_inspect(self, task_id: str, info: dict) -> None:
        workspace = self.task_path(task_id)
        expected_name = "/" + self.container_name(task_id)

        if info.get("Name") != expected_name:
            raise RuntimeError("ACP sandbox container identity mismatch")

        if info.get("Config", {}).get("Image") != self.image:
            raise RuntimeError("ACP sandbox image mismatch")

        labels = info.get("Config", {}).get("Labels") or {}
        if labels.get("com.librechat.coding-agent.kind") != "acp-sandbox":
            raise RuntimeError("ACP sandbox kind label mismatch")
        if labels.get("com.librechat.coding-agent.task") != task_id:
            raise RuntimeError("ACP sandbox task label mismatch")

        config = info.get("Config", {})

        if config.get("OpenStdin") is not True:
            raise RuntimeError("ACP sandbox stdin must remain open")

        if config.get("StdinOnce") is not True:
            raise RuntimeError("ACP sandbox stdin-once policy mismatch")
        if config.get("User") != "1000:1000":
            raise RuntimeError("ACP sandbox must run as the reviewed non-root user")

        if config.get("WorkingDir") != "/workspace":
            raise RuntimeError("ACP sandbox working directory mismatch")

        expected_cmd = [
            "opencode",
            "acp",
            "--pure",
            "--cwd",
            "/workspace",
        ]
        if config.get("Cmd") != expected_cmd:
            raise RuntimeError("ACP sandbox command mismatch")

        host = info.get("HostConfig", {})

        if host.get("ReadonlyRootfs") is not True:
            raise RuntimeError("ACP sandbox root filesystem is not read-only")

        if host.get("NetworkMode") != "none":
            raise RuntimeError("ACP sandbox network policy mismatch")

        if host.get("PidMode") not in ("", None):
            raise RuntimeError("ACP sandbox PID namespace policy mismatch")

        if host.get("IpcMode") not in ("", "private", None):
            raise RuntimeError("ACP sandbox IPC namespace policy mismatch")

        if host.get("UTSMode") not in ("", None):
            raise RuntimeError("ACP sandbox UTS namespace policy mismatch")

        if host.get("Privileged") is True:
            raise RuntimeError("ACP sandbox must not be privileged")

        if host.get("CapAdd"):
            raise RuntimeError("ACP sandbox has unexpected added capabilities")

        if "ALL" not in (host.get("CapDrop") or []):
            raise RuntimeError("ACP sandbox must drop all capabilities")

        if "no-new-privileges" not in (host.get("SecurityOpt") or []):
            raise RuntimeError("ACP sandbox missing no-new-privileges")

        if host.get("PidsLimit") != DEFAULT_PIDS_LIMIT:
            raise RuntimeError("ACP sandbox PID limit mismatch")

        if host.get("Memory") != 1073741824:
            raise RuntimeError("ACP sandbox memory limit mismatch")

        if host.get("MemorySwap") != 1073741824:
            raise RuntimeError("ACP sandbox memory-swap limit mismatch")

        if host.get("NanoCpus") != 2_000_000_000:
            raise RuntimeError("ACP sandbox CPU limit mismatch")

        tmpfs = host.get("Tmpfs") or {}
        expected_tmpfs = {
            "/tmp": "rw,nosuid,nodev,noexec,size=256m",
            "/home/node": "rw,nosuid,nodev,noexec,size=256m,uid=1000,gid=1000,mode=0700",
        }
        if tmpfs != expected_tmpfs:
            raise RuntimeError("ACP sandbox tmpfs policy mismatch")

        restart = host.get("RestartPolicy") or {}
        if restart.get("Name", "") != "no":
            raise RuntimeError("ACP sandbox restart policy mismatch")

        mounts = info.get("Mounts") or []
        if len(mounts) != 1:
            raise RuntimeError("ACP sandbox must have exactly one host mount")

        mount = mounts[0]
        if (
            mount.get("Type") != "bind"
            or Path(mount.get("Source", "")).resolve() != workspace
            or mount.get("Destination") != "/workspace"
            or mount.get("RW") is not True
        ):
            raise RuntimeError("ACP sandbox workspace mount mismatch")

    def start(self, task_id: str) -> None:
        """Start only a container that still matches reviewed policy."""
        self.inspect(task_id)
        self.runner([
            "/usr/bin/docker",
            "start",
            self.container_name(task_id),
        ])

    def remove(self, task_id: str) -> None:
        """Remove only a container that still matches reviewed policy."""
        self.inspect(task_id)
        self.runner([
            "/usr/bin/docker",
            "rm",
            "--force",
            self.container_name(task_id),
        ])
