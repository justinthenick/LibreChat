---
name: design-technical-solution
description: Turn an intended technical outcome and known environment into an evidence-grounded feasible solution design, challenge infeasible implementation ideas without losing the outcome, and produce a procurement-ready specification only after the architecture is defensible.
---

# Design Technical Solution

Version: **0.4.0**

## Purpose

Translate a desired technical outcome into an implementable architecture. The user may arrive with a proposed implementation that is impossible, unsupported, fragile, or simply not the best way to achieve the real outcome.

The Skill must preserve the **outcome** while being willing to reject or reshape the **implementation idea**.

## Core principle

**Do not argue with the goal merely because the proposed mechanism is wrong. Identify the actual blocker, preserve the intent, and design the smallest defensible architecture that still achieves the outcome.**

## Required flow

1. **Restate the outcome and success criteria.** Separate what the user is trying to achieve from how they initially proposed doing it.
2. **Build an evidence/state map.** Distinguish supplied facts, known constraints, assumptions, preferences and Unknowns. Do not silently fill hardware, software, licensing, network or supportability gaps.
3. **Assess the proposed implementation.** Classify it as `Feasible`, `Conditionally feasible`, `Infeasible`, or `Unknown / needs verification`, and explain the specific evidence behind that classification.
4. **Create a constraint register.** Consider only relevant dimensions, such as physical interfaces/clearance, power, thermal limits, CPU/GPU architecture, OS/driver support, storage, networking, security, identity, integration, lifecycle/supportability, operability, licensing and budget.
5. **Distinguish hard blockers from soft trade-offs.** A missing physical interface or unsupported runtime is different from a performance concern, target or preference.
6. **Design alternatives around the blocker.** If the proposed implementation is infeasible, present one or more architectures that preserve the outcome. Prefer simple, supportable patterns over hacks unless the user explicitly accepts experimental risk.
7. **Select a preferred architecture.** Explain why it is the smallest/lowest-risk design that meets the outcome. State important rejected alternatives and why they lost.
8. **Describe boundaries and integration.** Show which component owns compute, storage, networking, orchestration, user access and security where relevant. Make remote/offloaded components explicit rather than pretending they are part of the original device.
9. **Identify Unknowns and verification actions.** Ask only for information that can materially change architecture or sizing. Convert unresolved facts into verification tasks rather than guesses.
10. **Produce a procurement handoff only after the architecture is defensible.** Specify evidence-supported capabilities, interfaces, hard minimums, targets, preferences and candidate-verification tasks. Do not jump directly to product listings or make/model recommendations unless a procurement/search capability is deliberately invoked next.
11. **Keep architecture and procurement separate.** Architecture determines what must be bought; procurement determines which exact candidate satisfies it.

## Feasibility discipline

- Device-family capability is not proof of the user's exact unit/configuration.
- A USB port is not automatically a generic expansion bus for an internal PCIe device.
- An internal connector or storage slot is not automatically a supported general-purpose expansion path.
- Physical possibility does not equal driver/OS/vendor supportability.
- A workaround that requires undocumented adapters, firmware changes, unsupported kernels or invasive modification must be labelled experimental, not presented as a normal production design.
- Existing components may be retained in a new role. A device that cannot perform the new compute function may still remain valuable as storage, orchestration, backup, monitoring or network infrastructure.
- Do not manufacture implementation requirements that the outcome does not need.
- Do not claim a performance threshold is sufficient merely because the interface exists. If adequacy depends on workload, keep it as an Unknown or validation task.
- Do not add unsupported hazard, failure or support claims to strengthen an already-proven blocker. State only the risk supported by the evidence.

## Blocker evidence gate

Before calling something a hard blocker, ask: **is this blocker explicitly supplied by the evidence, or is it logically unavoidable from supplied facts?** If neither is true, it is not a blocker yet; classify it as an Unknown or omit it.

Rules:

- Once supplied evidence already proves the proposed mechanism infeasible, do not pile on plausible device-specific claims about PSU capacity, power delivery, thermal headroom, chassis clearance, internal wiring, firmware behavior or driver internals unless those facts are supplied.
- General engineering knowledge is not permission to invent exact-unit facts. For example, knowing that desktop GPUs consume substantial power does not prove a particular appliance's PSU, adapter, wiring or cooling is inadequate unless the evidence establishes that.
- Do not introduce derived numeric performance claims such as effective throughput, transfer times, wattage needs, latency or utilization limits unless the calculation is necessary to the decision and all inputs are supplied. If workload adequacy is unresolved, retain it as an Unknown and propose a validation action.
- Do not turn a plausible implementation detail into a requirement simply because it is common. Standard patterns may be offered as options or preferences, not mandatory facts, unless the architecture truly requires them.

## Requirement-strength discipline

Before putting any value into a procurement specification, classify it as one of:

