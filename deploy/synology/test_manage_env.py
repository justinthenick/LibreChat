#!/usr/bin/env python3
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("manage_env", HERE / "manage-env.py")
manage_env = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage_env)


class ManageEnvTests(unittest.TestCase):
    def setUp(self):
        self.schema, self.settings = manage_env.load_schema(HERE / "admin-settings.schema.json")
        self.temp = tempfile.TemporaryDirectory()
        self.env = Path(self.temp.name) / ".env"
        self.env.write_text(
            "# preserved comment\n"
            "NAS_HOST=192.168.1.5\n"
            "LIBRECHAT_SCHEME=http\n"
            "LIBRECHAT_PORT=3200\n"
            "NO_INDEX=true\n"
            "SEARCH=false\n"
            "SESSION_COOKIE_SECURE=false\n"
            "ALLOW_EMAIL_LOGIN=true\n"
            "ALLOW_REGISTRATION=true\n"
            "ALLOW_SOCIAL_LOGIN=false\n"
            "ALLOW_SOCIAL_REGISTRATION=false\n"
            "ALLOW_UNVERIFIED_EMAIL_LOGIN=true\n"
            "ALLOW_PASSWORD_RESET=false\n"
            "OPENROUTER_KEY=secret-do-not-print\n"
            "JWT_SECRET=locked-secret\n"
            "UNMANAGED_KEEP_ME=hello\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_optional_admin_panel_url_can_be_missing(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = manage_env.command_validate(self.schema, self.settings, self.env)
        self.assertEqual(rc, 0)
        self.assertIn("Managed .env validation OK", output.getvalue())

    def test_show_redacts_secret_values(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            manage_env.command_show(self.schema, self.settings, self.env)
        rendered = output.getvalue()
        self.assertIn("OPENROUTER_KEY", rendered)
        self.assertIn("CONFIGURED", rendered)
        self.assertNotIn("secret-do-not-print", rendered)
        self.assertNotIn("locked-secret", rendered)

    def test_set_preserves_unmanaged_lines_and_creates_backup(self):
        rc = manage_env.command_set(self.settings, self.env, "SEARCH", "true", True)
        self.assertEqual(rc, 0)
        text = self.env.read_text(encoding="utf-8")
        self.assertIn("# preserved comment", text)
        self.assertIn("UNMANAGED_KEEP_ME=hello", text)
        self.assertIn("SEARCH=true", text)
        backups = list(self.env.parent.glob(".env.backup-*"))
        self.assertEqual(len(backups), 1)

    def test_duplicate_managed_key_is_rejected(self):
        with self.env.open("a", encoding="utf-8") as handle:
            handle.write("SEARCH=true\n")
        with self.assertRaises(manage_env.SettingsError):
            manage_env.read_env(self.env, set(self.settings))

    def test_derived_domains_follow_host_scheme_and_port(self):
        _, values, _ = manage_env.read_env(self.env, set(self.settings))
        derived = manage_env.derive_values(values)
        self.assertEqual(derived["DOMAIN_CLIENT"], "http://192.168.1.5:3200")
        self.assertEqual(derived["DOMAIN_SERVER"], "http://192.168.1.5:3200")

    def test_locked_secret_cannot_be_changed_with_set(self):
        with self.assertRaises(manage_env.SettingsError):
            manage_env.command_set(self.settings, self.env, "JWT_SECRET", "replacement", True)


if __name__ == "__main__":
    unittest.main()
