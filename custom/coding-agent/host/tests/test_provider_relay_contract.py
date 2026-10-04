from __future__ import annotations

import base64
import hashlib
import hmac
import importlib.util
import json
import os
import time
import unittest
from pathlib import Path
from unittest.mock import patch


HOST_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

CODING_ROOT = HOST_ROOT.parent

RELAY_ROOT = (
    CODING_ROOT
    / "provider-relay"
)

RELAY = (
    RELAY_ROOT
    / "relay.py"
)

DOCKERFILE = (
    RELAY_ROOT
    / "Dockerfile"
)


class ProviderRelayContractTests(
    unittest.TestCase
):
    def test_relay_contains_signed_task_policy(
        self,
    ) -> None:
        text = RELAY.read_text(
            encoding="utf-8"
        )

        required = (
            "hmac.new",
            "hashlib.sha256",
            "compare_digest",
            "librechat-acp-provider-relay",
            "TOKEN_SECONDS = 3900",
            "token issued in future",
            "token expired",
            "claim mismatch",
            "CODEX_ADAPTER_SOCKET",
            "phase3-mock",
            "MAX_BODY",
            "MAX_PROMPT",
            "MAX_ADAPTER_RESPONSE",
            "upstream_quota",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(
                    value,
                    text,
                )

        self.assertNotIn(
            "OPENAI_API_KEY",
            text,
        )

        self.assertNotIn(
            "OPENROUTER_API_KEY",
            text,
        )

        self.assertNotIn(
            "ANTHROPIC_API_KEY",
            text,
        )

    def test_relay_runtime_rejects_noncanonical_signature(
        self,
    ) -> None:
        key_hex = "11" * 32
        key = bytes.fromhex(
            key_hex
        )

        spec = (
            importlib.util
            .spec_from_file_location(
                "phase3_provider_relay_test",
                RELAY,
            )
        )

        self.assertIsNotNone(
            spec,
        )
        self.assertIsNotNone(
            spec.loader,
        )

        module = (
            importlib.util
            .module_from_spec(
                spec
            )
        )

        with patch.dict(
            os.environ,
            {
                "RELAY_SIGNING_KEY":
                    key_hex,
                "ALLOWED_MODEL":
                    "phase3-mock",
            },
            clear=False,
        ):
            spec.loader.exec_module(
                module
            )

        now = int(
            time.time()
        )

        claims = {
            "v": 1,
            "aud":
                "librechat-acp-provider-relay",
            "task":
                "canonical-test-task",
            "model":
                "phase3-mock",
            "iat":
                now,
            "exp":
                now + 3900,
            "nonce":
                "n" * 24,
        }

        payload_bytes = json.dumps(
            claims,
            sort_keys=True,
            separators=(",", ":"),
        ).encode(
            "utf-8"
        )

        def encode(
            value: bytes,
        ) -> str:
            return (
                base64
                .urlsafe_b64encode(
                    value
                )
                .rstrip(b"=")
                .decode("ascii")
            )

        payload = encode(
            payload_bytes
        )

        signature_bytes = hmac.new(
            key,
            (
                "v1."
                + payload
            ).encode(
                "ascii"
            ),
            hashlib.sha256,
        ).digest()

        signature = encode(
            signature_bytes
        )

        alphabet = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789-_"
        )

        canonical_index = alphabet.index(
            signature[-1]
        )

        # A 32-byte SHA-256 digest leaves two
        # unused low bits in its final Base64URL
        # character. Canonical encodings therefore
        # use an alphabet index divisible by four.
        self.assertEqual(
            canonical_index % 4,
            0,
        )

        alias_signature = (
            signature[:-1]
            + alphabet[
                canonical_index + 1
            ]
        )

        def permissive_decode(
            value: str,
        ) -> bytes:
            return (
                base64
                .urlsafe_b64decode(
                    value
                    + "="
                    * (-len(value) % 4)
                )
            )

        self.assertEqual(
            permissive_decode(
                alias_signature
            ),
            signature_bytes,
        )

        alias_token = (
            "v1."
            + payload
            + "."
            + alias_signature
        )

        with self.assertRaisesRegex(
            ValueError,
            "non-canonical base64url",
        ):
            module.validate_token(
                alias_token
            )

    def test_relay_image_runs_non_root(
        self,
    ) -> None:
        text = DOCKERFILE.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "10001",
            text,
        )

        self.assertRegex(
            text,
            r"(?m)^USER\s+10001(?::10001)?\s*$",
        )

        self.assertNotRegex(
            text,
            r"(?m)^USER\s+(?:0|root)\s*$",
        )


