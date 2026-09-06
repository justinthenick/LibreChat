# Semantic Benchmark Evaluation

> Evaluator-only artifact. Raw benchmark outputs remain unchanged.

- Semantic job: `sem-a001-generalization-g37-002`
- Benchmark: `Benchmark 032 — A001 Selective Readiness Generalization`
- Evaluator model: `gemini-3.7-flash`
- Baseline final score: **100/100**
- Skill final score: **100/100**
- Gate: **PASS**

## Summary

Both the baseline and dynamic skill orchestration runs achieved perfect scores. The dynamic orchestrator correctly selected the minimum two-Skill route (prepare-solution-change-readiness -> assess-itil-alignment) and preserved all evidence states, policy gates, and uncertainties without hallucination or scope creep.

