# LibreChat on Synology

This deployment is intentionally small for the first side-by-side comparison with AgenticSeek on a Synology DS918+-class NAS with an Intel J3455 and 4 GB RAM.

## Initial scope

The first milestone runs only:

- LibreChat API/UI on NAS port `3200`
- MongoDB `4.4.18`
- OpenRouter using `deepseek/deepseek-v3.2`

Meilisearch, RAG/pgvector, code execution, extra MCP tools, and browser automation are intentionally left out of the first boot. They can be added after measuring baseline RAM, swap, and responsiveness.

MongoDB `4.4.18` is used because LibreChat's own Docker override example identifies it as the compatibility option for older CPUs without AVX support.

## Clone on Synology without host Git

Create the destination if needed:

```bash
sudo mkdir -p /volume1/docker/librechat
sudo chown 1026:100 /volume1/docker/librechat
```

Clone this branch using the Git container:

```bash
sudo docker run --rm --user 1026:100 -v /volume1/docker/librechat:/repo alpine/git clone --branch server/synology --single-branch https://github.com/justinthenick/LibreChat.git /repo
```

For later source updates:

```bash
sudo docker run --rm --user 1026:100 -v /volume1/docker/librechat:/repo alpine/git -C /repo pull --ff-only
```

## Private runtime configuration

```bash
cd /volume1/docker/librechat/deploy/synology
cp .env.example .env
chmod 600 .env
```

The `.env` file is private runtime state and must not be committed.

The Synology deployment now treats `.env` as the single source for normal host/application toggles. `DOMAIN_CLIENT` and `DOMAIN_SERVER` are derived by Compose from `LIBRECHAT_SCHEME`, `NAS_HOST`, and `LIBRECHAT_PORT`, so they do not need to be maintained separately. `SEARCH` and `SESSION_COOKIE_SECURE` are also taken from `.env`; they are no longer hard-coded by Compose.

### Safer settings helper

`manage-env.py` provides a schema-driven alternative to hand-editing routine values. It has no raw-edit command, does not reveal configured secret values, preserves unmanaged lines/comments, rejects duplicate managed keys, and makes a chmod-600 local backup before each write.

Show the current managed settings:

```bash
python3 manage-env.py show
```

Validate values:

```bash
python3 manage-env.py validate
```

Change a normal setting:

```bash
python3 manage-env.py set SEARCH true
```

Replace a secret without echoing it:

```bash
python3 manage-env.py set-secret OPENROUTER_KEY
```

Validate the resulting Compose configuration:

```bash
sudo python3 manage-env.py compose-check
```

The helper deliberately does **not** rotate `JWT_SECRET`, `JWT_REFRESH_SECRET`, `CREDS_KEY`, or `CREDS_IV`. Those are locked security material and need a separate maintenance workflow because changing them can invalidate sessions or stored credentials.

For an existing `.env` created before the managed-settings work, add the optional admin-panel placeholder once if it is absent:

```bash
python3 manage-env.py set ADMIN_PANEL_URL ''
```

This does not enable an admin service; it simply makes the existing file match the current managed template.

If the existing AgenticSeek deployment already has the current OpenRouter key, it can be copied without printing the secret to the terminal:

```bash
OR_KEY=$(sed -n 's/^OPENROUTER_API_KEY=//p' /volume1/docker/agenticseek/deploy/synology/.env | head -n 1)
```

```bash
printf '%s' "$OR_KEY" | python3 manage-env.py set-secret OPENROUTER_KEY --stdin --yes
```

```bash
unset OR_KEY
```

Verify presence without displaying the value:

```bash
python3 manage-env.py show | grep OPENROUTER_KEY
```

LibreChat can generate temporary JWT/credential secrets into the persistent `/app/data/.env.temp` volume when the corresponding values in `.env` are blank. Before any Internet-facing or long-term production deployment, replace them with unique persistent values in the private `.env` file using a separate controlled rotation process.

## Validate and pull images

This NAS uses standalone Compose v1, so use `docker-compose`, not `docker compose`.

```bash
cd /volume1/docker/librechat/deploy/synology
sudo docker-compose config >/dev/null && echo 'Compose config OK'
```

```bash
sudo docker-compose pull
```

No local image build is required.

## First boot

AgenticSeek can remain running on port `3100`; LibreChat uses `3200`.

```bash
sudo docker-compose up -d
```

```bash
sudo docker-compose ps
```

```bash
sudo docker-compose logs --tail=100 api
```

From a browser on the LAN:

```text
http://192.168.1.5:3200
```

Create the initial LibreChat account, select the OpenRouter endpoint and `deepseek/deepseek-v3.2`, then perform the same baseline prompt used with AgenticSeek.

## Resource comparison

Immediately after startup and again after a few prompts:

```bash
sudo docker stats --no-stream
```

```bash
free -h
```

The goal of this initial deployment is to compare LibreChat and AgenticSeek under the same NAS, provider, and model before enabling additional LibreChat services.

## Admin settings direction

`ADMIN_PANEL_URL` is now an optional managed setting and is passed through to LibreChat. It remains blank until the separate Synology Admin Settings service is implemented and authenticated. The intended design is documented in `ADMIN-SETTINGS.md`; the command-line manager is the first reusable backend/safety layer for that future UI.

## Security

This first deployment is intended for a trusted LAN only. Do not port-forward `3200` to the Internet. LibreChat provides authentication, but remote access should later use a VPN/Tailscale or a properly secured reverse proxy.
