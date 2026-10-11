"""Real gated helpers/workspaces; synthetic platform evidence, never OS confinement."""
from dataclasses import replace
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import threading
import time
import unittest

from coding_executor.containment import GatedExecutor, ExecutorSnapshot, ExecutorQuiescence
from coding_executor.dispatch import FencedWorkspace
from coding_executor.executions import (ExecutionService, ExecutionIdentity, ExecutionConflict,
                                        ExecutorResource, Observation)
from coding_executor.workspaces import WorkspaceManager


class SyntheticPlatform:
    def __init__(self):
        self.resource = ExecutorResource("synthetic", "boot", "root-device-inode", "resource-inode", "gated-v1")
        self.closed = False
        self.empty = False
        self.prepared = 0
        self.pids = []
        self.before_attach = lambda: None
        self.snapshot = None
        self.kill_failed = False
        self.missing = False

    def prepare(self, claim):
        self.prepared += 1
        return self.resource

    def attach(self, claim, resource, pid):
        self.pids.append(pid)
        self.before_attach()
        return None if self.closed else resource

    def seal(self, claim, resource):
        self.closed = True

    def stop(self, claim, resource):
        if self.kill_failed:
            raise RuntimeError("synthetic stop unavailable")

    def inspect(self, claim, resource):
        if self.missing:
            return None
        return self.snapshot if self.snapshot is not None else ExecutorSnapshot(claim, self.resource, self.closed, self.empty)


class Authority:
    authority_id = "fixture-authority"
    launcher = None

    def launch(self, claim):
        return Observation(claim, "running", False)

    def stop(self, claim):
        if self.launcher is not None:
            self.launcher.stop(claim)

    def observe(self, claim):
        # Executor-only evidence must not accidentally resolve the whole job.
        return self.launcher.observe(claim) if self.launcher else None


class ContainmentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.authority = Authority()
        self.ledger = ExecutionService(self.root / "ledger", self.authority)
        self.addCleanup(lambda: self.ledger.close())
        self.identity = ExecutionIdentity("job", "execution", "owner", "tenant", "generation", 1,
                                          "profile", "demo", "read_only")
        self.ledger.advance(self.identity)
        self.claim = self.ledger.start(self.identity, "job-worker", "a" * 64).operations[0].claim
        self.platform = SyntheticPlatform()
        self.launcher = GatedExecutor(self.ledger, platform=self.platform, enabled=True)
        self.authority.launcher = self.launcher
        repositories, tasks = self.root / "repositories", self.root / "tasks"
        source = repositories / "demo"
        source.mkdir(parents=True)
        tasks.mkdir()
        (source / "sample.txt").write_text("fixture\n")
        (source / "test_fixture.py").write_text(
            "import json, os, unittest\nfrom pathlib import Path\n"
            "class Fixture(unittest.TestCase):\n"
            " def test_child(self):\n"
            "  Path('child.json').write_text(json.dumps({'pid':os.getpid(),'parent':os.getppid()}))\n")
        for args in (("init", "-b", "main"), ("config", "user.email", "fixture@example.invalid"),
                     ("config", "user.name", "Fixture"), ("add", "."), ("commit", "-m", "fixture")):
            subprocess.run(["git", "-C", str(source), *args], check=True, capture_output=True)
        self.manager = WorkspaceManager(repositories, tasks)
        self.workspace = FencedWorkspace(self.ledger, self.manager, enabled=True,
            authorize=lambda identity: identity == self.identity,
            checks={"tests": "python3 -m unittest"}, launcher=self.launcher)

    def admit(self, timeout=15):
        self.workspace.admit(self.claim, max_requests=5, timeout_seconds=timeout)

    def create(self):
        return self.workspace.dispatch(self.claim, "create", "create_task", {})

    def test_default_and_unconfigured_never_prepare_or_spawn(self):
        for launcher in (GatedExecutor(self.ledger), GatedExecutor(self.ledger, enabled=True),
                         GatedExecutor(self.ledger, platform=self.platform)):
            with self.subTest(launcher=launcher), self.assertRaises(ExecutionConflict):
                launcher.admit(self.claim)
        self.assertEqual(self.platform.prepared, 0)
        self.assertEqual(self.platform.pids, [])
        self.assertIsNone(self.ledger.executor_resource(self.claim))

    def test_helper_is_gated_and_all_workspace_subprocesses_descend_from_it(self):
        self.admit()
        def before_attach():
            self.assertEqual(list(self.manager.task_root.glob("preview-*")), [])
            with sqlite3.connect(self.root / "ledger" / "executions.sqlite3") as db:
                self.assertEqual(db.execute("SELECT count(*) FROM executor_resources").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT state FROM dispatch_actions").fetchone()[0], "unknown")
        self.platform.before_attach = before_attach
        task = self.create()
        self.platform.before_attach = lambda: None
        content = self.workspace.dispatch(self.claim, "read", "read_file", {"path": "sample.txt"})
        self.assertIn("fixture", content)
        result = self.workspace.dispatch(self.claim, "check", "run_check", {"check": "tests"})
        self.assertEqual(result["exit_code"], 0, result)
        child = json.loads((Path(task["path"]) / "child.json").read_text())
        self.assertEqual(child["parent"], self.platform.pids[-1])
        self.assertNotEqual(child["parent"], os.getpid())
        self.assertEqual(len(self.platform.pids), 3)
        self.assertIsNone(self.launcher.observe(self.claim))
        self.assertNotEqual(self.ledger.stop(self.identity).state, "stopped")
        self.platform.empty = True
        self.assertIsInstance(self.launcher.observe(self.claim), ExecutorQuiescence)
        self.assertNotEqual(self.ledger.reconcile(self.identity).state, "stopped")

    def test_resource_is_immutable_claim_bound_and_commit_precedes_release(self):
        self.admit()
        self.admit()
        self.assertEqual(self.platform.prepared, 1)
        for field in ("platform_id", "boot_id", "root_id", "resource_id", "policy_id"):
            with self.subTest(field=field), self.assertRaises(ExecutionConflict):
                self.ledger.bind_executor(self.claim, replace(self.platform.resource, **{field: "other"}))
        for field in ("attempt_id", "authority_id", "request_sha256", "operation_id"):
            with self.subTest(field=field), self.assertRaises(ExecutionConflict):
                self.ledger.executor_resource(replace(self.claim, **{field: "other"}))
        for field in ("user_id", "tenant_id", "execution_id", "generation_id"):
            with self.subTest(field=field), self.assertRaises(ExecutionConflict):
                self.ledger.executor_resource(replace(self.claim, identity=replace(self.identity, **{field: "other"})))

    def test_binding_commit_failure_prevents_any_helper(self):
        self.ledger._db.set_authorizer(lambda code, value, *rest:
            sqlite3.SQLITE_DENY if code == sqlite3.SQLITE_TRANSACTION and value == "COMMIT" else sqlite3.SQLITE_OK)
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                self.launcher.admit(self.claim)
        finally:
            self.ledger._db.set_authorizer(None)
        self.assertIsNone(self.ledger.executor_resource(self.claim))
        self.assertEqual(self.platform.pids, [])

    def test_resource_binding_commit_failure_after_allocation_never_reallocates(self):
        def prepare(claim):
            self.platform.prepared += 1
            self.ledger._db.set_authorizer(lambda code, value, *rest:
                sqlite3.SQLITE_DENY if code == sqlite3.SQLITE_TRANSACTION and value == "COMMIT" else sqlite3.SQLITE_OK)
            return self.platform.resource
        self.platform.prepare = prepare
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                self.launcher.admit(self.claim)
        finally:
            self.ledger._db.set_authorizer(None)
        self.assertIsNone(self.ledger.executor_resource(self.claim))
        with self.assertRaises(ExecutionConflict):
            self.launcher.admit(self.claim)
        self.assertEqual(self.platform.prepared, 1)
        self.assertEqual(self.platform.pids, [])

    def test_lost_allocation_or_attachment_ack_never_retries_or_releases(self):
        def lost(claim):
            self.platform.prepared += 1
            raise RuntimeError("lost reply")
        self.platform.prepare = lost
        for _ in range(2):
            with self.assertRaises(ExecutionConflict):
                self.launcher.admit(self.claim)
        self.assertEqual(self.platform.prepared, 1)
        self.assertIsNone(self.ledger.executor_resource(self.claim))
        self.assertIsNone(self.launcher.observe(self.claim))
        self.assertEqual(self.platform.pids, [])

    def test_wrong_attachment_ack_leaves_workspace_untouched(self):
        self.admit()
        self.platform.attach = lambda *_: replace(self.platform.resource, resource_id="wrong")
        with self.assertRaises(ExecutionConflict):
            self.create()
        self.assertEqual(list(self.manager.task_root.glob("preview-*")), [])
        self.assertTrue(self.ledger.status(self.identity).sealed)

    def test_contained_checks_preserve_the_shorter_host_command_timeout(self):
        self.admit()
        task = self.create()
        target = Path(task["path"]) / "test_fixture.py"
        target.write_text("import time\ntime.sleep(2)\n")
        self.manager.command_timeout_seconds = .1
        with self.assertRaisesRegex(RuntimeError, "0.1 second timeout"):
            self.manager.run_check(task["task_id"], "python3 -m unittest", timeout_seconds=10)
        started = time.monotonic()
        with self.assertRaises(ExecutionConflict):
            self.workspace.dispatch(self.claim, "check", "run_check", {"check": "tests"})
        self.assertLess(time.monotonic() - started, 1.8)
        self.assertTrue(self.ledger.status(self.identity).sealed)

    def test_cancel_or_deadline_during_attachment_never_releases_delayed_work(self):
        for timeout in (15, .2):
            with self.subTest(timeout=timeout):
                # Each scenario owns a separate durable attempt and disposable workspace.
                fixture = ContainmentTests("runTest")
                fixture.setUp()
                entered, release = threading.Event(), threading.Event()
                errors = []
                caller = None
                try:
                    fixture.admit(timeout)
                    def delayed():
                        entered.set()
                        release.wait(3)
                    fixture.platform.before_attach = delayed
                    def invoke():
                        try:
                            fixture.create()
                        except ExecutionConflict as error:
                            errors.append(error)
                    caller = threading.Thread(target=invoke)
                    caller.start()
                    self.assertTrue(entered.wait(2))
                    if timeout == 15:
                        fixture.ledger.stop(fixture.identity)
                    else:
                        caller.join(2)
                    self.assertIsNone(fixture.launcher.observe(fixture.claim))
                    release.set()
                    caller.join(3)
                    deadline = time.monotonic() + 3
                    while fixture.ledger._active_actions and time.monotonic() < deadline:
                        time.sleep(.01)
                    self.assertEqual(len(errors), 1)
                    self.assertFalse(fixture.ledger._active_actions)
                    self.assertEqual(list(fixture.manager.task_root.glob("preview-*")), [])
                    with self.assertRaises(ExecutionConflict):
                        fixture.workspace.dispatch(fixture.claim, "late", "create_task", {})
                    self.assertEqual(len(fixture.platform.pids), 1)
                finally:
                    release.set()
                    if caller is not None:
                        caller.join(3)
                    cleanup_deadline = time.monotonic() + 3
                    while fixture.ledger._active_actions and time.monotonic() < cleanup_deadline:
                        time.sleep(.01)
                    fixture.doCleanups()

    def test_restart_requires_exact_independent_resource_and_closed_admission(self):
        self.admit()
        self.create()
        self.ledger.close()
        self.ledger = ExecutionService(self.root / "ledger", self.authority)
        self.launcher = GatedExecutor(self.ledger, platform=self.platform, enabled=True)
        self.authority.launcher = self.launcher
        self.assertEqual(self.ledger.executor_resource(self.claim), self.platform.resource)
        self.assertIsNone(self.launcher.observe(self.claim))
        self.platform.empty = True
        self.assertIsNone(self.launcher.observe(self.claim))
        self.launcher.stop(self.claim)
        proof = self.launcher.observe(self.claim)
        self.assertEqual(proof, ExecutorQuiescence(self.claim, self.platform.resource))
        baseline = ExecutorSnapshot(self.claim, self.platform.resource, True, True)
        for snapshot in (None, {}, replace(baseline, admission_closed=1), replace(baseline, quiescent=1),
                         replace(baseline, quiescent=False),
                         replace(baseline, claim=replace(self.claim, attempt_id="other"))):
            self.platform.snapshot = snapshot
            self.platform.missing = snapshot is None
            self.assertIsNone(self.launcher.observe(self.claim))
        self.platform.missing = False
        for field in ("boot_id", "root_id", "resource_id", "policy_id", "platform_id"):
            self.platform.snapshot = replace(baseline, resource=replace(self.platform.resource, **{field: "replaced"}))
            self.assertIsNone(self.launcher.observe(self.claim))
        with self.assertRaises(ExecutionConflict):
            self.launcher.admit(self.claim)

    def test_stop_failure_or_descendants_remaining_cannot_become_proof(self):
        self.admit()
        self.create()
        self.platform.kill_failed = True
        self.assertNotEqual(self.ledger.stop(self.identity).state, "stopped")
        self.assertIsNone(self.launcher.observe(self.claim))
        self.platform.kill_failed = False
        self.launcher.stop(self.claim)
        self.assertIsNone(self.launcher.observe(self.claim))
        self.platform.empty = True
        self.assertIsInstance(self.launcher.observe(self.claim), ExecutorQuiescence)


if __name__ == "__main__":
    unittest.main()
