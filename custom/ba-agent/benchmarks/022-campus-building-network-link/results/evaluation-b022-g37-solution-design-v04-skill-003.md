# Benchmark 022 Evaluation — `design-technical-solution` v0.4.0

Job: `b022-g37-solution-design-v04-skill-003`  
Model: `gemini-3.7-flash`  
Temperature: `0.0`

## Score

| Category | Preserved baseline | Skill v0.4 |
|---|---:|---:|
| Outcome vs mechanism separation | 15/15 | 15/15 |
| Feasibility and evidence accuracy | 17/20 | 17/20 |
| Alternative topology quality | 22/25 | 23/25 |
| Compatibility and requirement-strength discipline | 11/15 | 11/15 |
| Unknowns and validation discipline | 14/15 | 13/15 |
| Handoff discipline | 9/10 | 9/10 |
| **Raw / Final** | **88/100** | **88/100** |
| Penalties | **0** | **0** |

Token usage: preserved baseline **5,661**; Skill v0.4 **6,036**.

## Evaluation

v0.4 preserves the intended connectivity outcome, keeps 1 Gbit/s at Target strength, rejects the 900 metre direct copper channel from the supplied 100 metre limit, and selects the correct passive optical path through the existing conduit. Exact fibre, termination and transceiver choices remain conditional on path and switch evidence. BA/service ownership receives the unresolved service-boundary and availability decisions, while Procurement receives candidate-verification work rather than makes or models. No rubric penalty applies.

The provenance correction improves the v0.3 result by five points. Electrical isolation now remains a Preference in the Procurement handoff, and the Layer-2/Layer-3 boundary is returned to BA rather than declared as a trunk requirement.

The generic requirement-strength defect is not closed. The evidence map converts “adding intermediate powered cabinets is not preferred” into “topology must be fully passive”, and the Procurement handoff declares `Midpoint Active Equipment — Hard minimum (Zero)`. The answer also invents approximately eight midpoint cabinets and specific mandrel, pull-line, attenuation-testing, compatibility-matrix, cable-diameter, pull-strength and tensile-limit validation methods. These are plausible engineering practices, but the evidence establishes the conditions to validate, not those exact methods. Describing the preferred option as a standard Layer-2 link also runs ahead of the explicitly unresolved logical service boundary.

## Decision

**Do not retain v0.4 for composition.** It ties the 88-point baseline, costs 375 additional tokens, and remains in the rubric's “useful, but a reusable compatibility or handoff defect remains” range.

Create one final generic correction rather than adding network-specific rules. Require a mandatory-word strength sweep across the architecture and Procurement handoff, make source status explicit in Procurement rows, and constrain validation actions to the missing evidence and affected decision rather than an unevidenced method. Run one focused Skill-only B022 rerun against the preserved Gemini 3.7 baseline.

If that correction does not clear the standalone gate, stop tuning B022 and redesign the Skill/output contract before any Solution Architect composition.

## Release waiver

On 2026-09-04 the user accepted the documented 88-point deficit for the current release. The subsequent v0.5 validation attempt returned `provider_busy` with no model output, so the untested v0.5 Skill revision is not included in the release.

Release `design-technical-solution` v0.4.0 with zero rubric penalties and the residual preference-to-hard-requirement/validation-method weakness recorded as technical debt. This waiver permits repository integration; it does not erase the deficit or constitute evidence that the untested v0.5 correction works.
