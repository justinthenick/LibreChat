# Benchmark 002 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Factual completeness — 25 points

Award points for identifying the material business objective, stakeholders, requirements and boundaries supported by the source pack.

- 5 — business problem/objective accurately captured.
- 9 — major functional/business requirements substantially complete.
- 6 — external-communication approval, security/privacy and no-process-redesign boundaries captured.
- 5 — candidate/target/deferred scope items identified without hardening them.

Do not require exact wording or IDs from the gold standard.

## 2. Traceability — 20 points

- 15 — requirements/claims are consistently tied to Source A, B, C or D (or equivalent source IDs).
- 5 — evidence/rationale is specific enough to understand why the item was derived.

Full marks require item-level traceability, not only a generic statement that the response is based on supplied sources.

## 3. Ambiguity and contradiction handling — 20 points

- 10 — correctly identifies the **internal auto-send versus Incident Manager confirmation** disagreement and does not choose a side.
- 4 — correctly identifies the five-minute expectation as a tentative target, not an SLA.
- 3 — identifies undefined **material status change** and/or lack of standard cadence.
- 3 — identifies incomplete API/permission/data-quality feasibility and/or severity/recipient/channel uncertainty.

## 4. Evidence/status analytical discipline — 15 points

- 5 — distinguishes Evidence class from Requirement status and uses both coherently.
- 3 — candidate Severity 1 scope / Agile delivery suggestion remain Candidate/Proposed rather than committed.
- 2 — eight-week and five-minute items remain Target.
- 2 — future multilingual/customer-segment ideas remain Deferred.
- 3 — assumptions, unknowns and unsupported authority are clearly labelled rather than presented as facts.

## 5. Open questions — 10 points

Award for useful, decision-oriented questions rather than volume.

- 3 — internal approval/auto-send and decision ownership.
- 2 — material status change / trigger/cadence / severity behavior.
- 2 — MVP scope, channels, recipients and message fields.
- 2 — API/data/security/privacy feasibility.
- 1 — measurable performance/success criteria or handling of unknown next-update time.

## 6. Structure and usability — 10 points

- 4 — clear source register/sections and stable requirement IDs or equivalent structure.
- 3 — requirements reasonably atomic and understandable.
- 3 — useful separation of requirements, ambiguities, assumptions, analyst proposals and not-established items.

# Penalties

Apply after the 100-point score. Minimum final score is zero.

- **-10 each** — serious invented requirement, stakeholder, system or policy presented as fact.
- **-10** — permits or requires unreviewed **external customer messages to be auto-sent**, contrary to explicit source evidence.
- **-8** — resolves the known internal auto-send versus Incident Manager confirmation disagreement as settled without qualification.
- **-5 each** — invents an unsupported decision owner/governance body and presents that authority as established.
- **-5 each** — invents exact technology, vendor, API endpoint, protocol or architecture as though sourced.
- **-3 each** — hardens a meaningful Candidate/Target/Deferred item into a Confirmed mandatory current requirement.
- **-3 each** — mistakes evidenced activity/responsibility for decision authority in a material way.
- **-3 each** — presents an analyst-suggested mechanism (e.g. workshop, spike, async/tiered model) as the required stakeholder outcome rather than a proposal.
- **-5** — creates user stories, epics, story points or effort estimates despite the explicit stage instruction.

# Interpretation

- **90-100:** excellent; strong evidence that the skill generalizes to a different IT service-management problem.
- **80-89:** good; useful BA output with limited correction required.
- **70-79:** acceptable experiment; notable gaps remain.
- **50-69:** weak; significant BA review required.
- **Below 50:** unreliable for this workflow.

A response that auto-sends external communications contrary to the source, incorrectly resolves the internal approval dispute, or contains a serious hallucination should not be considered production-ready even if its numeric score remains high.

# Comparison rule

Benchmark 002 primarily tests **generalization**, not further tuning to Benchmark 001.

For the first Benchmark 002 experiment:

1. Run a baseline with the chosen model and no skill.
2. Run the same model/settings/input with `$analyze-requirements` v0.4.
3. Score both independently.

Retain v0.4 only if it preserves the strong discipline demonstrated on Benchmark 001 and materially improves the new baseline without increasing serious hallucinations, invented authority, or contradiction errors.
