import json
import os
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_deploy_rollback import DEPLOY, DOCKER

IMAGE = "sha256:" + "a" * 64
KEY = "b" * 64


class ActivationPreflightTests(unittest.TestCase):
    def test_invalid_activation_never_reaches_docker_or_exposes_key(self):
        text = DEPLOY.read_text()
        fragment = text[text.index('RELAY_SIGNING_KEY="$('):text.index("\nCURRENT_CONTAINER=")]
        for policy in ({}, {"acp_image_id": IMAGE},
                       {"acp_image_id": "latest", "acp_relay_signing_key": KEY},
                       {"acp_image_id": IMAGE, "acp_relay_signing_key": "invalid"}):
            with self.subTest(policy_fields=list(policy)), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / "policy.json"
                config.write_text(json.dumps(policy))
                marker = root / "docker-called"
                shell = ('set -Eeuo pipefail\nCONFIG=' + shlex.quote(str(config)) +
                         '\ndocker() { touch ' + shlex.quote(str(marker)) + '; }\n' + fragment)
                result = subprocess.run(["bash", "-c", shell], text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(marker.exists())
                self.assertNotIn(KEY, result.stdout + result.stderr)

    def test_activation_validation_precedes_backup_build_and_stop(self):
        text = DEPLOY.read_text()
        validation = text.index('RELAY_SIGNING_KEY="$(')
        for marker in ('echo "=== PREPARE BACKUP ==="', 'echo "=== CREATE IMMUTABLE RELEASE ==="',
                       'echo "=== PREPARE SWITCH ==="'):
            self.assertLess(validation, text.index(marker))
        self.assertLess(text.index('test "$(sha256sum "$CONFIG"'), text.index("\nARMED=1"))

    def test_policy_change_fails_before_arming(self):
        text = DEPLOY.read_text()
        fragment = text[text.index('echo "=== PREPARE SWITCH ==="'):text.index('\nsystemctl --user stop')]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy"
            path.write_text("{}")
            shell = ('set -Eeuo pipefail\nCONFIG=' + shlex.quote(str(path)) +
                     '\nCONFIG_DIGEST=changed\n' + fragment + '\necho ACTIVATED\n')
            result = subprocess.run(["bash", "-c", shell], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("ACTIVATED", result.stdout)


class SavedRollbackTests(unittest.TestCase):
    def run_recovery(self, *, drift=False, missing_backup=False, sandbox=False, daemon_failure=False):
        text = DEPLOY.read_text()
        functions = text[text.index("restore_file() {"):text.index("\nrollback() {")]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            backup = root / "backup"
            backup.mkdir(mode=0o700)
            old = root / "old"
            release = root / "release"
            old.mkdir()
            release.mkdir()
            current = root / "current"
            current.symlink_to(release)
            values = {
                "BACKUP": backup, "COMPOSE": root / "compose", "CONFIG": root / "policy",
                "UNIT": root / "host.service", "CODEX_UNIT": root / "adapter.service",
                "CODEX_CANDIDATE_DROPIN": root / "candidate.conf",
                "RUNTIME_DROPIN": root / "runtime.conf", "CURRENT": current,
                "OLD_CURRENT": old, "RELEASE": release, "PROJECT": "test",
                "OLD_CODEX_ACTIVE": "1", "RELAY_SWITCHED": "1",
                "RELAY_CONTAINER": "relay", "RELAY_BACKUP": "relay-backup",
                "OLD_RELAY_ID": "old-id", "OLD_RELAY_RUNNING": "true",
                "NEW_RELAY_ID": "new-id", "NEW_EXECUTOR_ID": "executor-id",
                "OLD_EXECUTOR_IMAGE": IMAGE,
            }
            names = {"compose.json": "COMPOSE", "policy.json": "CONFIG",
                     "unit.service": "UNIT", "codex-unit.service": "CODEX_UNIT",
                     "codex-candidate.conf": "CODEX_CANDIDATE_DROPIN"}
            for saved, key in names.items():
                (backup / saved).write_text("original-" + key)
                Path(values[key]).write_text("replacement-" + key)
            Path(values["RUNTIME_DROPIN"]).write_text("replacement-dropin")
            state = root / "state"
            containers = {
                "old-id": {"name": "relay-backup", "running": False},
                "new-id": {"name": "relay", "running": True},
                "executor-id": {"name": "librechat-coding-executor", "running": True},
            }
            if missing_backup:
                del containers["old-id"]
            if drift:
                containers["new-id"]["name"] = "different-relay"
            state.write_text(json.dumps({"containers": containers, "calls": [],
                                        "executor_image": "replacement-image"}))
            mock = DOCKER.replace('if action == "inspect":', """
if action == "image":
    print(os.environ["OLD_IMAGE"])
elif action == "ps":
    if os.environ["SANDBOX"] == "1":
        print("active-sandbox")
    elif os.environ["SANDBOX"] == "2":
        status = 1
elif action == "compose":
    state["executor_image"] = os.environ["OLD_IMAGE"]
elif action == "inspect":""").replace(
                'print(identity if fmt == "{{.Id}}" else',
                'print(state["executor_image"] if fmt == "{{.Image}}" else identity if fmt == "{{.Id}}" else')
            docker = root / "docker"
            docker.write_text(mock)
            docker.chmod(0o755)
            systemctl = root / "systemctl"
            systemctl.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$SYSTEM_CALLS\"\n")
            systemctl.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + ":" + os.environ["PATH"],
                       STATE=str(state), FAILURE="none", OLD_IMAGE=IMAGE,
                       SANDBOX="2" if daemon_failure else str(int(sandbox)), SYSTEM_CALLS=str(root / "system-calls"))
            assignments = "\n".join(key + "=" + shlex.quote(str(value)) for key, value in values.items())
            result = subprocess.run(["bash", "-c", "set -Eeuo pipefail\n" + assignments +
                                     "\n" + functions + "\nwrite_rollback"], env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            script = backup / "rollback.sh"
            self.assertEqual(script.stat().st_mode & 0o777, 0o700)
            self.assertNotIn("RELAY_SIGNING_KEY", script.read_text())
            result = subprocess.run(["bash", str(script)], env=env, text=True, capture_output=True)
            actual = json.loads(state.read_text())
            if drift or missing_backup or sandbox or daemon_failure:
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((root / "system-calls").exists())
                self.assertEqual(actual["containers"], containers)
                self.assertEqual(current.resolve(), release)
                return
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(current.resolve(), old)
            self.assertNotIn("new-id", actual["containers"])
            self.assertEqual(actual["containers"]["old-id"], {"name": "relay", "running": True})
            self.assertEqual(actual["executor_image"], IMAGE)
            for saved, key in names.items():
                self.assertEqual(Path(values[key]).read_text(), "original-" + key)
            self.assertFalse(Path(values["RUNTIME_DROPIN"]).exists())

    def test_saved_rollback_restores_files_release_and_containers(self):
        self.run_recovery()

    def test_runtime_drift_fails_before_any_stop(self):
        self.run_recovery(drift=True)

    def test_missing_retained_relay_fails_before_any_stop(self):
        self.run_recovery(missing_backup=True)

    def test_active_sandbox_fails_before_any_stop(self):
        self.run_recovery(sandbox=True)

    def test_failed_sandbox_query_fails_before_any_stop(self):
        self.run_recovery(daemon_failure=True)
