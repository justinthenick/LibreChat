# NAS telemetry freshness acceptance

Status: implementation proposed in draft PR #225. Runtime change is **not yet merged or deployed**.

## Evidence (2026-10-12)
- Last retrieved `nas-status/telemetry/latest.json` timestamp: `2026-10-08T20:06:57+1000`.
- Last published executor: HTTP 200, version 0.1.14; maintenance reachable. **Historical only, not current health.**
- `deploy/synology/publish-telemetry.sh` writes `telemetry/latest.json`, `telemetry/launchpad.json`, and `telemetry/latest.log` to `nas-status`.
- `deploy/synology/launchpad-telemetry.py` already collects sanitized executor/maintenance connectivity.
- `autodeploy.sh` invokes the publisher on successful deployments, deployment failures, and healthy steady-state polls when the marker is absent or older than 60 minutes. The NAS scheduler's enabled state and actual polling cadence are not yet verified.
- The new `telemetry-freshness.py` uses Python 3 `os.stat().st_mtime`, not Synology-dependent `find -mmin`; host Python 3 is already required by `autodeploy.sh`.
- A due heartbeat with an existing marker is `check / steady_state_periodic`, distinct from missing-marker `check / steady_state` recovery. This avoids false recovery statuses and hourly success-history commits. The routine poll updates the latest snapshots but does not create a historical recovery event.
- `publish-telemetry.sh` updates the marker only after successful publication. An unsuccessful publish leaves the prior marker unchanged, allowing retry on a later healthy poll.
- Focused shell regression test covers missing, recent, stale, future-dated, and malformed-content markers; `Synology Admin Settings` CI explicitly executes it.

## Remaining NAS-side acceptance
- Confirm the DSM scheduler is enabled and actually invokes `autodeploy.sh` at its configured cadence.
- After merge, verify a new `nas-status/telemetry/latest.json` timestamp from the NAS and check that no unnecessary LibreChat deployment occurred.
- Keep old telemetry classified as historical until that fresh publication is observed.

## Questions to resolve
1. How often is `autodeploy.sh` scheduled, and under which branches does it invoke the publisher?
2. Is the four-day gap caused by an inactive scheduler, a publication policy, GitHub API failures, network problems, or unavailable NAS?
3. Does the published timestamp represent collection time, and can consumers distinguish collection from publication?
4. Is GitHub status `nas/librechat` current, or also stale?

## Acceptance criteria
- Document intended publication cadence, including healthy steady-state.
- Define `fresh`, `stale`, and `unavailable` from a parseable UTC timestamp, with threshold tied to actual cadence.
- Never interpret an old green snapshot as current service health.
- Test missing, malformed, future-dated, and stale snapshots.
- Keep diagnostics read-only and sanitized: no secrets, private addresses, arbitrary command output, or raw logs.
- Review and staging validation before any merge to `server/synology`; no auto-deploy from this branch.

## Implementation boundary
Prefer the smallest tested change to existing publisher/consumer behavior. Do not add arbitrary remote execution, and do not modify OpenHands PR #182.
