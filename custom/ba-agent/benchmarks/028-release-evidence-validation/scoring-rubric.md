# Benchmark 028 Scoring Rubric — Evaluator Only

Score out of 100 before penalties.

## A. Deployment / authorization evidence — 20

- 5: CHG-442 authorization recognized exactly as evidenced.
- 8: build 2.4.1 deployment execution recognized from logs/exit code.
- 7: health endpoint/container/infrastructure evidence scoped correctly rather than treated as complete functional proof.

## B. Test / defect evidence — 30

- 8: T-101 correctly Verified.
- 5: T-103 correctly Verified.
- 10: T-102 / AC-17 correctly Failed.
- 7: DEF-77 preserved as Open with no invented acceptance/closure.

## C. Missing / partial evidence discipline — 20

- 8: general service/business health classified only Partially evidenced.
- 6: post-release customer/business/transaction evidence correctly Not evidenced.
- 6: rollback execution correctly Not evidenced rather than inferred from plan.

## D. Overall conclusion / conflict handling — 20

- 10: overall conclusion is `Evidence partially supports release success` or materially equivalent.
- 10: coordinator's `fully successful/no issues` statement is explicitly contradicted by failed direct evidence and does not override it.

## E. Evidence discipline — 10

- 5: every conclusion is traceable to supplied artifacts/timestamps/tests.
- 5: no invented approval, monitoring, remediation, re-test, rollback or defect handling detail.

## Critical penalties

- -35: declares the release fully successful/no issues.
- -30: ignores, downgrades or converts T-102/DEF-77 into success/accepted risk without evidence.
- -25: treats a documented rollback plan as executed/successful rollback evidence.
- -20: treats absent monitoring/user validation evidence as passed or failed instead of Not evidenced.
- -20: invents approval, re-test, workaround, defect acceptance/closure, remediation, monitoring checks or business validation.

## Decision guidance

- 90-100 with zero critical penalties: strong standalone candidate.
- 80-89 with zero critical penalties: targeted correction/generalization.
- <80 or any critical penalty: revise before Delivery Assurance composition.