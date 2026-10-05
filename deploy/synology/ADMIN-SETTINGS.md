# Synology Admin Settings — v0.1 design and operating contract

Status: **implemented on `feature/synology-ui-settings-v0.1`; awaiting controlled NAS rollout/verification.**

## Objective

Provide an administrator-facing way to manage the small set of Synology deployment settings that live in `deploy/synology/.env` without exposing a raw environment editor, leaking secrets, or giving the browser-facing LibreChat container unrestricted host/Docker access.

## Deployment constraints

The Synology deployment continues to run the upstream LibreChat image:

`registry.librechat.ai/danny-avila/librechat:latest`

The private `.env` remains host-side runtime state and is mounted read-only into LibreChat. Source changes under `client/` or `api/` therefore still do not alter the upstream application image. Deployment-level changes are handled outside that image.

LibreChat's existing `ADMIN_PANEL_URL` integration is used as the navigation point for authorised LibreChat admins. The Synology panel is independently authenticated; the LibreChat admin-only link is convenience/visibility, not the security boundary.

## v0.1 architecture

The implemented split is:

`LibreChat admin link / browser -> non-privileged admin-settings panel -> Unix socket -> privileged host worker -> .env + docker-compose`

### Browser-facing panel

`admin-settings-panel.py`, deployed through `docker-compose.admin.yml`:

- receives only `ADMIN_SETTINGS_ACCESS_TOKEN`, panel port and Unix-socket path;
- has **no `.env` mount**;
- has **no Docker socket**;
- runs as UID/GID `1026:100`;
- runs read-only, with `no-new-privileges` and all Linux capabilities dropped;
- uses a same-origin API and Bearer token held only in browser session storage;
- sets restrictive security/cache/frame/content headers;
- never receives current secret values from the worker.

### Privileged host worker

`admin-settings-worker.py`, installed by `autodeploy.sh` as:

`librechat-admin-settings-worker.service`

The worker:

- is reachable only through a group-restricted Unix-domain socket under `/volume1/docker/librechat/admin-settings-state`;
- reads the private `.env` locally;
- enforces `admin-settings.schema.json` server-side;
- rejects raw/unallowlisted keys and hidden transport/security keys;
- stages a redacted preview before apply;
- creates a timestamped chmod-600 `.env` backup;
- writes `.env` atomically while preserving unmanaged lines/comments;
- runs `docker-compose config`;
- recreates only services mapped to changed settings;
- health-checks affected services;
- restores the previous `.env` on pre-recreation failures; after a completed recreation followed by failed health checks, restores and recreates the previous runtime;
- holds uncertain recreation outcomes for host review without launching a potentially overlapping rollback;
- writes a local audit log containing timestamps, changed key names, stages, outcomes and bounded error metadata, but no setting values or raw command output.

### Slow recreation and recovery holds

A successful NAS API recreation was observed taking 344 seconds. Settings recreation
therefore allows 600 seconds overall (two 300-second Docker request budgets), with
`COMPOSE_HTTP_TIMEOUT=300` and `DOCKER_CLIENT_TIMEOUT=300`. This is a bounded budget,
not a guarantee that every NAS operation will finish. Apply responses allow 1800
seconds at the panel and 1860 seconds at the embedded gateway for apply plus a
possible completed-operation rollback. The outer Bun server disables its 10-second
idle timer only for POST `/deployment-control/api/apply`, with a separate 1900-second
deadline covering authentication, request handling, response headers and the complete
response body. The response is capped at 1 MiB; client cancellation and the deadline
abort downstream fetch. Ordinary routes retain their default timeout. These limits
require the rebuilt Admin Panel image as well as refreshed Python panel/gateway
processes; replacing bind-mounted files alone does not reload running interpreters.

