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
- Only the built-in non-mutating `FinishTool` is enabled. A small, per-agent
  SDK adapter initializes this tool explicitly, so saved vision profiles cannot
  inject a fallback tool. It does not scan profiles, change process-wide SDK
  state, or change the LLM's reported capabilities.
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

## Provider-controlled runs

Select the provider and model explicitly. There is no default model, provider
autodetection, or fallback to API credits:

    export CODING_OPENHANDS_PROVIDER=chatgpt_subscription
    export CODING_OPENHANDS_MODEL=gpt-5.6-sol

See `.env.example` for all settings. The CLI reads the process environment; it
does not automatically load dotenv files. Supply the executor URL, token, and
scratch root from the existing runtime configuration. Never commit credentials.

The installed OpenHands SDK must support the exact requested subscription model.
Unsupported models fail before authentication. Model catalog membership is only
a local compatibility check; a successful inference verifies actual access.

If cached subscription credentials are unavailable or unusable, explicitly run:

    coding-agent-backend login openhands

This operator-only command uses OpenHands' device-code login and consent flow.
It needs provider/model configuration but no executor token. Credentials remain
in the SDK-managed cache (by default `~/.openhands/auth`, or
`$OH_PERSISTENCE_DIR/auth`). Login success is not an inference test.

Run the checked-in, read-only acceptance prompt:

    coding-agent-backend run openhands \
      --prompt-file examples/provider-readonly.txt \
      --max-iterations 4

Run that command again to verify repeatability. Each invocation emits JSON with
the selected provider/model, execution status, exact runtime tools, action tools,
and final response. Expect the nine executor tools plus `finish` in the runtime
list, and `list_repositories`, then `finish`, in the action list. Verify the
reported tool outcome; finishing a conversation alone does not prove task success.

For other authorized tasks, provide a UTF-8 prompt file or use `--prompt-file -`
to read standard input. The iteration limit defaults to 12 and must be 1–100.
The existing executor controls still determine permitted repository operations.
The orchestrator does not grant commit, push, merge, or deployment capabilities.

For an uninstalled source checkout, use the SDK-equipped interpreter with
`PYTHONPATH=src python -m coding_orchestrator.cli` in place of
`coding-agent-backend`. No temporary Python runner is needed.

### Programmatic configuration and extension

Construct `OpenHandsProviderConfig(mode="chatgpt_subscription",
model="gpt-5.6-sol")` (or use `from_environment()`) and pass it as
`provider=` to `OpenHandsBackend`. A backend may be invoked repeatedly; each run
loads/refreshes cached credentials, creates a fresh LLM, verifies subscription
mode and the exact model, and uses the existing isolated scratch workspace.
Missing credentials or refresh failure stops the run without interactive login.

The existing injected `llm=` path remains for deterministic smoke tests and
explicit embedding. It cannot be combined with `provider=`.

Provider-specific authentication and construction live in `provider.py`,
separate from executor discovery and the restricted agent loop. A future
direct/API adapter must add an explicit mode with its own credential/endpoint
validation and tests. Today all other modes are rejected, as are
`CODING_OPENHANDS_API_KEY` and `CODING_OPENHANDS_BASE_URL`; no direct/API path is
implemented. Ambient OpenAI API credentials do not select or replace the
subscription provider.

### Tests

Using the SDK-equipped Python environment:

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
      python -m unittest discover -s tests -v

The tests exercise real SDK LLM construction with isolated, synthetic credential
stores. Network refresh/login and CLI execution boundaries are mocked where
needed; unit tests do not consume subscription usage. The real executor smoke
and real-model acceptance are separate, explicit operator commands.

## Proxy safety

Plaintext HTTP is limited to literal loopback addresses and is rejected whenever
Python discovers a configured HTTP, HTTPS, or ALL environment/system proxy.
Unrelated proxy settings (such as FTP or package-manager proxies) are ignored. A NO_PROXY exemption
does not override this conservative check. Use HTTPS with proxies, or remove proxy
settings from the orchestrator process before using its loopback HTTP endpoint.
Proxy URLs and credentials are never included in this configuration error.

The endpoint and current proxy configuration are checked at construction, before
each tool probe, and again when constructing the MCP server for a conversation.
This also rejects proxy settings introduced after a backend was constructed.

Scratch validation resolves and checks existing ancestors before creating missing
directories, then repeats the check after creation and for each run workspace.
Both ordinary Git markers and bare-repository metadata are rejected. The bare
check conservatively rejects a HEAD entry alongside objects, refs, or reftable
metadata; it does not execute Git or trust Git environment overrides.

## Credential-free regression suite and CI

Use a dedicated Python 3.12+ environment with this package's `openhands` and
`test` extras installed. Dependency installation is a separate step. Once the
reviewed dependencies are available, run from this directory:

    PYTHONPATH=src python -B tests/run_tests.py

The launcher uses disposable OpenHands state, clears inherited credentials,
uses the bundled LiteLLM model-cost map, and rejects non-loopback TCP connection
attempts. Tests use synthetic MCP tools and scripted `TestLLM` responses; they
do not contact an LLM provider, require secrets, or use a live coding executor.
This test shim is not an OS-level network sandbox. Scratch must be outside any
Git checkout, as in production; set `TMPDIR` to a suitable temporary location
before launching if your system temporary directory is inside a checkout.

The vision regression creates a temporary credential-free vision profile and
first reproduces the stock SDK's automatic `inspect_image_with_vision` injection.
It then runs the actual restricted Agent/Conversation loop and loopback MCP
transport twice, checking the exact ten-tool map, actions, and scratch cleanup.
It also proves that an unexpected runtime tool still aborts before an LLM call.
The profile fixture is isolated even under ordinary unittest discovery.

`RestrictedOpenHandsAgent._initialize` is a deliberately narrow compatibility
adapter for `openhands-sdk==1.51.0`, which has no per-agent vision-fallback opt-out.
It creates the real SDK `FinishTool`; inherited MCP registration and the exact
pre-loop contract check remain unchanged. Review this private SDK hook and rerun
the real-library regressions before changing the SDK pin. The PyPI 1.51.0 release
is tested here; the original PR's development reference commit
`84d4470acd85688b52c510532ffc83b234ebf453` is not the release tag commit.

The Coding Agent Orchestrator workflow runs this suite and syntax checks for
orchestrator/workflow changes on pull requests, including stacked branches, and
pushes to `server/synology`. It uses read-only repository permissions, no saved
checkout credentials, immutable action revisions, and no secrets. Top-level
SDK/test dependencies are pinned; transitive dependencies are not fully locked.
A passing local suite does not mean GitHub Actions has run for an unpublished patch.
