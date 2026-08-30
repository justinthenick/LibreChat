#!/bin/sh
set -eu

REPO_DIR="/volume1/docker/librechat"
DEPLOY_DIR="$REPO_DIR/deploy/synology"
WORKSPACE_DIR="$REPO_DIR/workspace"
REMOTE_URL="https://github.com/justinthenick/LibreChat.git"
BRANCH="server/synology"
LOG_FILE="/volume1/docker/librechat-deploy.log"
GIT_IMAGE="alpine/git:latest"
GIT_UID_GID="1026:100"
STATUS_IMAGE="curlimages/curl:8.10.1"
STATUS_REPO="justinthenick/LibreChat"
STATUS_CONTEXT="nas/librechat"
FORCE_DEPLOY="${FORCE_DEPLOY:-0}"
STATUS_TARGET_SHA=""

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

env_value() {
  sed -n "s/^$1=//p" "$DEPLOY_DIR/.env" | head -n 1
}

post_status() {
  STATE="$1"
  SHA="$2"
  DESCRIPTION="$3"
  TOKEN="$(env_value GITHUB_DEPLOY_STATUS_TOKEN)"

  if [ -z "$TOKEN" ]; then
    log "WARN: GitHub deployment status token is not configured; status not reported"
    return 0
  fi

  if ! docker run --rm \
    -e GH_TOKEN="$TOKEN" \
    -e GH_STATE="$STATE" \
    -e GH_SHA="$SHA" \
    -e GH_DESCRIPTION="$DESCRIPTION" \
    -e GH_REPO="$STATUS_REPO" \
    -e GH_CONTEXT="$STATUS_CONTEXT" \
    --entrypoint sh "$STATUS_IMAGE" -c '
      payload=$(printf "{\"state\":\"%s\",\"description\":\"%s\",\"context\":\"%s\"}" "$GH_STATE" "$GH_DESCRIPTION" "$GH_CONTEXT")
      curl -fsS -X POST \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer $GH_TOKEN" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "https://api.github.com/repos/$GH_REPO/statuses/$GH_SHA" \
        -d "$payload" >/dev/null
    '; then
    log "WARN: could not report GitHub commit status for $(short_sha "$SHA")"
  fi

  return 0
}

on_exit() {
  RC=$?
  trap - 0
  if [ "$RC" -ne 0 ] && [ -n "$STATUS_TARGET_SHA" ]; then
    post_status failure "$STATUS_TARGET_SHA" "Synology deployment failed; check NAS deploy log"
  fi
  exit "$RC"
}

trap on_exit 0

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

if [ "$LOCAL_SHA" = "$REMOTE_SHA" ] && [ "$FORCE_DEPLOY" != "1" ]; then
  log "No deployment change; already at $(short_sha "$LOCAL_SHA")"
  exit 0
fi

STATUS_TARGET_SHA="$REMOTE_SHA"

if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
  log "Forced deployment requested at $(short_sha "$LOCAL_SHA")"
else
  log "Change detected: $(short_sha "$LOCAL_SHA") -> $(short_sha "$REMOTE_SHA")"
fi

post_status pending "$REMOTE_SHA" "Synology deployment in progress"

# Only fast-forward updates are accepted. This preserves local private files and
# aborts rather than rewriting deployment history.
git_repo pull --ff-only origin "$BRANCH"

# Create a dedicated shared workspace. LibreChat keeps its normal unprivileged
# node user, gains only the Synology users group, and sees this directory at
# /workspace. No repository, Docker socket, or broader /volume1 path is exposed.
mkdir -p "$WORKSPACE_DIR"
chown 1026:100 "$WORKSPACE_DIR"
chmod 2770 "$WORKSPACE_DIR"
log "Workspace ready at $WORKSPACE_DIR"

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
post_status success "$DEPLOYED_SHA" "Synology deployment healthy"
STATUS_TARGET_SHA=""
log "Deployment healthy at $DEPLOYED_SHA"
