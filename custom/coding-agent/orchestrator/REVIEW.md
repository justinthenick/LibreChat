# Code Review Agent: Stage 4 checkpoint

Development branch: `feature/code-review-agent-v0` in the Clare review worktree.
Stages 1–3: `a6f15a63b`, `829c2dbe0`, `b1eba33db`.

## Review boundary

The operator selects a local repository and two full 40-character commit SHAs.
The base must be an ancestor of the head. Git reads use an explicit command
allowlist, a cleared environment, disabled external diff/textconv, disabled
protocol access and fsmonitor, a 30-second deadline, and a 256,000-byte output
limit enforced while reading. Oversized evidence fails without model access.
This subprocess reader targets the Linux/WSL runtime (selectable POSIX pipes).

Both CLI and backend apply the same 20,000-byte UTF-8 diff budget before model
execution. Source lines are split on Git's LF delimiter, preserving Unicode
line separators within a source line. Unsupported filenames, binary diffs,
mode-only changes, and malformed/empty diffs fail closed. Only added lines can
anchor findings; deletion-only changes have no eligible finding anchors.

The model sees the supplied diff as untrusted data. It has exactly `finish`.
There is no coding-executor MCP connection, native coding tool, shell, repository
workspace, or publication tool. The review-specific `ReviewConversation` skips
ambient plugin/hook and file-agent discovery before initialization and rejects
explicit plugins, hooks, MCP, and agent context. The exact runtime tool map,
finished status, and single finish action are checked before accepting output.
Unexpected attempted actions fail the review, even if followed by finish.

This adapter relies on private hooks in `openhands-sdk==1.51.0`. Re-audit it and
run the real-SDK regressions on any SDK upgrade. It does not modify the shared
coding backend, executor, global SDK loader, or any deployed service.

Each run uses a fresh private scratch workspace outside Git, no conversation
persistence, and a fresh profile directory. Scratch is removed on success or
failure. Filesystem ancestry checks assume trusted operators and are not an
OS-level sandbox against concurrent hostile filesystem changes.

## Output and request budgets

Accepted final JSON is at most 64,000 UTF-8 bytes, checked before JSON decoding.
Nesting is limited to eight levels. Duplicate keys, non-finite JSON constants,
invalid Unicode, and control characters in finding fields are rejected.
The existing schema allows at most 100 findings and 2,000 characters per text
field. Every finding must match an exact nonblank added line, filename, and
line number. A zero-finding result still requires human review.

Review LLMs have zero retries, a maximum 60-second per-attempt timeout, a maximum
30-second streaming idle timeout, and at most two conversation iterations.
The subscription adapter does not support a provider-side output-token cap.
The 64,000-byte limit is an acceptance/parser limit after the SDK receives the
answer; it does not cap provider generation, total stream memory, or billing.
Provider credential refresh is outside the inference timeout. A production
worker must additionally enforce a process-level wall-clock and memory budget.

## Operator commands

Run from `custom/coding-agent/orchestrator` using the existing virtual environment:

```sh
PYTHONPATH=src ~/.local/share/coding-agent-envs/code-review-v0/bin/python -B \
  tests/run_tests.py

PYTHONPATH=src ~/.local/share/coding-agent-envs/code-review-v0/bin/python -B \
  -m coding_orchestrator.review_cli preview \
  --repo /approved/local/repository --base FULL_BASE_SHA --head FULL_HEAD_SHA
```

For `review`, explicitly select `CODING_OPENHANDS_PROVIDER=chatgpt_subscription`,
`CODING_OPENHANDS_MODEL`, and a private non-Git
`CODING_OPENHANDS_SCRATCH_ROOT`. No executor URL or bearer token is needed.
The CLI does not load dotenv files. Do not pass credentials as CLI arguments.
Use a fresh review LLM; backend construction tightens its request settings.

If provider authentication fails, an operator can explicitly run
`python -B -m coding_orchestrator.cli login openhands` with the same provider
settings. Login is interactive operator work and is never triggered by a review.

