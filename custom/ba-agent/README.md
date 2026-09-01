# BA Agent Lab

This folder contains version-controlled Business Analyst skills and benchmark cases for LibreChat.

## Goal

Build a reliable BA agent for an ITIL / Agile delivery environment using **separately benchmarked capabilities** rather than one monolithic prompt.

## Capability 1 — Requirements analysis

Skill:

- `skills/analyze-requirements/SKILL.md`
- current version: **0.4.0**

Purpose: convert messy source material into a traceable requirements analysis while preserving uncertainty, requirement status, decision ownership and evidence strength.

This capability deliberately does **not** create epics, user stories, estimates, solution designs or detailed acceptance criteria.

### Benchmark 001 — Change Validation Automation

Latest validated Gemini 3.6 Flash results:

- no skill: **57/100**
- v0.2: **84/100**, **86/100** — average **85**
- v0.3: **93/100**, **97/100** — average **95**

Benchmark 001 drove the distinction between:

- **Evidence class** — how the source supports the statement;
- **Requirement status** — how agreed/committed the item is;
- **Confidence** — confidence that the extraction/classification accurately reflects the evidence.

### Benchmark 002 — Major Incident Communications Automation

Purpose: test generalization on a materially different IT service-management problem.

Results:

| Model | No skill | `analyze-requirements` v0.4 | Improvement |
|---|---:|---:|---:|
| Gemini 3.6 Flash | 57 | **95** | **+38** |
| Gemini 3.5 Flash | 60 | **81** | **+21** |

Conclusion: `analyze-requirements` v0.4 is validated as a useful reusable capability. Skill quality and underlying model capability remain separate variables.

Benchmark 002 files:

- `benchmarks/002-major-incident-communications/input.md`
- `benchmarks/002-major-incident-communications/gold-standard.md`
- `benchmarks/002-major-incident-communications/scoring-rubric.md`
- `benchmarks/002-major-incident-communications/results/`

## Capability 2 — Requirements decomposition

Skill:

- `skills/decompose-requirements/SKILL.md`
- current version: **0.2.0**

Purpose: take a completed requirements analysis and shape supported delivery work without forcing everything into user stories.

The skill distinguishes:

- Epic / Capability;
- User Story;
- Enabler / Technical Task;
- Spike / Discovery Item;
- Decision Item;
- Dependency;
- Risk;
- Candidate work;
- Deferred work.

Core rules include:

- preserve upstream requirement status;
- disputed business rules become Decision Items, not silently selected stories;
- unverified technical feasibility becomes Spike/Discovery work rather than committed build work;
- Candidate scope remains conditional;
- Targets do not become hard SLAs;
- Deferred items stay outside the current backlog;
- every delivery item traces to upstream requirement IDs;
- no story points, estimates or invented architecture;
- no unsupported downstream qualities/mechanisms such as immutable audit logs, queues/screens, notifications, storage jobs or API protocols;
- Unknown decision ownership remains Unknown everywhere;
- all work-item cross-references must resolve to real IDs before output is returned.

### Benchmark 003 — Application Access Request Delivery Decomposition

Purpose: test whether a model can correctly decompose a **Partially Ready** requirements analysis while isolating blockers and preserving status.

Key benchmark traps:

- a disputed privileged-access approval rule must become a Decision Item;
- candidate/unverified identity-platform automation must become discovery/conditional work;
- candidate CRM / Reporting Portal / Dev Wiki pilot scope must not become committed scope;
- a four-business-hour target must not become an SLA;
- deferred automatic deprovisioning must stay deferred;
- unknown audit-retention duration must remain unknown;
- the analyst-proposed staged-pilot mechanism must not become mandatory delivery sequencing;
- the model must not force all work into user stories.

Initial Gemini 3.5 Flash results:

| Run | Score | Finding |
|---|---:|---|
| No decomposition skill | **73/100** | Good uncertainty handling, but invented `tamper-evident` audit qualities and had weaker capability/readiness structure. |
| `decompose-requirements` v0.1 | **47/100** (raw 87) | Much better decomposition structure, but serious downstream invention: immutability, queue/UI mechanisms, inferred governance/sign-off and a phantom work-item ID. |

Decision: **v0.1 not validated.** The methodology improved, but downstream invention control regressed. v0.2 targets those exact failure modes while retaining the stronger decomposition structure.

Files:

- `benchmarks/003-access-request-decomposition/input.md` — model-visible input.
- `benchmarks/003-access-request-decomposition/prompt.md` — exact runner/manual instruction.
- `benchmarks/003-access-request-decomposition/benchmark.json` — automated-runner configuration.
- `benchmarks/003-access-request-decomposition/gold-standard.md` — evaluator-only.
- `benchmarks/003-access-request-decomposition/scoring-rubric.md` — evaluator-only.
- `skills/decompose-requirements/SKILL.md` — skill under test.

## Automated benchmark runner

`tools/benchmark_runner.py` can run benchmark A/B cases directly against Gemini from a separate NAS lab checkout. This removes the manual LibreChat copy/paste step for most iterative benchmark work.

The runner:

- sends only model-visible `prompt.md` + `input.md`;
- injects the selected skill body as Gemini system instruction for Skill runs;
- never loads the evaluator-only gold standard or scoring rubric;
- records model/settings and SHA-256 hashes for input, prompt and skill;
- saves raw `.md` output plus JSON metadata/manifest;
- stops on Gemini `429` quota exhaustion and never silently changes model;
- can optionally `git commit` and `git push` results when the NAS lab clone has push authentication.

Documentation: `tools/README.md`.

Recommended pattern for later skill iterations is to retain the existing baseline and run only the changed Skill version, then periodically repeat baseline/LibreChat validation when needed.

## Standard manual A/B test procedure

Use the same model and generation settings for both runs.

### Requirements-analysis benchmarks

Run A: clean chat, Skills disabled, benchmark `input.md` only.

Run B: clean chat, same model/settings, manually invoke `$analyze-requirements`, same input and instruction.

### Decomposition benchmark

Run A: clean chat, Skills disabled, Benchmark 003 `input.md` only, using `prompt.md`.

Run B: clean chat, same model/settings, manually invoke `$decompose-requirements`, same input and instruction.

Save the complete response for scoring.

## Benchmark discipline

Do not allow the model under test to read a benchmark's `gold-standard.md` or `scoring-rubric.md`.

For a clean manual test, disable unrelated browsing/tools and do not expose this repository through Filesystem MCP during the run.

Record:

- model and exact model version/name;
- reasoning/temperature settings if exposed;
- date/time;
- skill version;
- baseline score;
- skill score;
- hallucinations or invented scope;
- requirement-status promotions;
- unresolved decisions incorrectly converted into implementation work;
- technical unknowns incorrectly treated as confirmed build work;
- missing traceability;
- estimates or architecture invented despite instruction.

## Versioning and generalization rule

Change one material thing at a time. If a skill changes, increment its version and rerun an appropriate benchmark.

Do not optimize indefinitely against one benchmark. Once behavior is repeatably strong, add a materially different benchmark or move to the next capability.
