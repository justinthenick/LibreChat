---
name: analyze-nonfunctional-requirements
description: Analyze supplied business, technical, operational or service material for evidence-backed non-functional requirements, quality targets, constraints, assumptions, conflicts and unknowns without inventing standard NFRs, architecture mechanisms, thresholds or compliance obligations.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Analyze Non-Functional Requirements

Version: **0.1.0**

## Purpose

Extract and classify non-functional requirements (NFRs) and quality concerns from supplied evidence while preserving uncertainty and source strength.

This Skill does not design architecture, select technologies, create implementation mechanisms, or manufacture a checklist of requirements that the source never established.

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
- Missing NFR evidence may be listed as an **open question / unassessed quality area** if it is materially relevant to the requested outcome, but must not be rewritten as a requirement.

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

Explicit non-functional constraints that solution design must preserve.

### 4. Conflicts / disputed quality decisions

Preserve all positions; use `Decision owner: Unknown` unless authority is explicitly sourced.

### 5. Assumptions / estimates

Keep estimates and assumptions outside Confirmed requirements.

### 6. Unassessed / unknown quality areas

Questions only; do not invent requirements.

### 7. Solution-design handoff

List NFR IDs and statuses that `design-technical-solution` may rely on. State which Targets/Candidates/Unknowns must remain non-binding.

## Self-check

Before returning, verify that every numeric threshold is sourced, no common best practice became a requirement by default, no mechanism was substituted for an outcome, no Target was hardened, and no regulatory/approval authority was invented.