#!/bin/sh
set -eu

SOURCE_REPO="https://github.com/LibreChat-AI/code-interpreter.git"
# No tagged release exists in the upstream repository yet. Pin the reviewed
# source commit exactly; change this only as a separately validated upgrade.
SOURCE_SHA="725f79900bf06298653668a029eefd69460d900e"
SOURCE_DIR="/volume1/docker/librechat-code-interpreter"
DATA_DIR="/volume1/docker/librechat-code-interpreter-data"
ENV_FILE="$DATA_DIR/codeapi.env"
DEPLOY_DIR="/volume1/docker/librechat/deploy/synology"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.code-interpreter.yml"
BUILD_MARKER="$DATA_DIR/built-source.sha"
PROJECT="librechat-codeapi"
SHARED_NETWORK="librechat_librechat"
GIT_IMAGE="alpine/git:latest"
COMPOSE_HTTP_TIMEOUT="${COMPOSE_HTTP_TIMEOUT:-300}"
export COMPOSE_HTTP_TIMEOUT

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

code_compose() {
  docker-compose -p "$PROJECT" -f "$COMPOSE_FILE" "$@"
}

git_source() {
  docker run --rm -v /volume1/docker:/host "$GIT_IMAGE" -C /host/librechat-code-interpreter "$@"
}

ensure_source() {
  mkdir -p "$DATA_DIR"
  chmod 0700 "$DATA_DIR" 2>/dev/null || true

  if [ ! -d "$SOURCE_DIR/.git" ]; then
    if [ -e "$SOURCE_DIR" ]; then
      log "ERROR: $SOURCE_DIR exists but is not the managed Code Interpreter git checkout"
      return 1
    fi
    log "Cloning LibreChat Code Interpreter source"
    docker run --rm -v /volume1/docker:/host "$GIT_IMAGE" clone --no-checkout "$SOURCE_REPO" /host/librechat-code-interpreter
  fi

  if ! git_source cat-file -e "$SOURCE_SHA^{commit}" >/dev/null 2>&1; then
    log "Fetching pinned Code Interpreter source $SOURCE_SHA"
    git_source fetch --depth 1 origin "$SOURCE_SHA"
  fi

  CURRENT="$(git_source rev-parse HEAD 2>/dev/null || true)"
  if [ "$CURRENT" != "$SOURCE_SHA" ]; then
    log "Checking out pinned Code Interpreter source $SOURCE_SHA"
    git_source checkout --detach "$SOURCE_SHA" >/dev/null
  fi

  CURRENT="$(git_source rev-parse HEAD)"
  if [ "$CURRENT" != "$SOURCE_SHA" ]; then
    log "ERROR: Code Interpreter checkout is $CURRENT, expected $SOURCE_SHA"
    return 1
  fi
  [ -f "$SOURCE_DIR/scripts/setup-local-auth-env.js" ] || {
    log "ERROR: pinned Code Interpreter auth bootstrap helper is missing"
    return 1
  }
}

preflight() {
  [ -f "$COMPOSE_FILE" ] || { log "ERROR: missing $COMPOSE_FILE"; return 1; }
  [ -f "$ENV_FILE" ] || { log "ERROR: Code Interpreter private env missing; run bootstrap-code-interpreter.sh"; return 1; }
  docker info >/dev/null 2>&1 || { log "ERROR: Docker daemon unavailable"; return 1; }
  docker network inspect "$SHARED_NETWORK" >/dev/null 2>&1 || {
    log "ERROR: LibreChat Docker network $SHARED_NETWORK does not exist"
    return 1
  }
  # The NAS deliberately has no local sandbox requirement. User-generated code
  # is executed only by the separately paired remote bridge worker.
  grep -q '^CODEAPI_SANDBOX_BACKEND=remote-bridge$' "$ENV_FILE" || {
    log "ERROR: Code Interpreter backend is not pinned to remote-bridge"
    return 1
  }
  grep -q '^CODEAPI_EXECUTION_PROFILE=stateful$' "$ENV_FILE" || {
    log "ERROR: Code Interpreter execution profile is not stateful"
    return 1
  }
  grep -q '^CODEAPI_BRIDGE_AUTH_MODE=paired$' "$ENV_FILE" || {
    log "ERROR: Code Interpreter bridge authentication is not paired"
    return 1
  }
}

