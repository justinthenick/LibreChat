from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import socket
import time
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)


KEY_HEX = os.environ[
    "RELAY_SIGNING_KEY"
]

MODEL = os.environ.get(
    "ALLOWED_MODEL",
    "phase3-mock",
)

ADAPTER_SOCKET = os.environ.get(
    "CODEX_ADAPTER_SOCKET",
    "/run/codex-adapter/codex.sock",
)

AUDIENCE = (
    "librechat-acp-provider-relay"
)

TOKEN_SECONDS = 3900
MAX_BODY = 1024 * 1024
MAX_PROMPT = 32 * 1024
MAX_ADAPTER_RESPONSE = 1024 * 1024

FORBIDDEN_REQUEST_FIELDS = frozenset({
    "audio",
    "function_call",
    "functions",
    "modalities",
    "parallel_tool_calls",
    "response_format",
})

# OpenCode's OpenAI-compatible provider advertises its own
# local tool catalogue. The relay accepts these fields only
# as compatibility metadata. They are intentionally discarded
# before the request crosses into the Codex adapter boundary.
IGNORED_TOOL_COMPATIBILITY_FIELDS = frozenset({
    "tool_choice",
    "tools",
})


TASK_ID = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}"
)


if not re.fullmatch(
    r"[0-9a-f]{64}",
    KEY_HEX,
):
    raise SystemExit(
        "invalid relay signing key"
    )


KEY = bytes.fromhex(
    KEY_HEX
)


def b64url_encode(
    value: bytes,
) -> str:
    return (
        base64.urlsafe_b64encode(
            value
        )
        .rstrip(b"=")
        .decode("ascii")
    )


def b64url_decode(
    value: str,
) -> bytes:
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

    if b64url_encode(decoded) != value:
        raise ValueError(
            "non-canonical base64url encoding"
        )

    return decoded


