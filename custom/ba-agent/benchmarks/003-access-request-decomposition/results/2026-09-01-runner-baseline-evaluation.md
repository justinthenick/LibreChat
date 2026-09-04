# Benchmark 003 — Runner Baseline Evaluation

**Model:** `gemini-3.5-flash`  
**Runner result:** `b003-g35-runner-baseline-001-gemini-3.5-flash-baseline-01.md`  
**Temperature:** `0.0`  
**Skill:** none  
**Result:** **70/100 — Acceptable experiment**

## Score

| Area | Score |
|---|---:|
| Upstream fidelity and readiness | 12/20 |
| Work-item decomposition quality | 17/25 |
| Traceability | 20/20 |
| Uncertainty and blocker handling | 19/20 |
| Target / deferred discipline | 5/5 |
| Structure and downstream usability | 7/10 |
| **Raw** | **80/100** |
| Penalties | **-10** |
| **Final** | **70/100** |

## Strengths

- Preserves Confirmed / Candidate / Target / Disputed / Deferred / Unknown status throughout.
- Correctly creates a Decision Item for the disputed privileged-access approval rule and does not choose a stakeholder position.
- Correctly creates a Spike for unverified automated-provisioning feasibility.
- Keeps CRM / Reporting Portal / Dev Wiki as Candidate pilot scope.
- Keeps the four-business-hour requirement as a Target rather than a hard SLA.
- Keeps automatic deprovisioning Deferred.
- Provides strong item-level traceability across all upstream requirements.
- Does not force every requirement into a user story.

## Main weaknesses

1. **No decomposition-readiness assessment.** The source explicitly states `Partially Ready`, but the response does not state readiness or distinguish what is ready for later acceptance-criteria elaboration.
2. **No Epic / Capability hierarchy.** The answer jumps directly into stories/enablers rather than shaping coherent outcome-level capabilities.
3. **Unsupported downstream design/governance detail.** `RSK-03` says the missing retention period may delay `database schema design and compliance sign-off`. Neither a database/schema design nor a compliance sign-off process is established upstream. This is treated as one serious unsupported downstream design/governance assumption and receives a **-10** penalty rather than double-penalizing the same sentence.
4. Minor precision issues include `direct reports` in the manager story and `integrate with or exist alongside` the HR process, neither of which is explicitly established upstream.

## Clean runner A/B comparison

This baseline uses the same runner path, model ID, temperature, prompt hash and input hash as the v0.2 Skill run.

| Runner mode | Score |
|---|---:|
| Gemini 3.5 Flash — no skill | **70/100** |
| Gemini 3.5 Flash — `decompose-requirements` v0.2 | **99/100** |
| **Improvement** | **+29** |

## Interpretation

The runner-native comparison confirms that the improvement is not merely an artifact of comparing LibreChat manual execution with the direct Gemini runner. v0.2 materially improves readiness framing, capability hierarchy, uncertainty isolation and downstream invention control while preserving the baseline's strong status/traceability discipline.

## Decision

**Retain v0.2 and run one repeatability check before moving to a materially different decomposition benchmark.** Do not tune v0.3 from Benchmark 003 unless the repeat exposes a recurring failure.
