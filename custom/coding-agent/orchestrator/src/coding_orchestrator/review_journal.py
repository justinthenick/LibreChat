"""Private review-state protocol over inherited pipes; never executes a review."""
from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
from uuid import UUID

from job_store import JobStore, JobNotFound, StoreBusy, StoreError, IdempotencyConflict, StopEvidence

MAX_BYTES = 132096
MAX_RECORDS = 1024
RETENTION = 600


def canonical_id(value):
    if not isinstance(value, str) or len(value) != 36:
        raise ValueError("Invalid review ID")
    canonical = str(UUID(value))
    if value.lower() != canonical:
        raise ValueError("Invalid review ID")
    return canonical


def validate_stored_identity(value):
    # Never rename legacy keys or infer equivalence for durable stop evidence.
    if canonical_id(value) != value:
        raise ValueError("Noncanonical stored review identity")


def public_record(row):
    payload = row["request"]
    record = {"id": row["job_id"], "state": row["state"],
              "expiresAt": (row["updated_at"] + RETENTION) * 1000,
              "cancelRequested": bool(row["cancel_requested"])}
    if payload is not None:
        record.update(request=payload["request"], model=payload["model"])
    if row["result"] is not None:
        record["result"] = row["result"]
    return record


def dispatch(store, command):
    if set(command) - {"sequence", "operation", "id", "principal", "payload", "result"}:
        raise ValueError("Invalid command")
    operation = command["operation"]
    principal = command["principal"]
    if set(principal) - {"userId", "tenantId"}:
        raise ValueError("Invalid principal")
    user, tenant, run_id = principal["userId"], principal.get("tenantId", ""), canonical_id(command["id"])
    store.discard_terminal_results(max(0, time.time() - RETENTION))
    if operation == "get":
        try:
            return {"record": public_record(store.get(user, tenant, run_id))}
        except JobNotFound:
            return {"record": None}
    if operation == "cancel":
        store.cancel_external(user, tenant, run_id, max_records=MAX_RECORDS)
        return {}
    if operation == "admit":
        payload = command["payload"]
        if set(payload) != {"request", "model"}:
            raise ValueError("Invalid payload")
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                                ensure_ascii=False).encode()).hexdigest()
        row, created = store.admit(user_id=user, tenant_id=tenant, idempotency_key=run_id,
            fingerprint=fingerprint, generation_id=run_id, generation_epoch=0,
            deadline_at=time.time()+165, metadata={"task_mode": "review", "model": payload["model"],
            "repository_alias": payload["request"]["repository"]},
            job_id=run_id, request=payload, max_records=MAX_RECORDS, max_results=64)
        if created:
            if not store.transition(user, tenant, run_id, {"queued"}, "running"):
                raise StoreError("Admission transition failed")
            row = store.get(user, tenant, run_id)
        return {"created": created, "record": public_record(row)}
    if operation == "finish":
        row = store.get(user, tenant, run_id)
        result = command.get("result")
        # Only a validated successful FinishTool outcome, after the TS worker has
        # settled and cleaned its process group, supplies this trusted proof.
        # Failure, cancellation, timeout and restart never infer remote quiescence.
        evidence = None
        state = "interrupted"
        if result is not None:
            payload = row["request"]
            if payload is None or any(result.get(k) != v for k, v in payload["request"].items()) or result.get("model") != payload["model"]:
                raise ValueError("Mismatched result")
            state = "cancelled" if row["state"] == "cancelling" else "completed"
            evidence = StopEvidence(store.execution_identity(user, tenant, run_id), True)
        if not store.transition(user, tenant, run_id, {"running", "cancelling"}, state,
                                result=result if state == "completed" else None, error_code=None if result else "execution_stop_unconfirmed",
                                stop_evidence=evidence):
            raise StoreError("Terminal state conflict")
        return {"record": public_record(store.get(user, tenant, run_id))}
    raise ValueError("Invalid operation")


def emit(value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if len(raw.encode()) > MAX_BYTES:
        raise ValueError("Response too large")
    print(raw, flush=True)


def main():
    if len(sys.argv) != 2:
        return 1
    try:
        with JobStore(sys.argv[1], validate_identity=validate_stored_identity) as store:
            stopped = threading.Event()
            def expire():
                while not stopped.wait(30):
                    try:
                        store.discard_terminal_results(max(0, time.time()-RETENTION))
                    except StoreError:
                        # A failed maintenance commit must fence the owning TS
                        # generation just like a failed command.
                        import os
                        os._exit(1)
            thread = threading.Thread(target=expire, daemon=True)
            thread.start()
            try:
                store.discard_terminal_results(max(0, time.time()-RETENTION))
                emit({"ready": True})
                while True:
                    line = sys.stdin.buffer.readline(MAX_BYTES+1)
                    if not line:
                        return 0
                    if len(line) > MAX_BYTES or not line.endswith(b"\n"):
                        return 1
                    command = json.loads(line)
                    sequence = command["sequence"]
                    if type(sequence) is not int or sequence < 1:
                        return 1
                    try:
                        value = dispatch(store, command)
                        emit({"sequence": sequence, "ok": True, **value})
                    except StoreBusy:
                        emit({"sequence": sequence, "ok": False, "code": "busy"})
                    except JobNotFound:
                        emit({"sequence": sequence, "ok": False, "code": "forbidden"})
                    except (IdempotencyConflict, ValueError, KeyError, TypeError):
                        emit({"sequence": sequence, "ok": False, "code": "invalid_request"})
            finally:
                stopped.set()
                thread.join(timeout=1)
    except (StoreError, ValueError, KeyError, TypeError, OSError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
