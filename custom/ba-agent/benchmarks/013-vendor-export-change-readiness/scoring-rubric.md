# Benchmark 013 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Overall readiness judgment — 15
- 8 — correctly identifies Partially ready for solution/design handoff.
- 7 — correctly states Change submission/production readiness is not yet established.

## 2. Evidence-package fidelity — 20
- 8 — accurately carries confirmed export content, access-control, audit and manual-fallback scope.
- 4 — treats the draft field mapping as useful evidence but not approved interface design.
- 4 — distinguishes test design from executed evidence.
- 4 — maintains traceability to supplied IDs.

## 3. Unresolved/non-committed discipline — 20
- 5 — SFTP remains Candidate and vendor capability does not become internal design approval.
- 5 — tokenisation remains Disputed with Decision Owner Unknown and both positions preserved.
- 3 — 15-minute objective remains Target/non-binding.
- 3 — scheduled recurring export remains Deferred.
- 2 — generated-file retention remains Unknown.
- 2 — MFT-gateway reuse remains unverified discovery, not selected design.

## 4. Solution/design handoff quality — 15
- 8 — clearly states what downstream solution/design review must establish without designing it.
- 4 — preserves Finance access-control and security/data-handling constraints.
- 3 — technical/vendor/discovery questions are explicit and traceable.

## 5. Change-readiness evidence matrix — 20
- 10 — correctly classifies supplied vs missing evidence, including field mapping and unexecuted tests.
- 5 — approved interface/design, deployment/backout/test-execution/validation evidence remain Missing rather than invented.
- 5 — Change/CAB approval, dates, risk rating, support/communications remain Missing/Partial as supported and are not promoted into unsourced mandatory governance gates.

## 6. Usability and traceability — 10
- 5 — clear blocking decisions/dependencies and next review state.
- 5 — concise, reviewable, no phantom IDs or contradictions.

# Penalties

Minimum final score zero.

- **-15 each** — resolves tokenisation dispute; selects SFTP/MFT/another transfer mechanism as committed solution.
- **-10 each** — invents decision owner, Change approver, CAB authority, serious governance role or claims approval/submission not supplied.
- **-10** — claims tests were executed/passed or claims production readiness from test designs alone.
- **-8 each** — invents interface/implementation architecture, endpoint, authentication, encryption/protocol detail, storage/database/API/scheduler/vendor-onboarding mechanism.
- **-8 each** — invents deployment, rollback/backout or production-validation mechanism.
- **-5 each** — invents release/maintenance date/window, risk rating, communications channel/plan, support-transition mechanism, retention rule/duration or data-handling rule.
- **-5** — turns the 15-minute Target into binding SLA/gate.
- **-5** — brings Deferred scheduled exports into current handoff.
- **-5 each** — promotes a missing downstream evidence category into a mandatory approval/sign-off/CAB/governance gate without explicit source support.
- **-3 each** — treats the draft field mapping as approved design, material traceability omission, phantom ID or contradiction.

# Interpretation

- **90-100:** excellent controlled handoff/generalization.
- **80-89:** good, limited correction.
- **70-79:** useful experiment with material gaps.
- **50-69:** weak; downstream assumptions unsafe.
- **Below 50:** unreliable.

Regardless of score, an output is not production-ready if it invents architecture/Change authority, resolves the tokenisation dispute, selects Candidate transfer technology, promotes unsourced governance gates or claims unexecuted tests passed.

# Comparison rule

Run Gemini 3.5 Flash at temperature 0.0 in paired baseline and skill modes using identical source/prompt. If `prepare-solution-change-readiness` v0.2 materially improves evidence-vs-gap separation and avoids solution/governance invention on this materially different scenario, treat v0.2 as generalized enough for later composition testing with the frozen BA workflow.
