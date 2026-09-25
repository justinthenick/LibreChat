import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("renderer", ROOT / "render-librechat-config.py")
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)

TELEMETRY_SPEC = importlib.util.spec_from_file_location("launchpad_telemetry", ROOT / "launchpad-telemetry.py")
telemetry = importlib.util.module_from_spec(TELEMETRY_SPEC)
TELEMETRY_SPEC.loader.exec_module(telemetry)


class MaintenanceIntegrationTests(unittest.TestCase):
    def test_endpoint_and_private_address_render_without_materializing_secret(self):
        rendered = renderer.render((ROOT / "librechat.yaml").read_text(), {
            "CODING_MAINTENANCE_HOST": "192.168.1.120", "CODING_MAINTENANCE_PORT": "8767",
            "CODING_MAINTENANCE_TOKEN": "never-render-this-secret"})
        self.assertIn("- '192.168.1.120:8767'", rendered)
        self.assertIn("url: 'http://192.168.1.120:8767/mcp'", rendered)
        self.assertIn("Bearer ${CODING_MAINTENANCE_TOKEN}", rendered)
        self.assertNotIn("never-render-this-secret", rendered)
        self.assertNotIn("${CODING_MAINTENANCE_HOST}", rendered)

    def test_invalid_endpoint_values_are_rejected(self):
        template = (ROOT / "librechat.yaml").read_text()
        for values in ({"CODING_MAINTENANCE_HOST": "host/path"},
                       {"CODING_MAINTENANCE_PORT": "0"}, {"CODING_MAINTENANCE_PORT": "65536"},
                       {"CODING_MAINTENANCE_PORT": "not-a-port"}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                renderer.render(template, values)


class LaunchpadMaintenanceTelemetryTests(unittest.TestCase):
    @patch.object(telemetry, "run")
    def test_maintenance_configured_and_reachable(self, mock_run):
        mock_run.return_value = (
            0,
            json.dumps({
                "endpoint_configured": True,
                "token_configured": True,
                "reachable": True,
                "ok": True,
                "host": "maintenance.internal",
                "token": "never-expose-me",
            }),
            "",
        )

        result = telemetry.maintenance_snapshot()

        self.assertEqual(result, {
            "endpoint_configured": True,
            "token_configured": True,
            "reachable": True,
            "ok": True,
        })

    @patch.object(telemetry, "run")
    def test_maintenance_configured_and_unreachable(self, mock_run):
        mock_run.return_value = (
            0,
            json.dumps({
                "endpoint_configured": True,
                "token_configured": True,
                "reachable": False,
                "ok": False,
                "error_code": "maintenance_unreachable",
            }),
            "",
        )

        self.assertEqual(telemetry.maintenance_snapshot(), {
            "endpoint_configured": True,
            "token_configured": True,
            "reachable": False,
            "ok": False,
            "error_code": "maintenance_unreachable",
        })

    @patch.object(telemetry, "run")
    def test_maintenance_missing_endpoint_configuration(self, mock_run):
        mock_run.return_value = (
            0,
            json.dumps({
                "endpoint_configured": False,
                "token_configured": False,
                "reachable": False,
            }),
            "",
        )

        self.assertEqual(telemetry.maintenance_snapshot(), {
            "endpoint_configured": False,
            "token_configured": False,
            "reachable": False,
        })

    @patch.object(telemetry, "run")
    def test_maintenance_probe_failure_does_not_expose_raw_error(self, mock_run):
        mock_run.return_value = (
            1,
            "",
            "connect maintenance.internal:8767 token=super-secret-value",
        )

        result = telemetry.maintenance_snapshot()
        serialized = json.dumps(result)

        self.assertEqual(result, {"ok": False, "error_code": "maintenance_probe_failed"})
        self.assertNotIn("maintenance.internal", serialized)
        self.assertNotIn("8767", serialized)
        self.assertNotIn("super-secret-value", serialized)

    @patch.object(telemetry, "run")
    def test_maintenance_non_json_response_does_not_expose_probe_output(self, mock_run):
        mock_run.return_value = (
            0,
            "maintenance.internal token=super-secret-value",
            "",
        )

        result = telemetry.maintenance_snapshot()
        serialized = json.dumps(result)

        self.assertEqual(result, {"ok": False, "error_code": "maintenance_non_json_response"})
        self.assertNotIn("maintenance.internal", serialized)
        self.assertNotIn("super-secret-value", serialized)

    @patch.object(telemetry, "maintenance_snapshot")
    @patch.object(telemetry, "executor_snapshot")
    @patch.object(telemetry, "managed_skills_snapshot")
    @patch.object(telemetry, "skill_sync_snapshot")
    @patch.object(telemetry, "checkout_snapshot")
    def test_main_snapshot_includes_coding_maintenance(
        self, mock_checkout, mock_sync, mock_skills, mock_executor, mock_maintenance
    ):
        mock_checkout.return_value = {
            "ok": True,
            "branch": "server/synology",
            "commit": "dd154463e64a6d5175545ba10e847de63b03eff0",
        }
        mock_sync.return_value = {"ok": True, "found": True}
        mock_skills.return_value = {"ok": True, "count": 0, "names": [], "skills": []}
        mock_executor.return_value = {
            "endpoint_configured": True,
            "token_configured": True,
            "reachable": True,
        }
        mock_maintenance.return_value = {
            "endpoint_configured": True,
            "token_configured": True,
            "reachable": True,
            "ok": True,
        }

        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(telemetry.main(), 0)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["coding_maintenance"], mock_maintenance.return_value)


if __name__ == '__main__':
    unittest.main()
