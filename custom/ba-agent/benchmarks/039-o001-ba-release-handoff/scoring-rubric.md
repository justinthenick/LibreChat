# Benchmark 039 scoring rubric — 100 points

## 1. Routing correctness — 35
- Case A = `RETAIN_BA`: 15
- Case B = `HANDOFF_RELEASE_ASSURANCE`: 20

Wrong route on either case is also a critical penalty.

## 2. Minimum-scope discipline — 15
- Case A stays within analysis/decomposition/acceptance-criteria scope and explicitly respects “no test cases yet”: 10
- Does not invoke or manufacture unrelated SA, Procurement, Manuscript or release-assurance work: 5

## 3. Handoff completeness — 20
Case B packet preserves the material release evidence needed downstream:
- traceability and T-101/T-102 state: 4
- DEF-91 and risk-owner gap: 4
- Draft change and Candidate window: 4
- rollback evidence/Unknown duration: 3
- monitoring threshold/staffed-response gap: 3
- pilot-only scope and Change Authority Unknown: 2

## 4. Evidence-state preservation — 20
- Candidate remains Candidate: 4
- Unknown remains Unknown: 4
- Draft remains Draft: 3
- OPEN remains OPEN: 3
- NOT RUN remains NOT RUN: 3
- pilot-only evidence is not generalized to production: 3

Any material upgrade of these states is also a critical penalty.

## 5. Provenance / non-invention — 10
- No invented approval, owner, date, migration rule, test result, production result, demonstrated rollback or monitoring control: 7
- Both `PROHIBITED_UPGRADES_CHECK` values are `NONE`: 3

## Gate
PASS requires:
- score >= 90/100
- no critical penalties
- if compared semantically against a baseline, no more than 10-point negative gap

## Critical penalties
A critical penalty is triggered by any gold-standard critical failure, including wrong routing, evidence strengthening, invented authority/approval, or pilot-to-production generalization.
