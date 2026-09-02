# Synology Admin Settings — design and rollout

Status: design locked for v0.1 implementation on `feature/synology-ui-settings-v0.1`.

## Objective

Add a safe, administrator-facing way to manage the small set of Synology deployment settings that currently live in `deploy/synology/.env`, without turning the LibreChat UI into an unrestricted environment-file editor and without exposing secret values.

The first housekeeping change also removes the obsolete deployment milestone wording from the landing-page welcome message.

## Current deployment constraints

The Synology deployment currently runs the upstream LibreChat image:

`registry.librechat.ai/danny-avila/librechat:latest`

The private deployment environment file is mounted into the app container as read-only (`./.env:/app/.env:ro`). The compose file itself also consumes values from that same host-side `.env` before the container starts. As a result:

- source changes under `client/` or `api/` are not part of the live NAS image today;
- the running LibreChat container should not be given unrestricted write access to the private host `.env`;
- many environment changes require a controlled container recreate/restart before they take effect.

LibreChat already has a useful integration point for this deployment. `ADMIN_PANEL_URL` is included in authenticated startup config only for a user with the `ACCESS_ADMIN` capability, and the existing Settings > General > Admin panel component renders a link when that value is present. This lets the Synology deployment add an administration surface without forking the main LibreChat UI in v0.1.

LibreChat also already provides authenticated dynamic application-configuration routes under `/api/admin/config`. Those should remain the preferred mechanism for settings that belong in LibreChat's runtime/application configuration. The Synology panel is specifically for host/deployment settings that genuinely require `.env` or compose-level changes.

## v0.1 architecture

Use the existing LibreChat **Admin panel** link to open a small Synology deployment administration service.

`LibreChat Settings -> General -> Admin panel -> Synology Admin Settings`

The Synology service will use a strict allowlist defined in `admin-settings.schema.json`. It will never provide a raw `.env` editor or an arbitrary command field.

The service must provide four operations only:

1. read and display allowlisted non-secret values;
2. report secret values as `Configured` / `Not configured`, never reveal the stored value;
3. validate and stage explicit changes, showing a before/after preview with secrets redacted;
4. apply an approved change atomically, recreate only the required LibreChat services, perform health checks, and roll back the `.env` change if deployment validation fails.

## Setting classes

### Editable deployment values

These are suitable for normal UI controls after validation:

- `NAS_HOST`
- `LIBRECHAT_SCHEME`
- `LIBRECHAT_PORT`
- `NO_INDEX`
- `SEARCH`
- `SESSION_COOKIE_SECURE`
- `ALLOW_EMAIL_LOGIN`
- `ALLOW_REGISTRATION`
- `ALLOW_SOCIAL_LOGIN`
- `ALLOW_SOCIAL_REGISTRATION`
- `ALLOW_UNVERIFIED_EMAIL_LOGIN`
- `ALLOW_PASSWORD_RESET`

`DOMAIN_CLIENT` and `DOMAIN_SERVER` are derived from scheme/host/port in the panel rather than edited independently, preventing inconsistent combinations.

### Replace-only secrets

These may eventually be set/replaced from a password input, but the current value is never returned to the browser:

- `OPENROUTER_KEY`
- `GITHUB_DEPLOY_STATUS_TOKEN`
- `GITHUB_TELEMETRY_TOKEN`
- `CLOUDFLARE_TUNNEL_TOKEN`

The UI reports only whether each is configured. Logs and change previews redact the supplied replacement.

### Locked security material

The following values are deliberately excluded from routine GUI editing because changing them can invalidate sessions or encrypted credentials:

- `JWT_SECRET`
- `JWT_REFRESH_SECRET`
- `CREDS_KEY`
- `CREDS_IV`

Rotation can be added later as a separate, explicit maintenance workflow with backup/recovery guidance.

### Internal / fixed values

These are not exposed as normal controls:

- `COMPOSE_PROJECT_NAME`
- container `HOST`
- container `PORT`
- `MONGO_URI`

## Safety contract

The administration service must meet all of these before deployment:

- authenticated independently at the service boundary; the LibreChat admin-only link is convenience/visibility, not the sole access control;
- no raw environment dump endpoint;
- no arbitrary shell/command execution;
- schema allowlist enforced server-side, not only in HTML/JavaScript;
- secret values never returned after storage and never included in audit output;
- CSRF protection for state-changing requests;
- atomic `.env` writes with a timestamped local backup;
- preserve unknown/unmanaged `.env` lines rather than rewriting from a template;
- reject duplicate managed keys rather than silently choosing one;
- validate booleans, ports, scheme and host values before staging;
- show whether a change requires recreate/restart;
- run `docker-compose config` before applying runtime changes;
- health-check LibreChat after the recreate and restore the previous `.env` on failure;
- maintain a sanitised local audit trail containing timestamp, actor/source, changed key names and outcome, but no secret values;
- never expose GitHub, Cloudflare, provider, JWT or encryption secret contents.

## Rollout sequence

### Phase 1 — housekeeping

- Remove the obsolete `AutoDeploy Verified` landing-page milestone.
- Add this design and the machine-readable settings allowlist.
- Keep the live deployment unchanged until reviewed/merged.

### Phase 2 — Synology Admin Settings service

Implement the small admin service and its tests. The service should be deployment-specific and should not require modifying upstream LibreChat source.

Add `ADMIN_PANEL_URL` to the private NAS environment during installation so LibreChat's existing admin-only Settings entry links to the service.

### Phase 3 — deployment integration

Add the service to the Synology deployment, with its own constrained configuration and authentication secret. Extend deployment health checks to cover the admin service without publishing secrets.

### Phase 4 — optional deeper integration

Only if the separate admin surface proves awkward should we introduce a custom LibreChat image and native Settings tab. That would require a reproducible image-build/publish pipeline; it should not be done merely to make the first version look more integrated.

## Acceptance criteria for v0.1 service

- An ordinary LibreChat user is not shown the Admin panel link.
- An authorised LibreChat admin can open the configured Synology Admin Settings URL.
- The admin service itself rejects unauthenticated access.
- Safe boolean/port/host settings can be changed through typed controls.
- Current secret values are never rendered or returned by an API call.
- Replacing a secret does not disclose its old or new value in logs.
- Invalid values are rejected before `.env` is changed.
- A successful apply recreates the required service and passes health checks.
- A failed apply restores the previous `.env` and attempts to restore the prior healthy runtime.
- Existing unmanaged `.env` entries survive a successful change unchanged.
