# Benchmark 006 — Baseline Evaluation

**Model:** `gemini-3.5-flash`  
**Runner result:** `b006-g35-ab-v01-001-gemini-3.5-flash-baseline-01.md`  
**Temperature:** `0.0`  
**Mode:** baseline / no Skill  
**Result:** **77/100 — Acceptable experiment**

## Score

| Area | Score |
|---|---:|
| Readiness and status preservation | 13/20 |
| Acceptance-criteria quality | 24/30 |
| Traceability and criterion structure | 15/15 |
| Uncertainty and blocker discipline | 13/15 |
| Target / deferred / process-boundary discipline | 10/10 |
| No-invention and downstream usability | 7/10 |
| **Raw** | **82/100** |
| Penalties | **-5** |
| **Final** | **77/100** |

## Strengths

- Correctly isolated the disputed duplicate-site rule and preserved both stakeholder positions with no decision owner invented.
- Kept Master Site Registry validation and the NSW/Victoria pilot as Candidate/conditional.
- Kept the ten-minute objective as a non-binding Target and recurring imports Deferred.
- Preserved the registry read-only/security constraints.
- Mandatory criteria were consistently traceable to delivery item and upstream REQ IDs.

## Material defect

`AC-02.2` states that **no validation is performed on site name or region values** while upstream REQ-013 says those validation rules are **Unknown / not established**. Unknown validation rules do not establish that validation is absent. This converts uncertainty into a concrete runtime rule and receives the rubric's **-5 unsupported site-name/region validation behaviour** penalty.

The same response later correctly lists OPEN-02 as Unknown, so the output is internally inconsistent on this point.

## Minor issues

- It did not explicitly state the supplied overall acceptance-criteria readiness as `Partially Ready`.
- US-01 expressed the system accepting a bulk submission but omitted the sourced actor (`Data Operations Analyst`) from the criterion.
- US-03 broadened the fallback slightly by saying manual single-site entry remains available independently of bulk-import availability rather than specifically when bulk import is unavailable.

## Decision

Useful baseline, but not production-ready for this benchmark because it turns an Unknown validation area into an asserted behaviour. The case provides a meaningful generalization test for the Skill.
