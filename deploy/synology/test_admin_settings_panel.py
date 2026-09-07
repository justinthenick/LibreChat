import importlib.util
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


panel = load("admin_settings_panel", ROOT / "admin-settings-panel.py")
renderer = load("render_librechat_config", ROOT / "render-librechat-config.py")


class AdminPasswordTests(unittest.TestCase):
    def test_password_hash_round_trip(self):
        encoded = panel.hash_password("correct horse battery staple")
        self.assertTrue(panel.verify_password("correct horse battery staple", encoded))
        self.assertFalse(panel.verify_password("wrong password entirely", encoded))

    def test_short_password_rejected(self):
        with self.assertRaises(ValueError):
            panel.hash_password("too-short")

    def test_session_signature_and_expiry_shape(self):
        secret = "test-session-secret-that-is-not-production"
        token = panel.make_session(secret)
        self.assertTrue(panel.verify_session(token, secret))
        self.assertFalse(panel.verify_session(token, secret + "-wrong"))

    def test_password_state_is_persistent_and_not_plaintext(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = panel.AUTH_PATH
            try:
                panel.AUTH_PATH = Path(tmp) / "auth.json"
                state = panel.write_auth_state("a sufficiently long admin password")
                raw = panel.AUTH_PATH.read_text(encoding="utf-8")
                self.assertNotIn("a sufficiently long admin password", raw)
                self.assertTrue(panel.verify_password("a sufficiently long admin password", state["password_hash"]))
                self.assertTrue(state["session_secret"])
            finally:
                panel.AUTH_PATH = original


class RuntimeConfigRendererTests(unittest.TestCase):
    TEMPLATE = """endpoints:\n  custom:\n    - name: 'OpenRouter'\n      # BEGIN MANAGED OPENROUTER MODELS\n      models:\n        default:\n          - 'deepseek/deepseek-v3.2'\n        fetch: true\n      # END MANAGED OPENROUTER MODELS\n      titleConvo: true\n"""

    def test_empty_allowlist_fetches_provider_catalogue(self):
        rendered = renderer.render(self.TEMPLATE, {"ALLOWED_MODELS": ""})
        self.assertIn("fetch: true", rendered)
        self.assertIn("deepseek/deepseek-v3.2", rendered)

    def test_allowlist_disables_provider_fetch(self):
        rendered = renderer.render(
            self.TEMPLATE,
            {"ALLOWED_MODELS": "google/gemini-2.5-pro,deepseek/deepseek-v3.2"},
        )
        self.assertIn("fetch: false", rendered)
        self.assertIn("google/gemini-2.5-pro", rendered)
        self.assertIn("deepseek/deepseek-v3.2", rendered)

    def test_allowlist_is_deduplicated(self):
        rendered = renderer.render(
            self.TEMPLATE,
            {"ALLOWED_MODELS": "google/gemini-2.5-pro,google/gemini-2.5-pro"},
        )
        self.assertEqual(rendered.count("          - 'google/gemini-2.5-pro'"), 1)

    def test_invalid_model_id_rejected(self):
        with self.assertRaises(ValueError):
            renderer.render(self.TEMPLATE, {"ALLOWED_MODELS": "model id with spaces"})


if __name__ == "__main__":
    unittest.main()
