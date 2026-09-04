---
name: assess-operational-readiness
description: Assess supplied service, support, monitoring, recovery, runbook, ownership, access, configuration, capacity, handover and known-defect evidence for operational readiness without inventing missing controls, treating absent evidence as failure, or converting best practice into mandatory local gates.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Assess Operational Readiness

Version: **0.1.0**

## Purpose

Assess whether the supplied evidence demonstrates that a service/change can be operated and supported as intended after release.

This Skill is a readiness assessment, not an approval, certification audit, operational design exercise, or generic production-readiness checklist.

## Core principle

**Operational readiness is evidence-backed. Missing evidence is `Not evidenced`, not automatically a failure or mandatory gate.**

## Readiness states

Use:

- `Ready` — supplied evidence adequately demonstrates the assessed operational condition.
- `Partially ready` — relevant evidence exists but material gaps/uncertainty remain.
- `Not evidenced` — packet does not demonstrate the condition.
- `Not ready` — supplied evidence directly demonstrates an unresolved condition that prevents the stated operational outcome.
- `Not applicable / out of scope` — explicitly excluded or irrelevant to the assessed release.

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
- Preserve explicit local policy gates exactly when they are supplied.
- Do not invent support owners, escalation teams, hours, monitoring tools, thresholds, alert routes, recovery objectives, permissions, change records or sign-off bodies.
- Distinguish a planned future operational control from evidence that it exists now.
- A known defect remains open unless evidence shows closure or accepted residual risk.
- A manual fallback counts only to the extent its availability/conditions are evidenced; do not invent procedure details.
- If supplied evidence directly shows an operational blocker, label it `Not ready` and explain the supported impact.
- Relevant-but-missing evidence should normally be `Not evidenced` plus a question, not an invented pre-release gate.

## Output contract

Return:

### 1. Overall operational-readiness assessment

`Ready`, `Partially ready`, `Not evidenced`, or `Not ready` with concise evidence-based rationale.

### 2. Readiness matrix

For each relevant operational domain include:

- Domain / readiness item;
- state;
- supplied evidence;
- demonstrated condition;
- gap / limitation;
- whether the gap is an explicit source/local-policy gate or merely an unanswered readiness question.

### 3. Confirmed blockers

Only conditions directly evidenced as preventing intended operation or violating an explicit supplied gate.

### 4. Known defects / workarounds / residual risk

Preserve their supplied status, owner/acceptance authority only when evidenced.

### 5. Not-evidenced operational questions

Questions that matter to the stated service/change but are not demonstrated. Do not convert these questions into mandatory controls by default.

### 6. Change / ITIL handoff

State what operational evidence can be carried into Change Readiness or ITIL alignment and what remains uncertain.

## Self-check

Before returning, verify no common best-practice artifact became a mandatory gate without source evidence, no absent evidence became a failure, no owner/tool/threshold/process was invented, and every `Not ready` conclusion is directly supported.