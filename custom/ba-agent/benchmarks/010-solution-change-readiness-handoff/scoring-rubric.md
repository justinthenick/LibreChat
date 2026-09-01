# Benchmark 010 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Overall readiness judgment — 15
- 8 — correctly identifies Partially ready for solution/design handoff.
- 7 — correctly states Change submission/production readiness is not yet established.

## 2. Evidence-package fidelity — 20
- 10 — accurately carries confirmed scope, ACs and constraints.
- 5 — distinguishes test design from executed evidence.
- 5 — maintains traceability to supplied IDs.

## 3. Unresolved/non-committed discipline — 20
- 5 — SMS remains Candidate.
- 5 — session invalidation remains Disputed with Decision Owner Unknown.
- 3 — two-minute objective remains Target/non-binding.
- 3 — mobile reset remains Deferred.
- 2 — retention remains Unknown.
- 2 — reuse of existing reset service remains unverified discovery, not selected design.

## 4. Solution/design handoff quality — 15
- 8 — clearly states what downstream solution/design review must establish without designing it.
- 4 — preserves identity-verification, security and Service Desk constraints.
- 3 — technical discovery/questions are explicit and traceable.

## 5. Change-readiness evidence matrix — 20
- 10 — correctly classifies supplied vs missing evidence.
- 5 — implementation/deployment/backout/test-execution evidence remain Missing rather than invented.
- 5 — CAB/Change approval, dates, risk rating, support/communications remain Missing/Partial as supported.

## 6. Usability and traceability — 10
- 5 — clear blocking decisions/dependencies and next review state.
- 5 — concise, reviewable, no phantom IDs.

# Penalties

Minimum final score zero.

- **-15 each** — resolves session-invalidation dispute or selects SMS/another verification channel as committed solution.
- **-10 each** — invents decision owner, Change approver, CAB authority, serious governance role or claims approval/submission not supplied.
- **-10** — claims tests were executed/passed or claims production readiness from test designs alone.
- **-8 each** — invents implementation architecture/service/API/protocol/database/hosting/integration mechanism.
- **-8 each** — invents deployment, rollback/backout or production-validation mechanism.
- **-5 each** — invents release/maintenance date/window, risk rating, communications channel/plan, support-transition mechanism, retention rule/duration, or session behavior.
- **-5** — turns two-minute Target into binding SLA/gate.
- **-5** — brings Deferred mobile reset into current handoff.
- **-3 each** — material traceability omission or phantom ID.

# Interpretation

- **90-100:** excellent controlled handoff.
- **80-89:** good, limited correction.
- **70-79:** useful experiment with material gaps.
- **50-69:** weak; downstream assumptions unsafe.
- **Below 50:** unreliable.

Regardless of score, an output is not production-ready if it invents architecture/Change authority, resolves the dispute, selects Candidate SMS, or claims unexecuted tests passed.

# Comparison rule

Run Gemini 3.5 Flash at temperature 0.0 in paired baseline and skill modes using identical source/prompt. If v0.1 materially improves evidence-vs-gap separation and avoids invented solution/Change mechanics, retain it and generalize on a materially different handoff benchmark before composing it into the frozen BA Delivery Analyst.