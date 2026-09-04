# BA Agent Lab — Test Timeline

This ledger records the development and benchmark history for the BA Agent Lab.

**Timezone:** Australia/Sydney (AEST, UTC+10 for 2026-09-01/02)  
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
| 20:40:03–20:40:17 | B010 Solution / Change-Readiness Handoff — baseline | NAS runner; baseline; 14s | **65/100**; 4,467 tokens | Strong raw structure but unsafe downstream process/content invention. |
| 20:40:17–20:40:40 | B010 — `prepare-solution-change-readiness` v0.1 | NAS runner; Skill; 23s | **75/100**; 8,661 tokens | Better evidence discipline, but reusable gap-to-gate promotion invented sign-off/approval requirements. Do not retain v0.1. |
| 20:40:49–20:41:12 | B011 Emergency Payment Change ITIL Alignment — baseline | NAS runner; baseline; 23s | **92/100**; 5,420 tokens | Strong baseline; minor policy/readiness precision issues. |
| 20:41:12–20:41:33 | B011 — `assess-itil-alignment` v0.1 | NAS runner; Skill; 21s | **98/100**; 7,057 tokens | Retain v0.1 for generalization; zero penalties. |
| 21:27 | B010/B011 evaluator decision | ChatGPT evaluation | B010 v0.1 rejected; B011 v0.1 retained | Created B010 handoff v0.2 focused only on gap-to-gate promotion. Created B012 planned certificate/proxy ITIL benchmark. |
| 21:27 | Queue update | GitHub-controlled NAS jobs | `b010-g35-handoff-v02-002` Skill-only + `b012-g35-itil-v01-ab-001` baseline/Skill | Three model calls queued; no NAS infrastructure change required. |

## 2026-09-02

