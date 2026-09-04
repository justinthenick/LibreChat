# Benchmark 008 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Requirements-analysis fidelity — 20 points

- 5 — overall readiness correctly identified as Partially Ready or equivalent.
- 10 — requirement set/statuses preserve Confirmed / Disputed / Candidate / Target / Deferred / Unknown / constraints as represented in the source.
- 5 — evidence/decision ownership is handled correctly; REQ-003 owner remains Unknown and stakeholder activity is not treated as authority.

## 2. Delivery decomposition and Stage 1 -> 2 handoff — 20 points

- 6 — coherent capabilities/epics without mirroring each REQ or inventing architecture layers.
- 7 — appropriate stories/enablers for confirmed current work.
- 5 — disputed after-hours rule becomes Decision Item and candidate automation becomes Spike/Discovery + conditional work.
- 2 — Target/Candidate/Deferred/Unknown/constraints remain clearly separated.

## 3. Acceptance-criteria discipline and Stage 2 -> 3 handoff — 15 points

- 8 — Ready criteria cover request data, normal-hours approval boundary, evidence, manual fallback and conditional security/process constraints without unsupported mechanics.
- 4 — no committed criteria for disputed after-hours approval, Candidate automation/pilot, Deferred revocation or Unknown retention.
- 3 — criteria trace to work-item and REQ IDs; derived negative boundary is labelled where used.

## 4. Test / assurance derivation and Stage 3 -> 4 handoff — 15 points

- 8 — committed behavioural tests cover all material Ready criteria without inventing execution mechanics or concrete data.
- 4 — conditional constraints are assurance states rather than committed Candidate functionality.
- 3 — every material committed test traces through AC ID and delivery item to REQ ID(s).

## 5. Cross-stage traceability and consistency — 15 points

- 6 — IDs remain stable and material downstream artifacts trace end-to-end.
- 5 — no status drift or contradiction across stages.
- 2 — explicit stage handoffs make Ready vs non-ready scope reviewable.
- 2 — no phantom IDs/references.

## 6. No-invention / process-boundary discipline — 10 points

- 4 — no unsupported UI, notification, validation/error, file/card/badge format, retry/timeout or workflow behavior.
- 3 — no unsupported API/protocol/storage/queue/vendor/integration architecture or test execution mechanism.
- 3 — contractor onboarding, security vetting, building-owner approval and Change approval boundaries are preserved without redesign or new authority.

## 7. End-to-end usability and efficiency — 5 points

- 2 — four stages are clearly separated and compact enough for review.
- 2 — final traceability/coverage summary is useful.
- 1 — output avoids unnecessary duplication while preserving auditability.

# Penalties

Apply after the 100-point score. Minimum final score is zero.

- **-15 each** — silently resolves the after-hours approval dispute or creates committed downstream behavior selecting Site Access on-call approval or Security approval.
- **-10 each** — invents a decision owner/approval authority/governance role or serious current-scope capability/business rule.
- **-8** — treats Building Access Platform automation as Ready/Confirmed committed build work or committed functional testing.
- **-8** — treats Sydney Metro / Newcastle as approved committed pilot scope.
- **-8** — pulls automatic revocation into current backlog/criteria/tests.
- **-5** — turns the two-business-hour Target into a binding SLA, mandatory AC or pass/fail release/test gate.
- **-5 each** — invents retention duration/regulation/owner, normal-hours definition, field/time format, validation/error behavior, notification channel/template, temporary badge/card format, retry/timeout or other unsupported behavior.
- **-5 each** — invents API protocol/endpoint/payload, webhook, queue, database/storage design, workflow engine or Building Access Platform architecture.
- **-5** — redesigns contractor onboarding, security vetting, building-owner approval or Change approval, or invents new approval authority/process.
- **-5** — creates estimates, points, sprint assignments, dates or test-automation implementation.
- **-5** — invents concrete test data, environment/account names, UI click paths, mocks/stubs or test tooling.
- **-3 each** — material status/readiness drift between stages without source evidence.
- **-3 each** — material downstream item lacks required traceability.
- **-3 each** — references a non-existent REQ/work-item/AC/test ID.

# Interpretation

- **90-100:** excellent end-to-end BA agent behavior.
- **80-89:** good; useful with limited correction.
- **70-79:** acceptable experiment; material gaps remain.
- **50-69:** weak; cross-stage review required.
- **Below 50:** unreliable.

Regardless of score, an answer is not production-ready if it silently resolves REQ-003, commits Candidate automation, materially invents architecture/process authority, or loses cross-stage status/traceability.

# Comparison rule

Run the same Gemini model/settings/source packet in:

1. baseline mode — end-to-end prompt only;
2. agent mode — same prompt/source plus `BA Delivery Analyst` v0.1 as the injected system instruction.

Do not modify the agent between paired runs.

The composite agent demonstrates value only if it improves or preserves end-to-end quality **without** increasing status drift, contradictions, invention or traceability loss. Consider token usage/cost as a secondary architectural metric, not a substitute for quality.
