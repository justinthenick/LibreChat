from __future__ import annotations

import re
import tempfile
from ipaddress import ip_address
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import getproxies

from .backend import (
    BackendContractError,
    BackendProbe,
    BackendRunRequest,
    BackendRunResult,
)
from .provider import OpenHandsProviderConfig


EXPECTED_CODING_EXECUTOR_TOOLS = frozenset(
    {
        "list_repositories",
        "create_task",
        "task_status",
        "list_files",
        "read_file",
        "search_text",
        "apply_patch",
        "run_check",
        "git_diff",
    }
)

EXPECTED_OPENHANDS_RUNTIME_TOOLS = frozenset(
    {
        *EXPECTED_CODING_EXECUTOR_TOOLS,
        "finish",
    }
)

OPENHANDS_RUNTIME_TOOL_REGEX = (
    r"^(?:"
    + "|".join(
        re.escape(name)
        for name in sorted(EXPECTED_OPENHANDS_RUNTIME_TOOLS)
    )
    + r")$"
)

RESTRICTED_SYSTEM_PROMPT = """You are a restricted software-engineering agent.

All repository inspection and mutation MUST go through the coding_executor MCP
tools provided to you.

You do not have and must not attempt to obtain direct terminal, filesystem,
browser, Docker, package-installation, git commit, git push, git merge,
deployment, or host-control access.

The coding_executor owns repository scope, worktrees, patch application,
command allowlists, validation budgets, and mutation boundaries.

Use only the tools actually provided. Use finish when the requested work is
complete or cannot safely continue.
"""

ToolDiscovery = Callable[[str, str], Iterable[str]]


def _validate_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    parsed = urlparse(endpoint)

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path != "/mcp"
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "OpenHands executor endpoint must be an http(s) URL ending exactly in /mcp"
        )

    if parsed.scheme == "http":
        try:
            address = ip_address(parsed.hostname)
        except ValueError as error:
            raise ValueError(
                "OpenHands executor endpoint may use HTTP only with a literal "
                "loopback address; use HTTPS for non-loopback endpoints"
            ) from error

        if not address.is_loopback:
            raise ValueError(
                "OpenHands executor endpoint may use HTTP only with a literal "
                "loopback address; use HTTPS for non-loopback endpoints"
            )

        # The SDK HTTP client honors environment/system proxy settings.
        # NO_PROXY matching is intentionally not trusted for bearer-token HTTP.
        proxies = getproxies()
        if any(proxies.get(scheme) for scheme in ("http", "https", "all")):
            raise ValueError(
                "OpenHands executor HTTP requires no configured proxies; "
                "use HTTPS or remove proxy settings from the process"
            )

    return endpoint


def _build_mcp_server(endpoint: str, token: str):
    endpoint = _validate_endpoint(endpoint)
    from pydantic import SecretStr
    from openhands.sdk.mcp import MCPServer

    return MCPServer(
        transport="streamable-http",
        url=endpoint,
        headers={
            "Authorization": SecretStr(
                f"Bearer {token}"
            ),
        },
    )


def _discover_openhands_tools(
    endpoint: str,
    token: str,
) -> tuple[str, ...]:
    from openhands.sdk.mcp.utils import create_mcp_tools

    server = _build_mcp_server(
        endpoint,
        token,
    )

    with create_mcp_tools(
        {"coding_executor": server},
        timeout=30.0,
    ) as client:
        return tuple(
            tool.name
            for tool in client.tools
        )


def _validate_non_git_ancestry(path: Path) -> None:
    for candidate in (path, *path.parents):
        marker = candidate / ".git"
        head = candidate / "HEAD"
        # Bare repositories have their metadata directly in the directory.
        # Conservatively reject metadata-shaped directories without invoking
        # Git or honoring repository-location environment overrides.
        bare_metadata = (
            (head.exists() or head.is_symlink())
            and any(
                entry.exists() or entry.is_symlink()
                for entry in (
                    candidate / "objects",
                    candidate / "refs",
                    candidate / "reftable",
                )
            )
        )
        if marker.exists() or marker.is_symlink() or bare_metadata:
            raise ValueError(
                "OpenHands scratch/workspace must not be inside a Git repository"
            )


def _validate_scratch_root(value: str | Path) -> Path:
    raw = Path(value).expanduser()

    if raw.is_symlink():
        raise ValueError(
            "OpenHands scratch root must not be a symbolic link"
        )

    # Resolve existing ancestors before mkdir so invalid configuration cannot
    # create even an empty scratch directory inside a repository.
    _validate_non_git_ancestry(raw.resolve(strict=False))
    raw.mkdir(
        mode=0o700,
        parents=True,
        exist_ok=True,
    )
    root = raw.resolve(strict=True)
    _validate_non_git_ancestry(root)
    return root


def _validate_run_workspace(
    value: str | Path,
    scratch_root: Path,
) -> Path:
    raw = Path(value)

    if raw.is_symlink():
        raise ValueError(
            "OpenHands run workspace must not be a symbolic link"
        )

    workspace = raw.resolve(strict=True)

    if workspace.parent != scratch_root:
        raise ValueError(
            "OpenHands run workspace must resolve directly beneath "
            "the validated scratch root"
        )

    _validate_non_git_ancestry(workspace)
    return workspace


