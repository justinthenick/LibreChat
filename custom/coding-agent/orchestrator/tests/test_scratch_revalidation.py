from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from openhands.sdk.testing import TestLLM

from coding_orchestrator import (
    BackendRunRequest,
    EXPECTED_CODING_EXECUTOR_TOOLS,
    OpenHandsBackend,
    OpenHandsProviderConfig,
)


class ScratchRevalidationTests(unittest.TestCase):
    def setUp(self) -> None:
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def assert_setup_mutation_rejected(self, stage: str, mutation: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            scratch = parent / "scratch"
            repo = parent / "repo"
            repo.mkdir()
            (repo / ".git").mkdir()
            llm = TestLLM.from_messages([])

            def mutate_root() -> None:
                if mutation == "git-marker":
                    (scratch / ".git").mkdir()
                else:
                    scratch.rename(parent / "original-scratch")
                    scratch.symlink_to(repo, target_is_directory=True)

            def discover(_endpoint, _token):
                if stage == "probe":
                    mutate_root()
                return EXPECTED_CODING_EXECUTOR_TOOLS

            def build_llm():
                if stage == "provider":
                    mutate_root()
                return llm

            backend = OpenHandsBackend(
                "http://127.0.0.1:8765/mcp", "synthetic-token",
                discover_tools=discover,
                provider=OpenHandsProviderConfig("chatgpt_subscription", "gpt-5.6-sol"),
                scratch_root=scratch,
            )
            allocator = tempfile.TemporaryDirectory
            with patch.object(
                OpenHandsProviderConfig, "build_llm", side_effect=build_llm,
            ) as provider, patch(
                "coding_orchestrator.openhands_backend.tempfile.TemporaryDirectory",
                wraps=allocator,
            ) as allocation, patch("openhands.sdk.Conversation") as conversation:
                with self.assertRaises(ValueError):
                    backend.run(BackendRunRequest(prompt="Must stop before workspace creation."))
                provider.assert_called_once()
                allocation.assert_not_called()
                conversation.assert_not_called()
            self.assertEqual(llm.call_count, 0)

    def test_revalidates_root_after_probe_before_workspace_creation(self) -> None:
        for mutation in ("git-marker", "symlink"):
            with self.subTest(mutation=mutation):
                self.assert_setup_mutation_rejected("probe", mutation)

    def test_revalidates_root_after_provider_before_workspace_creation(self) -> None:
        for mutation in ("git-marker", "symlink"):
            with self.subTest(mutation=mutation):
                self.assert_setup_mutation_rejected("provider", mutation)


if __name__ == "__main__":
    unittest.main()
