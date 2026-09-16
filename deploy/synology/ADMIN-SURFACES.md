# Synology administration surface contract

## Current architecture

Synology now presents one primary administration UI: the LibreChat Admin Panel derivative on the normal Admin Panel origin.

The derivative keeps the upstream Admin Panel application-management surface and adds one native `Deployment` route. That route embeds the Synology deployment controls through the same-origin `/deployment-control/` path.

The browser-facing shape is therefore:

- Dashboard / users / access / grants / configuration: upstream LibreChat Admin Panel responsibilities;
- Deployment: Synology host and environment administration;
- `/deployment-control/`: same-origin bridge from the Admin Panel to the internal deployment gateway.

The deployment gateway is not published on a host port. It exists only on the LibreChat Docker network and forwards to the existing Deployment Settings service.

The standalone Deployment Settings port (`3210` by default) remains temporarily available as the independent recovery path.

## Ownership boundary

### LibreChat Admin Panel owns

- users, groups, roles and membership;
- system grants and delegated administration;
- schema-driven LibreChat configuration and scoped overrides;
- other application-level capabilities exposed through LibreChat's admin APIs.

The upstream configuration editor is driven by LibreChat's configuration schema. Its existence does not make host `.env` values equivalent to LibreChat configuration fields.

### Synology Deployment owns

- NAS addressing and browser-visible deployment URLs;
- host-side `.env` values and environment-backed provider credentials;
- OCR, web-search, coding-executor and other capability service endpoints/credentials that are injected through the deployment environment;
- Synology, Cloudflare and GitHub deployment integrations;
- Compose validation and selective recreation;
- service health checks;
- host deployment backup and rollback;
- locked deployment security material and independent break-glass recovery.

Provider keys or similarly named values must not be removed merely because the upstream Admin Panel has a generic Configuration screen. Removal requires a proven upstream owner with equivalent persistence, secret handling, restart semantics and runtime behaviour.

## Privilege boundary

The Admin Panel container has no Docker socket and no private host `.env` mount.

The internal deployment gateway has no Docker socket and performs no host mutation itself.

Privileged deployment changes continue to pass through the existing restricted host worker over the Unix-domain socket. The worker remains responsible for allowlisting, validation, preview, backup, mutation, selective recreation, health checking and rollback.

Embedding Deployment in the Admin Panel changes presentation and routing; it does not move host privileges into the browser-facing application.

## Authentication boundary

Today there are two authentication layers:

1. the LibreChat Admin Panel session protects the primary Admin Panel application;
2. Synology Deployment Settings retains its independent password/recovery authentication.

The second layer must not simply be deleted. `/deployment-control/*` is a raw server route as well as an iframe target, so removing Deployment Settings authentication before the bridge itself can prove an authenticated LibreChat administrator session would expose privileged controls through a direct URL.

The intended next state is:

- routine access to Deployment requires a valid LibreChat Admin Panel administrator session;
- the browser never receives the Deployment recovery token or an unrestricted host credential;
- direct unauthenticated requests to `/deployment-control/*` fail closed;
- the independent port-3210 recovery path remains available for break-glass use;
- logout/session expiry must also invalidate routine Deployment access within a bounded interval;
- recovery authentication remains independent of the LibreChat application session so an application-auth failure cannot remove the operator's recovery path.

Any authentication-unification implementation must be covered by tests for direct-route denial, authenticated access, expiry/logout behaviour and recovery-path independence before the second routine login is removed.

## Session secret

The official-derived Admin Panel uses its own `ADMIN_PANEL_SESSION_SECRET`. `bootstrap-admin-settings.py --ensure-session-secret` creates a missing value without printing it, preserves an existing value exactly and fails closed on duplicates.

The Admin Panel session secret must remain independent from the Deployment Settings recovery credential.

## Health and rollout

With the administration overlay enabled, healthy steady state requires:

- LibreChat API health;
- the official-derived `librechat-admin-panel` container;
- the same-origin `/deployment-control/health` path;
- the internal deployment gateway;
- the Deployment Settings service and restricted worker.

The derivative Admin Panel image is published to GHCR from the reviewed `server/synology` branch. Synology reconciliation should occur only after the corresponding image publish succeeds so the rolling branch tag cannot race the Compose switch.

The standalone Deployment Settings port remains a rollback/recovery surface until the integrated route has proven stable on the NAS and the routine-auth bridge has passed its security tests.

## Cleanup rule

Do not remove a Deployment setting because its label sounds application-level. Remove or relocate it only when the replacement owner is explicit and equivalent across persistence, secrecy, validation, restart behaviour and failure recovery.

Do not remove the restricted host worker merely because Deployment is now visually integrated with the Admin Panel; the upstream panel does not replace host-side Compose/`.env` transactions or rollback duties.
