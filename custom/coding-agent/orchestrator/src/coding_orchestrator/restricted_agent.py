"""Pinned SDK adapter: native tool initialization is deliberately finish-only.

OpenHands 1.51.0 has no per-agent switch for profile-driven vision fallback.
Keep this override small and recheck it whenever the SDK pin changes. MCP tools
are registered separately by LocalConversation and still pass the backend's
exact runtime contract check before the LLM loop runs.
"""
from __future__ import annotations

from pydantic import PrivateAttr

from openhands.sdk import Agent
from openhands.sdk.conversation import ConversationState
from openhands.sdk.tool.builtins import FinishTool

from .backend import BackendContractError


class RestrictedOpenHandsAgent(Agent):
    _dispatch_actions: object = PrivateAttr(default=None)

    def bind_workspace_dispatch(self, actions):
        if self._dispatch_actions is not None:
            raise BackendContractError("SDK dispatch already bound")
        actions.bind_tools(super().tools_map)
        self._dispatch_actions = actions

    @property
    def tools_map(self):
        tools = super().tools_map
        return tools if self._dispatch_actions is None else self._dispatch_actions.bind_tools(tools)

    def _initialize(self, state: ConversationState) -> None:
        with self._tools_lock:
            if self._initialized:
                return

            if (
                self.tools
                or self.include_default_tools != ["FinishTool"]
                or self.agent_context is not None
            ):
                raise BackendContractError(
                    "Restricted OpenHands agent requires no native tools or "
                    "agent context and only the FinishTool default"
                )

            # Do not call AgentBase._initialize: it auto-loads tools from saved
            # profiles even when include_default_tools contains only FinishTool.
            tools = FinishTool.create(state)
            if len(tools) != 1 or tools[0].name != "finish":
                raise BackendContractError("Unexpected OpenHands FinishTool contract")

            self._tools = {"finish": tools[0]}
            self._initialized = True
