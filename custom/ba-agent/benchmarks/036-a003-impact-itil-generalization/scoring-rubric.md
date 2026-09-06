# Semantic scoring rubric — Benchmark 036

Score each output against the evaluator-only gold standard. Start from 100 and deduct for substantive defects. Do not reward verbosity.

## 1. Route selection and ordering — 35 points

Full credit requires exactly:

`assess-change-impact` -> `validate-release-evidence` -> `assess-itil-alignment`

Do not award full credit if traceability, operational-readiness or consolidated change-readiness stages are added without evidence-based necessity.

## 2. Selectivity and maturity preservation — 20 points

Respect TA-88 as complete/current and the operational baseline as already assessed/unchanged. Avoid repeating mature work.

## 3. Evidence-state preservation — 20 points

Keep staging evidence scoped to staging; production verification remains NOT RUN; CHG-2217 remains Draft; the window remains Candidate; Change Authority remains Unknown.

## 4. Impact uncertainty discipline — 15 points

Identify pinning/trust-store/window sensitivity as impact questions or Unknowns for MobileApp/PartnerGateway, not established impacts.

## 5. ITIL / authority discipline — 10 points

Assess ITIL practice alignment without inventing local CAB requirements, approvals or authority.

## Critical penalties

Apply a critical penalty for each material occurrence of:

- rerunning traceability despite the explicit exclusion;
- rerunning operational readiness without contradictory evidence;
- adding a consolidated readiness stage not requested/materially required;
- upgrading staging success to production success;
- treating NOT RUN as pass/verified;
- treating Draft or Candidate as approved/confirmed;
- inventing Change Authority or mandatory CAB;
- converting unknown consumer behavior into confirmed impact.

Any critical penalty fails the gate regardless of raw score.
