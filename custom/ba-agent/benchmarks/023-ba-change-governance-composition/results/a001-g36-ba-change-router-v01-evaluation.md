# A001 Evaluation — BA Change Delivery Orchestrator v0.1

Evaluator-only record. Raw model outputs remain unchanged.

## Run

- Job: `a001-g36-ba-change-router-v01-ab-004`
- Model: `gemini-3.6-flash`
- Temperature: `0.0`
- Baseline: 2026-09-05 00:45:04–00:45:45 Australia/Sydney, 3,049 total tokens
- Agent v0.1: 2026-09-05 00:45:45–00:46:34 Australia/Sydney, 3,651 total tokens

## Scores

### Baseline — 91/100, zero critical penalties

- A. Agent routing: 25/25
- B. Evidence/status preservation: 22/25
- C. Delivery/readiness discipline: 15/20
- D. ITIL alignment quality: 15/15
- E. Authority / invention discipline: 10/10
- F. Traceability / usability: 4/5

The baseline selected and ordered all six required Skills correctly, preserved the main Candidate/Target/Deferred/Disputed/Unknown boundaries, and avoided governance/architecture invention. It did not clearly carry the explicit local-policy approved-change-record gate into the route, and the confirmed corporate-identity/MFA outcome was only implicit rather than clearly preserved as a source-backed constraint.

### BA Change Delivery Orchestrator v0.1 — 89/100, zero critical penalties

- A. Agent routing: 25/25
- B. Evidence/status preservation: 19/25
- C. Delivery/readiness discipline: 15/20
- D. ITIL alignment quality: 15/15
- E. Authority / invention discipline: 10/10
- F. Traceability / usability: 5/5

The Agent is excellent at routing and unresolved-state protection, but its safety emphasis is asymmetric: it explicitly preserves almost every non-committed state while failing to carry two source-backed confirmed constraints that materially govern downstream work:

1. workforce access must use corporate identity and the existing MFA policy;
2. local Change Policy requires an approved change record before production implementation.

This drops v0.1 below the A001 >=90 Agent gate despite zero critical penalties. The defect is reusable: an orchestrator must preserve confirmed source-backed constraints as actively as it preserves uncertainty.

## Decision

Do **not** release v0.1. The focused v0.2 correction already adds symmetric routing guardrails for confirmed outcomes and explicit local-policy gates without altering Skill selection/order. Run v0.2 Skill-only on Gemini 3.6 against this preserved same-model baseline. If it reaches >=90 with zero critical penalties and explicitly preserves both confirmed constraints, advance A001 to the controlled-composition gate.
