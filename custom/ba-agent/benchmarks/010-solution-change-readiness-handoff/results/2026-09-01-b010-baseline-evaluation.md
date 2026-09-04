# Benchmark 010 — Baseline Evaluation

Model: `gemini-3.5-flash`  
Run: `b010-g35-handoff-v01-ab-001-gemini-3.5-flash-baseline-01`  
Execution: 2026-09-01 20:40:03–20:40:17 AEST (14s)  
Tokens: 4,467  
Final score: **65/100**

## Score

| Area | Score |
|---|---:|
| Overall readiness judgment | 15/15 |
| Evidence-package fidelity | 20/20 |
| Unresolved/non-committed discipline | 20/20 |
| Solution/design handoff quality | 13/15 |
| Change-readiness evidence matrix | 17/20 |
| Usability and traceability | 10/10 |
| Raw | **95/100** |
| Penalties | **-30** |
| Final | **65/100** |

## Penalties / defects

- **-10**: invents a CAB-submission path (`transition ... to a Change Coordinator for CAB submission`) not supplied by the packet.
- **-8**: introduces `database storage` as an assumed design consequence of the Unknown retention period.
- **-5**: invents a support-transition/escalation mechanism rather than simply classifying operational-readiness evidence as missing.
- **-5**: invents internal/external communications-plan scope rather than leaving the communications category content unspecified.
- **-2 raw deductions**: minor downstream wording overreach around technical architecture/service mapping.

## Decision

Useful control, but unsafe as a handoff default because it converts missing evidence categories into assumed downstream process/content. No user/NAS blocker.
