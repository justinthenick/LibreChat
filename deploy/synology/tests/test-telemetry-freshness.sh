#!/bin/sh
# Regression test for the production steady-state telemetry publication gate.
set -eu
SCRIPT="${1:-deploy/synology/autodeploy.sh}"
GATE="${2:-deploy/synology/telemetry-freshness.py}"
sh -n "$SCRIPT"
python3 -m py_compile "$GATE"
grep -Fq 'if telemetry_configured && python3 "$DEPLOY_DIR/telemetry-freshness.py" "$TELEMETRY_MARKER"; then' "$SCRIPT" || { echo "production telemetry gate missing" >&2; exit 1; }
grep -Fq 'publish_telemetry check steady_state_periodic "$REMOTE_SHA"' "$SCRIPT" || { echo "routine telemetry branch missing" >&2; exit 1; }
grep -Fq 'publish_telemetry check steady_state "$REMOTE_SHA"' "$SCRIPT" || { echo "recovery telemetry branch missing" >&2; exit 1; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
MARKER="$TMP/last-publish"
should_publish() { python3 "$GATE" "$MARKER" || { echo "expected telemetry publication" >&2; exit 1; }; }
should_skip() { if python3 "$GATE" "$MARKER"; then echo "expected telemetry throttle" >&2; exit 1; fi; }
set_age() {
  python3 - "$MARKER" "$1" <<'PY'
import os, sys, time
stamp = time.time() - int(sys.argv[2])
os.utime(sys.argv[1], (stamp, stamp))
PY
}
should_publish  # Missing marker
printf 'prior-success\n' > "$MARKER"
should_skip     # Just published
set_age 3500
should_skip     # Less than one hour old
set_age 3700
should_publish  # More than one hour old
set_age -1000
should_publish  # Corrupt future marker cannot indefinitely suppress reports
printf 'malformed marker content\n' > "$MARKER"
set_age 3700
should_publish  # Marker content is not parsed; actual mtime is authoritative
printf 'steady-state telemetry gate PASS\n'