def validate_token(
    value: str,
) -> dict:
    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            "missing token"
        )

    parts = value.split(".")

    if (
        len(parts) != 3
        or parts[0] != "v1"
    ):
        raise ValueError(
            "bad token format"
        )

    encoded = parts[1]

    supplied = b64url_decode(
        parts[2]
    )

    expected = hmac.new(
        KEY,
        f"v1.{encoded}".encode(
            "ascii"
        ),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(
        supplied,
        expected,
    ):
        raise ValueError(
            "bad token signature"
        )

    claims = json.loads(
        b64url_decode(encoded)
    )

    if not isinstance(
        claims,
        dict,
    ):
        raise ValueError(
            "bad claims"
        )

    if (
        claims.get("v") != 1
        or claims.get("aud")
        != AUDIENCE
        or claims.get("model")
        != MODEL
        or not isinstance(
            claims.get("task"),
            str,
        )
        or not TASK_ID.fullmatch(
            claims["task"]
        )
    ):
        raise ValueError(
            "claim mismatch"
        )

    iat = claims.get("iat")
    exp = claims.get("exp")
    nonce = claims.get("nonce")

    if (
        isinstance(iat, bool)
        or not isinstance(iat, int)
        or isinstance(exp, bool)
        or not isinstance(exp, int)
        or exp - iat
        != TOKEN_SECONDS
        or not isinstance(
            nonce,
            str,
        )
        or not re.fullmatch(
            r"[A-Za-z0-9_-]{20,64}",
            nonce,
        )
    ):
        raise ValueError(
            "token lifetime mismatch"
        )

    now = int(time.time())

    if iat > now + 30:
        raise ValueError(
            "token issued in future"
        )

    if exp <= now:
        raise ValueError(
            "token expired"
        )

    return claims


def content_text(
    content,
) -> str:
    if isinstance(
        content,
        str,
    ):
        return content

    if not isinstance(
        content,
        list,
    ):
        return ""

    parts = []

    for item in content:
        if not isinstance(
            item,
            dict,
        ):
            continue

        if item.get("type") not in (
            "text",
            "input_text",
        ):
            continue

        value = (
            item.get("text")
            or item.get("input_text")
        )

        if isinstance(
            value,
            str,
        ):
            parts.append(value)

    return "\n".join(parts)


def validate_request_surface(
    body: dict,
) -> None:
    if not isinstance(
        body,
        dict,
    ):
        raise ValueError(
            "request body must be an object"
        )

    forbidden = (
        FORBIDDEN_REQUEST_FIELDS
        & set(body)
    )

    if forbidden:
        raise ValueError(
            "unsupported request capability"
        )

    if (
        "stream" in body
        and not isinstance(
            body["stream"],
            bool,
        )
    ):
        raise ValueError(
            "stream must be boolean"
        )

    # OpenCode 1.18.34 advertises its local tools to its
    # OpenAI-compatible provider even though this relay is
    # deliberately text-only upstream. Accept only the shape
    # needed for compatibility; this metadata is never passed
    # to call_adapter().
    if "tools" in body:
        tools = body["tools"]

        if (
            not isinstance(
                tools,
                list,
            )
            or any(
                not isinstance(
                    item,
                    dict,
                )
                for item in tools
            )
        ):
            raise ValueError(
                "unsupported request capability"
            )

    if "tool_choice" in body:
        tool_choice = (
            body["tool_choice"]
        )

        if (
            not isinstance(
                tool_choice,
                str,
            )
            or tool_choice not in {
                "auto",
                "none",
            }
        ):
            raise ValueError(
                "unsupported request capability"
            )


def prompt_from_request(
    body: dict,
) -> str:
    messages = body.get(
        "messages"
    )

    if not isinstance(
        messages,
        list,
    ):
        raise ValueError(
            "messages missing"
        )

    prompts = []

    for message in messages:
        if not isinstance(
            message,
            dict,
        ):
            continue

        if message.get("role") != "user":
            continue

        value = content_text(
            message.get("content")
        ).strip()

        if value:
            prompts.append(value)

    if not prompts:
        raise ValueError(
            "no user prompt"
        )

    prompt = "\n\n".join(
        prompts
    )

    if len(
        prompt.encode("utf-8")
    ) > MAX_PROMPT:
        raise ValueError(
            "prompt too large"
        )

    return prompt


def call_adapter(
    prompt: str,
) -> dict:
    request = (
        json.dumps(
            {
                "prompt": prompt,
            },
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")

    client = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
    )

    client.settimeout(130)

    try:
        client.connect(
            ADAPTER_SOCKET
        )

        client.sendall(
            request
        )

        client.shutdown(
            socket.SHUT_WR
        )

        data = bytearray()

        while b"\n" not in data:
            chunk = client.recv(
                8192
            )

            if not chunk:
                break

            data.extend(chunk)

            if (
                len(data)
                > MAX_ADAPTER_RESPONSE
            ):
                raise RuntimeError(
                    "adapter response too large"
                )

    finally:
        client.close()

    if not data:
        raise RuntimeError(
            "empty adapter response"
        )

    response = json.loads(
        bytes(data).split(
            b"\n",
            1,
        )[0]
    )

    if not isinstance(
        response,
        dict,
    ):
        raise RuntimeError(
            "invalid adapter response"
        )

    return response


class Handler(
    BaseHTTPRequestHandler
):
    server_version = (
        "Phase3CodexRelay/0.3"
    )

    def log_message(
        self,
        fmt,
        *args,
    ):
        print(
            (
                self.address_string()
                + " "
                + fmt % args
            ),
            flush=True,
        )

    def send_json(
        self,
        status: int,
        payload: dict,
    ) -> None:
        body = json.dumps(
            payload
        ).encode("utf-8")

        self.send_response(
            status
        )

        self.send_header(
            "Content-Type",
            "application/json",
        )

        self.send_header(
            "Content-Length",
            str(len(body)),
        )

        self.end_headers()

        self.wfile.write(
            body
        )

    def authenticated(
        self,
    ):
        value = self.headers.get(
            "Authorization",
            "",
        )

        prefix = "Bearer "

        if not value.startswith(
            prefix
        ):
            return None

        try:
            return validate_token(
                value[len(prefix):]
            )

        except Exception as exc:
            print(
                "auth-rejected="
                + type(exc).__name__,
                flush=True,
            )

            return None

    def do_GET(
        self,
    ):
        if self.path == "/healthz":
            self.send_json(
                200,
                {
                    "ok": True,
                    "mode":
                        "signed-codex-adapter",
                },
            )
            return

        if self.path == "/v1/models":
            claims = (
                self.authenticated()
            )

            if claims is None:
                self.send_json(
                    401,
                    {
                        "error":
                            "unauthorized",
                    },
                )
                return

            self.send_json(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": MODEL,
                            "object": "model",
                            "owned_by":
                                "phase3-relay",
                        }
                    ],
                },
            )
            return

        self.send_json(
            404,
            {
                "error":
                    "not_found",
            },
        )

    def do_POST(
        self,
    ):
        if (
            self.path
            != "/v1/chat/completions"
        ):
            self.send_json(
                404,
                {
                    "error":
                        "not_found",
                },
            )
            return

        claims = self.authenticated()

        if claims is None:
            self.send_json(
                401,
                {
                    "error":
                        "unauthorized",
                },
            )
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
            )
        except ValueError:
            self.send_json(
                400,
                {
                    "error":
                        "bad_content_length",
                },
            )
            return

        if (
            length < 0
            or length > MAX_BODY
        ):
            self.send_json(
                413,
                {
                    "error":
                        "request_too_large",
                },
            )
            return

        try:
            body = json.loads(
                self.rfile.read(
                    length
                )
            )
        except Exception:
            self.send_json(
                400,
                {
                    "error":
                        "invalid_json",
                },
            )
            return

        if not isinstance(
            body,
            dict,
        ):
            self.send_json(
                400,
                {
                    "error":
                        "invalid_request",
                },
            )
            return

        if (
            body.get("model")
            != MODEL
        ):
            self.send_json(
                403,
                {
                    "error":
                        "model_not_allowed",
                },
            )
            return

        try:
            validate_request_surface(
                body
            )

            prompt = (
                prompt_from_request(
                    body
                )
            )

            adapter = call_adapter(
                prompt
            )

        except ValueError:
            self.send_json(
                400,
                {
                    "error":
                        "invalid_prompt",
                },
            )
            return

        except Exception as exc:
            print(
                "adapter-bridge-error="
                + type(exc).__name__,
                flush=True,
            )

            self.send_json(
                502,
                {
                    "error": {
                        "message":
                            "model backend unavailable",
                        "type":
                            "server_error",
                        "code":
                            "adapter_failure",
                    }
                },
            )
            return

        if adapter == {
            "ok": False,
            "error": "upstream_quota",
        }:
            print(
                "adapter-result "
                f"task={claims['task']} "
                "result=upstream_quota",
                flush=True,
            )

            self.send_json(
                429,
                {
                    "error": {
                        "message":
                            "model quota unavailable",
                        "type":
                            "rate_limit_error",
                        "code":
                            "upstream_quota",
                    }
                },
            )
            return

        if adapter.get(
            "ok"
        ) is not True:
            result = str(
                adapter.get(
                    "error",
                    "unknown",
                )
            )

            print(
                "adapter-result "
                f"task={claims['task']} "
                f"result={result}",
                flush=True,
            )

            self.send_json(
                502,
                {
                    "error": {
                        "message":
                            "model backend unavailable",
                        "type":
                            "server_error",
                        "code":
                            "upstream_failure",
                    }
                },
            )
            return

        text = adapter.get(
            "text"
        )

        if not isinstance(
            text,
            str,
        ):
            self.send_json(
                502,
                {
                    "error": {
                        "message":
                            "invalid model response",
                        "type":
                            "server_error",
                        "code":
                            "invalid_upstream",
                    }
                },
            )
            return

        print(
            "adapter-result "
            f"task={claims['task']} "
            "result=success",
            flush=True,
        )

        created = int(
            time.time()
        )

        ident = (
            "chatcmpl-phase3-codex"
        )

        if not body.get(
            "stream"
        ):
            self.send_json(
                200,
                {
                    "id": ident,
                    "object":
                        "chat.completion",
                    "created": created,
                    "model": MODEL,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role":
                                    "assistant",
                                "content":
                                    text,
                            },
                            "finish_reason":
                                "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 2,
                    },
                },
            )
            return

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/event-stream",
        )

        self.send_header(
            "Cache-Control",
            "no-cache",
        )

        self.send_header(
            "Connection",
            "close",
        )

        self.end_headers()

        events = [
            {
                "id": ident,
                "object":
                    "chat.completion.chunk",
                "created": created,
                "model": MODEL,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role":
                                "assistant",
                        },
                        "finish_reason":
                            None,
                    }
                ],
            },
            {
                "id": ident,
                "object":
                    "chat.completion.chunk",
                "created": created,
                "model": MODEL,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content":
                                text,
                        },
                        "finish_reason":
                            None,
                    }
                ],
            },
            {
                "id": ident,
                "object":
                    "chat.completion.chunk",
                "created": created,
                "model": MODEL,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason":
                            "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                },
            },
        ]

        for event in events:
            chunk = (
                "data: "
                + json.dumps(event)
                + "\n\n"
            ).encode("utf-8")

            self.wfile.write(
                chunk
            )

            self.wfile.flush()

        self.wfile.write(
            b"data: [DONE]\n\n"
        )

        self.wfile.flush()


def main() -> None:
    server = ThreadingHTTPServer(
        ("0.0.0.0", 8080),
        Handler,
    )

    print(
        "phase3 signed Codex relay "
        "listening on :8080",
        flush=True,
    )

    server.serve_forever()


if __name__ == "__main__":
    main()
