"""Fixed-origin auth transport; dormant until explicitly constructed in a worker.

Uses the pinned httpcore parser, with one owned socket and shrinking timeouts.
No configurable origin, proxy, TLS policy, retry or transport is exposed by the
factory. OS DNS is synchronous: ProcessWorker remains the hard deadline backstop.
"""
import os
import socket
import ssl
import threading

from .auth_exchange import BoundedAuthExchange, KEYS_URL, TOKEN_URL, MAX_REPLY
from .backend import BackendContractError
from .job_worker import WorkerLimit

HOST = "auth.openai.com"
# SSLSocket.recv returns plaintext HTTP, including HTTP framing. This does not
# count encrypted TLS records, padding or other network-level overhead.
MAX_HTTP_RESPONSE_BYTES = 128 * 1024


def create_auth_exchange(control, *, enabled=False):
    """Construct only inside the isolated worker; does not fetch or resolve auth."""
    if type(enabled) is not bool:
        raise ValueError("Explicit auth transport policy required")
    if not enabled:
        return BoundedAuthExchange(control)
    return BoundedAuthExchange(control, transport=_FixedTransport(control), enabled=True)


class _SocketStream:
    def __init__(self, owner, sock):
        self.owner, self.sock = owner, sock
        self.received = 0

    def read(self, max_bytes, timeout=None):
        self.sock.settimeout(self.owner.remaining())
        data = self.sock.recv(min(max_bytes, MAX_HTTP_RESPONSE_BYTES - self.received + 1))
        self.owner.remaining()
        self.received += len(data)
        if self.received > MAX_HTTP_RESPONSE_BYTES:
            raise WorkerLimit()
        return data

    def write(self, buffer, timeout=None):
        view = memoryview(buffer)
        while view:
            self.sock.settimeout(self.owner.remaining())
            count = self.sock.send(view)
            self.owner.remaining()
            if count <= 0:
                raise BackendContractError("Auth write outcome unknown")
            view = view[count:]

    def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        if server_hostname != HOST or ssl_context is not self.owner.context:
            raise BackendContractError("Auth TLS destination rejected")
        try:
            self.sock.settimeout(self.owner.remaining())
            self.sock = ssl_context.wrap_socket(self.sock, server_hostname=HOST,
                                                do_handshake_on_connect=False)
            self.sock.settimeout(self.owner.remaining())
            self.sock.do_handshake()
            self.owner.remaining()
            return self
        except Exception:
            self.close()
            raise

    def get_extra_info(self, info):
        # No reusable connections; the parser needs no socket introspection.
        return None

    def close(self):
        self.sock.close()


class _Network:
    def __init__(self, owner):
        self.owner = owner
        self.attempted = False

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        if self.attempted or host != HOST or port != 443 or local_address is not None:
            raise BackendContractError("Auth connection rejected")
        self.attempted = True
        self.owner.remaining()
        addresses = socket.getaddrinfo(HOST, 443, type=socket.SOCK_STREAM)
        self.owner.remaining()
        if not addresses:
            raise BackendContractError("Auth destination unavailable")
        # Deliberately no address fallback: one TCP attempt, never a retry.
        family, kind, protocol, _, address = addresses[0]
        sock = socket.socket(family, kind, protocol)
        stream = _SocketStream(self.owner, sock)
        self.owner.stream = stream
        try:
            sock.settimeout(self.owner.remaining())
            sock.connect(address)
            self.owner.remaining()
            return stream
        except Exception:
            stream.close()
            raise

    def connect_unix_socket(self, *args, **kwargs):
        raise BackendContractError("Auth Unix transport rejected")

    def sleep(self, seconds):
        raise BackendContractError("Auth retry rejected")


class _FixedTransport:
    def __init__(self, control):
        import certifi

        self.control = control
        self.pid = os.getpid()
        self.closed = False
        self.stream = None
        self.lock = threading.Lock()
        # create_default_context also discovers system/environment roots. Load
        # only certifi here so SSL_CERT_FILE/SSL_CERT_DIR cannot add trust.
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.context.load_verify_locations(cafile=certifi.where())
        self.context.minimum_version = ssl.TLSVersion.TLSv1_2

    def remaining(self):
        if self.closed or os.getpid() != self.pid:
            raise BackendContractError("Auth transport unavailable")
        return self.control.remaining_seconds()

    def handle_request(self, request):
        import httpcore
        import httpx

        if not self.lock.acquire(blocking=False):
            self.close()
            raise BackendContractError("Concurrent auth transport rejected")
        try:
            self.remaining()
            url = str(request.url)
            if ((request.method, url) not in {("POST", TOKEN_URL), ("GET", KEYS_URL)}
                    or len(request.content) > 32 * 1024
                    or self.context.check_hostname is not True
                    or self.context.verify_mode != ssl.CERT_REQUIRED
                    or self.context.minimum_version < ssl.TLSVersion.TLSv1_2):
                raise BackendContractError("Auth transport contract rejected")
            # Construct framing ourselves. Caller headers/extensions cannot inject
            # credentials, proxy auth, tracing, redirects or an alternate Host.
            body = request.content if request.method == "POST" else b""
            headers = [(b"Host", HOST.encode()), (b"Connection", b"close"),
                       (b"Accept", b"application/json"), (b"Accept-Encoding", b"identity"),
                       (b"Content-Length", str(len(body)).encode())]
            if request.method == "POST":
                headers.append((b"Content-Type", b"application/x-www-form-urlencoded"))
            with httpcore.ConnectionPool(ssl_context=self.context, proxy=None,
                    max_connections=1, max_keepalive_connections=0, http1=True, http2=False,
                    retries=0, network_backend=_Network(self)) as pool:
                core_request = httpcore.Request(request.method, url, headers=headers, content=body,
                    extensions={"timeout": dict.fromkeys(("connect", "read", "write", "pool"), self.remaining())})
                response = pool.handle_request(core_request)
                try:
                    self.remaining()
                    # Do not read redirect/error bodies and never follow Location.
                    if response.status != 200:
                        raise BackendContractError("Auth response rejected")
                    encodings = [value.strip().lower() for name, value in response.headers
                                 if name.lower() == b"content-encoding"]
                    media = [value.split(b";", 1)[0].strip().lower() for name, value in response.headers
                             if name.lower() == b"content-type"]
                    if (encodings not in ([], [b"identity"])
                            or media != [b"application/json"]):
                        raise BackendContractError("Auth response headers rejected")
                    payload = bytearray()
                    for chunk in response.iter_stream():
                        self.remaining()
                        if len(payload) + len(chunk) > MAX_REPLY:
                            raise WorkerLimit()
                        payload.extend(chunk)
                    self.remaining()
                    return httpx.Response(response.status, headers=response.headers, content=bytes(payload))
                finally:
                    response.close()
        finally:
            try:
                if self.stream is not None:
                    self.stream.close()
            finally:
                self.stream = None
                self.lock.release()

    def close(self):
        self.closed = True
        stream = self.stream
        if stream is not None:
            try:
                stream.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            stream.close()
