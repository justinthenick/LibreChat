# Benchmark 024 Scoring Rubric — Evaluator Only

Score out of 100 before penalties.

## A. Reference integrity — 20

- 8: identifies T-03 -> AC-99 as a phantom/unresolved reference and does not silently repair it.
- 6: distinguishes valid REQ-01 -> WI-01 -> AC-01 -> T-01 lineage.
- 6: identifies material missing/lost lineage without claiming every blocked/deferred item requires committed AC/tests.

## B. Status and requirement-strength integrity — 25

- 12: correctly identifies REQ-02 Candidate -> Confirmed/mandatory drift across downstream artifacts.
- 10: correctly identifies REQ-03 Target -> mandatory/SLA/release-threshold drift.
- 3: notes REQ-04 Deferred should remain visibly Deferred/out of current scope rather than disappear.

## C. Authority and governance integrity — 20

- 10: identifies DEC-01 `Decision owner: Unknown` becoming Security/Maya authority.
- 5: explains that Maya's preference/role does not establish decision authority.
- 5: identifies CAB approval as an invented gate.

## D. Constraint / semantic coverage — 15

- 8: identifies loss of confirmed CON-01 manual fallback.
- 7: identifies T-04 immutable audit-log behavior as invented assurance/product behavior.

## E. Audit quality and discipline — 20

- 5: gives an appropriate overall verdict.
- 5: findings are evidence-backed with artifact/ID references and sensible severity.
- 5: separates demonstrated defects from questions/observations.
- 5: does not rewrite the artifacts or invent remediation owners/mechanisms.

## Critical penalties

Apply after raw score; floor at 0.

- -30: fails to identify either REQ-02 Candidate hardening or REQ-03 Target hardening.
- -25: accepts or repeats Maya/Security/CAB as established authority/governance.
- -20: treats AC-99 as if it exists or silently repairs it without identifying the defect.
- -20: invents new requirements, owners, approval bodies, architecture, implementation steps, or validation methods as part of the audit.
- -15: claims Deferred/blocked work must automatically have committed AC/tests, demonstrating inability to distinguish legitimate stop conditions from coverage defects.

## Decision guidance

- 90-100 with zero critical penalties: strong standalone candidate.
- 80-89 with zero critical penalties: retain for targeted correction/generalization.
- <80 or any critical penalty: revise before composition/release.