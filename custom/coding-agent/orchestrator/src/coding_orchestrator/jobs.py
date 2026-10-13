"""Disabled-by-default, transport-neutral execution jobs.

This module is not an authentication server. A trusted adapter supplies a
principal after authenticating its caller; callers cannot select a runner,
credential, endpoint or filesystem path. No production execution profile is
registered here. LibreChat remains responsible for chat streaming/persistence.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import threading
import time
from dataclasses import dataclass
from typing import Callable

from .job_store import ExecutionIdentity, JobStore, StopEvidence
from .job_worker import ProcessWorker, RunContext


class JobError(RuntimeError):
    """A fixed, non-secret-bearing job boundary failure."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise JobError(code)


def _identifier(value: str, *, empty: bool = False) -> bool:
    return isinstance(value, str) and ((empty and value == "") or bool(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}", value)))


@dataclass(frozen=True)
class Principal:
    """Identity established by a trusted authentication adapter, not request JSON."""

    user_id: str
    tenant_id: str = ""

    def __post_init__(self) -> None:
        _require(_identifier(self.user_id) and _identifier(self.tenant_id, empty=True),
                 "invalid_principal")


@dataclass(frozen=True)
class RunScope:
    repository_alias: str
    task_mode: str = "read_only"

    def __post_init__(self) -> None:
        _require(_identifier(self.repository_alias) and self.task_mode in {"read_only", "modification"},
                 "invalid_run_scope")


@dataclass(frozen=True)
class JobRequest:
    prompt: str
    idempotency_key: str
    generation_id: str
    generation_epoch: int
    scope: RunScope
    max_requests: int = 10
    timeout_seconds: float = 300

    def __post_init__(self) -> None:
        _require(isinstance(self.prompt, str) and bool(self.prompt.strip())
                 and len(self.prompt.encode("utf-8")) <= 32768, "invalid_prompt")
        _require(_identifier(self.idempotency_key) and _identifier(self.generation_id),
                 "invalid_request_identity")
        _require(type(self.generation_epoch) is int and self.generation_epoch >= 0,
                 "invalid_generation_epoch")
        _require(isinstance(self.scope, RunScope), "invalid_run_scope")
        _require(type(self.max_requests) is int and 1 <= self.max_requests <= 10,
                 "invalid_request_limit")
        _require(type(self.timeout_seconds) in {int, float}
                 and math.isfinite(self.timeout_seconds) and 0 < self.timeout_seconds <= 300,
                 "invalid_time_limit")


@dataclass(frozen=True)
class ExecutionProfile:
    """Trusted server configuration; never deserialize this from a client.

    runner must use WorkerControl.before_provider_request immediately before
    every physical provider request, disable retry/fallback, enforce the selected
    repository/task scope and emit only bounded evidence. authorize and
    confirm_stopped are trusted, nonblocking policy/lease checks. The latter
    must return identity-bound evidence that external execution is quiescent
    and fenced against delayed dispatch, not merely that a local process exited.
    No production profile is registered and no ambient credentials are discovered.
    """

    profile_id: str
    repository_aliases: frozenset[str]
    runner: Callable
    authorize: Callable[[Principal, RunScope], bool]
    confirm_stopped: Callable[[ExecutionIdentity], StopEvidence | None]
    model: str = "gpt-5.6-sol"

    def __post_init__(self) -> None:
        _require(_identifier(self.profile_id) and isinstance(self.repository_aliases, frozenset)
                 and bool(self.repository_aliases)
                 and all(_identifier(alias) for alias in self.repository_aliases), "invalid_profile")
        _require(all(callable(value) for value in (self.runner, self.authorize, self.confirm_stopped)),
                 "profile_capability_missing")
        _require(self.model == "gpt-5.6-sol", "unsupported_preview_model")


_TERMINAL = {"completed", "failed", "cancelled", "timed_out", "interrupted"}
_EVIDENCE_KEYS = {"repository_alias", "task", "checks", "final_diff", "final_status",
                  "observed_checks_status", "evidence_complete", "action_count", "pending_count", "errors"}


def _result(value: object, scope: RunScope, *, partial: bool = False) -> dict:
    _require(isinstance(value, dict) and set(value) <= {"execution_status", "final_response", "evidence"},
             "invalid_profile_result")
    encoded = json.dumps(value, allow_nan=False, ensure_ascii=False, separators=(",", ":"))
    _require(len(encoded.encode("utf-8")) <= 131072, "profile_result_limit")
    result = json.loads(encoded)
    if "final_response" in result:
        _require(isinstance(result["final_response"], str)
                 and len(result["final_response"].encode()) <= 8192, "final_response_limit")
    if "execution_status" in result:
        _require(result["execution_status"] in {"finished", "failed", "paused", "interrupted"},
                 "invalid_execution_status")
    evidence = result.get("evidence")
    _require(isinstance(evidence, dict) and set(evidence) == _EVIDENCE_KEYS
             and evidence.get("repository_alias") == scope.repository_alias,
             "invalid_evidence_scope")
    _require(evidence.get("observed_checks_status") in {"not_run", "passed", "failed", "incomplete"}
             and type(evidence.get("evidence_complete")) is bool, "invalid_evidence_status")
    if not partial:
        _require(result.get("execution_status") == "finished", "profile_did_not_finish")
    return result


class JobService:
    """One bounded execution at a time, with no implicit activation or replay."""

    def __init__(self, store: JobStore, *, profile: ExecutionProfile | None = None,
                 enabled: bool = False, worker_factory=ProcessWorker, clock=time.time) -> None:
        _require(type(enabled) is bool, "invalid_enabled_setting")
        self.store, self.profile, self.enabled = store, profile, enabled
        self._worker_factory, self._clock = worker_factory, clock
        self._lock = threading.RLock()
        self._active = None
        self._closed = False

    @staticmethod
    def _owner(principal: Principal) -> tuple[str, str]:
        _require(isinstance(principal, Principal), "authenticated_principal_required")
        return principal.user_id, principal.tenant_id

    @staticmethod
    def _public(record: dict) -> dict:
        # Deliberately exclude identity/fingerprint/private store internals.
        keys = ("job_id", "generation_id", "generation_epoch", "state", "created_at", "updated_at",
                "deadline_at", "metadata", "result", "error_code", "request_count")
        return {key: record[key] for key in keys}

    def start_run(self, principal: Principal, request: JobRequest) -> dict:
        user, tenant = self._owner(principal)
        _require(isinstance(request, JobRequest), "invalid_job_request")
        with self._lock:
            _require(not self._closed and self.enabled and isinstance(self.profile, ExecutionProfile),
                     "preview_jobs_disabled")
            profile = self.profile
            _require(request.scope.repository_alias in profile.repository_aliases, "scope_not_authorized")
            try:
                authorized = profile.authorize(principal, request.scope) is True
            except Exception:
                authorized = False
            _require(authorized, "scope_not_authorized")
            identity = {"prompt": request.prompt, "scope": request.scope.__dict__,
                        "generation_id": request.generation_id, "generation_epoch": request.generation_epoch,
                        "max_requests": request.max_requests, "timeout_seconds": request.timeout_seconds,
                        "profile_id": profile.profile_id, "model": profile.model}
            fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
            record, created = self.store.admit(user_id=user, tenant_id=tenant,
                idempotency_key=request.idempotency_key, fingerprint=fingerprint,
                generation_id=request.generation_id, generation_epoch=request.generation_epoch,
                deadline_at=self._clock() + request.timeout_seconds,
                metadata={"profile_id": profile.profile_id, "repository_alias": request.scope.repository_alias,
                          "task_mode": request.scope.task_mode, "model": profile.model,
                          "max_requests": request.max_requests, "timeout_seconds": request.timeout_seconds})
            if not created:
                return self._public(record)
            identity = self.store.execution_identity(user, tenant, record["job_id"])
            context = RunContext(record["job_id"], request.prompt, request.scope.repository_alias,
                                 request.scope.task_mode, identity.execution_id)
            def progress(value):
                result = _result(value, request.scope, partial=True)
                self.store.update_progress(user, tenant, record["job_id"], result=result)
            worker = None
            dispatch_possible = False
            try:
                remaining = record["deadline_at"] - self._clock()
                _require(remaining > 0, "admission_deadline_exceeded")
                # A factory can dispatch before returning (or raising). Only
                # control flow before this point proves no execution existed.
                dispatch_possible = True
                worker = self._worker_factory(profile.runner, context, max_requests=request.max_requests,
                    timeout_seconds=min(request.timeout_seconds, remaining), on_progress=progress)
                active = (principal, request, context, worker)
                worker.start()
                _require(self.store.transition(user, tenant, record["job_id"], {"queued"}, "running"),
                         "job_start_conflict")
                thread = threading.Thread(target=self._monitor, args=(active, profile), daemon=True,
                                          name="openhands-preview-job")
                self._active = (*active, thread)
                thread.start()
            except BaseException:
                if worker is not None:
                    worker.close()
                self.store.transition(user, tenant, record["job_id"], {"queued", "running"}, "failed",
                                      error_code="worker_start_failed",
                                      stop_evidence=StopEvidence(identity, True) if not dispatch_possible else None)
                self._active = None
                raise JobError("worker_start_failed") from None
            return self.get_run(principal, record["job_id"])

    def get_run(self, principal: Principal, job_id: str) -> dict:
        user, tenant = self._owner(principal)
        return self._public(self.store.get(user, tenant, job_id))

    @staticmethod
    def _stop_evidence(profile, identity):
        try:
            evidence = profile.confirm_stopped(identity)
            if type(evidence) is StopEvidence and evidence.confirms(identity):
                return evidence
        except Exception:
            pass
        return None

    def reconcile_run(self, principal: Principal, job_id: str) -> bool:
        """Trusted embedding hook; no dispatcher route or caller-supplied proof.

        Reconciliation never replays work or rewrites terminal outcomes. A
        missing, stale or unavailable observation leaves admission quarantined.
        """
        user, tenant = self._owner(principal)
        with self._lock:
            _require(not self._closed and self.enabled and isinstance(self.profile, ExecutionProfile),
                     "preview_jobs_disabled")
            record = self.store.get(user, tenant, job_id)
            identity = self.store.execution_identity(user, tenant, job_id)
            profile = self.profile
            _require(identity.profile_id == profile.profile_id
                     and identity.repository_alias in profile.repository_aliases, "scope_not_authorized")
            scope = RunScope(identity.repository_alias, identity.task_mode)
            try:
                authorized = profile.authorize(principal, scope) is True
            except Exception:
                authorized = False
            _require(authorized, "scope_not_authorized")
            if (record["state"] not in _TERMINAL
                    or (self._active and self._active[2].job_id == job_id)):
                return False
        evidence = self._stop_evidence(profile, identity)
        with self._lock:
            _require(not self._closed and self.enabled and self.profile is profile,
                     "preview_jobs_disabled")
            if self._active and self._active[2].job_id == job_id:
                return False
            return self.store.resolve_execution(user, tenant, job_id, evidence)

    def cancel_run(self, principal: Principal, job_id: str, *, generation_id: str,
                   generation_epoch: int) -> dict:
        user, tenant = self._owner(principal)
        with self._lock:
            record = self.store.get(user, tenant, job_id)
            _require(type(generation_epoch) is int and record["generation_id"] == generation_id
                     and record["generation_epoch"] == generation_epoch, "stale_generation")
            if record["state"] in _TERMINAL:
                return self._public(record)
            if record["state"] == "queued":
                self.store.transition(user, tenant, job_id, {"queued"}, "cancelled", error_code="cancel_requested")
            else:
                self.store.transition(user, tenant, job_id, {"running"}, "cancelling", error_code="cancel_requested")
                if self._active and self._active[2].job_id == job_id:
                    self._active[3].cancel()
            return self.get_run(principal, job_id)

    def _monitor(self, active, profile) -> None:
        principal, request, context, worker = active
        user, tenant = self._owner(principal)
        try:
            last_count = -1
            while True:
                outcome = worker.poll()
                if worker.request_count != last_count:
                    self.store.update_progress(user, tenant, context.job_id, request_count=worker.request_count)
                    last_count = worker.request_count
                if outcome is not None:
                    break
                time.sleep(.02)
            record = self.store.get(user, tenant, context.job_id)
            result = record["result"]
            state, code = outcome.state, outcome.error_code
            if state == "completed" and outcome.result is None:
                state, code = "failed", "invalid_profile_result"
            if outcome.result is not None:
                try:
                    result = _result(outcome.result, request.scope, partial=state != "completed")
                except (JobError, TypeError, ValueError):
                    state, code = "failed", "invalid_profile_result"
            identity = self.store.execution_identity(user, tenant, context.job_id)
            evidence = self._stop_evidence(profile, identity)
            # Cancellation and terminal publication share one service lock. A
            # cancel accepted during the lease check must win over completion.
            with self._lock:
                current = self.store.get(user, tenant, context.job_id)
                if current["state"] == "cancelling":
                    state, code = "cancelled", "cancel_requested"
                if evidence is None:
                    state, code = "interrupted", "execution_stop_unconfirmed"
                elif state == "cancelled" and current["state"] == "running":
                    _require(self.store.transition(user, tenant, context.job_id, {"running"}, "cancelling",
                        error_code=code), "cancellation_state_conflict")
                _require(self.store.transition(user, tenant, context.job_id, {"running", "cancelling"}, state,
                    result=result, error_code=code, request_count=outcome.request_count,
                    stop_evidence=evidence), "terminal_state_conflict")
        except BaseException:
            self.store.transition(user, tenant, context.job_id, {"running", "cancelling"}, "interrupted",
                                  error_code="job_monitor_interrupted")
        finally:
            worker.close()
            with self._lock:
                if self._active and self._active[2].job_id == context.job_id:
                    self._active = None

    def close(self) -> None:
        with self._lock:
            self._closed = True
            active = self._active
            if active:
                principal, request, context, worker, thread = active
                self.cancel_run(principal, context.job_id, generation_id=request.generation_id,
                                generation_epoch=request.generation_epoch)
        if active:
            thread.join(timeout=5)
            if thread.is_alive():
                worker.close()
                thread.join(timeout=5)
            _require(not thread.is_alive(), "job_shutdown_unconfirmed")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()
