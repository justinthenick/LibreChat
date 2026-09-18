# MIG-002 — Complete GitHub Skill Sync migration

## Status

Prepared, not cut over. This record does not claim runtime completion.

The 2026-09-18 live catalog contains 23 skills:
- 2 GitHub-synced skills: analyze-manuscript-structure and skill-sync-pilot.
- 18 deployment-loaded BA skills listed in inventory.json.
- 3 manually imported skills: technical-writer, frontend-design, improve-codebase-architecture.

All 18 deployed BA SKILL.md files were hashed on the NAS and match the source blobs on server/synology at adb82762f84ccb6cc86e102e5b8eb2e8d8ebb1c8. The staged managed copies reuse those exact blobs. This migration changes no skill instructions, invocation flags, or tool allowances.

## Remaining cutover gates

1. Export all three imported skills with every supporting file, license, invocation setting, and existing agent/user binding. Preserve an access-controlled rollback snapshot.
2. Add their exact reviewed contents to the managed tree. Check for missing referenced resources; do not invent replacements.
3. Preserve source id managed-skills. Account explicitly for the temporary PR #91 manuscript-validation ref before changing it; this migration does not approve or merge PR #91.
4. Sync the staged tree and require succeeded status, zero skipped skills/files, matching blob hashes, and complete supporting-file counts.
5. Migrate deployment IDs and imported-skill IDs/bindings deliberately. The BA Supervisor and Release / Change Assurance seeders currently reference deployment IDs. Existing user availability selections must also be preserved.
6. Remove deployment shadowing only after sync and binding verification. Restart/reconcile LibreChat and verify both production agents retain their exact bounded skill lists and handoff.
7. Verify one effective catalog entry per name, GitHub provenance for all 23 skills, unchanged invocation/tool flags and user availability, and callable referenced resources.
8. Repeat sync to verify idempotence, then record the final approved ref, commit, counts, and runtime evidence.

## Boundaries

Do not delete the current deployment or imported copies before a verified rollback snapshot and binding plan exist. Copying files alone is not a completed migration. Skill semantic redesign and software-engineering benchmark runs are separate work.
