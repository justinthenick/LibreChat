#!/bin/sh
# One-shot B042 Gemini 3.7 vs 3.8 comparison with a larger output budget.
# This intentionally bypasses the normal queue's 8192-token default without
# changing global benchmark-runner behavior.

set -eu

ROOT="/volume1/docker/librechat-ba-lab"
BENCH="$ROOT/custom/ba-agent/benchmarks/042-multisource-ba-model-comparison"
RUNNER="$ROOT/custom/ba-agent/tools/benchmark_runner.py"
ENV_FILE="/volume1/docker/librechat/deploy/synology/.env"
BRANCH="feature/ba-agent-v0.1"
REPO="justinthenick/LibreChat"
TOKEN_ENV="GITHUB_TELEMETRY_TOKEN"
MAX_TOKENS="16384"

PYTHON_BIN="$(command -v python3 2>/dev/null || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "ERROR: python3 not found"
  exit 2
fi
if [ ! -f "$RUNNER" ]; then
  echo "ERROR: benchmark runner not found: $RUNNER"
  exit 2
fi
if [ ! -f "$BENCH/benchmark.json" ]; then
  echo "ERROR: B042 benchmark not present locally: $BENCH"
  exit 2
fi

run_one() {
  model="$1"
  run_id="$2"
  echo "[B042] starting $model as $run_id with max_output_tokens=$MAX_TOKENS"
  "$PYTHON_BIN" "$RUNNER" "$BENCH" \
    --model "$model" \
    --mode skill \
    --repeat 1 \
    --temperature 0.0 \
    --max-output-tokens "$MAX_TOKENS" \
    --run-id "$run_id" \
    --env-file "$ENV_FILE" \
    --publish-github \
    --github-token-env "$TOKEN_ENV" \
    --github-repo "$REPO" \
    --github-branch "$BRANCH"
}

run_one "gemini-3.7-flash" "b042-g37-multisource-ba-model-005"
run_one "gemini-3.8-flash" "b042-g38-multisource-ba-model-006"

echo "[B042] extended comparison complete"
