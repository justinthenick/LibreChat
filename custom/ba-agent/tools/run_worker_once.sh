#!/bin/sh
# One-shot BA lab wrapper for Synology Task Scheduler.
# Self-refreshes authenticated lab tools, executes new jobs, advances safe
# deterministic fallback transitions, then runs diagnostics.

set -u

ROOT="/volume1/docker/librechat-ba-lab"
ENV_FILE="/volume1/docker/librechat/deploy/synology/.env"
BOOTSTRAP="$ROOT/custom/ba-agent/tools/bootstrap_nas.py"
WORKER="$ROOT/custom/ba-agent/tools/benchmark_worker.py"
CONTROLLER="$ROOT/custom/ba-agent/tools/autonomy_controller.py"
DIAG_WORKER="$ROOT/custom/ba-agent/tools/diagnostic_worker.py"
LOG_DIR="$ROOT/custom/ba-agent/automation"
LOG_FILE="$LOG_DIR/scheduler.log"
LOCK_DIR="/tmp/librechat-ba-benchmark-worker.lock"

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

printf '%s autonomy poll start using %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$PYTHON_BIN" >> "$LOG_FILE"

SYNC_RC=0
if [ -f "$BOOTSTRAP" ]; then
  "$PYTHON_BIN" "$BOOTSTRAP" --tools-only --env-file "$ENV_FILE" >> "$LOG_FILE" 2>&1
  SYNC_RC=$?
  if [ "$SYNC_RC" -ne 0 ]; then
    printf '%s WARNING authenticated tool sync failed rc=%s; continuing with cached tools\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$SYNC_RC" >> "$LOG_FILE"
  fi
fi

"$PYTHON_BIN" "$WORKER" --once --env-file "$ENV_FILE" >> "$LOG_FILE" 2>&1
BENCH_RC=$?

CTRL_RC=0
if [ -f "$CONTROLLER" ]; then
  "$PYTHON_BIN" "$CONTROLLER" --env-file "$ENV_FILE" >> "$LOG_FILE" 2>&1
  CTRL_RC=$?
else
  printf '%s autonomy controller not installed; execution-only mode\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
fi

DIAG_RC=0
if [ -f "$DIAG_WORKER" ]; then
  "$PYTHON_BIN" "$DIAG_WORKER" --env-file "$ENV_FILE" >> "$LOG_FILE" 2>&1
  DIAG_RC=$?
fi

# Diagnostics are observability-only. A diagnostic GitHub/read failure must not
# turn a successful benchmark/controller cycle into an execution failure.
RC=$BENCH_RC
if [ "$RC" -eq 0 ] && [ "$CTRL_RC" -ne 0 ]; then RC=$CTRL_RC; fi
printf '%s autonomy poll end sync_rc=%s benchmark_rc=%s controller_rc=%s diagnostic_rc=%s rc=%s\n' \
  "$(date '+%Y-%m-%d %H:%M:%S')" "$SYNC_RC" "$BENCH_RC" "$CTRL_RC" "$DIAG_RC" "$RC" >> "$LOG_FILE"
exit "$RC"
