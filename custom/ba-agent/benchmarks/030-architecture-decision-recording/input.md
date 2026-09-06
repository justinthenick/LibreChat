# Benchmark 030 Input — Vendor Status Integration Architecture Evidence

Record architecture decisions from the supplied evidence. Do not convert recommendations or unresolved implementation details into accepted decisions.

## Context

The internal Service Portal must obtain order-status updates from Vendor X. Vendor X does not provide webhooks. Its supported integration interface is a REST endpoint that clients may poll.

## Architecture analysis

Options considered:

1. Wait for a future vendor webhook. Rejected for the current delivery because Vendor X has confirmed no webhook is available or committed.
2. Poll the vendor REST endpoint from the existing Integration Service.
3. Introduce a new separate middleware component that polls Vendor X and forwards events internally.

The architecture analysis says Option 2 is the simplest current option because the existing Integration Service already owns this vendor boundary and no new component is required.

## Accepted decision D-44 — 3 September 2026

- Decision forum: Architecture Review Board.
- Status: Accepted.
- Decision: For the current release, Vendor X order status will be obtained by polling the supported REST endpoint from the existing Integration Service.
- The board explicitly rejected waiting for a webhook for the current release and did not approve a new middleware component.
- Decision owner/authority recorded in D-44: Architecture Review Board.

## Remaining design evidence

- Product team would like updates to appear within about **5 minutes**. This is recorded as a Target, not a hard polling interval.
- Lead architect recommends using exponential backoff for transient vendor errors, but no decision forum has accepted a retry strategy and Vendor X retry guidance has not yet been checked.
- One engineer suggested adding an internal message queue later if volume grows. This is a Candidate future mechanism only; no capacity threshold or decision exists.
- Authentication method for the vendor REST endpoint is already handled by the existing Integration Service and is explicitly outside the scope of D-44. No credential mechanism is supplied in this packet.
- No source establishes exact poll interval, timeout, retry count, queue product, database, cache, monitoring tool, deployment topology, or cloud service.

## Request

Create ADR-style records from this evidence. Preserve the accepted D-44 decision separately from recommendations/candidates and retain the 5-minute item as a Target.