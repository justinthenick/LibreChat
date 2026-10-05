import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from host_maintenance import codex_adapter as adapter
from host_maintenance.relay_policy import validate_relay
from test_relay_policy import specimen, IMAGE, SOCKET, KEY


class ReviewRegressionTests(unittest.TestCase):
    def test_retargeted_codex_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            good = root / "reviewed"
            bad = root / "unreviewed"
            marker = root / "executed"
            good.write_text("#!/bin/sh\nprintf '%s\n' 'codex-cli 0.154.0'\n")
            bad.write_text(f"#!/bin/sh\ntouch {marker}\n")
            good.chmod(0o755)
            bad.chmod(0o755)
            link = root / "codex"
            link.symlink_to(good)
            with patch.object(adapter, "CODEX", link), patch.object(
                adapter, "CODEX_EXPECTED_SHA256", hashlib.sha256(good.read_bytes()).hexdigest()
            ):
                adapter._validate_codex_identity()
                link.unlink()
                link.symlink_to(bad)
                with self.assertRaisesRegex(RuntimeError, "identity mismatch"):
                    adapter.run_codex("hello")
            self.assertFalse(marker.exists())

    def test_missing_relay_key_fails_closed(self):
        with self.assertRaises(RuntimeError):
            info = specimen()
            info["Config"]["Env"] = [v for v in info["Config"]["Env"] if not v.startswith("RELAY_SIGNING_KEY=")]
            validate_relay(info, IMAGE, SOCKET, KEY)

    def test_custom_adapter_root_fails_before_deployment(self):
        deploy = Path(__file__).resolve().parents[1] / "bin/deploy-maintenance-release.sh"
        env = dict(os.environ, CODING_CODEX_ADAPTER_ROOT="/unsupported/adapter-root")
        result = subprocess.run(["bash", str(deploy)], cwd="/tmp",
                                env=env, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("adapter root override is unsupported", result.stdout)


    def test_replacement_after_version_check_executes_validated_descriptor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "codex"
            replacement = root / "replacement"
            marker = root / "unexpected"
            output = json.dumps({"type": "item.completed", "item": {
                "type": "agent_message", "text": "REVIEWED"}})
            binary.write_text("#!/bin/sh\nif [ \"$1\" = --version ]; then "
                              "echo 'codex-cli 0.154.0'; else "
                              f"printf '%s\\n' '{output}'; fi\n")
            replacement.write_text(f"#!/bin/sh\ntouch {marker}\n")
            binary.chmod(0o755)
            replacement.chmod(0o755)
            digest = hashlib.sha256(binary.read_bytes()).hexdigest()
            original_run = subprocess.run
            observed = []

            def replace_after_check(argv, **kwargs):
                observed.append(argv[0])
                result = original_run(argv, **kwargs)
                if argv[1] == "--version":
                    replacement.replace(binary)
                    descriptor = kwargs["pass_fds"][0]
                    with self.assertRaises(OSError):
                        os.write(descriptor, b"unreviewed")
                return result

            with patch.object(adapter, "CODEX", binary), patch.object(
                adapter, "CODEX_EXPECTED_SHA256", digest
            ), patch.object(adapter.subprocess, "run", replace_after_check):
                self.assertEqual(adapter.run_codex("hello"), {"ok": True, "text": "REVIEWED"})
            self.assertEqual(observed[0], observed[1])
            self.assertFalse(marker.exists())

    def test_rotated_and_duplicate_relay_keys_fail_without_disclosure(self):
        for environment in [
            ["RELAY_SIGNING_KEY=" + "d" * 64],
            ["RELAY_SIGNING_KEY=" + KEY.hex(), "RELAY_SIGNING_KEY=" + KEY.hex()],
        ]:
            info = specimen()
            info["Config"]["Env"] = [v for v in info["Config"]["Env"]
                                    if not v.startswith("RELAY_SIGNING_KEY=")] + environment
            with self.assertRaises(RuntimeError) as raised:
                validate_relay(info, IMAGE, SOCKET, KEY)
            self.assertNotIn(KEY.hex(), str(raised.exception))
            self.assertNotIn("d" * 64, str(raised.exception))
