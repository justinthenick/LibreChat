"""Dormant, in-process synthetic custody -> ledger -> model transport fixture.

No credential delivery protocol, live transport, worker containment or SDK OAuth.
The trusted host owns both stores; claims are correlation, not authentication.
"""
import hashlib
import threading
import time

from .auth_custody import SyntheticCredentialCustodian, CustodyError, _require, _failure, _raise
from .bounded_llm import RESPONSES_URL


MAX_FIXTURE_RESPONSE = 1024 * 1024


class SyntheticCredentialDispatch:
    def __init__(self, custody, ledger, claim, revision, epoch, control, *, enabled=False):
        from coding_executor.executions import ExecutionService
        _require(enabled is True and type(custody) is SyntheticCredentialCustodian
                 and type(ledger) is ExecutionService)
        self.custody, self.ledger, self.claim = custody, ledger, claim
        self.revision, self.epoch, self.control = revision, epoch, control
        self._sequence = 0
        self._lock = threading.Lock()
        self._failure = None

    def __reduce__(self):
        raise TypeError('Credential dispatch must be constructed inside the trusted fixture')

    def __call__(self, request, transport):
        result, category = self._call(request, transport)
        self = request = transport = None
        if category:
            result = None
            _raise(category)
        return result

    def _call(self, request, transport):
        import httpx
        if not self._lock.acquire(blocking=False):
            return None, CustodyError
        outcome = []
        try:
            if self._failure:
                return None, self._failure
            _require(type(transport) is httpx.MockTransport)
            _require(request.method == 'POST' and str(request.url) == RESPONSES_URL)
            self.control.remaining_seconds()
            action_id = f'model-{self._sequence}'
            self._sequence += 1
            digest = hashlib.sha256(request.content).hexdigest()
            def dispatch(_remaining):
                # Return only a sanitized outcome across the ledger thread seam.
                response, category = self._send(action_id, request, transport)
                outcome.append((response, category))
                if category:
                    raise CustodyError()
                return response

            self.ledger.dispatch(self.claim, action_id, digest, dispatch)
            _require(len(outcome) == 1)
            result, category = outcome[0]
            if category:
                self._failure = category
                return None, category
            self.control.remaining_seconds()
            return result, None
        except Exception as error:
            self._failure = _failure(self.control, error, outcome[0][1] if outcome else None)
            return None, self._failure
        finally:
            self._lock.release()

    def _send(self, action_id, request, transport):
        result = category = None
        try:
            with self.custody._guard(), self.ledger.synthetic_dispatch_fence(
                    self.claim, action_id, enabled=True) as deadline:
                result, category = self._send_locked(request, transport, deadline)
            if category is None:
                self.control.remaining_seconds()
        except Exception as error:
            result, category = None, _failure(self.control, error, category)
        return result, category

    def _send_locked(self, request, transport, deadline):
        import httpx
        result = category = response = wire = None
        try:
            with self.custody._transaction() as db:
                row, _ = self.custody._bound(db, self.claim, self.revision, self.epoch)
                _require(row['state'] == 'ready' and row['revision'] == self.revision
                         and type(row['expires_at']) is int and row['expires_at'] > time.time()
                         and type(row['access_token']) is str and row['access_token'])
                token, account = row['access_token'], row['account']
            # Only this separate wire object sees the fixture token. SDK request,
            # LLM configuration, ledger receipts and runner never receive it.
            headers = dict(request.headers)
            headers['authorization'] = 'Bearer ' + token
            headers['chatgpt-account-id'] = account
            wire = httpx.Request('POST', RESPONSES_URL, headers=headers, content=request.content)
            _require(time.monotonic() < deadline)
            self.control.before_provider_request()
            _require(time.monotonic() < deadline and row['expires_at'] > time.time())
            response = transport.handle_request(wire)
            _require(response.headers.get('content-encoding', 'identity') == 'identity')
            content = bytearray()
            for chunk in response.stream:
                self.control.remaining_seconds()
                _require(type(chunk) is bytes and len(content) + len(chunk) <= MAX_FIXTURE_RESPONSE)
                content.extend(chunk)
            self.control.remaining_seconds()
            _require(token.encode() not in content and all(
                token.encode() not in name and token.encode() not in value
                for name, value in response.headers.raw))
            result = httpx.Response(response.status_code, headers=response.headers,
                                    content=bytes(content), request=request)
        except Exception as error:
            category = _failure(self.control, error)
        finally:
            if wire is not None:
                wire.headers.pop('authorization', None)
                wire.headers.pop('chatgpt-account-id', None)
            if response is not None:
                try:
                    response.close()
                except Exception as error:
                    category = _failure(self.control, error, category)
        return (None if category else result), category
