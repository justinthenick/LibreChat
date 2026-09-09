---
name: prepare-implementation-ready-requirements
description: Always-primed BA requirements-lifecycle capability. Execute exactly the requested requirements stage or stages — analysis, delivery decomposition, acceptance criteria, or a combined lifecycle — while preserving evidence, status, uncertainty and traceability without inventing business or solution facts.
always-apply: true
user-invocable: false
disable-model-invocation: true
---

# Requirements Lifecycle

Version: **0.2.4**

## Purpose

This skill is pre-primed for BA Supervisor turns and is the Supervisor's sole requirements-lifecycle capability. The independently benchmarked `analyze-requirements`, `decompose-requirements`, and `elaborate-acceptance-criteria` skills remain reference capabilities in the repository but are intentionally not callable from BA Supervisor.

Do not invoke this skill or those component skills through the `skill` tool. Execute the appropriate stages directly from this already-loaded body. No requirements-lifecycle `skill` tool call is necessary or requested by these instructions.

## Stage selection

Execute **exactly the stage or stages requested by the user**. Do not silently expand scope.

- **Analysis-only** — perform Stage 1 only. Do not create decomposition or acceptance criteria.
- **Decomposition-only** — perform Stage 2 only when suitable analysed requirements are supplied.
- **Acceptance-criteria-only** — perform Stage 3 only when suitable decomposed items are supplied.
- **Analysis + decomposition** — perform Stages 1 and 2 only.
- **Decomposition + acceptance criteria** — perform Stages 2 and 3 only when adequate upstream analysis is supplied.
- **Full lifecycle** — perform Stages 1, 2 and 3 in one consolidated response.

Do not stop between already-requested stages to ask whether to continue. Preserve unresolved source-backed items as Unknown/Candidate and continue at the highest solution-neutral abstraction the evidence supports.

## Core principle

Continue as far as the supplied evidence defensibly permits while keeping every unresolved fact unresolved. Implementation-ready does not mean inventing implementation detail. Acceptance-ready does not mean deciding unknown business rules. Plausibility, common practice and likely architecture are not evidence.

## Source-closure contract — mandatory

Before drafting the answer, derive a **source-atom ledger** from the supplied evidence. A source atom is only something the source actually states or an unresolved dimension the source explicitly creates.

Every substantive output item must close back to at least one source atom or to an upstream item that itself closes to a source atom. This applies to:

- requirements;
- conditions;
- ambiguities;
- Decision Items;
- backlog items;
- acceptance criteria;
- open questions;
- risks, dependencies, assumptions and constraints.

If an item cannot be mapped to a source atom, **omit it**. Do not create it as `Unknown`, `Not Established`, `Candidate`, a question, a risk, a dependency or a future consideration.

### Structured operational source atomization

Treat structured operational sources — spreadsheets, configuration matrices, catalogues, decision tables and equivalent tabular controls — as **first-class evidence**, not background material.

When a structured source explicitly defines materially in-scope operational controls, atomize those controls into the requirements/traceability model rather than merely summarising the table in the source register. This includes, where actually supplied and relevant, booleans or enumerations controlling availability, eligibility, routing, assignment, classification, impact, approval, document flags, risk level, lead time or other explicit operational behaviour.

A source register entry saying that a workbook "contains" a control does **not** count as using that control. If the control materially determines behaviour in scope, it must be represented as a source atom and traced into a requirement/rule or into a sourced unresolved item where another source conflicts with it.

Do not infer extra behaviour from the existence of a column. Preserve only the semantics the source establishes.

### Multiplicity and set-handling rule

A source statement that one actor/item **may be linked or associated with multiple values** establishes multiplicity only. It does not establish union, intersection, precedence, primary selection, prompt-to-select, display-all, access-all, fallback or any other set-handling outcome.

If another sourced rule depends on that association and the multi-value handling outcome is not stated, preserve the multiplicity condition and keep the required handling outcome Unknown where needed to avoid a false confirmed requirement. Do not write acceptance criteria that silently choose one handling policy.

### Naming and field-mapping rule

Different business labels, technical field names, aliases or column identifiers are **not a contradiction merely because the strings differ**. Record both names or their supplied relationship without creating a Disputed requirement unless the evidence establishes incompatible meaning, order, value, cardinality or precedence.

Do not manufacture a source-precedence decision simply because one artifact uses human-readable labels and another uses technical identifiers.

### Target-state abstraction rule

When a source establishes a target event/outcome — for example, an event should trigger a state change — preserve that target at the stated abstraction. Do not create adjacent questions about how the event is detected, which API/service implements it, how exceptions reconcile, or what internal scoring/table structure is required unless the source itself raises those dimensions or the user explicitly asks for design recommendations.

