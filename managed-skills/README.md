# Managed Skills

This directory is the canonical Git-backed source for engineered LibreChat skills.

## Ownership model

- Git is the source of truth for managed production skills.
- Changes are developed on branches, benchmarked, reviewed by pull request, and merged before LibreChat consumes them.
- LibreChat Skill Sync is read-only from GitHub. The production sync credential must not have write access.
- Direct/manual editing of a Git-synced production skill in LibreChat is not part of the managed lifecycle.
- Migration and semantic redesign are separate changes: the first managed copy of an existing production skill must preserve the reviewed baseline unless its migration benchmark explicitly establishes otherwise.
- Sync state and runtime availability are separate. A non-`always-apply` managed skill must be enabled as `Available` for a user before it is injected into that user's runtime Skill Catalog.

## Layout

- `skills/` — directories discoverable by LibreChat Skill Sync. Each skill contains `SKILL.md` and optional supporting files.
- `benchmarks/` — benchmark definitions and evidence. This path is intentionally outside the sync path.
- `docs/` — operational notes for the managed-skill lifecycle.

## Lifecycle

The production source path is `managed-skills/skills`, synced from `server/synology` under the stable source ID `managed-skills`.

SYNC-001 proved discovery, import/update, runtime invocation, file mirroring, deletion handling, status reporting, path scoping, and read-only repository access. Production migrations now proceed in waves using the same branch → benchmark → PR → merge → sync → smoke-test model.

Wave 1 migrates the low-coupling `analyze-manuscript-structure` skill under MIG-001. Existing deployment skills can shadow same-named persisted skills during a staged cutover; the migration benchmark must therefore verify sync first, remove the legacy deployment copy second, and confirm the GitHub-synced skill becomes the effective runtime entry only after restart.

The tree can later be moved to a dedicated repository such as `justinthenick/agent-skills` without changing the lifecycle model. Keep the Skill Sync source `id` stable when repointing the repository so LibreChat can preserve upstream identity where paths remain stable.


## Reviewed third-party skills

Reusable third-party skills may be vendored into this tree when they provide mature workflow logic that LibreChat should reuse rather than reimplement.

Rules for third-party imports:

- Pin every import to an immutable upstream commit; never mirror a mutable branch directly into production.
- Preserve the upstream license and provenance beside the skill.
- Make only explicit compatibility adaptations needed for the LibreChat runtime or the deployment's security contract.
- Treat the local system/tool security boundary as authoritative when an upstream skill assumes broader shell, Git, package-install, or worktree capabilities.
- Review upstream updates as normal code changes before refreshing a managed snapshot.

The initial software-engineering foundation imports selected methodology-only skills from the Superpowers plugin: `systematic-debugging`, `test-driven-development`, and `verification-before-completion`. Skills that directly create worktrees, commit, merge, install dependencies, or require subagents are intentionally deferred until compatible orchestration exists.
