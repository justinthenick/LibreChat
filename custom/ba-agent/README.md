# BA Agent Lab

This folder contains version-controlled Business Analyst skills and benchmark cases for LibreChat.

## Goal

Build a reliable BA agent for an ITIL / Agile delivery environment using **separately benchmarked capabilities** and evidence-driven composition rather than assuming one monolithic prompt or a multi-agent design is best.

## Capability 1 — Requirements analysis

Skill:

- `skills/analyze-requirements/SKILL.md`
- current version: **0.4.0**
- status: **validated**

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
- status: **validated/generalized**

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

Core rules include preserving readiness/status, keeping disputed/Candidate/Target/Deferred/Unknown areas non-committed, tracing every criterion to delivery items and upstream requirements, and refusing unsupported UI, validation/error, workflow, architecture or governance detail.

### Benchmark 005 — Planned Maintenance Notification Acceptance Criteria

Runner-native Gemini 3.5 Flash results at temperature `0.0`:

| Run | Score |
|---|---:|
| No skill baseline | **96/100** |
| `elaborate-acceptance-criteria` v0.1 | **98/100** |
| Difference | **+2** |

### Benchmark 006 — Bulk Site Import Acceptance Criteria

Runner-native Gemini 3.5 Flash results:

| Run | Score |
|---|---:|
| No skill baseline | **77/100** |
| `elaborate-acceptance-criteria` v0.1 | **98/100** |
| **Improvement** | **+21** |

The harder batch-data benchmark exposed baseline status leakage while v0.1 preserved Unknown validation, disputed duplicate handling, Candidate registry validation, the non-binding Target, Deferred recurring imports and read-only registry constraints.

Conclusion: **`elaborate-acceptance-criteria` v0.1 is validated/generalized.**

## Capability 4 — Test-case / assurance derivation

Skill:

- `skills/derive-test-cases/SKILL.md`
- current version: **0.3.0**
- status: **retained after focused correction**

Purpose: derive traceable behavioural test cases and assurance coverage from sufficiently ready acceptance criteria without inventing execution mechanics.

### Benchmark 007 — Release Verification Test Cases

Runner-native Gemini 3.5 Flash results:

| Run | Score | Finding |
|---|---:|---|
| No-skill baseline | **97/100** | Very strong behavioural coverage and discipline. |
| `derive-test-cases` v0.1 | **95/100** | Strong tests, but closing gaps over-prescribed future execution prerequisites. |
| `derive-test-cases` v0.2 | **93/100** | Core derivation remained strong; closing section still manufactured prerequisites/ownership and leaked inspection mechanics. |
| `derive-test-cases` v0.3 | **98/100** | Core defect corrected; no material invention or execution-method leakage. |

Decision: **retain `derive-test-cases` v0.3.** Do not tune another version from Benchmark 007.

## Agent-composition layer

### Single composite agent — BA Delivery Analyst

Agent:

- `agents/ba-delivery-analyst/AGENT.md`
- current version: **0.2.0**
- status: **focused Benchmark 008 correction queued**

The composite agent coordinates four explicit stages in a single model call:

1. requirements analysis;
2. delivery decomposition;
3. acceptance-criteria elaboration;
4. behavioural test / assurance derivation.

### Benchmark 008 — Contractor Site Access End-to-End BA Delivery

Benchmark path:

- `benchmarks/008-contractor-site-access-end-to-end`

First paired Gemini 3.5 Flash result:

| Run | Raw score | Penalties | Final | Total tokens |
|---|---:|---:|---:|---:|
| No-agent baseline | **49/100** | -32 | **17/100** | **6,488** |
| Composite v0.1 | **73/100** | >= -85 | **0/100** | **9,030** |

The composite materially improved stage separation, handoffs, status preservation and end-to-end traceability, and reduced the baseline's architecture/test-mechanism invention. However, it introduced a harder governance failure: Stage 1 created a generic `Decision Owner` column and repeatedly converted source/proposer roles into unsupported decision authority. Under the rubric's per-occurrence authority penalty, this makes v0.1 non-production-ready regardless of its stronger raw structure.

