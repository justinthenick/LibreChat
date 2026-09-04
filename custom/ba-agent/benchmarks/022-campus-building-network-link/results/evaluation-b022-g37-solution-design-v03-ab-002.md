# Benchmark 022 Evaluation — `design-technical-solution` v0.3.0

Job: `b022-g37-solution-design-v03-ab-002`  
Model: `gemini-3.7-flash`  
Temperature: `0.0`

## Score

| Category | Baseline | Skill v0.3 |
|---|---:|---:|
| Outcome vs mechanism separation | 15/15 | 15/15 |
| Feasibility and evidence accuracy | 17/20 | 17/20 |
| Alternative topology quality | 22/25 | 22/25 |
| Compatibility and requirement-strength discipline | 11/15 | 7/15 |
| Unknowns and validation discipline | 14/15 | 14/15 |
| Handoff discipline | 9/10 | 8/10 |
| **Raw / Final** | **88/100** | **83/100** |
| Penalties | **0** | **0** |

Token usage: baseline **5,661**; Skill v0.3 **5,904**.

## Evaluation

Both runs solve the central problem correctly. They preserve private, maintainable inter-building connectivity, keep 1 Gbit/s as a Target, reject the 900 metre direct copper mechanism using the supplied 100 metre limit, and select a passive optical path through the existing conduit. Both keep exact switch/module compatibility unresolved, expose service-boundary and availability questions, and separate BA/service-owner questions from Procurement verification. Neither recommends a make/model or triggers a rubric penalty.

The baseline nevertheless introduces unsupported precision: it says the 900 metre run exceeds the limit by `900%` rather than 800%, asserts complete link loss after the standards-compliance blocker is already sufficient, prescribes repeaters at sub-100-metre intervals, and carries survey/installation techniques into the handoff without source evidence. It also promotes the electrical-isolation preference into an all-dielectric cable requirement.

The Skill repeats those issues and strengthens the reusable requirement-promotion defect. It turns “no intermediate cabinets are preferred” into a hard passive-span constraint and turns electrical isolation from a preference into a Procurement hard minimum. It prescribes underground cable construction, moisture resistance, tensile strength, optical-loss testing methods and Layer-2 trunk/STP ownership before those choices are established. The logical boundary was explicitly Unknown, yet the preferred topology describes the link as a Layer-2 trunk/uplink.

These details do not invalidate the optical architecture, but they violate the Skill’s own evidence and requirement-strength controls. The Skill scores five points below the baseline and uses more tokens.

## Decision

**Do not retain v0.3 for composition.** B022 confirms that the residual B019 issue is not merely a Synology/hardware-model tendency: the generic Skill still permits preferences and plausible implementation details to become architecture or Procurement requirements.

Reopen the generic evidence gate rather than adding network-specific rules. The next version should require a final provenance pass across constraints and handoff rows, prevent `Preference` or `Unknown` facts from becoming hard constraints, keep physical-path architecture separate from unresolved Layer-2/Layer-3 service design, and avoid prescribing validation methods when only the validation condition is evidenced.

After that focused generic correction, rerun only the Skill side of B022 against this same Gemini 3.7 baseline. Do not begin Solution Architect composition until the corrected Skill clears this third-domain gate without penalties and without requirement-strength promotion.
