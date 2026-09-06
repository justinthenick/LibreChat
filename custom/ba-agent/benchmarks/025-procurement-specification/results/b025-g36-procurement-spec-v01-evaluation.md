# Benchmark 025 Evaluation — Procurement Specification v0.1

Evaluator-only record. Raw outputs remain unchanged.

## Run

- Model: `gemini-3.6-flash`
- Temperature: `0.0`
- Baseline: 2026-09-05 00:51:38–00:52:34 Australia/Sydney, 3,025 total tokens
- Skill v0.1 retry: 2026-09-05 07:26:20–07:26:41 Australia/Sydney, 5,270 total tokens

## Scores

### Baseline — 92/100, zero critical penalties

- A. Domain / objective: 10/10
- B. Hard-minimum discipline: 20/25
- C. Preference / Target / Unknown preservation: 30/30
- D. Scope / brand discipline: 15/15
- E. Handoff / verification evidence: 17/20

The baseline preserves 75-inch and wireless casting as Preferences, 4K and A$2,500 as Targets, VESA/final mount details as Unknown, and brand as open. Its main source-strength defect is treating built-in speakers as a mandatory hard minimum even though the packet says only that built-in speakers are acceptable and external audio is outside this procurement. It also provides less explicit market-expansion handoff structure than the Skill.

### `prepare-procurement-specification` v0.1 — 91/100, zero critical penalties

- A. Domain / objective: 10/10
- B. Hard-minimum discipline: 19/25
- C. Preference / Target / Unknown preservation: 30/30
- D. Scope / brand discipline: 15/15
- E. Handoff / verification evidence: 17/20

The Skill is substantially more traceable and gives an excellent downstream expansion/verification register, but it shows three reusable precision defects:

1. `Built-in speakers are acceptable` becomes a `Hard minimum` requiring internal speakers. Permission/acceptability is weaker than requirement.
2. `fit within a 1.85 m wall` becomes `strictly under 1.85 m`; the source establishes a fit boundary, not a new strict inequality/margin.
3. It adds unsupported dependency/verification detail: electrical/cable-pass-through infrastructure is assumed present, HDMI cable reach becomes a procurement eligibility question, and speaker wattage is requested despite no sourced wattage need.

These do not trigger critical penalties because the source does mention display audio and the Skill does not invent a prohibited standard/version/product, but they violate the core rule that procurement strength and evidence requests must not exceed source strength.

## Decision

Do **not** retain v0.1 for Architecture -> Procurement composition yet. Create one focused generic v0.2 correction that distinguishes `acceptable/permitted` from `required`, preserves supplied fit operators exactly unless a margin is sourced, and limits dependency/evidence questions to facts that can actually change eligibility under the supplied specification. Then run one same-model Skill-only rerun against this preserved baseline.