Other v0.1 defects included:

- no explicit overall `Partially Ready` statement;
- explicit process-boundary constraints did not survive the full downstream chain;
- missing-field submission prevention was derived without an explicit upstream only-when/cannot boundary;
- manual issuance fallback was partly reframed as a recording/UI path;
- some tests leaked `selects` / `logs` execution mechanisms;
- an assurance note invented future Security verification ownership.

Token impact of v0.1 versus baseline:

- prompt tokens: **+142.1%**;
- candidate/output tokens: **+9.7%**;
- reasoning/thought tokens: **+42.7%**;
- total tokens: **+39.2%**.

### Architecture decision after v0.1

**Do not build the true multi-call specialist-agent runner yet.**

The failure can still be attributed to the single composite agent's control semantics rather than to an inherent need for separate model calls. The agent already contained the right high-level authority rule but allowed a generic owner field that encouraged source-to-authority substitution under combined stage load.

`BA Delivery Analyst` v0.2 therefore makes one focused correction set:

- no generic Decision Owner column;
- source/proposer explicitly separated from authority;
- Decision Owner appears only for explicit unresolved decisions and defaults to Unknown unless sourced;
- overall readiness must be explicit;
- process/security constraints must survive every handoff;
- missing-data rejection/prevention cannot be inferred from mere data capture;
- manual fallback remains an outcome rather than a UI/recording mechanism;
- test/assurance language cannot invent `logs`, `selects`, future verifiers or governance owners.

Queued NAS job:

- `b008-g35-composite-v02-002`
- model: `gemini-3.5-flash`
- mode: composite agent only
- temperature: `0.0`

The existing baseline remains the comparison control, avoiding an unnecessary extra Gemini call.

## Proposed specialist-agent architecture — conditional next step

Only if composite v0.2 fixes the hard authority/traceability defects while retaining the structural gains will the lab proceed to a specialist comparison:

- **Requirements Analyst** — requirements analysis;
- **Delivery Refinement Analyst** — decomposition + acceptance criteria;
- **Assurance Analyst** — test / assurance derivation.

A true multi-call pipeline would require runner support for persisted stage outputs, stage-to-stage input handoffs, per-stage hashes/metadata, token usage and end-to-end scoring. That infrastructure remains intentionally deferred.

If composite v0.2 still violates authority/status controls, that will be evidence that single-call cognitive load/composition interference is the limiting factor; at that point a multi-call specialist pipeline becomes a justified architecture experiment rather than speculative complexity.

## Automated benchmark runner

The NAS benchmark loop consists of:

1. GitHub-controlled `custom/ba-agent/automation/jobs.json`;
2. Synology DSM Task Scheduler periodically invoking `benchmark_worker.py --once`;
3. the worker refreshing benchmark/skill/agent files from GitHub;
4. `benchmark_runner.py` calling Gemini directly;
5. raw result + metadata/manifest files being published back to the feature branch;
6. evaluator scoring against the repo-held gold standard/rubric.

The runner never loads evaluator-only gold-standard or scoring-rubric files into model context, stops on Gemini quota errors, and does not silently change models.

## Benchmark discipline

- Use the same model/settings for paired baseline and Skill/Agent runs.
- Change one material variable at a time.
- Keep evaluator-only gold/rubric files out of model context.
- Record exact model, temperature, input/prompt/skill or agent hashes and provider status.
- Treat model quality, capability quality and composition quality as separate variables.
- Do not optimize indefinitely against one benchmark; use materially different benchmarks for generalization.
- Do not assume multi-agent is better: require evidence that added calls, handoffs and complexity improve quality enough to justify their cost.

## Capability sequence

Current sequence:

1. `analyze-requirements` — **validated**
2. `decompose-requirements` — **validated/generalized**
3. `elaborate-acceptance-criteria` — **validated/generalized**
4. `derive-test-cases` — **v0.3 retained**
5. single composite BA Delivery Analyst — **v0.2 focused rerun queued**
6. specialist-agent comparison — **conditional on v0.2 evidence**
7. future capability — solution / change-readiness handoff