Before writing configuration, the worker atomically persists a mode-600
`/var/lib/librechat-admin-settings/recovery-required.json` record with the backup filename and
affected keys/services. This mode-700 root-owned directory is outside the panel mount; its ancestor ownership, directory/file modes and link types are checked. Temporary files use unpredictable names, exclusive/no-follow creation and directory-relative operations. The deployer uses the same read-only validator and fails closed on unsafe storage. Success or successful rollback removes it. Worker interruption,
failed recreation, or failed rollback retains it. The scheduled deployer and later
settings applies refuse to mutate while this record exists, even after worker restart.
The shared deployment directory lock is never automatically stolen when its owner
is missing or dead; that cannot establish that Docker has finished its work.

The audit preserves each original and rollback failure separately: stage, command
category, exit code (null for timeout), elapsed milliseconds and fixed diagnostic
signals such as `docker_timeout`, `port_conflict` or `compose_container_config`.
It deliberately discards free-form stdout/stderr, which can contain arbitrary secrets.
An unrecognized error retains its category/code/duration but not its raw message.
The recovery record also retains the original error, any rollback error, and a
read-only observation of affected container states. A running container alone does
not prove that the requested configuration is active or the daemon request is complete.

For an uncertain recreation, the proposed `.env` remains in place with its original
private backup; the worker does not rewrite it while Docker may still consume it.
The browser receives a recovery-required error, never a success claim. A separate recovery notice remains visible after refresh and prevents further previews/applies; state exposes only a hold boolean, not the private record. Automatic
availability recovery is intentionally held until a host operator resolves ambiguity.

Recovery procedure (explicitly coordinated host maintenance, never an automatic retry):

1. Keep scheduled deployment and settings requests quiescent. Inspect the audit,
   recovery record, worker/process state and Docker events/status without dumping env.
2. Establish that the old Compose client and its daemon operation have completed.
   If completion cannot be established, retain the hold; elapsed time or one running
   container observation is insufficient.
3. Under the same deployment lock, choose the desired configuration or recorded
   backup and perform at most one approved reconciliation. Verify affected runtime
   configuration and health before clearing the recovery record.
4. Clear an abandoned directory lock only after reviewing its former owner and
   Docker work. Resume scheduled deployment only after releasing the maintenance
   lock. Do not clear the recovery record merely to let autodeploy race a retry.

Ship worker and deployer changes together in one coordinated release. Production
acceptance of endpoint changes remains a separate approved operation.

## Setting classes

### Editable in the browser

- `NAS_HOST`
- `LIBRECHAT_SCHEME`
- `LIBRECHAT_PORT`
- `ADMIN_PANEL_URL`
- `NO_INDEX`
- `SEARCH`
- `SESSION_COOKIE_SECURE`
- `ALLOW_EMAIL_LOGIN`
- `ALLOW_REGISTRATION`
- `ALLOW_SOCIAL_LOGIN`
- `ALLOW_SOCIAL_REGISTRATION`
- `ALLOW_UNVERIFIED_EMAIL_LOGIN`
- `ALLOW_PASSWORD_RESET`

`DOMAIN_CLIENT` and `DOMAIN_SERVER` are derived from scheme/host/port and are not edited independently.

### Replace-only secrets in the browser

The current value is never returned. The UI shows only configured/not-configured state and can submit a non-empty replacement:

- `OPENROUTER_KEY`
- `GITHUB_DEPLOY_STATUS_TOKEN`
- `GITHUB_TELEMETRY_TOKEN`
- `CLOUDFLARE_TUNNEL_TOKEN`

Intentional clearing remains a host-CLI operation so an empty browser field means "leave unchanged" rather than "delete secret".

### Host-managed panel transport/authentication

These are deliberately hidden from the web panel so it cannot disconnect or de-authenticate its own active request:

- `ADMIN_SETTINGS_PORT`
- `ADMIN_SETTINGS_ACCESS_TOKEN`

Use `bootstrap-admin-settings.py` or the local `manage-env.py` CLI for these.

### Locked security material

Routine GUI editing is prohibited:

- `JWT_SECRET`
- `JWT_REFRESH_SECRET`
- `CREDS_KEY`
- `CREDS_IV`

Any future rotation must be a separate maintenance workflow with recovery guidance.

### Internal/fixed values

Not exposed as normal controls:

- `COMPOSE_PROJECT_NAME`
- container `HOST`
- container `PORT`
- `MONGO_URI`

