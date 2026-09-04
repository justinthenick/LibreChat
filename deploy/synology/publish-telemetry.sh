#!/bin/sh
set -eu

DEPLOY_DIR="/volume1/docker/librechat/deploy/synology"
EVENT_LOG_FILE="/volume1/docker/librechat-deploy-events.log"
LAST_FAILURE_FILE="/volume1/docker/librechat-deploy.last-failure"
TELEMETRY_MARKER="/volume1/docker/librechat-telemetry.last-publish"
STATUS_IMAGE="curlimages/curl:8.10.1"
STATUS_REPO="justinthenick/LibreChat"
STATUS_CONTEXT="nas/librechat"
TELEMETRY_BRANCH="nas-status"
TMP_DIR="/tmp/librechat-telemetry.$$"

RESULT="${1:-check}"
STAGE="${2:-unknown}"
SHA="${3:-unknown}"

# A healthy steady-state poll after a failed reconciliation is a real recovery.
# Publish it as success so telemetry and the commit status do not remain stale
# red after the runtime has healed. Failure deliberately clears the marker so
# the next healthy poll runs this recovery path exactly once.
PUBLIC_RESULT="$RESULT"
PUBLIC_STAGE="$STAGE"
if [ "$RESULT" = "check" ] && [ "$STAGE" = "steady_state" ]; then
  PUBLIC_RESULT="success"
  PUBLIC_STAGE="steady_state_recovered"
fi
if [ "$RESULT" = "failure" ]; then
  rm -f "$TELEMETRY_MARKER" 2>/dev/null || true
fi

env_value() {
  sed -n "s/^$1=//p" "$DEPLOY_DIR/.env" | head -n 1
}

TOKEN="$(env_value GITHUB_TELEMETRY_TOKEN)"
if [ -z "$TOKEN" ]; then
  exit 2
fi

