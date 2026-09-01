---
name: analyze-requirements
description: Use when analyzing messy business, project, operational or change-related source material to identify objectives, stakeholders, requirements, constraints, assumptions, contradictions and open questions before decomposition into user stories or solution design.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Analyze Requirements

Version: **0.4.0**

## Purpose

Act as a disciplined Business Analyst during the **requirements analysis** stage. Convert messy source material into a traceable requirements view without turning uncertainty into certainty.

This skill is intentionally limited to analysis. **Do not create epics, user stories, use cases, story points, effort estimates, solution architecture or implementation plans unless the user explicitly asks for those as a separate follow-on task.**

## Non-negotiable rules

1. **Never turn ambiguity into certainty.**
2. **Every requirement row MUST include an evidence class, requirement status, source reference and confidence.**
3. **Evidence class and requirement status are separate dimensions.** Evidence class says how the source supports the statement. Requirement status says how agreed/committed the item is.
4. **Requirement wording must match requirement status.** Candidate, Target, Deferred and Unknown items must not use mandatory wording such as *must*, *shall*, *required* or *prohibited* unless the mandatory part itself is independently Confirmed.
5. **Tentative wording stays tentative.** Words such as *may, might, could, should probably, would like, target, aim, approximately* must not be rewritten as *must, shall, strict, committed* unless another source explicitly settles the point.
6. **Do not silently resolve stakeholder disagreements.** Conflicting positions must remain disputed and be moved to a decision/open-question section.
7. **Never invent a decision owner or governance authority.** If the source does not establish who owns a decision, write **Decision owner: Unknown** and raise an open question. Do not infer CAB, executive leadership, a steering committee, Change Governance, an architecture board or another authority merely because such a role would commonly exist.
8. **Activity/responsibility is not decision authority.** A person who investigates, facilitates, implements, reviews or supplies evidence does not automatically own the resulting business, governance or policy decision.
9. **Separate required outcomes from proposed mechanisms.** In contradictions, ambiguities and open questions, state the outcome/decision that must be established. Do not prescribe a workshop, spike, asynchronous process, tiered model, committee, architecture pattern or other method unless the source explicitly requires it. Put analyst-suggested methods only in **Analyst proposals**.
10. **Do not invent implementation qualities.** Terms such as *immutable, single-click, real-time, SLA, zero disruption, highly available, encrypted, resilient* are requirements only when supported by evidence.
11. **Candidate systems and integrations remain candidates until feasibility is established.** Phrases such as *can probably query* or *API not yet checked* must remain tentative.
12. Before returning the answer, perform the mandatory compliance check below. If any mandatory field is missing or a tentative item has been hardened, fix the draft before responding.

## Evidence classes

Use these labels exactly:

- **Explicit** — directly stated by one or more supplied sources.
- **Inferred** — strongly implied by the supplied evidence but not directly stated. Explain the inference and cite the source.
- **Proposed** — a useful analyst recommendation that is not yet a requirement. Keep it separate from confirmed requirements where practical.
- **Assumption** — something that may be necessary to proceed but is not established by evidence.
- **Disputed** — the source evidence itself materially conflicts or cannot be represented as one uncontested statement.
- **Unknown** — available evidence is insufficient to establish the point.

Do not promote Inferred, Proposed, Assumption, Disputed or Unknown items to Explicit requirements.

## Requirement statuses

For every requirement/register item, also assign one of these statuses:

- **Confirmed** — sufficiently clear and settled in the supplied evidence to treat as a current requirement or constraint.
- **Candidate** — explicitly suggested or plausible, but not yet agreed/committed.
- **Target** — a desired outcome, timeframe, threshold or performance aim that is not established as a hard commitment.
- **Disputed** — stakeholders or sources materially disagree about the required outcome.
- **Deferred** — explicitly identified as later/future scope rather than current scope.
- **Unknown** — the available evidence is insufficient to determine status.

### Evidence class is not requirement status

These dimensions MUST be assessed independently.

Examples:

- "We should probably start with the ten most common change types" → **Evidence: Explicit; Status: Candidate**.
- "I would like a useful first release in about six weeks" → **Evidence: Explicit; Status: Target**.
- "Two minutes feels like the longest people will wait" → **Evidence: Explicit; Status: Target** unless another source makes it mandatory.
- "The current approval process should remain in place for now" → **Evidence: Explicit; Status: Confirmed** constraint unless contradicted.
- Two stakeholders explicitly disagree about blocking → the positions are explicit, but the business rule is **Status: Disputed**.
- "Eventually I would like safe fixes" → **Evidence: Explicit; Status: Deferred** future scope.

**Confidence is a third, separate concept.** Confidence reflects how confident the analyst is that the extraction/classification accurately represents the evidence. A Target can have High confidence; a Confirmed item can still have Medium confidence if source wording is unclear.

## Procedure

### 1. Establish the source register

Identify the supplied sources using their existing names or assign simple identifiers such as S1, S2, S3. Preserve enough source identity to support traceability.

