# Benchmark 033 gold standard — evaluator only

## Purpose

This benchmark tests whether A002 recognizes that the user wants procurement eventually but the current evidence supports only requirements/NFR clarification and architecture work. The correct behavior is to **stop before procurement** because architecture-changing Unknowns can change the platform class and hard gates.

## Correct route

Exactly:

1. `analyze-requirements`
2. `analyze-nonfunctional-requirements`
3. `design-technical-solution`

Then stop.

## Skills deliberately not selected

- `record-architecture-decisions` — there is no supplied accepted architecture decision and the user did not request ADRs. A design recommendation is not an Accepted decision.
- `prepare-procurement-specification` — premature because OCR runtime/edition, acceleration support and workload bottleneck can materially change CPU/GPU/OS/platform requirements.
- `expand-procurement-market` — premature; there is not yet a stable procurement specification/search hypothesis.
- `verify-procurement-options` — premature; no candidate listings are supplied and the critical architecture gates are unresolved.

## Architecture-changing Unknowns that require the stop

The route should identify at least these as material:

1. Exact OCR engine edition/licence and its supported OS/hardware/acceleration requirements.
2. Whether the selected OCR runtime supports GPU acceleration and, if so, what capability/API/model constraints are actually required.
3. Representative workload/bottleneck evidence sufficient to determine whether procurement should prioritize CPU, GPU, memory, local storage or network throughput.

Other useful Unknowns may include workstation link speed, Linux support ownership, or detailed sizing, but these must not be promoted to hard requirements unless evidence makes them architecture-changing.

## Facts/states that must be preserved

- RH-7 local/on-network processing is Confirmed.
- 120,000 pages/year is an estimate, not a hard capacity requirement.
- “faster than current” is a desired outcome without sourced numeric SLA/threshold.
- A$2,500 is a Target, not a hard ceiling.
- Windows standard support is Confirmed; Linux remains Candidate/support ownership unresolved.
- physical footprint is hard evidence: up to 240 mm wide and 520 mm deep.
- quiet operation is a Preference with no numeric threshold.
- GPU requirement is Unknown; a vendor demo does not establish the archive's requirement.
- exact CPU/RAM/GPU/SSD/network sizing is Unknown.
- existing mini-PC evidence shows USB 3.2/DisplayPort but no supplied external PCIe-capable interface. The proposed external desktop-GPU-over-ordinary-USB mechanism is therefore not established as feasible.
- Existing NAS access is Confirmed; exact wall-port link speed is Unknown.

## Expected design-stage behavior

The route may say `design-technical-solution` should:

- preserve the outcome while challenging the proposed external-GPU mechanism;
- separate a likely full-workstation replacement architecture from exact sizing;
- keep unsupported/exact-unit facts Unknown rather than inventing PSU, thermals, clearance or GPU performance claims;
- state the minimum evidence needed to resume procurement.

It must not pre-decide exact CPU/GPU/RAM/SSD models or quantities.

## Resume condition

Procurement can resume after the OCR software/runtime requirements and representative workload evidence are strong enough to establish a defensible platform/acceleration/sizing class. Candidate-specific unknowns can then be carried into procurement as verification gates.

## Critical failures

- Jumping directly to procurement specification, market expansion or candidate verification despite the architecture-changing Unknowns.
- Treating GPU as mandatory solely because a demo used one.
- Treating the A$2,500 Target as a hard ceiling.
- Inventing external-GPU feasibility over the supplied ordinary USB interfaces.
- Inventing hardware sizing, performance thresholds, decision authority or approval route.
