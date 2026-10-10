"""Actual jobs, child workers and SDK; synthetic HTTP and loopback MCP only."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from coding_orchestrator.job_store import JobStore, StopEvidence
from coding_orchestrator.jobs import JobRequest, JobService, Principal, RunScope
from coding_orchestrator.openhands_profile import create_openhands_profile


TASK = "fix-fixture"
COMMAND = "python check_fixture.py"
BEFORE = "def add(a, b):\n    return a - b\n"
AFTER = "def add(a, b):\n    return a + b\n"
PATCH = "*** Begin Patch\n*** Update File: calculator.py\n@@\n-    return a - b\n+    return a + b\n*** End Patch\n"
CHECK = ("from pathlib import Path\nimport runpy\n"
         "value = runpy.run_path(str(Path(__file__).with_name('calculator.py')))['add'](2, 3)\n"
         "print(f'expected 5; got {value}')\nraise SystemExit(0 if value == 5 else 1)\n")


def fixture_token():
    return "synthetic-fixture-token"


def fixture_llm():
    from openhands.sdk import LLM
    from pydantic import SecretStr
    return LLM(model="openai/gpt-5.6-sol", api_key=SecretStr("synthetic-model-token"),
               base_url="https://chatgpt.com/backend-api/codex", api_mode="responses", stream=False,
               num_retries=0, max_input_tokens=32000, max_output_tokens=2000)


def script(scenario, mode):
    create = ("create_task", {"repository": "fixture", "task_name": "fix", "task_mode": mode})
    finish = ("finish", {"message": "Fixture complete."})
    task = {"task_id": TASK}
    if scenario == "finish":
        return [[finish]]
    if scenario == "repository":
        return [[("create_task", {**create[1], "repository": "foreign"})]]
    if scenario == "mode":
        return [[("create_task", {**create[1], "task_mode": "read_only"})]]
    if scenario == "list":
        return [[("list_repositories", {})]]
    if scenario == "batch":
        return [[create, ("list_repositories", {})]]
    if scenario == "foreign_task":
        return [[create], [("read_file", {"task_id": "foreign", "path": "calculator.py"})]]
    if scenario == "readonly_patch":
        return [[create], [("apply_patch", {**task, "patch": PATCH})]]
    flow = [create, ("read_file", {**task, "path": "calculator.py"}),
        ("run_check", {**task, "command": COMMAND}), ("apply_patch", {**task, "patch": PATCH}),
        ("run_check", {**task, "command": COMMAND}), ("git_diff", task), ("task_status", task), finish]
    if scenario == "limit":
        flow[2:2] = [("list_files", task), ("search_text", {**task, "query": "add"}),
                     ("search_text", {**task, "query": "return"})]
    return [[value] for value in flow]


@dataclass(frozen=True)
class FixtureTransport:
    scenario: str = "flow"
    mode: str = "modification"
    delay_second: float = 0

    def __call__(self):
        import httpx
        batches = iter(script(self.scenario, self.mode))
        count = 0
        def respond(request):
            nonlocal count
            count += 1
            if count == 2 and self.delay_second:
                time.sleep(self.delay_second)
            body = json.loads(request.content)
            if request.method != "POST" or not request.url.path.endswith("/responses") or body.get("stream"):
                raise AssertionError("Unexpected synthetic provider request")
            calls = next(batches)
            response = {"id": f"resp_{count}", "object": "response", "created_at": 0,
                "model": "gpt-5.6-sol", "status": "completed", "error": None,
                "output": [{"type": "function_call", "id": f"fc_{count}_{index}",
                    "call_id": f"call_{count}_{index}", "name": name, "arguments": json.dumps(arguments),
                    "status": "completed"} for index, (name, arguments) in enumerate(calls)],
                "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}}
            return httpx.Response(200, json=response)
        return httpx.MockTransport(respond)


@dataclass(frozen=True)
class GuardedFixtureRunner:
    runner: object
    endpoint: str

    def __call__(self, context, control):
        allowed = ("127.0.0.1", urlsplit(self.endpoint).port)
        resolve = socket.getaddrinfo
        def guarded_resolution(host, port, *args, **kwargs):
            if host not in {"127.0.0.1", b"127.0.0.1"} or int(port) != allowed[1]:
                raise AssertionError("Unexpected child name resolution")
            return resolve(host, port, *args, **kwargs)
        def guarded(original):
            def connect(sock, address):
                if sock.family in (socket.AF_INET, socket.AF_INET6) and tuple(address[:2]) != allowed:
                    raise AssertionError("Unexpected child network connection")
                return original(sock, address)
            return connect
        with patch.object(socket.socket, "connect", guarded(socket.socket.connect)), \
                patch.object(socket.socket, "connect_ex", guarded(socket.socket.connect_ex)), \
                patch.object(socket, "getaddrinfo", guarded_resolution):
            return self.runner(context, control)


class ExecutorFixture:
    """Disposable Git fixture; executes only fixed test bytes and one exact patch."""

    def __init__(self, root):
        self.source, self.task = Path(root) / "source", Path(root) / "task"
        self.source.mkdir()
        (self.source / "calculator.py").write_text(BEFORE)
        (self.source / "check_fixture.py").write_text(CHECK)
        self.git(self.source, "init", "-q", "-b", "main")
        self.git(self.source, "add", ".")
        self.git(self.source, "-c", "user.name=Synthetic Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-qm", "trusted fixture")
        self.commit = self.git(self.source, "rev-parse", "HEAD").strip()
        self.calls, self.checks = [], []
        self.in_flight = 0
        self.lock = threading.Lock()
        self.mode = None

    @staticmethod
    def git(root, *args):
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                              check=True, timeout=5).stdout

    @contextmanager
    def operation(self, name):
        with self.lock:
            self.calls.append(name)
            self.in_flight += 1
        try:
            yield
        finally:
            with self.lock:
                self.in_flight -= 1

    def stopped(self, identity):
        with self.lock:
            return StopEvidence(identity, self.in_flight == 0)

    def require_task(self, task_id):
        if task_id != TASK or not self.task.exists():
            raise ValueError("Unknown fixture task")

    def status(self):
        return {"task_id": TASK, "branch": "agent/" + TASK,
                "status": self.git(self.task, "status", "--short")}

    def list_repositories(self) -> list[str]:
        with self.operation("list_repositories"):
            return ["fixture", "must-not-disclose"]

    def create_task(self, repository: str, task_name: str, task_mode: str, base_ref: str = "HEAD") -> dict:
        with self.operation("create_task"):
            if repository != "fixture" or base_ref != "HEAD" or task_mode not in {"read_only", "modification"}:
                raise ValueError("Invalid fixture creation")
            self.git(self.source, "worktree", "add", "-q", "-b", "agent/" + TASK, str(self.task), "HEAD")
            self.mode = task_mode
            return {"task_id": TASK, "branch": "agent/" + TASK, "task_branch": "agent/" + TASK,
                    "task_mode": task_mode, "source_repository": repository, "source_ref": "HEAD",
                    "source_branch": "main", "source_commit": self.commit, "source_status": ""}

    def read_file(self, task_id: str, path: str) -> str:
        with self.operation("read_file"):
            self.require_task(task_id)
            if path != "calculator.py":
                raise ValueError("Untrusted fixture path")
            return (self.task / path).read_text()

    def run_check(self, task_id: str, command: str) -> dict:
        with self.operation("run_check"):
            self.require_task(task_id)
            if (command != COMMAND or (self.task / "check_fixture.py").read_text() != CHECK
                    or (self.task / "calculator.py").read_text() not in {BEFORE, AFTER}):
                raise ValueError("Untrusted fixture execution")
            completed = subprocess.run([sys.executable, "-I", str(self.task / "check_fixture.py")],
                cwd=self.task, capture_output=True, text=True, timeout=5)
            result = {"command": command, "exit_code": completed.returncode, "stdout": completed.stdout,
                      "stderr": completed.stderr, "truncated": False}
            self.checks.append(result)
            return result

    def apply_patch(self, task_id: str, patch: str) -> dict:
        with self.operation("apply_patch"):
            self.require_task(task_id)
            if self.mode != "modification" or patch != PATCH or (self.task / "calculator.py").read_text() != BEFORE:
                raise ValueError("Untrusted fixture patch")
            (self.task / "calculator.py").write_text(AFTER)
            return self.status()

    def git_diff(self, task_id: str) -> str:
        with self.operation("git_diff"):
            self.require_task(task_id)
            return self.git(self.task, "diff", "--", "calculator.py")

    def task_status(self, task_id: str) -> dict:
        with self.operation("task_status"):
            self.require_task(task_id)
            return self.status()

    def list_files(self, task_id: str) -> list[str]:
        with self.operation("list_files"):
            self.require_task(task_id)
            return ["calculator.py", "check_fixture.py"]

    def search_text(self, task_id: str, query: str) -> str:
        with self.operation("search_text"):
            self.require_task(task_id)
            return ""

    def __enter__(self):
        import uvicorn
        from fastmcp import FastMCP
        from coding_orchestrator.openhands_backend import EXPECTED_CODING_EXECUTOR_TOOLS
        mcp = FastMCP("synthetic-coding-executor")
        for name in EXPECTED_CODING_EXECUTOR_TOOLS:
            mcp.tool(name=name)(getattr(self, name))
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(128)
        self.endpoint = "http://127.0.0.1:%d/mcp" % self.listener.getsockname()[1]
        self.server = uvicorn.Server(uvicorn.Config(mcp.http_app(path="/mcp", stateless_http=True),
                                                    log_level="critical", lifespan="on"))
        self.thread = threading.Thread(target=self.server.run, kwargs={"sockets": [self.listener]}, daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 10
        while not self.server.started and time.monotonic() < deadline:
            time.sleep(.01)
        if not self.server.started:
            raise RuntimeError("Fixture server did not start")
        return self

    def __exit__(self, *_args):
        self.server.should_exit = True
        self.thread.join(timeout=10)
        self.listener.close()
        if self.thread.is_alive():
            raise RuntimeError("Fixture server did not stop")


class ProfileSDKIntegrationTests(unittest.TestCase):
    @contextmanager
    def job(self, scenario="flow", mode="modification", confirm=True, **transport):
        with tempfile.TemporaryDirectory() as root, ExecutorFixture(root) as fixture, \
                JobStore(Path(root) / "jobs.sqlite") as store:
            options = {"confirm_stopped": fixture.stopped} if confirm else {}
            profile = create_openhands_profile(profile_id="synthetic-sdk", repository_aliases=frozenset({"fixture"}),
                endpoint=fixture.endpoint, token_factory=fixture_token, llm_factory=fixture_llm,
                transport_factory=FixtureTransport(scenario, mode, **transport), authorize=lambda *_: True, **options)
            profile = replace(profile, runner=GuardedFixtureRunner(profile.runner, fixture.endpoint))
            with JobService(store, profile=profile, enabled=True) as service:
                yield service, fixture, Principal("owner", "tenant"), RunScope("fixture", mode)

    def start(self, service, owner, scope, **limits):
        return service.start_run(owner, JobRequest("Fix the trusted fixture and verify it.", "fixture-run", "generation", 1,
                                                  scope, **{"timeout_seconds": 60, **limits}))

    def wait(self, service, owner, run):
        deadline = time.monotonic() + 70
        while run["state"] in {"queued", "running", "cancelling"} and time.monotonic() < deadline:
            time.sleep(.02)
            run = service.get_run(owner, run["job_id"])
        self.assertNotIn(run["state"], {"queued", "running", "cancelling"}, run)
        return run

    def test_actual_sdk_repairs_fixture_with_matched_evidence_and_stored_retrieval(self):
        with self.job() as (service, fixture, owner, scope):
            run = self.wait(service, owner, self.start(service, owner, scope))
            self.assertEqual(run["state"], "completed", run)
            self.assertEqual(run["request_count"], 8)
            self.assertEqual(fixture.calls, ["create_task", "read_file", "run_check", "apply_patch",
                                              "run_check", "git_diff", "task_status"])
            evidence = run["result"]["evidence"]
            self.assertEqual(evidence["task"]["task_id"], TASK)
            self.assertEqual(evidence["task"]["source_commit"], fixture.commit)
            self.assertEqual([check["exit_code"] for check in evidence["checks"]], [1, 0])
            for proof, actual in zip(evidence["checks"], fixture.checks, strict=True):
                self.assertEqual(proof["command"], COMMAND)
                self.assertEqual(proof["stdout_sha256"], hashlib.sha256(actual["stdout"].encode()).hexdigest())
                self.assertEqual(proof["stderr_sha256"], hashlib.sha256(actual["stderr"].encode()).hexdigest())
                self.assertLess(proof["started"], proof["completed"])
                self.assertTrue(proof["action_id"])
                self.assertTrue(proof["tool_call_id"])
            self.assertNotEqual(evidence["checks"][0]["tool_call_id"], evidence["checks"][1]["tool_call_id"])
            self.assertEqual(evidence["observed_checks_status"], "passed")
            self.assertTrue(evidence["evidence_complete"])
            self.assertEqual(evidence["action_count"], 8)
            self.assertEqual(evidence["pending_count"], 0)
            self.assertEqual(evidence["final_diff"]["text"], fixture.git(fixture.task, "diff", "--", "calculator.py"))
            self.assertEqual((fixture.source / "calculator.py").read_text(), BEFORE)
            self.assertEqual(fixture.git(fixture.source, "status", "--short"), "")
            self.assertEqual(service.get_run(owner, run["job_id"]), run)
            service.close()
            service.store.close()
            with JobStore(fixture.source.parent / "jobs.sqlite") as reopened:
                stored = reopened.get(owner.user_id, owner.tenant_id, run["job_id"])
                self.assertEqual(stored["result"], run["result"])
                self.assertEqual(stored["request_count"], 8)

    def test_completion_is_distinct_from_evidence_and_stop_confirmation(self):
        for confirm, expected in ((True, "completed"), (False, "interrupted")):
            with self.subTest(confirm=confirm), self.job("finish", confirm=confirm) as (service, fixture, owner, scope):
                run = self.wait(service, owner, self.start(service, owner, scope))
                self.assertEqual(run["state"], expected, run)
                self.assertEqual(run["request_count"], 1)
                self.assertFalse(run["result"]["evidence"]["evidence_complete"])
                self.assertEqual(run["result"]["evidence"]["observed_checks_status"], "not_run")
                self.assertEqual(fixture.calls, [])
                if not confirm:
                    self.assertEqual(run["error_code"], "execution_stop_unconfirmed")

    def test_scope_mode_task_identity_and_batches_are_rejected_before_disallowed_calls(self):
        for scenario, mode, expected in (("repository", "modification", []), ("mode", "modification", []),
                ("list", "modification", []), ("batch", "modification", []),
                ("foreign_task", "modification", ["create_task"]), ("readonly_patch", "read_only", ["create_task"])):
            with self.subTest(scenario=scenario), self.job(scenario, mode) as (service, fixture, owner, scope):
                run = self.wait(service, owner, self.start(service, owner, scope))
                self.assertEqual(run["state"], "failed", run)
                self.assertEqual(run["error_code"], "worker_failed")
                self.assertEqual(fixture.calls, expected)
                self.assertEqual(run["request_count"], 2 if expected else 1)
                if expected or scenario == "batch":
                    self.assertIsNotNone(run["result"])
                    self.assertFalse(run["result"]["evidence"]["evidence_complete"])
                if scenario == "batch":
                    self.assertEqual(run["result"]["evidence"]["pending_count"], 1)

    def test_request_limit_preserves_partial_evidence(self):
        with self.job() as (service, fixture, owner, scope):
            run = self.wait(service, owner, self.start(service, owner, scope, max_requests=1))
            self.assertEqual(run["state"], "failed", run)
            self.assertEqual(run["error_code"], "worker_limit")
            self.assertEqual(run["request_count"], 1)
            self.assertEqual(fixture.calls, ["create_task"])
            self.assertEqual(run["result"]["evidence"]["task"]["task_id"], TASK)

    def test_tenth_request_is_last_physical_dispatch(self):
        with self.job("limit") as (service, fixture, owner, scope):
            run = self.wait(service, owner, self.start(service, owner, scope))
            self.assertEqual(run["state"], "failed", run)
            self.assertEqual(run["error_code"], "worker_limit")
            self.assertEqual(run["request_count"], 10)
            self.assertEqual(len(fixture.calls), 10)
            self.assertEqual(run["result"]["evidence"]["action_count"], 10)

    def test_cancel_and_deadline_keep_partial_evidence_and_correct_classification(self):
        for cancel in (True, False):
            with self.subTest(cancel=cancel), self.job(delay_second=90) as (service, fixture, owner, scope):
                run = self.start(service, owner, scope, timeout_seconds=60 if cancel else 45)
                deadline = time.monotonic() + 40
                while (run["result"] is None or run["result"]["evidence"]["task"] is None) and time.monotonic() < deadline:
                    time.sleep(.02)
                    run = service.get_run(owner, run["job_id"])
                self.assertIsNotNone(run["result"], run)
                self.assertIsNotNone(run["result"]["evidence"]["task"], run)
                if cancel:
                    service.cancel_run(owner, run["job_id"], generation_id="generation", generation_epoch=1)
                run = self.wait(service, owner, run)
                self.assertEqual(run["state"], "cancelled" if cancel else "timed_out", run)
                self.assertEqual(run["error_code"], "cancel_requested" if cancel else "deadline_exceeded")
                self.assertEqual(fixture.calls, ["create_task"])
                self.assertFalse(run["result"]["evidence"]["evidence_complete"])


if __name__ == "__main__":
    unittest.main()
