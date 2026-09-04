---
name: record-architecture-decisions
description: Convert supplied architecture reasoning and decision evidence into ADR-style records while distinguishing approved decisions from recommendations, candidates, disputed options and unknown authority, without inventing a decision, owner, date, rationale or implementation detail.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Record Architecture Decisions

Version: **0.2.0**

## Purpose

Create durable Architecture Decision Record (ADR) artifacts from supplied evidence **only when that evidence supports the stated decision status and reasoning**.

This Skill records architecture reasoning. It does not grant approval, choose an option on behalf of an unknown authority, manufacture implementation detail, or fill conventional ADR sections with plausible-but-unsourced trade-offs.

## Core principle

**A recommendation is not a decision, and ADR completeness must never exceed evidence completeness.**

A technically plausible consequence, trade-off or governance path is still invented if the source did not establish it.

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
- **Trade-offs/rationale/consequences are evidence fields, not template filler.** Record only reasoning the source supplies or that is a direct restatement of the accepted decision boundary. If a conventional ADR subsection lacks evidence, state `Not evidenced` / omit the subsection rather than supplying architectural common sense.
- Do not infer benefits such as reduced overhead, isolation, scalability, resilience, simplicity, cost, performance, security or operational complexity unless the source explicitly provides that reasoning. A source saying `simplest because existing service owns the boundary and no new component is required` supports exactly that rationale, not every usual advantage/disadvantage of polling or middleware.
- Preserve architecture-changing Unknowns rather than silently resolving them.
- Decision owner/authority is recorded only when explicitly evidenced. Otherwise use `Unknown`.
- Decision date is recorded only when explicitly evidenced; otherwise `Unknown`.
- **Future decision forum is also authority evidence.** For a Recommendation/Candidate with owner `Unknown`, do not add `awaiting Architecture Board`, `requires Security approval`, `pending design authority`, or similar approval-route language unless explicitly supplied.
- Do not invent vendor/product specs, interfaces, protocols, capacity figures, security mechanisms, deployment steps, or procurement requirements.
- A Preference/Target in upstream design remains a Preference/Target in consequences/constraints unless a real decision promotes it.
- If evidence supports only a recommendation, it may be represented as a `Recommended ADR candidate`, but do not force every recommendation/candidate into a standalone ADR. A status-separated recommendation/candidate register is preferable when there is no decision-specific metadata/rationale to record.
- Do not combine unrelated unaccepted recommendations/candidates into one pseudo-decision merely because they concern the same component.

## Output contract

For each **accepted/material decision** return:

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

Only evidenced options. For each option, include only evidenced trade-offs; use `Trade-off evidence: Not supplied` where the option is listed but its trade-off reasoning is absent.

### Decision / recommendation

State exactly what is accepted/recommended/candidate/disputed/deferred.

### Consequences

Only supplied consequences or direct decision-boundary effects. Do not expand the section with customary ADR benefits/risks.

### Open items

Unknowns that could change or invalidate the decision, without assigning a future decision forum/owner unless sourced.

### Supersession lineage

Where relevant, state which ADR/decision is superseded and by what explicit evidence.

### Recommendations / candidates not yet decided

Where the packet contains unaccepted items that do not justify separate ADRs, preserve them in a compact status register containing statement, status, source, Target/Candidate state, owner/authority if explicitly known, and open evidence. Keep them outside the accepted ADR.

## Self-check

Before returning, verify:

- every `Accepted` status has explicit acceptance evidence;
- no unknown owner/date/future decision forum was invented;
- no alternative was manufactured;
- every trade-off/rationale/consequence is traceable to supplied reasoning rather than common architecture knowledge;
- no Target/Preference was hardened;
- no implementation detail exceeds the supplied architecture reasoning;
- no unaccepted items were combined into a pseudo-decision solely to complete an ADR template.

## Changelog

### 0.2.0

- Added explicit protection against ADR completeness/trade-off inflation.
- Kept future decision forums/approval routes Unknown unless sourced.
- Added a non-ADR status register for recommendations/candidates that lack decision evidence.
- Prevented unrelated unaccepted items from being combined into pseudo-decisions.

### 0.1.0

- Initial evidence-backed ADR recording capability.