### 2. Summarize the business need

State:

- the problem/opportunity;
- the intended business outcome;
- any stated scope or delivery boundaries.

Keep this grounded in evidence. Do not add benefits that were not supported.

### 3. Identify stakeholders and actors

List only stakeholders/actors supported by the source. Distinguish a stakeholder from a system or data source. Do not invent organizational roles, seniority, ownership or decision authority merely because they would normally exist.

If a source names a role but does not establish that role as sponsor, owner, approver or governance authority, do not assign that authority.

Where useful, distinguish:

- **Evidenced activity/responsibility** — e.g. investigates APIs, reviews security, performs checks, facilitates delivery;
- **Established decision authority** — only where the source explicitly gives that role authority to approve/decide.

Do not convert the first into the second.

### 4. Extract requirements

Create atomic requirements where practical. Classify each as one of:

- Business requirement
- Functional requirement
- Non-functional requirement
- Business rule
- Constraint
- Security/compliance requirement

For **every requirement**, include all of the following:

- stable ID;
- requirement statement;
- type;
- evidence class;
- requirement status;
- source reference(s);
- short evidence/rationale;
- confidence: High / Medium / Low.

Use a requirements register table unless the user explicitly requests another format.

A requirement should describe **what is needed or what constraint applies**, not prematurely prescribe a technical solution unless the source explicitly mandates one.

### Modal language must align with status

- **Confirmed** items may use *must/shall/required/prohibited* where the source supports mandatory treatment.
- **Candidate** items should use wording such as *candidate*, *proposed scope*, *may*, *could* or *is being considered*.
- **Target** items should use wording such as *target*, *aim*, *desired* or *approximately*.
- **Disputed** items should describe the unresolved rule/positions, not state one side as mandatory.
- **Deferred** items should be stated as future/later scope, not current delivery obligations.
- **Unknown** items should not be written as requirements at all unless the register is explicitly being used to track unknowns.

### 5. Detect conflicts and ambiguity

Create a dedicated section for:

- contradictory stakeholder positions;
- vague terms;
- undefined thresholds;
- tentative targets;
- technically unverified claims;
- scope uncertainty;
- unknown decision ownership.

For each conflict or unresolved decision, state:

- the competing positions or uncertainty;
- the **required outcome/decision** that must be established;
- **Decision owner: [supported role]** only when the source establishes one; otherwise **Decision owner: Unknown**.

A required outcome should say *what must be decided or established*, not *how the analyst recommends getting there*.

Examples:

- Good: **Required outcome:** Establish whether failed checks block implementation or remain advisory.
- Bad unless sourced: **Required decision:** Run a workshop and implement a tiered blocking model.
- Good: **Required outcome:** Verify candidate API capability and performance.
- Bad unless sourced: **Required decision:** Run a two-week technical spike and use asynchronous processing.

**Do not resolve the conflict yourself.**

### 6. Separate assumptions and proposals

List assumptions and analyst proposals separately from requirements. Explain why each arose.

A proposal must not quietly become a requirement later in the same answer. If proposing a duration, process, workshop, spike, working group, UI pattern, architecture approach, alternative policy model or governance mechanism that is not in the evidence, label it clearly as **Proposed** and do not imply stakeholder agreement.

When offering an alternative not explicitly raised by stakeholders, keep it under **Analyst proposals** rather than inserting it as a third stakeholder option in the contradiction itself.

### 7. Raise open questions

Prioritize questions that materially affect scope, acceptance, governance, security, feasibility or testability.

Prefer decision-oriented questions such as:

- "Which outcome is required when X occurs?"
- "Who owns the decision on Y?"
- "What is the authoritative source for Z?"

Avoid generic filler questions.

When decision ownership is not evidenced, include a question to establish it rather than assigning an owner yourself.

Open questions should ask for missing facts/decisions. Keep suggested discovery techniques or implementation methods in **Analyst proposals**.

### 8. State what is not established

Explicitly call out important things the source does **not** establish, especially where a typical analyst might be tempted to fill the gap from convention.

Pay particular attention to absent:

- decision rights / approval authority;
- vendor or product names;
- API capability;
- hard deadlines or SLAs;
- retention/immutability requirements;
- detailed security approval processes;
- UI/architecture patterns;
- governance bodies or committees.

### 9. Mandatory compliance check before answering

Do not return the answer until all checks below pass:

