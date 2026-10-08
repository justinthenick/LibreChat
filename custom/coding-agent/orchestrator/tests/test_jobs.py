from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest

from coding_orchestrator.job_store import IdempotencyConflict, JobNotFound, JobStore
from coding_orchestrator.jobs import ExecutionProfile, JobError, JobRequest, JobService, Principal, RunScope


def evidence():
    return {"repository_alias": "fixture", "task": None, "checks": [], "final_diff": None,
            "final_status": None, "observed_checks_status": "not_run", "evidence_complete": False,
            "action_count": 0, "pending_count": 0, "errors": []}


def result():
    return {"execution_status": "finished", "final_response": "Read-only fixture complete.", "evidence": evidence()}


class FakeWorker:
    def __init__(self, runner, context, **kwargs):
        self.context = context
        self.kwargs = kwargs
        self.outcome = None
        self.request_count = 0
        self.cancelled = False
        self.closed = False

    def start(self):
        pass

    def poll(self):
        return self.outcome

    def cancel(self):
        self.cancelled = True
        self.outcome = SimpleNamespace(state="cancelled", result=None, error_code="cancelled", request_count=self.request_count)

    def close(self):
        self.closed = True
        if self.outcome is None:
            self.cancel()


class JobServiceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = JobStore(Path(self.directory.name) / "jobs.sqlite")
        self.addCleanup(self.store.close)
        self.workers = []
        self.stopped = True
        self.allowed = True
        def factory(*args, **kwargs):
            worker = FakeWorker(*args, **kwargs)
            self.workers.append(worker)
            return worker
        profile = ExecutionProfile("test-profile", frozenset({"fixture"}), lambda *_: result(),
            lambda *_: self.allowed, lambda *_: self.stopped)
        self.service = JobService(self.store, profile=profile, enabled=True, worker_factory=factory)
        self.addCleanup(self.service.close)
        self.owner = Principal("owner", "tenant")
        self.request = JobRequest("Inspect the synthetic fixture.", "request-1", "generation-1", 123, RunScope("fixture"))

    def wait_terminal(self, job_id):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            record = self.service.get_run(self.owner, job_id)
            if record["state"] not in {"queued", "running", "cancelling"}:
                return record
            time.sleep(.01)
        self.fail("job did not reach a terminal state")

    def test_default_disabled_and_principal_required(self):
        disabled = JobService(self.store)
        with self.assertRaisesRegex(JobError, "preview_jobs_disabled"):
            disabled.start_run(self.owner, self.request)
        with self.assertRaisesRegex(JobError, "authenticated_principal_required"):
            self.service.start_run({"user_id": "owner"}, self.request)
        self.assertEqual(self.workers, [])

    def test_scope_denial_before_worker_and_store_admission(self):
        self.allowed = False
        with self.assertRaisesRegex(JobError, "scope_not_authorized"):
            self.service.start_run(self.owner, self.request)
        self.assertEqual(self.workers, [])
        self.allowed = True
        with self.assertRaisesRegex(JobError, "scope_not_authorized"):
            self.service.start_run(self.owner, replace(self.request, scope=RunScope("other")))

    def test_idempotent_start_never_creates_second_worker(self):
        first = self.service.start_run(self.owner, self.request)
        second = self.service.start_run(self.owner, self.request)
        self.assertEqual(first["job_id"], second["job_id"])
        self.assertEqual(len(self.workers), 1)
        with self.assertRaises(IdempotencyConflict):
            self.service.start_run(self.owner, replace(self.request, prompt="different"))

    def test_result_has_evidence_but_no_owner_or_prompt_fields(self):
        job = self.service.start_run(self.owner, self.request)
        self.workers[0].request_count = 2
        self.workers[0].outcome = SimpleNamespace(state="completed", result=result(), error_code=None, request_count=2)
        terminal = self.wait_terminal(job["job_id"])
        self.assertEqual(terminal["state"], "completed")
        self.assertEqual(terminal["request_count"], 2)
        self.assertFalse(terminal["result"]["evidence"]["evidence_complete"])
        self.assertEqual(terminal["result"]["evidence"]["observed_checks_status"], "not_run")
        self.assertFalse({"user_id", "tenant_id", "prompt", "fingerprint"} & terminal.keys())

    def test_owner_tenant_and_generation_fences(self):
        job = self.service.start_run(self.owner, self.request)
        for other in (Principal("other", "tenant"), Principal("owner", "different")):
            with self.assertRaises(JobNotFound):
                self.service.get_run(other, job["job_id"])
            with self.assertRaises(JobNotFound):
                self.service.cancel_run(other, job["job_id"], generation_id="generation-1", generation_epoch=123)
        with self.assertRaisesRegex(JobError, "stale_generation"):
            self.service.cancel_run(self.owner, job["job_id"], generation_id="generation-1", generation_epoch=122)
        self.assertFalse(self.workers[0].cancelled)

    def test_cancel_requires_external_stop_confirmation(self):
        self.stopped = False
        job = self.service.start_run(self.owner, self.request)
        self.service.cancel_run(self.owner, job["job_id"], generation_id="generation-1", generation_epoch=123)
        terminal = self.wait_terminal(job["job_id"])
        self.assertEqual(terminal["state"], "interrupted")
        self.assertEqual(terminal["error_code"], "execution_stop_unconfirmed")

    def test_confirmed_cancel_retains_partial_evidence(self):
        job = self.service.start_run(self.owner, self.request)
        partial = {"evidence": evidence()}
        self.workers[0].kwargs["on_progress"](partial)
        self.service.cancel_run(self.owner, job["job_id"], generation_id="generation-1", generation_epoch=123)
        terminal = self.wait_terminal(job["job_id"])
        self.assertEqual(terminal["state"], "cancelled")
        self.assertEqual(terminal["result"], partial)
        self.workers[0].kwargs["on_progress"]({"evidence": {**evidence(), "action_count": 99}})
        self.assertEqual(self.service.get_run(self.owner, job["job_id"]), terminal)

    def test_cancel_during_stop_confirmation_wins_over_completion(self):
        entered, release = threading.Event(), threading.Event()
        def confirmation(_context):
            entered.set()
            return release.wait(2)
        self.service.profile = replace(self.service.profile, confirm_stopped=confirmation)
        job = self.service.start_run(self.owner, self.request)
        self.workers[0].outcome = SimpleNamespace(state="completed", result=result(), error_code=None, request_count=0)
        self.assertTrue(entered.wait(2))
        self.service.cancel_run(self.owner, job["job_id"], generation_id="generation-1", generation_epoch=123)
        release.set()
        self.assertEqual(self.wait_terminal(job["job_id"])["state"], "cancelled")
        next_job = self.service.start_run(self.owner, replace(self.request, idempotency_key="next-job"))
        self.assertNotEqual(next_job["job_id"], job["job_id"])

    def test_missing_or_unapproved_result_does_not_complete(self):
        for output in (None, {"token": "must-not-persist"}, {**result(), "evidence": {**evidence(), "repository_alias": "other"}}):
            request = replace(self.request, idempotency_key="case-" + str(len(self.workers)))
            job = self.service.start_run(self.owner, request)
            self.workers[-1].outcome = SimpleNamespace(state="completed", result=output, error_code=None, request_count=0)
            terminal = self.wait_terminal(job["job_id"])
            self.assertEqual(terminal["state"], "failed")
            self.assertEqual(terminal["error_code"], "invalid_profile_result")
            self.assertNotIn("must-not-persist", str(terminal))

    def test_worker_constructor_failure_is_terminal(self):
        def broken(*args, **kwargs):
            raise RuntimeError("private-error")
        self.service._worker_factory = broken
        with self.assertRaisesRegex(JobError, "worker_start_failed"):
            self.service.start_run(self.owner, self.request)
        self.assertIsNone(self.service._active)
        repeated = self.service.start_run(self.owner, self.request)
        self.assertEqual(repeated["state"], "failed")
        self.assertNotIn("private-error", str(repeated))

    def test_request_limits_are_strict_and_do_not_accept_booleans(self):
        for fields in ({"max_requests": 11}, {"max_requests": True}, {"timeout_seconds": 301},
                       {"timeout_seconds": float("nan")}, {"generation_epoch": True}, {"prompt": " "}):
            with self.assertRaises(JobError):
                replace(self.request, **fields)

    def test_unicode_diff_survives_result_and_storage_bounds(self):
        job = self.service.start_run(self.owner, self.request)
        completed = result()
        completed["evidence"]["final_diff"] = {"text": "é" * 32768}
        self.workers[0].outcome = SimpleNamespace(state="completed", result=completed, error_code=None, request_count=0)
        terminal = self.wait_terminal(job["job_id"])
        self.assertEqual(terminal["state"], "completed")
        self.assertEqual(terminal["result"], completed)


if __name__ == "__main__":
    unittest.main()
