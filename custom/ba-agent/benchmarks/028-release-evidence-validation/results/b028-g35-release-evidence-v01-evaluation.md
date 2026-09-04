# Benchmark 028 Evaluation — Release Evidence Validation v0.1

Evaluator-only record. Raw outputs remain unchanged.

## Run

- Model: `gemini-3.5-flash` (fallback after Gemini 3.7 provider-busy pair)
- Temperature: `0.0`
- Baseline: 2026-09-05 07:28:04–07:28:16 Australia/Sydney, 3,482 total tokens
- Skill v0.1: 2026-09-05 07:28:16–07:28:33 Australia/Sydney, 6,102 total tokens

## Scores

### Baseline — 96/100, zero critical penalties

- A. Deployment / authorization evidence: 20/20
- B. Test / defect evidence: 30/30
- C. Missing / partial evidence discipline: 16/20
- D. Overall conclusion / conflict handling: 20/20
- E. Evidence discipline: 10/10

The baseline correctly distinguishes deployment execution from functional success, preserves T-102/DEF-77 as failed/open, treats rollback execution as Not evidenced, and rejects the coordinator's `fully successful/no issues` claim. Its only material scoring loss is classifying post-deployment service/business health wholly `Not evidenced` even though the supplied infrastructure/health endpoint provide partial technical-health evidence; customer/business transaction health itself remains Not evidenced.

### `validate-release-evidence` v0.1 — 90/100, zero critical penalties

- A. Deployment / authorization evidence: 20/20
- B. Test / defect evidence: 30/30
- C. Missing / partial evidence discipline: 10/20
- D. Overall conclusion / conflict handling: 20/20
- E. Evidence discipline: 10/10

The Skill gives a strong overall verdict and excellent traceability, but it exposes one reusable state-classification defect: the documented rollback procedure exists only as a plan and was not executed, yet the validation matrix classifies `Rollback Capability` as `Not applicable / out of scope`. The correct execution-evidence state is `Not evidenced`; a planned-but-unexecuted activity is neither demonstrated nor automatically out of scope. The Skill also treats service/transaction health as wholly Not evidenced rather than distinguishing partial technical health from unproven customer/business health.

No critical penalty applies because the Skill explicitly says rollback execution is unproven and does not claim it succeeded.

## Decision

Do **not** retain v0.1 for Delivery Assurance composition yet. Create one focused generic v0.2 correction that:

- reserves `Not applicable / out of scope` for explicit scope evidence;
- classifies planned-but-unexecuted evidence as `Not evidenced` for execution;
- permits aggregate conditions such as service health to be `Partially evidenced` when some scoped technical evidence exists while preserving narrower customer/business outcomes as `Not evidenced`.

Then run a same-model Skill-only rerun against this preserved Gemini 3.5 baseline.
