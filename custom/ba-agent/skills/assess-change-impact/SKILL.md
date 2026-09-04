---
name: assess-change-impact
description: Assess the evidence-backed impact of a proposed business, technical, service or release change across services, users, interfaces, data, operations, dependencies and risks without inventing affected systems, owners, approvals or implementation mechanisms.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Assess Change Impact

Version: **0.2.0**

## Purpose

Identify what a proposed change demonstrably affects, what may be affected, and what remains unknown so downstream planning and Change Readiness can focus on real evidence rather than generic change checklists.

This Skill assesses impact. It does not approve the change, assign governance authority, design the solution, or manufacture an implementation plan.

## Core principles

**Potential relevance is not evidence of impact.**

Commonly related systems, teams, network paths, databases, security controls, vendors, support processes or customers must not be marked impacted unless the supplied evidence supports that relationship.

**Absence of evidence is not evidence of non-impact.**

An unmentioned domain must not be labelled `Not impacted`, `unchanged`, or `out of scope` merely because the packet says nothing about it. Use `Not impacted / excluded` only when the source explicitly establishes that state. Omit irrelevant unreferenced domains; if an unreferenced domain is materially important to readiness, surface it as `Unknown` / `Not evidenced`, not as a confirmed non-impact.

## Impact classes

Use:

- `Confirmed direct impact` — explicitly affected by the change.
- `Confirmed indirect impact` — explicit dependency/flow demonstrates downstream impact.
- `Candidate impact` — source suggests possible impact but dependency is unverified.
- `Unknown` — impact cannot be established from supplied evidence.
- `Not impacted / excluded` — explicitly established as unaffected or out of scope.

## Impact domains

Assess only where evidence exists or a material unknown must be raised:

- services / applications;
- users / customer groups;
- business processes / operating procedures;
- interfaces / integrations;
- data / records / mappings;
- access / identity / permissions;
- infrastructure / platform;
- support / service desk / operations;
- monitoring / reporting;
- vendors / third parties;
- release / deployment dependencies;
- continuity / fallback;
- policy / governance dependencies.

## Rules

- Separate the changed component from things that consume or depend on it.
- Preserve unverified dependency language such as `probably`, `may`, `believed to`, `not checked` as Candidate or Unknown.
- Do not infer network/firewall/database/security impact merely because software changes.
- Do not infer non-impact merely because a system/domain is unmentioned.
- Do not infer customer impact from an internal technical change unless a supported user/service path exists.
- Do not assign an impact owner or decision authority without explicit evidence.
- Do not convert missing evidence into a mandatory approval, CAB gate, test gate, rollback requirement, outage window, communication plan or implementation task.
- Do not turn an unapproved planning Target into an action to `obtain approval` unless supplied policy/evidence establishes that approval as a requirement. Preserve it as non-binding/unapproved and identify only the evidenced decision or clarification need.
- A suggestion that CAB, Security or another governance body may be involved remains Candidate/Unknown unless policy or authority evidence establishes the gate or decision right. Do not restate it as a formal sign-off task.
- Risks must be tied to a supported impact/dependency. Generic project risks are out of scope.
- If a fallback/manual path is explicitly available, preserve it as an operational impact/boundary without inventing workflow details.
- Distinguish current-state impact from future Candidate/Deferred scope.

## Output contract

Return:

### 1. Change objective / boundary

What is changing and what the packet explicitly excludes or defers.

### 2. Impact register

For each impact include:

- Impact ID;
- domain;
- impacted item/group;
- impact class;
- evidence/source reference;
- nature of impact;
- confidence;
- downstream planning implication limited to what the evidence supports.

### 3. Dependency chain

Show only supported upstream/downstream dependencies. Mark unverified links Candidate/Unknown.

### 4. Impact risks

Only evidence-backed risks caused by the identified impact/dependency.

### 5. Unknown / candidate impacts to verify

Questions that materially affect Change Readiness. Do not state a verification method unless sourced.

### 6. Explicit non-impacts / exclusions

Include only source-established unaffected items, explicit exclusions, and Deferred scope. Do not populate this section with generic unmentioned infrastructure or controls.

### 7. Change-readiness handoff

Summarize Confirmed impacts, Candidate/Unknown impacts, and dependencies that `prepare-solution-change-readiness` may rely on. Missing answers remain gaps/questions rather than invented gates, approvals or implementation tasks. Preserve planning Targets as non-binding unless the source explicitly establishes an approval requirement.

## Self-check

Before returning, verify:

- no affected system/team/process was introduced solely from common practice;
- no unmentioned system/domain was promoted to `Not impacted`, `unchanged`, or `out of scope` without explicit evidence;
- every Confirmed impact has explicit dependency evidence;
- no owner/authority was invented;
- no Candidate impact was presented as confirmed;
- no planning Target was converted into an approval obligation without source support;
- no implementation or approval mechanism was manufactured.

## Changelog

### 0.2.0

- Added the explicit `absence of evidence is not evidence of non-impact` rule.
- Restricted `Not impacted / excluded` to source-established states.
- Prevented planning Targets and suggested governance involvement from becoming invented approval/sign-off tasks.
- Tightened Change Readiness handoff wording around unreferenced domains and governance.

### 0.1.0

- Initial evidence-backed change-impact assessment capability.
