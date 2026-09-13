#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, str(ROOT / filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


worker = load("nas_infra_worker", "nas-infra-readonly-worker.py")
bridge = load("nas_infra_bridge", "nas-infra-readonly-mcp.py")


class WorkerSafetyTests(unittest.TestCase):
    def test_action_surface_is_read_only_and_fixed(self):
        forbidden = {"shell", "exec", "write", "delete", "remove", "restart", "stop", "start", "create"}
        for action in worker.ACTIONS:
            lowered = action.lower()
            self.assertFalse(any(word in lowered for word in forbidden), action)

    def test_unknown_action_rejected(self):
        with self.assertRaises(worker.WorkerError):
            worker.dispatch("docker_exec", {"command": "id"})

    def test_inspect_container_is_service_allowlisted(self):
        with self.assertRaises(worker.WorkerError):
            worker.inspect_container({"service": "../../other"})

    def test_safe_snapshot_excludes_env_labels_commands_and_host_sources(self):
        raw = [{
            "Id": "abcdef1234567890",
            "Config": {
                "Image": "example/image:1",
                "Env": ["SECRET=do-not-return"],
                "Labels": {"secret": "do-not-return"},
                "Cmd": ["sh", "-c", "do-not-return"],
            },
            "State": {
                "Status": "running",
                "Running": True,
                "Restarting": False,
                "ExitCode": 0,
                "StartedAt": "now",
                "FinishedAt": "",
                "Health": {"Status": "healthy"},
            },
            "RestartCount": 2,
            "NetworkSettings": {
                "Networks": {"librechat": {}},
                "Ports": {"3080/tcp": [{"HostIp": "0.0.0.0", "HostPort": "3200"}]},
            },
            "Mounts": [{
                "Type": "bind",
                "Source": "/volume1/secret/source",
                "Destination": "/workspace",
                "Mode": "rw",
                "RW": True,
            }],
        }]
        with mock.patch.object(worker, "run_fixed", return_value=json.dumps(raw)):
            result = worker.safe_container_snapshot("api", "librechat")
        encoded = json.dumps(result)
        self.assertNotIn("SECRET", encoded)
        self.assertNotIn("do-not-return", encoded)
        self.assertNotIn("/volume1/secret/source", encoded)
        self.assertEqual(result["mounts"][0]["destination"], "/workspace")

    def test_deployment_state_reads_only_fixed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git" / "refs" / "heads" / "server").mkdir(parents=True)
            (root / ".git" / "HEAD").write_text("ref: refs/heads/server/synology\n")
            (root / ".git" / "refs" / "heads" / "server" / "synology").write_text("abc123\n")
            state = root / "last-success"
            state.write_text("abc123\n")
            with mock.patch.object(worker, "REPO_DIR", root), mock.patch.object(worker, "DEPLOY_STATE_FILE", state):
                result = worker.get_deployment_state()
        self.assertEqual(result["repository_branch"], "server/synology")
        self.assertEqual(result["repository_head_commit"], "abc123")
        self.assertTrue(result["recorded_success_matches_head"])


class BridgeSafetyTests(unittest.TestCase):
    def test_tools_have_no_mutation_surface(self):
        names = {item["name"] for item in bridge.TOOLS}
        self.assertEqual(names, bridge.TOOL_NAMES)
        forbidden = {"shell", "exec", "write", "delete", "remove", "restart", "stop", "start", "create"}
        for name in names:
            self.assertFalse(any(word in name.lower() for word in forbidden), name)

    def test_initialize_declares_tools_only(self):
        result = bridge.handle({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        })
        self.assertEqual(result["result"]["capabilities"], {"tools": {"listChanged": False}})

    def test_unknown_tool_cannot_reach_worker(self):
        with mock.patch.object(bridge, "worker_call") as call:
            result = bridge.handle({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "restart_container", "arguments": {}},
            })
        call.assert_not_called()
        self.assertIn("error", result)

    def test_allowed_tool_forwards_exact_name_and_arguments(self):
        with mock.patch.object(bridge, "worker_call", return_value={"status": "ok"}) as call:
            result = bridge.handle({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "inspect_container", "arguments": {"service": "api"}},
            })
        call.assert_called_once_with("inspect_container", {"service": "api"})
        self.assertFalse(result["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
