# Synology administration surfaces

## Purpose

The Synology deployment now treats LibreChat application administration and NAS deployment administration as separate concerns.

### Official LibreChat Admin Panel

Use the upstream LibreChat Admin Panel for application-level administration:

- users, groups, roles and membership;
- system grants and delegated administration;
- schema-driven LibreChat configuration and scoped overrides;
- other capabilities provided by LibreChat's `/api/admin/*` surface.

The Synology overlay uses the upstream container image and connects it to the existing `api` service. The browser-facing host port defaults to `3220` while the container continues to listen on its upstream-standard port `3000`.

`ADMIN_PANEL_URL` now belongs to this upstream panel. LibreChat uses it for the admin-only Settings link and admin OAuth/SSO redirects.

### Synology Deployment Settings

The custom service previously described as the Synology Admin Settings panel remains because it controls a different layer:

- host-side `.env` values;
- deployment/provider credentials that must remain environment-backed;
- Synology/Cloudflare/GitHub deployment integrations;
- Compose validation;
- selective service recreation;
- health checks;
- backup and rollback of host deployment state.

It must not become a second implementation of LibreChat user/role/grant/configuration administration.

The custom panel continues to use port `3210` by default. Its existing internal variable and file names (`ADMIN_SETTINGS_*`, `admin-settings-*`) are retained for compatibility even though the user-facing role is now **Synology Deployment Settings**.

## Security boundary

The official LibreChat Admin Panel authenticates against LibreChat and is authorised by LibreChat's admin APIs.

The Synology Deployment Settings panel remains independently authenticated. Its browser-facing container has no private `.env` mount and no Docker socket. Privileged changes continue to be performed by the host worker over the restricted Unix-domain socket with allowlisting, preview, backup, validation, health checks and rollback.

Do not merge the two trust boundaries simply because both are administrative UIs.

## Session secret

The official Admin Panel requires an independent session secret. `bootstrap-admin-settings.py` now ensures that `ADMIN_PANEL_SESSION_SECRET` exists without printing it.

For one deployment only, `docker-compose.admin.yml` falls back to the existing deployment-settings recovery token when the dedicated Admin Panel secret has not yet been bootstrapped. This is a migration compatibility path, not the desired steady state.

After deploying this change, run:

```bash
cd /volume1/docker/librechat/deploy/synology
sudo python3 bootstrap-admin-settings.py
```

The bootstrap preserves any deliberate existing external `ADMIN_PANEL_URL`, but migrates the known legacy local Deployment Settings URL to the official panel URL. The default local URLs become:

- LibreChat: `http://<NAS_HOST>:3200`
- Synology Deployment Settings: `http://<NAS_HOST>:3210`
- LibreChat Admin Panel: `http://<NAS_HOST>:3220`

Ports remain configurable in `.env`.

## Rollout sequence

1. Merge only after CI is green.
2. Allow the normal Synology autodeploy to deploy the reviewed branch.
3. Confirm the existing LibreChat API and Synology Deployment Settings remain healthy.
4. Run `bootstrap-admin-settings.py` once to create the dedicated upstream-panel session secret and migrate the legacy local `ADMIN_PANEL_URL` when applicable.
5. Let the next autodeploy/reconciliation recreate the affected services if required.
6. Open the official Admin Panel directly on its configured port and authenticate with a LibreChat administrator account.
7. Confirm LibreChat's Settings -> General admin link now opens the official panel.
8. Confirm the Deployment Settings UI is still reachable directly on its own port and continues to manage only host/deployment concerns.

## Future cleanup

`docker-compose.librechat-admin.yml` is retained as a standalone upstream-panel overlay so the official panel can later be decoupled from `docker-compose.admin.yml`. Once the upstream panel has proven stable and any remaining overlap has been audited, the custom Deployment Settings UI can be reduced further or disabled without removing LibreChat's administration surface.

Do not remove the privileged deployment worker merely because the upstream panel exists; the upstream panel does not replace host-side Compose/.env transaction and rollback duties.
