---
name: assess-operational-readiness
description: Assess supplied service, support, monitoring, recovery, runbook, ownership, access, configuration, capacity, handover and known-defect evidence for operational readiness without inventing missing controls, treating absent evidence as failure, or converting best practice into mandatory local gates.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Assess Operational Readiness

Version: **0.2.0**

## Purpose

Assess whether the supplied evidence demonstrates that a service/change can be operated and supported as intended after release.

This Skill is a readiness assessment, not an approval, certification audit, operational design exercise, or generic production-readiness checklist.

## Core principle

**Operational readiness is evidence-backed. Missing evidence is `Not evidenced`, not automatically a failure, mandatory gate, or proof that the topic is out of scope.**

## Readiness states

Use:

- `Ready` — supplied evidence adequately demonstrates the assessed operational condition.
- `Partially ready` — relevant evidence exists but material gaps/uncertainty remain.
- `Not evidenced` — packet does not demonstrate the condition.
- `Not ready` — supplied evidence directly demonstrates an unresolved condition that prevents the stated operational outcome.
- `Not applicable / out of scope` — explicit supplied scope/applicability evidence establishes that the item does not apply or is excluded.

Do not use `Not applicable / out of scope` merely because the packet does not require or mention a common operational artifact.

## Operational domains

Assess only where relevant to the supplied service/change:

- support ownership and contact path;
- service hours / support coverage;
- runbook / operating procedure evidence;
- monitoring / alerting / observability outcomes;
- incident/escalation path;
- recovery / fallback / continuity;
- access / credentials / operational permissions;
- configuration / version / asset records;
- capacity / performance operating envelope;
- vendor / third-party support dependency;
- known defects / workarounds;
- handover / knowledge transfer;
- data operations / retention where relevant.

## Rules

- Do not require every common operational artifact. Assess what the source/request makes relevant.
- A missing runbook, dashboard, CMDB entry, on-call roster, rollback plan or vendor contract is not automatically a release blocker unless local/source evidence establishes that requirement.
- **Absence is not non-applicability.** If a generic artifact/domain is neither source-required nor materially relevant, omit it. If it is materially relevant to the requested assessment but not demonstrated, use `Not evidenced` / question. Use `Not applicable / out of scope` only when explicit evidence establishes that state.
- Preserve explicit local policy gates exactly when they are supplied.
- Do not invent support owners, escalation teams, hours, monitoring tools, thresholds, alert routes, recovery objectives, permissions, change records or sign-off bodies.
- Distinguish a planned future operational control from evidence that it exists now.
- A known defect remains open unless evidence shows closure or accepted residual risk.
- A manual fallback counts only to the extent its availability/conditions are evidenced; do not invent procedure details.
- If supplied evidence directly shows an operational blocker, label it `Not ready` and explain the supported impact.
- Relevant-but-missing evidence should normally be `Not evidenced` plus a question, not an invented pre-release gate.
- **Readiness state ≠ approval gate.** `Partially ready` or `Not evidenced` does not mean `prerequisite for Change approval`, `deployment checklist must`, `sign-off required`, or similar unless explicit local/source policy establishes that gate. Keep demonstrated blockers separate from ordinary gaps.
- A `Not ready` blocker may justify the operational conclusion that the stated service outcome is not ready; do not convert that assessment into a formal approve/reject/hold decision unless the supplied authority/policy asks the assessor to make that decision.

## Output contract

Return:

### 1. Overall operational-readiness assessment

`Ready`, `Partially ready`, `Not evidenced`, or `Not ready` with concise evidence-based rationale. This is an evidence assessment, not a formal Change approval/rejection.

### 2. Readiness matrix

For each **relevant** operational domain include:

- Domain / readiness item;
- state;
- supplied evidence;
- demonstrated condition;
- gap / limitation;
- whether the gap is an explicit source/local-policy gate, a demonstrated blocker, or merely an unanswered readiness question.

Do not add generic domains solely to mark them Not applicable.

### 3. Confirmed blockers

Only conditions directly evidenced as preventing intended operation or violating an explicit supplied gate. Keep these distinct from Partially ready / Not evidenced items.

### 4. Known defects / workarounds / residual risk

Preserve their supplied status, owner/acceptance authority only when evidenced.

### 5. Not-evidenced operational questions

Questions that matter to the stated service/change but are not demonstrated. Do not convert these questions into mandatory controls, approval prerequisites, or assigned actions by default.

### 6. Change / ITIL handoff

State separately:

- transferable Ready/accepted evidence;
- demonstrated operational blockers;
- Partially ready / Not evidenced questions;
- explicit local-policy gates, if any.

Do not label ordinary gaps as `Open items for Change Approval`, `approval prerequisites`, or `deployment checklist requirements` unless that gate is explicitly sourced.

## Self-check

Before returning, verify:

- no common best-practice artifact became a mandatory gate without source evidence;
- no absent evidence became a failure or `Not applicable/out of scope` merely from silence;
- no owner/tool/threshold/process was invented;
- every `Not ready` conclusion is directly supported;
- demonstrated blockers are separated from ordinary missing/partial evidence;
- no readiness gap was promoted into an approval/checklist prerequisite without explicit policy evidence;
- no formal approval/rejection authority was assumed by the assessment.

## Changelog

### 0.2.0

- Reserved `Not applicable / out of scope` for explicit applicability/scope evidence.
- Added omit-vs-Not-evidenced handling for generic operational artifacts.
- Separated operational blockers from ordinary partial/not-evidenced gaps in Change/ITIL handoff.
- Prevented readiness gaps from becoming approval/checklist prerequisites without explicit policy.

### 0.1.0

- Initial evidence-backed operational-readiness capability.
