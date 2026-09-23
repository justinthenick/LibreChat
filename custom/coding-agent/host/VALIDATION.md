# Host maintenance review evidence

Validated on 2026-09-24, starting from `server/synology` commit
`b200f6bcb1202fb42015f8d0074110295961df31`.

- Executor suite: **49 passed** on Linux, including original coding-flow regressions.
- Host suite: **31 passed**, including source-preflight regressions, real MCP SDK tool
  dispatch and real HTTP authentication/discovery. Missing/wrong tokens were refused.
- Release executor Dockerfile built successfully with executor 0.1.6 and MCP 2.2.0.
- Host wheel built and installed into a temporary directory in a disposable container;
  both suites passed against the newly built executor runtime. The host package version
  was subsequently incremented to 0.1.1; no implementation changed after this check.
- Real Docker lifecycle smoke passed against the release candidate: pinned image and
  mount checks, health, repository status, inventory, active-operation restart refusal,
  actual restart and health recovery, persisted task mode/budget, dirty-worktree cleanup
  refusal, clean-worktree removal with retained branch, and filtered logs.
- Fixtures used unique temporary repositories/tasks and a uniquely named container,
  with no production mounts. The test container was removed afterward. Candidate
  images were retained for review; no production image/tag was replaced.
- `git diff --check` passed. CI now builds both packages, runs both suites, builds the
  executor image and repeats the disposable Docker lifecycle smoke.

## Existing worktree accounting

Read-only production inventory found **39 worktrees: 19 clean and 20 dirty** (including
ignored content), with **zero stale Git registrations**. All were preserved. Clean
does not establish retirement: one clean worktree is a release branch, which the new
cleanup handler rejects. The successful subtract fix remains uncommitted in its
existing task and was not used as a cleanup fixture. No retirement was approved or
added to production policy.

## Review/rollout limitations

The maintenance service, token, policy and lock mount have not been installed in
production, and the production executor has not been restarted. LibreChat's production
agent/tool configuration remains unchanged. The live source checkout was verified
clean at the stated baseline before implementation.

Review the explicit trust boundary and staged activation procedure in
[MAINTENANCE.md](MAINTENANCE.md). In particular: the host broker's OS account is trusted;
credential-free GitHub HTTPS is the supported fetch transport; cleanup requires
operator retirement; legacy tasks without saved state become read-only/exhausted;
raw log text is intentionally unavailable through MCP. The old host source-sync timer
must be retired during approved rollout. This evidence does not claim production
activation or a production end-to-end LibreChat maintenance conversation.
