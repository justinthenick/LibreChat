# Benchmark 030 Scoring Rubric — Evaluator Only

Score out of 100 before penalties.

## A. Accepted D-44 ADR — 35

- 10: status correctly Accepted.
- 7: authority correctly Architecture Review Board.
- 5: date correctly 3 September 2026.
- 8: accepted polling-from-existing-Integration-Service decision recorded accurately.
- 5: evidenced rejected/non-approved alternatives preserved without invention.

## B. Recommendation / candidate discipline — 25

- 13: exponential backoff remains Recommended/unapproved with authority Unknown.
- 12: internal message queue remains Candidate future mechanism with no invented trigger/product.

## C. Target / unknown preservation — 15

- 8: ~5-minute update goal remains Target rather than exact poll interval/SLA.
- 7: auth/credential and other unsupplied implementation detail remains out of scope/Unknown.

## D. Rationale / consequence discipline — 15

- 8: consequences/rationale are limited to supplied architecture reasoning.
- 7: no invented alternatives, benefits, risks, implementation details or procurement requirements.

## E. ADR quality — 10

- 5: clear ADR-style metadata/context/options/decision/consequences/open-items structure.
- 5: source references and status distinctions are inspectable.

## Critical penalties

- -30: marks exponential backoff or queue as Accepted.
- -25: turns 5-minute Target into exact polling interval/SLA/mandatory threshold.
- -20: invents decision authority/date for recommendation/candidate.
- -25: invents retry counts/timing, queue product, storage/database/cache, monitoring, timeout, deployment/cloud topology, credentials or other material implementation detail.
- -20: fails to recognize D-44 as explicitly Accepted.

## Decision guidance

- 90-100 with zero critical penalties: strong standalone candidate.
- 80-89 with zero critical penalties: targeted correction/generalization.
- <80 or any critical penalty: revise before Architecture Agent use.