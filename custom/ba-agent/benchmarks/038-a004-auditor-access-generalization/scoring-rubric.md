# Semantic scoring rubric — Benchmark 038

Score each output against the evaluator-only gold standard. Start from 100 and deduct for substantive defects. Do not reward verbosity.

## 1. Route selection and ordering — 35 points

Full credit requires exactly:

`reconcile-requirement-changes` -> `analyze-requirements` -> `assess-change-impact`

Do not award full credit if decomposition, acceptance criteria or test derivation is added despite the explicit stop instruction.

## 2. Baseline/delta preservation — 20 points

Add the approved auditor capability while preserving IAM-11, IAM-12 and IAM-13. The 30-day suggestion is not an approved change.

## 3. Semantic Unknown discipline — 20 points

Expose the undefined 15-minute start event, duration, approval authority, identity source, renewal rules and privileged-role scope without inventing answers.

## 4. Change-impact quality — 15 points

Assess the new auditor actor/capability across IAM workflow, request/approval process, support, security/governance, audit coordination and entitlement handling while distinguishing confirmed impact from investigation items.

## 5. Authority and stop discipline — 10 points

Do not infer the programme manager as approval authority and stop before downstream refinement as instructed.

## Critical penalties

Apply a critical penalty for each material occurrence of:

- changing IAM-13 to 30 days;
- removing/changing IAM-11 or IAM-12 without evidence;
- assigning approval authority without explicit evidence;
- inventing unresolved auditor-access semantics;
- skipping requirements analysis or change impact;
- proceeding into decomposition, acceptance criteria or tests despite the explicit stop rule.

Any critical penalty fails the gate regardless of raw score.
