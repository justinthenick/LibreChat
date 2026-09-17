# Engineered Skills Catalog

This directory is the temporary Git-backed source of truth for LibreChat Skill Sync validation.

## Ownership contract

- Git is authoritative for engineered production skills.
- LibreChat Skill Sync is the deployment/mirroring mechanism.
- Synced skills should not be manually maintained in LibreChat.
- Changes to engineered skills should be made through branches and pull requests, with benchmark evidence where applicable.
- LibreChat should consume this source using a read-only GitHub credential scoped to Contents and Metadata for the selected repository.

## Structure

- `skills/` — skill packages discoverable by LibreChat Skill Sync.
- `benchmarks/` — benchmark definitions and results tied to skill versions.
- `evidence/` — supporting evidence for promotion decisions.
- `docs/` — operating guidance and deployment contracts.

## Pilot

`skills/skill-sync-smoke-test/` is Skill Sync Deployment 001. It is deliberately non-privileged and exists only to prove GitHub → LibreChat discovery, package import, update and removal semantics before any production skill is migrated.

## Intended future repository

Once the pilot is proven, this catalog should move into a dedicated repository such as `justinthenick/agent-skills`, preserving the same directory contract. LibreChat should then be repointed by changing the configured GitHub source while keeping the source `id` stable so synced skill identity can remain stable where supported.
