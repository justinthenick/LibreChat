---
name: prepare-implementation-ready-requirements
description: Always-primed BA requirements-lifecycle capability. Execute exactly the requested requirements stage or stages — analysis, delivery decomposition, acceptance criteria, or a combined lifecycle — while preserving evidence, status, uncertainty and traceability without inventing business or solution facts.
always-apply: true
user-invocable: false
disable-model-invocation: true
---

# Requirements Lifecycle

Version: **0.2.1**

## Purpose

This skill is pre-primed for BA Supervisor turns and is the Supervisor's sole requirements-lifecycle capability. The independently benchmarked `analyze-requirements`, `decompose-requirements`, and `elaborate-acceptance-criteria` skills remain reference capabilities in the repository but are intentionally not callable from BA Supervisor.

Do not invoke this skill or those component skills through the `skill` tool. Execute the appropriate stages directly from this already-loaded body.

## Stage selection

Execute **exactly the stage or stages requested by the user**. Do not silently expand scope.

- **Analysis-only** — perform Stage 1 only. Do not create decomposition or acceptance criteria.
- **Decomposition-only** — perform Stage 2 only when suitable analysed requirements are supplied. Do not re-run analysis unless necessary to preserve traceability.
- **Acceptance-criteria-only** — perform Stage 3 only when suitable decomposed items are supplied. Do not create new requirements or backlog scope.
- **Analysis + decomposition** — perform Stages 1 and 2 only.
- **Decomposition + acceptance criteria** — perform Stages 2 and 3 only when adequate upstream analysis is supplied.
- **Full lifecycle** — when the request asks for analysis, implementation-ready/decomposed requirements, and acceptance criteria, perform Stages 1, 2 and 3 in one consolidated response.

Do not stop between already-requested stages to ask whether to continue. A missing decision is not automatically a reason to stop; preserve it as Unknown/Candidate/Decision Item and continue at the highest solution-neutral abstraction the evidence supports.

## Core principle

Continue as far as the supplied evidence defensibly permits while keeping every unresolved fact unresolved. Implementation-ready does not mean inventing implementation detail. Acceptance-ready does not mean deciding unknown business rules. Plausibility, common practice and likely architecture are not evidence.

## Evidence-boundary rule

Only surface a gap, decision, dependency, risk, assumption, open question, constraint, validation rule or acceptance condition when it arises directly from supplied evidence or is logically necessary to preserve an explicit sourced condition.

Do **not** introduce adjacent engineering or governance concerns merely because they are commonly relevant. In particular, unless the source establishes them, do not introduce invalid/missing/duplicate ID handling, batch/list limits, item eligibility rules, permission models, retry/error semantics, audit/logging, performance targets, governance ownership, approval authority, UI mechanics, API contracts, endpoint schemas, status codes or response payloads — not even as Open Questions, Decision Items, Candidate scope, Not Established items, Risks, Dependencies or conditional acceptance criteria.

Absence of evidence is not itself evidence that a topic belongs in scope. When a topic is not raised by the source and is not required to preserve an explicit sourced uncertainty, omit it entirely.

## Non-negotiable evidence rules

1. Never turn ambiguity, inference, common practice or a plausible design into confirmed fact.
2. Use only actors, roles, systems, outcomes, permissions, business rules, constraints, qualities and decision authorities supported by the supplied source. Otherwise use Unknown only when the source itself creates that unresolved dimension.
3. A request for a future capability does not prove the current system lacks every bulk mechanism and does not prove users currently process items one-by-one.
4. Do not invent benefits such as productivity, reduced effort, reduced risk, improved usability or faster processing unless sourced. Do not add a `so that` clause to a user story unless that benefit is evidenced.
5. Do not invent non-functional requirements.
6. Do not manufacture assumptions just to populate an Assumptions section. Do not infer data-model facts such as status fields, uniqueness constraints or identifiers beyond what the source actually establishes.
7. Do not add an **Analyst proposals** section unless the user explicitly asks for recommendations.
8. Never invent UI, API, endpoint, screen, button, form, notification, queue, database, service, protocol, workflow, retry, timeout, error code, batch size, validation rule or other solution mechanism.
9. Never invent approval, governance, CAB, sponsor, Product Owner, administrator, developer, architect or decision owner.
10. Preserve Candidate, Target, Deferred, Disputed and Unknown as non-mandatory unless independently established.
11. Missing information is a gap only when the source makes that missing information material; it is not automatically a blocker or a new topic for investigation.
12. Do not create a Spike, Dependency or Risk simply because a technical unknown or engineering concern is conceivable.
13. A source statement that some items may already be in a target state establishes a condition, not the required outcome for that condition. Do not invent skip/error/idempotent/reporting semantics.
14. Before answering, perform the mandatory compliance check for every requested stage.

