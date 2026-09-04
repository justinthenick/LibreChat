# A001 Evaluation — BA Change Delivery Orchestrator

Evaluator-only record. Raw model outputs remain unchanged.

## Common control

- Benchmark: B023 / A001 routing
- Model: `gemini-3.6-flash`
- Temperature: `0.0`
- Baseline: 2026-09-05 00:45:04–00:45:45 Australia/Sydney, 3,049 total tokens

### Baseline — 91/100, zero critical penalties

- A. Agent routing: 25/25
- B. Evidence/status preservation: 22/25
- C. Delivery/readiness discipline: 15/20
- D. ITIL alignment quality: 15/15
- E. Authority / invention discipline: 10/10
- F. Traceability / usability: 4/5

The baseline selected and ordered all six required Skills correctly, preserved the main Candidate/Target/Deferred/Disputed/Unknown boundaries, and avoided governance/architecture invention. It did not clearly carry the explicit local-policy approved-change-record gate into the route, and the confirmed corporate-identity/MFA outcome was only implicit rather than clearly preserved as a source-backed constraint.

## Agent v0.1

- Job: `a001-g36-ba-change-router-v01-ab-004`
- Execution: 2026-09-05 00:45:45–00:46:34 Australia/Sydney
- Total tokens: 3,651
- Score: **89/100**, zero critical penalties

Breakdown:

- A. Agent routing: 25/25
- B. Evidence/status preservation: 19/25
- C. Delivery/readiness discipline: 15/20
- D. ITIL alignment quality: 15/15
- E. Authority / invention discipline: 10/10
- F. Traceability / usability: 5/5

The Agent was excellent at routing and unresolved-state protection, but its safety emphasis was asymmetric: it explicitly preserved almost every non-committed state while failing to carry two source-backed confirmed constraints that materially govern downstream work:

1. workforce access must use corporate identity and the existing MFA policy;
2. local Change Policy requires an approved change record before production implementation.

v0.1 therefore failed the A001 >=90 Agent gate despite zero critical penalties.

## Agent v0.2 focused rerun

- Job: `a001-g36-ba-change-router-v02-skill-007`
- Execution: 2026-09-05 07:25:04–07:25:18 Australia/Sydney
- Total tokens: 4,253
- Score: **99/100**, zero critical penalties

Breakdown:

- A. Agent routing: 25/25
- B. Evidence/status preservation: 24/25
- C. Delivery/readiness discipline: 20/20
- D. ITIL alignment quality: 15/15
- E. Authority / invention discipline: 10/10
- F. Traceability / usability: 5/5

v0.2 preserves the exact six-Skill route and now explicitly carries both confirmed anchors: corporate identity/existing MFA and the source-backed approved-change-record production gate. It continues to preserve SAML/Entra as Candidate, 30 November and 45 minutes as non-binding Targets, the Saturday window as non-approved/proposed, contractor access as Disputed, the 17 accounts as Unknown, and SCIM as Deferred. It invents no CAB, Change Authority, architecture or implementation mechanism.

The single-point deduction is wording precision: one stop-rule sentence groups the date/window/recovery items under broad `Candidate/proposed mechanisms` language even though the items themselves are correctly named as targets/proposed and remain non-committed. This does not constitute status promotion and attracts no critical penalty.

## Decision

**A001 routing gate passed at v0.2.** Freeze v0.2 for the B023 composition experiment. Do not tune the routing prompt further from this benchmark. The next decision is architectural: compare the guarded control composition against the guarded ITIL composition and retain the extra ITIL stage only if it adds material value without evidence, authority or state regression.
