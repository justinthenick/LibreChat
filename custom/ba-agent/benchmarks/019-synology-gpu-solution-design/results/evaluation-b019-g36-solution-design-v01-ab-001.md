# Benchmark 019 Evaluation — Synology GPU Solution Design

Job: `b019-g36-solution-design-v01-ab-001`  
Model: `gemini-3.6-flash`  
Temperature: `0.0`

## Scores

| Run | Raw | Penalties | Final | Tokens | Decision |
|---|---:|---:|---:|---:|---|
| Baseline | 88 | -10 | **78/100** | 4,392 | Correct architecture, but overconfident unsupported power/physical blocker plus invented procurement minimums. |
| `design-technical-solution` v0.1.0 | 88 | 0 | **88/100** | 7,778 | Material improvement in outcome preservation, feasibility discipline and architecture boundary, but procurement sizing still invents hard requirements. |

## Baseline evaluation

The baseline gets the central architecture decision right: the local CUDA outcome remains feasible, direct GPU installation into the DS918+ is not a normal/supportable path, and a separate LAN-attached GPU compute node should retain the NAS as storage. It correctly handles PCIe, Thunderbolt, USB, M.2 cache-slot and DSM supportability evidence, and it gives a clear split-compute/storage design.

The main defect is evidence discipline after the architecture decision. It adds DS918+-specific PSU/clearance/thermal claims as an "exact technical blocker" even though those facts were not supplied, triggering the rubric's invented critical power/physical-fact penalty. Its procurement table then hard-codes unsourced CPU core counts, 32 GB RAM, 1 TB NVMe and PSU sizing/overhead rather than carrying them as sizing Unknowns or candidate checks.

## Skill evaluation

The Skill materially improves the reasoning structure. It explicitly separates outcome from mechanism, distinguishes hard blockers from unsupported workarounds, retains the NAS in a valid storage role, describes the compute/storage/user-access boundaries, and makes candidate-specific clearance, cabling and thermal checks explicit.

However, v0.1.0 still has a reusable defect at the architecture-to-procurement boundary: it converts unspecified sizing choices into mandatory requirements. Examples include CUDA compute capability 8.0+, particular CPU generations, 32 GB RAM minimum, 1 TB NVMe minimum, PCIe electrical-generation thresholds, 500–650 W / 80 Plus PSU language and exact OS-version choices. The supplied packet only supports a CUDA-capable NVIDIA GPU around the 12 GB VRAM target, supported Windows/Linux driver path, local SSD as useful, LAN/NAS access, and candidate-dependent physical/power verification.

It also states that 1 GbE is "sufficient" rather than retaining workload adequacy as an Unknown to verify. These issues do not overturn the architecture, but they can cause an agent to hand procurement invented constraints and exclude valid candidates.

## Decision

**Do not generalize v0.1.0 yet.** The Skill has demonstrated material value over baseline, but the procurement-minimum discipline needs one focused correction.

Create v0.2.0 with a strict rule: only supplied or logically necessary capabilities may be hard minimums; targets remain targets; unsized CPU/RAM/SSD/network/power values remain Unknowns or candidate-verification tasks. Candidate-specific PSU connectors, wattage, clearance and cooling must not be fixed before a candidate GPU/host is selected. Then rerun B019 as a Skill-only correction using a unique job ID. If the corrected run reaches the excellent band without new invention, retain v0.2.0 and move to one materially different architecture domain.