## Evidence and status model

Evidence classes: Explicit, Inferred, Proposed, Assumption, Disputed, Unknown.
Requirement statuses: Confirmed, Candidate, Target, Disputed, Deferred, Unknown.
Keep evidence class, status and confidence separate.

# Stage 1 — Requirements analysis

## Procedure

1. Build a compact source register.
2. State the need/outcome only at the level supported by evidence.
3. Identify only sourced stakeholders/actors.
4. Extract atomic requirements where practical.
5. For material requirements include stable ID, statement, type, evidence class, status, source reference, rationale and confidence.
6. Capture only contradictions, ambiguities and unresolved scope explicitly created by the source.
7. State important Not Established items only when they directly bound or clarify sourced scope; do not use this section as a catalogue of ordinary engineering concerns.
8. State readiness for decomposition: Ready / Partially Ready / Not Ready.

## Analysis rules

- Candidate UI/API possibilities remain Candidate/Decision Items, not committed requirements.
- Do not silently turn a condition into its handling rule.
- If the source says some inspections may already be paused, preserve that condition and keep the required outcome Unknown.
- Do not invent assumptions about current workflow, data model, permissions, identifiers or operations.
- Do not create analyst proposals unless explicitly requested.
- Open questions must map to a sourced ambiguity, contradiction or unresolved condition. Do not add invalid-ID handling, batch-size limits, duplicate-ID rules, permission questions, governance ownership or other adjacent concerns unless the source itself raises them.

## Analysis-only default output

1. Executive summary
2. Source register
3. Business objective and scope
4. Stakeholders / actors
5. Requirements register
6. Contradictions and ambiguities
7. Assumptions — write None identified from supplied evidence if none are genuinely necessary
8. Analyst proposals — include only if explicitly requested; otherwise omit
9. Open questions — prioritized and source-linked only
10. Not established / out of scope — source-relevant only
11. Readiness for decomposition

# Stage 2 — Delivery decomposition

## Procedure

1. State decomposition readiness.
2. Build an upstream requirement-status map.
3. Identify the smallest useful capabilities/epics, sparingly.
4. Decompose confirmed observable behaviour.
5. Use User Story only for sourced actor behaviour/value; Enabler/Technical Task only for sourced technical outcomes; Decision Item only for a sourced unresolved choice; Spike, Dependency, Risk or Deferred Item only when genuinely supported.
6. Preserve Candidate and Target items separately from committed/current backlog.
7. Preserve Deferred items outside current delivery scope.
8. Check every cross-reference and upstream trace.

## Decomposition rules

- Do not force every requirement into a User Story.
- Do not invent an actor, benefit, UI, API, endpoint, technical layer or mechanism.
- If a benefit is not evidenced, omit the `so that` clause.
- If UI vs API is unresolved, keep only that sourced channel decision and describe confirmed bulk behaviour solution-neutrally.
- Do not create both UI and API implementation items merely because both are candidate options.
- Do not create feasibility spikes for ordinary unresolved business choices.
- Do not create a performance risk merely because no batch limit is specified.
- Do not create Decision Items for invalid IDs, duplicate IDs, list limits, permissions, governance, eligibility, error handling or other concerns not raised by the source.
- Decision owner stays Unknown only for a sourced decision whose owner is genuinely relevant and unspecified; do not create an ownership question merely to fill a field.
- Partially Ready means decompose the confirmed portion; it does not mean stop.

## Decomposition-only default output

1. Decomposition readiness
2. Upstream requirement-status map
3. Epics / capabilities
4. Current delivery backlog
5. Decision items
6. Spikes / discovery items
7. Dependencies and risks
8. Candidate backlog / conditional scope
9. Deferred / future backlog
10. Traceability summary
11. Readiness for acceptance-criteria elaboration

