#!/bin/sh
set -eu

DATA_DIR="/volume1/docker/librechat-code-interpreter-data"
MASTER_ENV="$DATA_DIR/codeapi.env"
WORKER_ID="${1:-justin-wsl}"
ENDPOINT="http://127.0.0.1:3112/v1"
CURL_IMAGE="curlimages/curl:8.10.1"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo/root so the private bridge administrator credential is never exposed." >&2
  exit 1
fi

[ -f "$MASTER_ENV" ] || { echo "Code Interpreter is not bootstrapped." >&2; exit 1; }
case "$WORKER_ID" in
  ''|*[!A-Za-z0-9._:-]*) echo "Invalid worker id: $WORKER_ID" >&2; exit 2 ;;
esac

TOKEN="$(sed -n 's/^CODEAPI_BRIDGE_TOKEN=//p' "$MASTER_ENV" | head -n 1)"
[ -n "$TOKEN" ] || { echo "CODEAPI_BRIDGE_TOKEN is missing." >&2; exit 1; }

# Verify the loopback-only Code API is reachable before issuing a one-time code.
docker run --rm --network host "$CURL_IMAGE" -fsS "$ENDPOINT/health" >/dev/null

BODY="$(printf '{\"workerId\":\"%s\"}' "$WORKER_ID")"
RESPONSE="$(docker run --rm --network host \
  -e LC_BRIDGE_TOKEN="$TOKEN" \
  -e LC_PAIR_BODY="$BODY" \
  "$CURL_IMAGE" sh -lc '
    curl -fsS -X POST \
      -H "Authorization: Bearer $LC_BRIDGE_TOKEN" \
      -H "Content-Type: application/json" \
      --data "$LC_PAIR_BODY" \
      http://127.0.0.1:3112/v1/bridge/pairings
  ')"

# Print only the one-time enrollment material. Never print the administrator token.
python3 - "$ENDPOINT" "$WORKER_ID" "$RESPONSE" <<'PY'
import json, sys
endpoint, worker_id, raw = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    payload = json.loads(raw)
except Exception as exc:
    raise SystemExit(f'Could not parse pairing response: {exc}')
code = payload.get('code') or payload.get('pairingCode') or payload.get('pairing_code')
if not code:
    raise SystemExit('Pairing response did not include a one-time code')
print(f'endpoint={endpoint}')
print(f'worker_id={worker_id}')
print(f'pairing_code={code}')
expires = payload.get('expiresAt') or payload.get('expires_at')
if expires:
    print(f'expires_at={expires}')
print('The pairing code is single-use and short-lived. It is not the Code API administrator token.')
PY
