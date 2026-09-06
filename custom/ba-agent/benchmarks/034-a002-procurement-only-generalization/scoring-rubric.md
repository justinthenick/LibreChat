# Semantic scoring rubric — Benchmark 034

Score each output against the evaluator-only gold standard. Start from 100 and deduct for substantive defects. Do not reward verbosity.

## 1. Route selection and ordering — 30 points

Full credit requires the exact minimum route:

`prepare-procurement-specification` -> `expand-procurement-market` -> `verify-procurement-options`

Do not award full credit if requirements/NFR/design/ADR stages are unnecessarily added, a required procurement stage is omitted, or market expansion and verification are collapsed.

## 2. Requirement-strength preservation — 20 points

Preserve Hard minimum / Target / Preference / Unknown distinctions exactly.

Especially:
- A$750 is Target.
- 10 weeks is Target.
- >=30% recycled content is Preference.
- upholstery colour is Unknown / non-eligibility.

## 3. Market-expansion discipline — 15 points

Recognize that current coverage is narrow because every supplied candidate came from one incumbent reseller. Require deliberate source/search diversification without inventing newly verified candidate facts.

## 4. Candidate evidence and eligibility discipline — 25 points

Expected conclusions:
- C-01: eligible against supplied Hard minimums.
- C-02: ineligible because 135 kg fails the 150 kg Hard minimum.
- C-03: unresolved / verify because lateral armrest-width adjustment is not evidenced.

Target/Preference misses must not become rejection gates.

## 5. Authority and non-invention discipline — 10 points

Do not infer procurement approval authority, preferred-supplier status, new product facts, mandatory governance, or exact-model capability from absence or generic plausibility.

## Critical penalties

Apply a critical penalty for each material occurrence of:

- hardening a Target or Preference into a Hard minimum/rejection gate;
- treating missing C-03 evidence as confirmed;
- passing C-02 despite its explicit Hard-minimum failure;
- inventing exact product/candidate facts or procurement approval authority;
- inventing verified market candidates during the market-expansion stage;
- bypassing the explicit market-expansion request;
- adding solution architecture/ADR work and materially changing the mature procurement boundary without evidence.

A result with any critical penalty cannot pass the release gate regardless of raw score.
