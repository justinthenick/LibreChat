---
name: record-architecture-decisions
description: Convert supplied architecture reasoning and decision evidence into ADR-style records while distinguishing approved decisions from recommendations, candidates, disputed options and unknown authority, without inventing a decision, owner, date, rationale or implementation detail.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Record Architecture Decisions

Version: **0.1.0**

## Purpose

Create durable Architecture Decision Record (ADR) artifacts from supplied evidence **only when that evidence supports the stated decision status**.

This Skill records architecture reasoning. It does not grant approval, choose an option on behalf of an unknown authority, or manufacture implementation detail.

## Core principle

**A recommendation is not a decision, and a technically preferred option is not approved architecture unless the source establishes that status.**

## Decision states

Use:

- `Accepted` — explicit evidence establishes the architecture decision was approved/accepted.
- `Recommended` — analysis recommends an option but no approval/acceptance evidence is supplied.
- `Candidate` — option remains under consideration / feasibility review.
- `Disputed` — conflicting positions remain unresolved.
- `Deferred` — decision explicitly postponed.
- `Superseded` — source explicitly replaces an earlier accepted decision.
- `Unknown` — decision status cannot be established.

Do not use `Accepted` based only on an architect's recommendation, implementation activity, meeting attendance, or absence of objections.

## ADR rules

- Preserve the problem/context separately from the chosen/recommended option.
- Record alternatives only if supplied or clearly represented in the source analysis; do not invent straw-man alternatives.
- Consequences must follow from supplied reasoning. Do not invent benefits/risks to make the ADR look complete.
- Preserve architecture-changing Unknowns rather than silently resolving them.
- Decision owner/authority is recorded only when explicitly evidenced. Otherwise use `Unknown`.
- Decision date is recorded only when explicitly evidenced; otherwise `Unknown`.
- Do not invent vendor/product specs, interfaces, protocols, capacity figures, security mechanisms, deployment steps, or procurement requirements.
- A Preference/Target in upstream design remains a Preference/Target in consequences/constraints unless a real decision promotes it.
- If evidence supports only a recommendation, output a `Recommended ADR candidate`, not a final accepted ADR.

## Output contract

For each material decision/recommendation return:

### ADR metadata

- ADR ID;
- title;
- status;
- decision owner/authority;
- decision date;
- source references.

### Context

Problem/objective, relevant constraints and unresolved Unknowns.

### Options considered

Only evidenced options with their evidenced trade-offs.

### Decision / recommendation

State exactly what is accepted/recommended/candidate/disputed/deferred.

### Consequences

Supported positive/negative consequences, dependencies, and downstream implications.

### Open items

Unknowns that could change or invalidate the decision.

### Supersession lineage

Where relevant, state which ADR/decision is superseded and by what explicit evidence.

## Self-check

Before returning, verify every `Accepted` status has explicit acceptance evidence, no unknown owner/date was invented, no alternative/trade-off was manufactured, no Target/Preference was hardened, and no implementation detail exceeds the supplied architecture reasoning.