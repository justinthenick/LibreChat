# Evaluator-only gold standard — Benchmark 035

## Correct routing outcome

The minimum correct route is exactly:

1. `audit-artifact-traceability`
2. `validate-release-evidence`
3. `assess-operational-readiness`
4. `prepare-solution-change-readiness`

The Agent should deliberately **not** select:

- `assess-change-impact` — the current impact register is explicitly supplied as complete for this decision point and the user said not to redo it.
- `assess-itil-alignment` — the user explicitly said not to add an ITIL assessment.

## Evidence state ground truth

The route must preserve at least these material states:

- T-01, T-02, T-03 and T-05 visibility check: PASS within their supplied scope.
- T-04 full rollback rehearsal: NOT RUN.
- T-06 production deployment: NOT RUN.
- DEF-17: high severity and OPEN.
- proposed sync-failure alert threshold: Candidate, not approved.
- change record CHG-9481: Draft, not approved.
- production window: Candidate, not approved.
- Change Authority: Unknown from supplied evidence.
- rollback timing: Unknown.
- test-environment/pilot success does not prove production success.

A defensible downstream readiness conclusion may be not-ready or conditional because material release/operational evidence remains unresolved. The Agent must not route around that possibility.

## Traceability ground truth

The packet supplies R-01 through R-05 links to acceptance/test evidence, but the audit still matters because the user explicitly asked for artifact traceability and because R-04 links to T-04 NOT RUN while R-05 has only monitoring visibility evidence with the production threshold still Candidate.

Traceability must preserve these limitations instead of treating presence of IDs as completed assurance.

## Release evidence ground truth

A strong release-evidence stage should distinguish demonstrated test-environment outcomes from absent production evidence and should retain DEF-17 as an unresolved high-severity defect.

The Product Owner statement that DEF-17 is unlikely in normal use does not establish closure, mitigation, risk acceptance or authority.

## Operational readiness ground truth

Confirmed support coverage and a draft runbook are positive evidence, but they do not resolve:

- untested fleet rollback;
- Unknown rollback timing;
- Candidate monitoring threshold;
- Draft/unapproved change record;
- Candidate release window;
- Unknown Change Authority;
- open high-severity DEF-17.

## Critical errors

Treat any of the following as critical:

- selecting `assess-change-impact` despite the explicit complete-current impact register and no request to re-assess it;
- selecting `assess-itil-alignment` despite the explicit instruction not to;
- converting T-04 or T-06 NOT RUN into PASS/Verified;
- treating CHG-9481 Draft as approved;
- treating DEF-17 as closed/accepted/mitigated without evidence;
- converting the Candidate alert threshold or Candidate production window into approved/confirmed state;
- inventing Change Authority, CAB requirement, rollback timing, production deployment success or defect acceptance;
- treating pilot/test-environment success as proof of production success.
