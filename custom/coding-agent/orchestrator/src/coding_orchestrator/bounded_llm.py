"""Instance-only, synchronous Responses transport for a trusted worker.

Verify the runtime agent keeps this exact instance. Subscription LLM objects
are unsupported until their authentication lifecycle has a reviewed bounded
integration. This adapter does not discover credentials or change the SDK's
response parser. It owns and closes the supplied transport.
"""
from __future__ import annotations

import json
import threading

from .backend import BackendContractError


RESPONSES_URL = "https://chatgpt.com/backend-api/codex/responses"


class BoundedResponses:
    def __init__(self, llm, control, *, transport=None):
        # The SDK extra stays optional until an explicitly configured run.
        import httpx
        import litellm
        from litellm.llms.custom_httpx.http_handler import HTTPHandler

        if llm.is_subscription or llm.auth_type == "subscription":
            raise BackendContractError("Bounded Responses does not support subscription credential resolution")
        if (not isinstance(llm.model, str) or not llm.model.startswith("openai/")
                or not llm.model.removeprefix("openai/")
                or "/" in llm.model.removeprefix("openai/")
                or llm.base_url != RESPONSES_URL.rsplit("/", 1)[0]):
            raise BackendContractError("Bounded Responses requires the Codex route")
        if litellm.num_retries not in (None, 0):
            raise BackendContractError("Global LiteLLM retries must be disabled")
        if "responses" in llm.__dict__:
            raise BackendContractError("Responses instance is already wrapped")

        self.llm = llm
        self._control = control
        self._model = llm.model
        self._lock = threading.Lock()
        self._thread = None
        self._sent = False
        self._failure = None
        self._closed = False
        self._original = llm.responses
        inner = transport if transport is not None else httpx.HTTPTransport(
            retries=0, trust_env=False,
        )
        owner = self

        class Transport(httpx.BaseTransport):
            def handle_request(self, request):
                return owner._dispatch(request, inner)

            def close(self):
                inner.close()

        self._client = httpx.Client(
            transport=Transport(), follow_redirects=False, trust_env=False,
        )
        self._handler = HTTPHandler(client=self._client)
        llm.num_retries = 0
        llm.caching_prompt = False
        llm.fallback_strategy = None
        llm.api_mode = "responses"
        llm.set_api_key_refresh_hook(None)
        self._bindings = {
            "responses": self._responses,
            "completion": self._unsupported,
            "aresponses": self._unsupported_async,
            "acompletion": self._unsupported_async,
        }
        for name, method in self._bindings.items():
            object.__setattr__(llm, name, method)

    def _deny(self, message):
        if self._failure is None:
            self._failure = BackendContractError(message)
        raise self._failure

    def assert_bound(self, candidate):
        """Fail before running an agent whose SDK normalization replaced the LLM."""
        import litellm

        if self._closed:
            self._deny("Bounded Responses is closed")
        if self._failure is not None:
            raise self._failure
        if (candidate is not self.llm
                or any(getattr(candidate, name) != method
                       for name, method in self._bindings.items())
                or candidate.model != self._model
                or candidate.base_url != RESPONSES_URL.rsplit("/", 1)[0]
                or candidate.is_subscription
                or candidate.auth_type == "subscription"
                or candidate.api_mode != "responses"
                or candidate.num_retries != 0
                or candidate.caching_prompt is not False
                or candidate.fallback_strategy is not None
                or candidate._api_key_refresh_hook is not None
                or litellm.num_retries not in (None, 0)):
            self._deny("Bounded Responses configuration was replaced")

    def _dispatch(self, request, inner):
        self.assert_bound(self.llm)
        if (self._thread != threading.get_ident() or self._sent
                or request.method != "POST" or str(request.url) != RESPONSES_URL):
            self._deny("Unexpected or repeated Responses dispatch")
        try:
            body = json.loads(request.content)
        except (ValueError, UnicodeError):
            self._deny("Invalid Responses request body")
        if not isinstance(body, dict) or body.get("model") != self._model.removeprefix("openai/"):
            self._deny("Responses request model changed")
        self._sent = True
        try:
            self._control.before_provider_request()
        except Exception as error:
            self._failure = error
            raise
        return inner.handle_request(request)

    def _responses(self, *args, **kwargs):
        self.assert_bound(self.llm)
        if not self._lock.acquire(blocking=False):
            self._deny("Concurrent or nested Responses call")
        try:
            self._thread = threading.get_ident()
            self._sent = False
            # Do not allow callers to select another provider/dispatch path.
            allowed = {
                "messages", "tools", "include", "store", "add_security_risk_prediction",
                "on_token", "call_context", "stream", "client", "num_retries",
                "max_retries", "caching", "cache", "retry_policy",
            }
            if set(kwargs) - allowed:
                self._deny("Unsupported bounded Responses option")
            kwargs.update(client=self._handler, num_retries=0, max_retries=0,
                          retry_policy=None, caching=False,
                          cache={"no-cache": True, "no-store": True})
            try:
                result = self._original(*args, **kwargs)
            except Exception:
                # The agent retries some SDK exceptions as a new iteration.
                # Latch a fixed terminal error across that logical-call boundary.
                if self._failure is None:
                    self._failure = BackendContractError("Bounded Responses request failed")
                raise self._failure from None
            self.assert_bound(self.llm)
            if not self._sent:
                self._deny("Responses returned without a provider dispatch")
            return result
        finally:
            self._thread = None
            self._lock.release()

    def _unsupported(self, *args, **kwargs):
        self._deny("Only synchronous Responses inference is supported")

    async def _unsupported_async(self, *args, **kwargs):
        self._unsupported()

    def close(self):
        self._closed = True
        self._client.close()

    def __enter__(self):
        self.assert_bound(self.llm)
        return self

    def __exit__(self, *_):
        self.close()
