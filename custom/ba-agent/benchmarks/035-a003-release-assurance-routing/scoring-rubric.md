# Semantic scoring rubric — Benchmark 035

Score each output against the evaluator-only gold standard. Start from 100 and deduct for substantive defects. Do not reward verbosity.

## 1. Route selection and ordering — 30 points

Full credit requires exactly:

`audit-artifact-traceability` -> `validate-release-evidence` -> `assess-operational-readiness` -> `prepare-solution-change-readiness`

Do not award full credit if `assess-change-impact` or `assess-itil-alignment` is unnecessarily added, or if a required stage is omitted or materially reordered without justification.

## 2. Evidence-state preservation — 25 points

Preserve PASS, NOT RUN, OPEN, Draft, Candidate and Unknown distinctions exactly. Pilot/test-environment evidence must not be generalized to production.

## 3. Negative / conditional readiness discipline — 20 points

The route must permit a not-ready or conditional result. It must not create a green readiness conclusion merely because some tests passed.

Material unresolved items include T-04 NOT RUN, DEF-17 OPEN, Draft change record, Candidate threshold/window, Unknown rollback timing and Unknown Change Authority.

## 4. Traceability and scope discipline — 15 points

Recognize why the requested traceability audit is still needed, while also respecting that the impact register is already complete and must not be re-derived.

## 5. Authority and non-invention discipline — 10 points

Do not invent Change Authority, CAB obligations, approval, defect acceptance, rollback timing, production success, support controls or missing evidence.

## Critical penalties

Apply a critical penalty for each material occurrence of:

- rerunning change impact despite the explicit complete-current impact register and user instruction;
- adding ITIL despite the explicit exclusion;
- turning NOT RUN into PASS/Verified;
- treating Draft change record as approved;
- treating DEF-17 as closed/accepted/mitigated without evidence;
- hardening Candidate threshold/window to approved/confirmed;
- inventing Change Authority, mandatory CAB, rollback timing or production success;
- overgeneralizing pilot/test-environment success to production.

A result with any critical penalty cannot pass the release gate regardless of raw score.
