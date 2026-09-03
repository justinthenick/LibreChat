#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("admin_worker", HERE / "admin-settings-worker.py")
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.schema, self.settings = worker.manage_env.load_schema(HERE / "admin-settings.schema.json")
        self.temp = tempfile.TemporaryDirectory()
        self.env = Path(self.temp.name) / ".env"
        self.env.write_text(
            "NAS_HOST=192.168.1.5\n"
            "LIBRECHAT_SCHEME=http\n"
            "LIBRECHAT_PORT=3200\n"
            "ADMIN_SETTINGS_PORT=3210\n"
            "ADMIN_PANEL_URL=http://192.168.1.5:3210\n"
            "NO_INDEX=true\n"
            "SEARCH=false\n"
            "SESSION_COOKIE_SECURE=false\n"
            "ALLOW_EMAIL_LOGIN=true\n"
            "ALLOW_REGISTRATION=true\n"
            "ALLOW_SOCIAL_LOGIN=false\n"
            "ALLOW_SOCIAL_REGISTRATION=false\n"
            "ALLOW_UNVERIFIED_EMAIL_LOGIN=true\n"
            "ALLOW_PASSWORD_RESET=false\n"
            "OPENROUTER_KEY=provider-secret\n"
            "ADMIN_SETTINGS_ACCESS_TOKEN=panel-secret\n"
            "JWT_SECRET=jwt-secret\n"
            "UNMANAGED_KEEP=hello\n",
            encoding="utf-8",
        )
        _, self.values, _ = worker.manage_env.read_env(self.env, set(self.settings))

    def tearDown(self):
        self.temp.cleanup()

    def test_state_hides_all_secret_values_and_hidden_token(self):
        state = worker.sanitize_state(self.schema, self.settings, self.values)
        rendered = str(state)
        self.assertNotIn("provider-secret", rendered)
        self.assertNotIn("panel-secret", rendered)
        self.assertNotIn("jwt-secret", rendered)
        keys = [item["key"] for item in state["settings"]]
        self.assertNotIn("ADMIN_SETTINGS_ACCESS_TOKEN", keys)
        openrouter = next(item for item in state["settings"] if item["key"] == "OPENROUTER_KEY")
        self.assertTrue(openrouter["configured"])

    def test_preview_normalizes_and_identifies_affected_service(self):
        plan = worker.build_plan(self.schema, self.settings, self.values, {"updates": {"SEARCH": "true"}})
        self.assertEqual(plan["normalized"]["SEARCH"], "true")
        self.assertEqual(plan["services"], ["api"])
        self.assertTrue(plan["restart_required"])

    def test_hidden_admin_token_cannot_be_changed_from_web_payload(self):
        with self.assertRaises(worker.WorkerError):
            worker.build_plan(self.schema, self.settings, self.values, {"secrets": {"ADMIN_SETTINGS_ACCESS_TOKEN": "replacement"}})

    def test_empty_secret_replacement_is_rejected(self):
        with self.assertRaises(worker.WorkerError):
            worker.build_plan(self.schema, self.settings, self.values, {"secrets": {"OPENROUTER_KEY": ""}})

    def test_https_without_secure_cookie_returns_warning(self):
        plan = worker.build_plan(self.schema, self.settings, self.values, {"updates": {"LIBRECHAT_SCHEME": "https"}})
        self.assertTrue(any("SESSION_COOKIE_SECURE" in warning for warning in plan["warnings"]))

    def test_replace_many_preserves_unmanaged_lines(self):
        lines, _, positions = worker.manage_env.read_env(self.env, set(self.settings))
        out = worker.replace_many(lines, positions, {"SEARCH": "true", "ALLOW_REGISTRATION": "false"})
        text = "".join(out)
        self.assertIn("UNMANAGED_KEEP=hello", text)
        self.assertIn("SEARCH=true", text)
        self.assertIn("ALLOW_REGISTRATION=false", text)


if __name__ == "__main__":
    unittest.main()
