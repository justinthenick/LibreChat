#!/bin/sh
set -eu

REPO_DIR="/volume1/docker/librechat"
DEPLOY_DIR="$REPO_DIR/deploy/synology"
LIBRECHAT_ENV="$DEPLOY_DIR/.env"
SOURCE_DIR="/volume1/docker/librechat-code-interpreter"
DATA_DIR="/volume1/docker/librechat-code-interpreter-data"
CODEAPI_ENV="$DATA_DIR/codeapi.env"
MANAGER="$DEPLOY_DIR/manage-code-interpreter.sh"
NODE_IMAGE="node:22-alpine"
COMPOSE_HTTP_TIMEOUT="${COMPOSE_HTTP_TIMEOUT:-300}"
export COMPOSE_HTTP_TIMEOUT

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this bootstrap with sudo/root so it can manage Docker, /dev/kvm and private env files." >&2
  exit 1
fi

[ -f "$LIBRECHAT_ENV" ] || { echo "Missing $LIBRECHAT_ENV" >&2; exit 1; }
[ -x "$MANAGER" ] || [ -f "$MANAGER" ] || { echo "Missing $MANAGER" >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "Docker daemon unavailable" >&2; exit 1; }

# Do not weaken isolation automatically. Upstream explicitly classifies the
# direct NsJail path as a development mode because it shares the host kernel.
if [ ! -c /dev/kvm ]; then
  echo "ERROR: /dev/kvm is not available on this NAS." >&2
  echo "Refusing to enable the weaker host-kernel NsJail fallback automatically." >&2
  exit 1
fi

if [ ! -r /dev/kvm ] || [ ! -w /dev/kvm ]; then
  echo "ERROR: /dev/kvm exists but is not usable by the deployment task." >&2
  exit 1
fi

docker network inspect librechat_librechat >/dev/null 2>&1 || {
  echo "ERROR: LibreChat Docker network librechat_librechat is missing." >&2
  exit 1
}

log "Preparing pinned Code Interpreter source"
sh "$MANAGER" source

mkdir -p "$DATA_DIR"
chmod 0700 "$DATA_DIR"
STAMP="$(date -u '+%Y%m%dT%H%M%SZ')"
LIBRECHAT_BACKUP="$LIBRECHAT_ENV.before-codeapi-$STAMP"
cp -p "$LIBRECHAT_ENV" "$LIBRECHAT_BACKUP"
chmod 0600 "$LIBRECHAT_BACKUP"
CODEAPI_EXISTED=0
CODEAPI_BACKUP=""
if [ -f "$CODEAPI_ENV" ]; then
  CODEAPI_EXISTED=1
  CODEAPI_BACKUP="$CODEAPI_ENV.before-bootstrap-$STAMP"
  cp -p "$CODEAPI_ENV" "$CODEAPI_BACKUP"
  chmod 0600 "$CODEAPI_BACKUP"
else
  : > "$CODEAPI_ENV"
  chmod 0600 "$CODEAPI_ENV"
fi

ROLLBACK_NEEDED=1
rollback() {
  RC=$?
  trap - EXIT INT TERM
  if [ "$ROLLBACK_NEEDED" = "1" ]; then
    log "Bootstrap failed; restoring previous private configuration"
    cp -p "$LIBRECHAT_BACKUP" "$LIBRECHAT_ENV" || true
    chmod 0600 "$LIBRECHAT_ENV" 2>/dev/null || true
    if [ "$CODEAPI_EXISTED" = "1" ] && [ -n "$CODEAPI_BACKUP" ]; then
      cp -p "$CODEAPI_BACKUP" "$CODEAPI_ENV" || true
      chmod 0600 "$CODEAPI_ENV" 2>/dev/null || true
    else
      rm -f "$CODEAPI_ENV" 2>/dev/null || true
    fi
    sh "$MANAGER" down >/dev/null 2>&1 || true
    cd "$DEPLOY_DIR" || true
    docker-compose -f docker-compose.yml up -d --no-deps --force-recreate api >/dev/null 2>&1 || true
    log "Previous LibreChat configuration restored"
  fi
  exit "$RC"
}
trap rollback EXIT INT TERM

log "Generating/reusing LibreChat JWT and execution-manifest keypairs"
# This is the upstream Code Interpreter helper from the exact pinned source.
# The source tree is read-only in the helper container; only the two private env
# files are writable. It never prints private key material.
docker run --rm \
  -v "$SOURCE_DIR:/codeapi:ro" \
  -v "$REPO_DIR:/librechat" \
  -v "$DATA_DIR:/codeapi-data" \
  "$NODE_IMAGE" \
  node /codeapi/scripts/setup-local-auth-env.js \
    --librechat-env /librechat/deploy/synology/.env \
    --codeapi-env /codeapi-data/codeapi.env \
    --base-url http://librechat-codeapi:3112/v1

# Add production-only service credentials that upstream's local helper does not
# generate. Values are retained on reruns; missing secrets are generated once.
python3 - "$LIBRECHAT_ENV" "$CODEAPI_ENV" <<'PY'
import os
import re
import secrets
import sys
from pathlib import Path

librechat_path = Path(sys.argv[1])
codeapi_path = Path(sys.argv[2])

def read(path):
    return path.read_text(encoding='utf-8') if path.exists() else ''

def value(text, key):
    m = re.search(r'^' + re.escape(key) + r'=(.*)$', text, flags=re.M)
    if not m:
        return ''
    raw = m.group(1).strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ('"', "'"):
        raw = raw[1:-1]
    return raw

