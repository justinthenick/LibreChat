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

### Benchmark 002 — Major Incident Communications Automation

| Model | No skill | `analyze-requirements` v0.4 | Improvement |
|---|---:|---:|---:|
| Gemini 3.6 Flash | 57 | **95** | **+38** |
| Gemini 3.5 Flash | 60 | **81** | **+21** |

Conclusion: `analyze-requirements` v0.4 is validated as a useful reusable capability. Skill quality and underlying model capability remain separate variables.

## Capability 2 — Requirements decomposition

Skill:

- `skills/decompose-requirements/SKILL.md`
- current version: **0.2.0**

Purpose: take a completed requirements analysis and shape supported delivery work without forcing everything into user stories.

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

Initial manual Gemini 3.5 Flash results:

| Run | Score | Finding |
|---|---:|---|
| No decomposition skill | **73/100** | Good uncertainty handling, but invented `tamper-evident` audit qualities and had weaker capability/readiness structure. |
| `decompose-requirements` v0.1 | **47/100** (raw 87) | Better decomposition structure, but serious downstream invention: immutability, queue/UI mechanisms, inferred governance/sign-off and a phantom work-item ID. |

Runner-native Gemini 3.5 Flash results at temperature `0.0`:

| Run | Score |
|---|---:|
| No skill baseline | **70/100** |
| `decompose-requirements` v0.2 | **99/100** |
| v0.2 repeat | **99/100** |

Decision: v0.2 retained after repeatability testing.

### Benchmark 004 — Release Evidence and Deployment Validation Decomposition

This materially different Change Enablement / release-evidence benchmark tested generalization rather than further tuning against Benchmark 003.

Runner-native Gemini 3.5 Flash results:

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
- status: **experimental / benchmark pending**

Purpose: turn sufficiently ready delivery items into traceable, testable acceptance criteria without creating new behavior.

Core rules include:

- Ready items may be elaborated only to the extent evidence supports them;
- Partially Ready items are elaborated only for their confirmed portion;
- Blocked/Disputed/Unknown behavior remains blocked rather than being resolved in criteria;
- Candidate/Conditional scope stays non-committed;
- Targets remain planning/quality objectives rather than mandatory pass/fail acceptance criteria;
- Deferred work receives no current acceptance criteria;
- every criterion traces to its delivery item and upstream requirement IDs;
- Given/When/Then is used only where all preconditions/actions/outcomes are evidenced;
- no invented UI, notification, validation/error, retry/timeout, workflow, role/permission, storage, API/protocol, governance or architecture details;
- logically necessary negative conditions are allowed only as explicit `Derived boundary` criteria.

### Benchmark 005 — Planned Maintenance Notification Acceptance Criteria

Purpose: first A/B benchmark for `elaborate-acceptance-criteria` v0.1.

Key traps include:

- Ready notice-creation criteria must remain limited to the four sourced data elements;
- the approved Change-reference rule may yield a derived negative boundary but must not invent Change-validation UI/API/error behavior;
- disputed cancellation handling must remain blocked with both positions preserved and Decision Owner Unknown;
- Candidate subscriber notification must not become committed behavior or invent email/SMS/push channels;
- Mobile App / Billing Portal pilot scope remains Candidate;
- the 24-hour objective remains a non-binding Target;
- automatic post-maintenance closure remains Deferred;
- retention remains Unknown;
- manual publication fallback remains supported without inventing its mechanism.

A runner-native Gemini 3.5 Flash baseline + v0.1 Skill A/B job is queued as `b005-g35-ab-v01-001`.

Files:

- `benchmarks/005-planned-maintenance-acceptance-criteria/input.md`
- `benchmarks/005-planned-maintenance-acceptance-criteria/prompt.md`
- `benchmarks/005-planned-maintenance-acceptance-criteria/benchmark.json`
- `benchmarks/005-planned-maintenance-acceptance-criteria/gold-standard.md`
- `benchmarks/005-planned-maintenance-acceptance-criteria/scoring-rubric.md`

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
3. `elaborate-acceptance-criteria` — **experimental / Benchmark 005 queued**
4. future capability — test/assurance traceability and solution handoff
