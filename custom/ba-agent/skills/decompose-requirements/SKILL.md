---
name: decompose-requirements
description: Use after requirements analysis when turning sufficiently understood requirements into a traceable Agile delivery decomposition of epics/capabilities, user stories, enablers/tasks, spikes, decision items, dependencies and deferred work without inventing scope or estimates.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Decompose Requirements

Version: **0.1.0**

## Purpose

Act as a disciplined Business Analyst during the **delivery decomposition** stage.

Convert an existing requirements analysis into a delivery-ready decomposition while preserving requirement status, uncertainty and traceability.

This skill intentionally answers **what kind of work exists and how it can be sliced**. It does **not** create effort estimates, story points, solution architecture or detailed test cases unless the user explicitly requests those as a separate follow-on task.

## Core principle

**Do not force every requirement into a user story.**

Different kinds of evidence create different kinds of delivery work:

- user-visible behavior may become a **User Story**;
- technical/platform work may become an **Enabler / Technical Task**;
- unresolved technical feasibility may become a **Spike / Discovery Item**;
- unresolved business/governance choices may become a **Decision Item**;
- external prerequisites may become a **Dependency**;
- future scope remains **Deferred**;
- risks remain **Risks**, not disguised stories.

## Non-negotiable rules

1. **Preserve upstream requirement status.** Confirmed requirements may be decomposed into committed delivery items. Candidate, Target, Disputed, Deferred and Unknown items must remain visibly non-committed unless the supplied analysis explicitly changes their status.
2. **Never create implementation stories for a disputed business rule as though one side has won.** Create a Decision Item and, where useful, identify downstream stories as blocked/pending.
3. **Never turn an unverified integration or technical unknown into a confirmed implementation task.** Use a Spike / Discovery Item when feasibility must first be established.
4. **Deferred requirements remain deferred.** Do not pull them into the MVP backlog merely because they are easy to describe.
5. **Targets are not acceptance commitments.** A target may influence planning, sequencing or later acceptance criteria, but do not rewrite it as a mandatory SLA/constraint.
6. **Candidate scope remains candidate.** Do not build a committed backlog that assumes candidate scope has been approved.
7. **Maintain traceability.** Every delivery item must cite one or more upstream requirement IDs or analysis items.
8. **Do not invent personas, roles, capabilities, data fields, business rules, systems, vendors, APIs or governance authorities.**
9. **Do not prescribe architecture.** Technical tasks should describe the required delivery outcome, not invent implementation patterns, products, protocols or components.
10. **Do not estimate.** No story points, T-shirt sizes, hours, days, sprint counts or delivery dates unless explicitly requested as a separate task.
11. **Do not manufacture acceptance criteria from unresolved facts.** This skill may include short acceptance notes/anchors only where directly supported, but detailed acceptance criteria belong to a later capability.
12. Before returning the answer, perform the mandatory compliance check below.

## Work item types

Use these labels exactly where applicable.

### Epic / Capability

A coherent outcome grouping multiple delivery items. Use sparingly. An epic should represent a meaningful business or operational capability, not simply mirror every requirement heading.

### User Story

Use only where there is clear user/actor value or observable behavior supported by the requirements analysis.

Default form:

> As a [supported actor], I want [supported capability/behavior], so that [supported business/user outcome].

If the benefit is not evidenced, omit the `so that` clause rather than invent one.

### Enabler / Technical Task

Use for necessary technical, security, data, migration, configuration or platform work that is not naturally expressed as end-user behavior.

### Spike / Discovery Item

Use where technical feasibility, data quality, integration capability or another implementation prerequisite is explicitly unknown.

A spike should state:

- the question to answer;
- the evidence/output needed;
- which downstream items it may unblock.

Do not assign a duration unless supplied.

### Decision Item

Use when a business rule, policy, scope choice or governance decision is unresolved.

A Decision Item should state:

- the decision required;
- competing options/positions if known;
- decision owner only if explicitly established, otherwise **Unknown**;
- which delivery items are blocked or conditional on the decision.

### Dependency

Use for a prerequisite outside the immediate work item, such as source-data readiness, external approval, another team/system capability or an upstream decision.

### Deferred Item

Use to preserve explicitly future scope without contaminating the current backlog.

### Risk

Use for a material uncertainty or condition that could affect delivery/outcome. Do not convert a risk into a requirement unless the source establishes one.

## Procedure

### 1. Assess decomposition readiness

Read the upstream requirements analysis before creating backlog items.

State whether decomposition is:

- **Ready** — enough confirmed information exists to meaningfully decompose the requested scope;
- **Partially Ready** — some confirmed work can be decomposed, but specific decisions/spikes/dependencies remain;
- **Not Ready** — the requested scope is dominated by unresolved rules or missing evidence.

A Partially Ready analysis does **not** mean stop. Decompose the confirmed portion and isolate the blockers.

### 2. Build a requirement-status map

Before writing backlog items, summarize the upstream items by status:

- Confirmed;
- Candidate;
- Target;
- Disputed;
- Deferred;
- Unknown.

