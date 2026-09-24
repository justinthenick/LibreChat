from __future__ import annotations

import unittest
from pathlib import Path


HOST_ROOT = Path(__file__).resolve().parents[1]
DEPLOY = HOST_ROOT / "bin" / "deploy-maintenance-release.sh"
UNIT = HOST_ROOT / "systemd" / "coding-agent-host-maintenance.service"


class ReleaseDeploymentContractTests(unittest.TestCase):
    def test_release_deploy_is_immutable_and_pip_independent(self) -> None:
        text = DEPLOY.read_text()

        self.assertIn("set -Eeuo pipefail", text)
        self.assertIn('RELEASE="$ROOT/releases/$SHA"', text)
        self.assertIn('CURRENT="$ROOT/current"', text)
        self.assertIn('python3 -m venv --without-pip "$RELEASE/venv"', text)
        self.assertIn('BENCHMARK_DIR="$REPO_ROOT/custom/coding-agent/benchmarks"', text)
        self.assertIn('test -d "$BENCHMARK_DIR"', text)
        self.assertIn('cp -a "$BENCHMARK_DIR" "$RELEASE/custom/coding-agent/"', text)
        self.assertIn('sysconfig.get_path("purelib")', text)
        self.assertIn("venv purelib escapes release venv", text)
        self.assertNotIn("site.getsitepackages()", text)
        self.assertIn("python:3.12-slim-bookworm", text)
        self.assertIn("python -m pip install", text)
        self.assertIn("--target /out", text)
        self.assertIn('tar -C "$SITE" -xf -', text)
        self.assertNotIn('--volume "$SITE:/target:rw"', text)
        self.assertIn('test ! -e "$RELEASE"', text)

    def test_release_deploy_updates_both_executor_image_pins(self) -> None:
        text = DEPLOY.read_text()

        self.assertIn('service["image"] = image', text)
        self.assertIn('data["image_id"] = image', text)
        self.assertIn('"image_id": health["image_id"]', text)
        self.assertIn('assert health["image_id"] == config["image_id"]', text)

    def test_release_deploy_has_rollback_and_runtime_proof(self) -> None:
        text = DEPLOY.read_text()

        self.assertIn("rollback()", text)
        self.assertIn("trap 'rollback $?' ERR", text)
        self.assertIn('exit "$status"', text)
        self.assertIn("No production switch had been armed; nothing was rolled back.", text)
        self.assertIn('restore_file "$BACKUP/compose.json" "$COMPOSE"', text)
        self.assertIn('restore_file "$BACKUP/policy.json" "$CONFIG"', text)
        self.assertIn("=== FAIL-CLOSED RUNTIME VERIFICATION ===", text)
        self.assertIn('assert health["version"] == expected_executor', text)
        self.assertIn('systemctl --user show coding-agent-host-maintenance -p ExecStart --value', text)
        self.assertIn("STOP: maintenance service has a non-empty PYTHONPATH", text)

    def test_systemd_uses_current_release_and_clears_pythonpath(self) -> None:
        text = UNIT.read_text()

        self.assertIn("Environment=PYTHONPATH=", text)
        self.assertIn(
            "ExecStart=%h/.local/share/coding-maintenance/current/venv/bin/python "
            "-m host_maintenance.server",
            text,
        )
        self.assertNotIn("/releases/", text)
        self.assertNotIn("/venv/bin/coding-agent-host-maintenance", text)


if __name__ == "__main__":
    unittest.main()
