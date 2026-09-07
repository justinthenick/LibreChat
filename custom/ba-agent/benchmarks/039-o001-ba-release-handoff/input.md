# Benchmark 039 input — O001 selective BA → Release assurance handoff

Evaluate the two independent cases below. The workflow must decide whether the BA Supervisor should retain the work or hand it to Release / Change Assurance. Preserve the supplied evidence states exactly.

## Case A — requirements refinement only

The Customer Portal team wants to add a user preference called **Invoice delivery method**.

Supplied facts:
- Current users receive PDF invoices by email.
- Product has asked for two selectable values: `Email PDF` and `Portal only`.
- The requested target date is **Candidate: 30 November**.
- Whether existing customers are migrated automatically is **Unknown**.
- The business owner for the preference is **Unknown**.
- No release candidate, deployment plan, CAB/change record, operational-readiness decision or go/no-go question has been supplied.

User request:
> Analyse this request, decompose it into implementation-ready requirements, and identify the acceptance criteria we still need. Do not create test cases yet.

## Case B — explicit release/change assurance decision

The Billing API team has completed BA refinement and now asks whether release `2026.09.2` has enough evidence to proceed to the production change window.

Supplied BA handoff facts and states:
- Requirement `BR-17` → design `DES-22` → tests `T-101` and `T-102`: **linked**.
- `T-101`: **PASS** in the production-like staging environment.
- `T-102`: **NOT RUN** because the dependent billing simulator was unavailable.
- Defect `DEF-91`: **OPEN**, severity 2; no accepted risk owner is supplied.
- Change `CHG-2107`: **Draft**.
- Deployment window: **Candidate: Sunday 22:00–23:00**.
- Rollback runbook exists and is version controlled, but measured rollback duration is **Unknown**.
- Monitoring dashboard exists. Alert threshold is **Candidate: 5% error rate for 5 minutes**. No evidence of a staffed alert-response test is supplied.
- Pilot: 12 internal accounts completed a limited pilot successfully. This is **pilot-only evidence**, not production proof.
- Change Authority identity/approval is **Unknown**.

User request:
> Give me a defensible release/change assurance view. Tell me what is verified, partial, missing or blocked and whether we have evidence for a production go decision.
