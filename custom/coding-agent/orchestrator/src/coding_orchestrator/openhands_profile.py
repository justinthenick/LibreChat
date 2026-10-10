"""Dormant SDK job runner for explicitly supplied trusted server factories.

Nothing registers or enables this profile. Factories run inside ProcessWorker,
must not capture credentials, and must construct fresh per-job capabilities.
Production authentication, execution leases and restart reconciliation remain
activation prerequisites. A stopped local worker is not proof of remote stop.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import tempfile

from .backend import BackendRunRequest
from .evidence import EvidenceCollector
from .job_store import ExecutionIdentity, StopEvidence
from .job_worker import RunContext, WorkerCancelled, WorkerControl, WorkerDeadline, WorkerLimit
from .jobs import ExecutionProfile, Principal, RunScope
from .openhands_backend import OpenHandsBackend, _validate_endpoint


class OpenHandsProfileError(RuntimeError):
    """A fixed boundary error that contains no provider or executor payload."""


def _raise_run_failure(error: Exception) -> None:
    cause, seen = error.__cause__, set()
    while cause is not None and id(cause) not in seen:
        if type(cause) in (WorkerCancelled, WorkerDeadline, WorkerLimit):
            raise cause from None
        seen.add(id(cause))
        cause = cause.__cause__
    raise OpenHandsProfileError("openhands_profile_failed") from None


class _ScopedEvents:
    def __init__(self, context: RunContext, control: WorkerControl):
        self.context, self.control = context, control
        self.collector = EvidenceCollector(context.repository_alias)
        self.denied = False

    def _require(self, allowed: bool) -> None:
        if not allowed:
            self.denied = True
            raise OpenHandsProfileError("action_scope_denied") from None

    def __call__(self, event: object) -> None:
        from openhands.sdk.event import ActionEvent, ObservationEvent
        from openhands.sdk.mcp.definition import MCPToolAction

        self.control._check()
        self._require(not self.denied)
        if isinstance(event, ActionEvent):
            snapshot = self.collector.snapshot()
            # The pinned SDK emits the entire action batch before dispatch.
            self._require(snapshot["pending_count"] == 0)
            self._require(event.tool_name != "list_repositories")
            if event.tool_name != "finish":
                self._require(isinstance(event.action, MCPToolAction))
                arguments = event.action.data
                self._require(type(arguments) is dict)
                if event.tool_name == "create_task":
                    self._require(arguments.get("repository") == self.context.repository_alias
                                  and arguments.get("task_mode") == self.context.task_mode)
                else:
                    task = snapshot["task"]
                    self._require(task is not None and arguments.get("task_id") == task["task_id"])
                self._require(event.tool_name != "apply_patch" or self.context.task_mode == "modification")
        if isinstance(event, (ActionEvent, ObservationEvent)):
            try:
                self.collector.on_event(event)
            except Exception:
                self.denied = True
                raise
            self.control.emit_progress({"evidence": self.collector.snapshot()})


class _BoundBackend(OpenHandsBackend):
    def __init__(self, *args, binding, **kwargs):
        self._binding = binding
        super().__init__(*args, llm=binding.llm, **kwargs)

    def _build_agent(self):
        agent = super()._build_agent()
        self._binding.assert_bound(agent.llm)
        return agent


@dataclass(frozen=True)
class OpenHandsJobRunner:
    """Picklable server configuration, never constructed from request JSON.

    token_factory and llm_factory are explicit trusted capabilities. They run
    only when the worker calls the runner; credentials must not be captured in
    these factories or serialized with it. transport_factory is a test seam
    for physical HTTP responses, not a replacement for the SDK agent loop.
    """

    endpoint: str
    token_factory: Callable[[], str]
    llm_factory: Callable[[], object]
    transport_factory: Callable[[], object] | None = None

    def __post_init__(self) -> None:
        _validate_endpoint(self.endpoint)
        if not all(callable(factory) for factory in (self.token_factory, self.llm_factory)):
            raise ValueError("Explicit child-side factories are required")
        if self.transport_factory is not None and not callable(self.transport_factory):
            raise ValueError("Invalid transport factory")

    def __call__(self, context: RunContext, control: WorkerControl) -> dict:
        from openhands.sdk.conversation.exceptions import ConversationRunError
        from .bounded_llm import BoundedResponses

        try:
            control._check()
            RunScope(context.repository_alias, context.task_mode)
            events = _ScopedEvents(context, control)
            token, llm = self.token_factory(), self.llm_factory()
            if type(token) is not str or not token or getattr(llm, "model", None) != "openai/gpt-5.6-sol":
                raise OpenHandsProfileError("openhands_profile_configuration")
            control._check()
            transport = self.transport_factory() if self.transport_factory is not None else None
            with BoundedResponses(llm, control, transport=transport) as binding:
                backend = _BoundBackend(self.endpoint, token, binding=binding,
                                        scratch_root=tempfile.gettempdir())
                prompt = ("Selected repository: " + context.repository_alias
                          + ". Required task_mode: " + context.task_mode
                          + ". Use these explicit values for create_task. Do not list repositories. "
                          "Issue exactly one tool call per response.\n\n" + context.prompt)
                # One extra logical iteration reaches the physical request gate
                # when ten requests finish without completing the task.
                result = backend.run(BackendRunRequest(prompt, max_iterations=11), on_event=events)
                control._check()
                events._require(not events.denied)
                return {"execution_status": result.execution_status,
                        "final_response": result.final_response.encode("utf-8")[:8192].decode("utf-8", "ignore"),
                        "evidence": events.collector.snapshot()}
        except (WorkerCancelled, WorkerDeadline, WorkerLimit):
            raise
        except ConversationRunError as error:
            _raise_run_failure(error)
        except Exception:
            raise OpenHandsProfileError("openhands_profile_failed") from None


def _execution_unconfirmed(_identity: ExecutionIdentity) -> None:
    return None


def create_openhands_profile(*, profile_id: str, repository_aliases: frozenset[str],
                             endpoint: str, token_factory: Callable[[], str],
                             llm_factory: Callable[[], object],
                             authorize: Callable[[Principal, RunScope], bool],
                             transport_factory: Callable[[], object] | None = None,
                             confirm_stopped: Callable[[ExecutionIdentity], StopEvidence | None] = _execution_unconfirmed
                             ) -> ExecutionProfile:
    """Assemble dormant trusted configuration; does not enable JobService."""
    return ExecutionProfile(profile_id, repository_aliases,
        OpenHandsJobRunner(endpoint, token_factory, llm_factory, transport_factory),
        authorize, confirm_stopped)
