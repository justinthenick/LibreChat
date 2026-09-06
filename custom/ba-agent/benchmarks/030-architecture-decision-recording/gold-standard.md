# Benchmark 030 Gold Standard — Evaluator Only

## ADR 1 — Accepted current integration mechanism

Expected status: `Accepted`.

- Title: Poll Vendor X REST endpoint from existing Integration Service.
- Decision authority: Architecture Review Board.
- Decision date: 3 September 2026.
- Source: D-44.
- Context: Service Portal needs Vendor X order status; Vendor X has no webhook.
- Options evidenced:
  1. wait for future webhook — rejected for current release;
  2. poll REST from existing Integration Service — accepted;
  3. introduce new middleware poller — not approved for current release.
- Accepted decision: current release uses polling of supported REST endpoint from existing Integration Service.
- Supported rationale/consequence: preserves current vendor-boundary ownership and avoids adding a new middleware component; future webhook is not available for current delivery.

Do not add exact poll interval, timeout, retry policy, queue, storage, monitoring, deployment topology or credential mechanism.

## ADR candidate / recommendation — retry strategy

The lead architect's exponential-backoff statement is **Recommended**, not Accepted.

- Decision owner/authority: Unknown.
- Decision date: Unknown unless the source timestamp for the recommendation is explicitly treated as statement date rather than decision date.
- Vendor retry guidance remains unchecked.
- No retry count, timing/backoff values or mechanism details may be invented.

## Candidate future mechanism — internal message queue

The engineer suggestion is `Candidate` future architecture only.

- No Accepted decision.
- No queue product, trigger threshold, volume requirement or topology is established.

## Target

- `updates within about 5 minutes` remains a Target.
- It must not become an accepted exact polling interval or SLA.

## Out-of-scope / unknown detail

- authentication method is outside D-44 and not supplied here; do not invent credentials.

## Critical defects

- marking exponential backoff or queue as Accepted;
- converting 5-minute Target into exact polling interval/requirement;
- inventing owner/date for unapproved recommendation/candidate;
- inventing retry counts/timing, queue product, monitoring, storage, timeout, deployment/cloud topology, or credential mechanism;
- failing to record D-44 as explicitly Accepted.