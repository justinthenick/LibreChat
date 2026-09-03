# LibreChat on Synology

This deployment is intentionally small for a Synology DS918+-class NAS with an Intel J3455 and 4 GB RAM.

## Core scope

The deployment runs:

- LibreChat API/UI on NAS port `3200`
- MongoDB `4.4.18`
- OpenRouter using `deepseek/deepseek-v3.2`
- optional Cloudflare Tunnel overlay
- optional Synology Admin Settings panel on port `3210`

Meilisearch, RAG/pgvector, code execution, extra MCP tools, and browser automation remain outside the baseline deployment.

MongoDB `4.4.18` is used because LibreChat's Docker guidance identifies it as the compatibility option for older CPUs without AVX support.

## Private runtime configuration

```bash
cd /volume1/docker/librechat/deploy/synology
cp .env.example .env
chmod 600 .env
```

The `.env` file is private runtime state and must never be committed.

`DOMAIN_CLIENT` and `DOMAIN_SERVER` are derived by Compose from `LIBRECHAT_SCHEME`, `NAS_HOST`, and `LIBRECHAT_PORT`. `SEARCH`, `NO_INDEX`, `SESSION_COOKIE_SECURE`, and `ADMIN_PANEL_URL` are also controlled by `.env`; Compose no longer silently overrides those managed values.

## Safe command-line settings manager

`manage-env.py` is the low-level management layer used by the browser UI and remains useful over SSH. It has no raw `.env` edit command, never prints configured secrets, preserves unmanaged lines/comments, rejects duplicate managed keys, and creates a chmod-600 backup before every write.

```bash
python3 manage-env.py show
python3 manage-env.py validate
python3 manage-env.py set SEARCH true
python3 manage-env.py set ALLOW_REGISTRATION false
python3 manage-env.py set-secret OPENROUTER_KEY
sudo python3 manage-env.py compose-check
```

`JWT_SECRET`, `JWT_REFRESH_SECRET`, `CREDS_KEY`, and `CREDS_IV` are deliberately locked out of routine management because rotating them can invalidate sessions or stored credentials.

## Synology Admin Settings browser panel

The browser panel uses a split security model:

`browser -> non-privileged admin-settings container -> Unix socket -> privileged host worker -> .env / docker-compose`

The browser-facing container:

- does **not** mount `.env`;
- does **not** receive the Docker socket;
- receives only its independent access token;
- runs read-only with all Linux capabilities dropped;
- stores the access token only in the current browser tab's session storage;
- never receives current secret values from the worker.

The privileged host worker is installed as `librechat-admin-settings-worker.service`. It enforces the same schema allowlist, performs atomic `.env` updates, runs Compose validation, recreates only affected services, health-checks the result, and restores the previous `.env` if apply or health validation fails. Audit records contain changed key names and outcomes, never secret values.

### One-time bootstrap

After this deployment version has reached the NAS, run:

```bash
cd /volume1/docker/librechat/deploy/synology
sudo python3 bootstrap-admin-settings.py
```

Bootstrap will:

- generate an independent random `ADMIN_SETTINGS_ACCESS_TOKEN` if one is not already configured;
- add `ADMIN_SETTINGS_PORT=3210` when needed;
- set `ADMIN_PANEL_URL` to the local NAS URL when it is blank;
- create a chmod-600 `.env` backup;
- write a temporary local bootstrap-token file without printing the token to the terminal.

Retrieve the token locally once:

```bash
sudo cat /volume1/docker/librechat/admin-settings-bootstrap-token.txt
```

Then remove the bootstrap copy after confirming login:

```bash
sudo rm -f /volume1/docker/librechat/admin-settings-bootstrap-token.txt
```

The next normal autodeploy run sees `ADMIN_SETTINGS_ACCESS_TOKEN`, installs/starts the privileged worker, loads `docker-compose.admin.yml`, starts the browser panel, recreates LibreChat so the Admin panel link becomes visible, and validates panel/worker health.

The expected LAN URL is:

```text
http://192.168.1.5:3210
```

LibreChat administrators can also reach it from **Settings -> General -> Admin panel** once `ADMIN_PANEL_URL` is active.

### Browser apply workflow

The UI is intentionally staged:

1. enter the independent admin-settings access token;
2. review current allowlisted settings and secret configured/not-configured state;
3. edit normal settings or enter replacement secrets;
4. preview changed keys, derived URLs, restart impact, and warnings;
5. confirm Apply;
6. worker backs up `.env`, validates the change, runs `docker-compose config`, recreates only affected services, and health-checks them;
7. on failure the previous `.env` is restored and the previous runtime is recreated.

Panel transport settings (`ADMIN_SETTINGS_PORT` and the panel access token itself) remain host-managed so the panel cannot disconnect itself while applying a change. Change those through the local CLI/bootstrap path instead.

## Existing OpenRouter key migration

If another local deployment already contains the current OpenRouter key, it can be copied without printing it:

```bash
OR_KEY=$(sed -n 's/^OPENROUTER_API_KEY=//p' /volume1/docker/agenticseek/deploy/synology/.env | head -n 1)
printf '%s' "$OR_KEY" | python3 manage-env.py set-secret OPENROUTER_KEY --stdin --yes
unset OR_KEY
```

Verify only its configured state:

```bash
python3 manage-env.py show | grep OPENROUTER_KEY
```

## Validate and deploy

This NAS uses standalone Compose v1, so use `docker-compose`, not `docker compose`.

```bash
cd /volume1/docker/librechat/deploy/synology
sudo python3 manage-env.py compose-check
sudo docker-compose pull
sudo docker-compose up -d
```

Normal production updates should continue through `autodeploy.sh`; when the admin-settings token is configured it automatically includes the admin overlay and manages the privileged worker service.

## Health / diagnostics

```bash
sudo docker-compose ps
sudo docker-compose logs --tail=100 api
sudo docker logs --tail=100 librechat-admin-settings
sudo systemctl status librechat-admin-settings-worker.service --no-pager
```

The local admin-settings audit log is:

```text
/volume1/docker/librechat/admin-settings-state/audit.log
```

It contains no secret values.

## Security

Keep the private `.env`, bootstrap token and admin access token off GitHub and out of chat/log output. The admin panel is independently authenticated, but port `3210` should still be treated as a trusted-management interface rather than Internet-facing public UI.

Do not port-forward LibreChat or the admin-settings port directly to the Internet. Remote access should use a properly secured VPN, reverse proxy, or Cloudflare Access policy. A Cloudflare Tunnel token by itself is not an access policy.

See `ADMIN-SETTINGS.md` for the detailed design/safety contract.
