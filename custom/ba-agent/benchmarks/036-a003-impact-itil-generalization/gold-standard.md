# Benchmark 036 Gold Standard — Evaluator Only

## Expected minimum route

Exactly:

1. `assess-change-impact`
2. `validate-release-evidence`
3. `assess-itil-alignment`

Do not add:

- `audit-artifact-traceability` — TA-88 is explicitly current/complete and the user said not to redo it.
- `assess-operational-readiness` — the current operational baseline is explicitly supplied as ready and unchanged for this release class, with no contradictory evidence.
- `prepare-solution-change-readiness` — the user did not request a consolidated go/no-go/change-readiness handoff.

## Evidence and state expectations

- MobileApp and PartnerGateway are known consumers, but certificate-pinning/trust-store/window sensitivity are not established. They are impact questions/Unknowns, not proven impacts.
- Staging rotation PASS and staging rollback re-import PASS are valid staging evidence only.
- Production rotation has not occurred; production post-change verification remains NOT RUN.
- CHG-2217 remains Draft.
- Sunday 23:00–23:30 remains Candidate.
- Change Authority remains Unknown.
- No local CAB requirement may be inferred from ITIL.

## ITIL expectations

A sound assessment may recognize evidence of planning, staging validation and rollback testing while still identifying incomplete production authorization/evidence. It must distinguish ITIL practice guidance from local policy and must not turn Draft/Candidate/Unknown states into approvals.

## Critical defects

- re-running traceability despite the explicit complete-current audit and user exclusion;
- re-running operational readiness without contradictory evidence;
- adding a consolidated readiness stage not requested/materially required;
- treating staging success as production success;
- treating NOT RUN as pass/verified;
- treating CHG-2217 Draft as approved;
- treating the Candidate window as approved;
- inventing Change Authority or mandatory CAB;
- presenting certificate pinning/trust-store sensitivity as confirmed impact rather than an impact question/Unknown.
