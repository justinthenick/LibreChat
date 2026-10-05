#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

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

    def test_recreate_uses_long_docker_deadlines_for_affected_service_only(self):
        with patch.object(worker, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
            worker.recreate_services(self.values, ["api"])
        command = run.call_args.args[0]
        self.assertEqual(command[-5:], ["up", "-d", "--no-deps", "--force-recreate", "api"])
        self.assertGreater(run.call_args.kwargs["timeout"], 344)
        self.assertEqual(run.call_args.kwargs["env"]["COMPOSE_HTTP_TIMEOUT"], "300")
        self.assertEqual(run.call_args.kwargs["env"]["DOCKER_CLIENT_TIMEOUT"], "300")

    def test_run_passes_environment_and_enforces_deadline(self):
        env = dict(worker.os.environ, COMPOSE_HTTP_TIMEOUT="900")
        result = worker.run([sys.executable, "-c", "import os; print(os.environ['COMPOSE_HTTP_TIMEOUT'])"], env=env)
        self.assertEqual(result.stdout.strip(), "900")
        with self.assertRaisesRegex(worker.WorkerError, "timed out"):
            worker.run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.05)

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

    def test_coding_hosts_can_be_updated_together_without_changing_tokens(self):
        values = dict(self.values, CODING_EXECUTOR_HOST="192.0.2.20",
                      CODING_MAINTENANCE_HOST="192.0.2.20",
                      CODING_EXECUTOR_TOKEN="executor-secret",
                      CODING_MAINTENANCE_TOKEN="maintenance-secret")
        updates = {"CODING_EXECUTOR_HOST": "192.0.2.10",
                   "CODING_MAINTENANCE_HOST": "192.0.2.10"}
        plan = worker.build_plan(self.schema, self.settings, values, {"updates": updates})
        self.assertEqual(plan["normalized"], updates)
        self.assertEqual(plan["services"], ["api"])
        self.assertTrue(plan["restart_required"])
        self.assertNotIn("executor-secret", str(plan))
        self.assertNotIn("maintenance-secret", str(plan))
        lines = [key + "=" + value + "\n" for key, value in values.items()]
        positions = {key: index for index, key in enumerate(values)}
        result = "".join(worker.replace_many(lines, positions, plan["normalized"]))
        self.assertIn("CODING_EXECUTOR_TOKEN=executor-secret", result)
        self.assertIn("CODING_MAINTENANCE_TOKEN=maintenance-secret", result)

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

    def test_probe_coding_executor_unconfigured(self):
        res = worker.probe_coding_executor({})
        self.assertEqual(res, {
            "configured": False,
            "reachable": False,
            "status": "unconfigured",
            "version": None,
        })
        self.assertEqual(set(res.keys()), {"configured", "reachable", "status", "version"})

    @patch("urllib.request.urlopen")
    def test_probe_coding_executor_missing_token_is_unconfigured(self, mock_urlopen):
        env_vals = {
            "CODING_EXECUTOR_HOST": "127.0.0.1",
            "CODING_EXECUTOR_PORT": "4050",
            "CODING_EXECUTOR_TOKEN": "",
        }
        with patch.dict(worker.os.environ, {"CODING_EXECUTOR_TOKEN": ""}):
            res = worker.probe_coding_executor(env_vals)
        self.assertEqual(res, {
            "configured": False,
            "reachable": False,
            "status": "unconfigured",
            "version": None,
        })
        mock_urlopen.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_probe_coding_executor_healthy(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        payload = b'{"status": "healthy", "version": "0.1.12", "token": "leak"}'
        mock_resp.length = len(payload)

        def read_once(_size):
            mock_resp.length = 0
            mock_resp.fp = None
            return payload

        mock_resp.read1.side_effect = read_once
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        env_vals = {
            "CODING_EXECUTOR_HOST": "127.0.0.1",
            "CODING_EXECUTOR_PORT": "4050",
            "CODING_EXECUTOR_TOKEN": "secret-token-12345",
        }
        res = worker.probe_coding_executor(env_vals)
        self.assertEqual(res, {
            "configured": True,
            "reachable": True,
            "status": "healthy",
            "version": "0.1.12",
        })
        self.assertNotIn("secret-token-12345", str(res))
        self.assertNotIn("leak", str(res))
        self.assertNotIn("token", res)
        self.assertEqual(set(res.keys()), {"configured", "reachable", "status", "version"})
        self.assertEqual(mock_resp.read1.call_count, 1)

    @patch("urllib.request.urlopen")
    def test_probe_coding_executor_unreachable(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection refused")
        env_vals = {
            "CODING_EXECUTOR_HOST": "127.0.0.1",
            "CODING_EXECUTOR_PORT": "4050",
            "CODING_EXECUTOR_TOKEN": "secret-token-12345",
        }
        res = worker.probe_coding_executor(env_vals)
        self.assertEqual(res, {
            "configured": True,
            "reachable": False,
            "status": "unreachable",
            "version": None,
        })
        self.assertNotIn("secret-token-12345", str(res))
        self.assertEqual(set(res.keys()), {"configured", "reachable", "status", "version"})

    @patch("urllib.request.urlopen")
    def test_probe_coding_executor_malformed(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read1.side_effect = [b'invalid-non-json', b'']
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        env_vals = {
            "CODING_EXECUTOR_HOST": "127.0.0.1",
            "CODING_EXECUTOR_PORT": "4050",
            "CODING_EXECUTOR_TOKEN": "secret-token-12345",
        }
        res = worker.probe_coding_executor(env_vals)
        self.assertEqual(res, {
            "configured": True,
            "reachable": False,
            "status": "malformed",
            "version": None,
        })

    @patch("urllib.request.urlopen")
    def test_probe_coding_executor_rejects_oversized_health_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read1.return_value = b"x" * (worker.MAX_HEALTH_RESPONSE + 1)
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        env_vals = {
            "CODING_EXECUTOR_HOST": "127.0.0.1",
            "CODING_EXECUTOR_PORT": "4050",
            "CODING_EXECUTOR_TOKEN": "secret-token-12345",
        }
        res = worker.probe_coding_executor(env_vals)
        self.assertEqual(res, {
            "configured": True,
            "reachable": False,
            "status": "malformed",
            "version": None,
        })
        mock_resp.read1.assert_called_once_with(4096)

    @patch("urllib.request.urlopen")
    def test_probe_coding_executor_enforces_wall_clock_read_deadline(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read1.side_effect = [b"x", b"x"]
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        env_vals = {
            "CODING_EXECUTOR_HOST": "127.0.0.1",
            "CODING_EXECUTOR_PORT": "4050",
            "CODING_EXECUTOR_TOKEN": "secret-token-12345",
        }
        with patch.object(worker.time, "monotonic", side_effect=[0.0, 0.10, 0.20, 0.31]):
            res = worker.probe_coding_executor(env_vals, timeout=0.30)

        self.assertEqual(res, {
            "configured": True,
            "reachable": False,
            "status": "unreachable",
            "version": None,
        })
        self.assertEqual(mock_resp.read1.call_count, 2)
        socket_timeout = mock_resp.fp.raw._sock.settimeout
        self.assertEqual(socket_timeout.call_count, 2)
        self.assertAlmostEqual(socket_timeout.call_args_list[0].args[0], 0.20)
        self.assertAlmostEqual(socket_timeout.call_args_list[1].args[0], 0.10)

    @patch("urllib.request.urlopen")
    def test_probe_coding_executor_rejects_invalid_health_contract(self, mock_urlopen):
        env_vals = {
            "CODING_EXECUTOR_HOST": "127.0.0.1",
            "CODING_EXECUTOR_PORT": "4050",
            "CODING_EXECUTOR_TOKEN": "secret-token-12345",
        }
        payloads = (
            b'{}',
            b'{"status": 123, "version": "0.1.12"}',
            b'{"status": "ok"}',
            b'{"status": "ok", "version": 12}',
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                mock_resp = MagicMock()
                mock_resp.status = 200
                mock_resp.read1.side_effect = [payload, b""]
                mock_resp.__enter__.return_value = mock_resp
                mock_urlopen.return_value = mock_resp
                res = worker.probe_coding_executor(env_vals)
                self.assertEqual(res, {
                    "configured": True,
                    "reachable": False,
                    "status": "malformed",
                    "version": None,
                })

    def test_worker_core_state_handles_unconfigured_executor_gracefully(self):
        core = worker.WorkerCore(self.env, HERE / "admin-settings.schema.json", Path(self.temp.name))
        state = core.state()
        self.assertIn("coding_executor", state)
        self.assertEqual(set(state["coding_executor"].keys()), {"configured", "reachable", "status", "version"})
        self.assertFalse(state["coding_executor"]["configured"])

if __name__ == "__main__":
    unittest.main()
