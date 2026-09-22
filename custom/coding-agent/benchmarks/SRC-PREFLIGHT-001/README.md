# SRC-PREFLIGHT-001: Trusted Host-Side Repository Refresh / Preflight Layer

## Threat / Problem Being Addressed

The LibreChat production coding executor isolates task worktrees and enforces source repository freshness via `_ensure_source_fresh`. Specifically, the executor rejects task creation if the source repository has uncommitted changes or is behind its local tracking ref (`HEAD@{upstream}`).

However, local tracking metadata (`origin/<branch>`) can itself be stale if the trusted host environment has not fetched upstream from remote GitHub repositories recently.

If an agent task is created against a repository whose local tracking refs are outdated:
- The agent might branch from outdated code and produce patches against superseded baselines.
- The executor freshness gate only checks local upstream metadata, so it cannot detect remote commits without a prior fetch.

Giving the executor container direct network and credential access to fetch from GitHub would violate the executor security boundary (the executor has no GitHub credentials, no general internet access, and no capability to alter source branches).

## Trusted Architecture Boundary

The repository refresh must happen exclusively on the **trusted WSL host**, outside the executor sandbox:

```text
GitHub / Remote
    ↓ (trusted WSL host fetch with operator credentials)
Trusted Host-Side Preflight (`source_preflight` / fast-forward only)
    ↓ (clean, verified, fast-forwarded source clone)
WSL Source Clone (`~/coding-agent/repos/<repo>`)
    ↓ (local worktree creation)
Existing Executor Freshness Gate (`_ensure_source_fresh`)
    ↓ (isolated task worktree)
Agent Coding Task (`~/coding-agent/tasks/<task-id>`)
```

### Complementary Security Role

`source_preflight` **complements** rather than replaces the executor's `_ensure_source_fresh`:
1. **Host-side (`source_preflight`)**: Operates on the trusted host with network access. It performs `git fetch --prune <remote>`, verifies cleanliness, and advances the local branch **strictly via fast-forward merge** (`git merge --ff-only <fetched-upstream-sha>`). It fails closed on dirty worktrees, diverged branches, local-ahead commits, detached HEAD, or network errors.
2. **Executor-side (`_ensure_source_fresh`)**: Runs inside the isolated container with no network access. It acts as an immutable boundary gate verifying that the mounted source repository is clean and not behind its local tracking metadata when worktrees are spawned.

## Preflight Rules & Success / Failure Cases

| Case | Behavior | Status | Reason / Action |
|---|---|---|---|
| Clean and already current | No changes made | **PASS** | Up to date with upstream |
| Clean and behind upstream | `git merge --ff-only <fetched-upstream-sha>` | **PASS** | Fast-forwarded N commit(s) from upstream |
| Tracked dirty changes | No fetch / no merge | **FAIL** | Contains tracked modifications |
| Staged dirty changes | No fetch / no merge | **FAIL** | Contains staged changes |
| Untracked dirty changes | No fetch / no merge | **FAIL** | Contains untracked files |
| Subdirectory target | Refuse execution | **FAIL** | Target is not repository root |
| Mismatched / unexpected upstream | Refuse guessing | **FAIL** | Upstream does not match expected |
| Local branch ahead of upstream | Refuse push or rewrite | **FAIL** | Local-ahead commits present |
| Diverged from upstream | Refuse rebase or merge | **FAIL** | Diverged (ahead > 0, behind > 0) |
| Missing upstream configuration | Refuse guessing | **FAIL** | No upstream configured |
| Detached HEAD | Refuse guessing | **FAIL** | Detached HEAD not supported |
| Fetch / network failure | Fail closed | **FAIL** | Remote network / auth failure |

### Invariants Enforced
- **Never** uses `git reset --hard`.
- **Never** force-updates refs (`git push --force`, `git update-ref`, etc.).
- **Never** creates merge commits (`--ff-only` enforced).
- **Never** commits, pushes, rebases, stashes, cleans, or discards user changes.

## Structured Output Contract

The preflight tool produces structured results (both human-readable and JSON):

```json
{
  "repository_path": "/home/user/coding-agent/repos/LibreChat",
  "repository_name": "LibreChat",
  "branch": "main",
  "upstream": "origin/main",
  "sha_before": "bd90f576...",
  "fetched_upstream_sha": "2e82974b...",
  "sha_after": "2e82974b...",
  "ahead_count": 0,
  "behind_count": 1,
  "fast_forwarded": true,
  "status": "PASS",
  "reason": "fast-forwarded 1 commit from origin/main"
}
```

## Operator Usage from WSL

Operators can invoke the host-side preflight tool directly from WSL before launching tasks:

```bash
# Explicit safe binding with expected upstream (human readable)
coding-agent-source-preflight ~/coding-agent/repos/LibreChat --expected-upstream origin/server/synology

# JSON output mode (for scripting/automation)
coding-agent-source-preflight ~/coding-agent/repos/LibreChat --expected-upstream origin/server/synology --json

# Direct source-checkout execution without installing the package
PYTHONPATH="$HOME/coding-agent/control/custom/coding-agent/host/src" \
  python3 -m source_preflight.cli ~/coding-agent/repos/LibreChat --expected-upstream origin/server/synology
```

## Next Integration Steps

Automatic before-task integration must eventually bind **approved repository path + expected upstream** from trusted host/controller configuration (e.g. WSL host daemon or preflight scheduler), not agent-provided arbitrary values. To maintain the strict security boundary, this must not be triggered by or delegated to the unauthenticated or sandboxed executor container.