A referenced but underspecified target construct does not by itself create permission to invent its internal design dimensions. Keep the target as Candidate/Target and state only source-created uncertainty.

### Negative-space prohibition

Do not scan for ordinary things the source failed to mention. Absence of evidence is not itself evidence that a topic belongs in scope.

Unless explicitly sourced, do not introduce invalid/missing/duplicate ID handling, batch/list limits, input formats, delimiters, item eligibility, permissions, authorization, atomicity, retry/error semantics, logging, audit, telemetry, performance, availability, governance, ownership, approval, validation, UI mechanics, API schemas, endpoints, payloads, status codes, response bodies or test data.

In particular, **do not introduce invalid/missing/duplicate ID handling** merely because a list of IDs exists in the source.

A generic Not Established section must not be used as an inventory of unspecified engineering topics. If no source-linked absence is needed to prevent a false inference, omit the section entirely.

### Cardinality rule for unresolved dimensions

Open questions and Decision Items must be a one-for-one projection of unresolved dimensions actually created by the source.

If the source creates two unresolved dimensions, output at most those two unresolved dimensions unless a third is independently sourced. Do not split one sourced ambiguity into several adjacent engineering questions.

Do not mention decision ownership, governance or authority anywhere unless the source explicitly raises ownership/governance or the user explicitly asks for it.

### Alternative-channel rule

When the source says the delivery channel is undecided between UI and API-only, represent that as **one** unresolved channel decision. Do not create separate `UI shall...` and `API shall...` candidate requirements. The source establishes alternatives, not two candidate mandates.

### Unknown-outcome rule

When the source establishes a condition but not its required outcome, record only:

- the sourced condition; and
- `Required outcome: Unknown / Not established from supplied evidence`.

Do not enumerate possible outcomes such as skip, no-op, idempotent success, warning, error, rejection, partial success, rollback or status reporting unless the source itself names those alternatives.

Do not rewrite an unresolved condition into mandatory wording such as `the system shall handle ... according to defined business rules`.

## Non-negotiable evidence rules

1. Never turn ambiguity, inference, common practice or a plausible design into confirmed fact.
2. Use only source-supported actors, roles, systems, outcomes, permissions, rules, constraints, qualities and authorities.
3. A request for a future capability does not prove the current system lacks every bulk mechanism and does not prove users currently process items one-by-one.
4. Do not invent benefits. Do not add a `so that` clause to a user story unless that benefit is evidenced.
5. Do not invent non-functional requirements.
6. Do not manufacture assumptions just to populate an Assumptions section.
7. Do not add an **Analyst proposals** section unless the user explicitly asks for recommendations.
8. Never invent UI, API, endpoint, screen, button, form, notification, queue, database, service, protocol, workflow, retry, timeout, error code, batch size, validation rule or other solution mechanism.
9. Never invent approval, governance, CAB, sponsor, Product Owner, administrator, developer, architect or decision owner.
10. Preserve Candidate, Target, Deferred, Disputed and Unknown as non-mandatory unless independently established.
11. Missing information is a gap only when the source makes that missing information material.
12. Do not create a Spike, Dependency or Risk simply because a technical unknown or engineering concern is conceivable.
13. A source statement that some items may already be in a target state establishes a condition, not the required outcome for that condition. Do not invent skip/error/idempotent/reporting semantics.
14. A structured source control that materially governs in-scope behaviour must not disappear after the source register; trace it downstream at the abstraction actually supported.
15. Multiplicity does not establish how multiple associations are combined or presented.
16. Lexical differences between labels and technical field names do not establish a contradiction.
17. A target-state outcome does not create an unsourced implementation-mechanism question.
18. Before answering, apply the source-closure check to every output item.

## Evidence and status model

Evidence classes: Explicit, Inferred, Proposed, Assumption, Disputed, Unknown.
Requirement statuses: Confirmed, Candidate, Target, Disputed, Deferred, Unknown.
Keep evidence class, status and confidence separate.

# Stage 1 — Requirements analysis

## Procedure

1. Build a compact source register.
2. Build the source-atom ledger privately before drafting.
3. For structured operational evidence, atomize materially in-scope control columns/row rules that actually govern behaviour.
4. State the business need only at the level supported by evidence.
5. Extract atomic confirmed requirements from explicit requested behaviour.
6. Preserve explicit source conditions separately from their unknown outcomes.
7. Represent each source-created unresolved choice once.
8. State readiness for decomposition: Ready / Partially Ready / Not Ready.

