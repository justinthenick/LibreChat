from __future__ import annotations

from collections.abc import Mapping
import os
import selectors
import signal
import subprocess
import time

_ALLOWED_OVERRIDE_KEYS = frozenset({
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
})


def _environment(env_override: Mapping[str, object] | None) -> dict[str, str]:
    environment = {
        "PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp/coding-agent-home",
        "LANG": "C.UTF-8", "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if env_override is not None:
        if not isinstance(env_override, Mapping):
            raise TypeError(f"Environment override must be a mapping, got {type(env_override).__name__}")
        for key in env_override:
            if not isinstance(key, str):
                raise TypeError(f"Environment override key must be str, got {type(key).__name__}")
            if key not in _ALLOWED_OVERRIDE_KEYS:
                raise ValueError(f"Environment override key not permitted: {key!r}")
        for key, value in env_override.items():
            environment[key] = str(value)
    return environment


def run_bytes(
    argv: list[str],
    *,
    cwd=None,
    timeout: int = 60,
    limit: int = 65536,
    env_override: Mapping[str, object] | None = None,
    accepted_returncodes: tuple[int, ...] = (0,),
) -> bytes:
    """Capture bounded raw output; terminate the process group on overflow or timeout."""
    environment = _environment(env_override)
    if not accepted_returncodes or any(type(code) is not int for code in accepted_returncodes):
        raise ValueError("accepted_returncodes must contain one or more integer exit codes")

    with subprocess.Popen(argv, cwd=cwd, env=environment, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, start_new_session=True) as process:
        chunks = bytearray()
        deadline = time.monotonic() + timeout
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise RuntimeError("maintenance command timed out")
                    for key, _ in selector.select(min(remaining, 0.2)):
                        chunk = os.read(key.fd, 8192)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        chunks.extend(chunk)
                        if len(chunks) > limit:
                            raise RuntimeError("maintenance output limit exceeded")
                process.wait(timeout=max(0.01, deadline - time.monotonic()))
            if process.returncode not in accepted_returncodes:
                raise RuntimeError("maintenance command failed; inspect operator diagnostics")
            return bytes(chunks)
        finally:
            # Also reap background descendants after their parent exits.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()


def run_stdout_bytes(
    argv: list[str],
    *,
    cwd=None,
    timeout: int = 60,
    limit: int = 65536,
    env_override: Mapping[str, object] | None = None,
    accepted_returncodes: tuple[int, ...] = (0,),
) -> bytes:
    """Capture bounded stdout bytes while draining stderr separately."""
    environment = _environment(env_override)
    if not accepted_returncodes or any(type(code) is not int for code in accepted_returncodes):
        raise ValueError("accepted_returncodes must contain one or more integer exit codes")

    with subprocess.Popen(
        argv,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    ) as process:
        stdout_chunks = bytearray()
        total_output = 0
        deadline = time.monotonic() + timeout
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ, data="stdout")
                selector.register(process.stderr, selectors.EVENT_READ, data="stderr")
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise RuntimeError("maintenance command timed out")
                    for key, _ in selector.select(min(remaining, 0.2)):
                        chunk = os.read(key.fd, 8192)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        total_output += len(chunk)
                        if total_output > limit:
                            raise RuntimeError("maintenance output limit exceeded")
                        if key.data == "stdout":
                            stdout_chunks.extend(chunk)
                process.wait(timeout=max(0.01, deadline - time.monotonic()))
            if process.returncode not in accepted_returncodes:
                raise RuntimeError("maintenance command failed; inspect operator diagnostics")
            return bytes(stdout_chunks)
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()


def run(
    argv: list[str],
    *,
    cwd=None,
    timeout: int = 60,
    limit: int = 65536,
    env_override: Mapping[str, object] | None = None,
) -> str:
    """Capture bounded UTF-8 text output; terminate the process group on overflow or timeout."""
    return run_bytes(
        argv,
        cwd=cwd,
        timeout=timeout,
        limit=limit,
        env_override=env_override,
    ).decode("utf-8", errors="replace")
