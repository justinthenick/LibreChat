#!/bin/sh
set -eu

REPO_DIR="/volume1/docker/librechat"
DEPLOY_DIR="$REPO_DIR/deploy/synology"
LIBRECHAT_ENV="$DEPLOY_DIR/.env"
SOURCE_DIR="/volume1/docker/librechat-code-interpreter"
DATA_DIR="/volume1/docker/librechat-code-interpreter-data"
MASTER_ENV="$DATA_DIR/codeapi.env"
MANAGER="$DEPLOY_DIR/manage-code-interpreter.sh"
NODE_IMAGE="node:22-alpine"
EXPECTED_LIBRECHAT_IMAGE="librechat/lc-dev:f50c40e2f583b03262d600299e94e85411785fe3"
WORKER_ID="justin-wsl"
COMPOSE_HTTP_TIMEOUT="${COMPOSE_HTTP_TIMEOUT:-300}"
export COMPOSE_HTTP_TIMEOUT

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this bootstrap with sudo/root so it can manage Docker and private env files." >&2
  exit 1
fi

[ -f "$LIBRECHAT_ENV" ] || { echo "Missing $LIBRECHAT_ENV" >&2; exit 1; }
[ -f "$MANAGER" ] || { echo "Missing $MANAGER" >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "Docker daemon unavailable" >&2; exit 1; }
docker network inspect librechat_librechat >/dev/null 2>&1 || {
  echo "ERROR: LibreChat Docker network librechat_librechat is missing." >&2
  exit 1
}

CURRENT_IMAGE="$(docker inspect -f '{{.Config.Image}}' librechat 2>/dev/null || true)"
if [ "$CURRENT_IMAGE" != "$EXPECTED_LIBRECHAT_IMAGE" ]; then
  echo "ERROR: LibreChat runtime is $CURRENT_IMAGE" >&2
  echo "Remote Code Bridge requires the validated attached-environment runtime $EXPECTED_LIBRECHAT_IMAGE" >&2
  echo "Deploy the feature PR first, then rerun this bootstrap." >&2
  exit 1
fi

log "Preparing pinned Code Interpreter source"
sh "$MANAGER" source

mkdir -p "$DATA_DIR"
chmod 0700 "$DATA_DIR"
STAMP="$(date -u '+%Y%m%dT%H%M%SZ')"
LIBRECHAT_BACKUP="$LIBRECHAT_ENV.before-codeapi-$STAMP"
cp -p "$LIBRECHAT_ENV" "$LIBRECHAT_BACKUP"
chmod 0600 "$LIBRECHAT_BACKUP"

# Preserve every existing Code Interpreter private file so a failed bootstrap
# can restore the exact previous control-plane state.
BACKUP_DIR="$DATA_DIR/backup-$STAMP"
mkdir -p "$BACKUP_DIR"
chmod 0700 "$BACKUP_DIR"
for F in codeapi.env api.env worker.env egress.env tools.env files.env redis.env minio.env; do
  if [ -f "$DATA_DIR/$F" ]; then
    cp -p "$DATA_DIR/$F" "$BACKUP_DIR/$F"
    chmod 0600 "$BACKUP_DIR/$F"
  fi
done

if [ ! -f "$MASTER_ENV" ]; then
  : > "$MASTER_ENV"
  chmod 0600 "$MASTER_ENV"
fi

ROLLBACK_NEEDED=1
rollback() {
  RC=$?
  trap - EXIT INT TERM
  if [ "$ROLLBACK_NEEDED" = "1" ]; then
    log "Bootstrap failed; restoring previous private configuration"
    cp -p "$LIBRECHAT_BACKUP" "$LIBRECHAT_ENV" || true
    chmod 0600 "$LIBRECHAT_ENV" 2>/dev/null || true
    for F in codeapi.env api.env worker.env egress.env tools.env files.env redis.env minio.env; do
      if [ -f "$BACKUP_DIR/$F" ]; then
        cp -p "$BACKUP_DIR/$F" "$DATA_DIR/$F" || true
        chmod 0600 "$DATA_DIR/$F" 2>/dev/null || true
      else
        rm -f "$DATA_DIR/$F" 2>/dev/null || true
      fi
    done
    sh "$MANAGER" down >/dev/null 2>&1 || true
    cd "$DEPLOY_DIR" || true
    docker-compose -f docker-compose.yml up -d --no-deps --force-recreate api >/dev/null 2>&1 || true
    log "Previous LibreChat configuration restored"
  fi
  exit "$RC"
}
trap rollback EXIT INT TERM

log "Generating/reusing LibreChat JWT and execution-manifest keypairs"
# Upstream helper: creates LibreChat's Ed25519 JWT signer and Code API's public
# verifier plus the execution-manifest keypair. It never prints private keys.
docker run --rm \
  -v "$SOURCE_DIR:/codeapi:ro" \
  -v "$REPO_DIR:/librechat" \
  -v "$DATA_DIR:/codeapi-data" \
  "$NODE_IMAGE" \
  node /codeapi/scripts/setup-local-auth-env.js \
    --librechat-env /librechat/deploy/synology/.env \
    --codeapi-env /codeapi-data/codeapi.env \
    --base-url http://librechat-codeapi:3112/v1

