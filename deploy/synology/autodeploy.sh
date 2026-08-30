#!/bin/sh
set -eu

REPO_DIR="/volume1/docker/librechat"
DEPLOY_DIR="$REPO_DIR/deploy/synology"
WORKSPACE_DIR="$REPO_DIR/workspace"
REMOTE_URL="https://github.com/justinthenick/LibreChat.git"
BRANCH="server/synology"
LOG_FILE="/volume1/docker/librechat-deploy.log"
STATE_FILE="/volume1/docker/librechat-deploy.last-success"
LOCK_DIR="/tmp/librechat-autodeploy.lock"
GIT_IMAGE="alpine/git:latest"
GIT_UID_GID="1026:100"
STATUS_IMAGE="curlimages/curl:8.10.1"
STATUS_REPO="justinthenick/LibreChat"
STATUS_CONTEXT="nas/librechat"
FORCE_DEPLOY="${FORCE_DEPLOY:-0}"
STATUS_TARGET_SHA=""
FAILED_STAGE="startup"
LOCK_HELD=0

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

read_last_success() {
  if [ -f "$STATE_FILE" ]; then
    sed -n '1p' "$STATE_FILE"
  fi
}

write_last_success() {
  TMP_STATE="${STATE_FILE}.$$"
  printf '%s\n' "$1" > "$TMP_STATE"
  chmod 644 "$TMP_STATE"
  mv -f "$TMP_STATE" "$STATE_FILE"
}

acquire_lock() {
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    printf '%s\n' "$$" > "$LOCK_DIR/pid"
    LOCK_HELD=1
    return 0
  fi

  LOCK_PID=""
  if [ -f "$LOCK_DIR/pid" ]; then
    LOCK_PID="$(sed -n '1p' "$LOCK_DIR/pid" 2>/dev/null || true)"
  fi

  if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
    log "Another LibreChat deployment check is already running as PID $LOCK_PID; skipping"
    return 1
  fi

  log "WARN: removing stale deployment lock"
  rm -rf "$LOCK_DIR"
  mkdir "$LOCK_DIR"
  printf '%s\n' "$$" > "$LOCK_DIR/pid"
  LOCK_HELD=1
  return 0
}

release_lock() {
  if [ "$LOCK_HELD" = "1" ]; then
    rm -rf "$LOCK_DIR" 2>/dev/null || true
    LOCK_HELD=0
  fi
}

