"""Pinned SDK executor binding to a trusted, child-created dispatch capability.

Only the host factory may bind a claim/transport. The capability accepts a stable
action ID, tool name, arguments and remaining caller time; it must deliver to the
parent-owned SDKWorkspace ledger without retrying. This module registers nothing.
"""
from openhands.sdk.tool import ToolExecutor
from dataclasses import dataclass, replace
import hashlib
import json

from .job_worker import WorkerCancelled, WorkerDeadline, WorkerLimit
from .openhands_profile import OpenHandsProfileError


@dataclass(frozen=True)
class ClaimDispatch:
    """Picklable binding; the factory creates transport only inside the child.

    Factories must not capture credentials or the parent-owned ledger. Claim is
    correlation data, not authorization; the receiving host authenticates it.
    """
    claim: object
    factory: object

    def __call__(self, context, control):
        from coding_executor.executions import Claim
        if type(self.claim) is not Claim or not callable(self.factory):
            raise OpenHandsProfileError("sdk_dispatch_claim")
        identity = self.claim.identity
        if (context.job_id != identity.job_id or context.execution_id != identity.execution_id
                or context.repository_alias != identity.repository_alias
                or context.task_mode != identity.task_mode or identity.task_mode != "read_only"):
            raise OpenHandsProfileError("sdk_dispatch_scope")
        control._check()
        return self.factory(self.claim, control)


def bind_sdk_runner(runner, claim, factory):
    from .openhands_profile import OpenHandsJobRunner
    if type(runner) is not OpenHandsJobRunner or runner.dispatch_factory is not None:
        raise ValueError("unbound SDK runner required")
    return replace(runner, dispatch_factory=ClaimDispatch(claim, factory))


def _encoded(value):
    result = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(result.encode()) > 49152:
        raise OpenHandsProfileError("sdk_dispatch_frame_limit")
    return result


class BoundActions:
    def __init__(self, dispatch, control):
        if not callable(dispatch):
            raise ValueError("trusted dispatch capability required")
        self.dispatch, self.control = dispatch, control
        self.pending = None
        self.failed = False
        self.control_failure = None

    def raise_control_failure(self):
        if self.control_failure is not None:
            raise self.control_failure from None

    def capture(self, event):
        from openhands.sdk.event import ActionEvent
        if not isinstance(event, ActionEvent) or event.tool_name == "finish":
            return
        if (self.failed or self.pending is not None or type(event.tool_call_id) is not str
                or not event.tool_call_id or len(event.tool_call_id) > 128
                or event.tool_call.id != event.tool_call_id or event.tool_call.name != event.tool_name):
            self.failed = True
            raise OpenHandsProfileError("sdk_dispatch_identity")
        action_id = hashlib.sha256(event.tool_call_id.encode()).hexdigest()
        self.pending = (action_id, event.tool_name, _encoded(event.action.data))

    def install(self, conversation):
        conversation.agent.bind_workspace_dispatch(self)

    def bind_tools(self, tools):
        from openhands.sdk.mcp.tool import MCPToolDefinition
        from openhands.sdk.tool.builtins import FinishTool
        from .openhands_backend import EXPECTED_OPENHANDS_RUNTIME_TOOLS
        self.raise_control_failure()
        if set(tools) != EXPECTED_OPENHANDS_RUNTIME_TOOLS:
            raise OpenHandsProfileError("sdk_dispatch_tool_contract")
        bound = {}
        for name, tool in tools.items():
            if name == "finish":
                if type(tool) is not FinishTool:
                    raise OpenHandsProfileError("sdk_dispatch_finish_contract")
                bound[name] = tool
                continue
            if not isinstance(tool, MCPToolDefinition):
                raise OpenHandsProfileError("sdk_dispatch_tool_contract")
            bound[name] = tool.set_executor(_Executor(self, name))
        return bound

    def execute(self, name, action, conversation=None):
        from openhands.sdk.mcp.definition import MCPToolObservation
        from mcp.types import CallToolResult, TextContent
        try:
            self.control._check()
            if (self.failed or self.pending is None
                    or self.pending[1:] != (name, _encoded(action.data))):
                raise OpenHandsProfileError("sdk_dispatch_action_mismatch")
            action_id, _, encoded = self.pending
            self.pending = None
            result = self.dispatch(action_id, name, json.loads(encoded),
                                   timeout_seconds=self.control.remaining_seconds())
            self.control._check()
            text = _encoded(result)
            return MCPToolObservation.from_call_tool_result(tool_name=name,
                result=CallToolResult(content=[TextContent(type="text", text=text)], isError=False))
        except (WorkerCancelled, WorkerDeadline, WorkerLimit) as error:
            self.control_failure = error
            self.failed = True
            raise
        except Exception:
            self.failed = True
            raise OpenHandsProfileError("sdk_dispatch_unconfirmed") from None


class _Executor(ToolExecutor):
    def __init__(self, actions, name):
        self.actions, self.name = actions, name

    def __call__(self, action, conversation=None):
        return self.actions.execute(self.name, action, conversation)
