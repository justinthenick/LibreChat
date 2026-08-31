# Benchmark 001 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Factual completeness — 25 points

Award points for identifying the material business objective, stakeholders, requirements and constraints supported by the source pack.

- 5 — business objective accurately captured.
- 12 — explicit functional/business requirements substantially complete.
- 5 — constraints/security/auditability captured.
- 3 — tentative scope/performance items identified as tentative rather than firm.

Do not require exact wording or IDs from the gold standard.

## 2. Traceability — 20 points

- 15 — requirements/claims are consistently tied to Source A, B, C or D.
- 5 — evidence is specific enough that an evaluator can see why the item was derived.

Full marks require more than a generic statement that the answer is "based on the sources".

## 3. Ambiguity and contradiction handling — 20 points

- 10 — correctly identifies the blocking-vs-advisory disagreement and does not choose a side.
- 5 — correctly identifies the two-minute performance target as unproven/tentative.
- 5 — identifies other material ambiguity, including undefined critical checks and incomplete API feasibility.

## 4. Evidence classification / analytical discipline — 10 points

- 5 — clearly distinguishes explicit requirements from inferred/proposed items.
- 3 — labels assumptions rather than presenting them as fact.
- 2 — explicitly identifies unknowns / insufficient evidence where appropriate.

## 5. Open questions — 15 points

Award for useful, decision-oriented questions rather than volume.

- 5 — MVP scope/check catalogue/data-source questions.
- 5 — governance/business-rule questions around critical failures and blocking.
- 3 — security/integration/audit questions.
- 2 — performance/success criteria questions.

## 6. Structure and usability — 10 points

- 4 — clear sections/tables and stable IDs or equivalent structure.
- 3 — requirements are reasonably atomic and testable.
- 3 — concise enough to be usable by a BA/product/change team.

# Penalties

Apply after the 100-point score. Minimum final score is zero.

- **-10 each** — serious invented requirement, stakeholder, system or policy presented as fact.
- **-8 each** — converts a known stakeholder disagreement into a settled requirement without qualification.
- **-5 each** — invents exact technology/API/vendor details that are not in the source.
- **-5** — creates user stories/epics/estimates despite the explicit instruction not to do so in this stage.
- **-3 each** — meaningful inference presented as explicit fact rather than labelled inference/assumption.

# Interpretation

- **90-100:** excellent; suitable to proceed to decomposition with minor review.
- **80-89:** good; useful BA output with limited correction required.
- **70-79:** acceptable experiment; notable gaps remain.
- **50-69:** weak; significant BA review required.
- **Below 50:** unreliable for this workflow.

A response with a serious hallucination or an incorrectly resolved blocking decision should not be considered production-ready even if its numeric score remains high.

# Comparison rule

The purpose of the benchmark is comparative. Record both baseline and skill-assisted scores. A new skill version should normally be retained only when it improves total quality **and** does not increase serious hallucinations or contradiction errors.