## Analysis rules

- Candidate UI/API possibilities remain one Candidate/Decision Item, not two candidate requirements.
- Do not silently turn a condition into its handling rule.
- If the source says some inspections may already be paused, preserve that condition and keep the required outcome Unknown.
- If a source says an actor/item may have multiple associations, do not infer union/intersection/display/selection handling.
- Do not classify human-readable labels versus technical field identifiers as Disputed unless their semantics actually conflict.
- Do not invent assumptions about current workflow, data model, permissions, identifiers or operations.
- Open questions must map one-for-one to sourced ambiguity, contradiction or unresolved condition.
- Do not add invalid-ID handling, batch-size limits, duplicate-ID rules, permission questions, governance ownership, atomicity, NFRs or other adjacent concerns unless the source itself raises them.

## Analysis-only default output

1. Executive summary
2. Source register
3. Requirements register
4. Sourced ambiguities / unresolved conditions
5. Readiness for decomposition
6. Open questions — source-linked only

Do not include empty or speculative sections.

# Stage 2 — Delivery decomposition

## Procedure

1. State decomposition readiness.
2. Decompose only confirmed observable behaviour.
3. Use a Decision Item only for a sourced unresolved choice or sourced condition with unknown outcome.
4. Preserve Candidate and Unknown states.
5. Trace every delivery item to a source-backed upstream item.

## Decomposition rules

- Do not invent an actor, benefit, UI, API, endpoint, technical layer or mechanism.
- If a benefit is not evidenced, omit the `so that` clause.
- If UI vs API is unresolved, keep only one sourced channel Decision Item and describe confirmed bulk behaviour solution-neutrally.
- Do not create both UI and API implementation items merely because both are candidate options.
- Do not create Decision Items for invalid IDs, duplicate IDs, list limits, permissions, governance, eligibility, error handling, atomicity or other concerns not raised by the source.
- Do not add Decision Owner fields unless ownership is itself source-relevant.
- Do not create a Decision Item solely to reconcile business labels with technical field names.
- Do not create implementation-mechanism Decision Items around a target outcome unless the source itself makes the mechanism undecided.
- Partially Ready means decompose the confirmed portion; it does not mean stop.

## Decomposition-only default output

1. Decomposition readiness
2. Current delivery backlog
3. Source-backed Decision Items
4. Traceability summary
5. Readiness for acceptance-criteria elaboration

Do not populate speculative sections.

# Stage 3 — Acceptance criteria

## Readiness gate

Ready — elaborate only sourced confirmed behaviour. Partially Ready — elaborate the confirmed portion and isolate only sourced unresolved criteria. Blocked — do not manufacture the unresolved outcome. Candidate/Target/Deferred/Disputed/Unknown retain upstream status.

## Acceptance-criteria rules

1. Every mandatory criterion must trace to established behaviour.
2. Preserve upstream status.
3. Do not invent UI interaction, API payloads, endpoints, validation/error behaviour, retries, timeouts, notification mechanisms, permissions, architecture or test data.
4. Use Given/When/Then only when precondition, action and outcome are evidenced. Do not add qualifiers such as valid, eligible, authorized, existing, active, pausable, well-formed or processable unless supplied evidence establishes them.
5. Do not infer implementation mechanics such as `status is updated`, `state transition`, database changes or matching/lookup behaviour when the source only says the inspections are paused.
6. Already-paused behaviour remains Unknown/Blocked if the source establishes the condition but not its outcome. State only that the outcome is Unknown; do not enumerate hypothetical behaviors.
7. Candidate UI/API scope remains one unresolved channel decision. Do not create detailed channel-specific criteria.
8. Do not create acceptance criteria for invalid/missing/duplicate IDs, batch limits, authorization, eligibility, errors, atomicity or other topics absent from the source.
9. A multi-association fact does not justify ACs that assume all, any, primary, union or intersection handling unless that policy is sourced.
10. Do not elaborate Candidate/Target outcomes into technical detection or implementation mechanics absent from the source.

### Minimal-criterion rule

When the source establishes only `provide a list of inspection IDs` plus `pause those inspections`, the confirmed criterion must stay at that same abstraction:

- **Given** a list of inspection IDs,
- **When** bulk pause is requested for that list,
- **Then** the specified inspections are paused.

Do not add initial-state, validity, eligibility, authorization, error-handling, atomicity or implementation preconditions.

## Acceptance-criteria-only default output

1. Acceptance-criteria readiness
2. Acceptance criteria for source-backed Ready items
3. Source-backed blocked/unknown conditions
4. Traceability summary

# Full-lifecycle output

