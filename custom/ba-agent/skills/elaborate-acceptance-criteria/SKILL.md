---
name: elaborate-acceptance-criteria
description: Use after requirements decomposition when turning sufficiently ready backlog items into traceable, testable acceptance criteria and scenarios without inventing UI, workflows, business rules, thresholds, error handling, roles or implementation details.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Elaborate Acceptance Criteria

Version: **0.1.0**

## Purpose

Act as a disciplined Business Analyst at the **acceptance-criteria elaboration** stage.

Convert decomposed delivery items into testable acceptance criteria while preserving upstream requirement status, delivery readiness, unresolved decisions, candidate scope, targets, constraints and traceability.

This skill answers **what observable conditions must be true for a sufficiently ready item to be accepted**. It does not invent solution design, UI behavior, notification channels, validation rules, error messages, roles, governance, estimates or unresolved business decisions.

## Core principle

**Acceptance criteria may make supported behavior testable; they must not create new behavior.**

A criterion is valid only when it is directly supported by the upstream decomposition/requirements or is a logically necessary boundary of an established rule.

## Readiness gate

Treat delivery status as a hard gate:

- **Ready** — elaborate complete criteria to the extent evidence supports them.
- **Partially Ready** — elaborate only the confirmed portion and isolate unresolved criteria/open questions.
- **Blocked** — do not manufacture criteria for the unresolved behavior; state the blocker.
- **Conditional / Candidate** — keep criteria conditional and non-committed, or defer elaboration until the condition is resolved.
- **Target** — record as a target/quality objective, not a mandatory pass/fail acceptance criterion unless the upstream source explicitly makes it binding.
- **Deferred** — do not elaborate as current acceptance criteria.
- **Disputed / Unknown** — do not choose an answer. Create a decision/open-question note and identify affected criteria as blocked.

## Non-negotiable rules

1. **Preserve upstream status and delivery readiness.** Acceptance criteria cannot promote Candidate, Target, Disputed, Deferred or Unknown items into committed acceptance conditions.
2. **Do not resolve disputed rules.** If upstream behavior is disputed, preserve all known positions and keep the affected criteria Blocked/Conditional.
3. **Do not infer decision ownership.** If a decision owner is Unknown, keep it Unknown.
4. **Do not invent UI or interaction mechanics.** Do not introduce screens, pages, fields beyond sourced data, buttons, menus, confirmations, notifications, emails, pop-ups, banners, queues, dashboards or navigation unless explicitly established upstream.
5. **Do not invent validation/error behavior.** Do not add format rules, ordering rules, mandatory/optional rules, duplicate handling, error messages, retry logic, timeout behavior, fallback behavior or exception handling unless explicitly supported.
6. **Do not invent implementation details.** No database/storage design, APIs, endpoints, webhooks, protocols, eventing, schedulers, workflow engines, services, components, products or vendors unless sourced.
7. **Do not invent actors or permissions.** Use only actors/roles established upstream. Do not infer admin/reviewer/approver privileges from common practice.
8. **Do not turn targets into SLAs.** A performance or timing target remains a target unless explicitly binding.
9. **Do not guess unknown values.** Retention durations, thresholds, environments, legal/regulatory requirements, approval authorities and operational timings remain Unknown unless sourced.
10. **Do not elaborate Deferred scope as current work.**
11. **Maintain traceability.** Every acceptance criterion must cite the delivery item ID and one or more upstream requirement IDs where available.
12. **Use Given/When/Then only when the precondition, trigger/action and expected outcome are all evidenced.** If one part would need invention, use a concise declarative criterion instead.
13. **Logical-boundary derivation is allowed only when necessary.** Example: if a confirmed rule says fulfillment requires approval before it can proceed, a criterion that fulfillment does not proceed without that approval is a valid derived boundary. Label such criteria `Derived boundary` and trace them to the originating rule.
14. **Do not manufacture test data.** Avoid example names, IDs, dates, role values, service names, payloads or thresholds unless supplied.
15. **No estimates or test-case implementation.** Do not add story points, test execution steps, automation frameworks or test-environment design.
16. Before returning, perform the mandatory evidence-and-invention audit below.

## Acceptance criterion types

Use the minimum useful set.

### Functional outcome

Observable behavior explicitly supported by the story/requirement.

### Business-rule boundary

A required or prohibited condition established upstream. May include a logically necessary negative boundary when directly implied by the rule.

### Data / audit outcome

Required information or evidence that must be retained, recorded or associated, but without inventing storage mechanisms or data-quality rules.

### Security / compliance constraint

A sourced constraint that applies to the item or integration. Keep it outcome-oriented rather than implementation-oriented.

### Target / quality objective

A non-binding target carried forward for planning/measurement. Do not mix it into mandatory pass/fail criteria.

### Blocked criterion / open question

Use where an acceptance condition cannot be finalized because a Decision Item, Spike, Unknown value or Candidate scope remains unresolved.

## Procedure

### 1. Assess elaboration readiness

State whether acceptance-criteria elaboration is:

- **Ready**;
- **Partially Ready**; or
- **Not Ready**.

If only part of the backlog is ready, proceed with that part and explicitly isolate the rest.

