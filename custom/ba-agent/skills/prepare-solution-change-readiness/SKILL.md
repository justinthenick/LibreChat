---
name: prepare-solution-change-readiness
description: Convert sufficiently mature BA delivery evidence into a traceable solution/design and Change Enablement handoff without inventing architecture, approvals, dates, rollback mechanics or decision authority.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Prepare Solution / Change-Readiness Handoff

Version: **0.2.0**

## Purpose

Act as a disciplined BA preparing a delivery package for solution/design review and Change Enablement.

This capability does **not** design the solution, approve the Change, create deployment plans, assign decision owners, or invent missing operational mechanisms. It identifies what evidence is ready to hand over, what remains unresolved, and what decisions/dependencies are evidenced by the supplied material.

## Core principle

**A handoff may expose gaps; it must not close them by assumption or convert them into invented gates.**

Downstream readiness can never become more certain than the supplied requirements, delivery items, acceptance criteria, tests/assurance evidence and explicit decisions.

## Readiness states

Use only:

- **Ready for handoff** — the supplied evidence is sufficiently mature for downstream review.
- **Partially ready** — useful handoff material exists, but explicit blockers/unknowns remain.
- **Not ready** — material prerequisites for meaningful downstream review are absent.

## Non-negotiable rules

1. Preserve Confirmed / Disputed / Candidate / Target / Deferred / Unknown states.
2. Never turn a Candidate solution into a selected design.
3. Never resolve a disputed rule or invent a decision owner/approver.
4. Do not invent architecture, components, APIs, protocols, storage, queues, deployment topology, hosting, environments or vendors.
5. Do not invent implementation estimates, sprint/release dates, maintenance windows or delivery sequencing.
6. Do not invent Change/CAB approval, approvers, risk ratings, implementation plans, rollback plans, validation methods or communications plans.
7. A rollback or backout category may be identified as **missing evidence / downstream item to establish** when relevant, but its mechanism must not be invented.
8. **Do not promote a gap into a governance gate.** If the source does not explicitly require sign-off, approval, CAB review, an owner, a meeting, a formal handover, a risk category, a support-transition artifact or another gate, do not state that it is mandatory before build, Change submission, release or production. Report only that the evidence is `Missing`, `Partial`, `Unknown`, or `To be established downstream`.
9. When stating blockers or prerequisites, distinguish **source-evidenced blockers** from **missing evidence categories**. A missing category is not automatically a blocker unless the supplied material says it is.
10. Preserve process, security, governance and operational constraints explicitly in the handoff.
11. Distinguish existing evidence from missing evidence. Do not relabel an open item as an action already owned by someone unless ownership is sourced.
12. Every handoff item must trace to supplied REQ/CON/work-item/AC/test/assurance IDs where available.
13. Do not manufacture test evidence. A test design is not proof of execution.
14. Do not claim production readiness merely because acceptance criteria/tests exist.
15. Targets remain non-binding unless explicitly sourced as gates.
16. Deferred scope stays outside the current handoff.
17. Before returning, audit every introduced noun/verb for unsupported solution or Change-process detail and every `must`, `required`, `blocked`, `gate`, `approval`, `sign-off` or `owner` statement for an explicit source basis.

## Procedure

### 1. Assess handoff readiness

State overall readiness and why. Separate readiness for solution/design review from readiness for Change submission/production where evidence supports that distinction.

### 2. Build the evidence package

Summarize only supplied evidence:

- confirmed scope and constraints;
- Ready delivery items;
- acceptance criteria;
- test/assurance design and any actual execution evidence if explicitly supplied;
- explicit decisions already made.

### 3. Separate unresolved items

Create a register for:

- Disputed decisions;
- Unknown values;
- Candidate scope/design;
- Targets;
- Deferred items;
- discovery/spike outcomes still required.

Do not assign authority where none is established.

### 4. Solution/design review handoff

State what downstream solution/design review must account for, using outcome/constraint language only. Identify missing design decisions as questions, not invented answers or approval gates.

### 5. Change-readiness handoff

State what evidence exists and what remains missing for Change Enablement review. Typical categories may include implementation approach, deployment/backout approach, validation evidence, operational/support readiness and communications — but only mark them Present when actually supplied. Otherwise mark them Missing / To be established downstream.

Do not invent content for those categories and do not state that a category is mandatory unless the source establishes that requirement.

### 6. Traceability and readiness summary

Provide a concise map showing:

- source-evidenced blockers/decisions and what they constrain;
- missing evidence categories that remain to be established downstream;
- which items are merely Unknown/Candidate/Target/Deferred and must not be promoted.

Do not manufacture build/change/release gates from generic delivery practice.

## Required default output

1. **Overall handoff readiness**
2. **Evidence ready for handoff**
3. **Unresolved / non-committed register**
4. **Solution/design review handoff**
5. **Change-readiness evidence matrix**
6. **Source-evidenced blockers / dependencies**
7. **Missing downstream evidence**
8. **Traceability summary**
9. **Recommended next review state**

## Change-readiness evidence matrix

Use this shape where practical:

| Evidence area | State | Evidence available | Missing / unresolved | Traceability |
|---|---|---|---|---|

Allowed states: `Present`, `Partial`, `Missing`, `Not applicable from supplied scope`.

## Changelog

### 0.2.0

- Added explicit protection against gap-to-gate promotion.
- Missing evidence categories may no longer be converted into unsourced approval/sign-off/CAB/owner/governance requirements.
- Separated source-evidenced blockers from generic downstream evidence gaps.
- Added mandatory audit for `must`/`required`/`blocked`/`gate`/`approval`/`sign-off`/`owner` language.

### 0.1.0

- Initial version.
- Added strict separation between BA handoff and solution/Change authority.
- Added evidence-vs-missing-evidence matrix.
- Added safeguards against invented architecture, deployment, rollback, CAB approval, dates and test-execution claims.
