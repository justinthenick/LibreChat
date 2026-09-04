# Benchmark 003 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Upstream fidelity and readiness — 20 points

- 5 — correctly assesses overall readiness as Partially Ready (or clearly equivalent).
- 10 — preserves Confirmed / Candidate / Target / Disputed / Deferred / Unknown status across the supplied requirements.
- 5 — does not silently add scope, personas, business rules or decision owners.

## 2. Work-item decomposition quality — 25 points

- 7 — creates coherent Epics / Capabilities without simply mirroring every requirement or inventing architecture layers.
- 8 — creates appropriate User Stories for supported user-observable behavior.
- 5 — uses Enabler / Technical Task for non-user technical/security/audit work where appropriate.
- 5 — does not force every requirement into a user story and keeps constraints/risks/dependencies distinct.

## 3. Traceability — 20 points

- 15 — delivery items consistently reference upstream REQ IDs.
- 5 — traceability summary or equivalent shows coverage of confirmed, blocked, candidate, target and deferred requirements.

Full marks require item-level traceability.

## 4. Uncertainty and blocker handling — 20 points

- 7 — REQ-004 privileged approval becomes a Decision Item; no side is selected; decision owner remains Unknown.
- 6 — REQ-006 automated provisioning feasibility becomes a Spike / Discovery Item or clearly equivalent conditional discovery work.
- 3 — REQ-009 pilot applications remain Candidate/conditional rather than committed implementation scope.
- 2 — REQ-011 retention remains Unknown/open; no duration invented.
- 2 — downstream blocked/conditional items identify the relevant decision/spike dependency.

## 5. Target / deferred discipline — 5 points

- 3 — REQ-008 four-business-hour item remains a Target, not a hard SLA/acceptance commitment.
- 2 — REQ-010 automatic deprovisioning remains Deferred and outside the current backlog.

## 6. Structure and downstream usability — 10 points

- 3 — clear sections and stable work-item IDs.
- 3 — backlog items are understandable and reasonably sliced without solution-design invention.
- 2 — dependencies/risks/candidate/deferred work are visibly separated.
- 2 — readiness for later acceptance-criteria elaboration is stated sensibly.

# Penalties

Apply after the 100-point score. Minimum final score is zero.

- **-12 each** — silently resolves REQ-004 privileged-access approval disagreement or presents one side as the settled implementation rule.
- **-10 each** — serious invented requirement, actor, governance policy or current-scope capability presented as fact.
- **-8** — treats REQ-006 automated provisioning as Ready/Confirmed implementation work despite unverified feasibility.
- **-8** — treats REQ-009 CRM / Reporting Portal / Dev Wiki as approved committed first-release scope.
- **-8** — pulls REQ-010 automatic deprovisioning into the current committed backlog.
- **-5 each** — invents a retention period, legal rule, vendor, API endpoint/protocol, architecture component or workflow technology.
- **-5** — converts the four-business-hour Target into a hard SLA or mandatory acceptance criterion.
- **-5** — creates story points, T-shirt sizes, time estimates, sprint assignments or delivery dates despite the instruction not to estimate.
- **-5** — creates detailed acceptance criteria / Given-When-Then behavior with unsupported UI, notification, validation or error-handling details.
- **-3 each** — meaningful upstream status is promoted or downgraded without evidence.
- **-3 each** — analyst-proposed staged-pilot mechanism is presented as an agreed mandatory delivery sequence.
- **-3 each** — a material delivery item lacks upstream REQ traceability.

# Interpretation

- **90-100:** excellent; strong delivery-decomposition discipline with clean blocker/status handling.
- **80-89:** good; useful backlog shaping with limited correction required.
- **70-79:** acceptable experiment; notable decomposition or uncertainty-handling gaps remain.
- **50-69:** weak; significant BA/product review required before backlog use.
- **Below 50:** unreliable for this workflow.

A response that silently resolves REQ-004, commits unverified automation, or materially invents scope should not be considered production-ready regardless of numeric score.

# Comparison rule

Benchmark 003 tests the new `decompose-requirements` capability.

For the first experiment:

1. Run the chosen model with the benchmark input and **no decomposition skill**.
2. Run the same model/settings/input with `$decompose-requirements` v0.1.
3. Score both independently.

The model under test must not see this rubric or `gold-standard.md`.

Retain the skill only if it improves decomposition quality without increasing scope invention, status promotion, blocker resolution or architecture/estimate hallucination.
