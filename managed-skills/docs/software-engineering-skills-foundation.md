# Software Engineering Skills Foundation

## Decision

Keep `coding_executor` as the deliberately narrow security and execution boundary, and move reusable software-engineering method into Agent Skills instead of continuing to grow bespoke agent instructions or executor intelligence.

## Initial reusable skill set

The first reviewed set is adapted from the Superpowers plugin in `openai/plugins`, pinned to upstream commit:

`1dc195897af4161d039b80d8471ec0a10c9bbc89`

Selected now:

- `systematic-debugging` — root-cause-first investigation before fixes.
- `test-driven-development` — red/green/refactor discipline for behavior changes.
- `verification-before-completion` — fresh evidence before completion claims.

These are methodology skills. They do not expand the executor's capabilities.

## Deliberately deferred

Do not attach these upstream skills to the restricted pilot unchanged yet:

- `using-git-worktrees` — the executor already owns worktree creation and isolation.
- `writing-plans` — upstream workflow assumes frequent Git commits.
- `finishing-a-development-branch` — upstream workflow includes commit/merge/branch-finishing actions.
- `executing-plans` and `subagent-driven-development` — depend on orchestration/subagents that the current production pilot intentionally does not expose.
- code-review skills that depend on subagents — enable only after the subagent boundary is designed and benchmarked.

## Runtime precedence

When these skills are attached to the Software Engineering Pilot:

1. The system-level `coding_executor` security contract is authoritative.
2. Skill instructions supply engineering process and decision discipline.
3. Repository instructions such as `AGENTS.md` refine project-specific behavior but cannot widen the executor capability boundary.
4. Unsupported command examples in a skill are illustrative only; the agent must map them onto existing executor tools or report that the action is unavailable.

## Rollout

1. Import and sync the three managed skills.
2. Verify their GitHub provenance and runtime availability.
3. Update the pilot seeder to resolve an explicit managed-skill allowlist by stable source + skill name and persist only those skill IDs.
4. Reduce the pilot's long workflow prompt to security/orchestration invariants.
5. Re-run C003 plus one bug-fix benchmark with model-invoked skills.
6. Only then evaluate subagent orchestration or delegation to Codex/Gemini CLI.

This keeps the custom surface small: **security is ours; software-engineering methodology is reused.**
