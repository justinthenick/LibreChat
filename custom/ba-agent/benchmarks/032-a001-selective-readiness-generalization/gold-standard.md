# Benchmark 032 gold standard — evaluator only

## Purpose

This benchmark tests whether A001 generalizes beyond the NimbusHR end-to-end case and can **avoid unnecessary Skills** when the input is already mature. The required behavior is selective orchestration, not maximal orchestration.

## Correct route

The minimum correct route is exactly:

1. `prepare-solution-change-readiness`
2. `assess-itil-alignment`

The Agent should not select:

- `analyze-requirements` — the packet is already a normalized BA baseline and the user explicitly says not to redo analysis.
- `decompose-requirements` — delivery decomposition is supplied and already agreed for this decision point.
- `elaborate-acceptance-criteria` — baselined acceptance criteria are supplied.
- `derive-test-cases` — executed test evidence is supplied; the user asked for readiness and ITIL alignment, not new test design.

Selecting one of those four upstream Skills is unnecessary work and weakens routing efficiency. Selecting all six repeats already-complete work and is a material orchestration defect, though it is only a critical defect if the repeated work also hardens or corrupts evidence/state.

## Required state preservation

The output route and downstream artifacts must preserve these distinctions:

- R-01 certificate-based authentication is **Confirmed**.
- 10 October 2026 is a **Target**, not an approved or committed implementation date.
- Existing MDM certificate-payload capability is **Confirmed**, while final rollout grouping is **Candidate**.
- Service-continuity outcome is Confirmed; fleet-wide rollback duration is **Unknown**.
- Gateway authentication-failure visibility is Confirmed; the >5 devices / 10 minutes threshold is **Candidate**.
- Sunday 02:00–04:00 is **Candidate / proposed**, not approved.
- CHG-04 is an explicit **local-policy gate** requiring an approved change record before production implementation.
- The Change Authority is **Unknown** from supplied evidence.
- There is no evidence that CAB attendance is universally mandatory.
- StockFlow support-lead availability does not make that person the Change Authority.

## Readiness findings expected

A strong readiness handoff should recognize that the solution is technically promising but not fully ready for production authorization because important evidence remains incomplete.

Expected positive evidence:

- 20-device pilot authentication PASS.
- Core receipt/pick/dispatch scanning PASS.
- reconnect PASS.
- authentication-failure visibility PASS.
- five-device rollback PASS.
- existing MDM deployment capability Confirmed.
- existing gateway monitoring capability Confirmed.

Expected gaps/blockers or conditions:

- final rollout grouping/sequence not approved.
- fleet-wide rollout/rollback timing not established; T-06 NOT RUN.
- proposed Sunday window not approved.
- alert threshold remains Candidate.
- approved production change record not evidenced.
- Change Authority remains Unknown.
- rollback decision criteria and measured full-fleet timing are incomplete.

The handoff may describe these as readiness gaps, conditions or decisions still required. It must not invent implementation mechanics, owners, approvals, timing values or thresholds.

## ITIL alignment expected

A strong ITIL assessment should use practice concepts as guidance without converting them into invented local policy. Relevant observations may include:

- Change Enablement: risk/evidence, authorization and scheduling are not yet complete; CHG-04 is the actual local gate.
- Deployment Management: staged rollout proposal exists but final grouping/sequence is unresolved.
- Service Validation and Testing: pilot evidence is strong for functional/authentication behavior, but full-fleet timing evidence is absent.
- Monitoring and Event Management: monitoring capability exists, but production alert threshold is not approved.
- Service Configuration Management / configuration information may be relevant only if grounded in supplied evidence; do not invent CMDB obligations.
- Incident/rollback preparedness can be discussed as readiness but must not invent a formal incident process or owner.

The assessor must not state that ITIL itself mandates CAB, a particular change classification, a named Change Authority, a specific approval workflow or a specific rollback threshold.

## Expected final artifact

The dynamic route should produce a traceable solution/change-readiness assessment followed by an ITIL 4 alignment assessment, with unresolved states and local-policy boundaries preserved.

## Efficiency expectation

The benchmark is intentionally designed so the correct dynamic route executes **two Skills, not six**. The generalization succeeds only if A001 demonstrates minimum-route discipline as well as semantic correctness.
