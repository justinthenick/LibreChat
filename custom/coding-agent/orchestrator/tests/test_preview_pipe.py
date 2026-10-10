"""Private-pipe framing and fail-closed admission over the real dispatcher."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from contextlib import ExitStack

from coding_orchestrator.job_store import JobStore
from coding_orchestrator.jobs import ExecutionProfile, JobService, Principal
from coding_orchestrator.preview_pipe import PreviewPipe, MAX_INPUT_BYTES
from test_dispatch import ControlledWorker, start_message


def exchange(pipe, principal, payload):
    frame = {"version": 1, "request_id": "a" * 36,
             "principal": {"user_id": principal.user_id, "tenant_id": principal.tenant_id},
             "payload": payload}
    output = io.BytesIO()
    pipe.serve(io.BytesIO(json.dumps(frame).encode() + b"\n"), output)
    return json.loads(output.getvalue())["result"]


class PreviewPipeTests(unittest.TestCase):
    def test_python_rechecks_repository_and_owner_for_get_and_cancel(self):
        with tempfile.TemporaryDirectory() as root, JobStore(Path(root) / "jobs.sqlite") as store, ExitStack() as cleanup:
            owner, other = Principal("owner", "tenant"), Principal("other", "tenant")
            workers = []
            def factory(*args, **kwargs):
                worker = ControlledWorker(*args, **kwargs)
                workers.append(worker)
                return worker
            profile = ExecutionProfile("pipe-test", frozenset({"fixture"}), lambda *_: None,
                                       lambda *_: True, lambda *_: None)
            service = JobService(store, profile=profile, enabled=True, worker_factory=factory)
            cleanup.callback(service.close)
            allowed = PreviewPipe(service, grants={owner: {"fixture"}}, admit_start=lambda *_: True, enabled=True)
            started = exchange(allowed, owner, start_message())
            denied = PreviewPipe(service, grants={owner: {"foreign"}, other: {"fixture"}},
                                 admit_start=lambda *_: self.fail("status invoked start policy"), enabled=True)
            for operation in ("get", "cancel"):
                payload = {"version": 1, "operation": operation, "request": {"job_id": started["job"]["job_id"]}}
                self.assertEqual(exchange(denied, owner, payload)["error"], "scope_not_authorized")
                self.assertEqual(exchange(denied, other, payload)["error"], "job_not_found")
            self.assertFalse(workers[0].cancelled)

    def test_short_reply_write_closes_before_the_next_request(self):
        class ShortWriter:
            def write(self, response):
                return len(response) - 1

            def flush(self):
                raise AssertionError("short reply was flushed")

        with tempfile.TemporaryDirectory() as root, JobStore(Path(root) / "jobs.sqlite") as store, ExitStack() as cleanup:
            service = JobService(store)
            cleanup.callback(service.close)
            pipe = PreviewPipe(service, grants={}, admit_start=lambda *_: True)
            frame = {"version": 1, "request_id": "a" * 36,
                     "principal": {"user_id": "owner", "tenant_id": "tenant"}, "payload": {}}
            line = json.dumps(frame).encode() + b"\n"
            incoming = io.BytesIO(line * 2)
            with self.assertRaisesRegex(ValueError, "incomplete pipe reply"):
                pipe.serve(incoming, ShortWriter())
            self.assertEqual(incoming.tell(), len(line))

    def test_disabled_pipe_never_calls_admission_or_enables_service(self):
        with tempfile.TemporaryDirectory() as root, JobStore(Path(root) / "jobs.sqlite") as store, ExitStack() as cleanup:
            service = JobService(store)
            cleanup.callback(service.close)
            owner = Principal("owner", "tenant")
            pipe = PreviewPipe(service, grants={owner: {"fixture"}},
                               admit_start=lambda *_: self.fail("unexpected admission"))
            frame = {"version": 1, "request_id": "a" * 36,
                     "principal": {"user_id": "owner", "tenant_id": "tenant"}, "payload": {}}
            output = io.BytesIO()
            pipe.serve(io.BytesIO(json.dumps(frame).encode() + b"\n"), output)
            self.assertEqual(json.loads(output.getvalue())["result"]["error"], "preview_jobs_disabled")
            self.assertFalse(service.enabled)

    def test_invalid_wire_frames_close_without_dispatch(self):
        with tempfile.TemporaryDirectory() as root, JobStore(Path(root) / "jobs.sqlite") as store, ExitStack() as cleanup:
            service = JobService(store)
            cleanup.callback(service.close)
            pipe = PreviewPipe(service, grants={}, admit_start=lambda *_: self.fail("unexpected admission"))
            for value in (b'{"version":1,"version":1}\n', b'\xff\n', b'{}',
                          b' ' * MAX_INPUT_BYTES + b'\n', b'{"__proto__":{}}\n',
                          b'{"version":NaN}\n', b'{"command":"shutdown"}\n'):
                with self.subTest(value=value[:50]), self.assertRaises((ValueError, UnicodeError)):
                    pipe.serve(io.BytesIO(value), io.BytesIO())

    def test_allowlist_snapshot_and_unknown_principal(self):
        with tempfile.TemporaryDirectory() as root, JobStore(Path(root) / "jobs.sqlite") as store, ExitStack() as cleanup:
            service = JobService(store)
            cleanup.callback(service.close)
            owner = Principal("owner", "tenant")
            aliases = {"fixture"}
            grants = {owner: aliases}
            pipe = PreviewPipe(service, grants=grants, admit_start=lambda *_: True, enabled=True)
            aliases.add("foreign")
            grants[Principal("foreign")] = {"fixture"}
            self.assertNotIn("foreign", pipe.grants[owner])
            self.assertEqual(exchange(pipe, Principal("foreign"), {})["error"], "authenticated_principal_required")
            payload = {"version": 1, "operation": "start", "request": {"scope": {"repository_alias": "foreign"}}}
            self.assertEqual(exchange(pipe, owner, payload)["error"], "scope_not_authorized")
