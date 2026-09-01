# Benchmark 009 — No-Agent Baseline Evaluation

**Model:** `gemini-3.5-flash`  
**Runner result:** `b009-g35-composite-v02-ab-001-gemini-3.5-flash-baseline-01.md`  
**Temperature:** `0.0`  
**Result:** **49/100 — Structurally useful, but unsafe downstream invention**

## Score

| Area | Raw score |
|---|---:|
| Requirements-analysis fidelity | 17/20 |
| Delivery decomposition and Stage 1 -> 2 handoff | 14/20 |
| Acceptance-criteria discipline and Stage 2 -> 3 handoff | 9/15 |
| Test / assurance derivation and Stage 3 -> 4 handoff | 7/15 |
| Cross-stage traceability and consistency | 11/15 |
| No-invention / process-boundary discipline | 5/10 |
| End-to-end usability and efficiency | 4/5 |
| **Raw** | **67/100** |

## Penalties

- **-5** — invented routing/workflow behavior (`request must be routed`, pending-approval state / authorization-for-execution state).
- **-5** — invented serious current-scope actors/authority language around an `authorized user` / coordinator for manual update handling.
- **-5** — invented concrete test data (APP-9901, Alice Smith, Network Operations, a specific date/reason).
- **-3** — material downstream traceability weakness: tests trace to ACs, but do not consistently carry the full AC -> delivery item -> REQ/CON chain required by the benchmark.

**Final: 49/100.**

## Findings

The baseline preserves most source statuses reasonably well: emergency approval stays disputed, Service Registry automation stays Candidate, quarterly recertification stays Deferred, the one-business-day objective remains non-binding, and retention remains Unknown.

The failure is downstream discipline. It converts sourced boundaries into implementation-like workflow language, adds manual-update actors/confirmation behavior, uses concrete invented test data, and weakens end-to-end traceability. It also describes request fields as mandatory even though the source only establishes that the request records those data elements.

No emergency-approval side is selected and Candidate Service Registry automation is not committed, so the baseline avoids the benchmark's most severe governance failures. It is nevertheless not production-ready.

## Token usage

- Prompt: **941**
- Candidate/output: **2,665**
- Reasoning/thought: **2,996**
- Total: **6,602**
