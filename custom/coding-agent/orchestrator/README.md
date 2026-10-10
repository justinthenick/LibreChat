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

## Optional execution-job boundary (not activated)

`coding_orchestrator.jobs` adds transport-neutral `start_run`, `get_run` and
`cancel_run` operations. They are disabled by default. There is no listener,
CLI activation command or registered production execution profile. The Google
Pilot, LibreChat agent selection and Synology startup remain unchanged.

An embedding application must supply a private SQLite state path, a trusted
authenticated user/tenant `Principal`, and an explicitly enabled
`ExecutionProfile`. A principal object is not authentication: the future
LibreChat adapter must derive it from existing auth/ACL middleware, never from
request JSON. The profile supplies repository authorization, a static trusted
runner and a nonblocking check that its owned execution has stopped. Requests
cannot choose credentials, endpoints, filesystem paths, modules or commands.
Keep profile code/import paths and state outside model-editable worktrees.

`JobRequest` supplies the prompt, repository alias/task mode, owner-scoped
idempotency key, generation ID/epoch and lowerable limits. Maximum limits are ten
physical provider requests and 300 seconds from admission. Reviewed runners must
call `WorkerControl.before_provider_request()` immediately before each physical
dispatch, disable retries/fallback, and enforce repository/task scope. The job
layer does not automatically instrument arbitrary callables. No live profile,
ambient credential discovery or login is installed here. These bounds are not
token or spending caps.

SQLite admission/transitions are atomic, with an exclusive service-instance lock
and one active slot. Repeating an identical owner/key/request returns its existing
job; changing the payload conflicts. Prompt text is not persisted in the job
database. Public status excludes owner identities and internal fingerprints.
Explicit cancellation records cancelling before stopping dispatch. It becomes
cancelled only after local and profile-owned execution are confirmed stopped;
otherwise it is interrupted with `execution_stop_unconfirmed`. Generation epochs
fence stale aborts, and cancellation cannot be overwritten by late completion.

Workers isolate environment/HOME/state, enforce a parent deadline plus a kernel
alarm, and stop their owned process group before reaping the leader. This is
process supervision, not a repository/network sandbox. Remote execution and
processes escaping the session require separate profile lease reconciliation.
After restart, active records become interrupted and are never replayed; this
does not prove remote work stopped. Before activation, the embedding supervisor
must reconcile old leases before admitting new work. No automatic record or
artifact deletion is performed.

`EvidenceCollector` accepts matched SDK action/observation identities and keeps
task/source metadata, bounded diff/status and check exit/truncation details plus
output hashes. Exploratory contents and finish prose are not retained. A passing
rerun may supersede its baseline failure, but an overlapping or pre-patch check
cannot verify a later mutation. `observed_checks_status`, `evidence_complete` and
job completion are distinct; finish alone never proves tests passed. Partial
evidence survives failure/cancellation, with consistent UTF-8 JSON limits through
collection, IPC and storage.

`OpenHandsBackend.run(..., on_event=callback)` exposes real SDK events without
changing default CLI behavior or the exact nine-executor-tools-plus-finish map.
The offline tests cover races/recovery, worker deadlines/descendants, matched
evidence and a real pinned SDK job using `TestLLM` and loopback MCP. They use no
Docker, provider credentials or live model calls.

A later LibreChat client adapter must reuse GenerationJobManager for chat/SSE
replay and durable message publication, propagate authenticated ownership and
explicit aborts, fence late events by generation epoch, and await the existing
persistence barrier before FINAL. SSE disconnect is not automatically cancel.
Chat resume, steering, approvals, maintenance tools and skill parity are not
implemented by this job boundary.

### Dormant SDK execution profile

`openhands_profile.create_openhands_profile` assembles a reusable SDK runner for
the job boundary. It is not registered with the preview API, enabled by an
environment flag, or exposed through a new CLI command. Tests are its only
checked-in caller. Trusted server code must supply repository authorization,
the endpoint, and fresh child-side token/LLM factories. Factories must not capture
credentials: the worker serializes its runner before starting. This module does
not discover credentials, log in, reuse an operator's auth cache or provision an
executor. It accepts only the existing `openai/gpt-5.6-sol` Codex route.
SDK subscription LLM objects are rejected: their separate credential discovery,
refresh and account-header validation can make requests before the guarded
inference transport. Integrating a reviewed authentication boundary remains a
prerequisite for live subscription use. The injected LLM in the offline fixture
contains only synthetic credentials and never invokes that path.

`BoundedResponses` binds one synchronous SDK LLM instance to an owned HTTP client.
It checks the exact destination/model and calls the worker's request gate
immediately before each physical dispatch. SDK/LiteLLM retries, prompt caching,
fallback and auth-refresh callbacks are disabled; async/chat inference and a
second dispatch within one logical call fail closed. Provider/parser failures
are sticky, including errors the SDK would otherwise catch and retry on another
turn. The existing SDK parses
responses. The parent worker deadline still bounds the whole job; these controls
are not token or subscription-usage caps. The adapter relies on the pinned SDK
and LiteLLM's synchronous `HTTPHandler` interface, which the real-path regression
tests exercise. Dependency updates must retain those tests.

