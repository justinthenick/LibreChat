---
name: prepare-implementation-ready-requirements
description: Use when one request explicitly asks to analyse raw requirements and continue through implementation-ready delivery decomposition and acceptance criteria in the same response. Combines the validated analysis, decomposition and acceptance-criteria disciplines without inventing missing business or solution facts.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Prepare Implementation-Ready Requirements

Version: **0.1.0**

## Purpose

Execute the complete Business Analysis chain in one model-invoked skill when the user explicitly wants all three outcomes together:

1. requirements analysis;
2. delivery decomposition; and
3. acceptance-criteria elaboration.

This is an **orchestration skill**, not a replacement for the independently validated `analyze-requirements`, `decompose-requirements`, or `elaborate-acceptance-criteria` skills. Use those individual skills when only one stage is requested. This skill exists because the runtime model-invoked `skill` tool loads one skill per call; a single composite load makes an already-selected three-stage route atomic and prevents the chain from terminating between skill calls.

## Core principle

**Continue as far as the supplied evidence defensibly permits, while keeping every unresolved fact unresolved.**

Implementation-ready does not mean inventing implementation detail. Where a decision is unresolved, produce the confirmed work at the highest channel/solution-neutral abstraction and represent the unresolved choice as a Decision Item or blocked/conditional criterion.

## Non-negotiable evidence rules

1. Never turn ambiguity, inference, common practice or a plausible design into confirmed fact.
2. Use only actors, roles, systems, business outcomes, permissions, business rules, constraints, qualities and decision authorities supported by the supplied source. If none are established, write **Unknown** or **None identified from supplied evidence**.
3. Do not invent a current-state problem merely because a requested feature implies one. For example, a request for bulk processing does not prove users currently perform each item manually.
4. Do not invent benefits such as productivity, reduced effort, reduced risk, improved usability or faster processing unless the source establishes them. If useful as an analyst hypothesis, label it **Proposed**, never Confirmed.
5. Do not invent non-functional requirements such as stability, integrity, security, auditability, resilience, performance, scalability or availability. Record them only when sourced; otherwise leave them Not established.
6. Do not manufacture assumptions just to fill an Assumptions section. An assumption is allowed only when it is actually necessary to continue the analysis; label it explicitly and never use it to create a committed requirement or acceptance criterion.
7. Never invent UI, API, endpoint, screen, button, form, notification, queue, database, service, protocol, workflow, retry, timeout, error code, batch size, validation rule or other solution mechanism.
8. Never invent approval, governance, CAB, sponsor, Product Owner, administrator, developer, architect or decision owner. If authority is not supplied, write **Decision owner: Unknown**.
9. Preserve tentative language. Candidate, Target, Deferred, Disputed and Unknown items must remain non-mandatory unless the source independently establishes a mandatory rule.
10. Missing information is a gap, not automatically a blocker. Do not stop the chain merely because UI/API, error handling, batch size, permissions, performance or other downstream details are unknown. Continue with solution-neutral requirements and criteria where possible.

## Stage 1 — requirements analysis

Create a compact source register and extract only source-supported requirements and uncertainties.

For each material requirement include:

- stable requirement ID;
- atomic statement;
- type;
- evidence class: **Explicit / Inferred / Proposed**;
- requirement status: **Confirmed / Candidate / Target / Deferred / Disputed / Unknown** as applicable;
- source reference;
- evidence/rationale;
- confidence.

Do not write mandatory wording for an unresolved handling rule. If the source says a condition can occur but does not specify the required response, separate the established condition from the unresolved rule.

Example: `Some inspections may already be paused` establishes an input/state condition. It does **not** establish whether already-paused items must be skipped, accepted, rejected or reported in a particular way.

List ambiguities and decisions explicitly. If the implementation channel is undecided, keep UI/API/both as an unresolved Decision Item; do not select one as an analyst recommendation unless the user asked for recommendations, and never promote a recommendation into the backlog.

## Stage 2 — delivery decomposition

Do not wait for every open question to be resolved. Decompose the confirmed portion and isolate uncertainty.

Use the smallest appropriate work-item types:

- **Capability / Epic** only when useful;
- **User Story** for source-supported observable actor value/behaviour;
- **Enabler / Technical Task** only for source-supported technical outcomes;
- **Decision Item** for unresolved business/scope/channel choices;
- **Spike / Discovery Item** only when genuine technical feasibility must be established;
- **Dependency / Risk / Deferred Item** only when supported.

Every delivery item must trace to one or more upstream requirement/decision IDs. Never create an actor, benefit, implementation layer or mechanism just to make a story read naturally. If the actor benefit is not evidenced, omit the `so that` clause.

A solution-neutral story is valid. For example, when the channel is unresolved, describe the observable bulk-pause capability without inventing a screen or endpoint. The UI/API decision may remain a separate Decision Item without preventing behavioural decomposition.

## Stage 3 — acceptance criteria

Elaborate acceptance criteria only from behaviour already established by the requirements/decomposition. Criteria may make supported behaviour testable; they must not create new behaviour.

Use Given/When/Then where it improves clarity, otherwise use concise testable conditions.

For **Ready** confirmed behaviour, produce complete criteria to the extent evidence supports them.

For **Partially Ready / Conditional / Candidate / Unknown** behaviour:

- elaborate the supported portion;
- mark unresolved criteria as **Blocked / Conditional / TBD from evidence**;
- name the unresolved decision or source gap;
- do not choose an answer.

If the source establishes that already-paused inspections may be included but does not establish their expected result, a valid criterion can verify that the condition is recognised/in scope, while the exact outcome remains a blocked criterion pending the handling-rule decision. Do not invent skip/error/idempotent behaviour.

## Required output

Return **one consolidated answer**, not three independent essays. Default structure:

1. **Executive summary** — source-supported need and key unresolved decisions only.
2. **Source register**.
3. **Requirements register**.
4. **Decisions / ambiguities / not established**.
5. **Decomposition readiness** — Ready / Partially Ready / Not Ready, with explanation; Partially Ready does not mean stop.
6. **Implementation-ready delivery backlog** — source-supported current work only.
7. **Decision / discovery items** — only genuinely required unresolved work.
8. **Acceptance criteria** — grouped by delivery item, preserving blocked/conditional states.
9. **Traceability summary** — Requirement → delivery item → acceptance criteria.
10. **Open questions** — only questions that materially affect unresolved behaviour or scope.

Do not add an Analyst Proposals section unless the user explicitly requests recommendations. Do not add speculative assumptions merely to populate a section.

## Mandatory compliance check

Before answering, verify all of the following:

- [ ] Every claimed actor, problem, benefit, rule, quality and authority is source-supported or explicitly labelled Proposed/Unknown.
- [ ] No current-state workflow was inferred from the requested future capability.
- [ ] No UI/API decision was silently made.
- [ ] No already-paused handling behaviour was invented.
- [ ] No batch limit, permission model, error behaviour, performance target, logging/audit requirement or architecture was invented.
- [ ] Candidate/Target/Unknown items were not upgraded to Confirmed or mandatory language.
- [ ] Confirmed behaviour was decomposed even if unrelated downstream details remain unknown.
- [ ] Every backlog item traces upstream.
- [ ] Every acceptance criterion traces to established behaviour and does not create new behaviour.
- [ ] The response reaches all three requested stages in one consolidated answer.

If any check fails, revise before responding.
