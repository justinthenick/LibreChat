# Technical Solution Architecture Lab

This track develops a reusable capability that turns a desired technical outcome into a feasible architecture before procurement or implementation begins.

## Intended operating flow

`Outcome -> Current environment -> Evidence/constraints -> Feasibility -> Architecture options -> Preferred design -> Unknowns/verification -> Procurement-ready specification -> Procurement`

The governing principle is: **preserve the outcome; challenge the proposed mechanism when the evidence says it will not work.**

## Initial Skill

### `design-technical-solution` v0.1.0

Purpose: assess a proposed implementation against known technical constraints, identify hard blockers versus softer trade-offs, create alternatives that preserve the user's real objective, select a maintainable architecture, and produce a capability-level procurement handoff without prematurely shopping for products.

Key controls:

- outcome and implementation are separate;
- infeasible mechanisms must be rejected explicitly, not hand-waved;
- physical possibility, software support and vendor supportability are separate questions;
- unsupported hacks are labelled experimental rather than presented as ordinary production design;
- exact-unit/device facts remain Unknown unless evidenced;
- procurement begins only after the architecture has defined what must be sourced.

## Benchmark sequence

### B019 — Synology NAS GPU outcome-to-architecture

Status: **complete — v0.3 scored 82/100; correct architecture with residual evidence invention**.

Tests the core pattern directly: the user wants local CUDA-class AI acceleration and initially proposes installing a desktop NVIDIA GPU into a Synology DS918+. The supplied evidence makes that direct mechanism infeasible but leaves the outcome achievable through a separate LAN-connected GPU compute node while retaining the NAS for storage/services.

Primary evaluation question: does the Skill reject the impossible mechanism without rejecting the goal, then produce a clean split-compute architecture and procurement-ready capability specification without inventing hardware paths?

### Generalization sequence

Do not create all benchmarks at once; each next benchmark should target a distinct reasoning risk exposed by the previous result.

Candidate domains for later tests:

1. **Network/infrastructure:** desired remote/high-speed service where the proposed router/NAS interface or topology cannot directly provide the requested capability; test topology alternatives and security boundaries.
2. **Software/integration:** desired automation/integration where the proposed API or platform lacks a required capability; test adapter/service/event-driven alternatives rather than inventing endpoints.
3. **Edge/IoT:** camera/sensor outcome with compute/power/interface limits; test split edge/central processing and bandwidth trade-offs.
4. **Home/AV or appliance integration:** outcome where physical/interface compatibility blocks the first idea but an alternate topology can satisfy it.

### B020 — Vendor webhook-to-polling integration

Status: **complete — baseline 94/100; v0.3 93/100; zero penalties**.

The Skill safely generalized to software/integration, but did not improve on a strong baseline and was more prescriptive in its implementation handoff.

### B022 — Campus building network link

Status: **complete — baseline 88/100; v0.3 83/100; zero penalties**.

Both runs selected the correct passive optical topology. v0.3 nevertheless promoted preferences and plausible implementation details into hard constraints and Procurement requirements, including electrical-isolation/cable-construction strength and an unresolved Layer-2 boundary.

Decision: **v0.3 is not ready for composition.** Apply one generic provenance/requirement-strength correction and rerun only the Skill side of B022 against the existing Gemini 3.7 baseline. Do not add network-specific rules.

After the corrected Skill clears the third-domain gate, consider composing a Solution Architect agent around the Skill plus requirements analysis and, downstream, the procurement Skills.

## Composition target

Longer term:

`User goal -> Requirements clarification -> Solution architecture -> User design decision -> Procurement discovery/verification -> Implementation/change readiness`

The Solution Architect should not silently invoke procurement before the architecture is accepted. The procurement agent/Skills should receive a clean capability specification and explicit Unknowns to verify.

## Testing discipline

- Same model/settings for baseline vs Skill A/B.
- Fixed evidence packets; no hidden web browsing in architecture benchmarks.
- Gold standard and rubric remain evaluator-only.
- Penalize invented interfaces/supportability and false feasibility heavily.
- Penalize rejecting an achievable outcome merely because the user's first mechanism is impossible.
- Reward the smallest supportable architecture that preserves the outcome.
- Do not tune to one hardware example; generalize across materially different domains before composition.
