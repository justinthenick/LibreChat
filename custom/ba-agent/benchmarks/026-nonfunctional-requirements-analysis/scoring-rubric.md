# Benchmark 026 Scoring Rubric — Evaluator Only

Score out of 100 before penalties.

## A. Confirmed NFR/constraint extraction — 25

- 7: Australian data residency correctly Confirmed.
- 6: support window correctly Confirmed.
- 6: manual email fallback correctly Confirmed.
- 6: support claim-identification outcome correctly Confirmed without inventing mechanism.

## B. Target / candidate / estimate discipline — 35

- 8: 99.9% availability preserved as Target, not SLA/SLO.
- 7: 2,000 concurrent users preserved as planning estimate, not hard capacity requirement.
- 7: encryption-at-rest preserved as Candidate/policy-pending and no algorithm/mechanism invented.
- 7: WCAG 2.2 AA preserved as Candidate/unapproved.
- 6: `feel fast` remains qualitative with no invented response-time threshold.

## C. Recovery and unknowns — 15

- 8: same-day recovery language preserved as tentative; RTO/RPO remain Unknown.
- 7: relevant absent NFRs are questions/unassessed areas rather than invented requirements.

## D. Solution-design handoff — 15

- 8: clearly identifies which Confirmed items architecture may rely on.
- 7: explicitly protects Targets/Candidates/estimates/Unknowns from hardening downstream.

## E. Analysis quality — 10

- 5: appropriate readiness judgment and traceable register.
- 5: no generic checklist inflation, governance invention, or mechanism substitution.

## Critical penalties

- -30: invents any numeric response-time, RTO or RPO threshold.
- -25: turns 99.9% availability into a mandatory SLA/SLO.
- -20: turns 2,000 concurrent users into a hard capacity requirement.
- -20: makes WCAG 2.2 AA or encryption-at-rest mandatory without noting their Candidate status.
- -20: invents encryption algorithm, active-active/redundancy/autoscaling/backup/monitoring/logging technology or equivalent architecture mechanism.
- -20: invents regulatory, certification or approval obligations.

## Decision guidance

- 90-100 with zero critical penalties: strong standalone candidate.
- 80-89 with zero critical penalties: targeted correction/generalization.
- <80 or any critical penalty: revise before Architecture composition.