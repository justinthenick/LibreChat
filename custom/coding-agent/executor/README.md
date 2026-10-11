# LibreChat coding executor v0.1.14

This service gives a LibreChat Agent a deliberately narrow coding surface without granting access to the NAS Docker socket or the host filesystem.

## Security boundary

- Every task is created as a separate Git worktree and `agent/<task-id>` branch.
- All paths are resolved beneath that task worktree.
- Edits are unified diffs checked by `git apply --check` before application.
- Final `git_diff` output includes tracked changes and untracked regular files; it fails closed rather than returning a truncated patch.
- Shell strings are never evaluated. Only test, lint, build and `git diff --check` command prefixes are accepted.
- Child commands receive a minimal environment that excludes the MCP bearer token.
- The MCP server has no commit, push, delete-task, package-install or Docker tools. Dependency provisioning is operator-only and is not exposed through MCP.
- The container runs non-root, drops Linux capabilities, has no Docker socket and has CPU, memory and process limits.

Exploration is server-budgeted per task. Modification tasks warn at 12
`list_files`/`read_file`/`search_text` calls and block further exploration
after 16. Read-only tasks use a 24/32 profile and reject `apply_patch`.
Completion tools remain available after exploration exhaustion so modification
tasks can still patch, validate, inspect status, and return the final diff.

Repository code is still untrusted code. Running its tests can execute repository-controlled scripts inside this container. Keep secrets out of mounted repositories and review the final diff before committing or pushing.

## Host layout

Use the Linux filesystem inside WSL, not `/mnt/c`, for the repositories and worktrees:

```text
~/coding-agent/
  repos/     # manually cloned repositories that the Agent may access
  tasks/     # executor-created worktrees
  executor/  # this directory
```

## Initial setup

1. Copy `.env.example` to `.env`.
2. Generate the token with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.
3. Replace the example address with the Windows host LAN address that the Synology NAS can reach.
4. Set `CODING_REPOSITORY_HOST_PATH` and `CODING_TASK_HOST_PATH` to their absolute WSL paths. Compose mounts each directory at the identical path inside the container so Git worktree metadata remains usable from both WSL and the executor.
5. Create `repos` and `tasks`, clone only approved repositories under `repos`, and run `docker compose -f compose.example.yaml up -d --build`.
6. Confirm `curl http://127.0.0.1:8765/health` returns `{"status":"ok","version":"0.1.14"}`.

Do not expose port 8765 to the public internet. Permit it only from the NAS address in Windows Firewall.

## LibreChat configuration (after host validation)

The Synology config should use a Streamable HTTP server with a static bearer header and a single private-address exemption:

```yaml
mcpSettings:
  allowedAddresses:
    - '${CODING_EXECUTOR_HOST}:${CODING_EXECUTOR_PORT}'

mcpServers:
  coding_executor:
    type: streamable-http
    url: 'http://${CODING_EXECUTOR_HOST}:${CODING_EXECUTOR_PORT}/mcp'
    headers:
      Authorization: 'Bearer ${CODING_EXECUTOR_TOKEN}'
    requiresOAuth: false
    chatMenu: false
    serverInstructions: true
    timeout: 300000
```

Keep this server out of ordinary chat. Attach it only to the reviewed Software Engineering Agent after the executor and connectivity checks pass.

## Task inventory and cleanup

Task removal is deliberately not exposed through MCP. Run the maintenance command yourself in WSL through the executor container:

```bash
docker exec librechat-coding-executor coding-executor-tasks inventory
docker exec librechat-coding-executor coding-executor-tasks provision <task-id> --yes
docker exec librechat-coding-executor coding-executor-tasks deprovision <task-id> --yes
docker exec librechat-coding-executor coding-executor-tasks remove-clean <task-id> --yes
```

`inventory` reports clean, dirty and broken task directories plus stale Git worktree registrations. `remove-clean` refuses tasks containing tracked changes, untracked files, ignored files, invalid paths or broken repository attachment. It removes only the clean worktree and retains the `agent/<task-id>` branch.

`provision` is an operator-only LibreChat action. It requires a pristine task, validates the npm workspace shape, runs `npm ci --ignore-scripts` with the shared `CODING_TASK_ROOT/.npm-cache`, builds the internal packages, and verifies that workspace resolution remains inside the task worktree. It also refuses success if provisioning modifies tracked or ordinary untracked task content.

`deprovision` removes only reviewed dependency/build roots. It refuses unexpected ignored content, tracked content, or non-ignored untracked content inside those roots. Provisioned tasks therefore remain deliberately dirty until deprovisioned.

Stale registrations are reported but never pruned automatically. After confirming the corresponding task directory is genuinely absent, inspect and perform Git's metadata cleanup from WSL:

```bash
git -C ~/coding-agent/repos/<repository> worktree prune --dry-run --verbose
git -C ~/coding-agent/repos/<repository> worktree prune --expire now --verbose
```

Branch deletion remains a separate destructive decision.

## Human review

Executor-created task worktrees are deliberately left uncommitted. Because host and container paths match, review a task directly in WSL with:

```bash
git -C ~/coding-agent/tasks/<task-id> status --short
git -C ~/coding-agent/tasks/<task-id> diff --check
git -C ~/coding-agent/tasks/<task-id> diff
```

