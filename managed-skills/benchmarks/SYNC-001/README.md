# SYNC-001 — GitHub Skill Sync Pilot

## Objective

Prove that a managed skill can be promoted from GitHub into LibreChat using the native GitHub Skill Sync path without granting LibreChat repository write access.

## Source

- Repository: `justinthenick/LibreChat`
- Ref during validation: `feature/skill-sync-pilot`
- Production ref after merge: `server/synology`
- Source ID: `managed-skills`
- Sync path: `managed-skills/skills`
- Pilot skill: `sync-pilot`

## Acceptance criteria

1. Anonymous or unrelated repository content is not imported.
2. LibreChat discovers `managed-skills/skills/sync-pilot/SKILL.md`.
3. The skill appears in the LibreChat skills catalogue with GitHub as its source.
4. Invoking the pilot returns exactly `Skill Sync pilot is active.`
5. A committed change to the skill is reflected after the next sync run.
6. Sync status records the source and successful skill/file counts.
7. The GitHub credential used by LibreChat has read-only Contents and Metadata access to the selected repository.
8. Benchmark and documentation content outside `managed-skills/skills` is not imported as a skill.
9. Removing a synced pilot artifact upstream is reflected by the mirror according to LibreChat's deletion semantics.
10. No GitHub write capability is available to the LibreChat production credential.

## Promotion rule

Do not migrate business-analysis, solution-architecture, procurement, release-assurance, manuscript-engineering, or other engineered production skills until SYNC-001 passes.

After SYNC-001 passes on the branch, merge through PR and repeat a short production-ref smoke test against `server/synology`.