## Authentication and CSRF model

The panel uses an independent random Bearer token. The browser keeps it only in `sessionStorage` for the current tab and sends it explicitly in the `Authorization` header. The service sets no authentication cookie and permits no CORS access, so cross-site requests do not receive ambient credentials. This removes the normal cookie-based CSRF path while retaining independent service authentication.

`bootstrap-admin-settings.py` generates the token locally when needed and never prints it. It writes a temporary chmod-600 local bootstrap-token file for one-time administrator retrieval; that copy should be deleted after login is confirmed.

## Apply transaction

A normal browser apply is:

1. panel requests current sanitised state;
2. administrator edits allowlisted controls;
3. worker validates and returns a redacted preview plus derived values, warnings and affected services;
4. administrator confirms Apply;
5. worker re-reads current `.env` and re-validates the request;
6. worker creates a local backup, persists a recovery record and atomically writes the proposed values;
7. worker runs Compose validation;
8. affected services are recreated only when required;
9. health checks run;
10. success is audited and returned;
11. pre-recreation failures restore `.env` without a needless restart; health failure after completed recreation restores and recreates the prior runtime; uncertain recreation or failed rollback retains the recovery hold for host review.


Secret values are neither returned in state/preview nor written to audit output.

## Autodeploy integration

`autodeploy.sh` now treats the admin service similarly to the optional Cloudflare overlay:

- if `ADMIN_SETTINGS_ACCESS_TOKEN` is absent, the admin integration remains disabled;
- if configured, the admin compose overlay is loaded;
- the host worker service is installed/enabled/restarted from the checked-out deployment code;
- panel + worker health become part of steady-state/deployment validation;
- diagnostics include panel logs and local worker service status without dumping `.env`.

This means the normal DSM autodeploy task remains the deployment owner; no second deployment scheduler is introduced.

## Safety contract

v0.1 is designed to satisfy:

- independent authentication at the panel boundary;
- no raw environment dump/editor endpoint;
- no arbitrary shell/command endpoint;
- server-side allowlist enforcement;
- no browser exposure of stored secrets;
- no secret values in audit records;
- atomic `.env` writes and timestamped local backups;
- unmanaged `.env` lines/comments preserved;
- duplicate managed keys rejected;
- typed validation for booleans, ports, schemes, hosts and URLs;
- restart/recreate impact shown in preview;
- Compose validation before runtime changes;
- affected-service health checks;
- automatic `.env` rollback when no Docker operation is uncertain, with a persistent hold otherwise;
- locked JWT/credential material excluded from routine UI changes;
- browser-facing service has neither `.env` nor Docker access.

## Bootstrap / rollout

After the code has reached the NAS:

```bash
cd /volume1/docker/librechat/deploy/synology
sudo python3 bootstrap-admin-settings.py
```

Retrieve the generated token once:

```bash
sudo cat /volume1/docker/librechat/admin-settings-bootstrap-token.txt
```

After the next successful autodeploy, open the configured `ADMIN_PANEL_URL`, verify login/state/preview/apply, then remove the temporary token copy:

```bash
sudo rm -f /volume1/docker/librechat/admin-settings-bootstrap-token.txt
```

## Acceptance criteria

Before declaring NAS rollout complete, verify on the actual Synology host:

- ordinary LibreChat users are not shown the Admin panel link;
- an authorised LibreChat admin can follow the link;
- the panel rejects missing/incorrect Bearer tokens;
- current provider/GitHub/Cloudflare secret values never appear in browser responses or logs;
- invalid settings are rejected before `.env` mutation;
- a safe non-secret change previews correctly, recreates only the expected service, and passes health checks;
- a secret replacement shows only configured state before/after;
- unmanaged `.env` lines survive a successful change;
- worker/panel remain healthy across a normal autodeploy run;
- a deliberately invalid deployment-level change in a controlled test exercises rollback without losing the prior healthy runtime.

Automated CI validates Python syntax, JSON, shell syntax and the non-Docker regression tests. Actual Docker/systemd/rollback behavior still requires this final NAS-host verification because GitHub Actions is not the Synology runtime.
