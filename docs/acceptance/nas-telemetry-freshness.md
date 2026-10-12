# NAS telemetry freshness acceptance

Status: investigation / draft. No production change.

## Evidence (2026-10-12)
- Last retrieved `nas-status/telemetry/latest.json` timestamp: `2026-10-08T20:06:57+1000`.
- Last published executor: HTTP 200, version 0.1.14; maintenance reachable. **Historical only, not current health.**
- `deploy/synology/publish-telemetry.sh` writes `telemetry/latest.json`, `telemetry/launchpad.json`, and `telemetry/latest.log` to `nas-status`.
- `deploy/synology/launchpad-telemetry.py` already collects sanitized executor/maintenance connectivity.
- Publisher uses a telemetry marker; inspect invocation cadence in `autodeploy.sh` before changing anything.

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
