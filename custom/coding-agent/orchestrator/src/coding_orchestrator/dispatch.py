"""Inactive preview-job protocol for a trusted, authenticated transport.

No listener, authentication, profile loading or activation is provided here.
The transport must reject duplicate JSON keys before constructing a plain dict;
duplicate wire keys cannot be recovered from an already decoded Python dict.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

from .job_store import IdempotencyConflict, JobNotFound, StoreBusy
from .jobs import JobError, JobRequest, JobService, Principal, RunScope


MAX_INPUT_BYTES = 40960
MAX_OUTPUT_BYTES = 262144
_UNSAFE_KEYS = frozenset({"__proto__", "prototype", "constructor"})
_SERVICE_ERRORS = frozenset({
    "authenticated_principal_required", "preview_jobs_disabled", "scope_not_authorized",
    "job_not_found", "job_busy", "idempotency_conflict", "stale_generation",
    "worker_start_failed", "admission_deadline_exceeded", "job_service_unavailable",
})


def _json_value(value, depth=0):
    if depth > 16:
        raise ValueError
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str or key in _UNSAFE_KEYS:
                raise ValueError
            _json_value(child, depth + 1)
    elif type(value) is list:
        for child in value:
            _json_value(child, depth + 1)
    elif type(value) is float:
        if not math.isfinite(value):
            raise ValueError
    elif value is not None and type(value) not in (str, bool, int):
        raise ValueError


def _bounded_json(value, limit):
    # Iterate to stop before assembling an oversized document, and return a
    # detached JSON snapshot rather than the caller's mutable dictionaries.
    chunks, size = [], 0
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    for chunk in encoder.iterencode(value):
        size += len(chunk.encode("utf-8"))
        if size > limit:
            raise ValueError
        chunks.append(chunk)
    return json.loads("".join(chunks))


def _fields(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError


def _identifier(value):
    return type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}", value)


def _generation(record):
    generation_id, epoch = record["generation_id"], record["generation_epoch"]
    if not _identifier(generation_id) or type(epoch) is not int or not 0 <= epoch <= 9007199254740991:
        raise ValueError
    return generation_id, epoch


def _request(message):
    _json_value(message)
    message = _bounded_json(message, MAX_INPUT_BYTES)
    _fields(message, ("version", "operation", "request"))
    if type(message["version"]) is not int or message["version"] != 1:
        raise ValueError
    operation, request = message["operation"], message["request"]
    if operation == "start":
        _fields(request, ("prompt", "idempotency_key", "scope", "max_requests", "timeout_seconds"))
        _fields(request["scope"], ("repository_alias", "task_mode"))
        key = request["idempotency_key"]
        generation_id = "preview:" + hashlib.sha256(key.encode("utf-8")).hexdigest()
        return operation, JobRequest(
            prompt=request["prompt"], idempotency_key=key,
            generation_id=generation_id, generation_epoch=0,
            scope=RunScope(**request["scope"]), max_requests=request["max_requests"],
            timeout_seconds=request["timeout_seconds"],
        )
    if operation in ("get", "cancel"):
        _fields(request, ("job_id",))
        job_id = request["job_id"]
        if not _identifier(job_id):
            raise ValueError
        return operation, job_id
    raise ValueError


def _failure(code):
    return {"version": 1, "ok": False, "error": code}


def dispatch_job(service: JobService, principal: Principal, message: dict) -> dict:
    """Dispatch one bounded message; identity is never taken from the message.

    An unavailable response does not establish whether execution started or
    stopped. The caller must retain its idempotency key and immutable job ID.
    """
    if not isinstance(principal, Principal):
        return _failure("authenticated_principal_required")
    try:
        operation, request = _request(message)
    except Exception:
        return _failure("invalid_job_message")
    try:
        if operation == "start":
            job = service.start_run(principal, request)
        elif operation == "get":
            job = service.get_run(principal, request)
        else:
            owned = service.get_run(principal, request)
            generation_id, epoch = _generation(owned)
            job = service.cancel_run(principal, request,
                generation_id=generation_id, generation_epoch=epoch)
        if type(job) is not dict or not _identifier(job["job_id"]):
            raise ValueError
        _generation(job)
        return _bounded_json({"version": 1, "ok": True, "job": job}, MAX_OUTPUT_BYTES)
    except JobNotFound:
        return _failure("job_not_found")
    except StoreBusy:
        return _failure("job_busy")
    except IdempotencyConflict:
        return _failure("idempotency_conflict")
    except JobError as exc:
        code = str(exc)
        return _failure(code if code in _SERVICE_ERRORS else "job_service_unavailable")
    except Exception:
        return _failure("job_service_unavailable")
