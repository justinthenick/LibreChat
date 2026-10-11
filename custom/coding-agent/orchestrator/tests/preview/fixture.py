"""Private stdin/stdout test bridge; not a deployable transport or auth service.

Only the owning Jest process supplies this closed set of synthetic principals.
The production dispatcher receives that principal separately from request JSON.
Each process has a new private store and a real supervised ProcessWorker.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import sys
import tempfile

from coding_orchestrator.dispatch import dispatch_job
from coding_orchestrator.job_store import JobStore, StopEvidence
from coding_orchestrator.job_worker import ProcessWorker
from coding_orchestrator.jobs import ExecutionProfile, JobService, Principal
from fixture_runner import run


MAX_LINE_BYTES = 49152
MAX_REPLY_BYTES = 262144
PRINCIPALS = frozenset({("owner", "tenant"), ("other", "tenant"),
                        ("owner", "other-tenant"), ("owner", "")})


def plain_object(pairs):
    value = {}
    for key, child in pairs:
        if key in value or key in {"__proto__", "constructor", "prototype"}:
            raise ValueError("Invalid fixture JSON")
        value[key] = child
    return value


def write(value):
    payload = json.dumps(value, ensure_ascii=False, allow_nan=False,
                         separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_REPLY_BYTES:
        raise ValueError("Fixture reply exceeds bound")
    sys.stdout.buffer.write(payload + b"\n")
    sys.stdout.buffer.flush()


def stop(_signum, _frame):
    raise KeyboardInterrupt


def main():
    if sys.argv[1:] not in ([], ["--unconfirmed-stop"]):
        raise ValueError("Invalid fixture option")
    os.umask(0o077)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    confirmed = not sys.argv[1:]
    with tempfile.TemporaryDirectory(prefix="preview-store-") as directory:
        store = JobStore(Path(directory) / "jobs.sqlite")
        workers = []
        principals = []

        class ObservedWorker(ProcessWorker):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.cancel_calls = 0
                workers.append(self)

            def cancel(self):
                self.cancel_calls += 1
                super().cancel()

        profile = ExecutionProfile("http-fixture", frozenset({"fixture"}), run,
                                   lambda _principal, _scope: True,
                                   lambda identity: StopEvidence(identity, confirmed))
        service = JobService(store, profile=profile, enabled=True, worker_factory=ObservedWorker)
        try:
            write({"ready": True})
            while True:
                line = sys.stdin.buffer.readline(MAX_LINE_BYTES + 1)
                if not line:
                    break
                if len(line) > MAX_LINE_BYTES or not line.endswith(b"\n"):
                    raise ValueError("Fixture request exceeds bound")
                try:
                    message = json.loads(line, object_pairs_hook=plain_object,
                                         parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()))
                    if type(message) is not dict:
                        raise ValueError
                    if message == {"command": "shutdown"}:
                        break
                    if message == {"command": "inspect"}:
                        # Test-only observation, never an HTTP endpoint or job reply.
                        write({"worker_starts": len(workers),
                               "cancel_calls": sum(worker.cancel_calls for worker in workers),
                               "principals": principals,
                               "store_mode": store.path.stat().st_mode & 0o777})
                        continue
                    if set(message) != {"command", "principal", "payload"} or message["command"] != "exchange":
                        raise ValueError
                    identity = message["principal"]
                    if type(identity) is not dict or set(identity) != {"user_id", "tenant_id"}:
                        raise ValueError
                    if (identity["user_id"], identity["tenant_id"]) not in PRINCIPALS:
                        raise ValueError
                    principal = Principal(**identity)
                    principals.append(identity)
                    write(dispatch_job(service, principal, message["payload"]))
                except (ValueError, TypeError):
                    write({"version": 1, "ok": False, "error": "invalid_job_message"})
        except KeyboardInterrupt:
            pass
        finally:
            # close() cancels and joins the monitor, which reaps its owned child.
            service.close()
            store.close()


if __name__ == "__main__":
    main()
