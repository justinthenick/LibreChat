# Benchmark 029 Scoring Rubric — Evaluator Only

Score out of 100 before penalties.

## A. Explicit supported changes — 30

- 10: REQ-12 Candidate -> Accepted/Confirmed managed SFTP via AD-7.
- 10: approved invoice-status requirement recognized as Added with source provenance.
- 10: REQ-15 explicitly Removed/withdrawn via D-36.

## B. Unresolved proposal discipline — 25

- 13: REQ-10 remains current 18:00 Confirmed while 19:00 is only a proposed/unresolved change.
- 12: REQ-11 remains Confirmed 30-day retention; analyst suggestion does not remove it.

## C. Silence / unchanged discipline — 15

- 8: REQ-13 remains Confirmed despite absence from later notes.
- 7: CON-02 preserved as Confirmed unchanged.

## D. Authority / provenance discipline — 15

- 8: no Finance/Data Owner/other authority invented; unresolved owner remains Unknown where relevant.
- 7: old and new source/status provenance is clearly shown for material deltas.

## E. Selective downstream handoff — 15

- 8: identifies REQ-12, new invoice-status requirement and REQ-15 as needing downstream update/review.
- 7: prevents premature downstream changes for REQ-10/REQ-11 and correctly leaves REQ-13/CON-02 unchanged.

## Critical penalties

- -30: treats REQ-10 19:00 proposal as approved replacement.
- -25: removes/changes REQ-11 based only on analyst suggestion.
- -25: treats REQ-13 as removed due to silence.
- -20: invents Finance, Data Owner or another Decision Owner/authority.
- -20: fails to recognize AD-7 or D-36 explicit decision evidence.
- -15: rewrites baseline items without preserving provenance.

## Decision guidance

- 90-100 with zero critical penalties: strong standalone candidate.
- 80-89 with zero critical penalties: targeted correction/generalization.
- <80 or any critical penalty: revise before delta-driven Agent composition.