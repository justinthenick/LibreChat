#!/bin/sh
# One-shot BA lab wrapper for Synology Task Scheduler.
# Self-refreshes authenticated lab tools, then runs a bounded burst of execution,
# deterministic fallback, semantic evaluation, and evidence-backed revision phases.
# The burst removes the old five-minute phase-to-phase wait: a fallback or rerun
# queued in one phase can be consumed immediately by the next burst cycle.

set -u

ROOT="/volume1/docker/librechat-ba-lab"
ENV_FILE="/volume1/docker/librechat/deploy/synology/.env"
BOOTSTRAP="$ROOT/custom/ba-agent/tools/bootstrap_nas.py"
WORKER="$ROOT/custom/ba-agent/tools/benchmark_worker.py"
CONTROLLER="$ROOT/custom/ba-agent/tools/autonomy_controller.py"
SEM_EVAL="$ROOT/custom/ba-agent/tools/semantic_evaluator.py"
SEM_REVISE="$ROOT/custom/ba-agent/tools/semantic_reviser.py"
DIAG_WORKER="$ROOT/custom/ba-agent/tools/diagnostic_worker.py"
LOG_DIR="$ROOT/custom/ba-agent/automation"
LOG_FILE="$LOG_DIR/scheduler.log"
LOCK_DIR="/tmp/librechat-ba-benchmark-worker.lock"
MAX_BURST_CYCLES="${BA_LAB_BURST_CYCLES:-4}"

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

case "$MAX_BURST_CYCLES" in
  ''|*[!0-9]*) MAX_BURST_CYCLES=4 ;;
esac
if [ "$MAX_BURST_CYCLES" -lt 1 ]; then MAX_BURST_CYCLES=1; fi
if [ "$MAX_BURST_CYCLES" -gt 8 ]; then MAX_BURST_CYCLES=8; fi

printf '%s autonomy poll start using %s burst_cycles=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$PYTHON_BIN" "$MAX_BURST_CYCLES" >> "$LOG_FILE"

SYNC_RC=0
if [ -f "$BOOTSTRAP" ]; then
  "$PYTHON_BIN" "$BOOTSTRAP" --tools-only --env-file "$ENV_FILE" >> "$LOG_FILE" 2>&1
  SYNC_RC=$?
  if [ "$SYNC_RC" -ne 0 ]; then
    printf '%s WARNING authenticated tool sync failed rc=%s; continuing with cached tools\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$SYNC_RC" >> "$LOG_FILE"
  fi
fi

RC=0
LAST_BENCH_RC=0
LAST_CTRL_RC=0
LAST_SEM_EVAL_RC=0
LAST_SEM_REVISE_RC=0
cycle=1
while [ "$cycle" -le "$MAX_BURST_CYCLES" ]; do
  printf '%s autonomy burst cycle %s/%s start\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$cycle" "$MAX_BURST_CYCLES" >> "$LOG_FILE"

  "$PYTHON_BIN" "$WORKER" --once --env-file "$ENV_FILE" >> "$LOG_FILE" 2>&1
  LAST_BENCH_RC=$?
  if [ "$RC" -eq 0 ] && [ "$LAST_BENCH_RC" -ne 0 ]; then RC=$LAST_BENCH_RC; fi

  LAST_CTRL_RC=0
  if [ -f "$CONTROLLER" ]; then
    "$PYTHON_BIN" "$CONTROLLER" --env-file "$ENV_FILE" >> "$LOG_FILE" 2>&1
    LAST_CTRL_RC=$?
    if [ "$RC" -eq 0 ] && [ "$LAST_CTRL_RC" -ne 0 ]; then RC=$LAST_CTRL_RC; fi
  else
    printf '%s autonomy controller not installed; execution-only mode\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
  fi

  LAST_SEM_EVAL_RC=0
  if [ -f "$SEM_EVAL" ]; then
    "$PYTHON_BIN" "$SEM_EVAL" --env-file "$ENV_FILE" >> "$LOG_FILE" 2>&1
    LAST_SEM_EVAL_RC=$?
    if [ "$RC" -eq 0 ] && [ "$LAST_SEM_EVAL_RC" -ne 0 ]; then RC=$LAST_SEM_EVAL_RC; fi
  fi

  LAST_SEM_REVISE_RC=0
  if [ -f "$SEM_REVISE" ]; then
    "$PYTHON_BIN" "$SEM_REVISE" --env-file "$ENV_FILE" >> "$LOG_FILE" 2>&1
    LAST_SEM_REVISE_RC=$?
    if [ "$RC" -eq 0 ] && [ "$LAST_SEM_REVISE_RC" -ne 0 ]; then RC=$LAST_SEM_REVISE_RC; fi
  fi

  printf '%s autonomy burst cycle %s/%s end benchmark_rc=%s controller_rc=%s semantic_eval_rc=%s semantic_revise_rc=%s\n' \
    "$(date '+%Y-%m-%d %H:%M:%S')" "$cycle" "$MAX_BURST_CYCLES" "$LAST_BENCH_RC" "$LAST_CTRL_RC" "$LAST_SEM_EVAL_RC" "$LAST_SEM_REVISE_RC" >> "$LOG_FILE"
  cycle=$((cycle + 1))
done

DIAG_RC=0
if [ -f "$DIAG_WORKER" ]; then
  "$PYTHON_BIN" "$DIAG_WORKER" --env-file "$ENV_FILE" >> "$LOG_FILE" 2>&1
  DIAG_RC=$?
fi

# Diagnostics are observability-only. Semantic evaluation/revision failures are
# real engineering-cycle failures and should surface in the scheduler return code.
printf '%s autonomy poll end sync_rc=%s benchmark_rc=%s controller_rc=%s semantic_eval_rc=%s semantic_revise_rc=%s diagnostic_rc=%s rc=%s\n' \
  "$(date '+%Y-%m-%d %H:%M:%S')" "$SYNC_RC" "$LAST_BENCH_RC" "$LAST_CTRL_RC" "$LAST_SEM_EVAL_RC" "$LAST_SEM_REVISE_RC" "$DIAG_RC" "$RC" >> "$LOG_FILE"
exit "$RC"
