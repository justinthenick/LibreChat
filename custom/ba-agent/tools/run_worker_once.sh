#!/bin/sh
# Robust one-shot BA benchmark worker wrapper for Synology Task Scheduler.
# Runs at most one worker instance at a time and appends unbuffered output to scheduler.log.

set -u

ROOT="/volume1/docker/librechat-ba-lab"
ENV_FILE="/volume1/docker/librechat/deploy/synology/.env"
WORKER="$ROOT/custom/ba-agent/tools/benchmark_worker.py"
LOG_DIR="$ROOT/custom/ba-agent/automation"
LOG_FILE="$LOG_DIR/scheduler.log"
LOCK_DIR="/tmp/librechat-ba-benchmark-worker.lock"

# DSM scheduled tasks can have a smaller PATH than an interactive SSH shell.
PATH="/usr/local/bin:/usr/bin:/bin:/usr/syno/bin:/usr/syno/sbin:$PATH"
export PATH
export PYTHONUNBUFFERED=1

mkdir -p "$LOG_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  printf '%s worker already active; skipping\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
  exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT HUP INT TERM

PYTHON_BIN="$(command -v python3 2>/dev/null || true)"
if [ -z "$PYTHON_BIN" ]; then
  printf '%s ERROR python3 not found in PATH=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$PATH" >> "$LOG_FILE"
  exit 2
fi

printf '%s worker poll start using %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$PYTHON_BIN" >> "$LOG_FILE"
"$PYTHON_BIN" "$WORKER" \
  --once \
  --env-file "$ENV_FILE" \
  >> "$LOG_FILE" 2>&1
RC=$?
printf '%s worker poll end rc=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$RC" >> "$LOG_FILE"
exit "$RC"