For a full lifecycle request, return one consolidated answer:

1. Executive summary — source-supported need and source-created unresolved dimensions only
2. Source register
3. Requirements register — confirmed behaviour only; sourced conditions may appear separately with unknown outcome
4. Sourced decisions / ambiguities — one item per source-created unresolved dimension
5. Decomposition readiness
6. Implementation-ready delivery backlog — source-supported current work only
7. Source-backed Decision Items — no speculative discovery inventory
8. Acceptance criteria — minimal, source-closed, preserving blocked/unknown states
9. Traceability summary
10. Open questions — one-for-one with source-created unresolved dimensions

Do not add speculative Assumptions, Analyst Proposals, Risks, Dependencies, Spikes or generic Not Established catalogues merely to populate sections.

## Sparse-source profile

When the source is short and establishes only a small number of facts, **the answer should be correspondingly small**. Completeness means complete traceability to the source, not coverage of every engineering topic.

For a source equivalent to:

- add bulk pause;
- users provide a list of inspection IDs;
- pause those inspections;
- some may already be paused;
- UI vs API-only is undecided;

then the output may contain only:

- confirmed bulk-pause behaviour;
- one already-paused sourced condition with required outcome Unknown;
- one delivery-channel decision;
- decomposition of the confirmed bulk-pause behaviour;
- one minimal confirmed acceptance criterion;
- blocked/unknown notes for the two sourced unresolved dimensions;
- exactly two open questions corresponding to those two unresolved dimensions.

No invalid-ID, batch-size, permission, authorization, atomicity, NFR, audit, ownership, input-format, eligibility or implementation-mechanics topic is permitted for that source.

## Mandatory compliance check

Before answering, verify:

- [ ] Exactly the requested stage(s) are produced.
- [ ] Every substantive output item maps to a source atom or source-backed upstream item.
- [ ] Every actor, current-state problem, benefit, rule, quality and authority is source-supported.
- [ ] Structured operational controls that materially govern in-scope behaviour were atomized and traced, not merely mentioned in the source register.
- [ ] A multi-association/multiplicity statement was not converted into union/intersection/display/selection behaviour without evidence.
- [ ] Human-readable labels versus technical field names were not treated as a contradiction merely because the strings differ.
- [ ] Target-state outcomes were not expanded into unsourced technical-detection, mechanism, reconciliation or internal-design questions.
- [ ] A requested future capability was not used to invent a current workflow or deficiency.
- [ ] No manufactured assumptions were added.
- [ ] No unsolicited Analyst Proposals were added.
- [ ] UI/API alternatives were represented as one unresolved decision, not separate candidate mandates.
- [ ] No already-paused handling behaviour was invented or enumerated as candidate outcomes.
- [ ] No batch limit, invalid-ID rule, duplicate-ID rule, eligibility rule, permission model, error behaviour, atomicity rule, performance target, logging/audit requirement, governance owner or architecture was introduced unless sourced.
- [ ] No adjacent engineering concern was turned into a gap, Open Question, Decision Item, Not Established item, Risk, Dependency, Candidate scope or conditional AC merely because it is commonly relevant.
- [ ] Open questions and Decision Items are one-for-one with unresolved dimensions actually created by the source.
- [ ] Do not mention decision ownership, governance or authority anywhere unless the source explicitly raises ownership/governance or the user explicitly asks for it.
- [ ] A generic Not Established section must not be used as an inventory of unspecified engineering topics.
- [ ] No generic Not Established catalogue was emitted.
- [ ] No speculative Spike, Dependency or Risk was created merely because an engineering concern is conceivable.
- [ ] Do not rewrite an unresolved condition into mandatory wording such as `the system shall handle ... according to defined business rules`.
- [ ] Candidate/Target/Unknown items were not upgraded to mandatory language.
- [ ] Every backlog item traces upstream.
- [ ] User-story benefits are omitted unless evidenced.
- [ ] Every acceptance criterion traces to established behaviour and does not create new behaviour.
- [ ] Do not add qualifiers such as valid, eligible, authorized, existing, active, pausable, well-formed or processable unless supplied evidence establishes them.
- [ ] Do not infer implementation mechanics such as `status is updated`, `state transition`, database changes or matching/lookup behaviour when the source only says the inspections are paused.
- [ ] When the source establishes only `provide a list of inspection IDs` plus `pause those inspections`, the confirmed criterion must stay at that same abstraction.
- [ ] For full-lifecycle requests, all requested stages appear in one consolidated answer without an intermediate stop.
- [ ] No requirements-lifecycle `skill` tool call is necessary or requested by these instructions.

If any check fails, revise before responding.
