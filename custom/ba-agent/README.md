# BA Agent Lab

This folder contains version-controlled Business Analyst skills and benchmark cases for LibreChat.

## Goal

Build a reliable BA agent for an ITIL / Agile delivery environment using **separately benchmarked capabilities** rather than one monolithic prompt.

## Capability 1 — Requirements analysis

Skill:

- `skills/analyze-requirements/SKILL.md`
- current version: **0.4.0**

Purpose: convert messy source material into a traceable requirements analysis while preserving uncertainty, requirement status, decision ownership and evidence strength.

### Benchmark 001 — Change Validation Automation

Latest validated Gemini 3.6 Flash results:

- no skill: **57/100**
- v0.2: **84/100**, **86/100** — average **85**
- v0.3: **93/100**, **97/100** — average **95**

### Benchmark 002 — Major Incident Communications Automation

| Model | No skill | `analyze-requirements` v0.4 | Improvement |
|---|---:|---:|---:|
| Gemini 3.6 Flash | 57 | **95** | **+38** |
| Gemini 3.5 Flash | 60 | **81** | **+21** |

Conclusion: `analyze-requirements` v0.4 is validated as a useful reusable capability.

## Capability 2 — Requirements decomposition

Skill:

- `skills/decompose-requirements/SKILL.md`
- current version: **0.2.0**

Purpose: take a completed requirements analysis and shape supported delivery work without forcing everything into user stories.

Core rules include preserving upstream status, isolating disputes and technical discovery, keeping Candidate/Target/Deferred work non-committed, maintaining traceability, and refusing invented estimates, architecture, governance or downstream mechanisms.

### Benchmark 003 — Application Access Request Delivery Decomposition

Runner-native Gemini 3.5 Flash results at temperature `0.0`:

| Run | Score |
|---|---:|
| No skill baseline | **70/100** |
| `decompose-requirements` v0.2 | **99/100** |
| v0.2 repeat | **99/100** |

### Benchmark 004 — Release Evidence and Deployment Validation Decomposition

| Run | Score |
|---|---:|
| No skill baseline | **68/100** |
| `decompose-requirements` v0.2 | **92/100** |
| **Improvement** | **+24** |

Conclusion: `decompose-requirements` v0.2 is validated/generalized across materially different decomposition problems. Stop tuning decomposition for now.

## Capability 3 — Acceptance-criteria elaboration

Skill:

- `skills/elaborate-acceptance-criteria/SKILL.md`
- current version: **0.1.0**
- status: **experimental / generalization testing**

Purpose: turn sufficiently ready delivery items into traceable, testable acceptance criteria without creating new behavior.

Core rules include:

- Ready items may be elaborated only to the extent evidence supports them;
- Partially Ready items are elaborated only for their confirmed portion;
- Blocked/Disputed/Unknown behavior remains blocked rather than being resolved in criteria;
- Candidate/Conditional scope stays non-committed;
- Targets remain planning/quality objectives rather than mandatory pass/fail criteria;
- Deferred work receives no current acceptance criteria;
- every criterion traces to its delivery item and upstream requirement IDs;
- Given/When/Then is used only where every precondition/action/outcome is evidenced;
- no invented UI, file/channel, validation/error, retry/timeout, workflow, role/permission, storage, API/protocol, governance or architecture details;
- logically necessary negative conditions are allowed only as explicit `Derived boundary` criteria.

### Benchmark 005 — Planned Maintenance Notification Acceptance Criteria

Runner-native Gemini 3.5 Flash results at temperature `0.0`:

| Run | Score |
|---|---:|
| No skill baseline | **96/100** |
| `elaborate-acceptance-criteria` v0.1 | **98/100** |
| Difference | **+2** |

The Skill improved explicit readiness, per-criterion traceability and evidence classification, but the baseline was already exceptionally strong because the benchmark prompt and upstream decomposition imposed substantial discipline. v0.1 also introduced a small amount of unsupported `purging` / `storage and archiving` wording around the Unknown retention item, though not as committed design.

Decision: **retain v0.1 unchanged; do not tune from Benchmark 005.** Move to a harder, materially different acceptance-criteria benchmark to test whether the Skill provides reusable value rather than optimizing against an easy baseline.

### Benchmark 006 — Bulk Site Import Acceptance Criteria

Purpose: generalization/stress test in a batch-data domain with a Partially Ready item, a confirmed negative minimum-data boundary, disputed duplicate handling, Candidate Master Site Registry validation, a non-binding performance Target, Deferred recurring imports, Unknown retention, Unknown site-name/region validation, and strict no-invention boundaries around file/batch/integration behavior.

A runner-native Gemini 3.5 Flash baseline + v0.1 Skill A/B job is queued as `b006-g35-ab-v01-001`.

## Automated benchmark runner

The NAS benchmark loop consists of:

1. GitHub-controlled `custom/ba-agent/automation/jobs.json`;
2. Synology DSM Task Scheduler periodically invoking `benchmark_worker.py --once`;
3. the worker refreshing benchmark/skill files from GitHub;
4. `benchmark_runner.py` calling Gemini directly;
5. raw result + metadata/manifest files being published back to the feature branch;
6. evaluator scoring against the repo-held gold standard/rubric.

The runner never loads evaluator-only gold-standard or scoring-rubric files into model context, stops on Gemini quota errors, and does not silently change models.

## Benchmark discipline

- Use the same model/settings for paired baseline and Skill runs.
- Change one material variable at a time.
- Keep evaluator-only gold/rubric files out of model context.
- Record exact model, temperature, input/prompt/skill hashes and provider status.
- Treat model quality and Skill quality as separate variables.
- Do not optimize indefinitely against one benchmark; use materially different benchmarks for generalization.

## Capability sequence

Current intended sequence:

1. `analyze-requirements` — **validated**
2. `decompose-requirements` — **validated/generalized**
3. `elaborate-acceptance-criteria` — **v0.1 retained; Benchmark 006 generalization queued**
4. future capability — test/assurance traceability and solution handoff
