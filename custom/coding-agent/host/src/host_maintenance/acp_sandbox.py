from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import time
from pathlib import Path
from typing import Callable


TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}")
CONTAINER_PREFIX = "librechat-acp-"

DEFAULT_PIDS_LIMIT = 256
DEFAULT_MEMORY = "1g"
DEFAULT_CPUS = "2"

ACP_NETWORK = "librechat-acp-provider-internal"
ACP_RELAY_CONTAINER = "librechat-acp-provider-relay"
ACP_RELAY_BASE_URL = f"http://{ACP_RELAY_CONTAINER}:8080/v1"
ACP_RELAY_AUDIENCE = ACP_RELAY_CONTAINER
ACP_RELAY_TOKEN_SECONDS = 3900

ACP_PROVIDER_ID = "coding-agent-relay"
ACP_PROVIDER_MODEL = "coding-agent-text"
ACP_RELAY_TOKEN_ENV = "CODING_AGENT_RELAY_TOKEN"

OPENCODE_CONFIG_CONTENT = json.dumps(
    {
        "$schema": "https://opencode.ai/config.json",
        "provider": {
            ACP_PROVIDER_ID: {
                "npm": "@ai-sdk/openai-compatible",
                "name": "LibreChat Contained Provider Relay",
                "options": {
                    "baseURL": ACP_RELAY_BASE_URL,
                    "apiKey": f"{{env:{ACP_RELAY_TOKEN_ENV}}}",
                },
                "models": {
                    ACP_PROVIDER_MODEL: {
                        "name": "Coding Agent Text",
                    },
                },
            },
        },
        "model": f"{ACP_PROVIDER_ID}/{ACP_PROVIDER_MODEL}",
    },
    sort_keys=True,
    separators=(",", ":"),
)

FIXED_ENVIRONMENT = {
    "HOME": "/home/node",
    "OPENCODE_CONFIG_CONTENT": OPENCODE_CONFIG_CONTENT,
    "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
    "OPENCODE_DISABLE_AUTOUPDATE": "true",
    "OPENCODE_DISABLE_DEFAULT_PLUGINS": "true",
}

FORBIDDEN_ENVIRONMENT = {
    "ALL_PROXY",
    "ANTHROPIC_API_KEY",
    "BUN_OPTIONS",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "MISTRAL_API_KEY",
    "NODE_OPTIONS",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
}


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    if (
        not isinstance(value, str)
        or not value
        or re.fullmatch(
            r"[A-Za-z0-9_-]+",
            value,
        )
        is None
    ):
        raise ValueError(
            "invalid base64url encoding"
        )

    padding = "=" * (
        -len(value) % 4
    )

    decoded = (
        base64.urlsafe_b64decode(
            value + padding
        )
    )

    if _b64url_encode(decoded) != value:
        raise ValueError(
            "non-canonical base64url encoding"
        )

    return decoded


