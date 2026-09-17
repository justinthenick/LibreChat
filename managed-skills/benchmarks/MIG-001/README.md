# MIG-001 — Manuscript Structure Managed-Skill Migration

## Objective

Migrate the existing `analyze-manuscript-structure` skill from the deployment-skill mount into the GitHub-backed managed-skill lifecycle without changing its behavior or creating duplicate runtime entries.

## Candidate

- Existing source: `custom/ba-agent/skills/analyze-manuscript-structure/SKILL.md`
- Managed target: `managed-skills/skills/analyze-manuscript-structure/SKILL.md`
- Version: `0.1.0`
- Migration wave: 1

## Why this skill first

This is a single-file, self-contained reconstruction skill with no external helper files, no always-apply behavior, no deployment-specific credentials, and no dependency on another managed skill. It is therefore a low-risk first production migration candidate.

## Acceptance criteria

1. The managed target is textually equivalent to the existing deployment skill at migration start.
2. No behavior, frontmatter, name, description, version, or output contract is changed as part of the move.
3. The migration does not leave two independently active copies of `analyze-manuscript-structure` in LibreChat.
4. After cutover, the Skills UI shows the skill with GitHub Sync as its source.
5. The skill can be enabled as Available and invoked from a new chat.
6. A reconstruction-only smoke prompt does not produce rewriting or developmental-edit recommendations.
7. Persisted Skill Sync status remains `succeeded` with zero skipped skills/files after cutover.
8. Rollback remains possible by restoring the deployment-skill copy and removing the managed target in a follow-up PR.

## Transition rule

Do **not** merge this migration into `server/synology` while the same skill remains simultaneously exposed from `/app/deployment-skills` unless duplicate-name behavior has been explicitly verified safe. The preferred cutover is atomic at the deployment boundary: stop exposing the legacy deployment copy, then allow the managed copy to become authoritative.

## Source parity evidence

At branch creation, the source skill blob was `f1c4fb16aa6180130eaaa103523d9f4b7fb78992`. The managed copy was created from that exact content without intentional edits.

## Promotion rule

MIG-001 must pass before migrating the next manuscript skill or beginning a broader BA/architecture/procurement family move.
