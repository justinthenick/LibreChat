# Benchmark 011 — Baseline Evaluation

Model: `gemini-3.5-flash`  
Run: `b011-g35-itil-v01-ab-001-gemini-3.5-flash-baseline-01`  
Execution: 2026-09-01 20:40:49–20:41:12 AEST (23s)  
Tokens: 5,420  
Final score: **92/100**

## Score

| Area | Score |
|---|---:|
| Overall alignment/readiness framing | 8/10 |
| Change Enablement assessment | 25/25 |
| Release / deployment distinction | 15/15 |
| Service Configuration Management | 15/15 |
| Policy / stakeholder / guidance separation | 13/15 |
| Readiness dependencies / questions | 8/10 |
| Traceability / usability | 8/10 |
| Raw | **92/100** |
| Penalties | **0** |
| Final | **92/100** |

## Findings

The baseline is already strong. It correctly rejects the false `ITIL requires CAB` claim, keeps the Emergency Change Authority Unknown, separates Change Enablement/Release/Deployment/Configuration Management, preserves the risk assessment, treats the 6.4.1 revert as unagreed, and avoids invented CMDB tooling or security approval.

Deductions are mostly precision issues: it uses local-policy `Non-Compliant` language for the unresolved schedule conflict before the implementation window has actually been finalised, and its next-actions section is slightly more prescriptive about rollback/configuration ownership than necessary.

## Decision

Strong control. Any Skill value must come from cleaner `Not evidenced` semantics, scoped practice mapping, policy-vs-guidance separation and traceability rather than correcting gross ITIL misconceptions.
