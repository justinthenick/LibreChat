---
name: reconcile-requirement-changes
description: Compare an existing requirements baseline with new meeting notes, emails, decisions or revised artifacts to produce a traceable delta of added, changed, removed, disputed, superseded and still-unknown items without silently overwriting prior evidence or inventing authority.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Reconcile Requirement Changes

Version: **0.2.0**

## Purpose

Reconcile a prior requirements baseline against new evidence so downstream artifacts can be updated selectively and traceably.

This Skill does not rewrite the entire requirements set by default. It identifies what changed, why, and how confidently the change is supported.

## Core principle

**Newer evidence may modify the baseline, but it does not automatically invalidate or supersede older evidence unless the source establishes that authority and intent.**

## Delta classes

Use:

- `Added` — genuinely new item not represented in the baseline.
- `Modified` — same underlying item with a materially changed statement/status/value/boundary.
- `Confirmed unchanged` — new evidence explicitly reaffirms an existing item.
- `Disputed` — new evidence conflicts with the baseline or another current source and no authority resolves it.
- `Superseded` — source explicitly establishes that the previous item/value is replaced.
- `Removed / withdrawn` — source explicitly removes scope/requirement.
- `Deferred` — moved out of current scope by explicit evidence.
- `No reliable delta` — wording differs but material meaning cannot be shown to have changed.

## Rules

- Match items by semantic identity and stable IDs where available; do not rely only on wording similarity.
- Preserve the old baseline statement/status/source alongside the proposed new state.
- A stakeholder saying `we should change X` is not the same as an authorized decision that X changed.
- **Decision authority must be explicit.** Never infer change authority from role/title/sponsorship/meeting chairing/implementation responsibility, from being the consumer of an output, or from being asked to confirm/provide input.
- **Confirmation dependency ≠ Decision Owner.** A source may establish that a team/person must confirm, respond, review, supply evidence, or be consulted before a proposal can progress. Preserve that dependency exactly, but keep `Decision owner: Unknown` unless the packet separately establishes decision authority.
- **Missing approval evidence ≠ authority assignment.** A statement such as `no data-owner approval is supplied` proves only that the cited approval evidence is absent. It does not establish that `Data Owner` is the requirement's Decision Owner unless explicit authority evidence says so.
- Where a proposal is unresolved for lack of confirmation/evidence, use a neutral state such as `blocked pending decision/evidence` or `no baseline change` without inventing who must approve the final requirement.
- If a new note is tentative, preserve tentative language and classify the delta accordingly.
- Do not convert absence from newer notes into removal. Silence is not withdrawal.
- Do not create a new requirement merely to explain an implementation detail unless it is a real outcome/constraint supported by evidence.
- If a value changes (date, threshold, scope, actor, interface, status), identify exactly what changed.
- If the source explicitly supersedes an earlier decision, record the provenance and effective replacement.
- Preserve Deferred/Candidate/Target/Unknown states unless explicit evidence changes them.

## Output contract

Return:

### 1. Reconciliation summary

Counts by delta class and a concise description of material change.

### 2. Delta register

For each item:

- Delta ID;
- baseline ID / new ID where available;
- delta class;
- baseline statement/status/source;
- new evidence statement/status/source;
- authority/evidence basis for the delta — distinguish explicit decision evidence, confirmation dependency, missing evidence, and unknown authority;
- downstream impact (`none`, `review`, `update required`, `blocked pending decision/evidence`) without inventing implementation or approval ownership.

### 3. Conflicts / unresolved decisions

Preserve conflicting positions. Record any sourced confirmation/review dependencies separately. Use exactly `Decision owner: Unknown` unless explicit evidence establishes the authority that can resolve the requirement decision.

### 4. Baseline items not mentioned in new evidence

State that they remain unchanged/untouched unless other evidence changes them; do not treat silence as removal.

### 5. Downstream selective-update handoff

Identify which requirement IDs have a material supported delta and therefore which downstream artifacts may need re-evaluation. For unresolved proposals, state what evidence/decision is still missing without assigning an approval owner. Do not regenerate those artifacts in this Skill.

## Self-check

Before returning, verify:

- no baseline item was removed from silence;
- no stakeholder suggestion became an authorized change without evidence;
- every Superseded/Removed classification has explicit support;
- every material delta preserves both old and new provenance;
- no confirmation/review/input dependency was promoted into Decision Owner authority;
- no absent approval record was used to infer who owns the decision;
- every unresolved owner remains `Unknown` unless explicit authority evidence exists.

## Changelog

### 0.2.0

- Separated source-stated confirmation/review dependencies from Decision Owner authority.
- Prevented missing approval evidence from being used to infer authority.
- Added neutral unresolved handoff states that do not manufacture approval ownership.

### 0.1.0

- Initial traceable requirement-delta reconciliation capability.
