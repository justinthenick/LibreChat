# LibreChat coding-agent orchestrator

This package is the backend-neutral orchestration boundary above the restricted
`coding_executor` MCP service.

## Security boundary

The orchestrator does not own Git worktrees, repository mutation, command
execution, dependency provisioning, promotion, commit, push, merge, deployment,
Docker access, package installation, or arbitrary shell access.

Those responsibilities remain behind existing coding-agent boundaries.

The OpenHands backend connects only to the existing `coding_executor` MCP
endpoint and fails closed unless that server advertises exactly these nine
tools:

- `list_repositories`
- `create_task`
- `task_status`
- `list_files`
- `read_file`
- `search_text`
- `apply_patch`
- `run_check`
- `git_diff`

For an active OpenHands conversation:

- OpenHands native tools are configured as `tools=[]`.
- Only the built-in non-mutating `FinishTool` is enabled.
- A second exact allowlist filter permits only the nine executor tools plus
  `finish`.
- The initialized runtime tool map is checked again before the LLM loop runs.
- The OpenHands workspace is a temporary scratch directory outside Git
  repositories; it is never a LibreChat source or task worktree.
- The scratch directory is deleted after each run.
- Repository operations remain available only through `coding_executor`.

The executor bearer token is supplied at runtime and is never persisted by this
package.

## Local endpoints

OpenHands running directly in WSL should use a host-local executor endpoint:

    CODING_OPENHANDS_EXECUTOR_URL=http://127.0.0.1:8765/mcp

This is intentionally separate from `CODING_EXECUTOR_PUBLIC_URL`, which may be
an address advertised to external hosts such as the Synology NAS.

A separate non-Git scratch root is also required for agent runs:

    CODING_OPENHANDS_SCRATCH_ROOT=/home/user/coding-agent/openhands-scratch

## Credential-free loop smoke test

The `smoke openhands` command uses OpenHands' deterministic `TestLLM`. It runs
the real Agent/Conversation loop and real MCP transport, calls the executor's
read-only `list_repositories` operation, then invokes only OpenHands' `finish`
tool. No external LLM credentials are required for this acceptance test.

## Proxy safety

Plaintext HTTP is limited to literal loopback addresses and is rejected whenever
Python discovers a configured environment or system proxy. A NO_PROXY exemption
does not override this conservative check. Use HTTPS with proxies, or remove proxy
settings from the orchestrator process before using its loopback HTTP endpoint.
Proxy URLs and credentials are never included in this configuration error.

The endpoint and current proxy configuration are checked at construction, before
each tool probe, and again when constructing the MCP server for a conversation.
This also rejects proxy settings introduced after a backend was constructed.
