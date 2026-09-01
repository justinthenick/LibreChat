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

Core rules include:

- test only Ready or confirmed portions of Partially Ready criteria;
- preserve Blocked/Disputed/Unknown/Candidate/Target/Deferred status;
- trace every test to AC ID, delivery item and upstream REQ ID(s);
- derive negative cases only from established logical boundaries;
- do not invent UI steps, accounts, environments, concrete test data, validation/error text, APIs, storage, retries/timeouts, mocks/stubs, automation frameworks or test tooling;
- conditional constraints become assurance states describing **what** must hold, not an invented inspection mechanism;
- do not manufacture future execution prerequisites from absent technical detail.

### Benchmark 007 — Release Verification Test Cases

Runner-native Gemini 3.5 Flash results:

| Run | Score | Finding |
|---|---:|---|
| No-skill baseline | **97/100** | Very strong behavioural coverage and discipline. |
| `derive-test-cases` v0.1 | **95/100** | Strong tests, but closing gaps over-prescribed future execution prerequisites. |
| `derive-test-cases` v0.2 | **93/100** | Core derivation remained strong; closing section still manufactured prerequisites/ownership and leaked inspection mechanics. |
| `derive-test-cases` v0.3 | **98/100** | Core defect corrected; no material invention or execution-method leakage. |

Decision: **retain `derive-test-cases` v0.3.** Do not tune another version from Benchmark 007. The capability is strong enough to enter cross-capability composition testing.

## Agent-composition layer

### Single composite agent — BA Delivery Analyst v0.1

Agent:

- `agents/ba-delivery-analyst/AGENT.md`
- current version: **0.1.0**
- status: **Benchmark 008 queued**

The composite agent coordinates four explicit stages in a single model call:

1. requirements analysis;
2. delivery decomposition;
3. acceptance-criteria elaboration;
4. behavioural test / assurance derivation.

Each stage must produce an explicit handoff and downstream detail may never become more certain than upstream evidence. Cross-stage integrity checks require REQ -> delivery item -> AC -> test traceability and prevent disputed/Candidate/Target/Deferred/Unknown material leaking into committed downstream work.

### Benchmark 008 — Contractor Site Access End-to-End BA Delivery

Benchmark path:

- `benchmarks/008-contractor-site-access-end-to-end`

This is a fresh messy-source end-to-end benchmark. It compares a no-agent baseline with the single composite BA Delivery Analyst using the existing runner, so no NAS execution-infrastructure change is required.

The evaluator scores:

- stage fidelity;
- uncertainty/status preservation;
- cross-stage traceability;
- contradictions or status drift;
- invented scope/mechanics/authority;
- final downstream usability;
- token usage/cost as a secondary architectural measure.

Queued NAS job:

- `b008-g35-composite-v01-001`
- model: `gemini-3.5-flash`
- mode: baseline + composite agent
- temperature: `0.0`

No specialist multi-agent runner changes will be made until Benchmark 008 demonstrates that composition is valuable.

## Proposed specialist-agent architecture — conditional next step

Only if the single composite agent is useful, compare it with a small specialist architecture:

- **Requirements Analyst** — requirements analysis;
- **Delivery Refinement Analyst** — decomposition + acceptance criteria;
- **Assurance Analyst** — test / assurance derivation.

A true multi-call pipeline would require runner support for persisted stage outputs, stage-to-stage input handoffs, per-stage hashes/metadata, token usage and end-to-end scoring. That infrastructure is intentionally deferred until the single-call composite result justifies the complexity and extra model calls.

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
5. single composite BA Delivery Analyst — **Benchmark 008 queued**
6. specialist-agent comparison — **conditional on Benchmark 008**
7. future capability — solution / change-readiness handoff
