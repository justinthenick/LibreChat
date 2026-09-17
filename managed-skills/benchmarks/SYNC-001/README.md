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

## Validation evidence — 2026-09-17

Observed against `feature/skill-sync-pilot` on the Synology LibreChat deployment:

- PASS — criteria 2–3: `skill-sync-pilot` appeared in the LibreChat Skills catalogue and was labelled `GitHub Sync`.
- PASS — criterion 4: after enabling the synced skill as `Available` for the test user, a new LibreChat chat invoked `skill-sync-pilot` through the skill tool and returned exactly `Skill Sync pilot is active.`
- PASS — criterion 5: commit `76ba85434ba2ed90089fc12d77a3e3b95caf0f79` changed the synced skill description to include `SYNC-001 update marker: v2`; the updated description appeared in LibreChat after the next sync.
- PASS — criterion 9: disposable file `managed-skills/skills/sync-pilot/delete-me.txt` was first observed under the synced skill in LibreChat, then deleted upstream in commit `21028271b2af9bf19917c1afc2e4eda717211e62`; after the next sync the file no longer appeared under the skill.
- PASS — criterion 8 (observed): only content below `managed-skills/skills` appeared in the Skills catalogue; benchmark/documentation files were not surfaced as skills.
- PENDING EVIDENCE — criterion 6: capture sync-status source and successful skill/file counts.
- PENDING EVIDENCE — criteria 7 and 10: retain/configure the LibreChat production GitHub credential as repository-scoped, read-only Contents and Metadata; capture configuration evidence without exposing the token.
- Criterion 1 is constrained by the configured source path and is considered satisfied once status confirms the `managed-skills` source is the active source for this pilot.

## Operational note

GitHub Skill Sync imports the skill into LibreChat, but a non-`always-apply` skill still needs to be enabled as `Available` for the user before it is injected into that user's runtime Skill Catalog.

## Promotion rule

Do not migrate business-analysis, solution-architecture, procurement, release-assurance, manuscript-engineering, or other engineered production skills until SYNC-001 passes.

After SYNC-001 passes on the branch, merge through PR and repeat a short production-ref smoke test against `server/synology`.
