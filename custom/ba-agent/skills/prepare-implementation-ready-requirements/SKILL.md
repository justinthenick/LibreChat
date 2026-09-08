---
name: prepare-implementation-ready-requirements
description: Always-primed BA requirements-lifecycle capability. Execute exactly the requested requirements stage or stages — analysis, delivery decomposition, acceptance criteria, or a combined lifecycle — while preserving evidence, status, uncertainty and traceability without inventing business or solution facts.
always-apply: true
user-invocable: false
disable-model-invocation: true
---

# Requirements Lifecycle

Version: **0.2.0**

## Purpose

This skill is **pre-primed by the runtime** for BA Supervisor turns and is the Supervisor's sole requirements-lifecycle capability.

The three independently benchmarked component skills — `analyze-requirements`, `decompose-requirements`, and `elaborate-acceptance-criteria` — remain in the repository as reference capabilities, but they are intentionally not callable from BA Supervisor. Live regression testing showed that leaving them model-selectable made routing nondeterministic even when the intended lifecycle policy was already in context.

Do **not** invoke this skill or those three component skills through the `skill` tool. Execute the appropriate stage instructions directly from this already-loaded body.

## Stage selection

Execute **exactly the stage or stages requested by the user**. Do not silently expand scope.

- **Analysis-only** — perform Stage 1 only. Do not create decomposition or acceptance criteria.
- **Decomposition-only** — when a suitable analysed requirements view is supplied, perform Stage 2 only. Do not re-run analysis unless necessary to preserve traceability, and do not elaborate acceptance criteria.
- **Acceptance-criteria-only** — when suitable decomposed items are supplied, perform Stage 3 only. Do not create new requirements or backlog scope.
- **Analysis + decomposition** — perform Stages 1 and 2 only.
- **Decomposition + acceptance criteria** — perform Stages 2 and 3 only when adequate upstream analysis is supplied.
- **Full lifecycle** — when the request asks for analysis, implementation-ready/decomposed requirements, and acceptance criteria, perform Stages 1, 2 and 3 in one consolidated response.

Do not stop between already-requested stages to ask whether to continue. A missing decision is not automatically a reason to stop; preserve it as Unknown/Candidate/Decision Item and continue at the highest solution-neutral abstraction the evidence supports.

## Core principle

**Continue as far as the supplied evidence defensibly permits, while keeping every unresolved fact unresolved.**

Implementation-ready does not mean inventing implementation detail. Acceptance-ready does not mean deciding unknown business rules. Plausibility, common practice and likely architecture are not evidence.

## Non-negotiable evidence rules

1. Never turn ambiguity, inference, common practice or a plausible design into confirmed fact.
2. Use only actors, roles, systems, business outcomes, permissions, business rules, constraints, qualities and decision authorities supported by the supplied source. If none are established, write **Unknown** or **None identified from supplied evidence**.
3. Do not invent a current-state problem merely because the user asks to add a future capability. A request to add bulk processing does not prove the current system lacks every bulk mechanism, and it does not prove users currently process items one-by-one.
4. Do not invent benefits such as productivity, reduced effort, reduced risk, improved usability or faster processing unless the source establishes them. Do not add a `so that` clause to a user story unless that benefit is evidenced.
5. Do not invent non-functional requirements such as stability, integrity, security, auditability, resilience, performance, scalability or availability.
6. Do not manufacture assumptions just to populate an Assumptions section. Do not infer data-model facts such as status fields, uniqueness constraints or identifiers beyond what the source actually establishes.
7. Do not add an **Analyst proposals** section unless the user explicitly asks for recommendations. Do not introduce idempotence, batch limits, invalid-ID policy, UI patterns, architecture, workflows or governance as unsolicited proposals.
8. Never invent UI, API, endpoint, screen, button, form, notification, queue, database, service, protocol, workflow, retry, timeout, error code, batch size, validation rule or other solution mechanism.
9. Never invent approval, governance, CAB, sponsor, Product Owner, administrator, developer, architect or decision owner. If authority is not supplied, write **Decision owner: Unknown**.
10. Preserve tentative language. Candidate, Target, Deferred, Disputed and Unknown items must remain non-mandatory unless the source independently establishes a mandatory rule.
11. Missing information is a gap, not automatically a blocker. Do not promote an unknown into a mandatory gate merely because resolving it would be useful.
12. Do not create a Spike, Dependency or Risk simply because a technical unknown or engineering concern is conceivable. Create one only when the supplied evidence establishes genuine feasibility work, an external prerequisite, or a material risk condition.
13. A source statement that some items may already be in a target state establishes a condition, not the required outcome for that condition.
14. Before answering, perform the mandatory compliance check for every requested stage.

