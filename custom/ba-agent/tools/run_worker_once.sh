#!/bin/sh
# One-shot BA lab wrapper for Synology Task Scheduler.
#
# Reliability design:
# - an out-of-band diagnostic poll runs BEFORE the main worker lock, so a stuck
#   worker can still answer GitHub-triggered diagnostics on the next scheduler tick;
# - the main lock records its PID and stale locks are reclaimed safely;
# - every worker phase is run through bounded_exec.py so one wedged provider call
#   cannot hold the scheduler indefinitely;
# - a second diagnostic poll runs after the burst to publish post-cycle evidence.

set -u

ROOT="/volume1/docker/librechat-ba-lab"
ENV_FILE="/volume1/docker/librechat/deploy/synology/.env"
BOOTSTRAP="$ROOT/custom/ba-agent/tools/bootstrap_nas.py"
BOUND="$ROOT/custom/ba-agent/tools/bounded_exec.py"
WORKER="$ROOT/custom/ba-agent/tools/benchmark_worker.py"
DYNAMIC_WORKER="$ROOT/custom/ba-agent/tools/dynamic_agent_worker.py"
CONTROLLER="$ROOT/custom/ba-agent/tools/autonomy_controller.py"
SEM_EVAL="$ROOT/custom/ba-agent/tools/semantic_evaluator.py"
SEM_REVISE="$ROOT/custom/ba-agent/tools/semantic_reviser.py"
DIAG_WORKER="$ROOT/custom/ba-agent/tools/diagnostic_worker.py"
PROD_SEM_QUEUE="custom/ba-agent/automation/semantic-production-gates.json"
LOG_DIR="$ROOT/custom/ba-agent/automation"
LOG_FILE="$LOG_DIR/scheduler.log"
LOCK_DIR="/tmp/librechat-ba-benchmark-worker.lock"
DIAG_LOCK_DIR="/tmp/librechat-ba-diagnostic-worker.lock"
MAX_BURST_CYCLES="${BA_LAB_BURST_CYCLES:-4}"
PHASE_TIMEOUT="${BA_LAB_PHASE_TIMEOUT_SEC:-600}"
DIAG_TIMEOUT="${BA_LAB_DIAG_TIMEOUT_SEC:-90}"
SYNC_TIMEOUT="${BA_LAB_SYNC_TIMEOUT_SEC:-240}"

PATH="/usr/local/bin:/usr/bin:/bin:/usr/syno/bin:/usr/syno/sbin:$PATH"
export PATH
export PYTHONUNBUFFERED=1

mkdir -p "$LOG_DIR"
PYTHON_BIN="$(command -v python3 2>/dev/null || true)"
if [ -z "$PYTHON_BIN" ]; then
  printf '%s ERROR python3 not found in PATH=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$PATH" >> "$LOG_FILE"
  exit 2
fi

normalize_int() {
  value="$1"; default="$2"; min="$3"; max="$4"
  case "$value" in ''|*[!0-9]*) value="$default" ;; esac
  if [ "$value" -lt "$min" ]; then value="$min"; fi
  if [ "$value" -gt "$max" ]; then value="$max"; fi
  printf '%s' "$value"
}

MAX_BURST_CYCLES="$(normalize_int "$MAX_BURST_CYCLES" 4 1 8)"
PHASE_TIMEOUT="$(normalize_int "$PHASE_TIMEOUT" 600 60 1800)"
DIAG_TIMEOUT="$(normalize_int "$DIAG_TIMEOUT" 90 30 300)"
SYNC_TIMEOUT="$(normalize_int "$SYNC_TIMEOUT" 240 60 600)"

run_bounded() {
  timeout_sec="$1"; shift
  if [ -f "$BOUND" ]; then
    "$PYTHON_BIN" "$BOUND" --timeout "$timeout_sec" --log "$LOG_FILE" -- "$@"
    return $?
  fi
  "$@" >> "$LOG_FILE" 2>&1
}

run_diagnostic_poll() {
  [ -f "$DIAG_WORKER" ] || return 0
  if ! mkdir "$DIAG_LOCK_DIR" 2>/dev/null; then
    return 0
  fi
  printf '%s\n' "$$" > "$DIAG_LOCK_DIR/pid"
  run_bounded "$DIAG_TIMEOUT" "$PYTHON_BIN" "$DIAG_WORKER" --env-file "$ENV_FILE"
  diag_rc=$?
  rm -rf "$DIAG_LOCK_DIR" 2>/dev/null || true
  return "$diag_rc"
}