images_ready() {
  for SERVICE in codeapi worker egress tools files; do
    ID="$(code_compose images -q "$SERVICE" 2>/dev/null | head -n 1 || true)"
    [ -n "$ID" ] || return 1
  done
  [ -f "$BUILD_MARKER" ] && [ "$(sed -n '1p' "$BUILD_MARKER")" = "$SOURCE_SHA" ]
}

build_images() {
  log "Building pinned Code Interpreter control-plane images"
  code_compose build
  printf '%s\n' "$SOURCE_SHA" > "$BUILD_MARKER.tmp"
  chmod 0600 "$BUILD_MARKER.tmp"
  mv -f "$BUILD_MARKER.tmp" "$BUILD_MARKER"
  log "Code Interpreter image build completed"
}

container_running() {
  [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null || true)" = "true" ]
}

check() {
  for C in \
    librechat-codeapi \
    librechat-codeapi-worker \
    librechat-codeapi-egress \
    librechat-codeapi-tools \
    librechat-codeapi-files \
    librechat-codeapi-redis \
    librechat-codeapi-minio; do
    container_running "$C" || return 1
  done

  # Validate the exact Docker-internal path LibreChat uses. Remote worker
  # readiness is checked separately because the worker may intentionally be off.
  docker exec librechat node -e '
    const http=require("http");
    const r=http.get("http://librechat-codeapi:3112/v1/health",x=>process.exit(x.statusCode>=200&&x.statusCode<300?0:1));
    r.setTimeout(5000,()=>{r.destroy();process.exit(1)});
    r.on("error",()=>process.exit(1));
  ' >/dev/null 2>&1
}

worker_ready() {
  # The fixed worker registration is intentionally checked through Code API,
  # not by reaching into Redis directly. A missing/offline worker is a safe
  # unavailable state, not a reason to weaken execution policy.
  TOKEN="$(sed -n 's/^CODEAPI_BRIDGE_TOKEN=//p' "$ENV_FILE" | head -n 1)"
  [ -n "$TOKEN" ] || return 1
  docker run --rm --network host \
    -e CODEAPI_BRIDGE_TOKEN="$TOKEN" \
    curlimages/curl:8.10.1 \
    -fsS -H "Authorization: Bearer $TOKEN" \
    http://127.0.0.1:3112/v1/bridge/workers >/dev/null 2>&1
}

wait_ready() {
  COUNT=0
  until check; do
    COUNT=$((COUNT+1))
    if [ "$COUNT" -ge 36 ]; then
      log "ERROR: Code Interpreter control plane did not become healthy after 180 seconds"
      return 1
    fi
    sleep 5
  done
}

reconcile() {
  ensure_source
  preflight
  if ! code_compose config >/dev/null; then
    log "ERROR: Code Interpreter Compose validation failed"
    return 1
  fi
  if ! images_ready; then
    build_images
  fi
  log "Reconciling Code Interpreter remote-bridge control plane"
  code_compose up -d --remove-orphans
  wait_ready
  log "Code Interpreter control plane healthy at source $SOURCE_SHA"
}

status() {
  printf 'source_pin=%s\n' "$SOURCE_SHA"
  if [ -d "$SOURCE_DIR/.git" ]; then
    printf 'source_checkout=%s\n' "$(git_source rev-parse HEAD 2>/dev/null || echo unknown)"
  else
    printf 'source_checkout=missing\n'
  fi
  if check; then printf 'control_plane=healthy\n'; else printf 'control_plane=not_ready\n'; fi
  if worker_ready; then printf 'remote_worker_endpoint=reachable\n'; else printf 'remote_worker_endpoint=not_verified\n'; fi
}

down() {
  if [ -f "$COMPOSE_FILE" ] && [ -f "$ENV_FILE" ]; then
    code_compose down
  fi
}

case "${1:-}" in
  source) ensure_source ;;
  preflight) ensure_source; preflight ;;
  reconcile) reconcile ;;
  check) check ;;
  status) status ;;
  down) down ;;
  *)
    echo "Usage: $0 {source|preflight|reconcile|check|status|down}" >&2
    exit 2
    ;;
esac