## Evidence and status model

Keep these dimensions separate.

### Evidence class

- **Explicit** — directly stated by supplied evidence.
- **Inferred** — strongly implied by supplied evidence but not directly stated; explain the inference.
- **Proposed** — analyst recommendation, only when the user asks for recommendations.
- **Assumption** — necessary but unestablished premise; use sparingly and never to create committed downstream scope.
- **Disputed** — supplied sources materially conflict.
- **Unknown** — insufficient evidence.

### Requirement status

- **Confirmed**
- **Candidate**
- **Target**
- **Disputed**
- **Deferred**
- **Unknown**

Evidence class and status are independent. Confidence is a third dimension.

---

# Stage 1 — Requirements analysis

## Purpose

Convert supplied source material into a traceable requirements view without turning uncertainty into certainty.

## Procedure

1. Build a compact source register.
2. State the business need/outcome only at the level supported by evidence. Do not assert an unsupported current-state deficiency.
3. Identify only sourced stakeholders/actors. Activity is not decision authority.
4. Extract atomic requirements where practical.
5. For every material requirement include:
   - stable requirement ID;
   - requirement statement;
   - type;
   - evidence class;
   - requirement status;
   - source reference;
   - short evidence/rationale;
   - confidence: High / Medium / Low.
6. Detect contradictions, ambiguities, unresolved scope and unknown authority.
7. State important items that are **Not established**.
8. State readiness for decomposition: Ready / Partially Ready / Not Ready.

## Analysis rules

- Mandatory wording must align with status.
- Candidate UI/API possibilities remain Candidate/Decision Items, not committed requirements.
- Do not silently turn a condition into its handling rule.
- If the source says `Some inspections may already be paused`, preserve that condition but keep skip/success/error/reporting behaviour Unknown unless supplied.
- Do not invent assumptions about the data model, current workflow, identifiers, permissions or operational process.
- Do not create analyst proposals unless explicitly requested.

## Analysis-only default output

When only Stage 1 is requested, use:

1. **Executive summary**
2. **Source register**
3. **Business objective and scope**
4. **Stakeholders / actors**
5. **Requirements register**
6. **Contradictions and ambiguities**
7. **Assumptions** — write **None identified from supplied evidence** if none are genuinely necessary
8. **Analyst proposals** — include only if explicitly requested; otherwise omit
9. **Open questions — prioritized**
10. **Not established / out of scope**
11. **Readiness for decomposition**

---

# Stage 2 — Delivery decomposition

## Purpose

Shape supported delivery work while preserving upstream status, uncertainty and traceability.

## Procedure

1. State decomposition readiness: Ready / Partially Ready / Not Ready.
2. Build an upstream requirement-status map.
3. Identify the smallest useful capabilities/epics; use sparingly.
4. Decompose confirmed observable behaviour.
5. Use the correct work-item type:
   - **User Story** only for source-supported actor behaviour/value;
   - **Enabler / Technical Task** only for source-supported technical outcomes;
   - **Decision Item** for unresolved business/scope/channel choices;
   - **Spike / Discovery Item** only for genuinely evidenced feasibility unknowns;
   - **Dependency / Risk / Deferred Item** only when supported.
6. Preserve Candidate and Target items separately from committed/current backlog.
7. Preserve Deferred items outside current delivery scope.
8. Check every work-item cross-reference and upstream trace.

## Decomposition rules

- Do not force every requirement into a User Story.
- Do not invent an actor, benefit, UI, API, endpoint, technical layer or mechanism to make a story sound complete.
- If a benefit is not evidenced, omit the `so that` clause.
- If UI vs API is unresolved, keep the channel as a Decision Item and describe confirmed bulk behaviour solution-neutrally.
- Do not create both UI and API implementation items merely because both are candidate options.
- Do not create a feasibility spike just to investigate an ordinary unresolved business choice.
- Do not create a performance risk merely because the request does not specify a batch limit.
- Decision owner stays Unknown unless explicitly established.
- Partially Ready means decompose the confirmed portion; it does not mean stop.

## Decomposition-only default output

When only Stage 2 is requested, use:

