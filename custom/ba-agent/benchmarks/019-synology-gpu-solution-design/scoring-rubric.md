# Benchmark 019 — Scoring Rubric

This file is evaluator-only and must not be sent to the model under test.

Score out of 100 before penalties.

## 1. Outcome vs implementation separation — 15 points

- Clearly preserves the local GPU/AI outcome while separating it from the proposed “put GPU in NAS” mechanism: 8
- Does not reject the entire objective merely because direct installation is blocked: 4
- States useful success criteria rather than restating only the hardware idea: 3

## 2. Direct feasibility and blocker accuracy — 25 points

- Correctly classifies direct desktop-GPU installation in the DS918+ as infeasible as a normal/supportable design: 5
- Identifies no user-accessible PCIe GPU slot: 6
- Identifies no Thunderbolt/eGPU path: 4
- Does not misrepresent USB as a normal PCIe GPU-host path: 3
- Does not treat vendor-intended M.2 cache slots as supported GPU expansion: 4
- Recognizes supplied DSM/NVIDIA CUDA supportability constraint: 3

## 3. Alternative architecture quality — 25 points

- Proposes a separate LAN-connected GPU compute node while retaining NAS storage/services: 8
- Places AI execution on compute node and durable storage/output on NAS: 5
- Includes local SSD/model/cache role where appropriate: 3
- Describes SMB/NFS/network integration clearly: 3
- Gives at least one sensible alternative (consolidated GPU server/cloud/experimental path) and explains trade-off: 3
- Selects a preferred architecture with a defensible supportability/maintainability rationale: 3

## 4. Constraints, Unknowns and verification discipline — 15 points

- Distinguishes hard blockers from performance/preferences: 4
- Identifies architecture-relevant Unknowns without inventing facts: 5
- Converts unresolved sizing/configuration facts into verification actions: 3
- Does not promote every Unknown into an unsourced mandatory gate: 3

## 5. Procurement handoff quality — 15 points

- Produces capability-level spec rather than exact products: 5
- Includes CUDA-capable GPU around 12 GB VRAM target, host PCIe/chassis/power compatibility, supported OS/drivers, local SSD and LAN/NAS access: 7
- Makes candidate-specific PSU/connectors/clearance verification explicit rather than inventing them: 3

## 6. No invention / usability — 5 points

- No unsupported interface, GPU, network, driver, price, product or performance claims that materially affect design: 5

# Penalties

Apply after raw score, minimum final score 0.

- **-30** if the answer recommends direct internal desktop-GPU installation in the DS918+ as a normal viable solution.
- **-20** if USB is presented as a normal supported desktop-NVIDIA-GPU host path.
- **-20** if an M.2-to-GPU adapter/hack is presented as the preferred supported architecture without clearly labelling experimental/supportability risk.
- **-20** if the answer says the user's local-GPU outcome is impossible rather than designing the external-compute alternative.
- **-15** if integrated Intel graphics are treated as equivalent to the requested CUDA-class GPU outcome.
- **-10** if the answer jumps to specific product recommendations/listings rather than producing an architecture and procurement-ready specification.
- **-10 each** for invented critical interface/power/driver/network facts used to determine feasibility.
- **-5** if a preference or performance concern is incorrectly promoted into a hard blocker without supplied evidence.

# Interpretation

- 90–100: excellent outcome-to-architecture reasoning; safe to generalize to another domain.
- 80–89: useful but contains a reusable architecture/feasibility precision gap worth diagnosing.
- 70–79: mixed; material risk of infeasible or overconfident design remains.
- below 70: unreliable solution architecture discipline.

For A/B comparison, prefer the Skill only if it materially improves feasibility accuracy, preserves the user's true objective, and produces a cleaner architecture/procurement boundary without adding unsupported requirements.
