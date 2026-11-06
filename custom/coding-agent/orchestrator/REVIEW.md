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
test gating. Twenty-one deterministic scenarios cross real JWT verification, review
routes, HTTP transport, worker limits/cleanup, Git diff collection, CLI and SDK
finish/evidence validation. The actual application development wrapper, JWT
strategy, ban and capability middleware run against synthetic user/capability/ban
storage and fake model responses. Temporary repositories have real stacked base/head commits, hostile
content and no remotes; empty auth stores are checked after each case.

Completion, delivery disconnect/retrieval, cancellation, stale selection, owner
switch, unknown identity, expiry, malformed/disabled development settings, user
state, bans, capability denial, tenant repository discovery and caller spoofing are covered. The expiry case advances the
server clock, rather than waiting ten minutes. Local browser acceptance exercises
actual React/AuthContext/Axios behavior separately; this CI runner has no browser
and does not prove UI event ordering, persistent authentication/bans, remote-head
freshness, restart recovery, live subscription compatibility or activation.

## Development-only application wiring (default off)

The historical checkpoints above describe earlier unregistered components. The
application now mounts the existing panel at `/reviews` under its authenticated
root layout and the thin router at `/api/reviews`. The route returns configuration
unavailable unless **both** `NODE_ENV=development` and
`CODING_REVIEW_DEVELOPMENT=true` are present and every setting below validates.
Production mode cannot enable this development gate. No setting is installed or
enabled by this change; no credentials or service listener are provisioned.

The server reads these explicit environment settings at startup:

| Setting | Requirement |
| --- | --- |
| `CODING_REVIEW_URL` | Existing reviewed service URL, HTTPS or literal HTTP loopback, exact `/review` path, no query/fragment/userinfo |
| `CODING_REVIEW_TOKEN` | Explicit 32–256 character URL-safe transport token; never sent to the browser |
| `CODING_REVIEW_MODEL` | Explicit model ID matching the service |
| `CODING_REVIEW_REPOSITORIES` | Strict JSON array of 1–64 `{ "id": "fixture", "tenantId": "tenant-a" }` entries, at most 16 KiB |

Omit `tenantId` only for the application's non-tenant principal. It is never a
wildcard. Duplicate ID/tenant pairs, unknown fields, paths, invalid identities or
malformed settings disable the entire gate. Repository IDs must also exist in
the service's independent ID/path allowlist and authorization callback.

The existing JWT strategy resolves the current stored user; existing ban checks,
tenant context and `ACCESS_ADMIN` capability policy precede discovery and all
operations. This conservative development pilot adds no capability grants or
authentication framework. GET `/api/reviews/config` exposes only repository IDs
for that trusted tenant; it exposes no paths, service URL, token or model settings.
Start and retrieval recheck the server repository list. Cancellation retains
service owner checks, allowing the owner to clean up a run even if its repository
is removed from the list. Request JSON cannot supply principal, tenant or policy.

Open `/reviews` directly while authenticated. The panel waits for successful
server discovery; discovery failures keep it disabled. Its query cache is scoped
to user and tenant, and identity changes abort pending discovery. Existing panel
controls retain immutable commit selection, no automatic replay, explicit
retrieval/cancellation, inert findings and human-review-required outcomes.

Base/head still identify the **selected local commits**. This slice does not
fetch a current remote PR head or establish that the selection is fresh. Recovery
is process-local and expires after ten minutes; restart loses retained outcomes
and cannot prove a remote provider stopped. Existing visible limitations remain.
There is no publication path. Production activation, external containment,
restart reconciliation and separately authorized live compatibility remain open.

Verification uses synthetic repositories/users, empty auth stores and fake SDK
responses only. New config and composed-page tests cover fail-closed settings,
ready authentication, tenant/user changes, discovery, recovery and cancellation;
the contract runner exercises the actual app wrapper and established middleware.
No model call, login, production executor, NAS or deployment is involved.


### PR identity development follow-up

