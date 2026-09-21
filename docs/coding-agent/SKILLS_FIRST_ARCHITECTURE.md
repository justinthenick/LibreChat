# Skills-first coding architecture

## Decision

LibreChat's coding executor remains a narrow security and execution boundary. It should not become a bespoke coding-agent framework.

Reusable engineering behaviour belongs in repository instructions and interoperable Agent Skills. Before authoring a new skill, prefer an existing repository skill or a maintained upstream skill that already solves the problem.

## Why

The executor already provides the deployment-specific controls we need:

- approved repositories only;
- one isolated Git worktree per task;
- unified-patch mutation;
- allowlisted checks;
- no arbitrary shell, package installation, commit, push, merge or Docker socket;
- bounded exploration;
- complete final diff for human review.

Those controls are specific to this deployment and should stay local.

Planning, debugging, review, architecture and validation workflows are not executor responsibilities. Mature coding agents already provide the generic coding loop and support progressively disclosed skills. We should compose those capabilities rather than recreate them in one giant prompt or in executor code.

## Reuse-first policy

Use this order:

1. built-in coding-agent capability;
2. existing repository skill;
3. maintained upstream skill with a compatible license;
4. small repository-specific adaptation;
5. new skill only when the first four options do not fit.

Every copied or adapted third-party skill must retain its license and attribution.

The first interoperability fixture is `codebase-design`, already present under `.claude/skills`. It is mirrored into `.agents/skills` unchanged, including its MIT license, so Codex, Gemini CLI and LibreChat can exercise the same skill content without inventing a replacement.

## Target

```text
LibreChat
  |
Software Engineering Agent
  |
  +-- Agent Skills (.agents/skills)
  |     |
  |     +-- reused / adapted repository workflows
  |
  +-- coding_executor (MCP)
        |
        +-- security boundary
        +-- isolated task worktrees
        +-- constrained checks and patches
```

Codex and Gemini CLI both discover repository skills from `.agents/skills`. LibreChat mirrors the same path through GitHub Skill Sync.

## Responsibilities

### Executor

Keep the executor deliberately boring. Its responsibilities are policy enforcement, isolation, bounded access, checks, patch application, status and diff evidence.

Do not add planning frameworks, role-specific engineering knowledge, review methodology or task-specific heuristics unless they enforce a security or reliability invariant.

### Repository instructions

Use `AGENTS.md` for durable repository-wide constraints and project context that should apply to every coding task.

### Skills

Use skills for reusable workflows that should activate only when relevant. Good candidates are repository-specific verification, architecture, release, CI diagnosis and security workflows.

Do not create a generic "software engineering" skill merely to restate the coding loop already supplied by Codex, Gemini CLI, Claude Code or LibreChat's model.

## LibreChat integration

The existing `managed-skills/skills` production source remains intact.

A second GitHub Skill Sync source named `coding-agent-skills` mirrors `.agents/skills`. This keeps the interoperability workspace separate from the existing managed production-skill lifecycle while using the same read-only GitHub credential.

The Software Engineering Pilot remains skill-disabled until interoperability and sync are validated. Enabling or narrowing its skill allowlist is a separate change.

## Existing ecosystems

The repository already contains Claude-oriented skills under `.claude/skills`. Treat those as reuse candidates, not as a competing framework.

When a skill proves portable, prefer one canonical definition long term. During the first phase, duplication is acceptable only as a temporary compatibility bridge while discovery behaviour is verified across runtimes.

## Pilot simplification

After skills are active in LibreChat, reduce the Software Engineering Pilot instructions to:

- security and task-isolation invariants;
- task-mode selection;
- executor tool contract;
- concise skill-routing guidance;
- final evidence requirements.

Workflow expertise should live in skills or repository instructions instead of the permanent agent prompt.

## Evaluation

Evaluate portability and triggering rather than prompt size.

For each coding skill:

1. verify discovery in each target runtime;
2. verify one positive trigger;
3. verify one nearby non-trigger;
4. verify the skill does not request capabilities forbidden by that runtime;
5. keep it only if it improves task quality or consistency.

Existing executor benchmarks remain boundary tests. They should not grow into a parallel coding-agent framework.

## Immediate sequence

1. Reuse `codebase-design` as the first interoperability fixture.
2. Verify Codex discovers it from `.agents/skills`.
3. Verify Gemini CLI discovers it from `.agents/skills`.
4. Merge the Skill Sync source only after those checks are clean.
5. Confirm LibreChat mirrors the same skill.
6. Enable the pilot for a narrow skill allowlist in a separate change.
7. Trim duplicated workflow text from the pilot instructions.
8. Add or port more skills only when repeated work justifies them.
