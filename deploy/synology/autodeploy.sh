#!/bin/sh
set -eu

REPO_DIR="/volume1/docker/librechat"
DEPLOY_DIR="$REPO_DIR/deploy/synology"
REMOTE_URL="https://github.com/justinthenick/LibreChat.git"
BRANCH="server/synology"
LOG_FILE="/volume1/docker/librechat-deploy.log"
GIT_IMAGE="alpine/git:latest"
GIT_UID_GID="1026:100"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG_FILE"
}

git_repo() {
  docker run --rm --user "$GIT_UID_GID" -v "$REPO_DIR:/repo" "$GIT_IMAGE" -C /repo "$@"
}

remote_sha() {
  docker run --rm "$GIT_IMAGE" ls-remote "$REMOTE_URL" "refs/heads/$BRANCH" | awk '{print $1}'
}

short_sha() {
  printf '%s' "$1" | cut -c1-8
}

health_check() {
  docker exec librechat node -e '
    const http = require("http");
    const req = http.get("http://127.0.0.1:3080/api/config", (res) => {
      process.exit(res.statusCode >= 200 && res.statusCode < 500 ? 0 : 1);
    });
    req.setTimeout(5000, () => { req.destroy(); process.exit(1); });
    req.on("error", () => process.exit(1));
  ' >/dev/null 2>&1
}

log "LibreChat deployment check started"

if [ ! -d "$REPO_DIR/.git" ]; then
  log "ERROR: repository not found at $REPO_DIR"
  exit 1
fi

if [ ! -f "$DEPLOY_DIR/.env" ]; then
  log "ERROR: private .env missing at $DEPLOY_DIR/.env"
  exit 1
fi

CURRENT_BRANCH="$(git_repo rev-parse --abbrev-ref HEAD)"
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
  log "ERROR: repository is on $CURRENT_BRANCH, expected $BRANCH"
  exit 1
fi

LOCAL_SHA="$(git_repo rev-parse HEAD)"
REMOTE_SHA="$(remote_sha)"

if [ -z "$REMOTE_SHA" ]; then
  log "ERROR: could not resolve remote branch $BRANCH"
  exit 1
fi

if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
  log "No deployment change; already at $(short_sha "$LOCAL_SHA")"
  exit 0
fi

log "Change detected: $(short_sha "$LOCAL_SHA") -> $(short_sha "$REMOTE_SHA")"

# Only fast-forward updates are accepted. This preserves local private files and
# aborts rather than rewriting deployment history.
git_repo pull --ff-only origin "$BRANCH"

cd "$DEPLOY_DIR"

docker-compose config >/dev/null
log "Compose validation passed"

docker-compose pull
log "Image pull completed"

docker-compose up -d
log "Compose update completed"

COUNT=0
until health_check; do
  COUNT=$((COUNT + 1))
  if [ "$COUNT" -ge 12 ]; then
    log "ERROR: LibreChat health check failed after 60 seconds"
    docker-compose ps >> "$LOG_FILE" 2>&1 || true
    docker-compose logs --tail=80 api >> "$LOG_FILE" 2>&1 || true
    exit 1
  fi
  sleep 5
done

DEPLOYED_SHA="$(git_repo rev-parse HEAD)"
log "Deployment healthy at $DEPLOYED_SHA"