The authenticated development router now supports a bounded, public-GitHub-only
selection lookup and exact-pair comparison. See
[the HTTP contract](../../../packages/api/src/coding/review/HTTP.md#development-pr-identity-lookup).
The panel consumes this lookup and binds PR number/repository ID to the immutable
run request. Admission and result delivery recheck actual base/head; stale or
unverifiable outcomes withhold findings while cancellation remains available.
The metadata lookup itself performs no model call, Git fetch, publication or
credential access. All Stage 5 execution controls remain in place. Tests use fake
provider responses and synthetic GitHub metadata only. Checks are point-in-time;
private GitHub access and durable restart recovery remain outside this slice.

## Optional durable review recovery (development, default off)

The service can explicitly receive a `journal` opened by `createReviewJournal`
from `@librechat/api/coding`. Configure absolute Linux paths for `python`
(stdlib Python), `sourceRoot` (the orchestrator `src` directory), and `path`
(a dedicated private SQLite database). Await journal creation before accepting
requests and call `journal.close()` during shutdown. This does not add a route,
environment switch, production bootstrap, or automatic activation. Keep the
existing service authentication, repository authorization, PR identity checks,
bounded worker, cancellation, cleanup, result validation and finish-only backend.

The adapter reuses the orchestrator `JobStore` through a single lock-owning,
credential-free Python helper. It persists the external review UUID, owner,
tenant, repository alias, exact base/head, PR binding and configured model in
the admission transaction before dispatch. Successful validated outcomes are
committed after worker settlement and cleanup, before delivery. Completed
recovery still checks the current PR identity. An interrupted response has no
findings or freshness claim and remains observable without a GitHub lookup.

Restart never repeats model dispatch. Previously active jobs become explicit
`interrupted` records; unresolved execution reservations block new admissions.
A helper failure fences its TS service generation permanently, cancels local
work and rejects pending operations without retrying mutations or reconnecting.
Only successful settled execution supplies trusted stop evidence. Failures,
timeouts, cancellation without successful settlement, and process loss do not
prove external quiescence and remain quarantined. If cancellation wins the
terminal commit after successful worker settlement, persist cancelled, withhold
findings, and release the reservation using that settlement evidence.

Cancellation before admission persists a tombstone without taking an execution
slot. No UUID may be replayed, including after finding expiry. Result payloads
expire after 600 seconds (on access/admission and a 30-second maintenance sweep);
identity tombstones remain. Admission is bounded to 64 retained result payloads
and 1,024 lifetime records, failing closed at capacity. This milestone includes
no deletion/reset, automatic reconciliation or reservation-release endpoint.
Do not remove the journal to clear a quarantine: that loses no-replay evidence.

Process crashes can leave orphaned execution or scratch directories. This
milestone deliberately does not infer their termination or automate crash
cleanup; trusted reconciliation and retention/tombstone lifecycle policy remain
follow-up work before activation. Use a dedicated database, not the general job
store database. The helper imports only stdlib persistence code and receives no
provider credentials, executor access or publication capability.

Offline tests use real SQLite/helper processes, fake workers/provider outputs
and empty auth directories. They cover service/helper loss, both commit-before-
acknowledgement windows, owner/tenant/PR/model mismatch, orphaned execution,
precancellation, cancellation racing completion, expiry with no replay, lock
contention and subsequent admission after trusted settlement. No live model or
GitHub publication is part of those fixtures.

## Live-worker diagnostic and reconciliation follow-up (development only)

The separate review worker now supports an **optional operator-owned** `onDiagnostic`
callback. The application transport passes its validated review UUID into the
worker, allowing callback events to be correlated with the durable admission.
Events contain only fixed stages (`evidence_validated`, `provider_ready`,
`conversation_started`, `conversation_finished`, `result_validated`,
`schema_validated`) or child-exit fields (exit code, termination signal,
stdout/stderr byte counts, fixed outcome classification). No child stderr,
source code, model response, credentials, paths or arbitrary error messages
are forwarded. The Python child emits stage labels on a private fd3 pipe;
unknown labels and excess diagnostics are ignored. Listener exceptions cannot
change a review outcome or release a reservation. Operators must explicitly
configure and secure a suitable log sink; there is no default recording of
these events. A stage label is a local progress observation, **not** proof
that a provider received or finished a request.

**The current durable safety policy is intentionally unchanged.**
A missing/failed child, timeout, aborted response, supervisor restart or
empty scratch directory cannot establish that an external execution has
stopped. These cases must remain `interrupted` with an unresolved reservation.
This change adds no approval rearming, journal deletion/reset, automatic retry,
runtime activation, GitHub publication, or reconciliation endpoint.

Before implementing a trusted reconciliation mutation, specify and test
an authenticated supervisor attestation covering the exact review UUID,
generation, owned process/process group, child closure, prevention of delayed
dispatch, and any provider-side execution uncertainty. A local process
exit alone is insufficient for provider-side quiescence. Keep the
quarantined record visible and deny new dispatch if evidence is incomplete.
A separate reviewed design and explicit operator approval are required before
introducing any reservation-release operation.

Run offline Python and API worker/restart regressions against this development
branch before deployment. The historical interrupted live review must not
be replayed; retain its SQLite database and consumed pilot approval marker.

### Explicit private diagnostic recording (development only)

The createReviewDiagnosticLog factory is exported from @librechat/api/coding.
It does nothing until an operator explicitly constructs it and supplies its
onDiagnostic callback to the worker configuration. This change installs no settings,
log directory, listener, service bootstrap, or environment activation switch.

Example composition, with operator-selected paths and existing service config:

~~~ts
const log = await createReviewDiagnosticLog({
  directory: operatorSelectedEmptyPrivateDirectory,
  protectedRoots: [
    ...workerConfig.repositories.values(),
    workerConfig.authRoot,
    workerConfig.scratchRoot,
    journalDirectory,
  ],
  maxBytes: 1048576,
  maxPendingRecords: 64,
});
const handler = createReviewService({
  ...serviceConfig,
  worker: { ...workerConfig, onDiagnostic: log.onDiagnostic },
});
// Only during separately managed operator shutdown, after stopping admission:
// await log.close();
~~~

All protected roots must already exist and be absolute. The operator must list
every repository, credential, scratch and journal root, including any additional
runtime-state directories. The sink rejects overlap in either direction.
The directory must already exist, be empty, be owned by the process UID, and have
mode 0700. Symlink components and Git checkout/worktree ancestry are rejected.
The fixed file review-diagnostics.jsonl is exclusively created with mode 0600,
O_NOFOLLOW and O_EXCL; existing files, links and nonregular entries are not opened.
Concurrent constructors cannot share a log. No chmod, truncation, append-on-restart,
rotation, automatic deletion, or retention cleanup is performed.

The operator owns storage, access and retention. Keep these files on private local
storage outside shared/synced folders. UUIDs and timestamps remain operational
metadata, even though source and secrets are excluded. Checks assume a trusted
operator and stable filesystem ancestry, not hostile concurrent path replacement
or malicious code running under the same UID.

Records are reconstructed from fixed scalar fields, never serialized from the
input object. Schema version, UTC timestamp, sequence, UUID-or-null, allowlisted
stage/classification, exit code/signal and capped byte counters are permitted.
Unknown fields are omitted; invalid events are dropped; invalid UUIDs become null.
Counters saturate at the worker stream budgets (128000/64000), not exact overflow
sizes. Records cannot exceed 1024 bytes. No raw errors, stdout, stderr, findings,
source, provider replies, user/tenant identities, paths or credentials are stored.
The worker also sanitizes direct-caller IDs before invoking any observer.

A child_exit classification of success means only that the child exited zero.
It precedes response validation and cleanup and is not successful review
settlement. Even schema_validated precedes cleanup and durable commit.
Every stage is an observation, never provider completion or trusted stop evidence.
No diagnostic event authorizes reservation release, reconciliation, retry,
approval rearming, or replay.

Writes are serialized asynchronously, with at most 64 pending records by default
(configurable 1–256) and a lifetime file budget of 1 MiB by default (1024 bytes
through 16 MiB). Queue pressure drops events; capacity stops further recording.
Write failure stops recording without retry or fallback logging. The health()
method exposes only fixed state and counters; it is not an HTTP endpoint.
Review execution never awaits writes or close. The close() method is idempotent
and drains accepted writes; a stalled filesystem can stall this operator shutdown
await, but cannot grow the queue without bound or block review execution.
Process termination may lose queued records or leave a final partial line:
this is best-effort diagnostics, not a durable audit journal. Retain the file and
choose a fresh private directory for a later explicitly authorized logging session.

Offline regression fixtures use disposable directories and SQLite databases,
synthetic child scripts and fake SDK output. Restart fixtures exercise logging
during quarantine, no-replay and crash recovery, including closed/capacity sinks.
No existing review database, approval marker, running service or provider account
is needed. The historical interrupted review remains untouched.

#### Private sink offline validation — 15 October 2026 (Sydney)

Implemented from add6ffcb0561361353b9e779c78b598052dc5b08 in the separate
pr234-private-diagnostics worktree on development/pr234-private-diagnostics.

- Established guarded Python offline runner: 395 passed.
- Four newly added mocked fd3 Python tests: 4 passed separately.
- All six review Jest suites: 183 passed.
- Full guarded offline contracts/restart runner: 33 passed, including three new
  logging/quarantine/no-replay scenarios.
- Strict targeted TypeScript (sink, worker and their tests), changed-file ESLint,
  coding export JavaScript/declaration build, and git diff --check: passed.
- Data-provider JavaScript/types and data-schemas builds: passed.
- Full API build emitted JavaScript but failed declaration generation at the
  unchanged stream/jobStoreCapabilities.ts:11 with TS9010 (missing explicit
  exported variable annotation under isolatedDeclarations). No unrelated stream
  fix was included. The targeted coding export declaration build passed.

Validation reused installed Node v24.16.0, TypeScript/Jest and temporary build
tooling through links in this worktree only; no packages were downloaded and no
shared dependency, manifest, lockfile or active-service configuration changed.
The existing winston and rotation plugin were resolved from the same installed
tooling tree to avoid duplicate logger instances. Generated build outputs are
local validation artifacts, not activation.

The original acceptance worktree stayed clean at the pinned commit. The original
interrupted review 601ea173-850c-482a-bc8d-8ed05ac8aabf, its SQLite reservation,
consumed approval marker and running review services were not opened or changed.
No external model review, retry, quarantine clearing, merge, deployment, NAS or
production operation was performed. Tests restarted only their own disposable
synthetic service/helper processes.

#### Rebase onto the upstream Python P2 fix

The private logging branch was rebased onto PR #234 commit
4cf2f08fa605c2a02f991fdf8c39dad5f90b60db. The former local Python correction
9ae3756dff93524ccd6a1c3bf8919475a931e267 was dropped as superseded.
The upstream backend, CLI and their success/failure regression tests are retained
byte-for-byte; the alternate local callback helper and duplicate tests are not
part of this feature diff. The logging-specific fd3 test now asserts that unknown
labels are silently dropped, matching the upstream outcome-neutral writer.

The diff against PR #234 is limited to the explicit private sink, its public
exports, worker correlation-ID redaction, offline logging/worker/restart tests
and this operator documentation. It adds no runtime activation or recovery
mutation. The original interrupted review, journal/quarantine, consumed approval,
running services and original acceptance worktree remain outside this work.

The earlier TS9010 limitation was reproduced independently on an unchanged
add6ffcb baseline snapshot with the same Node 24.16.0 / tsdown 0.22.2 / rolldown
1.1.5 tooling: full API declaration generation exited 1 at
stream/jobStoreCapabilities.ts:11:14. That file and both build configurations
were byte-identical to the baseline Git objects. No stream fix is included here.

Rebased acceptance on 15 October 2026 (Sydney):
54 affected Python review tests passed under the established isolated-state,
loopback-only guard; all 183 tests in the six review Jest suites passed; all 33
full offline contract/restart scenarios passed. Strict targeted TypeScript,
changed-file ESLint, coding-export JavaScript/declarations and git diff --check
passed. The private logging implementation and TypeScript/restart regressions
were verified identical to cb89eadb; upstream Python implementation and P2 tests
were verified identical to 4cf2f08fa. Only the private fd3 unknown-label assertion
was adapted. No model or live review service participated in these checks.
