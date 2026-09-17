# MIG-002 — Procurement Specification Migration

## Objective

Promote `prepare-procurement-specification` from the legacy deployment-skill tree into the Git-backed managed-skill lifecycle without changing its semantics and without disrupting current production-agent attachments.

## Source provenance

- Legacy source: `custom/ba-agent/skills/prepare-procurement-specification/SKILL.md`
- Baseline source blob: `5c7735d852168caf861d12ad5d4422ce0b6c6eb2`
- Managed destination: `managed-skills/skills/prepare-procurement-specification/SKILL.md`
- Managed destination blob at migration baseline: `5c7735d852168caf861d12ad5d4422ce0b6c6eb2`
- Migration branch: `feature/managed-skill-procurement-specification`
- Production sync source: `managed-skills` → `managed-skills/skills`

## Dependency check

The current BA Supervisor and Release / Change Assurance production manifests do not attach `prepare-procurement-specification` by fixed skill ID. This makes it lower-coupling than skills such as `assess-operational-readiness`, which is explicitly attached to the Release / Change Assurance agent.

## Migration contract

The initial managed copy must be byte-for-byte identical to the baseline deployment skill. Migration and semantic redesign remain separate activities.

## Acceptance criteria

1. **PASS (static)** — managed and legacy `SKILL.md` blobs are identical (`5c7735d852168caf861d12ad5d4422ce0b6c6eb2`).
2. **PASS (static)** — migration introduces no change to `always-apply`, user invocation, model invocation, requirement-strength rules, domain classification, output contract, or self-check behavior.
3. **PASS (dependency review)** — the skill is not attached by fixed ID in either current production agent manifest.
4. **PENDING RUNTIME** — GitHub Skill Sync on `server/synology` succeeds with the managed procurement skill present and no skipped skill/file errors attributable to it.
5. **PENDING CUTOVER** — only after criterion 4 passes, move the legacy deployment directory out of `custom/ba-agent/skills` and preserve it under `_skill_backups`.
6. **PENDING RUNTIME** — after restart, the effective persisted skill reports `source: github`, `authorName: GitHub Sync`, production ref `server/synology`, and the expected skill blob SHA.
7. **PENDING BEHAVIOUR** — on a deliberately mixed-strength procurement fixture, the skill preserves Hard minimum / Preference / Target / Candidate / Permitted / Unknown strength, performs the correct domain classification, does not invent product specifications or vendor names, and does not perform market search/recommendation.
8. **PENDING RUNTIME** — post-cutover Skill Sync remains `succeeded` with no skipped skill/file errors attributable to this migration.
9. **PASS (rollback design)** — restoring the legacy deployment directory and restarting LibreChat remains the rollback path, with deployment-name precedence shadowing the managed copy.

## Promotion rule

Do not migrate production-agent-attached skills by this simple file-only pattern. Fixed-ID agent attachments require a coordinated migration/seeding design before cutover.
