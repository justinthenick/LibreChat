import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("renderer", ROOT / "render-librechat-config.py")
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


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


if __name__ == '__main__':
    unittest.main()
