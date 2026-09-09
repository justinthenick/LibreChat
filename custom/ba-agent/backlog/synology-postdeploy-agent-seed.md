# Synology post-deploy production-agent seeding

Status: **Open / independent deployment hardening**

## Context

PR #27 was closed as superseded, but one valid deployment concern remains: if the LibreChat API container is not recreated, startup seeding may not rerun even though production-agent JSON changed.

The manual command previously used successfully is:

```sh
docker exec librechat node /app/config/seed-production-agents.js /app/production-agents
```

## Required change

Implement this as an explicit bounded deployment stage in the current `server/synology` autodeploy flow after `/api/config` health is established and before deployment success is recorded.

## Acceptance criteria

- Seeder executes on every deployment reconciliation where the target commit is being applied, even if the API container remains up-to-date and is not recreated.
- Seeder failure makes the deployment fail; no green `nas/librechat` status is posted.
- Seeder output is written to the deployment log without exposing secrets.
- Existing health, workspace, Cloudflare and Admin Settings checks remain intact.
- Re-running the seeder is idempotent for already-seeded agents.
- Validate on a fresh current branch from `server/synology`; do not revive PR #27.

## Release discipline

Keep this independent from B042 / requirements Skill v0.2.4. Merge only after the current Synology deployment checks pass on the fresh branch.