| Local time | Benchmark / event | Execution | Score / result | Decision / note |
|---|---|---|---|---|
| 00:00:04–00:00:29 | B010 — `prepare-solution-change-readiness` v0.2 focused rerun | NAS runner; Skill; 25s | **100/100**; 9,609 tokens | Gap-to-gate defect removed with zero penalties. Retain v0.2; stop tuning B010. |
| 00:00:36–00:00:53 | B012 Planned Certificate Change ITIL Alignment — baseline | NAS runner; baseline; 17s | **94/100**; 5,211 tokens | Strong control; minor overstatement of local readiness obligations. |
| 00:00:53–00:01:11 | B012 — `assess-itil-alignment` v0.1 | NAS runner; Skill; 18s | **96/100**; 6,759 tokens | Strong generalization but reusable gap-to-gate variant: recovery/configuration gaps promoted to unsourced pre-authorisation requirements. Do not freeze yet. |
| 00:39 | Evaluator / architecture decision | ChatGPT evaluation + GitHub updates | B010 v0.2 retained; ITIL v0.2 created | B013 vendor-export handoff generalization created. ITIL v0.2 adds only protection against promoting relevant `Not evidenced` gaps into mandatory local gates. |
| 00:39 | Queue update | GitHub-controlled NAS jobs | `b012-g35-itil-v02-002` Skill-only + `b013-g35-handoff-v02-ab-001` baseline/Skill | Three model calls queued; no NAS infrastructure change required. |
| 00:40:05–00:40:23 | B012 — `assess-itil-alignment` v0.2 focused rerun | NAS runner; Skill; 18s | **100/100**; 7,303 tokens | Gap-to-gate variant removed with zero penalties. Retain v0.2; ITIL track generalized enough for composition planning. |
| 00:40:29 | B013 Vendor Export Handoff — baseline attempt | NAS runner; baseline; 0s | **quota_blocked**; no model output | Gemini free-tier daily request limit (20 requests/model/project) exhausted. B013 baseline and Skill comparison cannot proceed until provider quota becomes available. |
| 01:32 | B012/B013 evaluator decision | ChatGPT evaluation + GitHub updates | B012 v0.2 retained; B013 blocked | ITIL isolated track is clean/generalized. Composition still waits on B013 handoff generalization. |
| 15:27:27–15:27:42 | B013 retry `b013-g35-handoff-v02-ab-002` — baseline | NAS runner; baseline; 15s | **success**; 4,930 tokens | Baseline completed successfully, but comparison remains incomplete because the paired Skill call was quota-blocked. |
| 15:27:42–15:27:43 | B013 retry `b013-g35-handoff-v02-ab-002` — `prepare-solution-change-readiness` v0.2 | NAS runner; Skill; 1s | **quota_blocked**; no model output | Gemini 3.5 Flash free-tier daily request limit (20 requests/project/model) was reached immediately after the baseline call. Do not evaluate or change the Skill from this incomplete pair. |
| 17:07:08–17:07:36 | B014 Procurement Host/GPU — `verify-procurement-options` v0.2 focused rerun | NAS runner; Skill; 28s | **100/100**; 8,579 tokens | Cross-gate H-06 invention removed; C H-06 remains Unknown while B Recommend / A Hold / D Hold / C Reject are preserved. Retain v0.2.0. |
| 19:07:59–19:08:45 | B015 Apartment Dining Table — baseline | NAS runner; baseline; 46s | **82/100**; 6,142 tokens | Correct A/B/C, but incorrectly promotes approximate Candidate D access evidence into Reject; -10 critical access inference penalty. |
| 19:08:45–19:09:43 | B015 — `verify-procurement-options` v0.2 | NAS runner; Skill; 58s | **95/100**; 8,116 tokens | Correct B Recommend, A/D Hold, C Reject. Cross-domain furniture/access generalization passed; minor unsupported preference-level material wording prevents perfect score. |
| 20:49 | Procurement evaluator decision | ChatGPT evaluation + GitHub updates | B014 v0.2 retained; B015 82→95 | Treat verification Skill as cross-domain verified; no further tuning from isolated preference wording. Queue B016 market-expansion A/B. |
| 20:49 | Queue update | GitHub-controlled NAS jobs | `b016-g36-market-expand-v01-ab-001` baseline + `expand-procurement-market` v0.1 | Next isolated procurement capability test; NAS five-minute worker will pick it up autonomously. |
| 20:53:37–20:54:10 | B016 Market Expansion from Stale History — baseline | NAS runner; baseline; 33s | **100/100**; 4,491 tokens | Excellent stale-source diagnosis, 30/70 exploit/explore, genuine channel expansion, stop/watch logic and no fabrication. |
| 20:54:10–20:54:37 | B016 — `expand-procurement-market` v0.1 | NAS runner; Skill; 27s | **100/100**; 5,091 tokens | Equally excellent but no score gain; +600 tokens (~13%). Method works, but B016 does not demonstrate material Skill value. |
| 21:17 | B016 evaluator / architecture decision | ChatGPT evaluation + GitHub updates | baseline 100; Skill 100 | Do not tune or freeze v0.1 from an easy control. Create a harder mixed-history cross-domain market-expansion test. |
| 21:17 | B018 created + queued | GitHub-controlled NAS jobs | `b018-g36-market-expand-v01-ab-001` baseline + Skill v0.1 | Compact treadmill domain; tests calibrated exploitation of productive sources, retirement of stale sources, and rejection of overseas/110 V/no-incline/oversized novelty paths. |

## 2026-09-03/04