## LibreChat integration preparation

The CLI contract and installed entry point are ready for a separate integration
change. No web endpoint or deployed agent configuration is enabled here.

1. Implement a thin TypeScript service under `packages/api` and shared DTOs in
   `packages/data-provider`, following the repository backend boundaries.
2. Accept an authorized repository identifier and immutable base/head SHAs.
   Resolve the identifier through a server-side allowlist. Never accept a user
   filesystem path, shell command, provider URL, MCP configuration, or token.
3. Run the review CLI in a dedicated isolated worker using an argument array,
   an allowlisted environment, independent credentials, and no executor token.
   Enforce wall-clock, memory, concurrency, output, and cancellation budgets.
   Keep tracing/logging disabled or explicitly approved for source-code data.
4. Require exit code zero plus valid JSON with `ok: true`, matching SHAs, and
   `status: human_review_required`. Record model/provider, commit identity,
   result, and audit metadata. Failures and partial/truncated responses must
   never be rendered as a successful clean review.
5. Render findings as untrusted text using existing UI primitives. Do not run
   suggested commands or interpret model-produced HTML. Show that evidence
   anchoring validates location, not the truth or completeness of a finding.
6. Keep publication in a separate explicitly approved action. Re-fetch PR head
   before publishing; invalidate stale reviews when it changes. GitHub publish,
   merge, and deployment each retain their existing human approval gate.

Runtime settings, account login/consent, production integration, GitHub
publication, merges, and deployment remain operator decisions. Production
executor and NAS deployment are outside this checkpoint's change scope.

## Acceptance record

Baseline: 90/90 official offline tests passed on 13 October 2026 (Sydney).
Stage 4: 114/114 official offline tests passed, adding 24 regressions. Syntax
validation and `git diff --check` also passed. The suite used isolated state and
the official loopback-only network guard; no production executor was contacted.

The first live attempt initialized cached credentials but failed with HTTP 401
and expired/refresh signals. The operator explicitly authorized device login
and completed it. After login, `chatgpt_subscription` / `gpt-5.6-sol` completed
the controlled review successfully, returning one exact-line division-by-zero
finding with `status: human_review_required`. The synthetic repository remained
clean and the review scratch directory was removed. This is a historical operator acceptance record, not a review of this port or
proof of comprehensive model quality. Generated reports are not shipped.
Reproduce offline contract checks with `tests/review/run.cjs` as described below.
The controlled live fixture uses a disposable local Git repository containing
only a synthetic Python division-by-zero regression. No LibreChat source is
sent by that fixture, and no executor or GitHub publication is involved.


## Stage 5: local LibreChat worker integration

The `@librechat/api/coding` export now includes `createCodeReviewWorker` and
`ReviewWorkerError`. Shared request/finding/result types are exported by
`librechat-data-provider`. This is a callable integration service; no HTTP route,
UI action, agent tool, production service, or NAS configuration is registered.

The operator configures absolute Python, source, authentication-store, and
private scratch paths, an explicit model, and a repository-ID-to-path map.
Use the virtualenv interpreter path (do not resolve its symlink to system
Python). The service preserves that path after checking that it exists.
The scratch directory must be owned by the worker user and mode 0700.

Each call accepts only repository ID, base SHA, and head SHA. The caller must
supply authenticated user/tenant context separately and an authorization
callback that checks access to that repository. The service denies unknown
repositories, missing principals, denied access, and authorization failures
before starting a child. Do not populate principal context from request-body
fields. Use one service instance per worker process; it permits one active
review and returns `busy` instead of maintaining an unbounded queue.

The Linux worker invokes `/usr/bin/prlimit` and the review CLI using an argument
array with no shell. It provides a cleared environment, no executor/API tokens
or proxy settings, a disposable HOME, explicit authentication-store location,
disabled telemetry, and the local model-cost map. The CLI sends diagnostics to
stderr and reserves stdout for its JSON protocol. Stderr is counted and
discarded; neither provider errors nor stderr content reach the API caller.