if __name__ == "__main__":
    unittest.main()

class ProviderRelayRequestSurfaceTests(
    unittest.TestCase
):
    def _load_relay(self):
        spec = (
            importlib.util
            .spec_from_file_location(
                "phase3_provider_relay_surface_test",
                RELAY,
            )
        )

        self.assertIsNotNone(
            spec
        )
        self.assertIsNotNone(
            spec.loader
        )

        module = (
            importlib.util
            .module_from_spec(
                spec
            )
        )

        with patch.dict(
            os.environ,
            {
                "RELAY_SIGNING_KEY":
                    "11" * 32,
                "ALLOWED_MODEL":
                    "phase3-mock",
            },
            clear=False,
        ):
            spec.loader.exec_module(
                module
            )

        return module

    def test_text_request_surface_is_accepted(
        self,
    ) -> None:
        relay = self._load_relay()

        relay.validate_request_surface({
            "model":
                "phase3-mock",
            "messages": [
                {
                    "role":
                        "user",
                    "content":
                        "hello",
                }
            ],
            "stream":
                True,
        })

    def test_model_capability_fields_fail_closed(
        self,
    ) -> None:
        relay = self._load_relay()

        for field in sorted(
            relay.FORBIDDEN_REQUEST_FIELDS
        ):
            with self.subTest(
                field=field
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "unsupported request capability",
                ):
                    relay.validate_request_surface({
                        "model":
                            "phase3-mock",
                        "messages": [
                            {
                                "role":
                                    "user",
                                "content":
                                    "hello",
                            }
                        ],
                        "stream":
                            False,
                        field:
                            {},
                    })

    def test_non_boolean_stream_fails_closed(
        self,
    ) -> None:
        relay = self._load_relay()

        with self.assertRaisesRegex(
            ValueError,
            "stream must be boolean",
        ):
            relay.validate_request_surface({
                "model":
                    "phase3-mock",
                "messages": [],
                "stream":
                    "true",
            })


