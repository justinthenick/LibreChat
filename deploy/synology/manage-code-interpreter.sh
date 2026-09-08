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
  if [ ! -c /dev/kvm ]; then
    log "ERROR: /dev/kvm is unavailable. Refusing weaker host-kernel NsJail fallback."
    return 1
  fi
  if [ ! -r /dev/kvm ] || [ ! -w /dev/kvm ]; then
    # The deployment runs as root on Synology, so this normally succeeds. Keep
    # the explicit check because a device can exist but still be unusable.
    log "ERROR: /dev/kvm exists but is not readable/writable by the deployment task"
    return 1
  fi
}

images_ready() {
  for SERVICE in codeapi worker egress tools sandbox files; do
    ID="$(code_compose images -q "$SERVICE" 2>/dev/null | head -n 1 || true)"
    [ -n "$ID" ] || return 1
  done
  [ -f "$BUILD_MARKER" ] && [ "$(sed -n '1p' "$BUILD_MARKER")" = "$SOURCE_SHA" ]
}

build_images() {
  log "Building pinned Code Interpreter images; the first KVM build can take a while"
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
    librechat-codeapi-sandbox \
    librechat-codeapi-files \
    librechat-codeapi-redis \
    librechat-codeapi-minio; do
    container_running "$C" || return 1
  done

  [ "$(docker inspect -f '{{.State.Health.Status}}' librechat-codeapi-sandbox 2>/dev/null || true)" = "healthy" ] || return 1

  # Validate the exact network path LibreChat will use. The health route does
  # not require a model-generated token; execution itself remains JWT gated.
  docker exec librechat node -e '
    const http=require("http");
    const r=http.get("http://librechat-codeapi:3112/v1/health",x=>process.exit(x.statusCode>=200&&x.statusCode<300?0:1));
    r.setTimeout(5000,()=>{r.destroy();process.exit(1)});
    r.on("error",()=>process.exit(1));
  ' >/dev/null 2>&1
}

wait_ready() {
  COUNT=0
  until check; do
    COUNT=$((COUNT+1))
    if [ "$COUNT" -ge 36 ]; then
      log "ERROR: Code Interpreter did not become healthy after 180 seconds"
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
  log "Reconciling Code Interpreter containers"
  code_compose up -d --remove-orphans
  wait_ready
  log "Code Interpreter healthy at source $SOURCE_SHA"
}

status() {
  printf 'source_pin=%s\n' "$SOURCE_SHA"
  if [ -d "$SOURCE_DIR/.git" ]; then
    printf 'source_checkout=%s\n' "$(git_source rev-parse HEAD 2>/dev/null || echo unknown)"
  else
    printf 'source_checkout=missing\n'
  fi
  if check; then printf 'runtime=healthy\n'; else printf 'runtime=not_ready\n'; fi
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
