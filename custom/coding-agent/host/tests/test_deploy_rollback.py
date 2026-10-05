"""Exercise the real deployment shell functions with fault-injected Docker."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

DEPLOY = Path(__file__).resolve().parents[1] / "bin/deploy-maintenance-release.sh"
DOCKER = r"""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
path = Path(os.environ["STATE"])
state = json.loads(path.read_text())
args = sys.argv[1:]
action = args[0]
target = args[1] if len(args) > 1 else ""
containers = state["containers"]
identity = next((key for key, value in containers.items()
                 if key == target or value["name"] == target), None)
failure = os.environ["FAILURE"]
status = 0
state["calls"].append(args)
if action == "inspect":
    if identity is None:
        status = 1
    elif "--format" in args:
        fmt = args[-1]
        print(identity if fmt == "{{.Id}}" else
              str(containers[identity]["running"]).lower())
elif action == "stop":
    if failure == "stop_before":
        status = 1
    else:
        containers[identity]["running"] = False
        status = int(failure == "stop_after")
elif action == "rename":
    if failure == "rename_before" and args[2] != "relay":
        status = 1
    else:
        containers[identity]["name"] = args[2]
        status = int(failure == "rename_after" and args[2] != "relay")
elif action == "start":
    containers[identity]["running"] = True
elif action == "rm":
    identity = args[-1]
    del containers[identity]
elif action == "run":
    if failure != "run_before":
        containers["new-id"] = {"name": "relay", "running": True}
    status = int(failure in ("run_before", "run_after"))
else:
    raise SystemExit("unexpected command")
path.write_text(json.dumps(state))
sys.exit(status)
"""


class DeploymentRollbackTests(unittest.TestCase):
    def run_case(self, failure, *, original=True, running=True, conflict=False):
        text = DEPLOY.read_text()
        functions = text[text.index("switch_relay() {"):text.index("\nrollback() {")]
        containers = {}
        if original:
            containers["old-id"] = {"name": "relay", "running": running}
        if conflict:
            containers["backup-id"] = {"name": "relay-rollback-test", "running": False}
        expected = json.loads(json.dumps(containers))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            state.write_text(json.dumps({"containers": containers, "calls": []}))
            docker = root / "docker"
            docker.write_text(DOCKER)
            docker.chmod(0o755)
            shell = r"""
set -Eeuo pipefail
RELAY_CONTAINER=relay
SHORT_SHA=test
RELAY_SWITCHED=0
OLD_RELAY_ID=""
OLD_RELAY_RUNNING=false
RELAY_BACKUP=""
""" + functions + r"""
failed() {
  trap - ERR
  set +e
  rollback_relay
  exit 19
}
trap failed ERR
switch_relay
docker run
false
"""
            result = subprocess.run(
                ["bash", "-c", shell], text=True, capture_output=True,
                env=dict(os.environ, PATH=str(root) + ":" + os.environ["PATH"],
                         STATE=str(state), FAILURE=failure),
            )
            actual = json.loads(state.read_text())
        self.assertEqual(result.returncode, 19, result.stderr)
        self.assertEqual(actual["containers"], expected, actual["calls"])
        self.assertNotIn(["rm", "-f", "old-id"], actual["calls"])

    def test_stop_and_rename_failures_restore_original(self):
        for failure in ("stop_before", "stop_after", "rename_before", "rename_after"):
            with self.subTest(failure=failure):
                self.run_case(failure)

    def test_partial_new_container_and_later_failure_restore_original(self):
        for failure in ("run_before", "run_after", "later"):
            with self.subTest(failure=failure):
                self.run_case(failure)

    def test_original_stopped_state_is_preserved(self):
        self.run_case("later", running=False)

    def test_existing_backup_is_preserved(self):
        self.run_case("later", conflict=True)

    def test_absent_original_leaves_no_relay_after_failure(self):
        for failure in ("run_before", "run_after", "later"):
            with self.subTest(failure=failure):
                self.run_case(failure, original=False)
