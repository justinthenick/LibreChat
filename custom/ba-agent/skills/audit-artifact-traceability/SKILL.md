---
name: audit-artifact-traceability
description: Audit a chain of requirements, delivery items, acceptance criteria, tests, solution/change handoffs, or related artifacts for broken traceability, orphaned or phantom references, status drift, authority drift, requirement-strength drift, contradiction, and lost constraints without rewriting the source artifacts.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Audit Artifact Traceability

Version: **0.1.0**

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
   - distinguish a legitimate stop/block from accidental disappearance.
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

## Output contract

Return:

### 1. Audit verdict

`Pass`, `Pass with observations`, `Needs correction`, or `Traceability unreliable` with a concise reason.

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
- correction required at the semantic level, without rewriting the artifact unless asked.

### 4. Coverage / lineage summary

Summarize confirmed items/constraints that survive, are blocked legitimately, or disappear unexpectedly.

### 5. State-integrity summary

Explicitly list any Candidate/Target/Deferred/Disputed/Unknown promotions or confirm none were found.

### 6. Authority-integrity summary

Explicitly list invented or unsupported authority assignments or confirm none were found.

### 7. Unresolvable audit questions

Only questions required because the supplied artifacts are genuinely ambiguous or incomplete.

## Non-negotiable rules

- Never infer the intended correction when multiple corrections are possible.
- Never treat a downstream statement as proof that the upstream status changed.
- Never promote a missing reference into a new requirement.
- Never invent a Decision Owner, approver, verifier, CAB, Change Authority, architect, tester, or process owner.
- Never classify an absent downstream item as a defect if the upstream state legitimately blocks downstream work.
- Never rewrite the audited artifacts unless the user separately asks for remediation.
- Cite exact IDs and wording from the supplied packet where possible so every finding is inspectable.

## Self-check

Before returning, verify that every Critical/Major finding is demonstrated by the supplied artifacts, every claimed phantom reference is actually unresolved, every status-drift claim compares explicit upstream/downstream states, and no remediation suggestion creates new scope or authority.