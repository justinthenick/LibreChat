# BA Agent Lab — Test Timeline

This ledger records the development and benchmark history for the BA Agent Lab.

**Timezone:** Australia/Sydney (AEST, UTC+10 for 2026-09-01)  
**Timing source:** exact runner metadata from Benchmark 003 onward; Benchmarks 001–002 use GitHub result-recording timestamps because they pre-date the automated NAS runner.

## 2026-09-01

| Local time | Benchmark / event | Execution | Score / result | Decision / note |
|---|---|---|---|---|
| 09:37:28 | B001 Change Validation Automation — `analyze-requirements` v0.1 result recorded | manual / pre-runner | Gemini 3.7 baseline ~78; Skill ~52 | First Skill version regressed; diagnostic work followed. |
| 11:34:03 | B001 — v0.2 results recorded | manual / pre-runner | Gemini 3.6 Skill 84, 86; avg 85 | Material improvement; continue refinement. |
| 12:53:11 | B001 — v0.3 results recorded | manual / pre-runner | 93, 97; avg 95 | Strong result; later hardened into v0.4. |
| 14:11:25 | B002 Major Incident Communications — v0.4 results recorded | manual / pre-runner | Gemini 3.6 57→95; Gemini 3.5 60→81 | `analyze-requirements` v0.4 validated. |
| 15:05:44–15:06:06 | B003 Application Access Request Decomposition — v0.2 | NAS runner; Skill | 99/100 | First runner-native Skill result. |
| 15:27:07–15:27:24 | B003 — baseline | NAS runner; baseline | 70/100 | Control established. |
| 15:32:30–15:33:05 | B003 — v0.2 repeat | NAS runner; Skill | 99/100 | Repeatability confirmed. |
| 16:03:13–16:03:30 | B004 Release Evidence Decomposition — baseline | NAS runner; baseline | 68/100 | Generalization control. |
| 16:03:30–16:03:51 | B004 — v0.2 | NAS runner; Skill | 92/100 | `decompose-requirements` generalized; freeze v0.2. |
| 16:20:04–16:20:16 | B005 Planned Maintenance Acceptance Criteria — baseline | NAS runner; baseline | 96/100 | Strong baseline. |
| 16:20:16–16:20:29 | B005 — acceptance Skill v0.1 | NAS runner; Skill | 98/100 | Retain v0.1; harder benchmark required. |
| 16:40:04–16:40:16 | B006 Bulk Site Import Acceptance Criteria — baseline | NAS runner; baseline | 77/100 | Harder control exposed baseline status leakage. |
| 16:40:16–16:40:37 | B006 — acceptance Skill v0.1 | NAS runner; Skill | 98/100 | Acceptance Skill generalized; freeze v0.1. |
| 17:00:04–17:00:25 | B007 Release Verification Test Cases — baseline | NAS runner; baseline | 97/100 | Very strong baseline. |
| 17:00:25–17:00:48 | B007 — `derive-test-cases` v0.1 | NAS runner; Skill | 95/100 | Subtle defect: closing gaps invented future execution prerequisites. |
| 17:30:04–17:30:22 | B007 — v0.2 | NAS runner; Skill | 93/100 | Focused correction incomplete. |
| 17:40:03–17:40:20 | B007 — v0.3 | NAS runner; Skill | 98/100 | Defect corrected; retain v0.3. |
| 18:40:04–18:40:25 | B008 Contractor Site Access End-to-End — baseline | NAS runner; baseline | 17/100 final | Baseline had major downstream invention / governance issues. |
| 18:40:25–18:40:46 | B008 — Composite BA Delivery Analyst v0.1 | NAS runner; composite single call | 0/100 final after penalties | Better structure but severe unsupported decision-authority invention. |
| 19:40:04–19:40:32 | B008 — Composite BA Delivery Analyst v0.2 | NAS runner; composite single call | 95/100; 10,439 tokens | Governance defect corrected; retain as architecture control. |
| 19:58:33–19:58:48 | B008 specialist pipeline — Stage 1 Requirements Analyst | NAS pipeline runner | success | 5,567 tokens. |
| 19:58:48–19:59:08 | B008 specialist pipeline — Stage 2 Delivery Refinement Analyst | NAS pipeline runner | success | 7,667 tokens. |
| 19:59:08–19:59:30 | B008 specialist pipeline — Stage 3 Assurance Analyst | NAS pipeline runner | success | 10,514 tokens. |
| 19:58:33–19:59:30 | B008 three-specialist pipeline overall | NAS pipeline runner; 3 calls | 53/100; 23,748 tokens | Technically successful but amplified upstream semantic errors; not preferred. |
| 20:30:03–20:30:32 | B009 Service Ownership Update End-to-End — baseline | NAS runner; baseline | 49/100 | Independent architecture control. |
| 20:30:32–20:31:07 | B009 — Composite BA Delivery Analyst v0.2 | NAS runner; composite single call | 94/100; 10,720 tokens | Generalized successfully; freeze composite v0.2 as preferred BA architecture. |
| 20:37:05 | BA Benchmark Cycle evaluator | ChatGPT scheduled condition watch | no new B010/B011 result yet | Hourly evaluation/development loop remains enabled. |
| 20:40:03–20:40:17 | B010 Solution / Change-Readiness Handoff — baseline | NAS runner; baseline | raw result success | Evaluator score pending at time of ledger creation. |
| 20:40:17–20:40:40 | B010 — `prepare-solution-change-readiness` v0.1 | NAS runner; Skill | raw result success | Evaluator score pending at time of ledger creation. |
| 20:40:49–20:41:12 | B011 Emergency Payment Change ITIL Alignment — baseline | NAS runner; baseline | raw result success | Evaluator score pending at time of ledger creation. |
| 20:41:12–20:41:33 | B011 — `assess-itil-alignment` v0.1 | NAS runner; Skill | raw result success | Evaluator score pending at time of ledger creation. |

## Current architecture decision

- Requirements analysis: `analyze-requirements` v0.4 — validated.
- Decomposition: `decompose-requirements` v0.2 — validated/generalized.
- Acceptance criteria: `elaborate-acceptance-criteria` v0.1 — validated/generalized.
- Test / assurance: `derive-test-cases` v0.3 — retained after focused correction.
- Composite BA Delivery Analyst v0.2 — frozen / preferred architecture after B008 95/100 and B009 94/100 with zero penalties.
- Three-specialist pipeline — retained as experimental infrastructure, not preferred after B008 53/100 at 23,748 tokens.
- Active isolated capability tracks: Solution / Change-Readiness (B010) and ITIL 4 alignment/readiness (B011).

## Timing observations

From the first runner-native B003 execution at 15:05:44 through B011 completion at 20:41:33, the lab advanced for about **5h 36m elapsed**. Individual Gemini calls are generally **12–35 seconds**; most elapsed time is benchmark design, scoring, Skill correction, GitHub/NAS polling and evaluator cadence rather than model execution.

The NAS worker is the fast execution loop; the ChatGPT `BA Benchmark Cycle` is the slower evaluation/development loop. This ledger should be updated whenever a benchmark is evaluated or an architecture/version decision is made.
