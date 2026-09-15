import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("bootstrap", ROOT / "bootstrap-admin-settings.py")
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class SecretMigrationTests(unittest.TestCase):
    def test_missing_secret_is_independent_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            original = "ADMIN_SETTINGS_ACCESS_TOKEN=recovery\nADMIN_PANEL_URL=https://admin.example.com\n"
            env.write_text(original)
            self.assertTrue(bootstrap.ensure_official_session_secret(env))
            migrated = env.read_text()
            _, values, _ = bootstrap.manage_env.read_env(env, {"ADMIN_PANEL_SESSION_SECRET"})
            self.assertEqual(len(values["ADMIN_PANEL_SESSION_SECRET"]), 64)
            self.assertNotEqual(values["ADMIN_PANEL_SESSION_SECRET"], "recovery")
            self.assertTrue(migrated.startswith(original))
            self.assertFalse(bootstrap.ensure_official_session_secret(env))
            self.assertEqual(env.read_text(), migrated)
            self.assertEqual(len(list(Path(directory).glob(".env.backup-*"))), 1)

    def test_existing_secret_is_preserved_exactly(self):
        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            original = 'ADMIN_PANEL_SESSION_SECRET="' + "a" * 64 + '"\n'
            env.write_text(original)
            self.assertFalse(bootstrap.ensure_official_session_secret(env))
            self.assertEqual(env.read_text(), original)

    def test_duplicate_secret_fails_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            original = "ADMIN_PANEL_SESSION_SECRET=\nADMIN_PANEL_SESSION_SECRET=existing\n"
            env.write_text(original)
            with self.assertRaises(bootstrap.manage_env.SettingsError):
                bootstrap.ensure_official_session_secret(env)
            self.assertEqual(env.read_text(), original)


class HealthGateTests(unittest.TestCase):
    def functions(self):
        script = (ROOT / "autodeploy.sh").read_text()
        return script[script.index("admin_panel_check() {"):script.index("configure_admin_worker() {")]

    def run_shell(self, body):
        return subprocess.run(["sh", "-c", body], capture_output=True, text=True).returncode

    def test_steady_state_requires_each_panel(self):
        stubs = "\n".join(name + "() { return 0; }" for name in (
            "health_check", "production_agent_seed", "workspace_check", "cloudflare_check",
            "admin_worker_check", "nas_infra_runtime_check"))
        for custom, official in ((0, 0), (1, 0), (0, 1)):
            body = self.functions() + stubs + "\nadmin_panel_check() { return %d; }\nofficial_admin_panel_check() { return %d; }\nsteady_state_check" % (custom, official)
            self.assertEqual(self.run_shell(body), 0 if custom == official == 0 else 1)

    def test_official_probe_handles_container_and_http_failures(self):
        for running, http_result in (("true", 0), ("false", 0), ("", 0), ("true", 1)):
            body = self.functions() + '\nADMIN_SETTINGS_ENABLED=1\ndocker() { printf "%s" "' + running + '"; }\nenv_value() { printf 3220; }\npython3() { return ' + str(http_result) + '; }\nofficial_admin_panel_check'
            self.assertEqual(self.run_shell(body), 0 if running == "true" and http_result == 0 else 1)

    def test_disabled_overlay_requires_official_container_absent(self):
        for exists in (0, 1):
            body = self.functions() + "\nADMIN_SETTINGS_ENABLED=0\ndocker() { return %d; }\nofficial_admin_panel_check" % exists
            self.assertEqual(self.run_shell(body), 1 if exists == 0 else 0)


if __name__ == "__main__":
    unittest.main()
