# Synology LibreChat telemetry

This branch is written by the Synology LibreChat deployment task and is intentionally separate from `server/synology` so telemetry updates cannot trigger deployment.

Published data is allow-listed and sanitised. It may contain deployment SHA, stage/result, container state, workspace/HTTP/tunnel health, disk utilisation percentage, and messages emitted by the deployment script itself.

It must never contain `.env` contents, API keys, bearer/tunnel tokens, cookies, Docker environment dumps, raw application logs, or raw cloudflared logs.

Files:
- `latest.json` — current deployment/runtime snapshot.
- `latest.log` — recent sanitised autodeploy event messages only.
- `history/` — snapshots written for deployment failure/success events.
