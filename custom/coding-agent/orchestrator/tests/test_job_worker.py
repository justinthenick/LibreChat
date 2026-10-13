from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib.util
import os
from pathlib import Path
import signal
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from coding_orchestrator.job_worker import (
    MAX_JSON_BYTES, MAX_PROGRESS_MESSAGES, ProcessWorker, RunContext, WorkerLimit,
)


def count_requests(context, control):
    for _ in range(int(context.prompt)):
        control.before_provider_request()
    return {"requests": int(context.prompt)}


def threaded_requests(context, control):
    accepted = []
    rejected = []

    def attempt():
        try:
            control.before_provider_request()
            accepted.append(True)
        except WorkerLimit:
            rejected.append(True)

    threads = [threading.Thread(target=attempt) for _ in range(30)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return {"accepted": len(accepted), "rejected": len(rejected)}


def blocked_runner(context, control):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    control.before_provider_request()
    control.emit_progress({"ready": True})
    time.sleep(30)
    return {"unexpected": True}


def failing_runner(context, control):
    raise RuntimeError("secret exception message must never be returned")


def abrupt_runner(context, control):
    os._exit(7)


def progress_runner(context, control):
    for index in range(int(context.prompt)):
        control.emit_progress({"step": index})
    return {"done": True, "nested": [{"text": "exact result"}]}


def oversize_progress(context, control):
    control.emit_progress({"text": "x" * MAX_JSON_BYTES})
    return {"unexpected": True}


def large_progress(context, control):
    for index in range(MAX_PROGRESS_MESSAGES):
        control.emit_progress({"step": index, "text": "x" * (MAX_JSON_BYTES - 100)})
    return {"large": "x" * (MAX_JSON_BYTES - 100)}


def invalid_result(context, control):
    return {"value": float("nan")}


def isolated_runner(context, control):
    return {"environment": dict(os.environ), "cwd": os.getcwd(),
            "stdin": os.read(0, 1).decode(),
            "sdk_loaded": any(name.startswith("openhands.sdk") for name in sys.modules),
            "home_private":
            Path(os.environ["HOME"]).stat().st_mode & 0o777,
            "pid": os.getpid(), "group": os.getpgrp(), "session": os.getsid(0)}


def lingering_thread_runner(context, control):
    # Returning a result is not enough: interpreter shutdown waits for this thread.
    thread = threading.Thread(target=time.sleep, args=(30,))
    thread.start()
    return {"returned": True}


def descendant_runner(context, control):
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        os.write(write_fd, b"1")
        os.close(write_fd)
        time.sleep(10)
        os._exit(0)
    os.close(write_fd)
    os.read(read_fd, 1)
    os.close(read_fd)
    control.emit_progress({"descendant": pid})
    if context.prompt == "wait":
        # The leader exits on TERM, while its child deliberately ignores TERM.
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        time.sleep(10)
    return {"descendant": pid}


def unicode_runner(context, control):
    control.emit_progress({"text": "é" * 40000})
    return {"text": "漢" * 40000}


class JobWorkerTests(unittest.TestCase):
    def worker(self, runner=count_requests, prompt="0", **kwargs):
        worker = ProcessWorker(runner, RunContext("job", prompt, "repo", "test"), **kwargs)
        self.addCleanup(worker.close)
        return worker

    def finish(self, worker, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            outcome = worker.poll()
            if outcome is not None:
                return outcome
            time.sleep(0.005)
        self.fail("Worker did not finish within the test deadline")

    def wait_progress(self, worker, progress, timeout=5):
        deadline = time.monotonic() + timeout
        while not progress and time.monotonic() < deadline:
            worker.poll()
            time.sleep(0.005)
        self.assertTrue(progress)

    def test_limit_allows_ten_and_rejects_eleventh_physical_request(self):
        for requests, state, code in ((10, "completed", None),
                                      (11, "failed", "worker_limit")):
            with self.subTest(requests=requests):
                worker = self.worker(prompt=str(requests))
                worker.start()
                outcome = self.finish(worker)
                self.assertEqual((outcome.state, outcome.error_code), (state, code))
                self.assertEqual(outcome.request_count, 10)
                self.assertEqual(worker.request_count, 10)
                self.assertIs(worker.poll(), outcome)
                if state == "completed":
                    self.assertEqual(outcome.result, {"requests": 10})

    def test_counter_is_atomic_under_concurrent_adapter_calls(self):
        worker = self.worker(threaded_requests)
        worker.start()
        outcome = self.finish(worker)
        self.assertEqual((outcome.state, outcome.error_code, outcome.request_count),
                         ("failed", "worker_limit", 10))

    def test_cancel_before_start_never_runs(self):
        worker = self.worker(prompt="1")
        worker.cancel()
        worker.start()
        outcome = worker.poll()
        self.assertEqual((outcome.state, outcome.request_count), ("cancelled", 0))
        self.assertIsNone(worker._process)

    def test_cancel_blocked_runner_kills_and_reaps_after_bounded_grace(self):
        progress = []
        worker = self.worker(blocked_runner, on_progress=progress.append)
        worker.start()
        self.wait_progress(worker, progress)
        started = time.monotonic()
        worker.cancel()
        outcome = self.finish(worker)
        self.assertEqual((outcome.state, outcome.request_count), ("cancelled", 1))
        self.assertLess(time.monotonic() - started, 2)
        self.assertFalse(worker._process.is_alive())
        self.assertEqual(worker._process.exitcode, -signal.SIGKILL)

    def test_parent_deadline_stops_runner_without_cooperative_checks(self):
        worker = self.worker(blocked_runner, timeout_seconds=0.5)
        worker.start()
        started = time.monotonic()
        outcome = self.finish(worker)
        self.assertEqual((outcome.state, outcome.error_code),
                         ("timed_out", "deadline_exceeded"))
        self.assertLess(time.monotonic() - started, 2)
        self.assertFalse(worker._process.is_alive())

    def test_exception_and_abrupt_exit_have_fixed_error_codes(self):
        for runner, state, code in ((failing_runner, "failed", "worker_failed"),
                                     (abrupt_runner, "interrupted", "worker_interrupted")):
            with self.subTest(runner=runner):
                worker = self.worker(runner)
                worker.start()
                outcome = self.finish(worker)
                self.assertEqual((outcome.state, outcome.error_code), (state, code))
                self.assertNotIn("secret", repr(outcome))

    def test_progress_count_bound_and_exact_result_delivery(self):
        for count in (MAX_PROGRESS_MESSAGES, MAX_PROGRESS_MESSAGES + 1):
            progress = []
            worker = self.worker(progress_runner, str(count), on_progress=progress.append)
            worker.start()
            outcome = self.finish(worker)
            self.assertEqual(progress, [{"step": index} for index in range(64)])
            if count == 64:
                self.assertEqual(outcome.state, "completed")
                self.assertEqual(outcome.result,
                                 {"done": True, "nested": [{"text": "exact result"}]})
            else:
                self.assertEqual((outcome.state, outcome.error_code),
                                 ("failed", "worker_limit"))
            worker.poll()
            self.assertEqual(len(progress), 64)

    def test_json_size_and_invalid_result_are_bounded_fixed_failures(self):
        for runner, code in ((oversize_progress, "worker_limit"),
                              (invalid_result, "worker_failed")):
            worker = self.worker(runner)
            worker.start()
            outcome = self.finish(worker)
            self.assertEqual((outcome.state, outcome.error_code, outcome.result),
                             ("failed", code, None))

    def test_large_progress_and_result_do_not_deadlock_on_pipe_capacity(self):
        progress = []
        worker = self.worker(large_progress, on_progress=progress.append)
        worker.start()
        outcome = self.finish(worker)
        self.assertEqual(outcome.state, "completed")
        self.assertEqual(len(progress), 64)
        self.assertEqual(len(outcome.result["large"]), MAX_JSON_BYTES - 100)

    def test_result_from_still_living_child_is_not_completion(self):
        worker = self.worker(lingering_thread_runner, timeout_seconds=5)
        worker.start()
        until = time.monotonic() + 4
        while worker._pending is None and time.monotonic() < until:
            self.assertIsNone(worker.poll())
            time.sleep(0.005)
        self.assertIsNotNone(worker._pending)
        self.assertTrue(worker._process.is_alive())
        clock = time.monotonic
        with patch("coding_orchestrator.job_worker.time.monotonic", side_effect=lambda: clock() + 6):
            self.assertEqual(self.finish(worker).state, "timed_out")

    def test_isolates_home_state_environment_stdio_and_process_group(self):
        parent_environment = {"OPENAI_API_KEY": "secret", "HTTP_PROXY": "secret",
                              "AWS_PROFILE": "secret", "ARBITRARY_CREDENTIAL": "secret"}
        worker = self.worker(isolated_runner)
        with patch.dict(os.environ, parent_environment):
            worker.start()
            outcome = self.finish(worker)
            self.assertEqual(os.environ["OPENAI_API_KEY"], "secret")
        self.assertEqual(outcome.state, "completed")
        result = outcome.result
        for name in parent_environment:
            self.assertNotIn(name, result["environment"])
        self.assertEqual(result["environment"]["HOME"], result["cwd"])
        self.assertEqual(result["environment"]["OH_PERSISTENCE_DIR"],
                         str(Path(result["cwd"]) / "openhands"))
        self.assertEqual(result["home_private"], 0o700)
        self.assertEqual(result["stdin"], "")
        self.assertFalse(result["sdk_loaded"])
        self.assertEqual(result["environment"]["LITELLM_MODE"], "PRODUCTION")
        self.assertEqual(result["environment"]["PYTHON_DOTENV_DISABLED"], "1")
        self.assertEqual(result["pid"], result["group"])
        self.assertEqual(result["pid"], result["session"])
        worker.close()
        self.assertFalse(Path(result["cwd"]).exists())
        worker.close()

    def test_close_stops_and_reaps_owned_child(self):
        progress = []
        worker = self.worker(blocked_runner, on_progress=progress.append)
        worker.start()
        self.wait_progress(worker, progress)
        worker.close()
        self.assertEqual(worker.poll().state, "cancelled")
        worker.close()
        with self.assertRaises(RuntimeError):
            worker.start()

    def test_completed_child_is_not_reclassified_by_late_poll(self):
        worker = self.worker(count_requests, "1", timeout_seconds=5)
        worker.start()
        worker._process.join(timeout=10)
        self.assertFalse(worker._process.is_alive())
        # Simulate delayed observation after confirmed completion, without
        # assuming interpreter startup finishes within a fraction of a second.
        with patch("coding_orchestrator.job_worker.time.monotonic", return_value=worker._deadline + 1):
            self.assertEqual(worker.poll().state, "completed")

    def test_unpicklable_runner_has_fixed_start_failure_and_can_close(self):
        worker = self.worker(lambda context, control: {})
        worker.start()
        self.assertEqual((worker.poll().state, worker.poll().error_code),
                         ("failed", "worker_start_failed"))
        worker.close()
        self.assertEqual(worker.request_count, 0)

    def test_short_startup_deadline_prevents_provider_dispatch(self):
        worker = self.worker(count_requests, "1", timeout_seconds=0.0001)
        worker.start()
        outcome = self.finish(worker)
        self.assertEqual((outcome.state, outcome.request_count), ("timed_out", 0))

    def test_progress_callback_failure_stops_child_with_fixed_error(self):
        def callback(value):
            raise RuntimeError("private callback failure")
        worker = self.worker(blocked_runner, on_progress=callback)
        worker.start()
        outcome = self.finish(worker)
        self.assertEqual((outcome.state, outcome.error_code), ("failed", "worker_failed"))

    def assert_descendant_stopped(self, pid):
        # A killed adopted child can remain a zombie until the host init reaps it.
        # Zombies have stopped executing and cannot make provider requests.
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                state = Path(f"/proc/{pid}/stat").read_text().split(") ", 1)[1][0]
            except FileNotFoundError:
                return
            if state == "Z":
                return
            time.sleep(0.005)
        self.fail("Owned descendant survived process-group cleanup")

    def test_normal_completion_stops_remaining_same_session_descendants(self):
        progress = []
        worker = self.worker(descendant_runner, "exit", on_progress=progress.append)
        worker.start()
        outcome = self.finish(worker)
        self.assertEqual(outcome.state, "completed")
        self.assert_descendant_stopped(progress[0]["descendant"])
        self.assertFalse(worker._process.owns_pid)

    def test_cancel_kills_descendant_when_leader_exits_on_sigterm(self):
        progress = []
        worker = self.worker(descendant_runner, "wait", on_progress=progress.append)
        worker.start()
        self.wait_progress(worker, progress)
        worker.cancel()
        outcome = self.finish(worker)
        self.assertEqual(outcome.state, "cancelled")
        self.assertEqual(worker._process.exitcode, -signal.SIGTERM)
        self.assert_descendant_stopped(progress[0]["descendant"])

    def test_unicode_payloads_use_utf8_byte_limit(self):
        progress = []
        worker = self.worker(unicode_runner, on_progress=progress.append)
        worker.start()
        outcome = self.finish(worker)
        self.assertEqual(outcome.state, "completed")
        self.assertEqual(progress, [{"text": "é" * 40000}])
        self.assertEqual(outcome.result, {"text": "漢" * 40000})

    def test_child_deadline_fires_without_parent_polling(self):
        worker = self.worker(blocked_runner, timeout_seconds=0.5)
        worker.start()
        worker._process.join(timeout=3)
        self.assertFalse(worker._process.is_alive())
        outcome = self.finish(worker)
        self.assertEqual((outcome.state, outcome.error_code),
                         ("timed_out", "deadline_exceeded"))
        self.assertEqual(worker._process.exitcode, -signal.SIGALRM)

    def test_rejects_git_temp_base_before_allocating_worker_state(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / ".git").mkdir()
            with patch.object(tempfile, "tempdir", directory), \
                    patch.object(tempfile, "TemporaryFile") as allocate:
                with self.assertRaisesRegex(ValueError, "Git repository"):
                    self.worker()
                allocate.assert_not_called()

    def test_temp_root_is_revalidated_before_worker_start(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(tempfile, "tempdir", directory):
                worker = self.worker()
            (Path(directory) / ".git").mkdir()
            worker.start()
            self.assertEqual(worker.poll().error_code, "worker_start_failed")
            self.assertIsNone(worker._process)
            worker.close()

    def test_trusted_runner_import_does_not_write_bytecode_to_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "worker_import_probe.py"
            source.write_text('def run(context, control):\n    return {"ok": True}\n')
            spec = importlib.util.spec_from_file_location("worker_import_probe", source)
            module = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, {"worker_import_probe": module}), \
                    patch.object(sys, "path", [str(root), *sys.path]), \
                    patch.object(sys, "dont_write_bytecode", True):
                spec.loader.exec_module(module)
                self.assertFalse(list(root.rglob("*.pyc")))
                worker = self.worker(module.run)
                worker.start()
                outcome = self.finish(worker)
                self.assertEqual(outcome.state, "completed")
                self.assertEqual(outcome.result, {"ok": True})
                self.assertFalse(list(root.rglob("*.pyc")))

    def test_validation_and_immutable_context(self):
        for value in (True, False, 0, 11, 1.0, "1"):
            with self.assertRaises(ValueError):
                self.worker(max_requests=value)
        for value in (True, False, 0, -1, 300.1, float("nan"), float("inf"), "1"):
            with self.assertRaises(ValueError):
                self.worker(timeout_seconds=value)
        context = RunContext("job", "prompt", "repo", "test")
        with self.assertRaises(FrozenInstanceError):
            context.prompt = "changed"


if __name__ == "__main__":
    unittest.main()
