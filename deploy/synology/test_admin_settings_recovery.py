"""Exercise settings transactions with temporary Docker/Compose executables."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("recovery_worker", HERE / "admin-settings-worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)

FAKE = r'''#!/usr/bin/env python3
import json, os, pathlib, sys, time
root = pathlib.Path.cwd()
mode = (root / "scenario").read_text()
name = pathlib.Path(sys.argv[0]).name
action = "inspect" if name == "docker" else ("up" if "up" in sys.argv else "config")
with (root / "calls").open("a") as f:
    f.write(action + "\n")
if action == "inspect":
    print(json.dumps({"Status":"running", "Running":True, "Restarting":False, "ExitCode":0, "Error":"provider-secret"}))
elif action == "up":
    if mode == "slow":
        time.sleep(.2)
    if mode == "failure" or (mode == "rollback_failure" and (root / "calls").read_text().count("up") == 2):
        print("Read timed out: provider-secret new-secret jwt-secret https://u:p@example.test", file=sys.stderr)
        sys.exit(17)
elif mode == "config_failure" and (root / "calls").read_text().count("config") == 1:
    print("provider-secret " * 5000, file=sys.stderr)
    sys.exit(2)
'''


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = self.root / ".env"
        self.original = "SEARCH=false\nOPENROUTER_KEY=provider-secret\nJWT_SECRET=jwt-secret\n"
        self.env.write_text(self.original)
        self.state = self.root / "state"
        self.lock = self.root / "lock"
        self.marker = self.state / "recovery-required.json"
        self.core = worker.WorkerCore(self.env, HERE / "admin-settings.schema.json", self.state)
        (self.root / "scenario").write_text("success")
        for name in ("docker", "docker-compose"):
            path = self.root / name
            path.write_text(FAKE)
            path.chmod(0o700)
        (self.root / "python3").symlink_to(sys.executable)
        for ctx in (patch.object(worker, "ROOT", self.root),
                    patch.object(worker, "DEPLOY_LOCK", self.lock),
                    patch.dict(os.environ, {"PATH": str(self.root)})):
            ctx.start()
            self.addCleanup(ctx.stop)

    def apply(self):
        return self.core.apply({"updates": {"SEARCH": "true"}})

    def calls(self):
        return (self.root / "calls").read_text().splitlines()

    def audit(self):
        return [json.loads(line) for line in (self.state / "audit.log").read_text().splitlines()]

    def test_recreate_failure_retains_original_cause_without_destructive_rollback(self):
        (self.root / "scenario").write_text("failure")
        with self.assertRaises(worker.WorkerError):
            self.apply()
        self.assertEqual(self.calls().count("up"), 1)
        self.assertIn("SEARCH=true", self.env.read_text())
        self.assertEqual(len(list(self.root.glob(".env.backup-*"))), 1)
        record = self.audit()[0]
        self.assertEqual(record["stage"], "service_recreate")
        self.assertEqual(record["error"]["category"], "command_exit")
        self.assertEqual(record["error"]["returncode"], 17)
        self.assertIn("docker_timeout", record["error"]["signals"])
        self.assertGreaterEqual(record["error"]["duration_ms"], 0)
        recovery = json.loads(self.marker.read_text())
        self.assertEqual(recovery["runtime"]["api"]["status"], "running")
        self.assertNotIn("provider-secret", json.dumps(recovery) + str(self.audit()))
        self.assertNotIn("https://", json.dumps(recovery) + str(self.audit()))
        self.assertLess(len(self.marker.read_bytes()), 4096)

    def test_timed_out_client_leaves_recovery_hold_and_does_not_retry(self):
        (self.root / "scenario").write_text("slow")
        with patch.object(worker, "SERVICE_RECREATE_TIMEOUT", .05, create=True), \
             patch.object(worker, "wait_health", return_value=True):
            with self.assertRaises(worker.WorkerError):
                self.apply()
        self.assertEqual(self.calls().count("up"), 1)
        self.assertTrue(self.marker.exists())
        self.assertEqual(self.audit()[0]["error"]["category"], "command_timeout")
        self.assertIsNone(self.audit()[0]["error"]["returncode"])

    def test_existing_hold_blocks_apply_before_backup_or_config_write(self):
        self.state.mkdir()
        self.marker.write_text('{}')
        with self.assertRaises(worker.WorkerError):
            self.apply()
        self.assertEqual(self.env.read_text(), self.original)
        self.assertFalse((self.root / "calls").exists())
        self.assertEqual(list(self.root.glob(".env.backup-*")), [])

    def test_success_clears_hold_and_releases_lock(self):
        with patch.object(worker, "wait_health", return_value=True):
            result = self.apply()
        self.assertTrue(result["ok"])
        self.assertFalse(self.marker.exists())
        self.assertFalse(self.lock.exists())
        self.assertEqual(self.calls(), ["config", "up"])

    def test_validation_failure_restores_backup_and_does_not_recreate(self):
        (self.root / "scenario").write_text("config_failure")
        with patch.object(worker, "wait_health", return_value=True):
            with self.assertRaises(worker.WorkerError):
                self.apply()
        self.assertEqual(self.env.read_text(), self.original)
        self.assertNotIn("up", self.calls())
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.audit()[0]["error"]["returncode"], 2)
        self.assertNotIn("provider-secret", str(self.audit()))

    def test_health_failure_after_completed_recreate_can_roll_back(self):
        with patch.object(worker, "wait_health", side_effect=[False, True]):
            with self.assertRaises(worker.WorkerError):
                self.apply()
        self.assertEqual(self.env.read_text(), self.original)
        self.assertEqual(self.calls().count("up"), 2)
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.audit()[-1]["outcome"], "rolled_back")

    def test_failed_rollback_preserves_both_failure_stages_and_holds_recovery(self):
        (self.root / "scenario").write_text("rollback_failure")
        with patch.object(worker, "wait_health", return_value=False):
            with self.assertRaises(worker.WorkerError):
                self.apply()
        records = self.audit()
        self.assertEqual(records[0]["stage"], "health_check")
        self.assertEqual(records[-1]["stage"], "rollback_service_recreate")
        self.assertEqual(records[-1]["error"]["returncode"], 17)
        self.assertEqual(self.calls().count("up"), 2)
        self.assertTrue(self.marker.exists())

    def test_observed_344_second_recreate_fits_budget_and_http_deadline_is_shorter(self):
        def fake_run(cmd, **kwargs):
            if kwargs["timeout"] <= 344:
                raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])
            self.assertEqual(kwargs["env"]["COMPOSE_HTTP_TIMEOUT"], "300")
            self.assertLess(int(kwargs["env"]["COMPOSE_HTTP_TIMEOUT"]), kwargs["timeout"])
            return subprocess.CompletedProcess(cmd, 0, "", "")
        with patch.object(worker.subprocess, "run", side_effect=fake_run):
            worker.recreate_services({}, ["api"])

    def test_ownerless_lock_is_not_stolen_during_pid_publication(self):
        self.lock.mkdir()
        with self.assertRaises(worker.WorkerError):
            worker.acquire_deploy_lock()
        self.assertTrue(self.lock.exists())

    def test_stale_lock_is_not_stolen_without_explicit_recovery(self):
        self.lock.mkdir()
        (self.lock / "pid").write_text("99999999")
        with self.assertRaises(worker.WorkerError):
            worker.acquire_deploy_lock()
        self.assertEqual((self.lock / "pid").read_text(), "99999999")

    def test_worker_interruption_preserves_recovery_hold_before_mutation(self):
        with patch.object(worker, "recreate_services", side_effect=SystemExit(1)):
            with self.assertRaises(SystemExit):
                self.apply()
        self.assertTrue(self.marker.exists())
        before = self.env.read_text()
        with self.assertRaises(worker.WorkerError):
            self.apply()
        self.assertEqual(self.env.read_text(), before)

    def test_unknown_inspection_does_not_clear_recovery_hold(self):
        (self.root / "scenario").write_text("failure")
        (self.root / "docker").write_text('#!/bin/sh\nexit 1\n')
        with self.assertRaises(worker.WorkerError):
            self.apply()
        record = json.loads(self.marker.read_text())
        self.assertEqual(record["runtime"]["api"]["status"], "unknown")
        self.assertEqual(self.calls().count("up"), 1)

    def test_marker_failure_prevents_configuration_mutation(self):
        self.state.mkdir()
        (self.state / "recovery-required.json.tmp").mkdir()
        with self.assertRaises(OSError):
            self.apply()
        self.assertEqual(self.env.read_text(), self.original)
        self.assertFalse((self.root / "calls").exists())

    def test_audit_contains_only_bounded_signals_not_raw_output(self):
        result = worker.run(["docker-compose", "config"])
        self.assertEqual(result.returncode, 0)
        (self.root / "calls").unlink()
        (self.root / "scenario").write_text("config_failure")
        with self.assertRaises(worker.WorkerError):
            self.apply()
        raw = (self.state / "audit.log").read_text()
        self.assertNotIn("provider-secret", raw)
        self.assertLess(len(raw), 2048)

    def test_rag_runtime_is_included_in_recovery_observation(self):
        result = worker.observe_runtime(["rag_api"])
        self.assertEqual(result["rag_api"]["status"], "running")

    def test_concurrent_apply_is_rejected_instead_of_outliving_response_budget(self):
        self.core.lock.acquire()
        errors = []
        def apply():
            try:
                self.apply()
            except worker.WorkerError as exc:
                errors.append(str(exc))
        thread = threading.Thread(target=apply)
        thread.start()
        try:
            thread.join(.2)
            self.assertFalse(thread.is_alive(), "second apply must fail promptly, not queue another transaction")
            self.assertEqual(len(errors), 1)
        finally:
            self.core.lock.release()
            thread.join(2)

    def test_process_launch_error_keeps_sanitized_command_duration(self):
        (self.root / "docker-compose").chmod(0o600)
        with self.assertRaises(worker.WorkerError):
            self.apply()
        details = self.audit()[0]["error"]
        self.assertEqual(details["category"], "command_oserror")
        self.assertIn("duration_ms", details)


class AutodeployHoldTests(unittest.TestCase):
    def test_autodeploy_refuses_recovery_hold_even_without_live_worker(self):
        source = (HERE / "autodeploy.sh").read_text()
        functions = source[source.index("acquire_lock() {"):source.index("prepare_workspace() {")]
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "recovery-required.json"
            marker.write_text('{}')
            script = 'LOCK_DIR="{0}/lock"\nRECOVERY_FILE="{1}"\nLOCK_HELD=0\nlog() {{ :; }}\n'.format(temp, marker)
            proc = subprocess.run(["sh", "-c", script + functions + "\nacquire_lock"], capture_output=True)
            self.assertNotEqual(proc.returncode, 0)

    def test_autodeploy_does_not_steal_stale_lock(self):
        source = (HERE / "autodeploy.sh").read_text()
        functions = source[source.index("acquire_lock() {"):source.index("prepare_workspace() {")]
        with tempfile.TemporaryDirectory() as temp:
            lock = Path(temp) / "lock"
            lock.mkdir()
            (lock / "pid").write_text("99999999")
            script = 'LOCK_DIR="{0}"\nRECOVERY_FILE="{1}/absent"\nLOCK_HELD=0\nlog() {{ :; }}\n'.format(lock, temp)
            proc = subprocess.run(["sh", "-c", script + functions + "\nacquire_lock"], capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual((lock / "pid").read_text(), "99999999")


if __name__ == "__main__":
    unittest.main()
