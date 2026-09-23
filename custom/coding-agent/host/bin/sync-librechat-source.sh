#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${CODING_AGENT_LIBRECHAT_REPO:-$HOME/coding-agent/repos/LibreChat}"
EXPECTED_UPSTREAM="${CODING_AGENT_LIBRECHAT_UPSTREAM:-origin/server/synology}"
TASK_ROOT="${CODING_AGENT_TASK_ROOT:-$HOME/coding-agent/tasks}"
HOST_SRC="$REPO_ROOT/custom/coding-agent/host/src"

if [ ! -e "$REPO_ROOT/.git" ]; then
  echo "LibreChat source repository not found at $REPO_ROOT" >&2
  exit 1
fi

if [ ! -d "$HOST_SRC/source_preflight" ]; then
  echo "source_preflight package not found at $HOST_SRC" >&2
  exit 1
fi

if [ ! -d "$TASK_ROOT" ]; then
  echo "coding-agent task root not found at $TASK_ROOT" >&2
  exit 1
fi

if ! command -v flock >/dev/null 2>&1; then
  echo "flock is required to serialize source refresh with task creation" >&2
  exit 1
fi

exec 9>"$TASK_ROOT/.source-sync.lock"
flock -x 9

export PYTHONPATH="$HOST_SRC${PYTHONPATH:+:$PYTHONPATH}"

exec python3 -m source_preflight.cli \
  "$REPO_ROOT" \
  --expected-upstream "$EXPECTED_UPSTREAM" \
  --json
