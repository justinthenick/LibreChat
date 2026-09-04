# Benchmark 009 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Requirements-analysis fidelity — 20 points

- 5 — overall readiness correctly identified as Partially Ready or equivalent.
- 10 — requirements and constraints preserve Confirmed / Disputed / Candidate / Target / Deferred / Unknown states from the source.
- 5 — emergency-approval decision ownership remains Unknown and source/proposer is not treated as authority.

## 2. Delivery decomposition and Stage 1 -> 2 handoff — 20 points

- 6 — coherent capabilities/epics without mirroring every requirement into pseudo-architecture.
- 7 — appropriate stories/enablers/tasks for confirmed current work.
- 5 — emergency approval becomes Decision Item and Service Registry automation becomes Spike/Discovery plus conditional Candidate work.
- 2 — Target/Candidate/Deferred/Unknown/constraints remain clearly separated.

## 3. Acceptance-criteria discipline and Stage 2 -> 3 handoff — 15 points

- 8 — Ready criteria cover request data, normal approval boundary, evidence, manual fallback, imported-update traceability and applicable constraints without unsupported mechanisms.
- 4 — no committed criteria for disputed emergency approval, Candidate Service Registry automation/pilot, Deferred recertification or Unknown retention; Target remains non-binding.
- 3 — criteria trace to delivery items and REQ/CON IDs; derived negative boundary is labelled where used.

## 4. Test / assurance derivation and Stage 3 -> 4 handoff — 15 points

- 8 — behavioural tests cover material Ready criteria without inventing execution mechanics or concrete data.
- 4 — conditional integration/security/process constraints are assurance states rather than committed Candidate functionality.
- 3 — every material committed test traces through AC and delivery item to REQ/CON ID(s).

## 5. Cross-stage traceability and consistency — 15 points

- 6 — stable IDs and material end-to-end traceability.
- 5 — no status drift or contradiction across stages.
- 2 — explicit handoffs make Ready vs non-ready scope reviewable.
- 2 — no phantom IDs/references.

## 6. No-invention / process-boundary discipline — 10 points

- 4 — no unsupported UI, notification, field/date/team validation, error behavior, escalation, retry/timeout or workflow behavior.
- 3 — no unsupported API/protocol/payload/storage/queue/integration architecture or test-execution mechanism.
- 3 — service-ownership governance, HR organisation, application lifecycle and Change approval boundaries remain preserved without redesign or new authority.

## 7. End-to-end usability and efficiency — 5 points

- 2 — four stages are clearly separated and reviewable.
- 2 — final traceability/coverage summary is useful.
- 1 — avoids unnecessary duplication while preserving auditability.

# Penalties

Apply after the 100-point score. Minimum final score is zero.

- **-15 each** — silently resolves the emergency-approval dispute or creates committed emergency behavior selecting Major Incident Manager approval or Application Owner/delegate approval.
- **-10 each** — invents a decision owner/approval authority/governance role, serious current-scope actor, capability or business rule.
- **-8** — treats Service Registry automation as Ready/Confirmed committed build work or committed functional testing.
- **-8** — treats Finance Applications / Network Tools as approved committed pilot scope.
- **-8** — brings quarterly automated ownership recertification into current backlog/criteria/tests.
- **-5** — turns the one-business-day Target into a binding SLA, mandatory AC or pass/fail release/test gate.
- **-5 each** — invents retention duration/regulation/owner, a temporary no-delete/no-purge rule, ownership-team naming rule, effective-date validation, completeness/rejection behavior, notification/escalation or other unsupported behavior.
- **-5 each** — invents Service Registry API protocol/endpoint/payload, webhook, queue, database/storage design, workflow engine or integration architecture.
- **-5** — redesigns service-ownership governance, HR organisation, application lifecycle or Change approval, or invents new authority/process.
- **-5** — creates estimates, points, sprint assignments, delivery/test dates or test-automation implementation.
- **-5** — invents concrete test data, environment/account names, UI click paths, mocks/stubs or test tooling.
- **-3 each** — material status/readiness drift between stages without source evidence.
- **-3 each** — material downstream item lacks required traceability.
- **-3 each** — references a non-existent REQ/CON/work-item/AC/test ID.

# Interpretation

- **90-100:** excellent end-to-end BA behavior.
- **80-89:** good; useful with limited correction.
- **70-79:** acceptable experiment; material gaps remain.
- **50-69:** weak; cross-stage review required.
- **Below 50:** unreliable.

Regardless of score, an answer is not production-ready if it resolves the emergency-approval dispute, commits Candidate Service Registry automation, invents material authority/architecture, or loses cross-stage status/traceability.

# Comparison rule

Run the same model/settings/source packet in:

1. baseline mode — end-to-end prompt only;
2. agent mode — same prompt/source plus Composite BA Delivery Analyst v0.2.

Do not modify the agent between paired runs.

Benchmark 009 is a generalization test. If composite v0.2 remains strong without material invention/status drift and materially outperforms or disciplines the baseline, retain v0.2 as the preferred BA architecture and stop tuning it against Benchmarks 008/009.
