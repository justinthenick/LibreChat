# BA Lab NAS Control Channel

## Purpose

Provide a bounded, GitHub-mediated request/response path for troubleshooting the Synology BA lab without requiring an interactive shell session or manual log pasting.

The control channel is observability-only. GitHub requests select allowlisted diagnostic recipes; they cannot supply arbitrary shell commands and the worker never publishes secret values.

## Cycle behaviour

`custom/ba-agent/tools/run_worker_once.sh` is the Synology Task Scheduler entrypoint.

Each invocation now:

1. runs a diagnostic poll **before** acquiring the main benchmark lock;
2. reclaims a stale main lock when its recorded PID is no longer alive;
3. records the live wrapper PID in the main lock directory;
4. self-refreshes authenticated lab tools;
5. runs each benchmark/dynamic/controller/evaluator/reviser phase through `bounded_exec.py` with a hard wall-clock timeout;
6. stops the burst on a hard timeout rather than holding the lock indefinitely;
7. runs another diagnostic poll after the burst.

The pre-lock diagnostic step is deliberate: if a previous main cycle is stuck, the next scheduler tick can still execute a GitHub diagnostic request and publish the result.

## Request

Update:

`custom/ba-agent/automation/diagnostic-request.json`

with a fresh `request_id` and an allowlisted recipe under:

`custom/ba-agent/diagnostics/*.json`

Example:

```json
{
  "schema": 1,
  "enabled": true,
  "request_id": "cycle-health-20260909-001",
  "recipe": "custom/ba-agent/diagnostics/cycle-health.json"
}
```

A request ID is one-shot. Reusing an already-published request ID is intentionally idempotent and does not rerun it.

## Response

The NAS publishes structured JSON to:

`custom/ba-agent/automation/diagnostic-results/<request_id>.json`

This is the primary response path for remote diagnosis.

## Available diagnostic checks

The diagnostic worker currently allowlists:

- `python_info`
- `path_exists`
- `tail` for allowlisted lab files (never `.env` contents)
- `lock_status` with process matching
- `worker_state` for selected job IDs
- `queue_compare` between a GitHub job queue and local worker state
- `disk_usage`
- `env_presence` for explicitly allowlisted credential names, returning presence booleans only

Recipes can combine up to 20 checks. No recipe may execute a shell command supplied from GitHub.

## Standard recipes

- `cycle-health.json` — general scheduler/worker/process/queue/disk/log health.
- `worker-health.json` — benchmark worker-specific health.
- task-specific recipes may be created for a particular benchmark or incident and then removed or retained as evidence.

## Timeout controls

Defaults in `run_worker_once.sh`:

- phase timeout: 600 seconds
- diagnostic timeout: 90 seconds
- authenticated tool-sync timeout: 240 seconds

Environment overrides are bounded:

- `BA_LAB_PHASE_TIMEOUT_SEC` (60..1800)
- `BA_LAB_DIAG_TIMEOUT_SEC` (30..300)
- `BA_LAB_SYNC_TIMEOUT_SEC` (60..600)
- `BA_LAB_BURST_CYCLES` (1..8)

A timed-out phase returns `124`, is logged, terminates its process group, and stops the current burst so the lock can be released and the next scheduler cycle can recover.

## Queue output size

Benchmark jobs may specify:

```json
"max_output_tokens": 16384
```

The benchmark worker validates 1024..32768 and passes the value to `benchmark_runner.py`. This avoids manual one-shot commands for large BA packages.

## Troubleshooting pattern

When a cycle appears stalled:

1. create or reuse an appropriate diagnostic recipe;
2. set a fresh request ID in `diagnostic-request.json`;
3. allow one scheduler tick;
4. read `diagnostic-results/<request_id>.json`;
5. inspect lock PID/process, pending queue IDs, worker-state records and scheduler tail;
6. change code/queue only from evidence returned by that result.

This mechanism is designed specifically so step 4 can still work when the main worker is already locked by a previous cycle.
