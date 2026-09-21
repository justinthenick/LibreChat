# Skills-first coding architecture

## Decision

LibreChat's coding executor remains a narrow security and execution boundary. It should not become a bespoke coding-agent framework.

Reusable engineering behaviour belongs in interoperable Agent Skills and repository instructions. The same skill definitions should be consumable by LibreChat, Codex and Gemini CLI wherever practical.

## Why

The current executor already provides the deployment-specific controls we need:

- approved repositories only;
- one isolated Git worktree per task;
- unified-patch mutation;
- allowlisted checks;
- no arbitrary shell, package installation, commit, push, merge or Docker socket;
- bounded exploration;
- complete final diff for human review.

Those controls are specific to this deployment and should stay local.

Planning, debugging, test authoring, code review, release checks and other software-engineering workflows are not deployment-specific. Mature coding agents already support reusable skills and repository instructions, so we should reuse that ecosystem rather than encode more behaviour into the executor or one large agent prompt.

## Target

```text
LibreChat
  |
Software Engineering Agent
  |
  +-- Agent Skills (.agents/skills)
  |     |
  |     +-- reusable engineering workflows
  |
  +-- coding_executor (MCP)
        |
        +-- security boundary
        +-- isolated task worktrees
        +-- constrained checks and patches
```

Codex and Gemini CLI can also consume repository-level skills from `.agents/skills`, allowing the same engineering workflows to follow the repository across runtimes.

## Responsibilities

### Executor

Keep the executor deliberately boring. Its responsibilities are policy enforcement, isolation, bounded access, checks, patch application, status and diff evidence.

Do not add planning frameworks, role-specific engineering knowledge, code-review methodology or task-specific heuristics to the executor unless they are required to enforce a security or reliability invariant.

### Repository instructions

Use `AGENTS.md` for durable repository-wide constraints and project context that should apply to every coding task.

### Skills

Use skills for reusable workflows that should activate only when relevant. Initial candidates:

- software-engineering;
- bug-investigation;
- code-review;
- test-authoring;
- ci-failure-analysis;
- release-readiness;
- security-review.

Keep skills focused and composable. Put deterministic helpers in a skill's `scripts/` only when instructions alone are insufficient.

## LibreChat integration

The current production managed-skill lifecycle under `managed-skills/skills` remains unchanged until a deliberate migration is approved.

The first interoperability phase develops and evaluates coding skills under `.agents/skills`. Once stable, LibreChat Skill Sync can either:

1. add `.agents/skills` as a dedicated source for coding skills, or
2. repoint a dedicated coding-skill source to that path.

Do not disrupt the existing managed production skill source merely to gain interoperability.

## Pilot simplification

After skills are active in LibreChat, reduce the Software Engineering Pilot instructions to:

- security/task-isolation invariants;
- task-mode selection;
- executor tool contract;
- concise routing guidance for skills;
- final evidence requirements.

Move debugging, test strategy, code review and workflow detail out of the permanent agent prompt and into skills.

## Evaluation

Evaluate skills, not bespoke prompt growth.

For each coding skill:

1. define trigger/non-trigger cases;
2. define a small benchmark corpus;
3. measure task completion and safety;
4. verify the correct skill activates;
5. keep the skill only if it improves results without unnecessary tool use.

Existing executor benchmarks remain useful as boundary tests, but they should not evolve into a parallel coding-agent framework.

## Immediate sequence

1. Establish `.agents/skills` as the interoperable coding-skill workspace.
2. Start with one general `software-engineering` skill.
3. Test it with Codex and Gemini CLI skill discovery.
4. Expose the same skill to the LibreChat pilot through Skill Sync.
5. Trim duplicated workflow text from the pilot instructions.
6. Add specialized skills only when repeated tasks justify them.
