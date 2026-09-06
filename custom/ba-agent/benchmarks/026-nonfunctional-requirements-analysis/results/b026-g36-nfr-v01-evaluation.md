# Benchmark 026 Evaluation — Non-Functional Requirements Analysis v0.1

Evaluator-only record. Raw outputs remain unchanged.

## Run

- Model: `gemini-3.6-flash`
- Temperature: `0.0`
- Baseline: 2026-09-05 00:52:48–00:53:32 Australia/Sydney, 3,518 total tokens
- Skill v0.1 retry: 2026-09-05 07:26:47–07:27:11 Australia/Sydney, 5,938 total tokens

## Scores

### Baseline — 93/100, zero critical penalties

- A. Confirmed extraction: 25/25
- B. Target / Candidate / estimate discipline: 35/35
- C. Recovery / Unknowns: 15/15
- D. Solution-design handoff: 13/15
- E. Analysis quality: 5/10

The baseline classifies the supplied NFR evidence very well, including the 99.9% Target, 2,000-user estimate, encryption and WCAG Candidates, qualitative performance goal, same-day recovery discussion, and confirmed residency/support/fallback/claim-identification outcomes. The weakness is the handoff layer: it starts designing mechanisms (`provision data stores...`, availability messaging) and turns unresolved decisions into presumed approval/escalation workflows with inferred actors.

### `analyze-nonfunctional-requirements` v0.1 — 95/100, zero critical penalties

- A. Confirmed extraction: 25/25
- B. Target / Candidate / estimate discipline: 35/35
- C. Recovery / Unknowns: 15/15
- D. Solution-design handoff: 15/15
- E. Analysis quality: 5/10

The Skill is materially cleaner at protecting Targets/Candidates/estimates in the architecture handoff and introduces no prohibited numeric thresholds or architecture mechanisms. However, its conflicts section violates its own authority rule by inventing `Decision owner` values from stakeholder/group context: `Steering Group`, `Business / Operations Leadership`, `Security Governance / Policy Owner`, and `Business Continuity / Risk Owner` are not evidenced as decision authorities. It also risks turning the confirmed Service Desk coverage window into a technical/tooling boundary (`operational tooling need only align`) rather than preserving it as a support-process fact.

No critical penalty is applied: the output does not create an approved SLA, mandatory Candidate, regulatory obligation, numeric RTO/RPO, or prohibited architecture technology. But authority inference is unsafe for downstream Agent composition and must be corrected before release.

## Decision

Create one focused generic v0.2 correction that:

- treats source/proposer/reviewer/group participation as distinct from decision authority and emits exact `Decision owner: Unknown` unless explicit authority evidence exists;
- preserves support-process coverage separately from technical service availability/runtime/tooling requirements;
- keeps confirmed operational fallback outcomes as outcomes rather than inventing implementation/UX mechanisms.

Then run one same-model Skill-only rerun against the preserved baseline. If clean, move to a materially different NFR generalization benchmark before Solution Architecture composition.