If a section has no supported content, write **None identified from supplied analysis** rather than inventing work.

# Stage 3 — Acceptance criteria

## Readiness gate

Ready — elaborate criteria to the extent evidence supports them. Partially Ready — elaborate the confirmed portion and isolate only sourced unresolved criteria. Blocked — do not manufacture the unresolved outcome. Candidate/Target/Deferred/Disputed/Unknown retain their upstream status.

## Acceptance-criteria rules

1. Every mandatory criterion must trace to established behaviour.
2. Preserve upstream requirement and delivery status.
3. Do not invent UI interaction, API payloads, endpoints, validation/error behaviour, retries, timeouts, notification mechanisms, permissions, architecture or test data.
4. Use Given/When/Then only when precondition, action and expected outcome are all evidenced. Do not add qualifiers such as valid, eligible, authorized, existing, well-formed or processable unless supplied evidence establishes them.
5. A Derived boundary is allowed only when logically necessary from an established rule; label it explicitly.
6. Already-paused behaviour remains Blocked/Conditional if the source establishes the condition but not its outcome. Do not invent skip/error/idempotent/reporting semantics.
7. Candidate UI/API channels may be noted as unresolved scope; do not create detailed channel-specific criteria or enumerate screens, payloads, status codes, response bodies or feedback mechanics unless established.
8. Do not create acceptance criteria for invalid/missing/duplicate IDs, batch limits, authorization, eligibility, errors or other topics absent from the source.

## Acceptance-criteria-only default output

1. Acceptance-criteria readiness
2. Item/readiness map
3. Acceptance criteria for Ready items
4. Partially Ready / blocked criteria and open questions
5. Candidate / conditional acceptance notes
6. Planning / quality targets
7. Deferred items
8. Traceability summary
9. Readiness for test-case elaboration

# Full-lifecycle output

For a request covering analysis + decomposition + acceptance criteria, return one consolidated answer:

1. Executive summary — source-supported need and key unresolved decisions only
2. Source register
3. Requirements register
4. Decisions / ambiguities / not established
5. Decomposition readiness
6. Implementation-ready delivery backlog — source-supported current work only
7. Decision / discovery items — only genuinely supported unresolved work
8. Acceptance criteria — preserving blocked/conditional states
9. Traceability summary — Requirement → delivery item → acceptance criteria
10. Open questions — only questions directly created by sourced unresolved behaviour or scope

Do not add speculative Assumptions, Analyst Proposals, Risks, Dependencies or Spikes merely to populate sections.

## Mandatory compliance check

Before answering, verify:

- [ ] Exactly the requested stage(s) are produced.
- [ ] Every actor, current-state problem, benefit, rule, quality and authority is source-supported.
- [ ] A requested future capability was not used to invent a current workflow or deficiency.
- [ ] No manufactured assumptions about state fields, ID uniqueness, permissions or architecture were added.
- [ ] No unsolicited Analyst Proposals were added.
- [ ] No UI/API decision was silently made.
- [ ] No already-paused handling behaviour was invented.
- [ ] No batch limit, invalid-ID rule, duplicate-ID rule, eligibility rule, permission model, error behaviour, performance target, logging/audit requirement, governance owner or architecture was introduced unless sourced.
- [ ] No adjacent engineering concern was turned into a gap, Open Question, Decision Item, Not Established item, Risk, Dependency, Candidate scope or conditional AC merely because it is commonly relevant.
- [ ] No speculative Spike, Dependency or Risk was created merely because an engineering concern is conceivable.
- [ ] Candidate/Target/Unknown items were not upgraded to mandatory language.
- [ ] Confirmed behaviour was decomposed when requested even if unrelated downstream details remain unknown.
- [ ] Every backlog item traces upstream.
- [ ] User-story benefits are omitted unless evidenced.
- [ ] Every acceptance criterion traces to established behaviour and does not create new behaviour.
- [ ] For full-lifecycle requests, all requested stages appear in one consolidated answer without an intermediate stop.
- [ ] No requirements-lifecycle `skill` tool call is necessary or requested by these instructions.

If any check fails, revise before responding.