class ProviderRelayToolCompatibilityTests(
    unittest.TestCase
):
    """OpenCode tool metadata may enter the relay but never cross it."""

    def _load_relay(self):
        import importlib.util
        import os
        from pathlib import Path
        from unittest.mock import patch

        relay_path = (
            Path(__file__)
            .resolve()
            .parents[2]
            / "provider-relay"
            / "relay.py"
        )

        spec = (
            importlib.util
            .spec_from_file_location(
                "provider_relay_tool_compat_test",
                relay_path,
            )
        )

        self.assertIsNotNone(
            spec
        )
        self.assertIsNotNone(
            spec.loader
        )

        module = (
            importlib.util
            .module_from_spec(
                spec
            )
        )

        with patch.dict(
            os.environ,
            {
                "RELAY_SIGNING_KEY":
                    "11" * 32,
                "ALLOWED_MODEL":
                    "phase3-mock",
                "CODEX_ADAPTER_SOCKET":
                    "/tmp/nonexistent-codex.sock",
            },
            clear=False,
        ):
            spec.loader.exec_module(
                module
            )

        return module

    @staticmethod
    def _observed_request():
        return {
            "max_tokens":
                4096,
            "messages": [
                {
                    "role":
                        "system",
                    "content":
                        "OPEN_CODE_SYSTEM_TEXT",
                },
                {
                    "role":
                        "user",
                    "content":
                        "BOUNDARY_USER_PROMPT",
                },
            ],
            "model":
                "phase3-mock",
            "stream":
                True,
            "stream_options": {
                "include_usage":
                    True,
            },
            "tool_choice":
                "auto",
            "tools": [
                {
                    "type":
                        "function",
                    "function": {
                        "name":
                            f"opencode_tool_{index}",
                        "description":
                            "MUST_NOT_REACH_CODEX",
                        "parameters": {
                            "type":
                                "object",
                        },
                    },
                }
                for index
                in range(10)
            ],
        }

    def test_observed_opencode_envelope_is_accepted(
        self,
    ) -> None:
        relay = (
            self._load_relay()
        )

        relay.validate_request_surface(
            self._observed_request()
        )

    def test_tool_metadata_never_enters_codex_prompt(
        self,
    ) -> None:
        relay = (
            self._load_relay()
        )

        body = (
            self._observed_request()
        )

        relay.validate_request_surface(
            body
        )

        prompt = (
            relay.prompt_from_request(
                body
            )
        )

        self.assertIn(
            "BOUNDARY_USER_PROMPT",
            prompt,
        )

        self.assertNotIn(
            "OPEN_CODE_SYSTEM_TEXT",
            prompt,
        )

        self.assertNotIn(
            "MUST_NOT_REACH_CODEX",
            prompt,
        )

        self.assertNotIn(
            "opencode_tool_",
            prompt,
        )

    def test_empty_tools_and_none_choice_are_accepted(
        self,
    ) -> None:
        relay = (
            self._load_relay()
        )

        body = (
            self._observed_request()
        )

        body["tools"] = []
        body["tool_choice"] = (
            "none"
        )

        relay.validate_request_surface(
            body
        )

    def test_capability_expanding_tool_choice_is_rejected(
        self,
    ) -> None:
        relay = (
            self._load_relay()
        )

        for value in (
            "required",
            {
                "type":
                    "function",
                "function": {
                    "name":
                        "dangerous",
                },
            },
        ):
            with self.subTest(
                value=value
            ):
                body = (
                    self._observed_request()
                )

                body[
                    "tool_choice"
                ] = value

                with self.assertRaisesRegex(
                    ValueError,
                    "unsupported request capability",
                ):
                    relay.validate_request_surface(
                        body
                    )

    def test_malformed_tools_are_rejected(
        self,
    ) -> None:
        relay = (
            self._load_relay()
        )

        malformed_values = (
            {
                "not":
                    "a-list",
            },
            [
                {
                    "type":
                        "function",
                },
                "not-an-object",
            ],
        )

        for value in malformed_values:
            with self.subTest(
                value=value
            ):
                body = (
                    self._observed_request()
                )

                body["tools"] = (
                    value
                )

                with self.assertRaisesRegex(
                    ValueError,
                    "unsupported request capability",
                ):
                    relay.validate_request_surface(
                        body
                    )

    def test_true_capability_fields_remain_rejected(
        self,
    ) -> None:
        relay = (
            self._load_relay()
        )

        for field in sorted(
            relay.FORBIDDEN_REQUEST_FIELDS
        ):
            with self.subTest(
                field=field
            ):
                body = (
                    self._observed_request()
                )

                body[field] = {}

                with self.assertRaisesRegex(
                    ValueError,
                    "unsupported request capability",
                ):
                    relay.validate_request_surface(
                        body
                    )


class ProviderRelayHandlerShapeTests(
    unittest.TestCase
):
    def _load_relay(self):
        import importlib.util
        import os
        from pathlib import Path
        from unittest.mock import patch

        relay_path = (
            Path(__file__)
            .resolve()
            .parents[2]
            / "provider-relay"
            / "relay.py"
        )

        spec = importlib.util.spec_from_file_location(
            "provider_relay_handler_shape_test",
            relay_path,
        )

        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        module = importlib.util.module_from_spec(
            spec
        )

        with patch.dict(
            os.environ,
            {
                "RELAY_SIGNING_KEY":
                    "11" * 32,
                "ALLOWED_MODEL":
                    "phase3-mock",
                "CODEX_ADAPTER_SOCKET":
                    "/tmp/nonexistent",
            },
            clear=False,
        ):
            spec.loader.exec_module(
                module
            )

        return module

    def test_non_object_json_fails_with_bounded_400(
        self,
    ) -> None:
        import io
        from unittest.mock import Mock

        relay = self._load_relay()

        handler = object.__new__(
            relay.Handler
        )

        payload = b"[]"

        handler.path = (
            "/v1/chat/completions"
        )
        handler.headers = {
            "Content-Length":
                str(len(payload)),
        }
        handler.rfile = io.BytesIO(
            payload
        )
        handler.authenticated = (
            lambda: {
                "task":
                    "shape-test",
            }
        )
        handler.send_json = Mock()

        handler.do_POST()

        handler.send_json.assert_called_once_with(
            400,
            {
                "error":
                    "invalid_request",
            },
        )
