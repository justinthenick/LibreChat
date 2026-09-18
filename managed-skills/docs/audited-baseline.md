# Managed Skills Audited Baseline

## Objective

Establish `managed-skills/skills` as the canonical source for every production LibreChat skill.

A production skill is compliant when:

- its authoritative `SKILL.md` and all bundled files are committed under `managed-skills/skills/<name>/`;
- LibreChat records it with `source: github`;
- `sourceMetadata.sourceId` is `managed-skills`;
- `sourceMetadata.skillPath` points to the matching managed-skills directory;
- GitHub Skill Sync reports `status: succeeded`;
- `skippedSkillCount` and `skippedFileCount` are both zero;
- no duplicate `source: inline` record remains for the same production skill name.

## Baseline captured 2026-09-18

Live LibreChat catalog before migration:

| Skill | Source | Migration state |
|---|---|---|
| analyze-manuscript-structure | github | compliant |
| skill-sync-pilot | github | compliant |
| analyze-requirements | inline | promote exact live definition |
| decompose-requirements | inline | promote exact live definition |
| frontend-design | inline | promote exact live definition |
| improve-codebase-architecture | inline | promote exact live definition and 2 bundled files |
| technical-writer | inline | promote exact live definition and 2 bundled files |

GitHub Skill Sync baseline:

- source id: `managed-skills`
- repository: `justinthenick/LibreChat`
- ref: `server/synology`
- path: `managed-skills/skills`
- status: `succeeded`
- synced skills: 2
- skipped skills: 0
- skipped files: 0

## Migration discipline

1. Preserve the exact live inline definition before promotion.
2. Preserve all bundled skill files.
3. Commit promoted content to a feature branch.
4. Review/validate before merge.
5. Merge and allow GitHub Skill Sync to create the GitHub-backed counterparts.
6. Verify content and attachment equivalence.
7. Remove the superseded inline records only after verification.
8. Re-run the live catalog audit and require zero inline production skills.

Do not use the migration itself as an opportunity to upgrade skill content. Version/content improvements are separate changes after the audited baseline is established.

## Scope boundaries

The following are not production LibreChat skills merely because they use the Skill format:

- `.claude/skills/**` — coding/agent workspace skills;
- `custom/ba-agent/skills/**` — BA lab/candidate source material;
- `e2e/fixtures/**` — test fixtures.

Those may be promoted separately, but they are not included in the production catalog until deliberately added to `managed-skills/skills`.
