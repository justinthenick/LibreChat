---
name: audit-artifact-traceability
description: Audit a chain of requirements, delivery items, acceptance criteria, tests, solution/change handoffs, or related artifacts for broken traceability, orphaned or phantom references, status drift, authority drift, requirement-strength drift, contradiction, and lost constraints without rewriting the source artifacts.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Audit Artifact Traceability

Version: **0.2.0**

## Purpose

Perform an independent assurance review across one or more delivery artifacts. Detect where downstream artifacts no longer faithfully represent upstream evidence.

This Skill audits. It does **not** silently repair, rewrite, re-authorize, or complete the artifacts under review.

## Core principle

**Downstream artifacts may add structure, but they must not add certainty, authority, scope, or implementation detail that the upstream evidence does not support.**

## Audit dimensions

Check all applicable dimensions:

1. **Reference integrity**
   - every material downstream reference resolves to a real upstream ID;
   - no phantom IDs;
   - no duplicate IDs with conflicting meaning;
   - no malformed references that make lineage ambiguous.
2. **Coverage / survival**
   - confirmed requirements and explicit constraints that should survive the workflow remain visible downstream;
   - identify orphan upstream items with no downstream representation where representation is expected;
   - distinguish a legitimate stop/block from accidental disappearance;
   - **execution eligibility and lineage visibility are different questions:** a Deferred, Blocked, Candidate, Disputed or Unknown item may correctly have no committed AC/test/current implementation work, but its state should remain visibly traceable where the downstream artifact represents scope/status. Silent disappearance can therefore be a lineage weakness without implying that committed downstream work is required.
3. **Status integrity**
   - Candidate remains Candidate;
   - Target remains Target;
   - Deferred remains Deferred;
   - Disputed remains Disputed unless supplied evidence resolves it;
   - Unknown remains Unknown.
4. **Authority integrity**
   - source/proposer/sponsor/implementer/reviewer is not silently converted into Decision Owner, approver, CAB, Change Authority, or other governance authority;
   - missing authority remains Unknown unless explicitly evidenced.
5. **Requirement-strength integrity**
   - preferences, aims and targets are not promoted into hard minimums, pass/fail gates or mandatory acceptance criteria;
   - proposed mechanisms are not promoted into confirmed requirements.
6. **Semantic integrity**
   - wording changes do not materially alter scope, actor, trigger, outcome, constraint or condition;
   - contradictions between artifacts are surfaced rather than resolved by assumption.
7. **Assurance integrity**
   - acceptance criteria and tests verify supported behavior rather than inventing UI, validation, errors, data values, environments, tooling, methods or execution prerequisites;
   - missing evidence is not converted into an invented mandatory gate.

## Severity

Use:

- `Critical` — material invented scope/authority, confirmed-vs-noncommitted status promotion, phantom lineage that invalidates assurance, or contradiction that changes delivery meaning.
- `Major` — material lost traceability/constraint/coverage or requirement-strength drift that could change implementation or acceptance.
- `Minor` — reviewability or lineage weakness that does not currently change semantic meaning.
- `Observation` — useful note with no demonstrated defect.

Do not inflate severity merely because a field is absent. Severity reflects demonstrated semantic risk.

## Audit / remediation boundary

An audit finding states **what integrity condition is violated**, not the exact rewrite that should be made.

- State the minimum semantic condition that must be restored, for example: `REQ-02 must remain Candidate unless new compatibility evidence supports promotion` or `DEC-01 decision authority must remain Unknown unless explicit authority evidence is supplied`.
- Do not prescribe a work-item type, acceptance criterion, test case, implementation task, validation method, approval process, governance body, or replacement ID unless the supplied evidence uniquely establishes it.
- A phantom reference must be reported as unresolved. If another existing ID appears semantically similar, it may be noted only as an unverified possible correspondence; never instruct the reader to substitute it without evidence.
- A missing confirmed constraint must remain represented where applicable, but the audit must not automatically require that it become a separate work item, AC and test in every downstream artifact.
- Do not ask `who approved/authorized` an omission or decision unless the source establishes that an approval/authorization event should exist. Where authority is absent, simply state that the authority/owner is not evidenced.

## Output contract

Return:

### 1. Audit verdict

`Pass`, `Pass with observations`, `Needs correction`, or `Traceability unreliable` with a concise reason. Do not pronounce formal compliance, release approval/rejection, or deployment permission unless that authority is explicitly part of the supplied audit criteria.

### 2. Artifact inventory

List the supplied artifacts and their role/order. Do not invent missing artifacts.

### 3. Traceability findings

For each defect provide:

- Finding ID;
- severity;
- source artifact / upstream ID;
- downstream artifact / reference;
- defect type;
- evidence of the mismatch;
- impact on downstream confidence;
- **required semantic state / integrity condition** — what must remain true after remediation, without writing the remediation itself.

### 4. Coverage / lineage summary

Summarize confirmed items/constraints that survive, are blocked legitimately, are intentionally non-executable but remain visible, or disappear unexpectedly. Do not equate legitimate non-execution with permission for an item's status/lineage to disappear.

### 5. State-integrity summary

Explicitly list any Candidate/Target/Deferred/Disputed/Unknown promotions or confirm none were found. Distinguish `Deferred but correctly not executed` from `Deferred lineage silently lost`.

### 6. Authority-integrity summary

Explicitly list invented or unsupported authority assignments or confirm none were found. Do not introduce a governance role/body merely to fill an Unknown.

### 7. Unresolvable audit questions

Only questions required because the supplied artifacts are genuinely ambiguous or incomplete. Frame them as evidence questions, not presumed approval/governance workflows.

## Non-negotiable rules

- Never infer the intended correction when multiple corrections are possible.
- Never treat a downstream statement as proof that the upstream status changed.
- Never promote a missing reference into a new requirement.
- Never invent a Decision Owner, approver, verifier, CAB, Change Authority, architect, tester, or process owner.
- Never require committed downstream work merely because a Deferred/Blocked/Candidate/Disputed/Unknown item remains traceable.
- Never use legitimate non-execution as a reason to ignore silent loss of the upstream item's state/lineage.
- Never rewrite the audited artifacts unless the user separately asks for remediation.
- Cite exact IDs and wording from the supplied packet where possible so every finding is inspectable.

## Self-check

Before returning, verify that every Critical/Major finding is demonstrated by the supplied artifacts, every claimed phantom reference is actually unresolved, every status-drift claim compares explicit upstream/downstream states, Deferred/Blocked items are assessed separately for execution and lineage visibility, and no remediation suggestion creates new scope, authority, artifact structure, implementation steps or validation methods.

## Changelog

### 0.2.0

- Separated execution eligibility from lineage visibility so Deferred/Blocked items can remain non-executable without silently disappearing.
- Replaced prescriptive remediation with minimum semantic integrity conditions.
- Prohibited inferred phantom-ID repairs and automatic work-item/AC/test creation for lost constraints.
- Tightened audit verdicts and evidence questions against invented compliance/release/governance authority.

### 0.1.0

- Initial independent artifact-chain traceability audit.