class OpenHandsBackend:
    """OpenHands agent loop restricted to coding_executor MCP."""

    name = "openhands"

    def __init__(
        self,
        endpoint: str,
        token: str,
        *,
        discover_tools: ToolDiscovery | None = None,
        llm: Any | None = None,
        provider: OpenHandsProviderConfig | None = None,
        scratch_root: str | Path | None = None,
    ) -> None:
        self._endpoint = _validate_endpoint(endpoint)

        if not token:
            raise ValueError(
                "coding executor bearer token is required"
            )

        self._token = token
        self._discover_tools = (
            discover_tools
            or _discover_openhands_tools
        )
        if llm is not None and provider is not None:
            raise ValueError("Specify either an injected LLM or a provider, not both")
        self._llm = llm
        self._provider = provider
        self._scratch_root = (
            _validate_scratch_root(scratch_root)
            if scratch_root is not None
            else None
        )

    def probe(self) -> BackendProbe:
        _validate_endpoint(self._endpoint)
        names = tuple(
            sorted(
                {
                    str(name).strip()
                    for name in self._discover_tools(
                        self._endpoint,
                        self._token,
                    )
                    if str(name).strip()
                }
            )
        )

        discovered = set(names)
        missing = (
            EXPECTED_CODING_EXECUTOR_TOOLS
            - discovered
        )
        unexpected = (
            discovered
            - EXPECTED_CODING_EXECUTOR_TOOLS
        )

        if missing or unexpected:
            details: list[str] = []

            if missing:
                details.append(
                    "missing="
                    + ",".join(sorted(missing))
                )

            if unexpected:
                details.append(
                    "unexpected="
                    + ",".join(sorted(unexpected))
                )

            raise BackendContractError(
                "OpenHands coding_executor tool contract mismatch: "
                + "; ".join(details)
            )

        return BackendProbe(
            backend=self.name,
            tool_names=names,
        )

    def _build_agent(self):
        llm = (
            self._provider.build_llm()
            if self._provider is not None
            else self._llm
        )
        if llm is None:
            raise BackendContractError(
                "OpenHands LLM is not configured"
            )

        from .restricted_agent import RestrictedOpenHandsAgent

        return RestrictedOpenHandsAgent(
            llm=llm,
            tools=[],
            include_default_tools=[
                "FinishTool",
            ],
            mcp_config={
                "coding_executor": _build_mcp_server(
                    self._endpoint,
                    self._token,
                ),
            },
            filter_tools_regex=(
                OPENHANDS_RUNTIME_TOOL_REGEX
            ),
            system_prompt=(
                RESTRICTED_SYSTEM_PROMPT
            ),
        )

    def run(
        self,
        request: BackendRunRequest,
    ) -> BackendRunResult:
        prompt = request.prompt.strip()

        if not prompt:
            raise ValueError(
                "agent prompt must not be empty"
            )

        if not (
            1
            <= request.max_iterations
            <= 100
        ):
            raise ValueError(
                "max_iterations must be between 1 and 100"
            )

        if self._scratch_root is None:
            raise BackendContractError(
                "OpenHands scratch root is not configured"
            )

        # Revalidate immediately before every run. A long-lived backend must
        # not trust a scratch path that has changed since construction.
        scratch_root = _validate_scratch_root(
            self._scratch_root
        )

        # Fail closed before starting an LLM-driven loop.
        self.probe()

        from openhands.sdk import Conversation
        from openhands.sdk.conversation.response_utils import (
            get_agent_final_response,
        )
        from openhands.sdk.event import ActionEvent

        agent = self._build_agent()

        # Discovery and provider initialization may block or change the root.
        # Recheck after both, immediately before allocating the workspace.
        scratch_root = _validate_scratch_root(self._scratch_root)

        with tempfile.TemporaryDirectory(
            prefix="run-",
            dir=scratch_root,
        ) as workspace:
            workspace_path = _validate_run_workspace(
                workspace,
                scratch_root,
            )

            conversation = Conversation(
                agent=agent,
                workspace=workspace_path,
                visualizer=None,
                max_iteration_per_run=(
                    request.max_iterations
                ),
                stuck_detection=True,
            )

            try:
                # send_message() performs lazy agent/MCP
                # initialization but does not execute the loop.
                conversation.send_message(prompt)

                runtime_names = tuple(
                    sorted(
                        conversation.agent.tools_map
                    )
                )

                if (
                    set(runtime_names)
                    != EXPECTED_OPENHANDS_RUNTIME_TOOLS
                ):
                    raise BackendContractError(
                        "OpenHands runtime tool contract mismatch: "
                        + repr(runtime_names)
                    )

                conversation.run()

                action_tools = tuple(
                    event.tool_name
                    for event
                    in conversation.state.events
                    if isinstance(
                        event,
                        ActionEvent,
                    )
                )

                forbidden = (
                    set(action_tools)
                    - EXPECTED_OPENHANDS_RUNTIME_TOOLS
                )

                if forbidden:
                    raise BackendContractError(
                        "OpenHands executed forbidden tools: "
                        + ",".join(
                            sorted(forbidden)
                        )
                    )

                status = (
                    conversation
                    .state
                    .execution_status
                    .value
                )

                final_response = (
                    get_agent_final_response(
                        conversation.state.events
                    )
                )

                if status != "finished":
                    raise BackendContractError(
                        "OpenHands conversation did not finish: "
                        + status
                    )

                return BackendRunResult(
                    backend=self.name,
                    execution_status=status,
                    final_response=final_response,
                    runtime_tool_names=(
                        runtime_names
                    ),
                    action_tools=action_tools,
                )
            finally:
                conversation.close()