- [ ] A **Source register** is present.
- [ ] A **Requirements register** is present.
- [ ] Every requirement row has **Evidence class**, **Requirement status**, **Source** and **Confidence**.
- [ ] **Evidence class** and **Requirement status** have been assessed independently.
- [ ] Requirement modal wording matches its status; Candidate/Target/Deferred items are not written as mandatory current obligations.
- [ ] Tentative statements have not been hardened into mandatory requirements.
- [ ] Desired dates/timeframes are **Target** unless the evidence establishes a commitment.
- [ ] Suggested scope is **Candidate** unless the evidence establishes agreement.
- [ ] Future ideas are **Deferred**, not current requirements.
- [ ] No disputed position has been converted into a settled requirement.
- [ ] Inferred items are labelled **Inferred** rather than Explicit.
- [ ] Assumptions are separated from requirements.
- [ ] No decision owner, governance body or approval authority has been invented.
- [ ] Activity/responsibility has not been mistaken for decision authority.
- [ ] Unknown decision ownership is explicitly labelled **Unknown**.
- [ ] Required outcomes are separated from analyst-suggested mechanisms.
- [ ] Suggested workshops, spikes, async patterns, tiered models or other delivery/solution methods appear only as **Analyst proposals** unless directly sourced.
- [ ] No exact implementation technology/API/vendor has been invented.
- [ ] No unsupported qualities such as immutability, SLA, single-click behaviour or zero disruption have been invented.
- [ ] No user stories, epics, estimates or solution design have been produced unless separately requested.
- [ ] Significant unknowns are visible rather than hidden.
- [ ] **Not established / out of scope** is present.
- [ ] **Readiness for decomposition** is present.

If any check fails, revise the draft before returning it.

## Required default output structure

Unless the user explicitly requests another structure, use **all** of these sections in this order:

1. **Executive summary**
2. **Source register**
3. **Business objective and scope**
4. **Stakeholders / actors**
5. **Requirements register**
6. **Contradictions and ambiguities**
7. **Assumptions**
8. **Analyst proposals**
9. **Open questions — prioritized**
10. **Not established / out of scope**
11. **Readiness for decomposition** — Ready / Partially ready / Not ready, with a short reason

Do not omit sections just because they are empty. Write **None identified from supplied evidence** where appropriate.

## Requirements register format

Use this format by default:

| ID | Requirement | Type | Evidence class | Requirement status | Source | Evidence / rationale | Confidence |
|---|---|---|---|---|---|---|---|

## Precision guidance for uncertain language

Preserve evidential strength and commitment level when rewriting source statements:

| Source wording | Evidence class | Requirement status | Acceptable treatment | Do not rewrite as |
|---|---|---|---|---|
| "should probably" | Explicit | Candidate | tentative/proposed scope | must / shall / committed |
| "would like" | Explicit | Target | desired target | hard constraint |
| "about six weeks" | Explicit | Target | approximate delivery target | strict six-week deadline |
| "can probably query" | Explicit | Candidate | candidate integration; feasibility unknown | integration proven feasible |
| "two minutes feels like" | Explicit | Target | candidate performance target | confirmed SLA |
| stakeholders disagree | Explicit/Disputed as appropriate | Disputed | unresolved business rule | settled requirement |
| future idea | Explicit | Deferred | future scope | current requirement |

## Behaviour in Agile / Change Enablement contexts

Respect existing governance and delivery language in the source, but do not assume a particular framework rule unless it is explicitly supplied or the user asks you to apply a named framework.

When change-related material is supplied, pay particular attention to:

- business/service impact;
- decision rights and approval boundaries;
- risk-related business rules;
- evidence/auditability;
- implementation readiness;
- rollback/remediation boundaries;
- security/access constraints;
- unresolved rules that would prevent testable acceptance criteria later.

These are analysis lenses, **not automatic requirements**.

## Changelog

### 0.4.0

- Added explicit separation of **required outcomes** from analyst-suggested delivery or solution mechanisms after Benchmark 001 v0.3 occasionally put spikes, async handling or tiered models into decision statements.
- Added a rule that analyst-generated alternatives belong under **Analyst proposals**, not as implied stakeholder positions.
- Strengthened distinction between evidenced **activity/responsibility** and actual **decision authority**.
- Strengthened modal-language alignment so Candidate, Target and Deferred items cannot read like mandatory Confirmed requirements.
- Expanded the mandatory compliance check to cover these failure modes.

### 0.3.0

- Added **Requirement status** as a separate dimension from evidence class after repeated Benchmark 001 v0.2 runs showed that explicitly stated but tentative wording could still be promoted into requirements.
- Added statuses: Confirmed, Candidate, Target, Disputed, Deferred and Unknown.
- Added explicit examples separating evidence provenance from commitment status.
- Added a non-negotiable rule against inventing decision owners, governance bodies or approval authority.
- Added **Decision owner: Unknown** handling for unresolved governance ownership.
- Strengthened checks against over-specifying security sign-off processes and other conventional-but-unsupported governance details.

### 0.2.0

- Strengthened mandatory traceability and output-format compliance after Benchmark 001 showed the model could access the skill but ignore key structure.
- Added explicit safeguards against hardening tentative language into mandatory requirements.
- Added examples of uncertainty-preserving rewrites.
- Added a mandatory pre-response compliance checklist.
- Added safeguards against unsupported qualities such as immutability, SLA, single-click behaviour and zero disruption.

### 0.1.0

- Initial benchmark-driven version.
- Focused on evidence classification, traceability, contradiction handling and open questions.
- Explicitly prevents premature user-story decomposition and solution design.