Host `git diff` shows tracked changes only. Use the Agent's final `git_diff` result and the complete-patch procedure in [PROMOTION.md](./PROMOTION.md) whenever the task contains `??` entries. Empty untracked files are rejected because they cannot be represented as an unstaged content patch.

A rejected command returns exit code `126` and a `command_not_allowed` result without spawning the requested process.

After review, follow [PROMOTION.md](./PROMOTION.md) for the fail-closed, human-authorised patch transfer into the source repository. The executor itself never commits, pushes, merges or promotes changes.

## Optional host maintenance

See [constrained host maintenance](../host/MAINTENANCE.md) for the separate, opt-in
MCP service. It adds approved repository refresh, health, filtered logs, retired-task
cleanup and controlled restart without changing this server's coding tool surface.
Production activation requires staging validation, an immutable lock mount, pinned
image and a separate maintenance token. Task modes and exploration counters now
survive restarts; legacy tasks without saved state default to read-only/exhausted.

## Dormant execution records (offline development)

`coding_executor.executions.ExecutionService` is a library only. It is not
imported by the MCP server or registered as a tool. The dormant orchestrator
supervisor and explicit FencedWorkspace adapter compose it; live tools and
configuration are unchanged.

A trusted embedding supervisor supplies an authority ID and bounded launch,
observe and stop callbacks. The caller must first authenticate/authorize the full
ExecutionIdentity (job/execution, user/tenant, generation/epoch, profile,
repository and task mode). This library is not authentication or a sandbox.

- `advance(identity)` durably registers a generation and seals older executions
  within the exact user/tenant/generation/profile/repository/mode lineage. It does
  not dispatch or stop anything. Epochs from unrelated lineages are incomparable.
- `start(identity, operation_id, request_sha256)` persists an operation claim,
  random attempt ID and configured authority before invoking launch once. The
  digest must bind the canonical authorized request; the future adapter must
  validate that binding before executing. The ledger stores no prompt, command,
  credential or result payload. Identical replay returns status even after seal;
  conflicting replay fails. Any unresolved operation globally blocks new claims.
- `stop(identity)` commits a seal before contacting the supervisor. An unknown
  identity gets a durable stop-before-start tombstone. New operations cannot be
  claimed after sealing. `reconcile(identity)` explicitly queries observations.
- `status(identity)` reads durable state without callbacks. Missing records are
  unknown. An execution is stopped only when sealed and all claimed operations
  have exact authoritative quiescent-and-fenced observations. Completed operations
  alone leave an execution open for another action, up to 64 operations.

The supervisor must durably fence delayed delivery of each attempt before it
reports quiescent-and-fenced; absence, local worker exit and request timeout are
insufficient. Observations must match all identity, operation, digest, attempt and
supervisor authority fields. Changing supervisor authority cannot resolve earlier
claims. A future process/transport adapter must establish this contract; the
synthetic supervisor tests do not prove any live executor has stopped.

A private owned directory (0700) holds SQLite and the exclusive owner lock (0600).
Use a trusted local filesystem with working SQLite durability and POSIX flock;
retain the directory and all tombstones across restarts. Do not share it with
untrusted repository code. One process owns the ledger. Restart seals all existing
executions and marks unresolved operations unknown without callbacks or replay.
There is no expiry, force-clear or automatic cleanup. A lock protects local
launch/stop ordering; supervisor callbacks run outside transactions, may read
status, and must not reenter mutations or block indefinitely.

Acceptance uses real SQLite and synthetic callbacks for lost replies, restart,
replay conflicts, generation fences, exact proof matching, persistence failures,
exclusive ownership and concurrent launch/stop. The existing Coding Agent Executor
Linux CI runs these tests. No live transport, credentials, provider calls or service
activation are required. Authentication, request/result transport, a durable
process supervisor and orchestrator integration remain separate work.

### Dormant claim-bound workspace dispatch

`FencedWorkspace` defaults off and is never registered by `server.py`. A trusted
host supplies an authenticated full Claim, exact authorization policy, the existing
ExecutionService and WorkspaceManager. `admit` fixes a maximum of 64 actions and
an absolute monotonic deadline of at most 300 seconds; reconfiguration cannot
renew it. Tool frames cannot select identity, task ID, commands or repository.
Only read-only task creation, bounded inspection and operator-named checks are
available. Existing path validation, exploration budgets and maintenance locking
remain in the actual WorkspaceManager path.

Action IDs/digests and the created task binding live in the existing execution
database, beneath the existing job-worker claim. They are not another attempt
ledger. Each action commits an unknown receipt before dispatch; replay never
executes again, even if a response was lost. A single owned action thread allows
stop to seal immediately without waiting on workspace work. No database or
admission lock spans that work. Caller wait is deadline-bounded; late work remains
tracked and blocks further admission. Deadlines do not kill work or prove stop.

Exact external supervisor evidence is still required for quiescence, including
after successful workspace return. In-flight action threads suppress stop proof.
Restart seals all executions, retains action receipts/task bindings and cannot
replay delayed requests. Unknown outcomes are resolved only by exact authority
evidence; absence of a thread, a PID exit or WorkspaceManager process-group cleanup
does not establish containment of escaped descendants. A production supervisor
and authenticated transport must enforce this contract before activation.

Synthetic tests use real SQLite, real disposable Git worktrees and an injected
authority. They cover commit-before-dispatch, request/deadline limits, replay,
identity mismatch, stop races, late completion, restart, task binding and traversal.
No service, network setting, credential file or provider is configured by this code.