cleanup() {
  rm -rf "$TMP_DIR" 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM
mkdir -p "$TMP_DIR"

timestamp() {
  date '+%Y-%m-%dT%H:%M:%S%z'
}

container_field() {
  NAME="$1"
  TEMPLATE="$2"
  docker inspect -f "$TEMPLATE" "$NAME" 2>/dev/null || printf '%s' "absent"
}

api_health() {
  if docker exec librechat node -e '
    const http = require("http");
    const req = http.get("http://127.0.0.1:3080/api/config", (res) => {
      process.exit(res.statusCode >= 200 && res.statusCode < 500 ? 0 : 1);
    });
    req.setTimeout(5000, () => { req.destroy(); process.exit(1); });
    req.on("error", () => process.exit(1));
  ' >/dev/null 2>&1; then
    printf '%s' "pass"
  else
    printf '%s' "fail"
  fi
}

workspace_health() {
  if docker exec librechat sh -lc 'test -d /workspace && test -w /workspace' >/dev/null 2>&1; then
    printf '%s' "pass"
  else
    printf '%s' "fail"
  fi
}

cloudflare_health() {
  if ! docker inspect librechat-cloudflared >/dev/null 2>&1; then
    printf '%s' "disabled"
    return
  fi

  RUNNING="$(docker inspect -f '{{.State.Running}}' librechat-cloudflared 2>/dev/null || true)"
  if [ "$RUNNING" != "true" ]; then
    printf '%s' "fail"
    return
  fi

  if docker logs --tail=200 librechat-cloudflared 2>&1 | grep -q "Registered tunnel connection"; then
    printf '%s' "connected"
  else
    printf '%s' "running_unregistered"
  fi
}

encode_base64() {
  if command -v base64 >/dev/null 2>&1; then
    base64 | tr -d '\r\n'
  elif command -v openssl >/dev/null 2>&1; then
    openssl base64 -A
  else
    return 1
  fi
}

github_api() {
  METHOD="$1"
  URL="$2"
  PAYLOAD="${3:-}"

  if [ -n "$PAYLOAD" ]; then
    docker run --rm \
      -e GH_TOKEN="$TOKEN" \
      -e GH_URL="$URL" \
      -e GH_METHOD="$METHOD" \
      -e GH_PAYLOAD="$PAYLOAD" \
      -v "$TMP_DIR:/work:ro" \
      --entrypoint sh "$STATUS_IMAGE" -c '
        curl -fsS -X "$GH_METHOD" \
          -H "Accept: application/vnd.github+json" \
          -H "Authorization: Bearer $GH_TOKEN" \
          -H "X-GitHub-Api-Version: 2022-11-28" \
          --data-binary "@/work/$GH_PAYLOAD" \
          "$GH_URL"
      '
  else
    docker run --rm \
      -e GH_TOKEN="$TOKEN" \
      -e GH_URL="$URL" \
      -e GH_METHOD="$METHOD" \
      --entrypoint sh "$STATUS_IMAGE" -c '
        curl -fsS -X "$GH_METHOD" \
          -H "Accept: application/vnd.github+json" \
          -H "Authorization: Bearer $GH_TOKEN" \
          -H "X-GitHub-Api-Version: 2022-11-28" \
          "$GH_URL"
      '
  fi
}

put_file() {
  PATH_NAME="$1"
  SOURCE_FILE="$2"
  MESSAGE="$3"
  API_URL="https://api.github.com/repos/$STATUS_REPO/contents/$PATH_NAME"

  META="$(github_api GET "$API_URL?ref=$TELEMETRY_BRANCH" 2>/dev/null || true)"
  EXISTING_SHA="$(printf '%s' "$META" | sed -n 's/.*"sha":[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"
  CONTENT_B64="$(encode_base64 < "$SOURCE_FILE")"

  if [ -n "$EXISTING_SHA" ]; then
    printf '{"message":"%s","content":"%s","branch":"%s","sha":"%s"}' \
      "$MESSAGE" "$CONTENT_B64" "$TELEMETRY_BRANCH" "$EXISTING_SHA" > "$TMP_DIR/payload.json"
  else
    printf '{"message":"%s","content":"%s","branch":"%s"}' \
      "$MESSAGE" "$CONTENT_B64" "$TELEMETRY_BRANCH" > "$TMP_DIR/payload.json"
  fi

  github_api PUT "$API_URL" payload.json >/dev/null
}

post_recovery_status() {
  STATUS_TOKEN="$(env_value GITHUB_DEPLOY_STATUS_TOKEN)"
  if [ -z "$STATUS_TOKEN" ]; then
    return 0
  fi
  docker run --rm \
    -e GH_TOKEN="$STATUS_TOKEN" \
    -e GH_SHA="$SHA" \
    -e GH_REPO="$STATUS_REPO" \
    -e GH_CONTEXT="$STATUS_CONTEXT" \
    --entrypoint sh "$STATUS_IMAGE" -c '
      payload=$(printf "{\"state\":\"success\",\"description\":\"Synology deployment healthy after recovery\",\"context\":\"%s\"}" "$GH_CONTEXT")
      curl -fsS -X POST \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer $GH_TOKEN" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "https://api.github.com/repos/$GH_REPO/statuses/$GH_SHA" \
        -d "$payload" >/dev/null
    '
}

NOW="$(timestamp)"
API_STATUS="$(container_field librechat '{{.State.Status}}')"
API_EXIT="$(container_field librechat '{{.State.ExitCode}}')"
API_RESTARTS="$(container_field librechat '{{.RestartCount}}')"
MONGO_STATUS="$(container_field librechat-mongodb '{{.State.Status}}')"
CF_STATUS="$(cloudflare_health)"
HTTP_STATUS="$(api_health)"
WORKSPACE_STATUS="$(workspace_health)"
DISK_USED="$(df -P /volume1 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}' | head -n 1)"
[ -n "$DISK_USED" ] || DISK_USED="unknown"

if [ "$RESULT" = "failure" ]; then
  printf '%s|%s|%s|%s|%s|%s|%s\n' \
    "$NOW" "$SHA" "$STAGE" "$API_STATUS" "$API_EXIT" "$CF_STATUS" "$DISK_USED" \
    > "$LAST_FAILURE_FILE"
  chmod 600 "$LAST_FAILURE_FILE" 2>/dev/null || true
fi

LF_TIMESTAMP=""
LF_SHA=""
LF_STAGE=""
LF_API_STATUS=""
LF_API_EXIT=""
LF_CF_STATUS=""
LF_DISK_USED=""
if [ -f "$LAST_FAILURE_FILE" ]; then
  IFS='|' read -r LF_TIMESTAMP LF_SHA LF_STAGE LF_API_STATUS LF_API_EXIT LF_CF_STATUS LF_DISK_USED < "$LAST_FAILURE_FILE" || true
fi

cat > "$TMP_DIR/latest.json" <<EOF
{
  "schema": 1,
  "timestamp": "$NOW",
  "result": "$PUBLIC_RESULT",
  "stage": "$PUBLIC_STAGE",
  "commit": "$SHA",
  "runtime": {
    "librechat_container": "$API_STATUS",
    "librechat_exit_code": "$API_EXIT",
    "librechat_restart_count": "$API_RESTARTS",
    "mongodb_container": "$MONGO_STATUS",
    "http_health": "$HTTP_STATUS",
    "workspace": "$WORKSPACE_STATUS",
    "cloudflare_tunnel": "$CF_STATUS",
    "volume1_used_percent": "$DISK_USED"
  },
  "last_failure": {
    "timestamp": "$LF_TIMESTAMP",
    "commit": "$LF_SHA",
    "stage": "$LF_STAGE",
    "librechat_container": "$LF_API_STATUS",
    "librechat_exit_code": "$LF_API_EXIT",
    "cloudflare_tunnel": "$LF_CF_STATUS",
    "volume1_used_percent": "$LF_DISK_USED"
  }
}
EOF

if [ -f "$EVENT_LOG_FILE" ]; then
  tail -40 "$EVENT_LOG_FILE" > "$TMP_DIR/latest.log"
else
  printf '%s\n' "No sanitised deployment events have been recorded yet." > "$TMP_DIR/latest.log"
fi

put_file "telemetry/latest.json" "$TMP_DIR/latest.json" "Update NAS telemetry snapshot"
put_file "telemetry/latest.log" "$TMP_DIR/latest.log" "Update NAS telemetry event log"

if [ "$PUBLIC_RESULT" = "failure" ] || [ "$PUBLIC_RESULT" = "success" ]; then
  SAFE_TIME="$(date -u '+%Y%m%dT%H%M%SZ')"
  SAFE_SHA="$(printf '%s' "$SHA" | cut -c1-12)"
  HISTORY_PATH="telemetry/history/${SAFE_TIME}-${SAFE_SHA}-${PUBLIC_RESULT}.json"
  put_file "$HISTORY_PATH" "$TMP_DIR/latest.json" "Record NAS telemetry $PUBLIC_RESULT"
fi

if [ "$RESULT" = "check" ] && [ "$STAGE" = "steady_state" ]; then
  post_recovery_status || true
fi

if [ "$RESULT" != "failure" ]; then
  printf '%s\n' "$NOW" > "$TELEMETRY_MARKER"
  chmod 600 "$TELEMETRY_MARKER" 2>/dev/null || true
fi
