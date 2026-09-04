# Benchmark 020 — Provisional Skill-Only Evaluation

Job: `b020-g36-solution-design-v03-ab-001`  
Model: `gemini-3.6-flash`  
Skill: `design-technical-solution` v0.3.0  
Comparison status: **provisional — baseline unavailable because Gemini returned provider_busy**

## Score

| Category | Score |
|---|---:|
| Outcome vs mechanism separation | 15/15 |
| Feasibility and evidence accuracy | 20/20 |
| Alternative architecture quality | 25/25 |
| State, failure and operability discipline | 14/15 |
| Unknowns, security and validation discipline | 12/15 |
| Handoff / no unnecessary procurement | 9/10 |
| **Raw / Final** | **95/100** |
| Penalties | **0** |

## Evaluation

The Skill cleanly separates the user's automation objective from the unavailable webhook mechanism and selects the expected polling/adapter architecture on the existing corporate host. It uses the supplied `updated_since`, stable `record_id`, idempotent `external_id` upsert and dual network reachability correctly. It preserves the roughly ten-minute freshness objective, rejects the hourly CSV route as insufficient for that objective, and does not fall back to unnecessary RPA or hardware procurement.

State/recovery reasoning is strong: it keeps a checkpoint/watermark, does not advance it after failed processing, relies on idempotent upsert for safe re-reading, and makes failures observable. The proposed five-minute cadence is explicitly labelled as a target requiring rate-limit validation, so it does not trigger the exact-cadence penalty.

The remaining deductions are precision rather than architectural defects. The answer narrows some implementation choices earlier than necessary (`local state file`, environment-variable credential injection, cron/container daemon examples) and the Unknown register should include mapping/deletion semantics, timestamp ordering edge cases and operational ownership/alerting, not only rate limit, volume and secret storage. It also sketches POST/PUT and 200/201 response details that were not required by the packet, although those details are not used to determine feasibility.

## Decision

**Strong cross-domain evidence for `design-technical-solution` v0.3.0.** The generic evidence-invention problem seen in B019 does not recur as a material architecture failure here. No Skill change is justified from B020 Skill output alone.

A valid baseline is still required before closing the A/B benchmark. If baseline is substantially weaker, retain v0.3 and proceed to a third materially different domain. If baseline is equally strong, B020 still demonstrates that v0.3 is safe in software/integration, but incremental value should be judged across the wider benchmark set rather than forced from this case.
