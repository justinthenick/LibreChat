---
name: analyze-nonfunctional-requirements
description: Analyze supplied business, technical, operational or service material for evidence-backed non-functional requirements, quality targets, constraints, assumptions, conflicts and unknowns without inventing standard NFRs, architecture mechanisms, thresholds or compliance obligations.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Analyze Non-Functional Requirements

Version: **0.2.0**

## Purpose

Extract and classify non-functional requirements (NFRs) and quality concerns from supplied evidence while preserving uncertainty, authority boundaries and source strength.

This Skill does not design architecture, select technologies, create implementation mechanisms, assign decision authority, or manufacture a checklist of requirements that the source never established.

## Core principle

**A common quality concern is not automatically a requirement.**

Performance, availability, security, accessibility, recoverability, observability, supportability and similar qualities may be relevant domains, but they become requirements only when supported by the supplied evidence.

## NFR domains

Classify only where useful. Typical domains include:

- performance / latency / throughput;
- availability / resilience;
- scalability / capacity;
- security / privacy;
- data residency / retention;
- recoverability / continuity;
- observability / auditability;
- maintainability / supportability;
- usability / accessibility;
- compatibility / interoperability;
- portability;
- compliance / policy constraint;
- environmental / physical constraints.

Do not force every domain into the output.

## Evidence and status

For each material NFR distinguish:

- evidence class: `Explicit`, `Inferred`, `Proposed`, `Assumption`, `Disputed`, `Unknown`;
- status: `Confirmed`, `Candidate`, `Target`, `Disputed`, `Deferred`, `Unknown`;
- confidence where useful.

Mandatory wording is reserved for Confirmed mandatory content.

## Rules

- Preserve tentative language such as `aim`, `target`, `prefer`, `probably`, `roughly`, `should`, `may`.
- Do not turn a Target into an SLA/SLO or pass/fail requirement.
- Do not invent numeric thresholds to make a qualitative request measurable.
- Do not turn a quality outcome into a technology mechanism. For example, `recover quickly` does not imply active-active architecture; `secure` does not imply a particular encryption scheme.
- Do not infer regulatory or certification obligations merely because a domain commonly has them.
- Distinguish a workload/capacity estimate from a committed capacity requirement.
- Distinguish location/residency outcomes from storage/cloud architecture choices.
- When source statements conflict, preserve the conflict and identify the decision that remains unresolved.
- **Authority must be explicit.** A proposer, reviewer, sponsor, steering participant, subject-matter team, policy function, job title or affected business area does not establish Decision Owner or approval authority. Unless the packet explicitly establishes authority, use exactly `Decision owner: Unknown`; do not substitute a likely committee, leadership group, governance function or role.
- **Operational coverage is not technical runtime.** A Service Desk/support-hours statement establishes the support process window only unless the source separately constrains service availability, system runtime, monitoring/tooling operation, maintenance windows or after-hours behavior.
- **Fallback outcomes are not implementation mechanisms.** If the source confirms an existing manual/business fallback, preserve that outcome/path without designing user messaging, routing automation, failover logic or technical integration around it.
- Missing NFR evidence may be listed as an **open question / unassessed quality area** if it is materially relevant to the requested outcome, but must not be rewritten as a requirement. Do not turn an unassessed area into an assigned action/approval workflow.

## Output contract

Return:

### 1. Overall NFR readiness

`Ready`, `Partially Ready`, or `Not Ready` for downstream solution design, with a concise reason.

### 2. NFR register

For each item include:

- NFR ID;
- domain;
- requirement / quality statement;
- evidence class;
- status;
- source reference;
- confidence;
- measurable threshold only when sourced.

### 3. Constraints and boundaries

Explicit non-functional constraints that solution design must preserve. Keep business/operational process boundaries distinct from technical service/runtime constraints.

### 4. Conflicts / disputed quality decisions

Preserve all positions. Include `Decision owner: <explicitly sourced owner>` only when authority evidence is present; otherwise use `Decision owner: Unknown`. Do not infer authority from who proposed, reviews, sponsors, discusses or would normally govern the topic.

### 5. Assumptions / estimates

Keep estimates and assumptions outside Confirmed requirements.

### 6. Unassessed / unknown quality areas

Questions only; do not invent requirements, mechanisms, assignees or approval routes.

### 7. Solution-design handoff

List NFR IDs and statuses that `design-technical-solution` may rely on. State which Targets/Candidates/Unknowns must remain non-binding. For Confirmed operational/process constraints, pass the confirmed outcome and boundary without extrapolating technical architecture or tooling behavior that is not sourced.

## Self-check

Before returning, verify that:

1. every numeric threshold is sourced;
2. no common best practice became a requirement by default;
3. no mechanism was substituted for an outcome;
4. no Target was hardened;
5. no source/proposer/reviewer/team/title was converted into Decision Owner or approval authority without explicit evidence;
6. no support-process coverage window was converted into a system/runtime/tooling constraint;
7. no manual fallback outcome was expanded into invented UX, automation or failover design;
8. no regulatory/approval authority was invented.

## Changelog

### 0.2.0

- Strengthened explicit-authority handling for disputed/unresolved NFR decisions.
- Separated support-process coverage from technical runtime/availability/tooling constraints.
- Prevented confirmed manual fallback outcomes from becoming invented implementation/UX mechanisms.
- Prevented unassessed NFR questions from becoming assigned approval/action workflows.

### 0.1.0

- Initial evidence-backed NFR analysis capability.
