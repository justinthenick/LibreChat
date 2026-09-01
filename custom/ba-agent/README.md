# BA Agent Lab

Version-controlled Business Analyst skills, agents and benchmarks for LibreChat.

## Goal

Build a reliable ITIL / Agile BA capability using evidence-driven benchmarking. Individual capabilities are tested first, then composition architectures are compared rather than assuming either a monolithic prompt or multi-agent design is best.

## Validated capability stack

| Capability | Current version | Status | Key evidence |
|---|---:|---|---|
| `analyze-requirements` | 0.4.0 | validated | B001 v0.3 avg 95; B002 Gemini 3.6 95, Gemini 3.5 81 |
| `decompose-requirements` | 0.2.0 | validated/generalized | B003 70 -> 99, repeat 99; B004 68 -> 92 |
| `elaborate-acceptance-criteria` | 0.1.0 | validated/generalized | B005 96 -> 98; B006 77 -> 98 |
| `derive-test-cases` | 0.3.0 | retained | B007 baseline 97; v0.1 95; v0.2 93; corrected v0.3 98 |

The common quality controls are status preservation, explicit evidence/authority separation, stable traceability, no silent dispute resolution, no promotion of Candidate/Target/Deferred/Unknown work, and refusal to invent architecture, workflow, UI, governance or test execution detail.

## Agent composition

### Composite BA Delivery Analyst

Agent: `agents/ba-delivery-analyst/AGENT.md`  
Current version: **0.2.0**

Single-call sequence:

1. requirements analysis;
2. delivery decomposition;
3. acceptance-criteria elaboration;
4. behavioural test / assurance derivation.

Each stage has an explicit handoff and downstream detail may never become more certain than upstream evidence.

### Benchmark 008 — Contractor Site Access End-to-End

Gemini 3.5 Flash, temperature `0.0`:

| Architecture | Raw | Penalties | Final | Total tokens |
|---|---:|---:|---:|---:|
| No-agent baseline | 49 | -32 | **17/100** | **6,488** |
| Composite v0.1 | 73 | >= -85 | **0/100** | **9,030** |
| **Composite v0.2** | **95** | **0** | **95/100** | **10,439** |
| Three-specialist pipeline v0.1 | 76 | -23 | **53/100** | **23,748** |

#### Composite v0.2 finding

v0.2 corrected the v0.1 authority/governance failure and retained strong handoffs, constraint survival and end-to-end traceability. Emergency/disputed behavior stayed unresolved; Candidate automation/pilot stayed non-committed; Target and Deferred work remained correctly classified; Unknown retention was not converted into design or tests. No rubric penalties applied.

**Composite v0.2 is retained as the preferred architecture control.**

#### Specialist pipeline finding

The persisted three-call pipeline technically worked end to end, but it amplified semantic errors across handoffs:

- Stage 1 invented routing/workflow-engine concepts;
- refinement introduced an unsupported `compliance auditor` actor;
- Unknown retention became a committed no-purge/no-delete acceptance criterion;
- assurance then converted that invented criterion into a committed test.

The pipeline scored **53/100** and consumed **23,748 tokens**, about **2.28x** the composite v0.2 token usage while scoring 42 points lower.

**Architecture decision: prefer Composite BA Delivery Analyst v0.2.** Keep the pipeline runner as experimental infrastructure, but do not tune the specialist pipeline further against B008.

## Benchmark 009 — Service Ownership Update End-to-End

Path: `benchmarks/009-service-ownership-update-end-to-end`

Purpose: fresh generalization test for Composite BA Delivery Analyst v0.2 in a materially different service-data/governance domain.

Key traps include:

- disputed Severity-1 emergency approval authority;
- Candidate Service Registry automation with unverified integration capability;
- Candidate Finance Applications / Network Tools pilot;
- non-binding one-business-day Target;
- Deferred quarterly ownership recertification;
- Unknown evidence-retention period;
- conditional imported-update source traceability;
- explicit service-governance / HR / application-lifecycle / Change-authority boundaries;
- no established UI, validation, API, storage, queue, workflow or test mechanics.

Queued NAS job:

- `b009-g35-composite-v02-ab-001`
- model: `gemini-3.5-flash`
- mode: baseline + Composite v0.2
- temperature: `0.0`

If v0.2 remains strong on B009 without material status drift or invention, treat the composite architecture as generalized enough to freeze before moving to the next capability layer.

## Specialist pipeline infrastructure

Experimental specialist agents:

- `agents/requirements-analyst/AGENT.md`
- `agents/delivery-refinement-analyst/AGENT.md`
- `agents/assurance-analyst/AGENT.md`

Pipeline tooling:

- `tools/agent_pipeline_runner.py`
- pipeline-aware `tools/benchmark_worker.py`

The pipeline runner persists every stage output plus metadata/hash information and passes the prior artifact into the next model call. It is retained for future architecture experiments even though B008 currently favors the simpler composite.

## Automated benchmark loop

1. GitHub queue: `custom/ba-agent/automation/jobs.json`;
2. Synology DSM Task Scheduler invokes `benchmark_worker.py --once` through `run_worker_once.sh`;
3. worker refreshes benchmark/skill/agent files from GitHub;
4. runner calls Gemini directly;
5. raw result, metadata and manifests publish back to this feature branch;
6. evaluator-only gold standard/rubric are used after the run and are never sent to the model under test.

## Benchmark discipline

- Same model/settings for paired comparisons.
- Change one material variable at a time.
- Gold/rubric never enter model context.
- Record model, temperature, hashes, provider status and token usage.
- Treat model quality, Skill quality and composition quality as separate variables.
- Do not tune indefinitely against one benchmark; use materially different generalization tests.
- Additional model calls/handoffs must earn their complexity through measurable quality or reliability gains.

## Current sequence

1. requirements analysis — **validated**
2. requirements decomposition — **validated/generalized**
3. acceptance criteria — **validated/generalized**
4. test/assurance derivation — **v0.3 retained**
5. Composite BA Delivery Analyst — **v0.2 preferred, B009 generalization queued**
6. specialist pipeline — **experimental; B008 not preferred**
7. next after B009 — solution/change-readiness handoff capability
