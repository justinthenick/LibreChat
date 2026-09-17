# LibreChat Skill Sync Pilot Setup

## Recommended GitHub credential

Create a fine-grained GitHub personal access token dedicated to LibreChat Skill Sync.

Repository access:
- `justinthenick/LibreChat` only during the pilot

Repository permissions:
- Contents: Read-only
- Metadata: Read-only

Do not grant Actions, Pull requests, Issues, Administration, or repository write permissions.

Store the token in LibreChat Admin Panel Skill Sync credentials under a key such as:

`github-skills-prod`

Do not commit the token to this repository or place the literal token in `librechat.yaml`.

## Pilot source configuration

During branch validation:

```yaml
skillSync:
  github:
    enabled: true
    intervalMinutes: 5
    runOnStartup: true
    sources:
      - id: managed-skills
        owner: justinthenick
        repo: LibreChat
        ref: feature/skill-sync-pilot
        paths:
          - managed-skills/skills
        credentialKey: github-skills-prod
```

After PR merge, change only the ref:

```yaml
ref: server/synology
```

Keep `id: managed-skills` stable. This source ID participates in LibreChat's upstream identity model, so keeping it stable makes later repository/ref repointing safer.

## Operational lifecycle

1. Create a feature branch.
2. Change a skill under `managed-skills/skills/<skill>/`.
3. Run its benchmark suite.
4. Review and merge the PR.
5. LibreChat syncs the approved ref.
6. Verify Skill Sync status and perform the production smoke test.

## Future repository split

After SYNC-001 passes, create a dedicated repository such as `justinthenick/agent-skills` and move the `managed-skills` contents into its top-level `skills`, `benchmarks`, and `docs` directories. Repoint the existing source while retaining the source ID `managed-skills` where possible.
