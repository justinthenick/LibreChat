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
- Production migration merge: `c163beaf2d042023775ce89e91470e55d8ed679e`

## Migration contract

The initial managed copy must be byte-for-byte identical to the baseline deployment skill. Any behavioral improvement belongs in a later independently benchmarked change; migration and semantic redesign must not be combined.

LibreChat's deployment-skill compatibility layer deliberately lets deployment skills shadow persisted skills with the same name. Therefore the managed copy may be synced safely while the legacy deployment copy still exists, but the persisted managed copy will not become the effective catalog entry until the legacy copy is removed from the deployed `/app/deployment-skills` tree and LibreChat is restarted.

## Acceptance criteria

1. **PASS (static)** — `managed-skills/skills/analyze-manuscript-structure/SKILL.md` has the same Git blob SHA as the production baseline (`f1c4fb16aa6180130eaaa103523d9f4b7fb78992`), proving the migration copy is byte-for-byte identical.
2. **PASS (static)** — because the copy is identical, the migration introduces no new tool permissions, `always-apply` behavior, model-invocation restriction, or user-invocation restriction.
3. **PASS (runtime, 2026-09-17)** — before cutover, persisted Skill Sync status on `server/synology` reported `status: succeeded`, `syncedSkillCount: 2`, `skippedSkillCount: 0`, and `skippedFileCount: 0`, proving the managed manuscript skill synced successfully alongside `skill-sync-pilot`.
4. **PASS (staged collision control)** — the managed copy was synced while the legacy deployment copy remained present. LibreChat's deployment-skill precedence kept the deployment copy authoritative until cutover; no semantic difference existed because both files had the same blob content.
5. **PASS (cutover, 2026-09-17)** — only after criterion 3 passed, the legacy directory was moved out of `custom/ba-agent/skills` to `_skill_backups/analyze-manuscript-structure-pre-managed-sync`. The deployment loader then dropped from 19 to 18 skills after restart.
6. **PASS (runtime, 2026-09-17)** — after restart, the persisted `analyze-manuscript-structure` record reports `source: github`, `authorName: GitHub Sync`, `alwaysApply: false`, and `sourceMetadata.sourceId: managed-skills`; its source metadata records `ref: server/synology`, migration commit `c163beaf2d042023775ce89e91470e55d8ed679e`, and the expected skill blob SHA.
7. **PASS (behaviour, 2026-09-17)** — the GitHub-synced skill reconstructed `fixture.md` without rewriting it or giving developmental-edit recommendations. It kept Leon's ferry use unconfirmed, the torn red fabric unmatched to the scarf, the identity of `M.` unresolved, the wearer of Leon's coat unidentified, and Mara's role unresolved. It also separated direct facts from character/witness statements and unknowns. Minor interpretive phrasing such as `foreknowledge`, `misdirection / fabrication`, and `premeditation or thwarted expectations` was present, but these were framed as interpretation rather than resolved canon and did not collapse the fixture's ambiguity.
8. **PASS (runtime, 2026-09-17)** — after cutover, persisted Skill Sync status remained `status: succeeded` on `server/synology` with `syncedSkillCount: 2`, `skippedSkillCount: 0`, and `skippedFileCount: 0` at `2026-09-17T12:02:32.532Z`.
9. **PASS (rollback design)** — rollback remains possible by restoring `_skill_backups/analyze-manuscript-structure-pre-managed-sync` to `custom/ba-agent/skills/analyze-manuscript-structure`, restarting LibreChat, and allowing deployment-name precedence to shadow the persisted managed copy again.

## Behaviour fixture

Use [`fixture.md`](./fixture.md) for the final runtime test. This fixture intentionally contains ambiguous identity, conflicting timing signals, character assertions that are not objective facts, and possible-but-unproven causal links.

### Invocation

Enable `analyze-manuscript-structure` as **Available** in LibreChat, start a new chat, provide the contents of `fixture.md`, and ask:

`Use analyze-manuscript-structure to reconstruct this manuscript exactly as written. Do not edit or improve it.`

Criterion 7 passes only if the result preserves the fixture's unresolved ambiguity and stays within reconstruction-only scope.

## Result

**MIG-001: PASS — all nine acceptance criteria satisfied.**

## Promotion rule

Do not use MIG-001 as evidence that other skill families can be bulk-migrated without their own dependency and collision checks. After MIG-001 passes, reuse this migration pattern for the next low-coupling family and keep requirements-lifecycle/supervisor-coupled skills until later waves.