Before tool dispatch, the profile checks the selected repository and explicit
task mode, permits only the observed task ID, and rejects patches in read-only
mode. Repository inventory and multi-action responses are rejected. Under the
pinned SDK the entire action batch is emitted before execution, so a denied
action prevents even earlier actions in that batch from reaching MCP. Evidence
continues to use matched action/observation IDs; errors, limits and cancellation
retain partial evidence and never make finish prose count as successful checks.

The offline integration test runs JobService, its child worker, the actual SDK,
a fake physical provider transport and a loopback MCP fixture. It creates a
synthetic worktree, observes a failing check, applies one exact trusted patch,
reruns the same check successfully, and verifies diff/status evidence plus the
unchanged source. Only fixed synthetic code executes in this fixture; it is not
a sandbox for arbitrary model-written code. Negative cases cover scope/batch
denials before MCP dispatch, partial evidence, limits and uncertain stops.

Live activation remains blocked on admission quarantine and remote execution
lease/restart reconciliation. The default stop confirmer always returns false;
local worker exit does not establish remote executor stop. The synthetic fixture
can confirm its own synchronous ledger, but that proof does not transfer to a
live executor. The current job service releases its active slot after recording
an interrupted run, so a live embedding must first reconcile outstanding work
before admitting another job. This development profile does not implement that
activation prerequisite or change the default preview API behavior.

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

The root is revalidated after tool discovery and provider initialization,
immediately before workspace allocation, and workspace ancestry is checked again
before the conversation starts. Keep the scratch root and its ancestors private
to trusted operators. These path checks are not atomic isolation against another
process concurrently replacing/moving directories or adding Git metadata between
filesystem operations.

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
# Disabled preview job-control API

The optional `/api/agents/preview` routes expose the job boundary to a future
preview interface. They are a separate API with immutable preview job IDs;
they do not create chat turns, publish chat SSE events, or persist chat history.
The existing Google Pilot and normal chat routes keep their current behavior.

The routes run after LibreChat's existing JWT authentication and ban checks.
With the default configuration they return `404 preview_jobs_disabled`.
`CODING_OPENHANDS_PREVIEW=true` alone returns `503 job_service_unavailable`:
no live transport, credentials, or execution profile are installed by this code.
The server-only `createPreviewRouter` factory accepts an explicitly supplied
transport and admission policy for integration; request JSON cannot supply them.

- `POST /jobs`: accepts `prompt`, `idempotency_key`, `scope` (repository alias
  and `read_only` or `modification` task mode), plus optional `max_requests`
  and `timeout_seconds` (defaults 10 and 300).
- `GET /jobs/:jobId`: returns an owner- and tenant-scoped snapshot.
- `POST /jobs/:jobId/cancel`: accepts an empty body and requests cancellation
  using the stored preview generation identity. A request is not proof that
  remote execution has stopped; the returned job state remains authoritative.
- Resume and steering routes reject the operation. Disconnecting HTTP does not
  cancel execution. There is no automatic transport retry or provider fallback.

Identity comes only from authenticated `req.user.id` and `req.user.tenantId`.
The Python dispatcher takes a trusted `Principal` separately from command JSON.
An eventual transport must authenticate its caller and preserve that identity;
the stdin/stdout fixture is test-only and is not a deployable auth service.
The required server admission policy must enforce repository access and, for
start, text/rate policy before dispatch. Mounting this API does not inherit the
normal chat router's moderation, conversation ACL, or message-limiter chain.
Repository authorization is checked again before returning status or cancelling.

Commands use a versioned, closed schema with a 40 KiB serialized JSON budget;
snapshots use a 256 KiB budget. The controller also checks Content-Length when
present. These are parsed-payload limits, not a replacement for the application's
global raw-body parser limit. Errors use fixed codes and responses use no-store.
An unavailable/timeout response does not establish whether remote work started
or stopped. Retain the idempotency key and job ID when reconciling that outcome.
Completion, observed check results, and complete evidence remain separate fields.

The focused test toolchain lives in `tests/preview` with an exact lockfile.
`run.cjs` uses existing Node 24 and Python interpreters plus an explicitly supplied
installed toolchain (`PREVIEW_TEST_TOOLS` and `PREVIEW_TEST_PYTHON`); it installs
nothing itself. Tests compile the real TypeScript controller, load the actual
Express routes, and exchange synthetic jobs with the real Python store/service
and supervised worker. Existing JWT verification is stubbed only to establish
test principals; these tests do not validate the application's login system.
No real repository, provider credential, or model call is used.

Before live activation, implement and review the authenticated transport and
bounded execution profile, supply the full admission policy, add the preview UI,
and verify deployment-specific cancellation/restart reconciliation. Integration
with the normal resumable chat lifecycle is a separate change.
