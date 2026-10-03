from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class BackendContractError(RuntimeError):
    """The selected backend does not satisfy the coding-agent contract."""


@dataclass(frozen=True)
class BackendProbe:
    """Read-only evidence that an agent backend satisfies its runtime contract."""

    backend: str
    tool_names: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "tool_count": len(self.tool_names),
            "tool_names": list(self.tool_names),
        }


@dataclass(frozen=True)
class BackendRunRequest:
    """One bounded agent run."""

    prompt: str
    max_iterations: int = 12


@dataclass(frozen=True)
class BackendRunResult:
    """Evidence returned by a completed backend run."""

    backend: str
    execution_status: str
    final_response: str
    runtime_tool_names: tuple[str, ...]
    action_tools: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "execution_status": self.execution_status,
            "final_response": self.final_response,
            "runtime_tool_names": list(self.runtime_tool_names),
            "action_tools": list(self.action_tools),
        }


class AgentBackend(Protocol):
    """Backend-neutral coding-agent orchestration contract."""

    name: str

    def probe(self) -> BackendProbe:
        """Validate this backend without mutating a repository."""

    def run(self, request: BackendRunRequest) -> BackendRunResult:
        """Execute one bounded agent run."""
