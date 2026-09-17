# Managed Skills

This directory is the canonical Git-backed source for engineered LibreChat skills during the Skill Sync pilot.

## Ownership model

- Git is the source of truth for managed production skills.
- Changes are developed on branches, benchmarked, reviewed by pull request, and merged before LibreChat consumes them.
- LibreChat Skill Sync is read-only from GitHub. The production sync credential must not have write access.
- Direct/manual editing of a Git-synced production skill in LibreChat is not part of the managed lifecycle.

## Layout

- `skills/` — directories discoverable by LibreChat Skill Sync. Each skill contains `SKILL.md` and optional supporting files.
- `benchmarks/` — benchmark definitions and evidence. This path is intentionally outside the sync path.
- `docs/` — operational notes for the managed-skill lifecycle.

## Pilot

The initial source path is `managed-skills/skills` and contains only `sync-pilot`. Its purpose is to prove discovery, import/update, file mirroring, deletion handling, and status reporting before migrating higher-value engineered skills.

Once the pilot is proven, this tree can be moved to a dedicated repository such as `justinthenick/agent-skills` without changing the lifecycle model. Keep the Skill Sync source `id` stable when repointing the repository so LibreChat can preserve upstream identity where paths remain stable.
