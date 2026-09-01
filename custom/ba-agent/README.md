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
- status: **validated/generalized**

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

The Skill improved explicit readiness, per-criterion traceability and evidence classification, but the baseline was already exceptionally strong. Decision: retain v0.1 unchanged and test it on a harder domain rather than tuning against Benchmark 005.

### Benchmark 006 — Bulk Site Import Acceptance Criteria

Runner-native Gemini 3.5 Flash results:

| Run | Score |
|---|---:|
| No skill baseline | **77/100** |
| `elaborate-acceptance-criteria` v0.1 | **98/100** |
| **Improvement** | **+21** |

The baseline converted Unknown site-name/region validation into an asserted `no validation is performed` rule. v0.1 preserved the Unknown area, kept duplicate handling disputed, registry validation Candidate, the performance Target non-binding, recurring imports Deferred and registry access read-only, while maintaining full criterion traceability.

Conclusion: **`elaborate-acceptance-criteria` v0.1 is validated/generalized across materially different service-notification and batch-data problems.** Do not tune v0.2 unless later cross-capability testing exposes a reusable defect.

## Capability 4 — Test-case / assurance derivation

Skill:

- `skills/derive-test-cases/SKILL.md`
- current version: **0.1.0**
- status: **experimental / Benchmark 007 queued**

Purpose: derive traceable behavioural test cases and assurance coverage from sufficiently ready acceptance criteria without inventing execution mechanics.

Core rules include:

- test only Ready or confirmed portions of Partially Ready criteria;
- preserve Blocked/Disputed/Unknown/Candidate/Target/Deferred status;
- trace every test to AC ID, delivery item and upstream REQ ID(s);
- derive negative cases only from established logical boundaries;
- do not invent UI steps, accounts, environments, concrete test data, validation/error text, APIs, storage, retries/timeouts, mocks/stubs, automation frameworks or test tooling;
- keep Targets non-binding unless upstream explicitly makes them acceptance commitments;
- represent conditional security/process constraints without implying Candidate implementation is committed;
- perform a coverage-integrity check before returning output.

### Benchmark 007 — Release Verification Test Cases

Purpose: first A/B benchmark for `derive-test-cases` v0.1. The benchmark combines Ready behavioural acceptance criteria, an explicit positive/negative Change-reference boundary, conditional integration constraints, a disputed rollback decision, Candidate automated import, unapproved pilot services, a non-binding completion Target, Deferred predictive scoring and Unknown retention.

A runner-native Gemini 3.5 Flash baseline + v0.1 Skill A/B job is queued as `b007-g35-ab-v01-001`.

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
3. `elaborate-acceptance-criteria` — **validated/generalized**
4. `derive-test-cases` — **experimental / Benchmark 007 queued**
5. future capability — solution / change-readiness handoff
