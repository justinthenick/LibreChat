---
name: software-engineering
description: Use for repository changes that require inspecting code, reproducing or understanding a problem, making a focused implementation change, validating it, and presenting reviewable evidence. Do not use for simple explanation-only requests or tasks that are primarily release, security, or documentation review when a more specific skill applies.
---

# Software Engineering

Work from evidence and keep changes narrowly scoped.

1. Read the repository instructions that apply to the working directory.
2. Inspect the smallest relevant implementation, configuration, and test surface.
3. Establish the current behaviour with an existing check or test when practical.
4. Identify the likely root cause or implementation requirement before editing.
5. Make the smallest coherent change that addresses the task.
6. Preserve existing behaviour outside the requested scope.
7. Add or update focused tests when they materially protect the change.
8. Run the most relevant available checks after editing.
9. Review the final diff for unrelated changes, generated artifacts, secrets, and accidental churn.
10. Report what changed, what was validated, and any residual uncertainty.

## Efficiency

Prefer targeted search and focused reads over exhaustive repository traversal. Stop gathering evidence once it is sufficient to justify the next action.

Do not repeatedly retry an unavailable dependency or unsupported command. Record the limitation and use an available independent check where useful.

## Change discipline

Avoid speculative refactors, cosmetic churn, new dependencies, generated artifacts, or temporary files unless the task genuinely requires them.

Do not claim a change exists until the edit operation has actually succeeded.

## Validation discipline

A passing check is evidence, not the goal by itself. Do not weaken tests or implementation semantics merely to make a check pass.

When a baseline check fails for the problem being fixed, preserve that evidence and demonstrate the post-change result.

## Handoff

Leave the repository in a reviewable state and provide concise evidence:

- files changed;
- checks run and results;
- important implementation decisions;
- residual risks or unverified areas;
- final diff or equivalent review surface when the runtime provides one.
