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
Status: **frozen / preferred architecture**

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

Composite v0.2 corrected the v0.1 authority/governance failure and retained strong handoffs, constraint survival and end-to-end traceability. The three-specialist pipeline technically worked but amplified upstream semantic errors downstream and cost about 2.28x the tokens.

### Benchmark 009 — Service Ownership Update End-to-End

Gemini 3.5 Flash, temperature `0.0`:

| Architecture | Raw | Penalties | Final | Total tokens |
|---|---:|---:|---:|---:|
| No-agent baseline | **67** | **-18** | **49/100** | **6,602** |
| **Composite v0.2** | **94** | **0** | **94/100** | **10,720** |

B009 is materially different from B008 and confirms generalization. Composite v0.2 preserves the emergency-approval dispute, Candidate Service Registry automation and pilot scope, non-binding Target, Deferred recertification, Unknown retention, process/governance boundaries and full cross-stage traceability without rubric penalties.

Minor deductions were limited to wording of the disputed emergency proposition and omission of a Stage-4 conditional security assurance state. Neither is a production-blocking reusable defect.

**Architecture decision: freeze Composite BA Delivery Analyst v0.2.** Do not tune it further against B008/B009. Re-open only if a later independent benchmark exposes a genuine reusable defect.

## Specialist pipeline infrastructure

Experimental specialist agents:

- `agents/requirements-analyst/AGENT.md`
- `agents/delivery-refinement-analyst/AGENT.md`
- `agents/assurance-analyst/AGENT.md`

Pipeline tooling:

- `tools/agent_pipeline_runner.py`
- pipeline-aware `tools/benchmark_worker.py`

The pipeline runner persists every stage output plus metadata/hash information and passes the prior artifact into the next model call. It is retained for future architecture experiments, but is not the default BA architecture.

## Capability 5 — Solution / Change-Readiness Handoff

Skill:

- `skills/prepare-solution-change-readiness/SKILL.md`
- status: **experimental / Benchmark 010 queued**

Purpose: convert sufficiently mature BA delivery evidence into a controlled handoff for solution/design review and Change Enablement without pretending to be the Solution Architect, Change Manager or approver.

Benchmark:

- `benchmarks/010-solution-change-readiness-handoff`
- queued job: `b010-g35-handoff-v01-ab-001`

The capability should identify what is ready to hand off, unresolved solution/design decisions, test/assurance evidence, deployment/change-readiness dependencies, and process/security/governance constraints without inventing implementation architecture, CAB approval, release dates, rollback mechanisms or decision authority.

## Capability 6 — ITIL 4 Alignment / Readiness Assessment

Skill:

- `skills/assess-itil-alignment/SKILL.md`
- current version: **0.1.0**
- status: **experimental / Benchmark 011 queued**

Purpose: assess supplied BA, solution-handoff, release, deployment, configuration and change-readiness evidence against relevant **ITIL 4 practice concepts** while keeping ITIL guidance separate from organisation-specific policy and authority.

The lab deliberately uses the term **ITIL alignment/readiness**, not formal `ITIL compliance`, because this capability is not a certification audit. Missing evidence is reported as `Not evidenced` rather than automatically `Non-compliant`.

Core controls:

- do not invent universal CAB, rollback, PIR, change-category, CMDB-tooling or approval requirements;
- do not infer Change Authority / Emergency Change Authority from job title or stakeholder activity;
- distinguish Change Enablement, Release Management, Deployment Management and Service Configuration Management concerns;
- treat explicit internal policy separately from ITIL guidance and stakeholder opinion;
- preserve Candidate/Target/Deferred/Disputed/Unknown status;
- do not invent an official ITIL maturity/capability score without authorised ITIL Maturity Model criteria;
- trace findings to supplied evidence.

Public reference provenance is recorded in `references/itil-public-basis.md` and is limited to high-level PeopleCert public descriptions rather than licensed Practice Guide content.

### Benchmark 011 — Emergency Payment Change ITIL Alignment

Benchmark path:

- `benchmarks/011-emergency-change-itil-alignment`

Queued job:

- `b011-g35-itil-v01-ab-001`
- model: `gemini-3.5-flash`
- mode: baseline + skill
- temperature: `0.0`

Benchmark 011 tests Change Enablement risk/authorisation/schedule concerns, Release vs Deployment separation, Service Configuration Management evidence, local-policy vs ITIL-guidance separation, unknown emergency authority, and traps such as unsupported `ITIL requires CAB`, rollback/PIR mandates, false compliance conclusions and unofficial maturity scoring.

Development plan:

1. score B011 baseline and v0.1 independently;
2. if v0.1 shows a reusable defect, make one focused correction and rerun Skill-only;
3. if strong, create a materially different ITIL-alignment generalization benchmark rather than tuning against B011;
4. only after isolated validation, test composition with the frozen BA / solution-change-readiness stack;
5. keep the frozen Composite BA Delivery Analyst v0.2 unchanged unless an independent composition test reveals a real cross-capability defect.

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
5. Composite BA Delivery Analyst — **v0.2 frozen / preferred**
6. specialist pipeline — **experimental; not preferred**
7. solution/change-readiness handoff — **B010 active**
8. ITIL 4 alignment/readiness — **B011 active**
9. composition of validated handoff + ITIL alignment into the preferred BA workflow — **after isolated validation**