class AcpSandboxManager:
    """Construct a fixed-policy disposable ACP sandbox.

    Callers provide task identity only. Image, command, mounts, privileges,
    network, provider routing and resource limits are controlled by reviewed
    configuration/code.

    The sandbox receives a short-lived Broker-issued relay credential. The
    upstream provider credential remains outside the sandbox.
    """

    def __init__(
        self,
        *,
        task_root: Path,
        image: str,
        runner: Callable[..., str],
        task_authorizer: Callable[[str, Path], bool],
        relay_signing_key: bytes,
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
            raise ValueError(
                "task_root must be a canonical absolute host path"
            )

        if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.image):
            raise ValueError(
                "ACP sandbox image must be pinned by immutable sha256 image ID"
            )

        if (
            not isinstance(relay_signing_key, bytes)
            or len(relay_signing_key) < 32
        ):
            raise ValueError(
                "ACP relay signing key must be at least 32 bytes"
            )

        self._relay_signing_key = bytes(relay_signing_key)

    def task_path(self, task_id: str) -> Path:
        if not TASK_ID.fullmatch(task_id):
            raise ValueError("invalid task identifier")

        candidate = self.task_root / task_id

        if not candidate.exists() or not candidate.is_dir():
            raise ValueError("task worktree does not exist")

        if candidate.is_symlink():
            raise ValueError(
                "task worktree must not be a symlink"
            )

        resolved = candidate.resolve()

        if resolved.parent != self.task_root:
            raise ValueError(
                "task worktree escapes configured task root"
            )

        git_marker = resolved / ".git"
        if not git_marker.exists():
            raise ValueError(
                "task path is not a Git worktree"
            )

        if not self.task_authorizer(
            task_id,
            resolved,
        ):
            raise ValueError(
                "task is not an authorized managed worktree"
            )

        return resolved

    @staticmethod
    def container_name(task_id: str) -> str:
        if not TASK_ID.fullmatch(task_id):
            raise ValueError(
                "invalid task identifier"
            )

        return f"{CONTAINER_PREFIX}{task_id}"

    def _issue_relay_token(
        self,
        task_id: str,
    ) -> str:
        if not TASK_ID.fullmatch(task_id):
            raise ValueError(
                "invalid task identifier"
            )

        issued_at = int(time.time())

        claims = {
            "v": 1,
            "aud": ACP_RELAY_AUDIENCE,
            "task": task_id,
            "model": ACP_PROVIDER_MODEL,
            "iat": issued_at,
            "exp": issued_at + ACP_RELAY_TOKEN_SECONDS,
            "nonce": secrets.token_urlsafe(18),
        }

        payload = json.dumps(
            claims,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        encoded = _b64url_encode(payload)

        signature = hmac.new(
            self._relay_signing_key,
            f"v1.{encoded}".encode("ascii"),
            hashlib.sha256,
        ).digest()

        return (
            "v1."
            + encoded
            + "."
            + _b64url_encode(signature)
        )

    def _validate_relay_token(
        self,
        token: str,
        task_id: str,
    ) -> dict:
        if not isinstance(token, str):
            raise RuntimeError(
                "ACP relay token is missing"
            )

        parts = token.split(".")

        if (
            len(parts) != 3
            or parts[0] != "v1"
        ):
            raise RuntimeError(
                "ACP relay token format mismatch"
            )

        encoded = parts[1]

        try:
            supplied_signature = _b64url_decode(
                parts[2]
            )
        except Exception as exc:
            raise RuntimeError(
                "ACP relay token signature encoding mismatch"
            ) from exc

        expected_signature = hmac.new(
            self._relay_signing_key,
            f"v1.{encoded}".encode("ascii"),
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(
            supplied_signature,
            expected_signature,
        ):
            raise RuntimeError(
                "ACP relay token signature mismatch"
            )

        try:
            claims = json.loads(
                _b64url_decode(encoded)
            )
        except Exception as exc:
            raise RuntimeError(
                "ACP relay token claims are invalid"
            ) from exc

        if not isinstance(claims, dict):
            raise RuntimeError(
                "ACP relay token claims are invalid"
            )

        if (
            claims.get("v") != 1
            or claims.get("aud")
            != ACP_RELAY_AUDIENCE
            or claims.get("task") != task_id
            or claims.get("model")
            != ACP_PROVIDER_MODEL
        ):
            raise RuntimeError(
                "ACP relay token claims mismatch"
            )

        issued_at = claims.get("iat")
        expires_at = claims.get("exp")
        nonce = claims.get("nonce")

        if (
            isinstance(issued_at, bool)
            or not isinstance(issued_at, int)
            or isinstance(expires_at, bool)
            or not isinstance(expires_at, int)
            or expires_at - issued_at
            != ACP_RELAY_TOKEN_SECONDS
            or not isinstance(nonce, str)
            or not re.fullmatch(
                r"[A-Za-z0-9_-]{20,64}",
                nonce,
            )
        ):
            raise RuntimeError(
                "ACP relay token lifetime or nonce mismatch"
            )

        now = int(time.time())

        if issued_at > now + 30:
            raise RuntimeError(
                "ACP relay token is issued in the future"
            )

        if expires_at <= now:
            raise RuntimeError(
                "ACP relay token is expired"
            )

        return claims

    def _validate_network_policy(
        self,
    ) -> None:
        raw = self.runner([
            "/usr/bin/docker",
            "network",
            "inspect",
            ACP_NETWORK,
        ])

        try:
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                "ACP provider network inspection failed"
            ) from exc

        if (
            not isinstance(data, list)
            or len(data) != 1
        ):
            raise RuntimeError(
                "unexpected ACP provider network inspect response"
            )

        info = data[0]

        if (
            info.get("Name") != ACP_NETWORK
            or info.get("Driver") != "bridge"
            or info.get("Internal") is not True
            or info.get("Attachable") is True
            or info.get("Ingress") is True
        ):
            raise RuntimeError(
                "ACP provider network identity or isolation mismatch"
            )

        options = info.get("Options") or {}

        if (
            options.get(
                "com.docker.network.bridge.gateway_mode_ipv4"
            )
            != "isolated"
            or options.get(
                "com.docker.network.enable_ipv6",
                "false",
            )
            == "true"
        ):
            raise RuntimeError(
                "ACP provider network gateway policy mismatch"
            )

    def _environment(
        self,
        task_id: str,
    ) -> dict[str, str]:
        return {
            **FIXED_ENVIRONMENT,
            ACP_RELAY_TOKEN_ENV:
                self._issue_relay_token(task_id),
        }

    def create_argv(
        self,
        task_id: str,
    ) -> list[str]:
        workspace = self.task_path(task_id)
        name = self.container_name(task_id)

        environment = self._environment(
            task_id
        )

        argv = [
            "/usr/bin/docker",
            "create",
            "--name",
            name,
            "--interactive",
            "--read-only",
            "--network",
            ACP_NETWORK,
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
        ]

        for key, value in environment.items():
            argv.extend([
                "--env",
                f"{key}={value}",
            ])

        argv.extend([
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,noexec,size=256m",
            "--tmpfs",
            (
                "/home/node:"
                "rw,nosuid,nodev,noexec,size=256m,"
                "uid=1000,gid=1000,mode=0700"
            ),
            "--mount",
            (
                f"type=bind,src={workspace},"
                "dst=/workspace"
            ),
            "--workdir",
            "/workspace",
            self.image,
            "opencode",
            "acp",
            "--pure",
            "--cwd",
            "/workspace",
        ])

        return argv

    def create(
        self,
        task_id: str,
    ) -> str:
        """Create, but do not start, the fixed-policy sandbox."""
        self._validate_network_policy()

        argv = self.create_argv(task_id)

        insert_at = argv.index(
            "--read-only"
        )

        argv[
            insert_at:insert_at
        ] = [
            "--label",
            (
                "com.librechat.coding-agent."
                "kind=acp-sandbox"
            ),
            "--label",
            (
                "com.librechat.coding-agent."
                f"task={task_id}"
            ),
        ]

        return self.runner(argv).strip()

    def inspect(
        self,
        task_id: str,
    ) -> dict:
        """Inspect and validate an existing sandbox before trusting it."""
        self._validate_network_policy()

        name = self.container_name(task_id)

        raw = self.runner([
            "/usr/bin/docker",
            "inspect",
            name,
        ])

        data = json.loads(raw)

        if (
            not isinstance(data, list)
            or len(data) != 1
        ):
            raise RuntimeError(
                "unexpected Docker inspect response"
            )

        info = data[0]
        self._validate_inspect(
            task_id,
            info,
        )

        return info

    def _validate_inspect(
        self,
        task_id: str,
        info: dict,
    ) -> None:
        workspace = self.task_path(task_id)
        expected_name = (
            "/"
            + self.container_name(task_id)
        )

        if info.get("Name") != expected_name:
            raise RuntimeError(
                "ACP sandbox container identity mismatch"
            )

        if (
            info.get("Config", {}).get("Image")
            != self.image
        ):
            raise RuntimeError(
                "ACP sandbox image mismatch"
            )

        labels = (
            info.get("Config", {})
            .get("Labels")
            or {}
        )

        if (
            labels.get(
                "com.librechat.coding-agent.kind"
            )
            != "acp-sandbox"
        ):
            raise RuntimeError(
                "ACP sandbox kind label mismatch"
            )

        if (
            labels.get(
                "com.librechat.coding-agent.task"
            )
            != task_id
        ):
            raise RuntimeError(
                "ACP sandbox task label mismatch"
            )

        config = info.get("Config", {})

        if config.get("OpenStdin") is not True:
            raise RuntimeError(
                "ACP sandbox stdin must remain open"
            )

        if config.get("StdinOnce") is not True:
            raise RuntimeError(
                "ACP sandbox stdin-once policy mismatch"
            )

        if config.get("User") != "1000:1000":
            raise RuntimeError(
                "ACP sandbox must run as the reviewed non-root user"
            )

        if (
            config.get("WorkingDir")
            != "/workspace"
        ):
            raise RuntimeError(
                "ACP sandbox working directory mismatch"
            )

        expected_cmd = [
            "opencode",
            "acp",
            "--pure",
            "--cwd",
            "/workspace",
        ]

        if config.get("Cmd") != expected_cmd:
            raise RuntimeError(
                "ACP sandbox command mismatch"
            )

        environment = {}

        for item in config.get("Env", []) or []:
            if (
                not isinstance(item, str)
                or "=" not in item
            ):
                raise RuntimeError(
                    "ACP sandbox environment is malformed"
                )

            key, value = item.split(
                "=",
                1,
            )

            environment[key] = value

        for key, expected in FIXED_ENVIRONMENT.items():
            if environment.get(key) != expected:
                raise RuntimeError(
                    "ACP sandbox OpenCode environment mismatch"
                )

        token = environment.get(
            ACP_RELAY_TOKEN_ENV
        )

        self._validate_relay_token(
            token,
            task_id,
        )

        if (
            FORBIDDEN_ENVIRONMENT
            & set(environment)
        ):
            raise RuntimeError(
                "ACP sandbox contains forbidden provider or runtime environment"
            )

        host = info.get("HostConfig", {})

        if (
            host.get("ReadonlyRootfs")
            is not True
        ):
            raise RuntimeError(
                "ACP sandbox root filesystem is not read-only"
            )

        if (
            host.get("NetworkMode")
            != ACP_NETWORK
        ):
            raise RuntimeError(
                "ACP sandbox network policy mismatch"
            )

        networks = (
            info.get("NetworkSettings", {})
            .get("Networks")
            or {}
        )

        if set(networks) != {
            ACP_NETWORK
        }:
            raise RuntimeError(
                "ACP sandbox network attachment mismatch"
            )

        if (
            host.get("PidMode")
            not in ("", None)
        ):
            raise RuntimeError(
                "ACP sandbox PID namespace policy mismatch"
            )

        if (
            host.get("IpcMode")
            not in ("", "private", None)
        ):
            raise RuntimeError(
                "ACP sandbox IPC namespace policy mismatch"
            )

        if (
            host.get("UTSMode")
            not in ("", None)
        ):
            raise RuntimeError(
                "ACP sandbox UTS namespace policy mismatch"
            )

        if host.get("Privileged") is True:
            raise RuntimeError(
                "ACP sandbox must not be privileged"
            )

        if host.get("CapAdd"):
            raise RuntimeError(
                "ACP sandbox has unexpected added capabilities"
            )

        if (
            "ALL"
            not in (
                host.get("CapDrop")
                or []
            )
        ):
            raise RuntimeError(
                "ACP sandbox must drop all capabilities"
            )

        if (
            "no-new-privileges"
            not in (
                host.get("SecurityOpt")
                or []
            )
        ):
            raise RuntimeError(
                "ACP sandbox missing no-new-privileges"
            )

        if (
            host.get("PidsLimit")
            != DEFAULT_PIDS_LIMIT
        ):
            raise RuntimeError(
                "ACP sandbox PID limit mismatch"
            )

        if (
            host.get("Memory")
            != 1073741824
        ):
            raise RuntimeError(
                "ACP sandbox memory limit mismatch"
            )

        if (
            host.get("MemorySwap")
            != 1073741824
        ):
            raise RuntimeError(
                "ACP sandbox memory-swap limit mismatch"
            )

        if (
            host.get("NanoCpus")
            != 2_000_000_000
        ):
            raise RuntimeError(
                "ACP sandbox CPU limit mismatch"
            )

        tmpfs = host.get("Tmpfs") or {}

        expected_tmpfs = {
            "/tmp":
                "rw,nosuid,nodev,noexec,size=256m",
            "/home/node": (
                "rw,nosuid,nodev,noexec,size=256m,"
                "uid=1000,gid=1000,mode=0700"
            ),
        }

        if tmpfs != expected_tmpfs:
            raise RuntimeError(
                "ACP sandbox tmpfs policy mismatch"
            )

        restart = (
            host.get("RestartPolicy")
            or {}
        )

        if restart.get("Name", "") != "no":
            raise RuntimeError(
                "ACP sandbox restart policy mismatch"
            )

        mounts = info.get("Mounts") or []

        if len(mounts) != 1:
            raise RuntimeError(
                "ACP sandbox must have exactly one host mount"
            )

        mount = mounts[0]

        if (
            mount.get("Type") != "bind"
            or Path(
                mount.get("Source", "")
            ).resolve()
            != workspace
            or mount.get("Destination")
            != "/workspace"
            or mount.get("RW")
            is not True
        ):
            raise RuntimeError(
                "ACP sandbox workspace mount mismatch"
            )

    def start(
        self,
        task_id: str,
    ) -> None:
        """Start only a container that still matches reviewed policy."""
        self.inspect(task_id)

        self.runner([
            "/usr/bin/docker",
            "start",
            self.container_name(task_id),
        ])

    def remove(
        self,
        task_id: str,
    ) -> None:
        """Remove only a container that still matches reviewed policy."""
        self.inspect(task_id)

        self.runner([
            "/usr/bin/docker",
            "rm",
            "--force",
            self.container_name(task_id),
        ])
