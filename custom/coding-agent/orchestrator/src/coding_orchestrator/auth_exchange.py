"""Dormant bounded auth wire exchanges, not credential discovery or validation.

Only trusted child-side code may supply the transport and secret. Nothing here
loads SDK auth, installs hooks, logs in, persists credentials or enables a profile.
The trusted transport must perform exactly one physical request per handle_request,
with no internal retry, redirect, proxy authentication or credential discovery,
and honor httpx timeouts. This wrapper cannot inspect arbitrary transport internals.
ProcessWorker bounds the whole process. The separate auth_transport factory
supplies a fixed-origin transport only when explicitly enabled inside the worker.
"""
from dataclasses import dataclass, field
import os
import threading
from urllib.parse import urlencode

from .backend import BackendContractError
from .job_worker import WorkerCancelled, WorkerDeadline, WorkerLimit

TOKEN_URL = "https://auth.openai.com/oauth/token"
KEYS_URL = "https://auth.openai.com/.well-known/jwks.json"
CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
MAX_REPLY = 64 * 1024


def _raise_failure(category):
    if category in (WorkerCancelled, WorkerDeadline, WorkerLimit):
        raise category() from None
    raise BackendContractError("Bounded auth exchange unavailable or outcome unknown") from None


@dataclass(frozen=True)
class AuthReply:
    """Unvalidated sensitive bytes; never a verified identity or stop proof."""

    body: bytes = field(repr=False)

    def __reduce__(self):
        raise TypeError("Auth replies cannot cross worker serialization")


class BoundedAuthExchange:
    """One refresh and one signing-key read per instance; errors are terminal.

    WorkerControl counts each dispatch; physical accounting requires the trusted
    one-request transport contract above (HTTPTransport(retries>0) is unsuitable). An
    uncertain refresh may have rotated the remote token; never retry it here.
    No default network transport exists. This module is not wired to the SDK.
    """

    def __init__(self, control, *, transport=None, enabled=False):
        if type(enabled) is not bool:
            raise ValueError("Explicit auth exchange policy required")
        self._control, self._transport, self._enabled = control, transport, enabled
        self._pid = os.getpid()
        self._lock = threading.Lock()
        self._used = set()
        self._failure = None
        self._closed = False

    def __reduce__(self):
        raise TypeError("Auth exchanges must be constructed inside the worker")

    def _check(self):
        if (self._failure is not None or self._closed or not self._enabled
                or self._transport is None or os.getpid() != self._pid):
            _raise_failure(self._failure)
        self._control.remaining_seconds()

    def refresh(self, refresh_token):
        reply, failure = self._exchange("refresh", refresh_token)
        # The secret-handling frame has returned. Do not retain the token or
        # transport owner in the public traceback when raising the safe category.
        self = refresh_token = None
        if failure is not None:
            _raise_failure(failure)
        return reply

    def signing_keys(self):
        reply, failure = self._exchange("keys", None)
        self = None
        if failure is not None:
            _raise_failure(failure)
        return reply

    def _exchange(self, operation, secret):
        acquired = False
        response = None
        try:
            acquired = self._lock.acquire(blocking=False)
            if not acquired:
                self._failure = BackendContractError
                _raise_failure(self._failure)
            self._check()
            if operation in self._used:
                raise BackendContractError("Auth operation already consumed")
            self._used.add(operation)
            import httpx

            if operation == "refresh":
                if (type(secret) is not str or not 1 <= len(secret) <= 8192
                        or any(ord(char) < 33 or ord(char) > 126 for char in secret)):
                    raise BackendContractError("Invalid auth input")
                content = urlencode({"grant_type": "refresh_token", "refresh_token": secret,
                                     "client_id": CLIENT_ID}).encode("ascii")
                request = httpx.Request("POST", TOKEN_URL, content=content,
                    headers={"content-type": "application/x-www-form-urlencoded"})
            else:
                request = httpx.Request("GET", KEYS_URL)
            # No Client: no ambient proxy, cookies, credentials, redirects or retries.
            remaining = self._control.remaining_seconds()
            request.extensions["timeout"] = dict.fromkeys(("connect", "read", "write", "pool"), remaining)
            self._control.before_provider_request()
            response = self._transport.handle_request(request)
            self._check()
            if response.status_code != 200 or response.headers.get("content-encoding", "identity") != "identity":
                raise BackendContractError("Auth response rejected")
            if response.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                raise BackendContractError("Auth response rejected")
            body = bytearray()
            # Iterate raw transport chunks so compressed bodies cannot inflate.
            for chunk in response.stream:
                self._check()
                if type(chunk) is not bytes or len(body) + len(chunk) > MAX_REPLY:
                    raise WorkerLimit()
                body.extend(chunk)
            self._check()
            response.close()
            response = None
            self._check()
            return AuthReply(bytes(body)), None
        except Exception as error:
            # Retain only an error type: transport exceptions may retain tokens.
            if self._failure is None:
                self._failure = type(error) if type(error) in (WorkerCancelled, WorkerDeadline, WorkerLimit) else BackendContractError
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass
            if acquired:
                self._lock.release()
        # No exception object or traceback escapes the secret-handling frame.
        return None, self._failure

    def close(self):
        self._closed = True
        failed = False
        if self._transport is not None:
            try:
                self._transport.close()
            except Exception:
                failed = True
        self = None
        if failed:
            raise BackendContractError("Auth transport close failed") from None
