from __future__ import annotations

import hashlib

import json
import os
import socket
import subprocess
from pathlib import Path


ROOT = (
    Path.home()
    / ".local"
    / "share"
    / "coding-maintenance"
    / "codex-adapter"
)

SOCKET = Path(
    os.environ.get(
        "CODEX_ADAPTER_SOCKET",
        str(ROOT / "run" / "codex.sock"),
    )
)

CODEX = Path(
    os.environ.get(
        "CODEX_ADAPTER_CODEX",
        str(
            Path.home()
            / ".local"
            / "bin"
            / "codex"
        ),
    )
)

WORKSPACE = Path(
    os.environ.get(
        "CODEX_ADAPTER_WORKSPACE",
        str(ROOT / "workspace"),
    )
)

MAX_REQUEST = 64 * 1024
MAX_PROMPT = 32 * 1024
MAX_RESPONSE = 1024 * 1024

TIMEOUT_SECONDS = 120

ALLOWED_ITEM_TYPES = {
    "agent_message",
    "reasoning",
}



CODEX_EXPECTED_VERSION = "codex-cli 0.154.0"
CODEX_EXPECTED_SHA256 = (
    "3188814c35471432d4123203e0eb38e5bddc60226e3d7ddf0e59e649ea140022"
)


def _validate_codex_identity(
    path: Path | None = None,
) -> Path:
    candidate = Path(
        path if path is not None else CODEX
    ).expanduser()

    try:
        resolved = candidate.resolve(
            strict=True
        )
    except OSError as exc:
        raise RuntimeError(
            "reviewed Codex executable is unavailable"
        ) from exc

    if (
        not resolved.is_file()
        or not os.access(
            resolved,
            os.X_OK,
        )
    ):
        raise RuntimeError(
            "reviewed Codex executable is unavailable"
        )

    digest = hashlib.sha256()

    with resolved.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    if (
        digest.hexdigest()
        != CODEX_EXPECTED_SHA256
    ):
        raise RuntimeError(
            "Codex executable identity mismatch"
        )

    try:
        result = subprocess.run(
            [
                str(resolved),
                "--version",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:
        raise RuntimeError(
            "Codex executable version check failed"
        ) from exc

    if (
        result.returncode != 0
        or result.stdout.strip()
        != CODEX_EXPECTED_VERSION
    ):
        raise RuntimeError(
            "Codex executable version mismatch"
        )

    return resolved

def log(
    message: str,
) -> None:
    print(
        message,
        flush=True,
    )


def recv_request(
    connection: socket.socket,
) -> dict:
    data = bytearray()

    while True:
        chunk = connection.recv(
            min(
                8192,
                MAX_REQUEST - len(data),
            )
        )

        if not chunk:
            break

        data.extend(chunk)

        if len(data) >= MAX_REQUEST:
            raise ValueError(
                "request too large"
            )

    if not data:
        raise ValueError(
            "empty request"
        )

    request = json.loads(
        data.decode("utf-8")
    )

    if not isinstance(
        request,
        dict,
    ):
        raise ValueError(
            "request must be object"
        )

    if set(request) != {
        "prompt"
    }:
        raise ValueError(
            "unsupported fields"
        )

    return request


def send_response(
    connection: socket.socket,
    payload: dict,
) -> None:
    encoded = (
        json.dumps(
            payload,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")

    if len(encoded) > MAX_RESPONSE:
        raise RuntimeError(
            "response too large"
        )

    connection.sendall(
        encoded
    )


def hardened_command(
    prompt: str,
) -> list[str]:
    return [
        str(CODEX),
        "exec",
        "--json",
        "--ephemeral",
        "--strict-config",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--cd",
        str(WORKSPACE),

        "-c",
        "features.shell_tool=false",

        "-c",
        "features.unified_exec=false",

        "-c",
        "features.unified_exec_tty=false",

        "-c",
        "features.view_image=false",

        "-c",
        "features.shell_snapshot=false",

        "-c",
        "features.sleep_tool=false",

        "-c",
        "features.standalone_web_search=false",

        "-c",
        "features.plugins=false",

        "-c",
        "features.apps=false",

        "-c",
        'web_search="disabled"',

        "-c",
        "mcp_servers={}",

        "-c",
        "include_apps_instructions=false",

        (
            "You are operating as a bounded "
            "text-generation backend. "
            "Use only the text-generation capability "
            "provided by this session. "
            "Return the requested answer.\n\n"
            "USER REQUEST:\n"
            + prompt
        ),
    ]


def run_codex(
    prompt: str,
) -> dict:
    if (
        not isinstance(prompt, str)
        or not prompt.strip()
    ):
        raise ValueError(
            "prompt must be non-empty"
        )

    if len(
        prompt.encode("utf-8")
    ) > MAX_PROMPT:
        raise ValueError(
            "prompt too large"
        )

    try:
        result = subprocess.run(
            hardened_command(prompt),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=TIMEOUT_SECONDS,
            env=os.environ.copy(),
        )

    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "upstream_timeout",
        }

    events = []

    for raw in result.stdout.splitlines():
        raw = raw.strip()

        if not raw:
            continue

        try:
            event = json.loads(raw)

        except json.JSONDecodeError:
            return {
                "ok": False,
                "error": "invalid_codex_output",
            }

        if isinstance(
            event,
            dict,
        ):
            events.append(event)

    failure_messages = []

    for event in events:
        if event.get("type") in {
            "error",
            "turn.failed",
        }:
            message = event.get(
                "message"
            )

            if not message:
                error = event.get(
                    "error"
                )

                if isinstance(
                    error,
                    dict,
                ):
                    message = error.get(
                        "message"
                    )

            if isinstance(
                message,
                str,
            ):
                failure_messages.append(
                    message
                )

    combined_failure = " ".join(
        failure_messages
    ).lower()

    if (
        "usage limit"
        in combined_failure
        or "purchase more credits"
        in combined_failure
    ):
        return {
            "ok": False,
            "error": "upstream_quota",
        }

    if (
        "log in again"
        in combined_failure
        or (
            "token"
            in combined_failure
            and "expired"
            in combined_failure
        )
    ):
        return {
            "ok": False,
            "error": "upstream_auth",
        }

    observed_item_types = set()

    for event in events:
        item = event.get(
            "item"
        )

        if not isinstance(
            item,
            dict,
        ):
            continue

        item_type = item.get(
            "type"
        )

        if isinstance(
            item_type,
            str,
        ):
            observed_item_types.add(
                item_type
            )

    unexpected = (
        observed_item_types
        - ALLOWED_ITEM_TYPES
    )

    if unexpected:
        log(
            "tool-surface-violation="
            + ",".join(
                sorted(unexpected)
            )
        )

        return {
            "ok": False,
            "error":
                "tool_surface_violation",
        }

    if result.returncode != 0:
        return {
            "ok": False,
            "error": "upstream_failure",
        }

    texts = []

    for event in events:
        item = event.get(
            "item"
        )

        if not isinstance(
            item,
            dict,
        ):
            continue

        if item.get(
            "type"
        ) != "agent_message":
            continue

        text = item.get(
            "text"
        )

        if isinstance(
            text,
            str,
        ):
            texts.append(text)

    if not texts:
        return {
            "ok": False,
            "error":
                "missing_model_output",
        }

    log(
        "codex-turn=success "
        "item_types="
        + ",".join(
            sorted(
                observed_item_types
            )
        )
    )

    return {
        "ok": True,
        "text": texts[-1],
    }


def handle(
    connection: socket.socket,
) -> None:
    try:
        request = recv_request(
            connection
        )

        response = run_codex(
            request["prompt"]
        )

    except (
        ValueError,
        json.JSONDecodeError,
    ):
        response = {
            "ok": False,
            "error": "invalid_request",
        }

    except Exception as exc:
        log(
            "adapter-error="
            + type(exc).__name__
        )

        response = {
            "ok": False,
            "error": "adapter_failure",
        }

    send_response(
        connection,
        response,
    )


def main() -> None:
    _validate_codex_identity()
    if not CODEX.is_file():
        raise SystemExit(
            "Codex binary missing"
        )

    if not WORKSPACE.is_dir():
        raise SystemExit(
            "workspace missing"
        )

    SOCKET.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        SOCKET.unlink()
    except FileNotFoundError:
        pass

    server = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
    )

    server.bind(
        str(SOCKET)
    )

    os.chmod(
        SOCKET,
        0o660,
    )

    server.listen(8)

    log(
        "hardened Codex adapter ready"
    )

    try:
        while True:
            connection, _ = (
                server.accept()
            )

            with connection:
                handle(
                    connection
                )

    finally:
        server.close()

        try:
            SOCKET.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
