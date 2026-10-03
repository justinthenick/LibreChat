from __future__ import annotations

import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_orchestrator import (
    BackendContractError,
    BackendRunRequest,
    EXPECTED_CODING_EXECUTOR_TOOLS,
    EXPECTED_OPENHANDS_RUNTIME_TOOLS,
    OPENHANDS_RUNTIME_TOOL_REGEX,
    OpenHandsBackend,
)
from coding_orchestrator.openhands_backend import (
    _validate_run_workspace,
)


class OpenHandsBackendTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_probe_accepts_exact_executor_contract(
        self,
    ) -> None:
        calls: list[
            tuple[str, str]
        ] = []

        def discover(
            endpoint: str,
            token: str,
        ):
            calls.append(
                (endpoint, token)
            )
            return reversed(
                sorted(
                    EXPECTED_CODING_EXECUTOR_TOOLS
                )
            )

        backend = OpenHandsBackend(
            "http://127.0.0.1:8765/mcp",
            "secret-token",
            discover_tools=discover,
        )

        result = backend.probe()

        self.assertEqual(
            result.backend,
            "openhands",
        )
        self.assertEqual(
            result.tool_names,
            tuple(
                sorted(
                    EXPECTED_CODING_EXECUTOR_TOOLS
                )
            ),
        )
        self.assertEqual(
            calls,
            [
                (
                    "http://127.0.0.1:8765/mcp",
                    "secret-token",
                )
            ],
        )

    def test_probe_fails_closed_when_tool_is_missing(
        self,
    ) -> None:
        discovered = (
            EXPECTED_CODING_EXECUTOR_TOOLS
            - {"apply_patch"}
        )

        backend = OpenHandsBackend(
            "http://127.0.0.1:8765/mcp",
            "secret-token",
            discover_tools=(
                lambda _endpoint, _token:
                discovered
            ),
        )

        with self.assertRaisesRegex(
            BackendContractError,
            r"missing=apply_patch",
        ):
            backend.probe()

    def test_probe_fails_closed_when_tool_is_added(
        self,
    ) -> None:
        discovered = (
            set(
                EXPECTED_CODING_EXECUTOR_TOOLS
            )
            | {"arbitrary_shell"}
        )

        backend = OpenHandsBackend(
            "http://127.0.0.1:8765/mcp",
            "secret-token",
            discover_tools=(
                lambda _endpoint, _token:
                discovered
            ),
        )

        with self.assertRaisesRegex(
            BackendContractError,
            r"unexpected=arbitrary_shell",
        ):
            backend.probe()

    def test_probe_rejects_missing_and_unexpected_together(
        self,
    ) -> None:
        discovered = (
            set(
                EXPECTED_CODING_EXECUTOR_TOOLS
            )
            - {"git_diff"}
        ) | {"docker"}

        backend = OpenHandsBackend(
            "http://127.0.0.1:8765/mcp",
            "secret-token",
            discover_tools=(
                lambda _endpoint, _token:
                discovered
            ),
        )

        with self.assertRaisesRegex(
            BackendContractError,
            r"missing=git_diff; unexpected=docker",
        ):
            backend.probe()

    def test_endpoint_must_end_exactly_in_mcp(
        self,
    ) -> None:
        invalid = [
            "http://127.0.0.1:8765",
            "http://127.0.0.1:8765/mcp/",
            "http://127.0.0.1:8765/mcp?extra=true",
            "file:///tmp/mcp",
            "",
        ]

        for endpoint in invalid:
            with self.subTest(
                endpoint=endpoint
            ):
                with self.assertRaises(
                    ValueError
                ):
                    OpenHandsBackend(
                        endpoint,
                        "secret-token",
                        discover_tools=(
                            lambda _endpoint,
                            _token: ()
                        ),
                    )

    def test_token_is_required(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"bearer token is required",
        ):
            OpenHandsBackend(
                "http://127.0.0.1:8765/mcp",
                "",
                discover_tools=(
                    lambda _endpoint,
                    _token: ()
                ),
            )

    def test_runtime_regex_is_exact_allowlist(
        self,
    ) -> None:
        pattern = re.compile(
            OPENHANDS_RUNTIME_TOOL_REGEX
        )

        for name in (
            EXPECTED_OPENHANDS_RUNTIME_TOOLS
        ):
            self.assertIsNotNone(
                pattern.fullmatch(name)
            )

        for forbidden in (
            "terminal",
            "execute_bash",
            "file_editor",
            "browser",
            "docker",
            "commit",
            "push",
            "merge",
            "think",
            "switch_llm",
        ):
            self.assertIsNone(
                pattern.fullmatch(forbidden)
            )

    def test_agent_has_only_finish_plus_executor_channel(
        self,
    ) -> None:
        from openhands.sdk.testing import (
            TestLLM,
        )

        backend = OpenHandsBackend(
            "http://127.0.0.1:8765/mcp",
            "secret-token",
            llm=TestLLM.from_messages([]),
        )

        agent = backend._build_agent()

        self.assertEqual(
            agent.tools,
            [],
        )
        self.assertEqual(
            agent.include_default_tools,
            ["FinishTool"],
        )
        self.assertEqual(
            set(agent.mcp_config),
            {"coding_executor"},
        )
        self.assertEqual(
            agent.filter_tools_regex,
            OPENHANDS_RUNTIME_TOOL_REGEX,
        )

    def test_http_requires_literal_loopback(
        self,
    ) -> None:
        rejected = (
            "http://192.168.1.120:8765/mcp",
            "http://localhost:8765/mcp",
            "http://executor.example.test/mcp",
        )

        for endpoint in rejected:
            with self.subTest(endpoint=endpoint):
                with self.assertRaisesRegex(
                    ValueError,
                    r"literal loopback",
                ):
                    OpenHandsBackend(
                        endpoint,
                        "secret-token",
                        discover_tools=(
                            lambda _endpoint, _token: ()
                        ),
                    )

        accepted = (
            "http://127.0.0.1:8765/mcp",
            "http://127.0.0.42:8765/mcp",
            "http://[::1]:8765/mcp",
            "https://192.168.1.120:8765/mcp",
            "https://executor.example.test/mcp",
        )

        for endpoint in accepted:
            with self.subTest(endpoint=endpoint):
                OpenHandsBackend(
                    endpoint,
                    "secret-token",
                    discover_tools=(
                        lambda _endpoint, _token: ()
                    ),
                )

    def test_run_revalidates_scratch_root_after_git_marker(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as root:
            scratch = Path(root) / "scratch"

            backend = OpenHandsBackend(
                "http://127.0.0.1:8765/mcp",
                "secret-token",
                discover_tools=(
                    lambda _endpoint, _token:
                    EXPECTED_CODING_EXECUTOR_TOOLS
                ),
                scratch_root=scratch,
            )

            (scratch / ".git").mkdir()

            with self.assertRaisesRegex(
                ValueError,
                r"must not be inside a Git repository",
            ):
                backend.run(
                    BackendRunRequest(
                        prompt="test",
                        max_iterations=1,
                    )
                )

    def test_run_revalidates_scratch_root_after_symlink_swap(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            scratch = base / "scratch"

            backend = OpenHandsBackend(
                "http://127.0.0.1:8765/mcp",
                "secret-token",
                discover_tools=(
                    lambda _endpoint, _token:
                    EXPECTED_CODING_EXECUTOR_TOOLS
                ),
                scratch_root=scratch,
            )

            original = base / "scratch-original"
            outside = base / "outside"

            scratch.rename(original)
            outside.mkdir()
            scratch.symlink_to(
                outside,
                target_is_directory=True,
            )

            with self.assertRaisesRegex(
                ValueError,
                r"must not be a symbolic link",
            ):
                backend.run(
                    BackendRunRequest(
                        prompt="test",
                        max_iterations=1,
                    )
                )

    def test_run_workspace_must_remain_beneath_scratch_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            scratch = base / "scratch"
            outside = base / "outside"

            scratch.mkdir()
            outside.mkdir()

            with self.assertRaisesRegex(
                ValueError,
                r"directly beneath",
            ):
                _validate_run_workspace(
                    outside,
                    scratch.resolve(),
                )

    def test_scratch_root_inside_git_repository_is_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as root:
            repo = Path(root) / "repo"
            repo.mkdir()
            (repo / ".git").mkdir()

            scratch = repo / "scratch"

            with self.assertRaisesRegex(
                ValueError,
                r"must not be inside a Git repository",
            ):
                OpenHandsBackend(
                    "http://127.0.0.1:8765/mcp",
                    "secret-token",
                    scratch_root=scratch,
                )


if __name__ == "__main__":
    unittest.main()
