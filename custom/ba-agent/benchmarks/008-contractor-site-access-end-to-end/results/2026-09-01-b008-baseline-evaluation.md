# Benchmark 008 — Baseline Evaluation

**Model:** `gemini-3.5-flash`  
**Runner result:** `b008-g35-composite-v01-001-gemini-3.5-flash-baseline-01.md`  
**Temperature:** `0.0`  
**Mode:** baseline  
**Result:** **17/100 — Unreliable end-to-end BA behavior**

## Score

| Area | Score |
|---|---:|
| Requirements-analysis fidelity | 13/20 |
| Delivery decomposition and Stage 1 -> 2 handoff | 9/20 |
| Acceptance-criteria discipline and Stage 2 -> 3 handoff | 7/15 |
| Test / assurance derivation and Stage 3 -> 4 handoff | 5/15 |
| Cross-stage traceability and consistency | 10/15 |
| No-invention / process-boundary discipline | 1/10 |
| End-to-end usability and efficiency | 4/5 |
| **Raw** | **49/100** |
| Penalties | **-32** |
| **Final** | **17/100** |

## What the baseline did well

- Preserved the after-hours dispute rather than choosing a side.
- Kept automated Building Access Platform work Candidate, the location pilot Candidate, the response target non-binding and automatic revocation Deferred.
- Maintained broadly stable REQ -> delivery -> AC -> test references for the artifacts it created.
- Correctly noted that the retention period was unknown.

## Material failures

The baseline progressively invented delivery and execution mechanisms that were not in the source:

- decomposed requirements almost one-for-one into `schema & logic`, approval `workflow`, API/protocol integration, database/log capture, reporting/metrics and an automated revocation engine;
- introduced a missing-field rejection rule even though no validation behavior was established;
- converted evidence retention into an `immutable log` implementation;
- invented concrete test values, timestamps, Change IDs, statuses, queues, routing-engine behavior, physical access keys and error/rejection behavior;
- failed to preserve the explicit contractor-onboarding/security-vetting/building-owner/Change-approval process constraint through the downstream chain.

The result is superficially structured but not trustworthy as an end-to-end BA artifact.

## Penalties applied

- **-5** unsupported missing-field validation/rejection behavior.
- **-5** unsupported API/protocol integration design.
- **-5** unsupported database/log storage design.
- **-5** unsupported workflow/queue/routing-engine behavior.
- **-5** concrete test data / execution detail.
- **-5** unsupported immutable-log behavior.
- **-2** additional process-boundary drift is reflected in raw scoring rather than double-penalized.

## Token usage

- Prompt tokens: **882**
- Candidate/output tokens: **3,344**
- Reasoning/thought tokens: **2,262**
- Total tokens: **6,488**

## Decision

The no-agent baseline is **not production-ready**. It establishes a useful control because its dominant failure mode is downstream implementation invention rather than silent resolution of the central dispute.
