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
3. PENDING RUNTIME — GitHub Skill Sync against `server/synology` completes successfully with the managed manuscript skill present and no skipped skill/file errors attributable to it.
4. PENDING RUNTIME — before legacy cutover, LibreChat continues to expose only the effective legacy deployment skill for the duplicate name; the persisted GitHub copy remains shadowed rather than creating an ambiguous runtime choice.
5. PENDING CUTOVER — the legacy deployment copy is removed from the NAS deployment-skill directory only after criterion 3 is satisfied.
6. PENDING RUNTIME — after restart, `analyze-manuscript-structure` appears as `GitHub Sync`, can be enabled as `Available`, and no deployment-sourced skill with the same name remains effective.
7. PENDING BEHAVIOR — invocation on a small supplied manuscript sample performs reconstruction only: it distinguishes explicit facts, inferences and unknowns, preserves unresolved ambiguity, and does not rewrite prose or provide developmental-edit recommendations.
8. PENDING RUNTIME — persisted Skill Sync status remains `succeeded` on `server/synology` after cutover with no skipped skill/file errors attributable to the migration.
9. PASS (rollback design) — rollback remains possible by restoring the legacy deployment `SKILL.md`, restarting LibreChat, and allowing deployment-name precedence to shadow the persisted managed copy again.

## Promotion rule

Do not use MIG-001 as evidence that other skill families can be bulk-migrated without their own dependency and collision checks. After MIG-001 passes, reuse this migration pattern for the next low-coupling family and keep requirements-lifecycle/supervisor-coupled skills until later waves.
