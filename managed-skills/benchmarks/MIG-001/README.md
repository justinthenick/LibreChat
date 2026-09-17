# MIG-001 — Manuscript Structure Analyst Migration

## Objective

Promote `analyze-manuscript-structure` from the legacy deployment-skill tree into the Git-backed managed-skill lifecycle without changing its semantics and without exposing a duplicate skill to users during cutover.

## Source provenance

- Legacy source: `custom/ba-agent/skills/analyze-manuscript-structure/SKILL.md`
- Baseline source blob: `f1c4fb16aa6180130eaaa103523d9f4b7fb78992`
- Managed destination: `managed-skills/skills/analyze-manuscript-structure/SKILL.md`
- Managed destination blob at migration baseline: `f1c4fb16aa6180130eaaa103523d9f4b7fb78992`
- Migration branch: `feature/managed-skill-manuscript-structure`
- Production sync source: `managed-skills` → `managed-skills/skills`

## Migration contract

The initial managed copy must be byte-for-byte identical to the baseline deployment skill. Any behavioral improvement belongs in a later independently benchmarked change; migration and semantic redesign must not be combined.

LibreChat's deployment-skill compatibility layer deliberately lets deployment skills shadow persisted skills with the same name. Therefore the managed copy may be synced safely while the legacy deployment copy still exists, but the persisted managed copy will not become the effective catalog entry until the legacy copy is removed from the deployed `/app/deployment-skills` tree and LibreChat is restarted.

## Acceptance criteria

1. PASS (static) — `managed-skills/skills/analyze-manuscript-structure/SKILL.md` has the same Git blob SHA as the production baseline (`f1c4fb16aa6180130eaaa103523d9f4b7fb78992`), proving the migration copy is byte-for-byte identical.
2. PASS (static) — because the copy is identical, the migration introduces no new tool permissions, `always-apply` behavior, model-invocation restriction, or user-invocation restriction.
3. PASS (runtime, 2026-09-17) — production Skill Sync on `server/synology` completed successfully with `syncedSkillCount: 2`, `skippedSkillCount: 0`, and `skippedFileCount: 0` after the managed manuscript skill was merged.
4. PASS (runtime, staged cutover) — before legacy removal, the deployment-skill compatibility layer retained the effective legacy entry while the GitHub-synced copy existed as the persisted duplicate, matching the designed shadowing model.
5. PASS (cutover, 2026-09-17) — the NAS legacy deployment directory `custom/ba-agent/skills/analyze-manuscript-structure` was moved outside the mounted deployment-skills tree into `_skill_backups/analyze-manuscript-structure-pre-managed-sync`; restart then loaded 18 deployment skills instead of 19.
6. PASS (runtime, 2026-09-17) — after restart, the persisted effective record for `analyze-manuscript-structure` reports `source: github`, `authorName: GitHub Sync`, `sourceId: managed-skills`, `ref: server/synology`, `syncStatus: synced`, and `alwaysApply: false`. No deployment copy remains in the mounted deployment-skills tree.
7. PENDING BEHAVIOR — invocation on a small supplied manuscript sample performs reconstruction only: it distinguishes explicit facts, inferences and unknowns, preserves unresolved ambiguity, and does not rewrite prose or provide developmental-edit recommendations.
8. PASS (runtime, 2026-09-17) — post-cutover Skill Sync status remained `succeeded` on `server/synology` with `syncedSkillCount: 2`, `skippedSkillCount: 0`, and `skippedFileCount: 0` at `2026-09-17T12:02:32.532Z`.
9. PASS (rollback design) — rollback remains possible by restoring the legacy deployment `SKILL.md`, restarting LibreChat, and allowing deployment-name precedence to shadow the persisted managed copy again.

## Promotion rule

Do not use MIG-001 as evidence that other skill families can be bulk-migrated without their own dependency and collision checks. After MIG-001 passes, reuse this migration pattern for the next low-coupling family and keep requirements-lifecycle/supervisor-coupled skills until later waves.
