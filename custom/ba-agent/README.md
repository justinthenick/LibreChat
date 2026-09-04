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

B009 is materially different from B008 and confirms generalization. Composite v0.2 preserves status/authority and cross-stage traceability without rubric penalties.

**Architecture decision: freeze Composite BA Delivery Analyst v0.2.** Re-open only if a later independent benchmark exposes a genuine reusable defect.

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
- current version: **0.2.0**
- status: **retained after B010; B013 generalization currently provider-quota blocked**

Purpose: convert sufficiently mature BA delivery evidence into a controlled handoff for solution/design review and Change Enablement without pretending to be the Solution Architect, Change Manager or approver.

### Benchmark 010 — Solution / Change-Readiness Handoff

Gemini 3.5 Flash, temperature `0.0`:

| Run | Raw | Penalties | Final | Tokens |
|---|---:|---:|---:|---:|
| Baseline | 95 | -30 | **65/100** | 4,467 |
| v0.1 | 95 | -20 | **75/100** | 8,661 |
| **v0.2 focused rerun** | **100** | **0** | **100/100** | **9,609** |

v0.1 exposed a reusable **gap-to-gate promotion** defect by converting missing downstream evidence into unsourced sign-off/approval gates. v0.2 added one focused semantic control: missing evidence categories may not become mandatory approvals/sign-offs/CAB/owner/governance gates unless the source explicitly establishes them.

The B010 v0.2 rerun removed that defect completely while preserving status, evidence and traceability discipline. No solution architecture, Change authority, CAB decision, dates, rollback mechanism or test execution was invented.

Decision: **retain `prepare-solution-change-readiness` v0.2.0.** Do not tune further on B010.

### Benchmark 013 — Vendor Export Solution / Change-Readiness Handoff

B013 is the materially different handoff generalization benchmark. It tests an external-vendor invoice-exception export with Candidate SFTP, disputed tokenisation with Decision Owner Unknown, a 15-minute Target, Deferred scheduled exports, Unknown file retention, draft-but-not-approved field mapping, unverified MFT-gateway reuse and missing downstream implementation/Change evidence.

Job: `b013-g35-handoff-v02-ab-001`, Gemini 3.5 Flash, temperature `0.0`, baseline + v0.2.

The first baseline attempt at 2026-09-02 00:40:29 Australia/Sydney was **quota_blocked** before model execution. Gemini reported the free-tier `generate_content` daily request limit of 20 requests for `gemini-3.5-flash` had been exhausted. The NAS worker intentionally attempts each unique job ID once, so this job will not automatically retry; a new job ID must be queued after quota becomes available.

No B013 score exists yet. Do not infer handoff generalization from the provider-blocked attempt.

## Capability 6 — ITIL 4 Alignment / Readiness Assessment

Skill:

- `skills/assess-itil-alignment/SKILL.md`
- current version: **0.2.0**
- status: **retained / generalized enough for composition planning**

Purpose: assess supplied BA, solution-handoff, release, deployment, configuration and change-readiness evidence against relevant **ITIL 4 practice concepts** while keeping ITIL guidance separate from organisation-specific policy and authority.

The lab deliberately uses **ITIL alignment/readiness**, not formal `ITIL compliance`. Missing evidence is reported as `Not evidenced` rather than automatically `Non-compliant`.

### Benchmark 011 — Emergency Payment Change ITIL Alignment

Gemini 3.5 Flash, temperature `0.0`:

| Run | Final | Tokens |
|---|---:|---:|
| Baseline | **92/100** | 5,420 |
| `assess-itil-alignment` v0.1 | **98/100** | 7,057 |

v0.1 cleanly separated local policy from ITIL guidance, preserved the Unknown Emergency Change Authority, rejected universal CAB/rollback/PIR/CMDB requirements, distinguished Change Enablement vs Release vs Deployment vs Service Configuration Management, and incurred zero penalties.

### Benchmark 012 — Planned Certificate Change ITIL Alignment

Gemini 3.5 Flash, temperature `0.0`:

| Run | Final | Tokens | Decision |
|---|---:|---:|---|
| Baseline | **94/100** | 5,211 | Strong control with minor readiness precision issues. |
| `assess-itil-alignment` v0.1 | **96/100** | 6,759 | Strong but exposed a gap-to-gate variant. |
| **`assess-itil-alignment` v0.2 focused rerun** | **100/100** | **7,303** | **Retain; zero penalties.** |

B012 v0.1 exposed a narrower **gap-to-gate promotion** defect: recovery/backout and configuration-update ownership/timing were labelled as required pre-authorisation evidence even though the packet did not establish those as mandatory local gates.

v0.2 made one focused correction: relevant `Not evidenced` practice concerns may be raised as questions/clarifications but may not become mandatory gates, approvals or pre-authorisation prerequisites without explicit local-policy/source support.