| Local time | Benchmark / event | Execution | Score / result | Decision / note |
|---|---|---|---|---|
| 2026-09-04 08:05:05–08:05:23 | B020 Vendor Webhook Integration — baseline | NAS runner; Gemini 3.5 Flash; 18s | **94/100**; 5,113 tokens | Strong polling-adapter control; zero penalties. |
| 2026-09-04 08:05:23–08:05:44 | B020 — `design-technical-solution` v0.3 | NAS runner; Gemini 3.5 Flash; 21s | **93/100**; 7,354 tokens | Safe cross-domain result with zero penalties, but no incremental value over baseline. |
| 2026-09-04 | B020 evaluator decision | Codex evaluation + repository update | baseline 94; Skill 93 | Close same-model A/B. Retain v0.3 as candidate; do not tune B020 and do not compose yet. |
| 2026-09-04 | B022 created + queued | GitHub-controlled NAS jobs | `b022-g35-solution-design-v03-ab-001` baseline + Skill v0.3 | Third standalone domain: inter-building network topology, exact compatibility Unknowns, BA/service and Procurement handoff boundaries. |
| 2026-09-04 | B022 Gemini 3.5 attempt | NAS runner; baseline + Skill | both `provider_busy`; no usable model output | Provider-capacity event only; do not score. |
| 2026-09-04 | B022 replacement queued | GitHub-controlled NAS jobs | `b022-g37-solution-design-v03-ab-002` baseline + Skill v0.3 | Fresh same-model Gemini 3.7 pair; unchanged benchmark and temperature `0.0`. |
| 2026-09-04 13:50:03–13:50:29 | B022 — baseline | NAS runner; Gemini 3.7 Flash; 26s | **88/100**; 5,661 tokens | Correct topology and handoffs; unsupported precision and preference promotion prevent a stronger score. |
| 2026-09-04 13:50:29–13:50:51 | B022 — `design-technical-solution` v0.3 | NAS runner; Gemini 3.7 Flash; 22s | **83/100**; 5,904 tokens | Correct topology, but stronger preference/Unknown-to-hard-requirement promotion than baseline. Zero penalties. |
| 2026-09-04 | B022 evaluator decision | Codex evaluation + repository update | baseline 88; Skill 83 | Reject v0.3 for composition. Correct the generic provenance/requirement-strength gate, then run a focused Skill-only rerun. |
| 2026-09-04 | Solution Architecture v0.4 created + queued | Focused generic Skill correction | `b022-g37-solution-design-v04-skill-003` | Adds evidence-to-requirement provenance audit without network-specific rules; Gemini 3.7 Skill-only rerun against preserved baseline. |

## Current architecture decision

- Requirements analysis: `analyze-requirements` v0.4 — validated.
- Decomposition: `decompose-requirements` v0.2 — validated/generalized.
- Acceptance criteria: `elaborate-acceptance-criteria` v0.1 — validated/generalized.
- Test / assurance: `derive-test-cases` v0.3 — retained after focused correction.
- Composite BA Delivery Analyst v0.2 — frozen / preferred architecture after B008 95/100 and B009 94/100 with zero penalties.
- Three-specialist pipeline — retained as experimental infrastructure, not preferred after B008 53/100 at 23,748 tokens.
- Solution / Change-Readiness: `prepare-solution-change-readiness` v0.2 retained after B010 **100/100**, zero penalties; B013 generalization remains provider-quota blocked because the latest retry produced a successful baseline but no Skill output.
- ITIL 4 alignment/readiness: `assess-itil-alignment` v0.2 retained after B011 v0.1 **98/100** and B012 v0.2 **100/100**, zero penalties on the corrected rerun; isolated ITIL track is generalized enough for composition planning.
- Procurement verification: `verify-procurement-options` v0.2.0 retained after B014 **100/100** and B015 **95/100** versus baseline **82/100**; cross-domain IT + furniture evidence is sufficient for composition planning.
- Procurement market expansion: `expand-procurement-market` v0.1.0 produced **100/100** on B016 but did not beat the **100/100** baseline and used more tokens. B018 is the harder generalization/value test; do not freeze or tune v0.1 until that result.
- Technical Solution Architecture: v0.3.0 is **not ready for composition** after B019 **82/100**, B020 baseline **94/100** vs Skill **93/100**, and B022 baseline **88/100** vs Skill **83/100**. v0.4.0 applies the focused generic provenance/requirement-strength correction and is queued for a B022 Skill-only rerun.
- Composition of handoff + ITIL with the frozen BA agent remains deferred until B013 handoff generalization completes cleanly.
- Procurement Analyst composition is the planned next architecture milestone after B018. B017 dishwasher remains reserve verification evidence, not a mandatory gate.

## Timing observations

Successful Gemini calls are still typically tens of seconds. Most elapsed time is benchmark design, scoring, Skill correction, GitHub/NAS polling and evaluator cadence rather than model execution.

The NAS worker is the fast execution loop; the ChatGPT benchmark cycles are the slower evaluation/development loop. This ledger should be updated whenever a benchmark is evaluated or an architecture/version decision is made.