# Add remote-bridge policy and generate production-only internal credentials.
# Then fan the master file out into least-privilege per-service env files.
python3 - "$LIBRECHAT_ENV" "$MASTER_ENV" "$DATA_DIR" "$WORKER_ID" <<'PY'
import os
import re
import secrets
import sys
from pathlib import Path

librechat_path = Path(sys.argv[1])
master_path = Path(sys.argv[2])
data_dir = Path(sys.argv[3])
worker_id = sys.argv[4]

def read(path):
    return path.read_text(encoding='utf-8') if path.exists() else ''

def parse(text):
    out = {}
    for line in text.splitlines():
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out

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

def raw_value(values, key):
    return values.get(key, '')

def keep_or_random(values, key, nbytes=32):
    current = raw_value(values, key).strip()
    return current if current else secrets.token_hex(nbytes)

master = parse(read(master_path))
redis_password = keep_or_random(master, 'REDIS_PASSWORD')
minio_password = raw_value(master, 'MINIO_ROOT_PASSWORD').strip() or raw_value(master, 'MINIO_SECRET_KEY').strip() or secrets.token_hex(32)
bridge_token = keep_or_random(master, 'CODEAPI_BRIDGE_TOKEN')
internal_token = keep_or_random(master, 'CODEAPI_INTERNAL_SERVICE_TOKEN')
egress_secret = keep_or_random(master, 'CODEAPI_EGRESS_GRANT_SECRET')

master_updates = {
    'LOCAL_MODE': 'false',
    'CODEAPI_HARDENED_SANDBOX_MODE': 'true',
    'CODEAPI_ALLOW_AUTH_PROVIDER_NONE': 'false',
    'CODEAPI_SANDBOX_BACKEND': 'remote-bridge',
    'CODEAPI_EXECUTION_PROFILE': 'stateful',
    'CODEAPI_RUNTIME_SESSION_MODE': 'affinity',
    'CODEAPI_BRIDGE_TOKEN': bridge_token,
    'CODEAPI_BRIDGE_AUTH_MODE': 'paired',
    'CODEAPI_BRIDGE_DYNAMIC_WORKERS': 'false',
    'CODEAPI_BRIDGE_WORKER_ID': worker_id,
    'CODEAPI_INTERNAL_SERVICE_TOKEN': internal_token,
    'CODEAPI_EGRESS_GRANT_SECRET': egress_secret,
    'CODEAPI_EGRESS_LEDGER_REQUIRED': 'true',
    'PTC_MODE': 'replay',
    'JOB_TIMEOUT': '300000',
    'REDIS_PASSWORD': redis_password,
    'MINIO_ROOT_USER': 'codeapi',
    'MINIO_ROOT_PASSWORD': minio_password,
    'MINIO_ACCESS_KEY': 'codeapi',
    'MINIO_SECRET_KEY': minio_password,
    'MINIO_BUCKET': 'codeapi',
    'MINIO_ENDPOINT': 'minio',
    'MINIO_PORT': '9000',
    'MINIO_USE_SSL': 'false',
    'PYTHON_CONCURRENCY': '1',
    'OTHER_CONCURRENCY': '1',
}
set_values(master_path, master_updates)
master = parse(read(master_path))

# Fail if upstream helper did not produce the auth/signing material we require.
required = [
    'CODEAPI_AUTH_PROVIDER', 'CODEAPI_JWT_ISSUER', 'CODEAPI_JWT_AUDIENCE',
    'CODEAPI_JWT_ALLOWED_ALGS', 'CODEAPI_JWT_JWKS_JSON',
    'CODEAPI_JWT_SINGLE_TENANT_ID', 'CODEAPI_EXECUTION_MANIFEST_PRIVATE_KEY',
]
missing = [key for key in required if not master.get(key, '').strip()]
if missing:
    raise SystemExit('Missing upstream Code API auth material: ' + ', '.join(missing))

def write_env(name, keys, extras=None):
    values = {key: master[key] for key in keys if key in master and master[key] != ''}
    if extras:
        values.update(extras)
    target = data_dir / name
    target.write_text(''.join(f'{key}={value}\n' for key, value in values.items()), encoding='utf-8')
    os.chmod(target, 0o600)

