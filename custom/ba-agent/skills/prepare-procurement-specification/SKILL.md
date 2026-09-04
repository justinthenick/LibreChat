---
name: prepare-procurement-specification
description: Convert a sufficiently mature technical solution or purchasing objective into a vendor-neutral procurement specification that preserves Hard minimum, Preference, Target, Candidate and Unknown source strength, performs domain classification, and avoids invented product specs or verification methods.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Prepare Procurement Specification

Version: **0.1.0**

## Purpose

Create a procurement-ready specification from supplied solution/design evidence without turning preferences, targets, candidates or unknowns into hard requirements.

This Skill defines **what a candidate must or preferably should satisfy**. It does not search the market, recommend products, verify listings, or choose a vendor.

## Core principle

**Procurement strength must not exceed source strength.**

A good specification is precise about what is actually required and equally precise about what is merely preferred, targeted, candidate, or unknown.

## Step 1 — Domain classification

Classify the procurement domain before building the specification. Use the most specific supported class, for example:

- IT compute / storage;
- networking / connectivity;
- audiovisual;
- appliance / electrical;
- furniture / physical fit-out;
- software / SaaS;
- professional service;
- mixed / other.

If the packet spans materially different domains, state that and separate domain-specific spec sections. Do not force IT-style fields onto non-IT goods.

## Requirement strength

Use these states:

- `Hard minimum` — explicitly mandatory or logically unavoidable for the stated solution to function.
- `Preference` — explicitly preferred or desirable but not mandatory.
- `Target` — desired quantitative/quality goal that is not established as a hard pass/fail threshold.
- `Candidate` — proposed mechanism/spec that remains subject to decision or feasibility.
- `Unknown` — required procurement fact/decision is not established.
- `Out of scope / Deferred` — explicitly excluded from this procurement.

Do not infer `Hard minimum` from common practice, best practice, convenience, or likely compatibility.

## Specification rules

- Preserve the stated objective separately from the proposed implementation mechanism.
- Use vendor-neutral capability language.
- Include exact numbers only when supplied or logically unavoidable from supplied dimensions/interfaces.
- Do not invent connector types, protocols, standards, certifications, dimensions, power ratings, materials, tolerances, warranties, support terms, environmental ratings, licensing terms or accessories.
- A preferred feature remains a Preference even if it would reduce implementation risk.
- A Target does not become a contractual minimum merely because it is measurable.
- A Candidate architecture component remains Candidate until the source establishes it.
- Unknown compatibility facts remain Unknown and become verification questions for downstream procurement verification.
- Do not prescribe a validation/test method unless the source requires that method. State the **evidence needed** to establish compliance instead.
- Do not name products or vendors unless they are in the supplied evidence, and do not treat a named example as mandatory unless explicitly stated.

## Output contract

Return:

### 1. Procurement objective

Concise outcome to be purchased/enabled.

### 2. Domain classification

Domain and any domain-specific assumptions that are explicitly supported.

### 3. Specification register

For each item include:

- Spec ID;
- requirement/capability;
- strength (`Hard minimum`, `Preference`, `Target`, `Candidate`, `Unknown`, `Deferred`);
- source reference / source wording;
- rationale limited to supplied design evidence;
- evidence needed from a candidate/vendor to verify the item.

### 4. Compatibility / dependency questions

Only unresolved facts that could materially change candidate eligibility or required specification.

### 5. Exclusions / deferred scope

Explicitly preserve exclusions and deferred work.

### 6. Downstream procurement handoff

State what `expand-procurement-market` may search for and what `verify-procurement-options` must verify. Unknowns must remain blockers or verification questions rather than silently assumed true.

## Self-check

Before returning, verify:

1. every Hard minimum is supported by explicit or logically unavoidable evidence;
2. no Preference/Target/Candidate/Unknown has been hardened;
3. no vendor/product was introduced without source support;
4. no verification method was invented;
5. domain classification fits the actual purchase rather than reusing an IT schema by habit;
6. every numeric threshold has a source.