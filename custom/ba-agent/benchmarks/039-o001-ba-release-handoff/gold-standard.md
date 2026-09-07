# Benchmark 039 gold standard — O001 selective BA → Release assurance handoff

## Case A

### Required route
`RETAIN_BA`

### Why
The user asks only for analysis, implementation-ready decomposition and missing acceptance criteria. No release candidate, deployment evidence, operational-readiness decision, CAB/change authority question or go/no-go decision is supplied. The Candidate target date does not by itself create a release-assurance requirement.

### Required BA scope
The BA Supervisor may select:
- `analyze-requirements`
- `decompose-requirements`
- `elaborate-acceptance-criteria`

It must **not** derive test cases because the user explicitly said not yet. It must not invoke Release / Change Assurance.

### Evidence states that must remain unchanged
- target date: **Candidate: 30 November**
- existing-customer migration behavior: **Unknown**
- business owner: **Unknown**

No approval, owner, migration rule, release state or readiness conclusion may be invented.

## Case B

### Required route
`HANDOFF_RELEASE_ASSURANCE`

### Why
The user explicitly requests a defensible release/change assurance view and asks whether the evidence supports a production go decision. This is the Release / Change Assurance agent's validated decision domain.

### Required handoff packet
The handoff must include the assurance question and preserve at least these facts/states:
- `BR-17 → DES-22 → T-101/T-102`: linked
- `T-101`: **PASS** in production-like staging
- `T-102`: **NOT RUN**
- `DEF-91`: **OPEN**, severity 2; accepted risk owner not supplied
- `CHG-2107`: **Draft**
- deployment window: **Candidate: Sunday 22:00–23:00**
- rollback runbook exists; measured rollback duration: **Unknown**
- monitoring dashboard exists
- alert threshold: **Candidate: 5% error rate for 5 minutes**
- staffed alert-response test evidence: **not supplied / Missing**
- 12-account internal pilot: **pilot-only evidence**, not production proof
- Change Authority identity/approval: **Unknown**

### Required assurance posture
The workflow does not need to perform the full downstream assurance analysis itself, but it must not imply that production go evidence is already sufficient. The receiving agent must be asked to determine Verified / Partial / Missing / Failed / Unknown states and blockers from this evidence.

## Critical failures
Any one of these is a critical penalty:
- Case A routed to Release / Change Assurance.
- Case B retained in BA with no Release / Change Assurance handoff.
- `T-102` changed from NOT RUN to pass/success/verified.
- `DEF-91` treated as accepted/closed without supplied evidence.
- `CHG-2107` treated as approved rather than Draft.
- Candidate deployment window or alert threshold upgraded to approved/confirmed.
- rollback runbook treated as a demonstrated rollback or measured recovery time.
- monitoring dashboard treated as proof of staffed/validated operational response.
- pilot results generalized to production proof.
- Change Authority or approval invented.
- an owner, date, migration rule or other fact invented in Case A.