common_control = [
    'LOCAL_MODE', 'CODEAPI_HARDENED_SANDBOX_MODE', 'CODEAPI_SANDBOX_BACKEND',
    'CODEAPI_EXECUTION_PROFILE', 'CODEAPI_RUNTIME_SESSION_MODE',
    'CODEAPI_BRIDGE_TOKEN', 'CODEAPI_BRIDGE_AUTH_MODE',
    'CODEAPI_BRIDGE_DYNAMIC_WORKERS', 'CODEAPI_BRIDGE_WORKER_ID',
    'CODEAPI_INTERNAL_SERVICE_TOKEN', 'PTC_MODE', 'JOB_TIMEOUT', 'REDIS_PASSWORD',
]
write_env('api.env', common_control + [
    'CODEAPI_AUTH_PROVIDER', 'CODEAPI_ALLOW_AUTH_PROVIDER_NONE',
    'CODEAPI_JWT_ISSUER', 'CODEAPI_JWT_AUDIENCE', 'CODEAPI_JWT_ALLOWED_ALGS',
    'CODEAPI_JWT_CLOCK_SKEW_SECONDS', 'CODEAPI_JWT_MAX_TTL_SECONDS',
    'CODEAPI_JWT_KEY_CACHE_TTL_SECONDS', 'CODEAPI_JWT_JWKS_JSON',
    'CODEAPI_JWT_SINGLE_TENANT_ID',
])
write_env('worker.env', common_control + [
    'CODEAPI_JWT_SINGLE_TENANT_ID', 'CODEAPI_EXECUTION_MANIFEST_PRIVATE_KEY',
    'PYTHON_CONCURRENCY', 'OTHER_CONCURRENCY',
])
write_env('egress.env', [
    'CODEAPI_HARDENED_SANDBOX_MODE', 'CODEAPI_EGRESS_GRANT_SECRET',
    'CODEAPI_EGRESS_LEDGER_REQUIRED', 'CODEAPI_INTERNAL_SERVICE_TOKEN', 'REDIS_PASSWORD',
])
write_env('tools.env', ['CODEAPI_INTERNAL_SERVICE_TOKEN', 'REDIS_PASSWORD'])
write_env('files.env', [
    'CODEAPI_INTERNAL_SERVICE_TOKEN', 'REDIS_PASSWORD', 'MINIO_BUCKET',
    'MINIO_ENDPOINT', 'MINIO_PORT', 'MINIO_USE_SSL', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY',
])
write_env('redis.env', ['REDIS_PASSWORD'])
write_env('minio.env', ['MINIO_ROOT_USER', 'MINIO_ROOT_PASSWORD'])

# Keep stateless code deliberately unusable. Production agents are explicitly
# bound to the attached stateful environment instead.
set_values(librechat_path, {
    'CODE_INTERPRETER_ENABLED': 'true',
    'LIBRECHAT_CODE_BASEURL': 'http://127.0.0.1:9',
    'LIBRECHAT_CODE_BASEURL_STATEFUL': 'http://librechat-codeapi:3112/v1',
})
PY

chmod 0600 "$LIBRECHAT_ENV" "$DATA_DIR"/*.env

# Verify only state, never values.
grep -q '^CODEAPI_AUTH_PROVIDER=librechat-jwt$' "$LIBRECHAT_ENV"
grep -q '^CODEAPI_JWT_PRIVATE_JWK_JSON=.' "$LIBRECHAT_ENV"
grep -q '^LIBRECHAT_CODE_BASEURL_STATEFUL=http://librechat-codeapi:3112/v1$' "$LIBRECHAT_ENV"
grep -q '^CODEAPI_SANDBOX_BACKEND=remote-bridge$' "$MASTER_ENV"
grep -q '^CODEAPI_EXECUTION_PROFILE=stateful$' "$MASTER_ENV"
grep -q '^CODEAPI_BRIDGE_WORKER_ID=justin-wsl$' "$MASTER_ENV"
grep -q '^CODEAPI_EGRESS_GRANT_SECRET=.' "$DATA_DIR/egress.env"
if grep -q '^CODEAPI_EGRESS_GRANT_SECRET=' "$DATA_DIR/api.env" "$DATA_DIR/worker.env"; then
  echo "ERROR: egress grant secret leaked into API/worker env" >&2
  exit 1
fi
if grep -q '^CODEAPI_EXECUTION_MANIFEST_PRIVATE_KEY=' "$DATA_DIR/api.env"; then
  echo "ERROR: execution-manifest private key leaked into API env" >&2
  exit 1
fi

log "Building/starting self-hosted Code Interpreter remote-bridge control plane"
sh "$MANAGER" reconcile

# LibreChat must be recreated after the signer/stateful base URL were added.
log "Recreating LibreChat API with remote Code Interpreter configuration"
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
log "Remote Code Interpreter control plane is ready"
printf '%s\n' "CODE_INTERPRETER_CONTROL_PLANE=READY"
printf '%s\n' "REMOTE_WORKER_ID=$WORKER_ID"
printf '%s\n' "Worker endpoint is NAS loopback 127.0.0.1:3112; use an SSH tunnel from WSL2"
printf '%s\n' "Private LibreChat env backup: $LIBRECHAT_BACKUP"
