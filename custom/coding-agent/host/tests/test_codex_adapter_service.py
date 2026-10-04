from __future__ import annotations

import unittest
from pathlib import Path


HOST_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

UNIT = (
    HOST_ROOT
    / "systemd"
    / "coding-agent-codex-adapter.service"
)


class CodexAdapterServiceTests(
    unittest.TestCase
):
    def test_service_uses_current_release(
        self,
    ) -> None:
        text = UNIT.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "Environment=PYTHONPATH=",
            text,
        )

        self.assertNotIn(
            "EnvironmentFile=",
            text,
        )

        self.assertNotIn(
            "coding-maintenance.env",
            text,
        )


        self.assertIn(
            "NoNewPrivileges=true",
            text,
        )

        self.assertIn(
            "PrivateTmp=true",
            text,
        )

        self.assertIn(
            "UMask=0077",
            text,
        )

        self.assertIn(
            "%h/.local/share/"
            "coding-maintenance/"
            "current/venv/bin/python "
            "-m host_maintenance.codex_adapter",
            text,
        )

        self.assertNotIn(
            "/releases/",
            text,
        )

        self.assertNotIn(
            "bash -c",
            text,
        )


if __name__ == "__main__":
    unittest.main()
