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
        self.assertIn('for _ in range(60):', text)
        self.assertIn('time.sleep(1)', text)
        self.assertIn('executor did not reach verified healthy state', text)
        self.assertIn('assert health["health"] == "healthy"', text)
        self.assertIn('assert health["version"] == expected_executor', text)
        self.assertIn('systemctl --user show coding-agent-host-maintenance -p ExecStart --value', text)
        self.assertIn("STOP: maintenance service has a non-empty PYTHONPATH", text)

    def test_release_owns_codex_adapter_and_provider_relay(self) -> None:
        text = DEPLOY.read_text()

        self.assertIn(
            'RELAY_DIR="$REPO_ROOT/custom/coding-agent/provider-relay"',
            text,
        )
        self.assertIn(
            'cp -a "$RELAY_DIR" "$RELEASE/custom/coding-agent/"',
            text,
        )
        self.assertIn(
            'RELAY_TAG="librechat-acp-provider-relay:',
            text,
        )
        self.assertIn(
            'docker build',
            text,
        )
        self.assertIn(
            '-t "$RELAY_TAG"',
            text,
        )
        self.assertIn(
            'data["acp_relay_image_id"] = relay_image',
            text,
        )
        self.assertIn(
            'coding-agent-codex-adapter.service',
            text,
        )
        self.assertIn(
            'systemctl --user start coding-agent-codex-adapter',
            text,
        )
        self.assertIn(
            'RELAY_SIGNING_KEY="$RELAY_SIGNING_KEY"',
            text,
        )
        self.assertIn(
            '--network "$RELAY_NETWORK"',
            text,
        )
        self.assertIn(
            'dst=/run/codex-adapter,readonly',
            text,
        )
        self.assertIn(
            'RELAY_SWITCHED=1',
            text,
        )
        self.assertIn(
            'docker rename "$OLD_RELAY_ID" "$RELAY_CONTAINER"',
            text,
        )

    def test_release_verifies_codex_and_relay_runtime(self) -> None:
        text = DEPLOY.read_text()

        self.assertIn(
            'coding-agent-codex-adapter',
            text,
        )
        self.assertIn(
            'test -S "$CODEX_SOCKET"',
            text,
        )
        self.assertIn(
            '{{.HostConfig.ReadonlyRootfs}}',
            text,
        )
        self.assertIn(
            '{{len .Mounts}}',
            text,
        )
        self.assertIn(
            '{{len .NetworkSettings.Networks}}',
            text,
        )
        self.assertIn(
            "STOP: Codex adapter service has a non-empty PYTHONPATH",
            text,
        )

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

class CodexIdentityDeploymentContractTests(
    unittest.TestCase
):
    def test_release_preflight_pins_reviewed_codex_binary(
        self,
    ) -> None:
        text = DEPLOY.read_text()

        self.assertIn(
            "codex-cli 0.154.0",
            text,
        )

        self.assertIn(
            "3188814c35471432d4123203e0eb38e5bddc60226e3d7ddf0e59e649ea140022",
            text,
        )

        self.assertIn(
            'sha256sum "$CODEX_REAL"',
            text,
        )


class CodexCandidateDropInDeploymentTests(
    unittest.TestCase
):
    def test_release_neutralizes_candidate_dropin_and_rolls_back(
        self,
    ) -> None:
        text = DEPLOY.read_text()

        self.assertIn(
            'CODEX_DROPIN_DIR="$CODEX_UNIT.d"',
            text,
        )
        self.assertIn(
            'CODEX_CANDIDATE_DROPIN="$CODEX_DROPIN_DIR/candidate.conf"',
            text,
        )
        self.assertIn(
            '"$BACKUP/codex-candidate.conf"',
            text,
        )
        self.assertIn(
            'restore_file "$BACKUP/codex-candidate.conf" "$CODEX_CANDIDATE_DROPIN"',
            text,
        )
        self.assertIn(
            'rm -f "$CODEX_CANDIDATE_DROPIN"',
            text,
        )
        self.assertIn(
            'test ! -e "$CODEX_CANDIDATE_DROPIN"',
            text,
        )
        self.assertIn(
            'STOP: unexpected Codex adapter drop-in',
            text,
        )
        self.assertIn(
            'test -z "$CODEX_SYSTEMD_DROPINS"',
            text,
        )

    def test_release_requires_exact_lowercase_relay_signing_key(
        self,
    ) -> None:
        text = DEPLOY.read_text()

        self.assertIn(
            'r"[0-9a-f]{64}"',
            text,
        )
        self.assertNotIn(
            'r"[0-9a-fA-F]{64,}"',
            text,
        )
