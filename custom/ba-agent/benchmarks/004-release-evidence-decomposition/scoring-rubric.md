# Benchmark 004 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Upstream fidelity and readiness — 20 points

- 5 — correctly assesses overall readiness as Partially Ready or clearly equivalent.
- 10 — preserves Confirmed / Candidate / Target / Disputed / Deferred / Unknown status across the supplied requirements.
- 5 — does not silently add scope, actors, approval rights, governance or business rules.

## 2. Work-item decomposition quality — 25 points

- 7 — creates coherent capabilities/epics without mirroring each requirement or inventing architecture layers.
- 8 — creates appropriate User Stories for supported user-observable behavior.
- 5 — uses Enabler / Technical Task for audit/security/traceability work where appropriate.
- 5 — keeps constraints, decisions, spikes, risks, candidate and deferred work distinct rather than forcing everything into stories.

## 3. Traceability — 20 points

- 15 — material delivery items consistently reference upstream REQ IDs.
- 5 — traceability summary or equivalent accounts for all requirements across current, blocked, candidate, target, deferred and unknown states.

## 4. Uncertainty and blocker handling — 20 points

- 7 — REQ-004 becomes a Decision Item; neither rollback position is selected; decision owner remains Unknown.
- 6 — REQ-006 becomes a Spike / Discovery Item or equivalent conditional feasibility work; downstream import remains Candidate/Conditional.
- 3 — REQ-008 pilot services remain Candidate/conditional rather than committed service-specific scope.
- 2 — REQ-010 retention remains Unknown/open with no invented duration or owner.
- 2 — downstream failed-validation/import work visibly identifies the relevant decision/spike dependency.

## 5. Target / deferred / process-boundary discipline — 5 points

- 2 — REQ-007 fifteen-minute objective remains a Target rather than hard SLA/acceptance commitment.
- 1 — REQ-009 predictive risk scoring remains Deferred/outside current backlog.
- 2 — REQ-012 remains a constraint; no CAB/change-approval redesign or new approval authority is invented.

## 6. Structure and downstream usability — 10 points

- 3 — clear sections and stable work-item IDs.
- 3 — items are understandable and reasonably sliced without solution-design invention.
- 2 — dependencies/risks/candidate/deferred work are visibly separated.
- 2 — readiness for later acceptance-criteria elaboration is stated sensibly.

# Penalties

Apply after the 100-point score. Minimum final score is zero.

- **-12 each** — silently resolves REQ-004 or presents automatic rollback / human decision as the settled implementation rule.
- **-10 each** — serious invented requirement, actor, governance authority, approval policy or current-scope capability presented as fact.
- **-8** — treats REQ-006 automated evidence import as Ready/Confirmed implementation work despite unverified feasibility.
- **-8** — treats Billing API / Customer Portal as approved committed first-release scope.
- **-8** — pulls REQ-009 predictive risk scoring into current committed work.
- **-5 each** — invents a retention period, regulation, vendor, API protocol/endpoint, webhook, queue, database/storage design, pipeline product, rollback technology or other architecture component.
- **-5** — converts the fifteen-minute Target into a hard SLA or mandatory acceptance criterion.
- **-5** — redesigns CAB/change approval or invents a new approval authority/process.
- **-5** — creates estimates, points, sprint assignments or delivery dates.
- **-5** — creates detailed unsupported acceptance criteria / Given-When-Then behavior with UI, notifications, validation/error states or rollback triggers.
- **-3 each** — meaningful upstream status promoted/downgraded without evidence.
- **-3 each** — analyst-proposed staged/proven-feasible mechanism treated as mandatory sequence.
- **-3 each** — material delivery item lacks upstream traceability.
- **-3 each** — references a non-existent work-item ID.

# Interpretation

- **90-100:** excellent; strong generalization and decomposition discipline.
- **80-89:** good; useful with limited correction.
- **70-79:** acceptable experiment; notable gaps remain.
- **50-69:** weak; significant BA/product review required.
- **Below 50:** unreliable for this workflow.

A response that silently resolves REQ-004, commits unverified evidence import, materially invents scope/architecture, or redesigns Change approval should not be considered production-ready regardless of numeric score.

# Comparison rule

Benchmark 004 is a generalization test for the already-tuned `decompose-requirements` v0.2 capability.

Run the same model/settings/input in baseline and skill modes. Do **not** tune the skill between the paired runs.

Retain v0.2 as generalized only if it materially improves decomposition quality without increasing invention, status promotion, decision resolution or Change-process redesign.
