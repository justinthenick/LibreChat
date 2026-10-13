"""Review-only isolation adapter for openhands-sdk==1.51.0.

LocalConversation loads ambient plugins (including hooks) before initializing
tools. Suppress that loader, rather than checking tools after hooks have run.
Re-audit these private hooks whenever the SDK pin changes.
"""

from openhands.sdk.conversation.impl.local_conversation import LocalConversation

from .backend import BackendContractError


class ReviewConversation(LocalConversation):
    def _ensure_plugins_loaded(self) -> None:
        if (self._plugin_specs or self._pending_hook_config is not None
                or self.agent.mcp_config or self.agent.agent_context is not None):
            raise BackendContractError("Review plugins, hooks and MCP are forbidden")
        self._plugins_loaded = True

    def _register_file_based_agents(self) -> None:
        return

    def _runtime_mcp_tools_for_agent(self):
        if self.agent.mcp_config:
            raise BackendContractError("Review MCP is forbidden")
        return []

    def load_plugin(self, plugin_ref: str) -> None:
        raise BackendContractError("Review plugins are forbidden")
