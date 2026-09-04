# Agent Engineering Lab

## Objective

Build and validate agents that **select, sequence and govern already-tested Skills** rather than duplicating those Skills inside ever-larger prompts.

A Skill is a bounded capability. An Agent is responsible for deciding **which capability to use, in what order, when to stop, and how to preserve evidence/authority/status across handoffs**.

## Engineering sequence

Agent work follows four gates:

1. **Routing test** — can the Agent select the right Skills, omit irrelevant Skills and order them correctly from a messy request?
2. **Controlled composition test** — execute the proposed architecture with fixed stages and measure whether handoffs improve the result without semantic drift.
3. **Dynamic invocation test** — only after routing and controlled composition are strong, test an Agent that actually invokes its selected Skills dynamically.
4. **LibreChat production registration** — expose only validated Agents to the live client.

Do not jump directly to dynamic multi-agent autonomy. Extra calls, routers and handoffs must earn their complexity through measured quality or reliability.

## Cross-agent controls

Every Agent must:

- use only capabilities supported by its allowed Skill set;
- keep Candidate, Target, Deferred, Disputed and Unknown states visibly non-committed;
- never infer decision authority from authorship, sponsorship, job title or participation;
- never turn missing evidence into invented approvals, gates, architecture or implementation mechanisms;
- preserve traceability through downstream handoffs;
- stop or narrow scope when an upstream artifact is not mature enough for a downstream capability;
- distinguish a user-requested end state from a proposed implementation mechanism;
- avoid invoking a Skill merely because it exists.

## Agent benchmark dimensions

Score Agent behavior separately from Skill behavior:

- **Routing accuracy** — correct Skill selection and omission.
- **Ordering** — prerequisites and dependency order are respected.
- **Stop discipline** — Agent does not force downstream work through unresolved blockers.
- **State preservation** — downstream certainty never exceeds upstream evidence.
- **Authority discipline** — no invented owners, CAB, Change Authority or governance.
- **Composition gain** — additional Skill stages must improve or preserve quality enough to justify cost.
- **Efficiency** — token/call growth is recorded and compared with simpler architectures.

A routing defect is an Agent defect. A defect inside a correctly selected Skill is a Skill defect. A state that is correct in one stage but corrupted at a handoff is a composition defect.

## Agent portfolio

### A001 — BA Change Delivery Orchestrator

First Agent under this method.

Allowed capability family:

- `analyze-requirements`
- `decompose-requirements`
- `elaborate-acceptance-criteria`
- `derive-test-cases`
- `prepare-solution-change-readiness`
- `assess-itil-alignment`

Initial validation uses Benchmark 023:

- routing A/B: baseline vs Agent v0.1;
- control composition: frozen Composite BA Delivery Analyst v0.2 -> Change Readiness v0.2;
- candidate composition: frozen Composite BA Delivery Analyst v0.2 -> Change Readiness v0.2 -> ITIL Alignment v0.2.

This deliberately separates **Agent routing quality** from **composition quality**.

### Planned after A001

- **Solution Architecture / Procurement Agent** — `design-technical-solution` plus procurement expansion/verification Skills.
- **Procurement Agent** — market expansion plus evidence/compatibility verification, with domain classification.
- **Manuscript Engineering Agent** — structure analysis first; editing capabilities only after decomposition/reconstruction is validated.

## Release rule

An Agent is not released merely because its component Skills are strong. It must pass an independent Agent benchmark with zero critical semantic/authority penalties and must not be materially worse than the simpler control architecture without a documented reason.
