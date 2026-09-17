---
name: prepare-procurement-specification
description: Convert a sufficiently mature technical solution or purchasing objective into a vendor-neutral procurement specification that preserves Hard minimum, Preference, Target, Candidate and Unknown source strength, performs domain classification, and avoids invented product specs or verification methods.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Prepare Procurement Specification

Version: **0.2.0**

## Purpose

Create a procurement-ready specification from supplied solution/design evidence without turning preferences, targets, candidates, permitted options, acceptable approaches or unknowns into hard requirements.

This Skill defines **what a candidate must or preferably should satisfy**. It does not search the market, recommend products, verify listings, or choose a vendor.

## Core principle

**Procurement strength must not exceed source strength.**

A good specification is precise about what is actually required and equally precise about what is merely preferred, targeted, candidate, acceptable/permitted, or unknown.

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
- `Permitted / acceptable` — a source explicitly allows an option or says it is acceptable, but does not require that option. Record it as a scope note/capability allowance rather than a Hard minimum unless the surrounding evidence independently makes it unavoidable.

Do not infer `Hard minimum` from common practice, best practice, convenience, likely compatibility, or from wording such as `acceptable`, `allowed`, `may`, `can`, `could`, or `is an option`.

## Specification rules

- Preserve the stated objective separately from the proposed implementation mechanism.
- Use vendor-neutral capability language.
- Include exact numbers only when supplied or logically unavoidable from supplied dimensions/interfaces.
- **Preserve comparison strength exactly.** `at least`, `at most`, `within`, `under`, `over`, approximate values and ranges must not be made stricter unless the source supplies a clearance/tolerance/margin.
- Do not invent connector types, protocols, standards, certifications, dimensions, power ratings, materials, tolerances, warranties, support terms, environmental ratings, licensing terms or accessories.
- A preferred feature remains a Preference even if it would reduce implementation risk.
- A Target does not become a contractual minimum merely because it is measurable.
- A Candidate architecture component remains Candidate until the source establishes it.
- An acceptable/permitted option does not become mandatory merely because other options are out of scope.
- Unknown compatibility facts remain Unknown and become verification questions for downstream procurement verification.
- Do not prescribe a validation/test method unless the source requires that method. State the **evidence needed** to establish a sourced eligibility criterion instead.
- **Eligibility relevance gate:** before adding a compatibility/dependency question or evidence field, ask whether its answer can change eligibility, preference/target scoring, or an explicit Unknown under the supplied specification. If not, omit it rather than expanding the procurement checklist.
- Do not assume surrounding installation, electrical, cabling, structural, network, software or operational conditions are present merely because the product would normally need them.
- Do not request secondary specifications (for example wattage, cable length, refresh rate, warranty detail) when the source only needs evidence that a higher-level capability exists.
- Do not name products or vendors unless they are in the supplied evidence, and do not treat a named example as mandatory unless explicitly stated.

## Output contract

Return:

### 1. Procurement objective

Concise outcome to be purchased/enabled.

### 2. Domain classification

Domain and only domain-specific assumptions explicitly supported by the source. If none are supported, state none rather than adding customary installation assumptions.

### 3. Specification register

For each material item include:

- Spec ID;
- requirement/capability;
- strength (`Hard minimum`, `Preference`, `Target`, `Candidate`, `Unknown`, `Deferred`, or `Permitted / acceptable` where useful);
- source reference / source wording;
- rationale limited to supplied design evidence;
- evidence needed from a candidate/vendor to verify the sourced item.

### 4. Compatibility / dependency questions

Only unresolved facts that could materially change candidate eligibility, preference/target assessment, or a supplied Unknown. Do not add installation-context questions by habit.

### 5. Exclusions / deferred scope

Explicitly preserve exclusions and deferred work. An exclusion does not automatically make a mentioned alternative mandatory.

### 6. Downstream procurement handoff

State what `expand-procurement-market` may search for and what `verify-procurement-options` must verify. Unknowns must remain blockers or verification questions rather than silently assumed true. Keep permitted/acceptable options non-mandatory.

## Self-check

Before returning, verify:

1. every Hard minimum is supported by explicit or logically unavoidable evidence;
2. no wording such as `acceptable/permitted/may/can` was promoted into mandatory scope;
3. no Preference/Target/Candidate/Unknown has been hardened;
4. every numeric comparison preserves the source operator/range without an invented margin;
5. every compatibility/dependency question can materially change a sourced eligibility/state decision;
6. no vendor/product was introduced without source support;
7. no verification method or secondary specification was invented;
8. domain classification fits the actual purchase rather than reusing an IT schema by habit;
9. every numeric threshold has a source.

## Changelog

### 0.2.0

- Added `Permitted / acceptable` handling so allowed options are not promoted to Hard minimums.
- Added exact comparison-strength preservation for fit/range boundaries.
- Added an eligibility-relevance gate for dependency questions and evidence fields.
- Prohibited customary installation assumptions and unnecessary secondary product specifications.

### 0.1.0

- Initial vendor-neutral procurement-specification capability.
