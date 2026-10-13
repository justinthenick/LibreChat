import importlib.util
import itertools
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dns_worker", HERE / "admin-settings-worker.py")
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)
manage = worker.manage_env


class DNSOverlaySelectionTests(unittest.TestCase):
    def test_all_entrypoints_preserve_overlay_order_and_arguments(self):
        source = (HERE / "autodeploy.sh").read_text()
        function = source.split("compose() {\n", 1)[1].split("\nread_last_success()", 1)[0]
        function = "compose() {\n" + function
        with tempfile.TemporaryDirectory(prefix="dns overlay ") as directory:
            root = Path(directory)
            env = root / ".env"
            bin_dir = root / "bin"
            bin_dir.mkdir()
            stub = bin_dir / "docker-compose"
            stub.write_text('#!/bin/sh\nprintf \'%s\\n\' docker-compose "$@"\n')
            stub.chmod(0o755)
            for cloud, admin, dns in itertools.product((False, True), repeat=3):
                with self.subTest(cloud=cloud, admin=admin, dns=dns):
                    values = {"CLOUDFLARE_TUNNEL_TOKEN": "fixture" if cloud else "",
                              "ADMIN_SETTINGS_ACCESS_TOKEN": "fixture" if admin else ""}
                    env.write_text("".join(f"{key}={value}\n" for key, value in values.items()))
                    for name in ("docker-compose.cloudflare.yml", "docker-compose.admin.yml"):
                        (root / name).write_text("")
                    dns_path = root / "docker-compose.dns.yml"
                    if dns:
                        dns_path.write_text((HERE / "docker-compose.dns.yml.example").read_text())
                    elif dns_path.exists():
                        dns_path.unlink()
                    files = [root / "docker-compose.yml"]
                    if cloud:
                        files.append(root / "docker-compose.cloudflare.yml")
                    if admin:
                        files.append(root / "docker-compose.admin.yml")
                    if dns:
                        files.append(dns_path)
                    args = ["up", "-d", "--no-deps", "--force-recreate", "api"]
                    expected = ["docker-compose"]
                    for file in files:
                        expected.extend(["-f", str(file)])
                    expected.extend(args)
                    self.assertEqual(manage.compose_command(env, args), expected)
                    with patch.object(worker, "ROOT", root):
                        self.assertEqual(worker.compose_cmd(values, args), expected)
                    variables = {"DEPLOY_DIR": str(root),
                                 "CLOUDFLARE_OVERLAY": str(root / "docker-compose.cloudflare.yml"),
                                 "ADMIN_OVERLAY": str(root / "docker-compose.admin.yml"),
                                 "CLOUDFLARE_ENABLED": str(int(cloud)),
                                 "ADMIN_SETTINGS_ENABLED": str(int(admin))}
                    shell = "\n".join(f"{key}={shlex.quote(value)}"
                                      for key, value in variables.items())
                    shell += "\n"
                    shell += function + "\ncompose " + shlex.join(args)
                    result = subprocess.run(["sh", "-eu", "-c", shell], text=True,
                                            capture_output=True, timeout=5, check=True,
                                            env=dict(os.environ, PATH=str(bin_dir) + ":" + os.environ["PATH"]))
                    self.assertEqual(result.stdout.splitlines(), expected)

    def test_example_alone_does_not_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = root / ".env"
            env.write_text("")
            (root / "docker-compose.dns.yml.example").write_text(
                (HERE / "docker-compose.dns.yml.example").read_text())
            self.assertEqual(manage.compose_command(env, ["config"]),
                             ["docker-compose", "-f", str(root / "docker-compose.yml"), "config"])


class DNSOverlayComposeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = shlex.split(os.environ.get("COMPOSE_TEST_COMMAND", "docker compose"))
        try:
            subprocess.run(cls.command + ["version"], capture_output=True, check=True, timeout=10)
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise unittest.SkipTest("An existing Compose CLI is required for parser-only tests")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / "base.yml"
        self.overlay = self.root / "dns.yml"
        self.base.write_text(json.dumps({"version": "3.7", "services": {
            "api": {"image": "example.invalid/api:fixture", "environment": {"KEEP": "unchanged"}},
            "rag_api": {"image": "example.invalid/rag:fixture"}
        }}))
        self.overlay.write_text((HERE / "docker-compose.dns.yml.example").read_text())

    def config(self, overlay=False):
        args = self.command + ["-p", "dns-fixture", "-f", str(self.base)]
        if overlay:
            args += ["-f", str(self.overlay)]
        return subprocess.run(args + ["config"], cwd=self.root, text=True, capture_output=True,
                              timeout=15, env={"PATH": os.environ["PATH"], "HOME": str(self.root)})

    def test_default_has_no_dns_and_opt_in_changes_only_api_dns(self):
        before = self.config()
        after = self.config(overlay=True)
        self.assertEqual(before.returncode, 0, before.stderr)
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertNotIn("dns:", before.stdout)
        dns_block = "    dns:\n      - 100.100.100.100\n"
        if dns_block not in after.stdout:
            dns_block = "    dns:\n    - 100.100.100.100\n"
        self.assertEqual(after.stdout.count(dns_block), 1)
        self.assertEqual(after.stdout.replace(dns_block, ""), before.stdout)
        self.assertEqual(self.config().stdout, before.stdout)

    def test_invalid_dns_is_rejected_by_compose(self):
        self.overlay.write_text(json.dumps({"version": "3.7",
            "services": {"api": {"dns": {"invalid": "resolver"}}}}))
        self.assertNotEqual(self.config(overlay=True).returncode, 0)

    def test_existing_dns_is_preserved_by_default_and_merges_when_enabled(self):
        data = json.loads(self.base.read_text())
        data["services"]["api"]["dns"] = ["192.0.2.53"]
        self.base.write_text(json.dumps(data))
        before = self.config()
        after = self.config(overlay=True)
        self.assertEqual(before.returncode, 0, before.stderr)
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertIn("192.0.2.53", before.stdout)
        self.assertNotIn("100.100.100.100", before.stdout)
        self.assertIn("192.0.2.53", after.stdout)
        self.assertIn("100.100.100.100", after.stdout)


if __name__ == "__main__":
    unittest.main()
