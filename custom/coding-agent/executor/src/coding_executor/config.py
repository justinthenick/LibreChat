from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _absolute_directory(name: str, default: str) -> Path:
    path = Path(os.environ.get(name, default)).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{name} must be an absolute path")
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def _positive_int(name: str, default: int, maximum: int) -> int:
    raw = os.environ.get(name, str(default))
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error
    if value < 1 or value > maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}")
    return value


@dataclass(frozen=True)
class Settings:
    repository_root: Path
    task_root: Path
    bearer_token: str
    public_url: str
    issuer_url: str
    allowed_hosts: tuple[str, ...]
    port: int
    command_timeout_seconds: int
    max_output_bytes: int

    @classmethod
    def from_environment(cls) -> "Settings":
        repository_root = _absolute_directory("CODING_REPOSITORY_ROOT", "/repos")
        task_root = _absolute_directory("CODING_TASK_ROOT", "/tasks")
        if repository_root == task_root:
            raise ValueError("CODING_REPOSITORY_ROOT and CODING_TASK_ROOT must differ")

        token = _required("CODING_EXECUTOR_TOKEN")
        if len(token) < 32:
            raise ValueError("CODING_EXECUTOR_TOKEN must contain at least 32 characters")

        public_url = _required("CODING_EXECUTOR_PUBLIC_URL")
        parsed = urlparse(public_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path != "/mcp":
            raise ValueError("CODING_EXECUTOR_PUBLIC_URL must be an http(s) URL ending in /mcp")

        allowed_hosts = tuple(
            item.strip()
            for item in _required("CODING_EXECUTOR_ALLOWED_HOSTS").split(",")
            if item.strip()
        )
        if not allowed_hosts:
            raise ValueError("CODING_EXECUTOR_ALLOWED_HOSTS must not be empty")

        return cls(
            repository_root=repository_root,
            task_root=task_root,
            bearer_token=token,
            public_url=public_url,
            issuer_url=os.environ.get("CODING_EXECUTOR_ISSUER_URL", "https://librechat.local").strip(),
            allowed_hosts=allowed_hosts,
            port=_positive_int("CODING_EXECUTOR_PORT", 8765, 65535),
            command_timeout_seconds=_positive_int("CODING_COMMAND_TIMEOUT_SECONDS", 300, 1800),
            max_output_bytes=_positive_int("CODING_MAX_OUTPUT_BYTES", 65536, 1048576),
        )
