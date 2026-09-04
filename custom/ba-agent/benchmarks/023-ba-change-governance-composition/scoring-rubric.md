# Benchmark 023 — Scoring Rubric

Evaluator-only. Never send this file to the model under test.

Score out of 100 before critical penalties.

## A. Agent routing — 25 points

- 10: selects all six required Skills and no invented Skill.
- 8: orders them correctly from requirements -> decomposition -> criteria -> tests -> readiness -> ITIL.
- 4: explains prerequisite/stop discipline rather than treating every downstream artifact as automatically committed.
- 3: identifies the requested final artifact accurately.

## B. Evidence/status preservation — 25 points

- 5: corporate identity/MFA policy preserved as confirmed outcome without hardening SAML/Entra.
- 4: 30 November remains Target/desired timing.
- 4: 45-minute recovery remains Target/suggestion.
- 4: Saturday 22:00 remains proposed/unapproved.
- 4: contractor identity remains Disputed and Decision owner Unknown.
- 4: SCIM Phase 2 remains Deferred/out of current scope.

## C. Delivery/readiness discipline — 20 points

- 5: criteria/tests are committed only for sufficiently ready portions.
- 5: federation capability, 17 unmatched accounts and other unresolved items remain open/conditional.
- 5: approved change record is correctly identified as an explicit local-policy production gate.
- 5: missing evidence is surfaced without converting every gap into invented sign-off/pre-authorisation gates.

## D. ITIL alignment quality — 15 points

- 5: separates ITIL guidance from local policy and avoids formal-compliance claims.
- 5: uses relevant practice concepts without collapsing Change Enablement, Release, Deployment and Configuration Management into one process.
- 5: missing evidence is treated as not evidenced/clarification rather than automatically non-compliant.

## E. Authority / invention discipline — 10 points

- 5: no invented CAB, Change Authority, decision owner or approver.
- 5: no invented architecture, rollback mechanics, monitoring method, SLA or implementation mechanism.

## F. Traceability / usability — 5 points

- 5: handoffs remain reviewable and preserve enough IDs/status context for the downstream stage to understand what is confirmed versus unresolved.

## Critical penalties

Apply after raw score. Multiple penalties may apply.

- **-30**: promotes SAML/Entra or another mechanism into confirmed mandatory architecture.
- **-25**: invents CAB/Change Authority/decision owner/approval authority.
- **-25**: converts Candidate, Target, Disputed, Deferred or Unknown content into committed scope without source support.
- **-20**: presents ITIL guidance as universal mandatory local policy or formal compliance.
- **-20**: converts missing evidence categories into mandatory gates/sign-offs without explicit local-policy support.
- **-15**: resolves the contractor identity dispute or Standard-vs-Normal classification without evidence.
- **-10**: invents rollback mechanics, monitoring/validation method, test execution mechanism or unsupported architecture detail.
- **-10**: routing omits a Skill required by the explicit requested final outcome or adds an irrelevant/nonexistent Skill.

## Agent gate

A001 routing passes when:

- final score >= 90;
- zero critical penalties;
- exact required Skill sequence is preserved.

## Composition gate

The ITIL composition is preferred over the control only when:

- zero critical penalties;
- evidence/status/authority is no worse than the control;
- ITIL interpretation adds material useful information;
- the quality gain justifies the extra model call/token cost.

A tie or regression means retain the simpler control architecture.
