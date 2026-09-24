# Fresh inspection and constrained cleanup

Release: Pilot 0.1.11, executor 0.1.8, host 0.1.3.

## Established inventory failure

Production parallel `status` and `inventory` helpers reproduced the original
acceptance failure: status exited 0 while inventory exited 1 with
`executor_busy: retry after the current operation finishes`. Both had requested
the exclusive nonblocking maintenance gate. The broker's subprocess wrapper hid
that diagnostic behind a generic tool error. This was local maintenance contention,
not an MCP discovery or first-use initialization failure.

The broker now serializes helper admission with a 15-second bounded mutex. No
subprocess starts until admitted; no subprocess is retried. The executor gate stays
exclusive and nonblocking so actual coding operations still cause a safe refusal.
Tests dispatch six concurrent helpers and assert six executions with no overlap.
Restart remains disabled in production and is not exposed to the Pilot.

## Fresh repository status

`fresh_repository_status(repository)` accepts only a configured repository alias.
It requires a clean checkout on the expected branch/upstream, one matching origin
URL and no URL rewrite. HTTPS GitHub transport and a single explicit refspec are
fixed by operator policy; redirects, tag fetching, pruning, submodule recursion,
automatic maintenance and FETCH_HEAD writes are disabled. A dedicated
`refs/coding-maintenance/status/<branch>` ref is the only fetched comparison ref.

Successful output includes `ok`, branch, HEAD, dirty, upstream, upstream SHA,
ahead/behind, divergence, fetch start/completion time, fetch result and
`comparison_basis: fresh_remote_ref`. Fetching objects and this ref is permitted;
source files, index, checked-out branch, cached origin ref and existing FETCH_HEAD
are not changed. Cached `repository_status` retains `not_fetched` semantics.
Refused/failed fresh status has `ok: false`, no upstream SHA/counts and no fallback
to stale comparison evidence. A clean divergent checkout may be compared but is
never updated. Remote state is evidence as of the fetch, not a lasting freshness claim.

## Eligibility and deletion

Clean inventory is never cleanup authorization. `preview_cleanup(task_id)` checks
enabled policy and an operator-written retirement record containing `retired_at`,
`repository`, `branch`, `head` and `fingerprint`. The default retirement age is
86400 seconds. Only an explicit operator policy can lower it, e.g. to zero for one
new disposable acceptance worktree. Old numeric-only retirement records fail closed.

Under the exclusive executor gate and source coordination lock, preview proves
expected task/branch/repository identity, registered nonbroken worktree, no Git lock,
clean tracked/index state, no untracked files and no ignored files. It matches the
complete retired identity before declaring eligible. Identity includes HEAD,
branch, filesystem device and inode. Missing/changed identity fails closed.

`cleanup_task(ticket, confirm_task_id)` consumes the 60-second ticket once, checks
the exact confirmation and current retirement policy, reacquires the exclusive
gate, then recomputes identity and cleanliness immediately before non-forced
`git worktree remove`. No path, shell command, force flag or branch-deletion option
is accepted. The branch and state audit record remain. A timeout is not permission
to retry a mutation: inspect inventory first. Service restart invalidates tickets.

## Deployment acceptance

1. Pin the tested image and packages outside executor mounts. Preserve source/task
   mounts and task states. Keep restart and working-tree refresh disabled.
2. Reconcile the exact seven maintenance IDs into the Pilot (no wildcard). Existing
   nine coding tools remain for coding tasks only. Maintenance tasks must not invoke
   `create_task` or substitute ordinary coding tools on refusal.
3. Run a fresh Pilot read-only conversation including cached and fresh status and
   inventory. Require successful maintenance calls, zero tool errors and zero coding
   calls. Also issue concurrent broker requests to verify stable inventory admission.
4. Create a unique deliberately disposable clean worktree as an operator setup
   action, outside the read-only conversation. Hash source working trees and every
   unrelated task, including ignored/untracked files. Record branch/HEAD and state
   metadata separately. Do not retire any existing task.
5. Record only this disposable identity in operator policy. Enable cleanup only,
   with zero minimum age explicitly for this test. Preview and confirm removal
   through MCP, then verify replay rejection, branch retention, source and unrelated
   content/identities unchanged. Retain the evidence and reset minimum age to 86400.

Locks coordinate service participants, not arbitrary out-of-band filesystem writes.
Do not run human Git or file edits concurrently. Broken, locked, dirty, manual-review
or unretired worktrees are ineligible. No automatic age-based deletion or pruning is
introduced. The intentionally retained dirty/manual-review worktrees are never used
as fixtures. The previously removed accidental inspection worktree is not a target.
