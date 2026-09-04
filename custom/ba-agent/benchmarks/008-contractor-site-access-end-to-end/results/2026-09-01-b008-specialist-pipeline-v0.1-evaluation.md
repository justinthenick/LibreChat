# Benchmark 008 — Three-Specialist Pipeline v0.1 Evaluation

**Model:** `gemini-3.5-flash`  
**Runner result:** `b008-g35-specialists-v01-003-gemini-3.5-flash-pipeline-01.md`  
**Temperature:** `0.0`  
**Architecture:** Requirements Analyst -> Delivery Refinement Analyst -> Assurance Analyst  
**Result:** **53/100 — weak end-to-end result; specialist handoffs amplify downstream invention**

## Score

| Area | Score |
|---|---:|
| Requirements-analysis fidelity | 18/20 |
| Delivery decomposition and Stage 1 -> 2 handoff | 16/20 |
| Acceptance-criteria discipline and Stage 2 -> 3 handoff | 10/15 |
| Test / assurance derivation and Stage 3 -> 4 handoff | 11/15 |
| Cross-stage traceability and consistency | 12/15 |
| No-invention / process-boundary discipline | 6/10 |
| End-to-end usability and efficiency | 3/5 |
| **Raw** | **76/100** |
| Penalties | **-23** |
| **Final** | **53/100** |

## What worked

The specialist architecture preserved several important controls across three independent model calls:

- overall readiness remained `Partially Ready`;
- the after-hours approval dispute remained unresolved with Decision Owner `Unknown`;
- Building Access Platform automation and the Sydney Metro/Newcastle pilot remained Candidate;
- the two-business-hour objective remained a non-binding Target;
- automatic revocation remained Deferred;
- process/security constraints generally survived into downstream work;
- stage artifacts were persisted with stable IDs, hashes and explicit handoff content;
- the final Assurance stage maintained substantial traceability back through the refinement artifact.

So the pipeline mechanism itself works technically and does not inherently destroy all upstream state.

## Material defects introduced/amplified through handoffs

### 1. Unsupported workflow/routing mechanics

Stage 1 changed the sourced business rule `Site Access Team approval before issuance` into a requirement that the system **route** normal-hours requests. It also introduced a `workflow routing engine` in a risk statement. The refinement and assurance stages then inherited and repeated that routing concept as if it were established behavior.

This is exactly the kind of semantic drift an explicit handoff is supposed to prevent.

### 2. Invented actor

The refinement stage introduced a `compliance auditor` persona for evidence recording. No such actor is established in the source.

### 3. Unknown retention converted into committed behavior

The largest cross-stage failure is `AC-US003-2`, which states that evidence **must not be purged or deleted while the retention decision is unresolved**. The source says only that the retention period is Unknown. It does not establish a temporary no-delete rule.

The Assurance Analyst then accepted that invented criterion and created committed test `TC-US003-2` to verify the no-purge behavior. This is a clear example of one specialist laundering an upstream invention into apparently well-traced downstream assurance.

### 4. Additional mechanism leakage

The pipeline also uses unsupported or unnecessarily implementation-adjacent concepts including `authentication protocols`, `record and store`, and a workflow-engine rework risk. These are narrower than the baseline's architecture invention, but they show that handoff persistence alone does not guarantee semantic fidelity.

## Penalties

- **-10** — invented `compliance auditor` current-scope actor.
- **-5** — unsupported workflow/routing-engine behavior carried across stages.
- **-5** — invented no-purge/no-delete behavior for an Unknown retention requirement.
- **-3** — material status drift: Unknown retention became a committed acceptance criterion and committed test.

No penalty is applied merely for using the words `store` or `authentication protocols`; those are reflected in raw scoring rather than double-counted.

## Token / cost comparison

| Architecture | Score | Total tokens |
|---|---:|---:|
| No-agent baseline | **17/100** | **6,488** |
| Composite BA Delivery Analyst v0.2 | **95/100** | **10,439** |
| Three-specialist pipeline v0.1 | **53/100** | **23,748** |

The specialist pipeline uses about **2.28x** the total tokens of the composite v0.2 while scoring **42 points lower**.

## Architecture decision

**Prefer the single-call Composite BA Delivery Analyst v0.2. Do not retain the three-specialist pipeline as the default BA architecture.**

Benchmark 008 provides strong evidence that the additional calls and persisted handoffs do not currently improve reliability. In this run they create an error-propagation problem: an upstream invention becomes easier for later specialists to treat as authoritative because it arrives inside a structured handoff artifact.

The pipeline runner remains useful experimental infrastructure, but the next validation step should be a **fresh end-to-end generalization benchmark for Composite BA Delivery Analyst v0.2**, not further tuning of the specialist pipeline against Benchmark 008.