# Crucial: diagnostics run even when a previous main worker invocation is still
# active. This gives the GitHub control channel a way to inspect a stalled cycle.
PRE_DIAG_RC=0
run_diagnostic_poll || PRE_DIAG_RC=$?

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  LOCK_PID=""
  if [ -f "$LOCK_DIR/pid" ]; then
    LOCK_PID="$(sed -n '1p' "$LOCK_DIR/pid" 2>/dev/null || true)"
  fi
  if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
    printf '%s worker already active pid=%s; out-of-band diagnostic_rc=%s; skipping main burst\n' \
      "$(date '+%Y-%m-%d %H:%M:%S')" "$LOCK_PID" "$PRE_DIAG_RC" >> "$LOG_FILE"
    exit 0
  fi
  printf '%s WARNING removing stale worker lock pid=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "${LOCK_PID:-unknown}" >> "$LOG_FILE"
  rm -rf "$LOCK_DIR" 2>/dev/null || true
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    printf '%s ERROR unable to acquire worker lock after stale-lock cleanup\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
    exit 1
  fi
fi
printf '%s\n' "$$" > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR" 2>/dev/null || true' EXIT HUP INT TERM

printf '%s autonomy poll start pid=%s python=%s burst_cycles=%s phase_timeout=%ss pre_diagnostic_rc=%s\n' \
  "$(date '+%Y-%m-%d %H:%M:%S')" "$$" "$PYTHON_BIN" "$MAX_BURST_CYCLES" "$PHASE_TIMEOUT" "$PRE_DIAG_RC" >> "$LOG_FILE"

SYNC_RC=0
if [ -f "$BOOTSTRAP" ]; then
  run_bounded "$SYNC_TIMEOUT" "$PYTHON_BIN" "$BOOTSTRAP" --tools-only --env-file "$ENV_FILE"
  SYNC_RC=$?
  if [ "$SYNC_RC" -ne 0 ]; then
    printf '%s WARNING authenticated tool sync failed rc=%s; continuing with cached tools\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$SYNC_RC" >> "$LOG_FILE"
  fi
fi

run_phase() {
  label="$1"; shift
  printf '%s phase=%s start\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$label" >> "$LOG_FILE"
  run_bounded "$PHASE_TIMEOUT" "$@"
  phase_rc=$?
  printf '%s phase=%s end rc=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$label" "$phase_rc" >> "$LOG_FILE"
  return "$phase_rc"
}

