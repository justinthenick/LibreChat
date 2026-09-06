# Semantic Benchmark Evaluation

> Evaluator-only artifact. Raw benchmark outputs remain unchanged.

- Semantic job: `sem-a004-dynamic-g37-002`
- Benchmark: `Benchmark 037 — A004 Selective Downstream Delta`
- Evaluator model: `gemini-3.7-flash`
- Baseline final score: **100/100**
- Skill final score: **89/100**
- Gate: **REVISION REQUIRED**

## Summary

Both models selected the optimal skill route and correctly handled governance constraints (rejecting 19:00 and 7-day retention while preserving REQ-23 and keeping Finance authority as Unknown). Baseline achieved full marks by strictly limiting downstream updates to affected artifacts, whereas Skill elaborated downstream ACs and tests for unaffected baseline items.

## Skill defects

1. **major / Selective downstream propagation** — In elaborate-acceptance-criteria and derive-test-cases, Skill generated AC-20-1, AC-21-1, AC-23-1 and TC-20-1, CHK-21-1, TC-23-1 for unaffected baseline items. Correction: Leave unaffected baseline requirements untouched in downstream AC elaboration and test case derivation, updating and creating artifacts only for REQ-22, REQ-24, and the new invoice_status requirement (REQ-25).
