"""Dormant private-pipe adapter; no listener, process spawning, credentials or registration.

Only a trusted embedding process may own these pipes. Principal fields are an
assertion by that owner, NOT network authentication. JobService retains all job,
ledger, supervisor and stop-proof semantics. EOF does not cancel or prove stop.
"""
from __future__ import annotations

import json
import re

from .dispatch import dispatch_job
from .jobs import JobError, JobService, Principal, RunScope

MAX_INPUT_BYTES = 49152
MAX_OUTPUT_BYTES = 270336


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result or key in {"__proto__", "prototype", "constructor"}:
            raise ValueError("invalid pipe frame")
        result[key] = value
    return result


def _failure(code):
    return {"version": 1, "ok": False, "error": code}


class PreviewPipe:
    """Single-reader bridge over exclusively owned binary streams.

    grants maps exact Principal values to repository aliases; only read_only
    requests are admitted. admit_start is a trusted bounded text/rate decision.
    Use the same grants for the ExecutionProfile's authorization policy. Supply
    an already composed JobService; this adapter never constructs workers or
    interprets execution attempts or stop evidence.
    """

    def __init__(self, service: JobService, *, grants, admit_start, enabled=False):
        if type(enabled) is not bool or not callable(admit_start):
            raise ValueError("trusted admission required")
        self.service, self.enabled, self.admit_start = service, enabled, admit_start
        self.grants = {}
        for principal, aliases in grants.items():
            if type(principal) is not Principal:
                raise ValueError("trusted principal required")
            repositories = frozenset(aliases)
            for alias in repositories:
                RunScope(alias)
            self.grants[principal] = repositories

    def _dispatch(self, principal, payload):
        if not self.enabled:
            return _failure("preview_jobs_disabled")
        if principal not in self.grants:
            return _failure("authenticated_principal_required")
        if type(payload) is not dict or set(payload) != {"version", "operation", "request"}:
            return _failure("invalid_job_message")
        operation, request = payload["operation"], payload["request"]
        if type(request) is not dict:
            return _failure("invalid_job_message")
        if operation == "start":
            try:
                scope = RunScope(**request["scope"])
            except (KeyError, TypeError, JobError):
                return _failure("invalid_job_message")
        elif operation in {"get", "cancel"}:
            # Ownership comes from the real service before scope is examined.
            previous = dispatch_job(self.service, principal,
                                    {"version": 1, "operation": "get", "request": request})
            if previous.get("ok") is not True:
                return previous
            scope = RunScope(previous["job"]["metadata"]["repository_alias"],
                             previous["job"]["metadata"]["task_mode"])
        else:
            return _failure("invalid_job_message")
        if scope.task_mode != "read_only" or scope.repository_alias not in self.grants[principal]:
            return _failure("scope_not_authorized")
        if operation == "start":
            # The policy receives a detached copy; it cannot change dispatched bytes.
            if self.admit_start(principal, json.loads(json.dumps(request))) is not True:
                return _failure("scope_not_authorized")
        return dispatch_job(self.service, principal, payload)

    def exchange(self, line):
        """One bounded frame, shared by private-pipe and authenticated broker adapters."""
        if len(line) > MAX_INPUT_BYTES or not line.endswith(b"\n"):
            raise ValueError("invalid pipe frame")
        frame = json.loads(line.decode("utf-8"), object_pairs_hook=_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if (type(frame) is not dict or set(frame) != {"version", "request_id", "principal", "payload"}
                or type(frame["version"]) is not int or frame["version"] != 1
                or type(frame["request_id"]) is not str
                or not re.fullmatch(r"[a-f0-9-]{36}", frame["request_id"])):
            raise ValueError("invalid pipe frame")
        identity = frame["principal"]
        if type(identity) is not dict or set(identity) != {"user_id", "tenant_id"}:
            raise ValueError("invalid pipe principal")
        principal = Principal(**identity)
        try:
            result = self._dispatch(principal, frame["payload"])
        except Exception:
            result = _failure("job_service_unavailable")
        response = json.dumps({"version": 1, "request_id": frame["request_id"],
                               "principal": {"user_id": principal.user_id, "tenant_id": principal.tenant_id},
                               "result": result}, ensure_ascii=False, allow_nan=False,
                              separators=(",", ":")).encode("utf-8") + b"\n"
        if len(response) > MAX_OUTPUT_BYTES:
            raise ValueError("pipe reply exceeds bound")
        return response

    def serve(self, reader, writer):
        """Use blocking binary streams; short writes close by raising without job replay."""
        while True:
            line = reader.readline(MAX_INPUT_BYTES + 1)
            if not line:
                return
            response = self.exchange(line)
            written = writer.write(response)
            if type(written) is not int or written != len(response):
                raise ValueError("incomplete pipe reply")
            writer.flush()
