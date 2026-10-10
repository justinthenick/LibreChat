"""Unregistered one-shot HTTPS broker. Host owns listener, TLS material and lifecycle."""
import hashlib
import re
import socket
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler

from .preview_pipe import PreviewPipe, MAX_INPUT_BYTES


class _BoundedReader:
    def __init__(self, reader, remaining=8192):
        self.reader, self.remaining = reader, remaining

    def readline(self, size=-1):
        value = self.reader.readline(min(self.remaining + 1, size) if size >= 0 else self.remaining + 1)
        self.remaining -= len(value)
        if self.remaining < 0:
            raise ValueError("request headers exceed bound")
        return value

    def read(self, size):
        if size > self.remaining:
            raise ValueError("request body exceeds bound")
        value = self.reader.read(size)
        self.remaining -= len(value)
        return value

    def close(self):
        self.reader.close()


class PreviewBroker:
    """One NAS identity realm per store; no ambient files, listener or worker creation.

    The host must exclusively own the SSLContext and keep its trust configuration
    immutable. A verified pinned client certificate may assert ONLY the configured
    principal/repository grants. Neither certificate nor frame fields prove stop.
    The trusted admission callback and supplied JobService must be bounded.
    """

    def __init__(self, service, *, context, client_id, client_sha256, grants, admit_start,
                 enabled=False, timeout_seconds=5):
        if (type(enabled) is not bool or type(timeout_seconds) not in (int, float)
                or not 0 < timeout_seconds <= 30
                or not isinstance(context, ssl.SSLContext)
                or context.protocol != ssl.PROTOCOL_TLS_SERVER
                or context.verify_mode != ssl.CERT_REQUIRED
                or context.minimum_version < ssl.TLSVersion.TLSv1_2
                or type(client_id) is not str or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", client_id)
                or type(client_sha256) is not str or not re.fullmatch(r"[a-f0-9]{64}", client_sha256)):
            raise ValueError("explicit mutually authenticated broker configuration required")
        self.context, self.client_id, self.client_sha256 = context, client_id, client_sha256
        self.enabled, self.timeout = enabled, timeout_seconds
        self.pipe = PreviewPipe(service, grants=grants, admit_start=admit_start, enabled=enabled)
        self._active = threading.Lock()

    def handle(self, connection):
        """Consume one already-accepted socket. Busy/disabled connections close without dispatch.

        No threads are created for client work. The owner bounds its accept loop;
        the single active call has an absolute network deadline including TLS.
        Closing this socket never cancels, retries or reconciles an admitted job.
        """
        if not self.enabled or not self._active.acquire(blocking=False):
            connection.close()
            return
        stream = connection
        expired = threading.Event()
        deadline = time.monotonic() + self.timeout

        def abort():
            expired.set()
            try:
                stream.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            stream.close()

        timer = threading.Timer(self.timeout, abort)
        timer.daemon = True
        timer.start()
        try:
            if (self.context.verify_mode != ssl.CERT_REQUIRED
                    or self.context.minimum_version < ssl.TLSVersion.TLSv1_2):
                return
            stream = self.context.wrap_socket(connection, server_side=True, do_handshake_on_connect=False)
            stream.settimeout(max(.001, deadline - time.monotonic()))
            stream.do_handshake()
            certificate = stream.getpeercert(binary_form=True)
            if not certificate or hashlib.sha256(certificate).hexdigest() != self.client_sha256:
                return
            broker = self

            class Handler(BaseHTTPRequestHandler):
                protocol_version = "HTTP/1.1"
                server_version = "Preview"
                sys_version = ""

                def setup(self):
                    super().setup()
                    self.rfile = _BoundedReader(self.rfile)

                def log_message(self, *_args):
                    pass

                def handle(self):
                    self.close_connection = True
                    self.handle_one_request()

                def do_POST(self):
                    self.close_connection = True
                    names = [name.lower() for name in self.headers.keys()]
                    size = self.headers.get("Content-Length", "")
                    if (self.path != "/preview/v1" or self.request_version != "HTTP/1.1"
                            or len(names) != len(set(names)) or "transfer-encoding" in names
                            or self.headers.get("Content-Type") != "application/json"
                            or not re.fullmatch(r"[0-9]{1,5}", size)
                            or not 0 < int(size) <= MAX_INPUT_BYTES):
                        self.send_error(400)
                        return
                    self.rfile.remaining = int(size)
                    body = self.rfile.read(int(size))
                    if len(body) != int(size) or expired.is_set() or time.monotonic() >= deadline:
                        return
                    response = broker.pipe.exchange(body)
                    if expired.is_set() or time.monotonic() >= deadline:
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(response)))
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.wfile.write(response)

            Handler(stream, stream.getpeername(), None)
        except (OSError, ValueError, RecursionError):
            # Fixed close-only failure: never expose provider, certificate or job details.
            pass
        finally:
            timer.cancel()
            stream.close()
            self._active.release()