- **Hard minimum** — explicitly supplied by the user/evidence, or logically necessary to make the chosen architecture function.
- **Target** — desired sizing/performance level that should guide procurement but may be negotiable.
- **Preference** — value, form-factor, operational or supportability choice that should influence ranking but does not define feasibility.
- **Unknown / verify** — unresolved sizing, compatibility or candidate-specific fact that must not be guessed.

Rules:

- A target must not silently become a hard minimum. Wording such as `around`, `desired`, `preferred`, `target` or similar remains a target unless the user explicitly makes it mandatory.
- Do not invent CPU architectures/generations/core counts, RAM quantities, SSD technologies/capacities, PCIe generations, PSU wattages/efficiency ratings, connector types, OS versions, network speeds or similar thresholds unless supplied or logically necessary from evidence.
- If CPU/RAM/SSD/network sizing is unresolved, write `sized to workload; verify` and name the sizing question.
- If local SSD is merely allowed or useful, do not promote NVMe/M.2 or a capacity to a hard minimum.
- Candidate-specific GPU clearance, PSU wattage/connectors and cooling remain candidate checks until the exact GPU/host combination is known.
- If an interface is present but workload adequacy is unknown, say so explicitly rather than declaring it sufficient.
- Do not add convenience features such as Wake-on-LAN, particular management software or a specific operating-system version unless supplied; keep them optional choices or Unknowns.

## Evidence-to-requirement provenance gate

Before finalizing the preferred architecture or Procurement handoff, audit every constraint and requirement back to the evidence map.

- A supplied `Preference` remains a preference. It may explain why one feasible option is preferred, but it must not be described as the only feasible design or as a hard Procurement minimum unless the user explicitly promotes it.
- An `Unknown` may create a decision question, sizing question or candidate-verification condition. It must not be silently resolved into a topology, implementation choice, compatibility claim or mandatory requirement.
- Keep independently unresolved architecture layers separate. A defensible physical or integration path does not establish the logical network boundary, security model, orchestration choice, deployment mechanism or operating process.
- State **what evidence must be established**, not a particular inspection tool, test method, construction technique or operating product, unless that method is supplied or logically indispensable.
- Do not turn a plausible implementation convention into a candidate requirement. Exact materials, connector types, packaging, protocols, validation tools and management mechanisms remain downstream choices when the outcome does not require them.
- If a calculation is necessary, show only conclusions supported by supplied inputs and verify the arithmetic. Otherwise state the comparison directly without invented percentages, effective-performance figures or component counts.
- In each Procurement row, ensure the declared strength matches its source: fact or unavoidable function may support a hard minimum; target supports Target; preference supports Preference; unresolved compatibility supports Unknown / verify.

If an architecture is preferred partly because it best satisfies preferences, say that explicitly. Do not rewrite those preferences as feasibility blockers.

## Procurement handoff format

When the design is ready for procurement, produce a short specification containing:

- component role;
- evidence-supported hard minimum capabilities;
- targets separately labelled from hard minimums;
- required interfaces/connectivity;
- power/physical constraints only where evidence supports them;
- software/driver/platform compatibility;
- storage/network requirements at the strength actually supported by evidence;
- preferences and value criteria;
- exact Unknowns that procurement must verify on each candidate.

Do **not** turn a preferred architecture into a specific product recommendation without candidate evidence.

## Recommended output

### 1. Outcome and success criteria

### 2. Current-state / evidence map
`Fact or assumption | Status | Architectural significance`

### 3. Proposed-approach feasibility
`Classification | Blockers | Soft constraints | Verification needed`

### 4. Architecture options
`Option | How it achieves the outcome | Advantages | Trade-offs / risks | Supportability`

### 5. Preferred solution
Include a compact component/data-flow description.

### 6. Unknowns and validation actions

### 7. Procurement-ready specification
Use `Requirement | Strength | Evidence / rationale | Candidate verification` where useful. Only include it if architecture is sufficiently resolved.

## Final audit

- Did I preserve the real outcome even if I rejected the proposed implementation?
- Did I state exactly why something is infeasible rather than hand-waving?
- Is every hard blocker supported by supplied evidence or unavoidable logic from supplied facts?
- Did I avoid adding plausible but unevidenced device-specific blockers after feasibility was already proven?
- Did I distinguish evidence from assumption?
- Did I avoid unsupported hacks masquerading as a normal design?
- Did I give a viable alternative when the original mechanism fails?
- Did I keep product selection downstream of architecture?
- Did every hard minimum come from evidence or unavoidable architectural necessity?
- Did I keep targets, preferences and Unknowns from being silently promoted into mandatory procurement requirements?
- Did I avoid unsupported numeric performance calculations and convenience features masquerading as requirements?
- Can every constraint and Procurement row be traced to evidence at the same requirement strength?
- Did I keep unresolved architecture layers unresolved rather than completing them with a common implementation pattern?
- Did I ask for the evidence condition needed without inventing the validation method?
