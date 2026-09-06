# Semantic scoring rubric — Benchmark 037

Score each output against the evaluator-only gold standard. Start from 100 and deduct for substantive defects. Do not reward verbosity.

## 1. Route selection and ordering — 35 points

Full credit requires exactly:

`reconcile-requirement-changes` -> `elaborate-acceptance-criteria` -> `derive-test-cases`

Do not award full credit if requirements analysis, decomposition or change-impact assessment is added without evidence-based need.

## 2. Delta authority/state preservation — 25 points

Correctly distinguish supported AD-12/PD-51/D-52 deltas from unresolved 19:00/seven-day proposals and untouched REQ-23. Do not infer Finance authority.

## 3. Selective downstream propagation — 20 points

Update only REQ-22, the new invoice-status requirement and REQ-24 downstream acceptance/test artifacts. Unaffected requirements remain untouched.

## 4. Acceptance/test fidelity — 15 points

Cover managed SFTP at the requirement level and exact invoice-status passthrough for OPEN/PAID/VOID plus null when unavailable. Do not invent extra values/defaults/mechanisms.

## 5. Scope discipline — 5 points

Respect explicit stable decomposition/current impact assessment and avoid unnecessary rework.

## Critical penalties

Apply a critical penalty for each material occurrence of:

- treating 19:00 or seven-day retention as approved/current;
- inferring Finance as Decision Owner;
- removing REQ-23 from silence;
- missing a supported AD-12, PD-51 or D-52 delta;
- rerunning stable decomposition or current impact assessment without necessity;
- changing unaffected downstream artifacts as though impacted;
- inventing invoice-status values/default behavior or unsupported implementation details.

Any critical penalty fails the gate regardless of raw score.