RC=0
LAST_BENCH_RC=0
LAST_DYNAMIC_RC=0
LAST_CTRL_RC=0
LAST_SEM_EVAL_RC=0
LAST_PROD_SEM_EVAL_RC=0
LAST_SEM_REVISE_RC=0
TIMED_OUT=0
cycle=1
while [ "$cycle" -le "$MAX_BURST_CYCLES" ]; do
  printf '%s autonomy burst cycle %s/%s start\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$cycle" "$MAX_BURST_CYCLES" >> "$LOG_FILE"

  run_phase "benchmark[$cycle]" "$PYTHON_BIN" "$WORKER" --once --env-file "$ENV_FILE"
  LAST_BENCH_RC=$?
  if [ "$RC" -eq 0 ] && [ "$LAST_BENCH_RC" -ne 0 ]; then RC=$LAST_BENCH_RC; fi
  if [ "$LAST_BENCH_RC" -eq 124 ]; then TIMED_OUT=1; break; fi

  LAST_DYNAMIC_RC=0
  if [ -f "$DYNAMIC_WORKER" ]; then
    run_phase "dynamic[$cycle]" "$PYTHON_BIN" "$DYNAMIC_WORKER" --env-file "$ENV_FILE"
    LAST_DYNAMIC_RC=$?
    if [ "$RC" -eq 0 ] && [ "$LAST_DYNAMIC_RC" -ne 0 ]; then RC=$LAST_DYNAMIC_RC; fi
    if [ "$LAST_DYNAMIC_RC" -eq 124 ]; then TIMED_OUT=1; break; fi
  fi

  LAST_CTRL_RC=0
  if [ -f "$CONTROLLER" ]; then
    run_phase "controller[$cycle]" "$PYTHON_BIN" "$CONTROLLER" --env-file "$ENV_FILE"
    LAST_CTRL_RC=$?
    if [ "$RC" -eq 0 ] && [ "$LAST_CTRL_RC" -ne 0 ]; then RC=$LAST_CTRL_RC; fi
    if [ "$LAST_CTRL_RC" -eq 124 ]; then TIMED_OUT=1; break; fi
  else
    printf '%s autonomy controller not installed; execution-only mode\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
  fi

  LAST_SEM_EVAL_RC=0
  if [ -f "$SEM_EVAL" ]; then
    run_phase "semantic-eval[$cycle]" "$PYTHON_BIN" "$SEM_EVAL" --env-file "$ENV_FILE"
    LAST_SEM_EVAL_RC=$?
    if [ "$RC" -eq 0 ] && [ "$LAST_SEM_EVAL_RC" -ne 0 ]; then RC=$LAST_SEM_EVAL_RC; fi
    if [ "$LAST_SEM_EVAL_RC" -eq 124 ]; then TIMED_OUT=1; break; fi

    run_phase "production-semantic-eval[$cycle]" "$PYTHON_BIN" "$SEM_EVAL" --env-file "$ENV_FILE" --semantic-jobs "$PROD_SEM_QUEUE"
    LAST_PROD_SEM_EVAL_RC=$?
    if [ "$RC" -eq 0 ] && [ "$LAST_PROD_SEM_EVAL_RC" -ne 0 ]; then RC=$LAST_PROD_SEM_EVAL_RC; fi
    if [ "$LAST_PROD_SEM_EVAL_RC" -eq 124 ]; then TIMED_OUT=1; break; fi
  fi

  LAST_SEM_REVISE_RC=0
  if [ -f "$SEM_REVISE" ]; then
    run_phase "semantic-revise[$cycle]" "$PYTHON_BIN" "$SEM_REVISE" --env-file "$ENV_FILE"
    LAST_SEM_REVISE_RC=$?
    if [ "$RC" -eq 0 ] && [ "$LAST_SEM_REVISE_RC" -ne 0 ]; then RC=$LAST_SEM_REVISE_RC; fi
    if [ "$LAST_SEM_REVISE_RC" -eq 124 ]; then TIMED_OUT=1; break; fi
  fi

  printf '%s autonomy burst cycle %s/%s end benchmark_rc=%s dynamic_rc=%s controller_rc=%s semantic_eval_rc=%s production_semantic_eval_rc=%s semantic_revise_rc=%s\n' \
    "$(date '+%Y-%m-%d %H:%M:%S')" "$cycle" "$MAX_BURST_CYCLES" "$LAST_BENCH_RC" "$LAST_DYNAMIC_RC" "$LAST_CTRL_RC" "$LAST_SEM_EVAL_RC" "$LAST_PROD_SEM_EVAL_RC" "$LAST_SEM_REVISE_RC" >> "$LOG_FILE"
  cycle=$((cycle + 1))
done

POST_DIAG_RC=0
run_diagnostic_poll || POST_DIAG_RC=$?

if [ "$TIMED_OUT" -eq 1 ]; then
  printf '%s ERROR lab burst stopped because a phase exceeded hard timeout=%ss\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$PHASE_TIMEOUT" >> "$LOG_FILE"
fi

# Diagnostics are observability-only. Semantic evaluation/revision failures and
# hard phase timeouts are real engineering-cycle failures and surface in RC.
printf '%s autonomy poll end sync_rc=%s benchmark_rc=%s dynamic_rc=%s controller_rc=%s semantic_eval_rc=%s production_semantic_eval_rc=%s semantic_revise_rc=%s pre_diagnostic_rc=%s post_diagnostic_rc=%s timed_out=%s rc=%s\n' \
  "$(date '+%Y-%m-%d %H:%M:%S')" "$SYNC_RC" "$LAST_BENCH_RC" "$LAST_DYNAMIC_RC" "$LAST_CTRL_RC" "$LAST_SEM_EVAL_RC" "$LAST_PROD_SEM_EVAL_RC" "$LAST_SEM_REVISE_RC" "$PRE_DIAG_RC" "$POST_DIAG_RC" "$TIMED_OUT" "$RC" >> "$LOG_FILE"
exit "$RC"