prepare_workspace() {
  # Shared only with the Synology users group. The LibreChat container keeps its
  # normal unprivileged node user and receives GID 100 as a supplemental group.
  mkdir -p "$WORKSPACE_DIR"
  chown 1026:100 "$WORKSPACE_DIR"
  chmod 2770 "$WORKSPACE_DIR"
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

collect_diagnostics() {
  log "Collecting deployment diagnostics for stage $FAILED_STAGE"
  {
    printf '%s\n' "--- docker-compose ps ---"
    docker-compose ps || true
    printf '%s\n' "--- librechat containers ---"
    docker ps -a --filter name=librechat || true
    printf '%s\n' "--- volume usage ---"
    df -h /volume1 || true
    printf '%s\n' "--- api logs (last 80 lines) ---"
    docker-compose logs --tail=80 api || true
    printf '%s\n' "--- end diagnostics ---"
  } >> "$LOG_FILE" 2>&1
}

on_exit() {
  RC=$?
  trap - 0
  release_lock
  if [ "$RC" -ne 0 ] && [ -n "$STATUS_TARGET_SHA" ]; then
    post_status failure "$STATUS_TARGET_SHA" "Synology deployment failed at $FAILED_STAGE"
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

workspace_check() {
  docker exec librechat sh -lc '
    test -d /workspace || exit 1
    probe="/workspace/.librechat-deploy-write-test.$$"
    trap "rm -f \"$probe\"" EXIT HUP INT TERM
    printf "%s" "LibreChat workspace write test" > "$probe" || exit 1
    test "$(cat "$probe")" = "LibreChat workspace write test" || exit 1
    rm -f "$probe"
    trap - EXIT HUP INT TERM
  ' >/dev/null 2>&1
}

log "LibreChat deployment check started"

if ! acquire_lock; then
  exit 0
fi

FAILED_STAGE="docker_preflight"
if ! docker info >/dev/null 2>&1; then
  log "ERROR: Docker daemon is not accessible to the deployment task"
  exit 1
fi

FAILED_STAGE="preflight"
if [ ! -d "$REPO_DIR/.git" ]; then
  log "ERROR: repository not found at $REPO_DIR"
  exit 1
fi

if [ ! -f "$DEPLOY_DIR/.env" ]; then
  log "ERROR: private .env missing at $DEPLOY_DIR/.env"
  exit 1
fi

# Run on every scheduler pass so the workspace is repaired even if a previous
# Compose run created the bind-mount directory as root before this script landed.
prepare_workspace

CURRENT_BRANCH="$(git_repo rev-parse --abbrev-ref HEAD)"
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
  log "ERROR: repository is on $CURRENT_BRANCH, expected $BRANCH"
  exit 1
fi

LOCAL_SHA="$(git_repo rev-parse HEAD)"
REMOTE_SHA="$(remote_sha)"
LAST_SUCCESS_SHA="$(read_last_success)"

if [ -z "$REMOTE_SHA" ]; then
  log "ERROR: could not resolve remote branch $BRANCH"
  exit 1
fi

# A Git checkout is not proof of deployment. Only the separately persisted
# last-successful SHA suppresses a deployment. This ensures failed SHAs retry.
if [ "$LAST_SUCCESS_SHA" = "$REMOTE_SHA" ] && [ "$LOCAL_SHA" = "$REMOTE_SHA" ] && [ "$FORCE_DEPLOY" != "1" ]; then
  log "No deployment change; healthy deployment already recorded at $(short_sha "$REMOTE_SHA")"
  exit 0
fi

STATUS_TARGET_SHA="$REMOTE_SHA"

if [ "$FORCE_DEPLOY" = "1" ]; then
  log "Forced deployment requested at $(short_sha "$REMOTE_SHA")"
elif [ "$LAST_SUCCESS_SHA" = "$REMOTE_SHA" ]; then
  log "Repository checkout differs from recorded deployment; reconciling to $(short_sha "$REMOTE_SHA")"
elif [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
  if [ -n "$LAST_SUCCESS_SHA" ]; then
    log "Retrying deployment at $(short_sha "$REMOTE_SHA"); last successful deployment was $(short_sha "$LAST_SUCCESS_SHA")"
  else
    log "Deploying $(short_sha "$REMOTE_SHA"); no successful deployment state has been recorded yet"
  fi
else
  log "Change detected: $(short_sha "$LOCAL_SHA") -> $(short_sha "$REMOTE_SHA")"
fi

post_status pending "$REMOTE_SHA" "Synology deployment in progress"

FAILED_STAGE="git_update"
if [ "$LOCAL_SHA" != "$REMOTE_SHA" ]; then
  # Only fast-forward updates are accepted. This preserves local private files and
  # aborts rather than rewriting deployment history.
  if ! git_repo pull --ff-only origin "$BRANCH" >> "$LOG_FILE" 2>&1; then
    log "ERROR: Git fast-forward update failed"
    exit 1
  fi
fi

CHECKED_OUT_SHA="$(git_repo rev-parse HEAD)"
if [ "$CHECKED_OUT_SHA" != "$REMOTE_SHA" ]; then
  log "ERROR: checkout is at $(short_sha "$CHECKED_OUT_SHA"), expected $(short_sha "$REMOTE_SHA")"
  exit 1
fi

prepare_workspace
cd "$DEPLOY_DIR"

FAILED_STAGE="compose_validation"
if ! docker-compose config >/dev/null 2>> "$LOG_FILE"; then
  log "ERROR: Compose validation failed"
  exit 1
fi
log "Compose validation passed"

FAILED_STAGE="image_pull"
if ! docker-compose pull >> "$LOG_FILE" 2>&1; then
  log "ERROR: image pull failed"
  collect_diagnostics
  exit 1
fi
log "Image pull completed"

FAILED_STAGE="compose_up"
if ! docker-compose up -d >> "$LOG_FILE" 2>&1; then
  log "ERROR: Compose update failed"
  collect_diagnostics
  exit 1
fi
log "Compose update completed"

FAILED_STAGE="health_check"
COUNT=0
until health_check; do
  COUNT=$((COUNT + 1))
  if [ "$COUNT" -ge 12 ]; then
    log "ERROR: LibreChat health check failed after 60 seconds"
    collect_diagnostics
    exit 1
  fi
  sleep 5
done
log "LibreChat health check passed"

FAILED_STAGE="workspace_check"
if ! workspace_check; then
  log "ERROR: LibreChat cannot complete a write/read/delete test in /workspace"
  collect_diagnostics
  exit 1
fi
log "MCP workspace mount passed write/read/delete check"

FAILED_STAGE="state_record"
DEPLOYED_SHA="$(git_repo rev-parse HEAD)"
if [ "$DEPLOYED_SHA" != "$REMOTE_SHA" ]; then
  log "ERROR: deployed checkout changed unexpectedly to $(short_sha "$DEPLOYED_SHA")"
  exit 1
fi
write_last_success "$DEPLOYED_SHA"

FAILED_STAGE="status_report"
post_status success "$DEPLOYED_SHA" "Synology deployment healthy"
STATUS_TARGET_SHA=""
FAILED_STAGE="complete"
log "Deployment healthy at $DEPLOYED_SHA"
