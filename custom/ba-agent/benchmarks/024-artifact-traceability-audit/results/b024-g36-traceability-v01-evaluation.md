# Benchmark 024 Evaluation — Artifact Traceability Audit v0.1

Evaluator-only record. Raw model outputs remain unchanged.

## Run

- Benchmark: B024 Artifact Traceability Audit
- Model: `gemini-3.6-flash`
- Temperature: `0.0`
- Baseline: 2026-09-05 00:50:13–00:51:09 Australia/Sydney, 6,218 total tokens
- Skill v0.1 retry: 2026-09-05 07:25:33–07:26:14 Australia/Sydney, 9,410 total tokens

## Scores

### Baseline — 94/100, zero critical penalties

- A. Reference integrity: 20/20
- B. Status / requirement-strength integrity: 25/25
- C. Authority / governance integrity: 20/20
- D. Constraint / semantic coverage: 15/15
- E. Audit quality / discipline: 14/20

The baseline catches every material ground-truth defect, including AC-99 phantom lineage, REQ-02 Candidate hardening, REQ-03 Target hardening, DEC-01/Maya authority invention, CAB invention, CON-01 loss, REQ-04 deferred-lineage loss, and T-04 immutable-log invention. It also distinguishes WI-05's legitimate blocked state from the later unsupported authority assignment.

Its main weakness is audit authority/discipline: `REJECT / NON-COMPLIANT` and `Deployment cannot proceed` overstate what the supplied audit evidence authorizes, and several questions presume approval/governance mechanics rather than simply identifying missing evidence.

### `audit-artifact-traceability` v0.1 — 89/100, zero critical penalties

- A. Reference integrity: 18/20
- B. Status / requirement-strength integrity: 22/25
- C. Authority / governance integrity: 20/20
- D. Constraint / semantic coverage: 15/15
- E. Audit quality / discipline: 14/20

The Skill is strong on the core high-risk failures and does not accept invented Maya/Security/CAB authority. It correctly identifies the AC-99 phantom before suggesting any possible correction, so no phantom-reference penalty applies.

Two reusable defects prevent retention:

1. **Deferred lineage vs execution is conflated.** REQ-04 is called `Legitimately Blocked / COMPLIANT` because current delivery work is not required. The correct distinction is that Deferred scope need not have committed current AC/tests, but its Deferred/out-of-current-scope lineage should remain visible rather than silently disappear.
2. **Audit turns into remediation.** Repeated `Required Semantic Correction` sections prescribe exact downstream edits, including AC-99 -> AC-03 and decomposing CON-01 into a Work Item, Acceptance Criteria, Test Validation and Readiness Criteria. The audit evidence establishes the integrity state that must be restored, not a unique artifact rewrite. The final authority question also introduces `Change Authority` wording even though the supplied evidence only establishes that decision authority/ownership is Unknown.

These defects are material but do not meet a critical-penalty threshold in this run: the Skill identifies the actual defects before discussing correction and does not invent a substantive product requirement or established governance authority.

## Decision

Do **not** retain v0.1 for composition. Create one focused generic v0.2 correction that:

- separates `execution eligibility` from `lineage visibility` for Deferred/Blocked/Candidate/Unknown items;
- reports the minimum semantic integrity condition rather than prescribing the remediation artifact structure;
- leaves phantom references unresolved unless evidence uniquely identifies the intended reference;
- avoids formal compliance/release/deployment verdicts and invented governance wording.

Then run a Gemini 3.6 Skill-only B024 rerun against the preserved baseline. If v0.2 reaches >=90 with zero critical penalties and removes these defects, move to a materially different generalization benchmark before using it as a cross-workflow assurance gate.
