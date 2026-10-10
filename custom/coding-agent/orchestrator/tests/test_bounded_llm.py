"""Real pinned SDK/LiteLLM Responses calls with synthetic auth and fake wire I/O."""
from __future__ import annotations

import asyncio
from contextlib import ExitStack
import io
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from coding_orchestrator.backend import BackendContractError
from coding_orchestrator.bounded_llm import BoundedResponses, RESPONSES_URL
from coding_orchestrator.job_worker import (
    WorkerCancelled, WorkerControl, WorkerDeadline, WorkerLimit,
)


MODEL = "gpt-5.6-sol"


def synthetic_llm():
    """Keep SDK parsing/routing real; require streaming without loading OAuth."""
    from openhands.sdk import LLM

    class SyntheticLLM(LLM):
        @property
        def requires_streaming(self):
            return True

    return SyntheticLLM(
        model=f"openai/{MODEL}", base_url=RESPONSES_URL.rsplit("/", 1)[0],
        api_key="synthetic-not-a-credential", api_mode="responses", stream=True,
        max_input_tokens=32768, max_output_tokens=1024,
        retry_min_wait=0, retry_max_wait=0, retry_multiplier=0,
    )


def function_call_response(*calls):
    """Codex-shaped SSE: complete function items, then an empty completed output."""
    import httpx

    events = []
    for index, (name, arguments) in enumerate(calls):
        events.append({
            "type": "response.output_item.done", "sequence_number": index,
            "output_index": index,
            "item": {"id": f"item-{index}", "type": "function_call",
                     "call_id": f"call-{index}", "name": name,
                     "arguments": json.dumps(arguments), "status": "completed"},
        })
    events.append({
        "type": "response.completed", "sequence_number": len(events),
        "response": {
            "id": "resp-synthetic", "object": "response", "created_at": 1,
            "status": "completed", "model": MODEL, "output": [],
            "parallel_tool_calls": False, "tool_choice": "auto", "tools": [],
            "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        },
    })
    body = "".join(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"
                   for event in events).encode()
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body)


class Counter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def get_lock(self):
        return self.lock


class BoundedResponsesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack = ExitStack()
        cls.addClassCleanup(cls.stack.close)
        root = cls.stack.enter_context(tempfile.TemporaryDirectory())
        cls.stack.enter_context(patch.dict(os.environ, {
            "HOME": root, "OH_PERSISTENCE_DIR": root,
            "LITELLM_LOCAL_MODEL_COST_MAP": "True", "OTEL_SDK_DISABLED": "true",
            "PYTHON_DOTENV_DISABLED": "1",
            "OPENHANDS_SUPPRESS_BANNER": "1",
        }, clear=True))
        cls.forbidden_calls = []
        for name in ("connect", "connect_ex"):
            cls.forbidden_calls.append(cls.stack.enter_context(patch.object(socket.socket, name,
                side_effect=AssertionError("No test socket connections are allowed"))))
        cls.forbidden_calls.append(cls.stack.enter_context(patch.object(socket, "getaddrinfo",
            side_effect=AssertionError("No test DNS resolution is allowed"))))
        from openhands.sdk.llm.auth.credentials import CredentialStore
        from openhands.sdk.llm.auth.openai import OpenAISubscriptionAuth
        for name in ("get", "save"):
            cls.forbidden_calls.append(cls.stack.enter_context(patch.object(CredentialStore, name,
                side_effect=AssertionError("Tests must not access credentials"))))
        for name in ("refresh_if_needed_sync", "extract_chatgpt_account_id"):
            cls.forbidden_calls.append(cls.stack.enter_context(
                patch.object(OpenAISubscriptionAuth, name,
                    side_effect=AssertionError("Tests must not resolve authentication"))))

    @classmethod
    def tearDownClass(cls):
        for forbidden in cls.forbidden_calls:
            forbidden.assert_not_called()

    def setUp(self):
        import litellm
        # Isolate the library's own failure-path mutation between test cases.
        retries = patch.object(litellm, "num_retries", None)
        retries.start()
        self.addCleanup(retries.stop)
        self.reset_control()

    def reset_control(self):
        self.counter = Counter()
        self.cancelled = threading.Event()
        self.limited = threading.Event()
        self.control = WorkerControl(self.counter, self.cancelled, self.limited,
            time.monotonic() + 30, 10, io.BytesIO())
        self.wire = []

    def bind(self, handler=None, llm=None):
        import httpx

        def send(request):
            self.wire.append(request)
            self.assertEqual(self.counter.value, len(self.wire))
            if handler is not None:
                return handler(request)
            return function_call_response(("list_repositories", {}))

        bounded = BoundedResponses(llm or synthetic_llm(), self.control,
                                   transport=httpx.MockTransport(send))
        self.addCleanup(bounded.close)
        return bounded

    def messages(self):
        from openhands.sdk.llm import Message, TextContent
        return [Message(role="user", content=[TextContent(text="Synthetic fixture only.")])]

    def test_real_sdk_parses_function_call_sse_and_counts_each_wire_request(self):
        bounded = self.bind()
        with bounded:
            for _ in range(2):
                result = bounded.llm.generate(self.messages())
                self.assertEqual(result.message.tool_calls[0].name, "list_repositories")
                self.assertEqual(json.loads(result.message.tool_calls[0].arguments), {})
            bounded.assert_bound(bounded.llm)
        self.assertEqual(self.counter.value, 2)
        self.assertEqual(len(self.wire), 2)
        self.assertTrue(bounded._client.is_closed)
        self.assertFalse(bounded._client.follow_redirects)
        with self.assertRaises(BackendContractError):
            bounded.llm.generate(self.messages())
        self.assertEqual(len(self.wire), 2)

    def test_default_transport_initialization_never_dispatches(self):
        with BoundedResponses(synthetic_llm(), self.control) as bounded:
            bounded.assert_bound(bounded.llm)
            self.assertFalse(bounded._client.follow_redirects)
            self.assertEqual(self.counter.value, 0)
        self.assertTrue(bounded._client.is_closed)

    def test_subscription_credentials_are_rejected_without_authentication(self):
        from openhands.sdk.llm.auth.credentials import OAuthCredentials

        for expiry in (None, 0, int(time.time() * 1000) + 3600000):
            with self.subTest(expiry=expiry):
                llm = synthetic_llm()
                llm.is_subscription = True
                llm.auth_type = "subscription"
                llm.subscription_vendor = "openai"
                if expiry is not None:
                    llm._subscription_credentials = OAuthCredentials(
                        vendor="openai", access_token="synthetic-token",
                        refresh_token="synthetic-refresh", expires_at=expiry,
                    )
                with self.assertRaisesRegex(BackendContractError, "credential resolution"):
                    self.bind(llm=llm)
        serialized = synthetic_llm()
        serialized.auth_type = "subscription"
        self.assertFalse(serialized.is_subscription)
        with self.assertRaisesRegex(BackendContractError, "credential resolution"):
            self.bind(llm=serialized)
        for field, value in (("is_subscription", True), ("auth_type", "subscription")):
            bounded = self.bind()
            setattr(bounded.llm, field, value)
            with self.assertRaises(BackendContractError):
                bounded.llm.responses(self.messages())
        self.assertEqual(self.counter.value, 0)
        self.assertEqual(self.wire, [])

    def test_budget_cancel_deadline_reject_before_fake_dispatch(self):
        for error in (WorkerLimit, WorkerCancelled, WorkerDeadline):
            with self.subTest(error=error.__name__):
                self.reset_control()
                if error is WorkerLimit:
                    self.control._maximum = 0
                elif error is WorkerCancelled:
                    self.cancelled.set()
                else:
                    self.control._deadline = time.monotonic() - 1
                bounded = self.bind()
                with self.assertRaises(error):
                    bounded.llm.responses(self.messages())
                self.assertEqual(self.counter.value, 0)
                self.assertEqual(self.wire, [])

    def test_failures_never_retry_or_refresh(self):
        import httpx

        for failure in (401, 429, 500, 307, "connection", "malformed"):
            with self.subTest(failure=failure):
                self.reset_control()
                refreshes = []
                llm = synthetic_llm()
                llm.set_api_key_refresh_hook(lambda: refreshes.append(True) or "replacement")

                def fail(request):
                    if failure == "connection":
                        raise httpx.ConnectError("Synthetic connection error", request=request)
                    if failure == "malformed":
                        return httpx.Response(200, content=b"data: {\n\n",
                                              headers={"content-type": "text/event-stream"})
                    return httpx.Response(failure,
                        headers={"location": "https://example.invalid/redirect"},
                        json={"error": {"message": "Synthetic failure", "type": "test_error"}})

                bounded = self.bind(fail, llm)
                with self.assertRaisesRegex(BackendContractError, "request failed") as first:
                    bounded.llm.responses(self.messages())
                with self.assertRaises(BackendContractError) as second:
                    bounded.llm.responses(self.messages())
                self.assertIs(first.exception, second.exception)
                self.assertEqual(len(self.wire), 1)
                self.assertEqual(self.counter.value, 1)
                self.assertEqual(refreshes, [])

    def test_content_filter_ends_real_sdk_loop_after_one_request(self):
        import httpx
        from openhands.sdk import Conversation
        from coding_orchestrator.openhands_backend import _validate_scratch_root
        from coding_orchestrator.restricted_agent import RestrictedOpenHandsAgent

        def respond(_request):
            if len(self.wire) == 1:
                return httpx.Response(400, json={"error": {
                    "message": "Synthetic content filter", "type": "invalid_request_error",
                    "code": "content_filter",
                }})
            return function_call_response(("finish", {"message": "Unexpected retry"}))

        bounded = self.bind(respond)
        agent = RestrictedOpenHandsAgent(
            llm=bounded.llm, tools=[], include_default_tools=["FinishTool"],
            system_prompt="Only finish this synthetic fixture.",
        )
        bounded.assert_bound(agent.llm)
        with tempfile.TemporaryDirectory() as workspace:
            _validate_scratch_root(workspace)
            conversation = Conversation(agent=agent, workspace=workspace,
                visualizer=None, max_iteration_per_run=3)
            try:
                conversation.send_message("Synthetic fixture only; finish immediately.")
                with self.assertRaisesRegex(Exception, "Bounded Responses request failed"):
                    conversation.run()
                self.assertEqual(conversation.state.execution_status.value, "error")
            finally:
                conversation.close()
        with self.assertRaisesRegex(BackendContractError, "request failed"):
            bounded.llm.responses(self.messages())
        self.assertEqual(self.counter.value, 1)
        self.assertEqual(len(self.wire), 1)

    def test_same_logical_call_cannot_dispatch_twice(self):
        def duplicate(request):
            bounded._client.send(request)
            return function_call_response(("list_repositories", {}))

        bounded = self.bind(duplicate)
        with self.assertRaisesRegex(BackendContractError, "repeated"):
            bounded.llm.responses(self.messages())
        self.assertEqual(len(self.wire), 1)
        self.assertEqual(self.counter.value, 1)

    def test_caller_cannot_replace_client_cache_or_request_budget(self):
        bounded = self.bind()
        self.control._maximum = 1
        bounded.llm.responses(self.messages(), client=object(), num_retries=99,
            max_retries=99, caching=True, cache={"no-cache": False}, retry_policy=object())
        with self.assertRaises(WorkerLimit):
            bounded.llm.responses(self.messages())
        self.assertEqual(self.counter.value, 1)
        self.assertEqual(len(self.wire), 1)

    def test_physical_request_without_logical_call_is_rejected(self):
        bounded = self.bind()
        with self.assertRaisesRegex(BackendContractError, "Unexpected"):
            bounded._client.post(RESPONSES_URL, json={"model": MODEL})
        self.assertEqual(self.counter.value, 0)
        self.assertEqual(self.wire, [])

    def test_nested_logical_call_is_rejected(self):
        def nested(_request):
            bounded.llm.responses(self.messages())
            return function_call_response(("list_repositories", {}))

        bounded = self.bind(nested)
        with self.assertRaisesRegex(BackendContractError, "nested"):
            bounded.llm.responses(self.messages())
        self.assertEqual(self.counter.value, 1)
        self.assertEqual(len(self.wire), 1)

    def test_destination_and_model_are_checked_at_wire(self):
        import httpx

        for url, method, body in (
            (RESPONSES_URL + "?unexpected=1", "POST", {"model": MODEL}),
            (RESPONSES_URL, "GET", {"model": MODEL}),
            (RESPONSES_URL, "POST", {"model": "different-model"}),
        ):
            with self.subTest(url=url, method=method, body=body):
                bounded = self.bind()
                bounded._thread = threading.get_ident()
                with self.assertRaises(BackendContractError):
                    bounded._client.send(httpx.Request(method, url, json=body))
                self.assertEqual(self.wire, [])
                self.assertEqual(self.counter.value, 0)

    def test_sdk_body_override_is_checked_at_physical_dispatch(self):
        llm = synthetic_llm()
        llm.litellm_extra_body = {"model": "different-model"}
        bounded = self.bind(llm=llm)
        with self.assertRaisesRegex(BackendContractError, "model changed"):
            bounded.llm.responses(self.messages())
        self.assertEqual(self.wire, [])

    def test_global_retries_and_alternate_call_routes_fail_closed(self):
        import litellm

        with patch.object(litellm, "num_retries", 2):
            with self.assertRaisesRegex(BackendContractError, "Global"):
                self.bind()
        bounded = self.bind()
        with patch.object(litellm, "num_retries", 2):
            with self.assertRaises(BackendContractError):
                bounded.llm.responses(self.messages())
        for name in ("model", "api_base", "custom_llm_provider", "use_chat_completions_api"):
            bounded = self.bind()
            with self.assertRaises(BackendContractError):
                bounded.llm.responses(self.messages(), **{name: "unexpected"})
        self.assertEqual(self.wire, [])

    def test_async_and_chat_paths_are_rejected(self):
        for name in ("completion", "acompletion", "aresponses", "agenerate"):
            with self.subTest(method=name):
                bounded = self.bind()
                with self.assertRaisesRegex(BackendContractError, "synchronous Responses"):
                    if name.startswith("a"):
                        asyncio.run(getattr(bounded.llm, name)(self.messages()))
                    else:
                        getattr(bounded.llm, name)(self.messages())
        self.assertEqual(self.wire, [])

    def test_instance_guard_isolation_and_runtime_identity(self):
        first = self.bind()
        other_llm = synthetic_llm()
        self.assertNotIn("responses", other_llm.__dict__)
        other_counter = Counter()
        other_control = WorkerControl(other_counter, threading.Event(), threading.Event(),
            time.monotonic() + 30, 10, io.BytesIO())
        import httpx
        other_wire = []
        def send(request):
            other_wire.append(request)
            self.assertEqual(other_counter.value, 1)
            return function_call_response(("finish", {"message": "Done"}))
        with BoundedResponses(other_llm, other_control, transport=httpx.MockTransport(send)) as other:
            first.llm.responses(self.messages())
            other.llm.responses(self.messages())
            first.close()
            other.assert_bound(other_llm)
        self.assertEqual(self.counter.value, 1)
        self.assertEqual(other_counter.value, 1)
        self.assertEqual(len(other_wire), 1)
        fresh = self.bind()
        with self.assertRaisesRegex(BackendContractError, "replaced"):
            fresh.assert_bound(fresh.llm.model_copy())


if __name__ == "__main__":
    unittest.main()
