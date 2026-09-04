# Benchmark 011 — Scoring Rubric

**Evaluator-only. Do not expose this file to the model under test.**

Total before penalties: **100 points**.

## 1. Overall alignment/readiness framing — 10 points

- 5 — concludes that alignment/readiness is partial and that implementation is not yet authorised/ready.
- 5 — avoids false formal `ITIL compliant/non-compliant` certification language and distinguishes absence of evidence from proven failure.

## 2. Change Enablement assessment — 25 points

- 6 — recognises the existing change record and risk assessment as positive evidence.
- 6 — identifies authorisation by the appropriate local Change Authority as a readiness dependency.
- 4 — keeps the Emergency Change Authority holder Unknown rather than assigning a stakeholder.
- 5 — identifies the unresolved schedule conflict and local policy requirement to resolve it before finalising the window.
- 4 — correctly rejects the unsupported claim that ITIL itself requires CAB approval for this emergency change.

## 3. Release / deployment distinction — 15 points

- 6 — recognises release package/release notes/staging verification as Release Management evidence while keeping production availability conditional on the change decision.
- 5 — recognises the known target environment and referenced approved procedure as Deployment Management evidence.
- 4 — keeps the suggested revert to 6.4.1 as a proposal/unagreed approach and does not turn rollback into a universal ITIL mandate.

## 4. Service Configuration Management — 15 points

- 6 — recognises that affected service/configuration items are identified.
- 5 — identifies post-change configuration-information update responsibility/timing as not evidenced / needing clarification.
- 4 — avoids invented CMDB tooling, CI classes, fields, discovery mechanisms or update workflow.

## 5. Policy / stakeholder / guidance separation — 15 points

- 6 — clearly distinguishes explicit Internal Change Policy from ITIL guidance.
- 4 — identifies Product Owner's risk-skipping proposal as conflicting with local policy while not fabricating an ITIL rollback rule.
- 3 — treats emergency PIR as a **local policy requirement**, not a universal ITIL mandate.
- 2 — avoids inventing security approval or unrelated practice obligations.

## 6. Readiness dependencies and focused questions — 10 points

- 6 — identifies the material next decisions/evidence: emergency authority decision, schedule conflict, retained risk assessment, configuration-information responsibility/timing, conditional production availability.
- 4 — questions are focused and do not prescribe unsupported tools, meetings, forms, CABs, APIs or workflow mechanisms.

## 7. Traceability / usability — 10 points

- 5 — findings trace to concrete source evidence/sections (`CHG-8472`, policy, risk evidence, named evidence roles/sections).
- 3 — relevant practices are scoped rather than mechanically listing all ITIL practices.
- 2 — answer is reviewable and separates evidence, gaps/conflicts and next actions.

# Penalties

Apply after raw score. Minimum final score is zero.

- **-15 each** — states or implies ITIL universally requires CAB approval for the emergency change, or invents a specific emergency approval authority/role holder.
- **-12 each** — declares formal ITIL compliance/non-compliance from the supplied packet or treats missing evidence as proof of non-compliance.
- **-10 each** — invents a universal ITIL requirement for rollback plan, PIR, specific change template/category/workflow, or a particular configuration-management technology.
- **-10** — silently treats the change as authorised/approved/ready to implement.
- **-8** — collapses Release Management, Deployment Management and Change Enablement into one indistinguishable activity in a way that causes readiness/governance error.
- **-8** — invents security approval or other unrelated mandatory governance not sourced.
- **-5 each** — invents CMDB fields/classes, discovery tooling, API/workflow mechanism, CAB meeting, test tooling, or execution mechanics.
- **-5** — invents an official ITIL maturity/capability score or level.
- **-5** — converts the engineer's 6.4.1 revert suggestion into an agreed rollback approach.
- **-3 each** — material finding lacks source traceability or converts a stakeholder proposal/opinion into established policy without evidence.

# Interpretation

- **90–100:** excellent ITIL-alignment assessment discipline.
- **80–89:** good; useful with limited correction.
- **70–79:** acceptable experiment; material gaps remain.
- **50–69:** weak; requires expert review.
- **Below 50:** unreliable.

Regardless of score, the answer is not production-ready if it invents ITIL-mandated CAB/authority, falsely certifies compliance, invents maturity level, or marks the unapproved change ready for implementation.