def set_values(path, updates):
    text = read(path)
    for key, val in updates.items():
        line = f'{key}={val}'
        pattern = re.compile(r'^' + re.escape(key) + r'=.*$', flags=re.M)
        if pattern.search(text):
            text = pattern.sub(line, text, count=1)
        else:
            if text and not text.endswith('\n'):
                text += '\n'
            text += line + '\n'
    path.write_text(text, encoding='utf-8')
    os.chmod(path, 0o600)

code_text = read(codeapi_path)

def keep_or_random(key, nbytes=32):
    current = value(code_text, key)
    return current if current else secrets.token_hex(nbytes)

redis_password = keep_or_random('REDIS_PASSWORD')
minio_password = value(code_text, 'MINIO_ROOT_PASSWORD') or value(code_text, 'MINIO_SECRET_KEY') or secrets.token_hex(32)

code_updates = {
    'LOCAL_MODE': 'false',
    'CODEAPI_HARDENED_SANDBOX_MODE': 'true',
    'CODEAPI_ALLOW_AUTH_PROVIDER_NONE': 'false',
    'CODEAPI_EXECUTION_PROFILE': 'default',
    'CODEAPI_TENANT_ISOLATION_STRICT': 'false',
    'CODEAPI_BRIDGE_TOKEN': keep_or_random('CODEAPI_BRIDGE_TOKEN'),
    'CODEAPI_BRIDGE_AUTH_MODE': 'paired',
    'CODEAPI_BRIDGE_DYNAMIC_WORKERS': 'true',
    'CODEAPI_INTERNAL_SERVICE_TOKEN': keep_or_random('CODEAPI_INTERNAL_SERVICE_TOKEN'),
    'CODEAPI_EGRESS_GRANT_SECRET': keep_or_random('CODEAPI_EGRESS_GRANT_SECRET'),
    'CODEAPI_EGRESS_LEDGER_REQUIRED': 'true',
    'REDIS_PASSWORD': redis_password,
    'MINIO_ROOT_USER': 'codeapi',
    'MINIO_ROOT_PASSWORD': minio_password,
    'MINIO_ACCESS_KEY': 'codeapi',
    'MINIO_SECRET_KEY': minio_password,
    'MINIO_BUCKET': 'codeapi',
    'MINIO_ENDPOINT': 'minio',
    'MINIO_PORT': '9000',
    'MINIO_USE_SSL': 'false',
    'KVM_ENABLED': 'true',
    'SANDBOX_REQUIRE_EGRESS_MANIFEST': 'true',
    'SANDBOX_MAX_CONCURRENT_JOBS': '1',
    'PYTHON_CONCURRENCY': '1',
    'OTHER_CONCURRENCY': '2',
}
set_values(codeapi_path, code_updates)
set_values(librechat_path, {'CODE_INTERPRETER_ENABLED': 'true'})
PY

chmod 0600 "$LIBRECHAT_ENV" "$CODEAPI_ENV"

# Fail before building anything if the helper did not leave the expected auth
# contract on both sides. Values are never echoed.
grep -q '^LIBRECHAT_CODE_BASEURL=http://librechat-codeapi:3112/v1$' "$LIBRECHAT_ENV"
grep -q '^CODEAPI_AUTH_PROVIDER=librechat-jwt$' "$LIBRECHAT_ENV"
grep -q '^CODEAPI_JWT_PRIVATE_JWK_JSON=.' "$LIBRECHAT_ENV"
grep -q '^CODEAPI_AUTH_PROVIDER=librechat-jwt$' "$CODEAPI_ENV"
grep -q '^CODEAPI_JWT_JWKS_JSON=.' "$CODEAPI_ENV"
grep -q '^CODEAPI_EXECUTION_MANIFEST_PRIVATE_KEY=.' "$CODEAPI_ENV"
grep -q '^SANDBOX_EXECUTION_MANIFEST_PUBLIC_KEY=.' "$CODEAPI_ENV"

log "Building/starting self-hosted Code Interpreter"
sh "$MANAGER" reconcile

# LibreChat must be recreated after the signer/base URL were added to .env.
log "Recreating LibreChat API with self-hosted Code Interpreter configuration"
cd "$DEPLOY_DIR"
docker-compose -f docker-compose.yml up -d --no-deps --force-recreate api

COUNT=0
until docker exec librechat node -e '
  const http=require("http");
  const r=http.get("http://127.0.0.1:3080/api/config",x=>process.exit(x.statusCode>=200&&x.statusCode<500?0:1));
  r.setTimeout(5000,()=>{r.destroy();process.exit(1)});
  r.on("error",()=>process.exit(1));
' >/dev/null 2>&1; do
  COUNT=$((COUNT+1))
  if [ "$COUNT" -ge 18 ]; then
    echo "ERROR: LibreChat did not become healthy after Code Interpreter bootstrap." >&2
    exit 1
  fi
  sleep 5
done

sh "$MANAGER" check

ROLLBACK_NEEDED=0
trap - EXIT INT TERM
log "Self-hosted Code Interpreter is ready"
printf '%s\n' "CODE_INTERPRETER=READY"
printf '%s\n' "LibreChat base URL: http://librechat-codeapi:3112/v1 (Docker-internal only)"
printf '%s\n' "Private env backup: $LIBRECHAT_BACKUP"
