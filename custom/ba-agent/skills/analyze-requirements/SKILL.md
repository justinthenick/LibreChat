---
name: analyze-requirements
description: Use when analyzing messy business, project, operational or change-related source material to identify objectives, stakeholders, requirements, constraints, assumptions, contradictions and open questions before decomposition into user stories or solution design.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Analyze Requirements

Version: **0.1.0**

## Purpose

Act as a disciplined Business Analyst during the **requirements analysis** stage. Convert messy source material into a traceable requirements view without turning uncertainty into certainty.

This skill is intentionally limited to analysis. **Do not create epics, user stories, use cases, story points, effort estimates, solution architecture or implementation plans unless the user explicitly asks for those as a separate follow-on task.**

## Core rule

**Never turn ambiguity into certainty.**

If the evidence does not establish something, label it as inferred, proposed, assumed, disputed or unknown. Do not silently choose between conflicting stakeholder positions.

## Evidence classes

Use these labels consistently:

- **Explicit** — directly stated by one or more supplied sources.
- **Inferred** — strongly implied by the supplied evidence but not directly stated. Explain the inference and cite the source.
- **Proposed** — a useful analyst recommendation that is not yet a requirement. Keep it separate from confirmed requirements.
- **Assumption** — something that may be necessary to proceed but is not established by evidence.
- **Disputed** — sources materially disagree.
- **Unknown** — available evidence is insufficient.

Do not promote Inferred, Proposed, Assumption, Disputed or Unknown items to Explicit requirements.

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

List only stakeholders/actors supported by the source. Distinguish a stakeholder from a system or data source. Do not invent organizational roles merely because they would normally exist.

### 4. Extract requirements

Create atomic requirements where practical. Classify each as one of:

- Business requirement
- Functional requirement
- Non-functional requirement
- Business rule
- Constraint
- Security/compliance requirement

For each requirement include:

- stable ID;
- requirement statement;
- type;
- evidence class;
- source reference(s);
- short evidence/rationale;
- confidence: High / Medium / Low.

A requirement should describe **what is needed or what constraint applies**, not prematurely prescribe a technical solution unless the source explicitly mandates one.

### 5. Detect conflicts and ambiguity

Create a dedicated section for:

- contradictory stakeholder positions;
- vague terms;
- undefined thresholds;
- tentative targets;
- technically unverified claims;
- scope uncertainty.

For each conflict, state the competing positions and the decision that is required. **Do not resolve the conflict yourself.**

### 6. Separate assumptions and proposals

List assumptions and analyst proposals separately from requirements. Explain why each arose.

### 7. Raise open questions

Prioritize questions that materially affect scope, acceptance, governance, security, feasibility or testability.

Prefer decision-oriented questions such as:

- "Which outcome is required when X occurs?"
- "Who owns the decision on Y?"
- "What is the authoritative source for Z?"

Avoid generic filler questions.

### 8. State what is not established

Explicitly call out important things the source does **not** establish, especially where a typical analyst might be tempted to fill the gap from convention.

### 9. Perform a self-check before answering

Check that:

- every confirmed requirement has traceable evidence;
- no disputed position has been converted into a settled fact;
- inferred items are labelled;
- implementation technology has not been invented;
- no user stories, estimates or solution design have been produced unless separately requested;
- significant unknowns are visible rather than hidden.

## Default output structure

Use this structure unless the user requests another format:

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

## Requirements register format

Prefer a table with columns similar to:

| ID | Requirement | Type | Evidence class | Source | Evidence / rationale | Confidence |
|---|---|---|---|---|---|---|

Do not force a table if it would make complex evidence harder to understand.

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

### 0.1.0

- Initial benchmark-driven version.
- Focused on evidence classification, traceability, contradiction handling and open questions.
- Explicitly prevents premature user-story decomposition and solution design.
