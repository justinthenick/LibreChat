# Benchmark 027 Evaluation — Change Impact Assessment v0.1

Evaluator-only record. Raw model outputs remain unchanged.

## Run

- Job: `b027-g36-change-impact-v01-ab-001`
- Model: `gemini-3.6-flash`
- Temperature: `0.0`
- Baseline: 2026-09-05 00:54:19–00:55:22 Australia/Sydney, 3,129 total tokens
- Skill v0.1: 2026-09-05 00:55:22–00:57:08 Australia/Sydney, 6,424 total tokens

## Scores

### Baseline — 98/100, zero critical penalties

- A. Confirmed direct impacts: 30/30
- B. Candidate / Unknown discipline: 20/20
- C. Non-impact / exclusion discipline: 20/20
- D. Governance / planning-state integrity: 15/15
- E. Risks and handoff quality: 13/15

The baseline correctly preserved the mobile dependency as unverified, OIDC fallback as unresolved, reporting identifier mapping as undecided, payroll/API non-impacts, contractor deferral, Security authority uncertainty, unsupported CAB wording, and the implementation window as an unapproved planning target.

The only meaningful weakness is in the readiness handoff: `Formalize implementation window approvals` subtly turns an unapproved planning target into a presumed approval workflow. The output otherwise states the target correctly and does not invent a mandatory gate, so no critical penalty is applied.

### `assess-change-impact` v0.1 — 97/100, zero critical penalties

- A. Confirmed direct impacts: 30/30
- B. Candidate / Unknown discipline: 20/20
- C. Non-impact / exclusion discipline: 20/20
- D. Governance / planning-state integrity: 15/15
- E. Risks and handoff quality: 12/15

The Skill correctly preserves all scored source states and governance boundaries. It is more structured and traceable than the baseline, but two reusable semantic defects prevent retention:

1. It places wholly unreferenced infrastructure/security domains under `Explicit non-impacts / exclusions` and says they are `marked as not impacted/out of scope`. Absence of evidence cannot establish non-impact or exclusion.
2. Its handoff says to `Obtain formal approval for the target implementation window`. The source establishes only an unapproved planning target, not an approval obligation or approval mechanism.

Neither defect crosses a rubric critical-penalty threshold in this run, but both are unsafe for downstream Change Readiness composition.

## Decision

Do **not** retain v0.1 for composition yet. Create one focused generic v0.2 correction that:

- makes `absence of evidence is not evidence of non-impact` explicit;
- restricts `Not impacted / excluded` to source-established states;
- prevents unapproved planning Targets or suggested governance involvement from becoming approval/sign-off tasks.

Then run one Gemini 3.6 Skill-only rerun against the preserved same-model baseline. If v0.2 reaches >=90 with zero critical penalties and removes these reusable defects, retain it for a materially different generalization benchmark before Agent composition.