Limits: 150 seconds for the child process lifecycle, 4 GiB address space per
process, 120 CPU seconds per process, 16 MiB per created file, 128 descriptors,
zero core dump size, 128,000 bytes stdout, and 64,000 bytes stderr. The worker
kills the process group on cancellation, timeout, output overflow, or failure;
it also terminates leftover descendants on leader exit and removes the outer
scratch directory after process closure. The API authorization callback and
filesystem setup are outside the child timer and must have their own service
deadlines. SIGKILL or host termination of the supervisor requires an external
job reaper; in-process cleanup cannot run after supervisor death.

These are process resource limits, not a container sandbox or aggregate cgroup
memory/disk/CPU quota. A production host must still provide a dedicated service
account, restricted filesystem/network access, aggregate resource controls,
concurrency/rate limits across replicas, and cleanup after supervisor crashes.
Do not share the production coding executor's credentials or environment.

Successful exit alone is insufficient. The service validates the complete CLI
schema, UTF-8, finding count, exact requested base/head, provider, model, and
`human_review_required` status. Invalid, stale, truncated, oversized, or failed
results become a fixed error code, never a clean review. No raw source path or
credential is included in the returned result or error.

For deployment, the caller must run on the approved Linux/WSL host where the
repositories and virtualenv live. The service is not a NAS-to-WSL transport.
Adding an authenticated remote transport, request rate limits, auditing, UI,
and a stale-head check before any separately approved GitHub publication is
remaining integration work. None of those operations are enabled by this
checkpoint. Publication, merges, and deployment require human approval.

### Stage 5 verification

- Official offline Python suite: 115/115, including clean JSON stdout.
- API coding and affected stream suites: 31/31, exercising real child processes and OS resource
  limits, authorization, cancellation/process-group cleanup, concurrency,
  invalid responses, oversized streams, memory exhaustion, and timeout.
- Strict TypeScript check for changed review modules/shared DTOs and ESLint:
  passed. This targeted check is not a full monorepo typecheck.
- Data-provider, data-schemas, and full API package builds passed, including
  coding subpath declarations. This publication retains the target branch's
  stream capability type guard; the earlier isolated workaround is excluded.
  The historical stream capability regression suite passed. Missing build/logger tools
  were provisioned in temporary local tooling; shared production dependencies
  and package manifests/lockfiles were not changed.
- Full worker-to-CLI-to-provider acceptance on 13 October 2026 (Sydney):
  `gpt-5.6-sol` returned the exact-line synthetic division-by-zero finding in
  approximately nine seconds under the OS limits. Repository and scratch
  cleanup checks passed. Generated reports are excluded from publication;
  these historical live calls were not repeated during the offline port.

The local live acceptance used the operator-approved existing subscription
store. Provision independent review credentials before production integration.


## Reproducible offline composition

After the normal data-provider, data-schemas and API package builds, run:

```sh
REVIEW_TEST_PYTHON=/path/to/installed/sdk/python node custom/coding-agent/orchestrator/tests/review/run.cjs
```

The interpreter must contain this orchestrator's pinned `openhands,test` extras.
The runner installs nothing, uses fresh temporary state and permits only literal
loopback networking. The backend workflow runs it independently of selective unit
test gating. Seven deterministic scenarios cross real JWT verification, review
routes, HTTP transport, worker limits/cleanup, Git diff collection, CLI and SDK
finish/evidence validation. Only user lookup, ban checks and model responses are
fixtures. Temporary repositories have real stacked base/head commits, hostile
content and no remotes; empty auth stores are checked after each case.

Completion, delivery disconnect/retrieval, cancellation, stale selection, owner
switch, unknown identity and expiry are covered. The expiry case advances the
server clock, rather than waiting ten minutes. Local browser acceptance exercises
actual React/AuthContext/Axios behavior separately; this CI runner has no browser
and does not prove UI event ordering, persistent authentication/bans, remote-head
freshness, restart recovery, live subscription compatibility or activation.