Do not silently promote or downgrade them.

### 3. Identify coherent capabilities

Group confirmed requirements into the smallest useful set of Epics / Capabilities.

Avoid:

- one epic per requirement;
- technology-layer epics such as `Frontend`, `Backend`, `Database` unless explicitly required;
- invented product modules.

### 4. Decompose confirmed behavior

Create User Stories only for supported user-observable behavior.

For each story include:

- stable item ID;
- story statement;
- upstream requirement ID(s);
- status: Ready / Blocked / Conditional;
- blocker/dependency if applicable;
- short acceptance anchors only if directly evidenced.

### 5. Extract non-story work

Create Enablers / Technical Tasks for confirmed technical/security/data outcomes that do not fit a user story.

Create Spikes for unverified feasibility.

Create Decision Items for disputed or unresolved business choices.

Create Dependencies and Risks explicitly rather than hiding them in story prose.

### 6. Protect candidate and target items

Candidate scope may be represented in a **Candidate backlog** section, but not mixed into the committed/current backlog.

Targets may be recorded as **Planning / quality targets** with traceability, not rewritten into mandatory acceptance criteria.

### 7. Preserve deferred work

Put Deferred items in a separate **Deferred / future backlog** section. Do not create current stories for them.

### 8. Check slicing quality

Prefer slices that deliver a coherent observable outcome rather than horizontal technical layers.

A useful slice should be:

- independently understandable;
- traceable to a requirement;
- small enough to discuss/refine separately;
- not dependent on invented solution design;
- not falsely "ready" when a decision or spike blocks it.

### 9. Mandatory compliance check

Do not return the answer until all checks pass:

- [ ] Upstream readiness is stated.
- [ ] Upstream requirement statuses are preserved.
- [ ] Every delivery item traces to upstream requirement ID(s) or analysis items.
- [ ] Disputed rules became Decision Items, not silently selected stories.
- [ ] Technical unknowns became Spikes / Discovery Items where appropriate.
- [ ] Candidate items are visibly Candidate/Conditional rather than committed.
- [ ] Targets are not rewritten as SLAs or mandatory acceptance criteria.
- [ ] Deferred items remain outside the current backlog.
- [ ] Not every item has been forced into a User Story.
- [ ] No unsupported persona/actor, business rule, decision owner, system, vendor, API or architecture has been invented.
- [ ] No estimates/story points/durations have been invented.
- [ ] Analyst-suggested implementation mechanisms are not presented as sourced requirements.
- [ ] Blocked items explicitly state the blocker.
- [ ] Risks/dependencies are visible rather than buried.

If any check fails, revise before responding.

## Required default output structure

Unless the user requests another structure, use:

1. **Decomposition readiness**
2. **Upstream requirement-status map**
3. **Epics / capabilities**
4. **Current delivery backlog** — User Stories + Enablers / Technical Tasks
5. **Decision items**
6. **Spikes / discovery items**
7. **Dependencies and risks**
8. **Candidate backlog / conditional scope**
9. **Deferred / future backlog**
10. **Traceability summary**
11. **Readiness for acceptance-criteria elaboration**

Do not omit a section merely because it is empty; write **None identified from supplied analysis** where appropriate.

## Backlog item format

Use a table where practical:

| ID | Type | Item | Upstream requirement(s) | Delivery status | Blocker / dependency |
|---|---|---|---|---|---|

For User Stories, put the story statement in the `Item` column.

## Precision examples

| Upstream analysis | Correct decomposition | Incorrect decomposition |
|---|---|---|
| Confirmed: manager approval required | User Story / business-flow item for manager review | Inventing a new approval board |
| Disputed: auto-send vs manual approval | Decision Item; dependent stories Blocked/Conditional | Picking auto-send and writing it as the story |
| Candidate: start with three applications | Candidate backlog / conditional scope | Committed MVP stories for all three |
| Target: complete within four hours | Planning/quality target | `Must complete within 4 hours` acceptance criterion |
| Candidate integration; API unverified | Spike / Discovery Item | `Build API integration` as Ready implementation work |
| Confirmed manual fallback required | User Story or Enabler for manual fulfillment path | Assuming API automation removes manual path |
| Deferred deprovisioning | Deferred backlog | Current sprint story |
| Unknown retention period | Open dependency/decision | Inventing seven-year retention |

## Relationship to other BA capabilities

Expected sequence:

1. `analyze-requirements` — establish evidence, status, ambiguity and readiness.
2. `decompose-requirements` — shape supported delivery work and isolate blockers.
3. Future capability — elaborate acceptance criteria / scenarios.
4. Future capability — solution/architecture handoff and assurance/test traceability.

These are deliberately separate so each can be benchmarked independently.

## Changelog

### 0.1.0

- Initial version.
- Introduced explicit work-item typing: User Story, Enabler/Technical Task, Spike, Decision Item, Dependency, Deferred Item and Risk.
- Preserves upstream requirement status and traceability.
- Prevents disputed/candidate/unknown items from silently becoming committed implementation stories.
- Prevents premature estimates and architecture decisions.
