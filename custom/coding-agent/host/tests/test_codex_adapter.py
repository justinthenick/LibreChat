from __future__ import annotations

import json
import subprocess
import unittest
from unittest.mock import patch
from contextlib import contextmanager

from host_maintenance import codex_adapter


class CodexAdapterPolicyTests(
    unittest.TestCase
):
    def setUp(self):
        @contextmanager
        def reviewed():
            yield codex_adapter.CODEX, "/proc/self/fd/99", 99
        self.identity = patch.object(codex_adapter, "_reviewed_codex", reviewed)
        self.identity.start()
        self.addCleanup(self.identity.stop)

    def test_command_hard_disables_all_model_tools(
        self,
    ) -> None:
        argv = codex_adapter.hardened_command(
            "hello"
        )

        joined = "\n".join(argv)

        required = (
            "features.shell_tool=false",
            "features.unified_exec=false",
            "features.unified_exec_tty=false",
            "features.view_image=false",
            "features.shell_snapshot=false",
            "features.sleep_tool=false",
            "features.standalone_web_search=false",
            "features.plugins=false",
            "features.apps=false",
            'web_search="disabled"',
            "mcp_servers={}",
            "include_apps_instructions=false",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(
                    value,
                    joined,
                )

        self.assertIn(
            "--ignore-user-config",
            argv,
        )

        self.assertIn(
            "--ignore-rules",
            argv,
        )

        self.assertIn(
            "--strict-config",
            argv,
        )

        self.assertEqual(
            argv[
                argv.index("--sandbox") + 1
            ],
            "read-only",
        )

    def test_agent_message_only_is_accepted(
        self,
    ) -> None:
        stdout = "\n".join(
            [
                json.dumps(
                    {
                        "type":
                            "thread.started",
                        "thread_id":
                            "example",
                    }
                ),
                json.dumps(
                    {
                        "type":
                            "item.completed",
                        "item": {
                            "id":
                                "item_0",
                            "type":
                                "agent_message",
                            "text":
                                "MODEL_OK",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type":
                            "turn.completed",
                    }
                ),
            ]
        )

        result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=stdout,
            stderr="",
        )

        with patch.object(
            codex_adapter.subprocess,
            "run",
            return_value=result,
        ):
            response = (
                codex_adapter.run_codex(
                    "hello"
                )
            )

        self.assertEqual(
            response,
            {
                "ok": True,
                "text": "MODEL_OK",
            },
        )

    def test_any_mcp_tool_event_fails_closed(
        self,
    ) -> None:
        stdout = "\n".join(
            [
                json.dumps(
                    {
                        "type":
                            "item.completed",
                        "item": {
                            "id":
                                "item_0",
                            "type":
                                "mcp_tool_call",
                            "server":
                                "codex",
                            "tool":
                                "list_mcp_resources",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type":
                            "item.completed",
                        "item": {
                            "id":
                                "item_1",
                            "type":
                                "agent_message",
                            "text":
                                "should not pass",
                        },
                    }
                ),
            ]
        )

        result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=stdout,
            stderr="",
        )

        with patch.object(
            codex_adapter.subprocess,
            "run",
            return_value=result,
        ):
            response = (
                codex_adapter.run_codex(
                    "hello"
                )
            )

        self.assertEqual(
            response,
            {
                "ok": False,
                "error":
                    "tool_surface_violation",
            },
        )

    def test_command_execution_event_fails_closed(
        self,
    ) -> None:
        stdout = json.dumps(
            {
                "type":
                    "item.completed",
                "item": {
                    "id":
                        "item_0",
                    "type":
                        "command_execution",
                    "command":
                        "cat /etc/passwd",
                },
            }
        )

        result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=stdout,
            stderr="",
        )

        with patch.object(
            codex_adapter.subprocess,
            "run",
            return_value=result,
        ):
            response = (
                codex_adapter.run_codex(
                    "hello"
                )
            )

        self.assertEqual(
            response.get("error"),
            "tool_surface_violation",
        )

    def test_quota_error_is_sanitized(
        self,
    ) -> None:
        stdout = json.dumps(
            {
                "type":
                    "turn.failed",
                "error": {
                    "message":
                        "You've hit your usage "
                        "limit; purchase more "
                        "credits.",
                },
            }
        )

        result = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=stdout,
            stderr="sensitive upstream text",
        )

        with patch.object(
            codex_adapter.subprocess,
            "run",
            return_value=result,
        ):
            response = (
                codex_adapter.run_codex(
                    "hello"
                )
            )

        self.assertEqual(
            response,
            {
                "ok": False,
                "error":
                    "upstream_quota",
            },
        )

    def test_oversize_prompt_is_rejected(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "prompt too large",
        ):
            codex_adapter.run_codex(
                "x"
                * (
                    codex_adapter.MAX_PROMPT
                    + 1
                )
            )


if __name__ == "__main__":
    unittest.main()

class CodexReviewedIdentityTests(unittest.TestCase):
    def test_reviewed_codex_identity_is_hard_pinned(
        self,
    ) -> None:
        import host_maintenance.codex_adapter as adapter

        self.assertEqual(
            adapter.CODEX_EXPECTED_VERSION,
            "codex-cli 0.154.0",
        )

        self.assertEqual(
            adapter.CODEX_EXPECTED_SHA256,
            "3188814c35471432d4123203e0eb38e5bddc60226e3d7ddf0e59e649ea140022",
        )

    def test_codex_identity_rejects_digest_drift(
        self,
    ) -> None:
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        import host_maintenance.codex_adapter as adapter

        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "codex"

            fake.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' 'codex-cli 0.154.0'\n",
                encoding="utf-8",
            )

            fake.chmod(
                0o755
            )

            with patch.object(
                adapter,
                "CODEX_EXPECTED_SHA256",
                "0" * 64,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "identity mismatch",
                ):
                    adapter._validate_codex_identity(
                        fake
                    )

    def test_codex_identity_accepts_exact_reviewed_shape(
        self,
    ) -> None:
        import hashlib
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        import host_maintenance.codex_adapter as adapter

        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "codex"

            fake.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' 'codex-cli 0.154.0'\n",
                encoding="utf-8",
            )

            fake.chmod(
                0o755
            )

            digest = hashlib.sha256(
                fake.read_bytes()
            ).hexdigest()

            with (
                patch.object(
                    adapter,
                    "CODEX_EXPECTED_SHA256",
                    digest,
                ),
                patch.object(
                    adapter,
                    "CODEX_EXPECTED_VERSION",
                    "codex-cli 0.154.0",
                ),
            ):
                resolved = (
                    adapter
                    ._validate_codex_identity(
                        fake
                    )
                )

            self.assertEqual(
                resolved,
                fake.resolve(),
            )
