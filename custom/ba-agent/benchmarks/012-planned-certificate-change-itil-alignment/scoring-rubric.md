# Benchmark 012 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Overall alignment/readiness framing — 10
- 5 — Partially evidenced / not yet ready for implementation authorisation.
- 5 — avoids formal ITIL compliance certification and treats missing evidence as Not evidenced/Unknown.

## 2. Change Enablement — 30
- 6 — recognises existing change record/risk evidence.
- 7 — does not promote `SCM-12` to cover the proxy change or falsely call the whole change pre-authorised Standard Change.
- 5 — keeps local Change Authority holder Unknown and authorisation path unresolved.
- 5 — identifies schedule conflict and local policy requirement to resolve it before finalising the window.
- 4 — rejects universal CAB requirement / automatic ITIL approval claims.
- 3 — identifies Product Owner risk-skipping proposal as conflict with local policy.

## 3. Release / deployment distinction — 15
- 6 — recognises release package/release notes/staging verification as Release evidence while production availability remains conditional.
- 5 — recognises routine certificate deployment procedure but keeps applicability to proxy change Not evidenced.
- 4 — keeps restore-old-config/cert suggestion as proposal and avoids universal ITIL rollback mandate.

## 4. Service Configuration Management — 15
- 6 — recognises affected service/configuration information.
- 5 — identifies post-change update responsibility/timing as not evidenced.
- 4 — avoids invented CMDB/tooling/classes/workflow.

## 5. Policy / stakeholder / guidance separation — 15
- 7 — explicitly separates local policy from ITIL guidance.
- 4 — distinguishes stakeholder claims/proposals from policy.
- 4 — does not invent security/PIR/other practice obligations.

## 6. Readiness dependencies / questions — 10
- 6 — focuses on authorisation path, schedule overlap, retained risk evidence, deployment-procedure applicability, configuration-update responsibility/timing and conditional production availability.
- 4 — questions do not prescribe CABs, meetings, forms, APIs, workflows or unsupported owners.

## 7. Traceability / usability — 5
- 3 — findings trace to `CHG-8526`, policy and named evidence sections/roles.
- 2 — concise/reviewable separation of evidence, gaps/conflicts and next actions.

# Penalties

Minimum final score zero.

- **-15 each** — says ITIL automatically approves this as Standard Change; invents a specific Change Authority holder; or says ITIL universally requires CAB.
- **-12 each** — formal ITIL compliant/non-compliant certification or missing evidence treated as proof of ITIL non-compliance.
- **-10 each** — promotes `SCM-12` to cover proxy change without evidence; invents universal rollback/PIR/change-template/category/CMDB technology requirement.
- **-10** — treats change as authorised/ready to implement.
- **-8** — collapses Change Enablement/Release/Deployment in a way that causes governance error.
- **-8** — invents security approval or unrelated mandatory governance.
- **-5 each** — invents CMDB fields/classes, discovery/tooling, API/workflow, CAB meeting, test tooling or execution mechanics.
- **-5** — converts engineer's restore suggestion into agreed recovery plan.
- **-3 each** — material traceability omission or stakeholder opinion promoted to policy.

## Interpretation
- **90–100:** excellent generalization.
- **80–89:** good; limited correction.
- **70–79:** useful experiment with material gaps.
- **50–69:** weak.
- **Below 50:** unreliable.