1. **Decomposition readiness**
2. **Upstream requirement-status map**
3. **Epics / capabilities**
4. **Current delivery backlog**
5. **Decision items**
6. **Spikes / discovery items**
7. **Dependencies and risks**
8. **Candidate backlog / conditional scope**
9. **Deferred / future backlog**
10. **Traceability summary**
11. **Readiness for acceptance-criteria elaboration**

If a section has no supported content, write **None identified from supplied analysis** rather than inventing work.

---

# Stage 3 — Acceptance criteria

## Purpose

Turn sufficiently ready decomposed work into traceable, testable acceptance conditions without creating new behaviour.

## Readiness gate

- **Ready** — elaborate complete criteria to the extent evidence supports them.
- **Partially Ready** — elaborate the confirmed portion and isolate unresolved criteria.
- **Blocked** — do not manufacture the unresolved outcome.
- **Conditional / Candidate** — keep criteria conditional and non-committed.
- **Target** — keep as a target, not a pass/fail rule unless explicitly binding.
- **Deferred** — do not elaborate as current criteria.
- **Disputed / Unknown** — do not choose an answer.

## Acceptance-criteria rules

1. Every mandatory criterion must trace to established behaviour.
2. Preserve upstream requirement and delivery status.
3. Do not invent UI interaction, API payloads, endpoints, validation/error behaviour, retries, timeouts, notification mechanisms, permissions, architecture or test data.
4. Use Given/When/Then only when precondition, action and expected outcome are all evidenced.
5. A `Derived boundary` is allowed only when logically necessary from an established rule; label it explicitly.
6. Already-paused behaviour remains Blocked/Conditional if the source establishes the condition but not its outcome. Do not invent skip/error/idempotent/reporting semantics.
7. Candidate UI/API channels may be noted as unresolved scope; do not create detailed channel-specific criteria unless the chosen channel and behaviour are established.

## Acceptance-criteria-only default output

When only Stage 3 is requested, use:

1. **Acceptance-criteria readiness**
2. **Item/readiness map**
3. **Acceptance criteria for Ready items**
4. **Partially Ready / blocked criteria and open questions**
5. **Candidate / conditional acceptance notes**
6. **Planning / quality targets**
7. **Deferred items**
8. **Traceability summary**
9. **Readiness for test-case elaboration**

---

# Full-lifecycle output

For a request covering analysis + decomposition + acceptance criteria, return **one consolidated answer**, not three independent essays. Default structure:

1. **Executive summary** — source-supported need and key unresolved decisions only.
2. **Source register**.
3. **Requirements register**.
4. **Decisions / ambiguities / not established**.
5. **Decomposition readiness**.
6. **Implementation-ready delivery backlog** — source-supported current work only.
7. **Decision / discovery items** — only genuinely supported unresolved work.
8. **Acceptance criteria** — grouped by delivery item, preserving blocked/conditional states.
9. **Traceability summary** — Requirement → delivery item → acceptance criteria.
10. **Open questions** — only questions that materially affect unresolved behaviour or scope.

Do not add speculative Assumptions, Analyst Proposals, Risks, Dependencies or Spikes merely to populate sections.

## Mandatory compliance check

Before answering, verify all of the following:

- [ ] Exactly the user-requested requirements stage(s) are being produced; no silent scope expansion.
- [ ] Every claimed actor, current-state problem, benefit, rule, quality and authority is source-supported or explicitly labelled Unknown/Proposed where permitted.
- [ ] A requested future capability was not used to invent a current workflow or current deficiency.
- [ ] No manufactured assumptions about state fields, ID uniqueness, permissions or system architecture were added.
- [ ] No unsolicited Analyst Proposals were added.
- [ ] No UI/API decision was silently made.
- [ ] No already-paused handling behaviour was invented.
- [ ] No batch limit, invalid-ID rule, permission model, error behaviour, performance target, logging/audit requirement or architecture was invented.
- [ ] No speculative Spike, Dependency or Risk was created merely because an engineering concern is conceivable.
- [ ] Candidate/Target/Unknown items were not upgraded to Confirmed or mandatory language.
- [ ] Confirmed behaviour was decomposed when decomposition was requested even if unrelated downstream details remain unknown.
- [ ] Every backlog item traces upstream.
- [ ] User-story benefits are omitted unless evidenced.
- [ ] Every acceptance criterion traces to established behaviour and does not create new behaviour.
- [ ] For full-lifecycle requests, all requested stages appear in one consolidated answer without an intermediate stop.
- [ ] No requirements-lifecycle `skill` tool call is necessary or requested by these instructions.

If any check fails, revise before responding.
