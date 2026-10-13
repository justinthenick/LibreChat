"""Dormant bounded stop-confirmation hook; no endpoint or profile registration.

The injected trusted control must idempotently seal/stop the exact execution and
return an authenticated authority/status envelope. This is not a transport or
authentication implementation. A timeout never cancels remote work or proves it
stopped. One unresolved callback occupies the adapter until explicitly consumed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
import os
import re
import threading
from typing import Callable

from .job_store import ExecutionIdentity, StopEvidence


def _fields(value, keys):
    return (type(value) is dict and len(value) == len(keys)
            and all(type(key) is str for key in value) and value.keys() == keys)


def _identifier(value):
    return type(value) is str and len(value) <= 128 and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]*", value)


def _identity_matches(value, expected):
    return _fields(value, expected.keys()) and all(
        type(value[key]) is type(item) and value[key] == item for key, item in expected.items())


def _confirmed(response, identity, authority):
    if (not _fields(response, {"authority_id", "status"})
            or type(response["authority_id"]) is not str or response["authority_id"] != authority):
        return False
    status = response["status"]
    if not _fields(status, {"identity", "state", "sealed", "operations"}):
        return False
    expected = asdict(identity)
    if (type(response["authority_id"]) is not str or type(status["state"]) is not str
            or status["state"] != "stopped" or status["sealed"] is not True
            or not _identity_matches(status["identity"], expected)):
        return False
    operations = status["operations"]
    if type(operations) not in (tuple, list) or len(operations) > 64:
        return False
    operation_ids, attempts = set(), set()
    for operation in operations:
        if not _fields(operation, {"state", "claim"}) or type(operation["state"]) is not str or operation["state"] != "stopped":
            return False
        claim = operation["claim"]
        if not _fields(claim, {"identity", "operation_id", "request_sha256", "attempt_id", "authority_id"}):
            return False
        if (not _identity_matches(claim["identity"], expected)
                or type(claim["authority_id"]) is not str or claim["authority_id"] != authority
                or not _identifier(claim["operation_id"]) or not _identifier(claim["attempt_id"])
                or type(claim["request_sha256"]) is not str
                or len(claim["request_sha256"]) != 64
                or not re.fullmatch(r"[0-9a-f]{64}", claim["request_sha256"])):
            return False
        if claim["operation_id"] in operation_ids or claim["attempt_id"] in attempts:
            return False
        operation_ids.add(claim["operation_id"])
        attempts.add(claim["attempt_id"])
    return True


@dataclass
class _Pending:
    identity: ExecutionIdentity
    ready: threading.Event = field(default_factory=threading.Event)
    response: object = None


class ExecutorStopAdapter:
    """Optional ExecutionProfile.confirm_stopped callable for a trusted control.

    control(identity_dict, timeout_seconds=budget) must return
    {authority_id, status}, where status is the exact ExecutionService.stop
    snapshot. Bound the real transport too. A hung callback is not killed: at
    most one daemon callback remains, no new calls are queued, and quarantine
    persists. Late evidence is only consumed by a later explicit matching call.
    """

    def __init__(self, control: Callable, *, authority_id: str, timeout_seconds: float = .5):
        if not callable(control) or not _identifier(authority_id):
            raise ValueError("trusted executor control and authority required")
        if (type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 1
                or not math.isfinite(timeout_seconds)):
            raise ValueError("stop confirmation budget must be positive and at most one second")
        self._control, self._authority, self._budget = control, authority_id, float(timeout_seconds)
        self._lock = threading.Lock()
        self._pending = None
        self._pid = os.getpid()

    def _request(self, pending):
        try:
            pending.response = self._control(asdict(pending.identity), timeout_seconds=self._budget)
        except BaseException:
            # Transport exception strings can contain credentials or endpoints.
            pending.response = None
        finally:
            pending.ready.set()

    def confirm_stopped(self, identity: ExecutionIdentity) -> StopEvidence | None:
        if os.getpid() != self._pid or type(identity) is not ExecutionIdentity:
            return None
        with self._lock:
            pending = self._pending
            if pending is not None and pending.identity != identity:
                return None
            if pending is None:
                pending = _Pending(identity)
                self._pending = pending
                thread = threading.Thread(target=self._request, args=(pending,), daemon=True,
                                          name="executor-stop-confirmation")
                try:
                    thread.start()
                except Exception:
                    self._pending = None
                    return None
        if not pending.ready.wait(self._budget):
            return None
        with self._lock:
            if self._pending is not pending:
                return None
            self._pending = None
        if _confirmed(pending.response, identity, self._authority):
            return StopEvidence(identity, True)
        return None
