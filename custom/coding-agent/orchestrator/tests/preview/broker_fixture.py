"""Loopback-only test host; all certificates are generated in its temporary directory."""
import hashlib
import json
from pathlib import Path
import socket
import ssl
import sys
import threading
from contextlib import ExitStack

from coding_orchestrator.job_store import JobStore
from coding_orchestrator.jobs import ExecutionProfile, JobService, Principal
from coding_orchestrator.preview_broker import PreviewBroker
from supervised_fixture import Authority, bind, run, LedgerWorkerSupervisor


def main():
    directory, mode = Path(sys.argv[1]), sys.argv[2]
    owner = Principal("owner", "tenant")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(directory / "ca.crt")
    server = "wrong-server" if mode == "wrong-server" else "server"
    context.load_cert_chain(directory / (server + ".crt"), directory / (server + ".key"))
    certificate = ssl.PEM_cert_to_DER_cert((directory / "nas.crt").read_text())
    with JobStore(directory / "jobs.sqlite") as store, ExitStack() as cleanup:
        authority = Authority(directory, "unknown" if "unknown" in mode else mode)
        supervisor = LedgerWorkerSupervisor(directory / "executor", authority=authority,
            identity_for=lambda ctx: store.execution_identity(owner.user_id, owner.tenant_id, ctx.job_id),
            bind_runner=bind)
        cleanup.callback(supervisor.close)
        authority.inspect = supervisor.ledger.status
        profile = ExecutionProfile("broker-fixture", frozenset({"fixture"}), run,
            lambda principal, scope: principal == owner and scope.repository_alias == "fixture" and scope.task_mode == "read_only",
            supervisor.confirm_stopped)
        service = JobService(store, profile=profile, enabled=True, worker_factory=supervisor.worker_factory)
        cleanup.callback(service.close)
        broker = PreviewBroker(service, context=context, client_id="synthetic-nas",
            client_sha256=hashlib.sha256(certificate).hexdigest(),
            grants={owner: {"fixture"}, Principal("other", "tenant"): {"fixture"}},
            admit_start=lambda principal, request: request.get("prompt") != "denied",
            enabled=mode != "disabled", timeout_seconds=1)
        exchange = broker.pipe.exchange
        dropped = False

        def drop_reply(body):
            nonlocal dropped
            response = exchange(body)
            operation = json.loads(body)["payload"]["operation"]
            if not dropped and ((mode == "drop-start-unknown" and operation == "start")
                                or (mode == "drop-cancel-unknown" and operation == "cancel")):
                dropped = True
                raise ConnectionResetError("synthetic lost reply")
            if mode == "wrong-reply":
                value = json.loads(response)
                value["principal"]["user_id"] = "foreign"
                return json.dumps(value).encode() + b"\n"
            return response

        broker.pipe.exchange = drop_reply
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(2)
            listener.settimeout(.1)
            stop = threading.Event()
            threading.Thread(target=lambda: (sys.stdin.buffer.read(), stop.set()), daemon=True).start()
            print(json.dumps({"port": listener.getsockname()[1]}), flush=True)
            while not stop.is_set():
                try:
                    connection, _ = listener.accept()
                except socket.timeout:
                    continue
                broker.handle(connection)


if __name__ == "__main__":
    main()
