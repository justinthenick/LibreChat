#!/bin/sh
# Regression test for the steady-state telemetry publication gate.
set -eu
SCRIPT="${1:-deploy/synology/autodeploy.sh}"
sh -n "$SCRIPT"
LINE=$(grep -F 'if telemetry_configured && { [ ! -f "$TELEMETRY_MARKER" ]' "$SCRIPT")
[ -n "$LINE" ] || { echo "telemetry gate missing" >&2; exit 1; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
TELEMETRY_MARKER="$TMP/last-publish"
REMOTE_SHA=test-sha
CALLS="$TMP/calls"
telemetry_configured() { return 0; }
publish_telemetry() { printf '%s %s %s\n' "$1" "$2" "$3" >> "$CALLS"; }
# Evaluate only the extracted condition, not the deployment script.
check() {
  : > "$CALLS"
  eval "$LINE"
  wc -l < "$CALLS" | tr -d ' '
}
[ "$(check)" = 1 ] || { echo "missing marker should publish" >&2; exit 1; }
touch "$TELEMETRY_MARKER"
[ "$(check)" = 0 ] || { echo "new marker should not publish" >&2; exit 1; }
python3 - "$TELEMETRY_MARKER" <<'PY'
import os, sys, time
stamp = time.time() - 65 * 60
os.utime(sys.argv[1], (stamp, stamp))
PY
[ "$(check)" = 1 ] || { echo "old marker should publish" >&2; exit 1; }
echo "steady-state telemetry gate PASS"
