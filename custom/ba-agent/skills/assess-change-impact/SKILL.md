---
name: assess-change-impact
description: Assess the evidence-backed impact of a proposed business, technical, service or release change across services, users, interfaces, data, operations, dependencies and risks without inventing affected systems, owners, approvals or implementation mechanisms.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Assess Change Impact

Version: **0.1.0**

## Purpose

Identify what a proposed change demonstrably affects, what may be affected, and what remains unknown so downstream planning and Change Readiness can focus on real evidence rather than generic change checklists.

This Skill assesses impact. It does not approve the change, assign governance authority, design the solution, or manufacture an implementation plan.

## Core principle

**Potential relevance is not evidence of impact.**

Commonly related systems, teams, network paths, databases, security controls, vendors, support processes or customers must not be marked impacted unless the supplied evidence supports that relationship.

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
- Do not infer customer impact from an internal technical change unless a supported user/service path exists.
- Do not assign an impact owner or decision authority without explicit evidence.
- Do not convert missing evidence into a mandatory approval, CAB gate, test gate, rollback requirement, outage window, communication plan or implementation task.
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

Preserve stated exclusions and Deferred scope.

### 7. Change-readiness handoff

Summarize Confirmed impacts, Candidate/Unknown impacts, and dependencies that `prepare-solution-change-readiness` may rely on. Missing answers remain gaps/questions rather than invented gates.

## Self-check

Before returning, verify no affected system/team/process was introduced solely from common practice, every Confirmed impact has explicit dependency evidence, no owner/authority was invented, no Candidate impact was presented as confirmed, and no implementation or approval mechanism was manufactured.