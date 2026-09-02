#!/bin/sh
# One-time installer for the constrained GitHub-triggered NAS diagnostic worker.
# Does not read or print .env values and does not run benchmark jobs.

set -eu

ROOT="/volume1/docker/librechat-ba-lab"
TOOLS="$ROOT/custom/ba-agent/tools"
BRANCH="feature/ba-agent-v0.1"
RAW_BASE="https://raw.githubusercontent.com/justinthenick/LibreChat/$BRANCH/custom/ba-agent/tools"
TMP="/tmp/librechat-ba-diagnostic-install.$$"
STAMP="$(date '+%Y%m%dT%H%M%S')"

mkdir -p "$TMP" "$TOOLS"
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

PYTHON_BIN="$(command -v python3 2>/dev/null || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "ERROR: python3 not found"
  exit 2
fi

fetch() {
  url="$1"
  out="$2"
  "$PYTHON_BIN" - "$url" "$out" <<'PY'
import sys
import urllib.request
url, out = sys.argv[1:]
req = urllib.request.Request(url, headers={"User-Agent": "librechat-ba-diagnostic-installer/1.0"})
with urllib.request.urlopen(req, timeout=60) as r:
    data = r.read()
open(out, "wb").write(data)
PY
}

fetch "$RAW_BASE/diagnostic_worker.py" "$TMP/diagnostic_worker.py"
fetch "$RAW_BASE/run_worker_once.sh" "$TMP/run_worker_once.sh"

"$PYTHON_BIN" -m py_compile "$TMP/diagnostic_worker.py"
sh -n "$TMP/run_worker_once.sh"

if [ -f "$TOOLS/run_worker_once.sh" ]; then
  cp "$TOOLS/run_worker_once.sh" "$TOOLS/run_worker_once.sh.bak.$STAMP"
fi
if [ -f "$TOOLS/diagnostic_worker.py" ]; then
  cp "$TOOLS/diagnostic_worker.py" "$TOOLS/diagnostic_worker.py.bak.$STAMP"
fi

cp "$TMP/diagnostic_worker.py" "$TOOLS/diagnostic_worker.py"
cp "$TMP/run_worker_once.sh" "$TOOLS/run_worker_once.sh"
chmod 755 "$TOOLS/diagnostic_worker.py" "$TOOLS/run_worker_once.sh"

echo "Installed constrained NAS diagnostic trigger support."
echo "Diagnostic worker: $TOOLS/diagnostic_worker.py"
echo "Worker wrapper:    $TOOLS/run_worker_once.sh"
echo "No diagnostic request was triggered by this installer."
