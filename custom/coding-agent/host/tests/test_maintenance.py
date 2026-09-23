from __future__ import annotations

import asyncio
import copy
import json
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings

from coding_executor.coordination import maintenance_lock
from host_maintenance.broker import Broker, LOCK_DESTINATION
from host_maintenance.server import MaintenanceTokenVerifier, build_server


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        (root / "tasks").mkdir()
        (root / "repos").mkdir()
        (root / "gate").touch()
        self.config = {"container": "executor-test", "image_id": "sha256:" + "a" * 64,
                       "task_root": str(root / "tasks"), "repository_root": str(root / "repos"),
                       "lock_path": str(root / "gate"),
                       "repositories": {"demo": {"branch": "main", "url": "https://github.com/example/demo.git"}},
                       "retired_tasks": {"finished": time.time() - 90000},
                       "enabled_mutations": {"refresh": True, "cleanup": True, "restart": True}}
        self.container = {"Id": "b" * 64, "Image": self.config["image_id"],
                          "Config": {"User": "1000:1000", "Cmd": ["python3", "-m", "coding_executor.server"], "Env": [
                              "CODING_MAINTENANCE_LOCK=" + LOCK_DESTINATION,
                              "CODING_REPOSITORY_ROOT=" + self.config["repository_root"],
                              "CODING_TASK_ROOT=" + self.config["task_root"]]},
                          "State": {"Running": True, "Status": "running", "StartedAt": "initial",
                                    "Health": {"Status": "healthy"}},
                          "HostConfig": {"ReadonlyRootfs": True, "Privileged": False, "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges"]},
                          "Mounts": [
                              {"Destination": self.config["task_root"], "Source": self.config["task_root"], "RW": True, "Type": "bind"},
                              {"Destination": self.config["repository_root"], "Source": self.config["repository_root"], "RW": True, "Type": "bind"},
                              {"Destination": LOCK_DESTINATION, "Source": self.config["lock_path"], "RW": False, "Type": "bind"}]}
        self.calls = []
        self.logs = "INFO: Application startup complete.\nERROR: bearer SECRET\nGET /mcp?token=SECRET\n"
        self.snapshot = {"fingerprint": "f" * 64, "dirty": False}
        self.broker = Broker(self.config, runner=self.docker)

    def tearDown(self):
        self.temp.cleanup()

    def docker(self, argv, **kwargs):
        self.calls.append(argv)
        if argv[1] == "inspect":
            return json.dumps([self.container])
        if argv[1] == "logs":
            return self.logs
        if argv[1] == "restart":
            self.container["State"]["StartedAt"] = "restarted"
            return self.container["Id"]
        if argv[1] == "exec":
            return json.dumps(self.snapshot)
        raise AssertionError(argv)

    def test_unknown_repository_and_injection_never_reach_docker(self):
        for name in ("missing", "../demo", "demo;id", "--help"):
            with self.assertRaises(ValueError):
                self.broker.refresh_repository(name)
        self.assertFalse(self.calls)

    def test_refresh_uses_fixed_argv_and_pinned_container_id(self):
        self.broker.refresh_repository("demo")
        self.assertEqual(self.calls[-1], ["/usr/bin/docker", "exec", "b" * 64, "python3", "-I", "-B", "-m",
                                        "coding_executor.maintenance", "refresh", "--repository", "demo",
                                        "--branch", "main", "--url", "https://github.com/example/demo.git"])

    def test_all_mutations_default_disabled(self):
        self.config.pop("enabled_mutations")
        for function, argument in ((self.broker.refresh_repository, "demo"), (self.broker.cleanup_task, "ticket"),
                                   (self.broker.restart_executor, "ticket")):
            with self.assertRaisesRegex(ValueError, "disabled"):
                function(argument)
        self.assertFalse(self.calls)

    def test_cleanup_requires_retirement_delay_and_clean_snapshot(self):
        for name in ("active", "../escape", "--help"):
            with self.assertRaises(ValueError):
                self.broker.preview_cleanup(name)
        self.config["retired_tasks"]["recent"] = time.time()
        with self.assertRaises(ValueError):
            self.broker.preview_cleanup("recent")
        self.snapshot["dirty"] = True
        with self.assertRaises(ValueError):
            self.broker.preview_cleanup("finished")

    def test_cleanup_tickets_bind_identity_expire_and_are_single_use(self):
        preview = self.broker.preview_cleanup("finished")
        self.broker.cleanup_task(preview["ticket"])
        self.assertEqual(self.calls[-1][-4:], ["--task", "finished", "--fingerprint", "f" * 64])
        with self.assertRaises(ValueError):
            self.broker.cleanup_task(preview["ticket"])
        preview = self.broker.preview_cleanup("finished")
        with patch("host_maintenance.broker.time.monotonic", return_value=time.monotonic() + 61):
            with self.assertRaises(ValueError):
                self.broker.cleanup_task(preview["ticket"])

    def test_restart_refuses_active_operations_changed_identity_and_replay(self):
        preview = self.broker.preview_restart()
        with maintenance_lock(self.broker.tasks, lock_path=self.broker.lock):
            with self.assertRaisesRegex(RuntimeError, "executor_busy"):
                self.broker.restart_executor(preview["ticket"])
        self.assertFalse(any(call[1] == "restart" for call in self.calls))
        preview = self.broker.preview_restart()
        self.container["State"]["StartedAt"] = "changed"
        with self.assertRaisesRegex(ValueError, "changed"):
            self.broker.restart_executor(preview["ticket"])
        preview = self.broker.preview_restart()
        result = self.broker.restart_executor(preview["ticket"])
        self.assertTrue(result["restarted"])
        with self.assertRaises(ValueError):
            self.broker.restart_executor(preview["ticket"])
        with self.assertRaisesRegex(ValueError, "cooldown"):
            self.broker.restart_executor(self.broker.preview_restart()["ticket"])
        restarts = [call for call in self.calls if call[1] == "restart"]
        self.assertEqual(restarts, [["/usr/bin/docker", "restart", "--time", "10", "b" * 64]])

    def test_restart_unhealthy_is_not_reported_as_success(self):
        preview = self.broker.preview_restart()
        original = self.docker
        def unhealthy(argv, **kwargs):
            result = original(argv, **kwargs)
            if argv[1] == "restart":
                self.container["State"]["Health"]["Status"] = "unhealthy"
            return result
        self.broker.runner = unhealthy
        with patch("host_maintenance.broker.time.sleep"), self.assertRaisesRegex(RuntimeError, "did not become healthy"):
            self.broker.restart_executor(preview["ticket"])

    def test_wrong_image_writable_lock_extra_mount_or_privilege_is_refused(self):
        original = copy.deepcopy(self.container)
        for change in (lambda: self.container.update(Image="sha256:" + "c" * 64),
                       lambda: self.container["Mounts"][-1].update(RW=True),
                       lambda: self.container["Mounts"].append({"Destination": "/socket", "Source": "/var/run/docker.sock", "RW": True, "Type": "bind"}),
                       lambda: self.container["HostConfig"].update(Privileged=True)):
            self.container = copy.deepcopy(original)
            change()
            with self.assertRaises(RuntimeError):
                self.broker.health()

    def test_logs_suppress_secrets_and_arbitrary_text(self):
        logs = self.broker.logs()
        self.assertNotIn("SECRET", json.dumps(logs))
        self.assertIn("INFO: Application startup complete.", logs["events"])
        self.assertEqual(self.calls[-1][-5:-1], ["--tail", "100", "--since", "10m"])

    def test_real_mcp_sdk_contract_and_dispatch(self):
        async def check():
            server = build_server(self.broker, "m" * 48, "http://127.0.0.1:8766/mcp")
            tools = await server.list_tools()
            names = {tool.name for tool in tools}
            self.assertEqual(names, {"executor_health", "repository_status", "refresh_repository", "task_inventory",
                                     "preview_cleanup", "cleanup_task", "executor_logs", "preview_restart", "restart_executor"})
            result = await server.call_tool("executor_health", {})
            self.assertFalse(result.is_error)
            with self.assertRaises(Exception) as refused:
                await server.call_tool("refresh_repository", {"repository": "../escape"})
            self.assertIsInstance(refused.exception.__cause__, ValueError)
            verifier = MaintenanceTokenVerifier("m" * 48, "http://127.0.0.1:8766/mcp")
            self.assertIsNone(await verifier.verify_token("executor-token"))
            token = await verifier.verify_token("m" * 48)
            self.assertEqual(token.scopes, ["coding:maintain"])
        asyncio.run(check())

    def test_real_http_authentication_and_tool_discovery(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
            url = f"http://127.0.0.1:{port}/mcp"
            mcp = build_server(self.broker, "m" * 48, url)
            app = mcp.streamable_http_app(stateless_http=True, json_response=True,
                transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True,
                    allowed_hosts=[f"127.0.0.1:{port}"], allowed_origins=[]))
            server = uvicorn.Server(uvicorn.Config(app, log_level="error"))
            thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
            thread.start()
            try:
                deadline = time.monotonic() + 5
                while not server.started and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(server.started)
                def request(token=None, method="tools/list", params=None):
                    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                               "MCP-Protocol-Version": "2025-06-18"}
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
                    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=5) as response:
                        return json.load(response)
                for token in (None, "ordinary-executor-token"):
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        request(token)
                    self.assertEqual(error.exception.code, 401)
                initialized = request("m" * 48, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                       "clientInfo": {"name": "maintenance-test", "version": "1"}})
                self.assertIn("serverInfo", initialized["result"])
                discovered = request("m" * 48)
                self.assertEqual(len(discovered["result"]["tools"]), 9)
                result = request("m" * 48, "tools/call", {"name": "executor_health", "arguments": {}})
                self.assertFalse(result["result"].get("isError", False))
            finally:
                server.should_exit = True
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