The focused rerun confirms the correction. Recovery/backout and configuration-update ownership/timing remain clarifications; the schedule conflict remains a genuine local-policy gate; Standard Change scope and Unknown Change Authority are preserved; Release, Deployment and Service Configuration Management remain distinct; and no universal CAB/rollback/PIR/CMDB/security/maturity/execution obligation is invented.

Decision: **retain `assess-itil-alignment` v0.2.0.** B011 plus corrected B012 provide enough isolated evidence for composition planning. Do not retune against these benchmarks for cosmetic score gains.

Do not modify the frozen Composite BA Delivery Analyst merely to add ITIL wording. Composition remains deferred until the B013 solution/change-readiness generalization completes cleanly.

## Capability 7 — Technical Solution Architecture

Skill:

- `skills/design-technical-solution/SKILL.md`
- current version: **0.4.0**
- status: **focused generic correction queued for B022 validation**

Purpose: preserve the intended technical outcome while challenging an impossible or unsupported implementation, expose architecture-changing Unknowns, and create a capability-level Procurement handoff only after the design is defensible.

### Benchmark 019 — Synology GPU Solution Design

The hardware-domain sequence established that the Skill can reject direct GPU attachment while preserving the AI-workload outcome and selecting split compute. v0.3 scored **82/100** after a critical evidence-invention penalty. The preferred architecture remained correct, but the output invented M.2 modification mechanics and derived throughput effects. Decision: do not tune the Synology case further; retain v0.3 as a candidate and test elsewhere.

### Benchmark 020 — Vendor Webhook Integration Architecture

The clean Gemini 3.5 Flash A/B pair closed at **baseline 94/100 vs Skill v0.3 93/100**, both with zero penalties. v0.3 safely rejected the nonexistent webhook while preserving the automation objective and designing the expected polling adapter. The B019 invention did not recur as a material failure, but the strong baseline was marginally cleaner and cheaper. Decision: no B020 tuning and no composition yet.

### Benchmark 022 — Campus Building Network Link Architecture

B022 is the exact next standalone gate and the third materially different domain. It tests whether v0.3 rejects a 900 metre direct copper-Ethernet mechanism, preserves the campus-connectivity outcome, avoids invented optical/transceiver compatibility, keeps 1 Gbit/s as a Target, and separates BA/service questions from Procurement candidate verification.

The first job, `b022-g35-solution-design-v03-ab-001`, returned `provider_busy` for both sides. Replacement job `b022-g37-solution-design-v03-ab-002` completed a fresh Gemini 3.7 Flash pair at temperature `0.0`.

The baseline scored **88/100** and Skill v0.3 scored **83/100**, both with zero penalties. Both selected the correct passive optical topology, but v0.3 more strongly promoted preferences and plausible implementation details into hard architecture/Procurement requirements. It converted preferred electrical isolation and avoidance of midpoint cabinets into hard constraints, prescribed cable construction/testing details, and described a Layer-2 trunk while the L2/L3 boundary remained Unknown.

Decision: **do not retain v0.3 for composition.** v0.4 adds one generic evidence-to-requirement provenance gate: preferences cannot become blockers/hard minimums, Unknowns cannot silently resolve architecture layers, validation conditions must not invent methods, and every Procurement row must preserve its source strength.

Focused rerun: `b022-g37-solution-design-v04-skill-003`, Gemini 3.7 Flash, Skill-only at temperature `0.0`, against the preserved B022 baseline.

Do not compose Solution Architecture with BA or Procurement until v0.4 clears the B022 gate.

## Test timeline

`custom/ba-agent/TEST-TIMELINE.md` is the permanent experiment ledger. From runner-native B003 onward it records exact start/end times, duration, scores, token usage where relevant and resulting decisions. Pre-runner B001/B002 entries use GitHub result-recording timestamps and are labelled accordingly.

## Automated benchmark loop

1. GitHub queue: `custom/ba-agent/automation/jobs.json`;
2. Synology DSM Task Scheduler invokes `benchmark_worker.py --once` through `run_worker_once.sh`;
3. worker refreshes benchmark/skill/agent files from GitHub;
4. runner calls Gemini directly;
5. raw result, metadata and manifests publish back to this feature branch;
6. evaluator-only gold standard/rubric are used after the run and are never sent to the model under test.

The worker attempts each unique job ID once. A provider-blocked run therefore needs a **new job ID** for an intentional retry after quota becomes available; this avoids repeated polling consuming or hammering provider quota.

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
7. solution/change-readiness handoff — **v0.2 retained; B013 retry required after provider quota resets**
8. ITIL 4 alignment/readiness — **v0.2 retained/generalized enough for composition planning**
9. composition of validated handoff + ITIL alignment into the preferred BA workflow — **after B013 completes cleanly**