### 2. Build an item/readiness map

Summarize each supplied delivery item by:

- item ID;
- type;
- delivery status;
- upstream requirement IDs;
- whether criteria can be elaborated now.

Do not silently change status.

### 3. Elaborate Ready items

For each Ready item:

- assign stable criterion IDs, preferably `<ITEM-ID>-AC01`, `<ITEM-ID>-AC02`, etc.;
- state one observable condition per criterion;
- cite upstream requirement ID(s);
- identify any criterion that is a `Derived boundary` rather than explicit wording.

Prefer declarative criteria unless Given/When/Then adds clarity without invention.

### 4. Handle Partially Ready / Blocked items

Elaborate only the supported portion.

For unresolved behavior, state:

- what cannot yet be accepted;
- the blocker/decision/spike/open question;
- upstream IDs;
- whether existing criteria remain valid independently.

### 5. Protect Candidate, Target and Deferred items

- Candidate/Conditional work: keep separate and non-committed.
- Targets: list separately as planning/quality objectives.
- Deferred: list separately; no current criteria.

### 6. Check criterion quality

Each criterion should be:

- observable or verifiable;
- unambiguous at the level supported by evidence;
- atomic enough to discuss/test separately;
- free of hidden solution design;
- traceable;
- consistent with upstream status/readiness.

Avoid vague words such as `appropriate`, `properly`, `securely`, `quickly`, `user-friendly`, `valid` or `correct` unless upstream defines what they mean.

### 7. Mandatory evidence-and-invention audit

Before responding, check every criterion and every noun/verb/adjective introduced downstream:

- [ ] Readiness is stated.
- [ ] Delivery/upstream statuses are preserved.
- [ ] Every mandatory criterion traces to a Ready/confirmed-supported item.
- [ ] Every criterion cites its delivery item and upstream requirement(s) where available.
- [ ] Disputed behavior remains blocked; no side was selected.
- [ ] Unknown values remain unknown.
- [ ] Candidate scope remains conditional/non-committed.
- [ ] Targets remain targets, not SLAs or mandatory criteria.
- [ ] Deferred work has no current acceptance criteria.
- [ ] No unsupported UI, notification, error, validation, retry, timeout or workflow behavior was added.
- [ ] No unsupported actor, permission, decision owner or governance authority was added.
- [ ] No architecture/storage/API/protocol/vendor detail was added.
- [ ] Given/When/Then scenarios contain only evidenced preconditions, actions and outcomes.
- [ ] Any negative criterion is a necessary logical boundary of an explicit rule and is labelled `Derived boundary`.
- [ ] No estimates or test-automation design were added.

If any check fails, revise before responding.

## Required default output structure

Unless the user requests another structure, use:

1. **Acceptance-criteria readiness**
2. **Item/readiness map**
3. **Acceptance criteria for Ready items**
4. **Partially Ready / blocked criteria and open questions**
5. **Candidate / conditional acceptance notes**
6. **Planning / quality targets**
7. **Deferred items**
8. **Traceability summary**
9. **Readiness for test-case elaboration**

If a section is empty, write **None identified from supplied decomposition**.

## Acceptance-criteria table

Use where practical:

| Criterion ID | Delivery item | Acceptance condition | Evidence basis | Upstream requirement(s) | Status |
|---|---|---|---|---|---|

`Evidence basis` should normally be `Explicit` or `Derived boundary`.

## Precision examples

| Upstream evidence | Good acceptance criterion | Bad acceptance criterion |
|---|---|---|
| Request must contain application and requested role | Request contains application and requested role | Form highlights missing fields in red |
| Fulfillment requires manager approval first | Derived boundary: fulfillment does not proceed before manager approval | User receives an email when approval is missing |
| Audit record retains outcome and date/time | Outcome and associated date/time are retained | Immutable database audit log records actor IP address |
| Candidate automated integration | Conditional note pending feasibility | System automatically calls REST API and retries three times |
| Target: complete within 4 hours | Planning/quality target: 4 hours | Must complete within 4 hours or fail acceptance |
| Retention period Unknown | Retention-specific criterion blocked; period Unknown | Records retained seven years |
| Disputed rollback rule | Failed-validation criteria blocked pending decision | System automatically rolls back on failure |

## Relationship to other BA capabilities

Expected sequence:

1. `analyze-requirements` — establish evidence, status, ambiguity and readiness.
2. `decompose-requirements` — shape delivery work and isolate blockers.
3. `elaborate-acceptance-criteria` — make sufficiently ready work testable without inventing behavior.
4. Future capability — test/assurance traceability and solution handoff.

These remain separate so each capability can be benchmarked independently.

## Changelog

### 0.1.0

- Initial version.
- Added readiness gating for Ready/Partially Ready/Blocked/Candidate/Target/Deferred/Unknown/Disputed work.
- Added explicit safeguards against invented UI, error handling, notification, workflow, architecture and governance behavior.
- Added traceable criterion IDs and evidence-basis labels.
- Added controlled `Derived boundary` rule for logically necessary negative conditions.
- Added Given/When/Then safety gate and final evidence-and-invention audit.
