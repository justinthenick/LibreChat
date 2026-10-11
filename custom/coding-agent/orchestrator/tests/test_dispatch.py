from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import UUID

from coding_orchestrator.dispatch import MAX_INPUT_BYTES, MAX_OUTPUT_BYTES, dispatch_job
from coding_orchestrator.job_store import JobStore, StopEvidence
from coding_orchestrator.jobs import ExecutionProfile, JobError, JobService, Principal


def start_message(**changes):
    request = {"prompt": "Inspect the synthetic fixture.", "idempotency_key": "request-1",
               "scope": {"repository_alias": "fixture", "task_mode": "read_only"},
               "max_requests": 10, "timeout_seconds": 300}
    request.update(changes)
    return {"version": 1, "operation": "start", "request": request}


def lifecycle(operation, job_id):
    return {"version": 1, "operation": operation, "request": {"job_id": job_id}}


def completed_result():
    return {"execution_status": "finished", "final_response": "Synthetic fixture inspected.",
            "evidence": {"repository_alias": "fixture", "task": None, "checks": [],
                         "final_diff": None, "final_status": None, "observed_checks_status": "not_run",
                         "evidence_complete": False, "action_count": 0, "pending_count": 0, "errors": []}}


class ControlledWorker:
    def __init__(self, runner, context, **kwargs):
        self.context, self.kwargs = context, kwargs
        self.outcome = None
        self.request_count = 0
        self.cancelled = False

    def start(self):
        pass

    def poll(self):
        return self.outcome

    def finish(self):
        self.outcome = SimpleNamespace(state="completed", result=completed_result(),
                                       error_code=None, request_count=self.request_count)

    def cancel(self):
        self.cancelled = True
        self.outcome = SimpleNamespace(state="cancelled", result=None, error_code="cancelled",
                                       request_count=self.request_count)

    def close(self):
        if self.outcome is None:
            self.cancel()


class DispatchTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="dispatch-tests-")
        self.addCleanup(directory.cleanup)
        self.store = JobStore(Path(directory.name) / "jobs.sqlite")
        self.addCleanup(self.store.close)
        self.owner = Principal("owner", "tenant")
        self.workers = []
        self.allowed, self.stopped = True, True

        def factory(*args, **kwargs):
            worker = ControlledWorker(*args, **kwargs)
            self.workers.append(worker)
            return worker

        profile = ExecutionProfile("test-profile", frozenset({"fixture"}), lambda *_: completed_result(),
                                   lambda *_: self.allowed, lambda identity: StopEvidence(identity, self.stopped))
        self.service = JobService(self.store, enabled=True, profile=profile, worker_factory=factory)
        self.addCleanup(self.service.close)

    def dispatch(self, message, principal=None):
        return dispatch_job(self.service, self.owner if principal is None else principal, message)

    def assert_error(self, response, code):
        self.assertEqual(response, {"version": 1, "ok": False, "error": code})

    def start(self, **changes):
        response = self.dispatch(start_message(**changes))
        self.assertEqual(set(response), {"version", "ok", "job"})
        self.assertIs(response["ok"], True, response)
        return response["job"]

    def wait_terminal(self, job_id, principal=None):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            response = self.dispatch(lifecycle("get", job_id), principal)
            self.assertIs(response["ok"], True, response)
            if response["job"]["state"] not in {"queued", "running", "cancelling"}:
                return response["job"]
            time.sleep(.01)
        self.fail("job did not reach a terminal state")

    def test_start_derives_identity_and_preserves_public_record(self):
        job = self.start()
        self.assertEqual(UUID(job["job_id"]).version, 4)
        self.assertEqual(job["generation_id"], "preview:" + hashlib.sha256(b"request-1").hexdigest())
        self.assertEqual(job["generation_epoch"], 0)
        self.assertNotEqual(job["job_id"], job["generation_id"])
        self.assertEqual(self.workers[0].context.job_id, job["job_id"])
        self.assertEqual(self.workers[0].kwargs["max_requests"], 10)
        fetched = self.dispatch(lifecycle("get", job["job_id"]))["job"]
        public = self.service.get_run(self.owner, job["job_id"])
        self.assertEqual(set(fetched), set(public))
        # The monitor may publish its first request-count timestamp between reads.
        self.assertEqual({key: value for key, value in fetched.items() if key != "updated_at"},
                         {key: value for key, value in public.items() if key != "updated_at"})
        self.assertFalse({"user_id", "tenant_id", "prompt", "fingerprint", "idempotency_key"} & job.keys())

    def test_idempotency_conflict_and_single_execution(self):
        job = self.start()
        self.assertEqual(self.start()["job_id"], job["job_id"])
        self.assert_error(self.dispatch(start_message(prompt="Changed prompt.")), "idempotency_conflict")
        self.assert_error(self.dispatch(start_message(idempotency_key="other")), "job_busy")
        self.assertEqual(len(self.workers), 1)
        self.workers[0].finish()
        self.wait_terminal(job["job_id"])
        self.assertEqual(self.start()["job_id"], job["job_id"])
        self.assertEqual(len(self.workers), 1)

    def test_owner_tenant_isolation_and_owner_scoped_idempotency(self):
        first = self.start()
        for other in (Principal("other", "tenant"), Principal("owner", "other")):
            for operation in ("get", "cancel"):
                self.assert_error(self.dispatch(lifecycle(operation, first["job_id"]), other), "job_not_found")
        self.assertFalse(self.workers[0].cancelled)
        self.workers[0].finish()
        self.wait_terminal(first["job_id"])
        other = Principal("owner", "other")
        second = self.dispatch(start_message(), other)["job"]
        self.assertNotEqual(second["job_id"], first["job_id"])
        self.assertEqual(second["generation_id"], first["generation_id"])
        self.assertEqual(len(self.workers), 2)

    def test_explicit_cancel_uses_stored_generation_and_retains_evidence(self):
        job = self.start()
        partial = {"evidence": completed_result()["evidence"]}
        self.workers[0].kwargs["on_progress"](partial)
        with patch.object(self.service, "cancel_run", wraps=self.service.cancel_run) as cancel:
            response = self.dispatch(lifecycle("cancel", job["job_id"]))
            self.assertIs(response["ok"], True)
            cancel.assert_called_once_with(self.owner, job["job_id"],
                generation_id=job["generation_id"], generation_epoch=0)
        terminal = self.wait_terminal(job["job_id"])
        self.assertEqual(terminal["state"], "cancelled")
        self.assertEqual(terminal["result"], partial)
        self.assertEqual(self.dispatch(lifecycle("cancel", job["job_id"]))["job"], terminal)

    def test_unconfirmed_stop_stays_interrupted(self):
        self.stopped = False
        job = self.start()
        self.assertIs(self.dispatch(lifecycle("cancel", job["job_id"]))["ok"], True)
        terminal = self.wait_terminal(job["job_id"])
        self.assertEqual(terminal["state"], "interrupted")
        self.assertEqual(terminal["error_code"], "execution_stop_unconfirmed")
        self.assertEqual(self.start()["state"], "interrupted")
        self.assertEqual(len(self.workers), 1)

    def test_completion_and_get_never_implicitly_cancel(self):
        job = self.start()
        self.dispatch(lifecycle("get", job["job_id"]))
        self.assertFalse(self.workers[0].cancelled)
        self.workers[0].finish()
        terminal = self.wait_terminal(job["job_id"])
        self.assertEqual(terminal["state"], "completed")
        self.assertEqual(terminal["result"], completed_result())

    def test_disabled_and_untrusted_principal_never_start(self):
        disabled = JobService(self.store)
        self.assert_error(dispatch_job(disabled, self.owner, start_message()), "preview_jobs_disabled")
        for principal in (None, {}, {"user_id": "owner", "tenant_id": "tenant"}, "owner"):
            self.assert_error(dispatch_job(self.service, principal, start_message()), "authenticated_principal_required")
        self.assertEqual(self.workers, [])

    def test_authorization_precedes_admission_and_runs_for_repeated_starts(self):
        self.allowed = False
        self.assert_error(self.dispatch(start_message()), "scope_not_authorized")
        self.assert_error(self.dispatch(start_message(scope={"repository_alias": "other", "task_mode": "read_only"})),
                          "scope_not_authorized")
        self.assertEqual(self.workers, [])
        self.allowed = True
        self.start()
        self.allowed = False
        self.assert_error(self.dispatch(start_message()), "scope_not_authorized")
        self.assertEqual(len(self.workers), 1)

    def test_closed_envelope_and_request_shapes(self):
        cases = [None, [], "{}", b"{}", {}, {**start_message(), "version": True},
                 {**start_message(), "version": 1.0}, {**start_message(), "version": 2},
                 {**start_message(), "operation": []}, {**start_message(), "operation": "listen"},
                 {**start_message(), "request": None}]
        for key in start_message():
            message = start_message()
            del message[key]
            cases.append(message)
        for key in start_message()["request"]:
            message = start_message()
            del message["request"][key]
            cases.append(message)
        for key in ("principal", "owner", "user_id", "tenant_id", "generation_id", "generation_epoch",
                    "endpoint", "transport", "profile", "credentials", "path", "url"):
            cases.extend([{**start_message(), key: "injected"}, start_message(**{key: "injected"})])
        for key in ("repository_alias", "task_mode"):
            message = start_message()
            del message["request"]["scope"][key]
            cases.append(message)
        cases.append(start_message(scope={"repository_alias": "fixture", "task_mode": "read_only", "path": "/repo"}))
        for message in cases:
            with self.subTest(message=message):
                self.assert_error(self.dispatch(message), "invalid_job_message")
        self.assertEqual(self.workers, [])

    def test_lifecycle_accepts_only_one_bounded_identifier(self):
        for operation in ("get", "cancel"):
            for value in (None, "", True, 1, [], "../job", "job/id", "é", "x" * 129, " job", "_job"):
                self.assert_error(self.dispatch(lifecycle(operation, value)), "invalid_job_message")
            for key in ("generation_id", "generation_epoch", "owner", "principal"):
                message = lifecycle(operation, "valid-job")
                message["request"][key] = "injected"
                self.assert_error(self.dispatch(message), "invalid_job_message")
            self.assert_error(self.dispatch(lifecycle(operation, "x" * 128)), "job_not_found")
        self.assertEqual(self.workers, [])

    def test_start_limits_reject_bool_nonfinite_and_wrong_types(self):
        cases = ({"prompt": " "}, {"prompt": None}, {"prompt": "é" * 16385},
                 {"idempotency_key": "x" * 129}, {"idempotency_key": "../key"}, {"idempotency_key": 4},
                 {"max_requests": True}, {"max_requests": 0}, {"max_requests": 11}, {"max_requests": 1.0},
                 {"timeout_seconds": True}, {"timeout_seconds": 0}, {"timeout_seconds": 301},
                 {"timeout_seconds": float("nan")}, {"timeout_seconds": float("inf")},
                 {"timeout_seconds": -float("inf")}, {"timeout_seconds": 10 ** 400},
                 {"scope": {"repository_alias": "fixture", "task_mode": "shell"}})
        for changes in cases:
            with self.subTest(changes=changes):
                self.assert_error(self.dispatch(start_message(**changes)), "invalid_job_message")
        self.assertEqual(self.workers, [])
        job = self.start(prompt="é" * 16384, idempotency_key="x" * 128, max_requests=1, timeout_seconds=.5)
        self.assertEqual(job["metadata"]["max_requests"], 1)
        self.assertEqual(job["metadata"]["timeout_seconds"], .5)

    def test_non_json_values_cycles_prototype_keys_and_depth_are_rejected(self):
        class MappingSubclass(dict):
            pass

        cycle = []
        cycle.append(cycle)
        nested = "leaf"
        for _ in range(18):
            nested = [nested]
        for value in (object(), {"a"}, (1, 2), MappingSubclass(), {1: "value"}, cycle, nested, "\ud800"):
            self.assert_error(self.dispatch(start_message(prompt=value)), "invalid_job_message")
        self.assert_error(self.dispatch(MappingSubclass(start_message())), "invalid_job_message")
        for key in ("__proto__", "constructor", "prototype"):
            self.assert_error(self.dispatch(start_message(scope={key: {}})), "invalid_job_message")
        self.assert_error(self.dispatch('{"version":1,"version":2}'), "invalid_job_message")
        self.assertEqual(self.workers, [])

    def test_input_budget_counts_json_escaping_and_utf8(self):
        message = start_message(prompt="x" + "\x00" * 6500)
        encoded = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode()
        message["request"]["prompt"] += "a" * (MAX_INPUT_BYTES - len(encoded))
        self.assertEqual(len(json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode()), MAX_INPUT_BYTES)
        oversized = deepcopy(message)
        oversized["request"]["prompt"] += "a"
        self.assert_error(self.dispatch(oversized), "invalid_job_message")
        self.assertEqual(self.workers, [])
        self.assertIs(self.dispatch(message)["ok"], True)

    def test_worker_and_service_failures_have_fixed_public_codes(self):
        def broken(*_args, **_kwargs):
            raise RuntimeError("secret-worker-error")

        self.service._worker_factory = broken
        self.assert_error(self.dispatch(start_message()), "worker_start_failed")
        self.assertEqual(self.start()["state"], "failed")
        for error in (RuntimeError("private-exception"), JobError("private-job-error")):
            with patch.object(self.service, "get_run", side_effect=error):
                self.assert_error(self.dispatch(lifecycle("get", "job")), "job_service_unavailable")
        for code in ("stale_generation", "admission_deadline_exceeded"):
            with patch.object(self.service, "get_run", side_effect=JobError(code)):
                self.assert_error(self.dispatch(lifecycle("get", "job")), code)

    def test_output_budget_and_invalid_output_never_expose_raw_errors(self):
        job = self.start()
        job["result"] = {"text": ""}
        response = {"version": 1, "ok": True, "job": job}
        overhead = len(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode())
        job["result"]["text"] = "é" * ((MAX_OUTPUT_BYTES - overhead) // 2)
        remaining = MAX_OUTPUT_BYTES - len(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode())
        job["result"]["text"] += "a" * remaining
        with patch.object(self.service, "get_run", return_value=job):
            self.assertIs(self.dispatch(lifecycle("get", job["job_id"]))["ok"], True)
            job["result"]["text"] += "a"
            self.assert_error(self.dispatch(lifecycle("get", job["job_id"])), "job_service_unavailable")
        for invalid in (None, {**job, "result": object()}, {**job, "result": float("nan")},
                        {**job, "result": "\ud800"}):
            with patch.object(self.service, "get_run", return_value=invalid):
                self.assert_error(self.dispatch(lifecycle("get", job["job_id"])), "job_service_unavailable")

    def test_get_and_cancel_reject_unsafe_stored_identity(self):
        job = self.start()
        for invalid in ({"generation_epoch": True}, {"generation_epoch": -1},
                        {"generation_epoch": 9007199254740992}, {"generation_id": "../generation"}):
            with patch.object(self.service, "get_run", return_value={**job, **invalid}):
                for operation in ("get", "cancel"):
                    self.assert_error(self.dispatch(lifecycle(operation, job["job_id"])), "job_service_unavailable")
        self.assertFalse(self.workers[0].cancelled)


if __name__ == "__main__":
    unittest.main()
