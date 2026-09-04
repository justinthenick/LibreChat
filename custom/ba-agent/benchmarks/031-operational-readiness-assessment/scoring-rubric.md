# Benchmark 031 Scoring Rubric — Evaluator Only

Score out of 100 before penalties.

## A. Confirmed blocker recognition — 25

- 15: production write permission failure correctly classified Not ready.
- 10: ACC-91 Open/no successful re-test used to support blocker conclusion.

## B. Ready evidence — 25

- 5: service ownership/support coverage recognized.
- 5: vendor support contact recognized.
- 5: approved RB-12 recognized.
- 5: manual fallback recognized.
- 5: release version/configuration record recognized.

## C. Partial / not-evidenced discipline — 20

- 7: draft service-desk article classified Partially ready rather than complete.
- 7: monitoring definition/planned deployment classified Partially ready/Not evidenced for production activation.
- 6: RTO/RPO and other absent artifacts treated as Not evidenced/questions, not automatic blockers.

## D. Residual risk / scope discipline — 15

- 8: DEF-42 preserved as explicitly accepted residual risk with Billing Operations authority scoped to that decision.
- 7: future automated retry remains Deferred/out of current release.

## E. Governance / handoff discipline — 15

- 7: CMDB/service-catalog update not promoted into unsupported pre-release gate.
- 8: Change/ITIL handoff clearly separates blocker, ready evidence, accepted risk and unknown/not-evidenced items.

## Critical penalties

- -35: overall assessment fails to treat permission-denied write failure as a production blocker.
- -25: turns CMDB, 24x7 on-call, DR exercise, backup, capacity test, formal KT, security sign-off or other absent generic artifact into mandatory local gate without evidence.
- -25: invents monitoring tool/threshold/alert route, RTO/RPO, owner, approval or procedure.
- -20: claims production monitoring/alerts are active when only planned.
- -20: ignores or changes DEF-42 accepted residual-risk status / pulls Deferred retry into current scope.

## Decision guidance

- 90-100 with zero critical penalties: strong standalone candidate.
- 80-89 with zero critical penalties: targeted correction/generalization.
- <80 or any critical penalty: revise before Delivery Assurance composition.