# Dynamic Agent Invocation Result

- Agent: `ba-change-delivery-orchestrator`
- Run ID: `a002-g37-dynamic-stop-018`
- Model: `gemini-3.7-flash`
- Status: `success`
- Operational status: `none`
- Selected Skills: `analyze-requirements -> analyze-nonfunctional-requirements -> design-technical-solution`
- Total prompt tokens: `21454`
- Total candidate tokens: `10829`
- Total thought tokens: `3687`
- Total tokens: `35970`

## Agent routing decision

```json
{
  "objective": "Establish a defensible workstation architecture and evaluate the feasibility of the proposed mini-PC upgrade versus replacement for Northbridge Archive's local OCR workflow, stopping before procurement due to unresolved software runtime and hardware-acceleration dependencies.",
  "selected_skills": [
    "analyze-requirements",
    "analyze-nonfunctional-requirements",
    "design-technical-solution"
  ],
  "not_selected": [
    {
      "skill": "record-architecture-decisions",
      "reason": "No formal ADRs were requested and no architecture decision has reached an accepted state in the source packet."
    },
    {
      "skill": "prepare-procurement-specification",
      "reason": "Procurement specification is premature because core platform class, GPU necessity, and sizing dimensions depend on unselected OCR software runtime requirements."
    },
    {
      "skill": "expand-procurement-market",
      "reason": "Market discovery cannot proceed without a stable architecture boundary and procurement specification."
    },
    {
      "skill": "verify-procurement-options",
      "reason": "Candidate verification cannot be performed without a completed procurement specification and verified candidate evidence."
    }
  ],
  "stop_rules": [
    "Stop execution after design-technical-solution at the architecture stop gate.",
    "Do not proceed to prepare-procurement-specification, expand-procurement-market, or verify-procurement-options until the OCR engine edition/licence and its associated hardware, OS, and GPU acceleration support matrix are confirmed.",
    "Do not assume GPU acceleration is required or that USB external-GPU expansion is feasible on the existing mini-PC without verified PCIe/Thunderbolt interface evidence."
  ],
  "expected_final_artifact": "A structured solution design document establishing normalized functional and non-functional requirements, technical feasibility analysis of the mini-PC plus external GPU proposal, and an architecture stop-gate assessment detailing the specific software selection evidence required before procurement specifications and market verification can begin."
}
```

---

## 1 — analyze-requirements

- Status: `success`
- Skill SHA-256: `9b3033fb72fff244c170fa49e5719db5bbb10b9f0b5694d151f2445b3a844130`

# Requirements Analysis Handoff Artifact

## 1. Executive summary

Northbridge Archive requires a defensible hardware architecture to replace or upgrade an aging on-premises optical character recognition (OCR) workstation used for digitizing historic paper records. The archive processes an estimated 120,000 pages per year in batch mode during staffed hours from bound and loose paper records scanned to TIFF/PDF files on an existing local NAS. 

Under Records Handling Standard RH-7, all processing and text extraction must strictly remain within the archive’s local network; cloud-based OCR services are explicitly prohibited. While a hardware planning budget target of approximately A$2,500 and physical under-desk footprint boundaries (240 mm W × 520 mm D) are confirmed, technical sizing and platform selection are currently blocked. The specific edition and licence of the third-party OCR engine have not been selected, leaving runtime dependencies, resource bottlenecks (CPU vs. GPU vs. RAM vs. I/O), OS requirements, and GPU acceleration capabilities unverified. Additionally, a technician proposal to retain an existing mini-PC via an external USB-attached GPU faces significant feasibility risks due to the absence of documented external PCIe/Thunderbolt interfaces on the mini-PC.

---

## 2. Source register

| Source ID | Source Name | Description / Context |
|---|---|---|
| **S1** | Records Manager Email | Outlines archive scanning workload, cloud prohibition under RH-7, performance desires, estimated annual volume, and batch operating hours. |
| **S2** | Digitisation Technician Notes | Documents current software stack (ScanFlow Desktop + third-party OCR engine), NAS SMB integration, vendor demo observation, and GPU proposal. |
| **S3** | Infrastructure Notes | Details network connectivity, RH-7 compliance, Windows vs. Linux operational support status, and lack of baseline hardware sizing. |
| **S4** | Facilities / Physical Notes | Specifies measured under-desk floor footprint dimensions and acoustic preference. |
| **S5** | Proposed Implementation Notes | Documents technical interface specifications for the existing archive mini-PC model (USB-A 3.2 Gen 1, USB-C 3.2 Gen 1 w/ DP Alt Mode). |
| **S6** | Finance Note | Establishes the planning target budget for workstation hardware and notes separate software funding. |
| **S7** | Meeting Excerpt | Captures stakeholder dialogue regarding mini-PC feasibility, GPU assumptions, runtime dependency risks, and staging boundaries. |

---

## 3. Business objective and scope

### Business problem & opportunity
The current OCR workstation at Northbridge Archive is aging, leading staff to seek faster text-generation throughput for historic paper digitization without compromising archive security or purchasing an incompatible hardware platform.

### Intended business outcomes
- Establish a reliable, defensible on-premises workstation architecture to process digitised historic records locally.
- Maintain strict compliance with Records Handling Standard RH-7 (no off-network/cloud data exposure).
- Resolve whether the existing mini-PC can be extended or whether a complete workstation replacement is required.
- Define verified software runtime prerequisites prior to committing capital expenditure.

### Delivery & scope boundaries
- **In scope (Current Analysis):** Elicitation and baseline definition of functional, compliance, operational, and physical requirements; identification of technical contradictions and feasibility dependencies.
- **Out of scope / Blocked:** Hardware procurement specifications, market scanning, vendor shortlisting, story estimation, and commercial acquisition (held until software runtime and acceleration support are confirmed).

---

## 4. Stakeholders / actors

| Stakeholder / Actor | Role & Evidenced Responsibility | Established Decision Authority |
|---|---|---|
| **Records Manager** | Defines archival workflows, records compliance (RH-7), and business expectations; submitted funding request. | Decision authority over workstation replacement vs. upgrade preference; overall operational sign-off. |
| **Digitisation Technician** | Operates digitisation workflow (ScanFlow Desktop, OCR engine); suggested GPU need based on vendor demo and proposed mini-PC reuse. | Evidenced activity/responsibility only (operational user/proposer). No established commercial or architectural decision authority. |
| **Infrastructure Team** | Manages network, endpoints, and storage; maintains standard Windows endpoint management; raised software-dependency gating constraint. | Decision authority over supported OS platforms and network endpoint integration standards. |
| **Facilities** | Measured under-desk workstation footprint constraints. | Evidenced responsibility for physical environment constraints. |
| **Finance** | Allocated planning budget target. | Decision authority over hardware funding limit approval. |

---

## 5. Requirements register

| ID | Requirement Statement | Type | Evidence class | Requirement status | Source | Evidence / Rationale | Confidence |
|---|---|---|---|---|---|---|---|
| **REQ-SEC-01** | All document image processing, text extraction, and OCR data storage must remain strictly inside the archive local network. Off-premise or cloud OCR processing is prohibited. | Security / Compliance | Explicit | Confirmed | S1, S3 | Mandatory compliance rule under Records Handling Standard RH-7. | High |
| **REQ-INT-01** | The workstation must read input scan files (TIFF/PDF) from, and write generated search-ready text/files to, the existing archive NAS via an SMB network share over wired Ethernet. | Functional requirement | Explicit | Confirmed | S1, S2, S3 | Current and future scanning workflow requires reading/writing to existing NAS SMB shares. | High |
| **REQ-OPS-01** | The OCR processing workflow shall operate in batch processing mode during staffed operating hours. 24x7 continuous automated processing is not required. | Business rule / Operational | Explicit | Confirmed | S1 | Records Manager confirmed operational mode is batch during staffed hours. | High |
| **REQ-ENV-01** | The physical hardware chassis must fit within an available under-desk floor footprint not exceeding 240 mm in width and 520 mm in depth. | Constraint (Physical) | Explicit | Confirmed | S4 | Physical space measured and constrained by desk dimensions; height is unconstrained. | High |
| **REQ-OPS-02** | The workstation operating system must align with an infrastructure-supported standard, which currently confirms managed Windows endpoints. | Constraint (Infrastructure) | Explicit | Confirmed | S3 | Infrastructure explicitly confirms standard support for managed Windows endpoints; Linux is unconfirmed. | High |
| **REQ-VOL-01** | The system should be sized to accommodate an estimated annual workload volume of approximately 120,000 pages per year. | Non-functional (Capacity) | Explicit | Target | S1 | 120,000 pages/year was quoted in funding request based on prior year, noted as an estimate rather than guaranteed volume. | High |
| **REQ-PERF-01** | The system should generate search-ready text faster than the current aging workstation. | Non-functional (Performance) | Explicit | Target | S1 | Desired outcome from staff; no numeric throughput SLA or processing-time threshold has been established. | High |
| **REQ-ENV-02** | The workstation should exhibit reasonably quiet acoustic operation in the office/desk work environment. | Non-functional (Acoustic) | Explicit | Target | S4 | User preference stated; no numeric decibel (dB) threshold or sound power rating has been specified. | Medium |
| **REQ-FIN-01** | Total workstation hardware acquisition cost should target approximately A$2,500. | Constraint (Financial) | Explicit | Target | S6 | Finance noted A$2,500 as a planning target, not an approved hard ceiling; software licensing is funded separately. | High |
| **REQ-PLT-01** | The archive is considering a newer release of the third-party OCR engine for use alongside ScanFlow Desktop. | Functional / Software | Explicit | Candidate | S2 | Team is evaluating a newer release, but exact engine edition and licence remain unselected. | High |
| **REQ-ACC-01** | The workstation platform may incorporate dedicated GPU acceleration if verified as supported and beneficial for the selected OCR engine and document mix. | Functional / Hardware | Inferred | Candidate | S2, S7 | Technician proposed GPU based on a demo, but software compatibility and workload benefit are unverified. | Medium |
| **REQ-PLT-02** | A Linux-based operating system workstation may be considered as an alternative execution platform. | Constraint (Infrastructure) | Explicit | Candidate | S3 | Infrastructure noted Linux might be supportable, but support ownership and policy have not been decided. | Medium |
| **REQ-HW-01** | Retaining an existing archive mini-PC and attaching a desktop GPU via an external USB connection is being considered as a potential upgrade option. | Architecture / Hardware | Explicit | Candidate | S5, S7 | Technician proposed reusing mini-PC to avoid full replacement; technical interface feasibility is unverified. | High |

---

## 6. Contradictions and ambiguities

### CA-01: GPU acceleration necessity vs. unverified software runtime support
- **Competing positions:** The Digitisation Technician assumes a powerful dedicated GPU is necessary based on a vendor demonstration (S2, S7). Infrastructure notes that actual hardware acceleration support, supported APIs (e.g., CUDA, OpenCL, DirectCompute), and real-world performance benefits for the archive's specific document mix depend entirely on the unselected OCR engine edition (S3, S7).
- **Required outcome:** Confirm the specific OCR engine edition/licence and obtain the vendor's official hardware acceleration support matrix.
- **Decision owner:** Unknown *(Requires agreement between Digitisation Technician / Records Manager for software selection and Infrastructure for platform validation)*.

### CA-02: Proposed USB external-GPU upgrade vs. physical interface limitations
- **Competing positions:** The Technician proposes avoiding a full PC replacement by attaching an external GPU enclosure over USB to an existing mini-PC (S5, S7). However, the mini-PC’s documented specifications confirm only USB-A 3.2 Gen 1 and USB-C 3.2 Gen 1 (with DP Alt Mode), with no native PCIe, Thunderbolt, or USB4 external expansion capability (S5). Standard desktop GPUs require PCIe bus interfaces typically tunneled via Thunderbolt/USB4 or direct OCuLink/M.2 PCIe lanes.
- **Required outcome:** Determine whether the mini-PC upgrade proposal is technically viable or must be formally rejected in favor of a standard chassis replacement.
- **Decision owner:** Infrastructure Team *(Technical feasibility and endpoint standard authority)*.

### CA-03: Operating system platform support (Windows vs. Linux)
- **Competing positions:** Standard managed Windows endpoints are fully supported by Infrastructure (S3). A Linux OS workstation was raised as a potential alternative, but no operational support ownership, management tooling, or policy has been established (S3).
- **Required outcome:** Decide whether the workstation OS is strictly Windows or whether Linux support ownership will be established.
- **Decision owner:** Infrastructure Team.

### CA-04: Undefined performance and link speed thresholds
- **Competing positions:** Staff require the system to run "faster" than the current machine (S1), but no numeric processing rate (e.g., pages per minute, seconds per batch) or wall-port Ethernet link speed (e.g., 1 Gbps vs. 10 Gbps) is documented (S1, S3).
- **Required outcome:** Establish baseline processing expectations and verify wall-port network bandwidth to the NAS.
- **Decision owner:** Unknown.

---

## 7. Assumptions

- **ASM-01 (Wired Network Connectivity):** It is assumed that the physical wall port at the workstation desk provides at least 1 Gbps (1000BASE-T) connectivity to the existing archive NAS switch fabric, consistent with typical enterprise managed environments. *(Rationale: Necessary for sustained TIFF/PDF transfer, but unstated in S3).*
- **ASM-02 (Scanner Export Decoupling):** It is assumed that the physical paper scanner connects directly to the network or existing NAS independently of this workstation, as files are ingested via SMB share (S2).
- **ASM-03 (Display / Peripheral Reusability):** It is assumed that existing desk peripherals (monitor, keyboard, mouse) will be reused and do not consume the A$2,500 hardware budget target, which is dedicated to the base workstation unit.

---

## 8. Analyst proposals

*Note: The following items are recommendations from the business analyst and do not represent committed stakeholder decisions or confirmed requirements.*

- **PROP-01 (OCR Runtime & Benchmark Assessment):** The project team should obtain evaluation/trial licences for the candidate OCR engine release and execute a representative sample benchmark of archive TIFF/PDF documents to identify whether execution is bound by CPU single-thread speed, multi-core parallelism, GPU compute, RAM capacity, or NAS network I/O.
- **PROP-02 (Formal Retirement of USB-A/C eGPU Option):** Infrastructure should formally evaluate the mini-PC specification sheet (S5) against external GPU enclosure interface requirements (PCIe tunneling via Thunderbolt 3/4 or USB4) and formally close the mini-PC reuse proposal if hardware compatibility cannot be established without proprietary/unsupported bus adapters.
- **PROP-03 (Two-Stage Gated Delivery Approach):** The archive should execute a formal architecture stop gate: complete Stage 1 (Software runtime and hardware requirement confirmation) before commencing Stage 2 (Workstation procurement specification, market scanning, and hardware shortlisting).

---

## 9. Open questions — prioritized

1. **[Priority 1 - Architecture Blocker]** What exact third-party OCR software engine, edition, and licensing model will be selected for the new workflow?
2. **[Priority 1 - Architecture Blocker]** Does the selected OCR software edition explicitly support hardware/GPU acceleration, and if so, what specific compute APIs (e.g., NVIDIA CUDA, OpenCL, Vulkan, DirectML) and OS platforms are required/supported?
3. **[Priority 2 - Governance]** Who owns the final decision authority for selecting the OCR engine edition and approving deviations (if any) from standard managed Windows endpoints?
4. **[Priority 2 - Feasibility]** Will Infrastructure formally rule on the technical viability of the mini-PC + USB eGPU proposal based on the lack of Thunderbolt/USB4/PCIe external support?
5. **[Priority 3 - Non-Functional]** What is the verified Ethernet link speed at the workstation wall port (e.g., 100 Mbps, 1 Gbps, 2.5 Gbps, 10 Gbps)?
6. **[Priority 3 - Non-Functional]** What is the target processing throughput threshold (e.g., average seconds per page or pages per hour) required by the Records Manager to satisfy the "faster than current machine" requirement?
7. **[Priority 3 - Non-Functional]** What is the acceptable acoustic noise threshold (in dBA) for the under-desk location during sustained batch OCR processing?

---

## 10. Not established / out of scope

### Items not established in source evidence
- **Exact hardware baseline:** Minimum CPU core count/clock, system RAM capacity, internal SSD storage size/endurance, and power supply capacity.
- **GPU requirement:** Whether GPU compute provides any measurable performance acceleration for the archive's specific workload.
- **Network wall-port speed:** The exact link negotiation speed at the physical desk location.
- **Acoustic and throughput numerical SLAs:** Quantitative decibel ratings or page-per-minute performance metrics.
- **Linux operational ownership:** Service/maintenance model and management tooling for Linux endpoints.
- **Decision ownership for software engine selection:** Sourced evidence does not specify whether the Records Manager, Infrastructure, or another entity holds commercial/technical authority over software selection.

### Explicitly out of scope for current stage
- Cloud-based OCR services and off-premise SaaS architectures (explicitly barred by RH-7).
- Generating bill-of-materials (BOM), commercial procurement specifications, or vendor request-for-quotes (RFQs).
- Vendor shortlisting and hardware supplier market verification.
- Solution implementation plans, user stories, and task estimation.

---

## 11. Readiness for decomposition

**Status:** **Partially ready**

**Reason:** Core business objectives, compliance constraints (RH-7 local processing mandate), operational batch workflows, physical under-desk footprint boundaries, and planning budget targets are clearly understood and confirmed. However, requirements decomposition into technical procurement specifications cannot proceed because the foundational runtime dependency—the specific OCR engine edition and its underlying hardware/GPU/OS support matrix—remains unknown. The project must proceed through non-functional requirement analysis and high-level solution design to formalize these architecture boundaries and stop-gate criteria.

---

## 2 — analyze-nonfunctional-requirements

- Status: `success`
- Skill SHA-256: `46e1300f2bac96ee7d9df95d9f326dd2a24521c4776cde7859efe9903c70ce04`

# Non-Functional Requirements Analysis Handoff Artifact

## 1. Overall NFR readiness

**Status:** `Partially Ready`

**Reason:** Core compliance boundaries (Records Handling Standard RH-7 mandatory local/on-network processing), operational batch processing windows (staffed hours only), standard OS support constraints (managed Windows), and physical under-desk chassis dimensions (240 mm W × 520 mm D) are confirmed. However, sizing dimensions and hardware-level performance baselines remain non-binding because third-party OCR software runtime specifications, compute bottlenecks (CPU vs. GPU vs. RAM vs. I/O), network link speeds, and throughput targets have no confirmed quantitative criteria or selected engine matrix.

---

## 2. NFR register

| NFR ID | Domain | Requirement / Quality Statement | Evidence Class | Status | Source Reference | Confidence | Measurable Threshold (sourced only) |
|---|---|---|---|---|---|---|---|
| **NFR-SEC-01** | Security / Privacy & Compliance | Restricted collection images and extracted OCR text must remain strictly within the archive local network. Cloud-based OCR processing or off-premise transmission is prohibited under Records Handling Standard RH-7. | Explicit | Confirmed | S1 (Records Manager), S3 (Infrastructure) | High | 100% on-premises / local archive network execution (0% off-network/cloud transmission). |
| **NFR-ENV-01** | Environmental / Physical Constraints | Workstation chassis must fit within the measured available floor footprint beneath the existing desk. | Explicit | Confirmed | S4 (Facilities) | High | Maximum width: 240 mm; Maximum depth: 520 mm. Height is unconstrained. |
| **NFR-SUP-01** | Maintainability / Supportability | Workstation operating environment must align with standard infrastructure-supported endpoint management. Standard managed Windows endpoints are supported. | Explicit | Confirmed | S3 (Infrastructure) | High | Standard managed Windows endpoint support confirmed. |
| **NFR-OPS-01** | Operational / Availability | OCR processing workflow operates as batch processing during staffed hours. Continuous 24x7 system runtime or high-availability processing is not required. | Explicit | Confirmed | S1 (Records Manager) | High | Operational window: Staffed hours (no 24x7 runtime requirement). |
| **NFR-CAP-01** | Scalability / Capacity | Workstation should accommodate the estimated annual historic records digitization workload. | Explicit | Target | S1 (Records Manager) | High | Estimated ~120,000 pages per year (planning estimate based on prior year, not a guaranteed quota). |
| **NFR-PERF-01** | Performance / Throughput | Search-ready text generation should be faster than the current aging workstation. | Explicit | Target | S1 (Records Manager) | High | None sourced (no contractual processing-time or page-per-minute threshold established). |
| **NFR-FIN-01** | Policy / Financial Constraint | Workstation hardware acquisition should align with the allocated planning budget. | Explicit | Target | S6 (Finance) | High | Planning target: ~A$2,500 for hardware (planning target, not an approved hard ceiling; software funded separately). |
| **NFR-ENV-02** | Environmental / Usability (Acoustics) | Workstation acoustic noise level should be reasonably quiet for an under-desk office/digitisation environment. | Explicit | Target | S4 (Facilities) | Medium | None sourced (no dBA sound pressure or sound power rating specified). |
| **NFR-ACC-01** | Performance / Hardware Acceleration | Workstation platform may utilize dedicated GPU acceleration if supported by the licensed OCR engine and beneficial for the document mix. | Inferred | Candidate | S2 (Technician), S7 (Meeting) | Medium | None sourced (software support, API compatibility, and acceleration gain unverified). |
| **NFR-SUP-02** | Maintainability / Supportability | Workstation execution on a Linux-based operating system. | Explicit | Candidate | S3 (Infrastructure) | Medium | None sourced (operational support ownership and management model unestablished). |
| **NFR-INT-01** | Compatibility / Interoperability | Workstation must interface with the existing archive NAS SMB share over wired Ethernet for reading source scans (TIFF/PDF) and writing OCR outputs. | Explicit | Confirmed | S1 (Records Manager), S2 (Technician), S3 (Infrastructure) | High | Protocol: SMB over wired Ethernet. Wall-port link speed unsupplied. |

---

## 3. Constraints and boundaries

### Compliance & operational boundaries
- **Data Boundary (RH-7 Compliance):** All document image ingestion, text extraction, intermediate caching, and output text generation must execute strictly on the local archive network fabric. External/cloud OCR APIs, cloud-hosted processing containers, or off-premise routing are strictly prohibited (NFR-SEC-01).
- **Operational Process Boundary:** Business operations are bounded to batch processing during staffed working hours. There is no operational mandate for unattended 24x7 service availability, automatic multi-node failover, or after-hours automated processing (NFR-OPS-01).
- **Peripheral Reuse Boundary:** The A$2,500 planning target is dedicated to workstation base hardware; software licensing is funded separately, and existing desk peripherals are assumed to be retained (NFR-FIN-01, ASM-03).

### Technical & physical constraints
- **Physical Envelope Constraint:** Chassis volume is strictly constrained in horizontal footprint: width $\le 240\text{ mm}$ and depth $\le 520\text{ mm}$. Vertical height is unconstrained by the desk structure (NFR-ENV-01).
- **Endpoint Support Constraint:** Infrastructure confirms management and operational support for standard managed Windows endpoints. Non-Windows operating environments have no confirmed operational support path (NFR-SUP-01, NFR-SUP-02).
- **Network Interface Constraint:** Ingestion and output storage must communicate via SMB file shares over wired Ethernet connected to the archive NAS (NFR-INT-01).

---

## 4. Conflicts and disputed quality decisions

### CON-01: Dedicated GPU acceleration requirement vs. software support uncertainty
- **Position A (Technician):** Assumes dedicated GPU acceleration is necessary for workstation replacement based on an observed vendor demonstration.
- **Position B (Infrastructure):** GPU acceleration cannot be specified or sized until the specific OCR engine edition/licence is selected and verified to support GPU compute APIs (e.g., CUDA, OpenCL, DirectML) with demonstrable benefit on the archive's TIFF/PDF document mix.
- **Current Status:** Disputed / Candidate.
- **Decision owner:** `Decision owner: Unknown` *(Authority for software selection and platform validation is not explicitly assigned in the source evidence).*

### CON-02: Existing mini-PC external GPU reuse vs. hardware interface limitations
- **Position A (Technician):** Proposes retaining the existing mini-PC and attaching an external desktop GPU enclosure over USB to reduce hardware replacement scope.
- **Position B (Technical Evidence / Infrastructure):** The documented mini-PC specification provides only USB-A 3.2 Gen 1 (5 Gbps) and USB-C 3.2 Gen 1 (5 Gbps w/ DP Alt Mode). It lacks Thunderbolt, USB4, or external PCIe expansion capabilities necessary for standard desktop GPU enclosures.
- **Current Status:** Disputed / Technically constrained.
- **Decision owner:** `Decision owner: Unknown`

### CON-03: Operating system platform standard (Windows vs. Linux)
- **Position A (Infrastructure Standard):** Infrastructure team officially supports standard managed Windows endpoints.
- **Position B (Candidate Linux Option):** Linux was noted as potentially supportable in principle, but support ownership, patching, and endpoint management responsibility remain unassigned.
- **Current Status:** Disputed / Candidate.
- **Decision owner:** `Decision owner: Unknown`

---

## 5. Assumptions and estimates

- **EST-01 (Annual Workload Estimate):** The figure of ~120,000 pages per year is a planning estimate derived from prior-year scanning volumes quoted in the funding request; it is not a binding minimum or maximum processing quota (NFR-CAP-01).
- **EST-02 (Hardware Budget Target):** The A$2,500 figure is a planning target for workstation hardware allocation, not a certified contractual ceiling (NFR-FIN-01).
- **ASM-01 (Wired Ethernet Link Bandwidth):** Workstation wall-port drop is assumed to operate at standard enterprise rate (minimum 1 Gbps / 1000BASE-T), but physical port speed has not been measured or documented in evidence (NFR-INT-01).
- **ASM-02 (Acoustic Environment):** Office desk environment implies standard office acoustic comfort, but no specific dBA sound pressure rating is mandated (NFR-ENV-02).

---

## 6. Unassessed and unknown quality areas

1. **OCR Engine Software Specification:** What specific OCR engine edition and licence will be selected, and what are its vendor-documented minimum and recommended CPU, RAM, OS, and GPU acceleration prerequisites?
2. **Workload Resource Bottleneck:** Is the archive's specific document mix (bound and loose historic TIFF/PDF records) primary-bound by single-threaded CPU speed, multi-threaded CPU cores, GPU compute, memory capacity, or NAS network I/O?
3. **Quantitative Performance Threshold:** What specific throughput rate (e.g., average seconds per page, pages per minute, or batch turnaround time) defines "faster than the current machine"?
4. **Physical Network Wall-Port Speed:** What is the actual negotiated Ethernet link speed at the workstation wall port (e.g., 100 Mbps, 1 Gbps, 2.5 Gbps, 10 Gbps)?
5. **Acoustic Threshold:** Is there a defined sound pressure ceiling (e.g., $< 35\text{ dBA}$ under load at 1 meter) for the under-desk location?
6. **Operating System Support Governance:** Will infrastructure or digitisation staff establish operational support ownership if a non-Windows OS is proposed?

---

## 7. Solution-design handoff

### Binding NFRs for downstream solution design (`design-technical-solution`)
The downstream technical solution design may treat the following items as confirmed requirements and boundaries:
- **NFR-SEC-01 (Confirmed):** Architecture must be 100% on-premises / local archive network. Zero external cloud OCR dependencies.
- **NFR-ENV-01 (Confirmed):** Physical chassis dimensions must strictly respect width $\le 240\text{ mm}$ and depth $\le 520\text{ mm}$.
- **NFR-SUP-01 (Confirmed):** Primary platform design must align with standard managed Windows endpoints.
- **NFR-OPS-01 (Confirmed):** System sizing must assume staffed batch processing workflows; do not architect for high-availability multi-node clustering or 24x7 continuous services.
- **NFR-INT-01 (Confirmed):** Storage interface must utilize SMB over wired Ethernet to the existing NAS.

### Non-binding targets, candidates, and unknowns to preserve
- **NFR-CAP-01 (~120,000 pages/yr):** Treat as an indicative sizing baseline, not a hard contractual SLA.
- **NFR-PERF-01 ("Faster than current"):** Qualitative target only; solution design must not invent numeric pass/fail thresholds.
- **NFR-FIN-01 (~A$2,500 target):** Planning target; architecture must avoid premature commercial lock-in.
- **NFR-ENV-02 ("Reasonably quiet"):** Qualitative target; solution design must prefer standard quiet active/passive cooling without inventing decibel SLAs.
- **NFR-ACC-01 / REQ-HW-01 (GPU & Mini-PC eGPU):** Retain as an unverified candidate and evaluate technical interface feasibility (USB 3.2 Gen 1 vs. PCIe requirements) without assuming GPU is mandatory.
- **NFR-SUP-02 (Linux Platform):** Retain as candidate; do not mandate Linux architecture unless support ownership is resolved.

---

## 3 — design-technical-solution

- Status: `success`
- Skill SHA-256: `89bbcf3b465e7536e486f02192cabcabcb00759e3c68a3722d5e4ddc4c2c685e`

# Technical Solution Design Handoff Artifact

## 1. Outcome and Success Criteria

### 1.1 Core Business Outcome
Northbridge Archive requires a reliable, supportable on-premises compute environment to digitize and perform optical character recognition (OCR) on historic bound and loose paper records (scanned as TIFF/PDF), replacing an aging workstation while maintaining strict data sovereignty inside the archive local network.

### 1.2 Success Criteria
- **Compliance Preservation:** 100% of document ingestion, intermediate image processing, OCR text extraction, and export must occur strictly within the archive local network per Records Handling Standard RH-7 (no cloud/external API reliance).
- **Physical Fit:** Compute hardware must occupy an under-desk footprint not exceeding $240\text{ mm (width)} \times 520\text{ mm (depth)}$ (vertical height is unconstrained).
- **Operational Integration:** Seamlessly interface with the existing archive network storage (NAS) via SMB over wired Ethernet to process scan batches during staffed hours.
- **Supportable Platform Baseline:** System architecture and operating environment must align with standard infrastructure endpoint management (standard managed Windows environment confirmed).
- **Defensible Platform Sizing:** Avoid premature hardware lock-in or unsupportable custom hardware configurations until the third-party OCR software runtime requirements, licensing tier, and hardware acceleration matrix are confirmed.

---

## 2. Current-State and Evidence Map

| Fact / Constraint / Assumption | Status | Architectural Significance |
|---|---|---|
| **Local Processing Mandate (RH-7)** | Confirmed Fact | Strict architectural boundary: architecture must be purely on-premises. Cloud-hosted OCR engines, off-premise SaaS, or external processing endpoints are completely excluded. |
| **Existing Storage & Workflow (NAS / SMB)** | Confirmed Fact | Scanners write TIFF/PDF files to an existing SMB share on the archive NAS. The new processing node reads inputs from and writes search-ready outputs back to this share over wired Ethernet. |
| **Physical Space Allowance** | Confirmed Fact | Hard physical constraint: maximum under-desk footprint is $240\text{ mm (W)} \times 520\text{ mm (D)}$. Height is unconstrained. |
| **Operational Schedule** | Confirmed Fact | Batch processing occurs during staffed hours. No requirement for continuous 24x7 availability, automated overnight failover, or high-availability clustering. |
| **OS Support Model** | Confirmed Fact | Managed Windows endpoints are officially supported by infrastructure. Linux is a candidate in principle, but lacks defined support ownership. |
| **Existing Mini-PC Port Inventory** | Confirmed Fact | Exact device documentation verifies two USB-A 3.2 Gen 1 (5 Gbps) ports and one USB-C 3.2 Gen 1 (5 Gbps with DP Alt Mode) port. Lacks Thunderbolt, USB4, or external PCIe expansion. |
| **Workload Volume (~120,000 pages/yr)** | Target / Estimate | Planning baseline derived from prior-year volumes. Sizing indicator for batch duty cycle, not a rigid contractual SLA. |
| **Hardware Budget (~A$2,500)** | Target / Estimate | Planning financial target for workstation hardware; not an approved contractual ceiling. Software licensing is funded separately. |
| **Performance ("Faster than current")** | Desired Preference | Qualitative target. No sourced numeric processing-time threshold, page-per-minute target, or contractual SLA has been established. |
| **Dedicated GPU Requirement** | Unknown / Unverified | Inferred solely from a vendor demonstration. Whether the archive's specific OCR engine edition/licence supports GPU compute (e.g., CUDA/DirectML/OpenCL) or benefits the TIFF/PDF document mix is unverified. |
| **OCR Software Selection & Runtime Matrix** | Unknown | Engine edition and licence are unselected; minimum/recommended CPU, RAM, OS, and hardware-acceleration specifications are currently unknown. |
| **Workload Resource Bottleneck** | Unknown | Profile of primary bottleneck (single-core CPU, multi-core CPU, GPU compute, memory footprint, or SMB network/storage I/O) is undetermined. |
| **Wired Network Wall-Port Link Speed** | Unknown | Network drop exists at the desk, but physical negotiated rate (e.g., 1 Gbps, 2.5 Gbps, 10 Gbps) is unsupplied. |

---

## 3. Proposed Implementation Feasibility Assessment

### Proposed Mechanism
Retain an existing archive mini-PC and attach a standard desktop GPU housed in an external enclosure over USB.

### Feasibility Classification
**`Infeasible`** (for standard, vendor-supported external GPU operation)

### Detailed Assessment and Evidence
1. **Interface Bus Incompatibility:** External GPU (eGPU) enclosures require an expansion interface capable of tunneling raw PCI Express (PCIe) signals directly to the host CPU (such as Thunderbolt 3/4, USB4, or proprietary external PCIe interfaces like OCuLink).
2. **Supplied Host Interface Limitations:** The documented mini-PC provides only standard USB 3.2 Gen 1 (5 Gbps) over USB-A and USB-C (with DisplayPort Alt Mode). USB 3.2 Gen 1 is a packetized USB host/device protocol and does not support PCIe bus tunneling.
3. **Absence of Supported Expansion Path:** Standard commercial eGPU enclosures will not enumerate or operate over standard USB 3.2 Gen 1. Any non-standard workaround (e.g., DisplayLink-based display adapters or experimental USB-to-PCIe bridging) does not provide general-purpose DirectML/CUDA GPU compute acceleration for desktop graphics cards and is not supported in an enterprise production environment.
4. **Conclusion:** Upgrading the existing mini-PC via an external USB GPU is architecturally non-viable and rejected.

---

## 4. Constraint and Blocker Register

### 4.1 Hard Blockers (Must determine architecture boundaries)
- **BLK-01 (External Interface Blocker):** Existing mini-PC lacks Thunderbolt / USB4 / PCIe expansion capability, rendering external desktop GPU expansion technically impossible without unsupported hardware modifications.
- **BLK-02 (Compliance Blocker):** Records Handling Standard RH-7 strictly prohibits transmitting collection records outside the local archive network fabric.
- **BLK-03 (Software Dependency Blocker):** Specific OCR engine edition and licence tier are unselected, leaving runtime prerequisites (CPU architecture, RAM minimums, OS compatibility, and GPU API requirements) formally undefined.

### 4.2 Hard Constraints (Physical & Infrastructure Boundaries)
- **CST-01 (Physical Footprint):** Workstation chassis footprint must not exceed $240\text{ mm (W)} \times 520\text{ mm (D)}$.
- **CST-02 (OS Standard):** Standard managed Windows endpoint is the confirmed infrastructure support path.

### 4.3 Soft Constraints and Trade-Offs
- **TRD-01 (GPU vs. CPU Sizing):** Procuring a dedicated GPU adds cost, power draw, and acoustic output. Sizing must be gated on whether the selected OCR engine supports acceleration and shows measurable gain on archive document types.
- **TRD-02 (Target Budget A$2,500):** Sizing should prioritize standard workstation form factors (e.g., Small Form Factor or Compact Tower) that comfortably fit within the A$2,500 target.
- **TRD-03 (Acoustics):** While no specific dBA threshold is mandated, an under-desk placement in a staffed records environment favors standard quiet active cooling over high-RPM server fans.

---

## 5. Architecture Options Analysis

```
                      +------------------------------------------+
                      |   Records Handling Standard RH-7         |
                      |   Local Archive Network Boundary (SMB)   |
                      +--------------------+---------------------+
                                           |
                                   [Wired Ethernet]
                                           |
                                           v
+------------------------------------------------------------------------------------+
| OPTION 1: Dedicated Standard Workstation (Preferred)                               |
| - Standard SFF / Compact Mid-Tower Chassis (W <= 240 mm, D <= 520 mm)              |
| - Managed Windows OS Endpoint                                                      |
| - CPU-only or Internal PCIe GPU (Configured after OCR engine runtime verification) |
+------------------------------------------------------------------------------------+

+------------------------------------------------------------------------------------+
| OPTION 2: Mini-PC + External GPU over USB (Proposed by Technician)                 |
| - Retain existing mini-PC; attach desktop GPU via USB 3.2 Gen 1                    |
| - STATUS: INFEASIBLE (No PCIe tunneling/Thunderbolt on host USB-C port)            |
+------------------------------------------------------------------------------------+

+------------------------------------------------------------------------------------+
| OPTION 3: Dedicated Headless Processing Server + Mini-PC Client                    |
| - Mini-PC retained for UI/ScanFlow; offloads OCR jobs to network compute node      |
| - STATUS: REJECTED (Unnecessary complexity, multi-node orchestration overhead,     |
|   and inconsistent with simple single-seat staffed batch processing workflow)      |
+------------------------------------------------------------------------------------+
```

### Options Comparison Matrix

| Dimension | Option 1: Dedicated Workstation Replacement (Preferred) | Option 2: Mini-PC + USB eGPU (Proposed) | Option 3: Two-Tier Split (Mini-PC Client + Network Compute Node) |
|---|---|---|---|
| **Mechanism** | Replace aging PC with a standalone managed Windows workstation (SFF or Compact Tower) sized to OCR runtime. | Retain mini-PC; connect external GPU enclosure via USB port. | Retain mini-PC as operator console; deploy dedicated headless OCR server in rack/network. |
| **Feasibility** | **Feasible** | **Infeasible** (USB 3.2 Gen 1 lacks PCIe tunneling) | **Conditionally Feasible** (Subject to multi-seat OCR software architecture) |
| **Outcome Delivery** | High: Direct execution, native internal PCIe bus for optional GPU, standard enterprise management. | Fails: Hardware cannot enumerate desktop GPU over standard USB. | High: Preserves RH-7 local boundary, offloads heavy compute. |
| **Supportability** | Standard infrastructure-supported managed Windows endpoint. | Unsupported / Broken. | High operational complexity; introduces client-server orchestration, job scheduling, and two-node maintenance. |
| **Physical Fit** | Fits within $240\text{ mm} \times 520\text{ mm}$ footprint using standard Tower/SFF chassis. | Small footprint, but non-functional. | Client fits on desk; server requires rack space / network provisioning. |
| **Cost & Budget** | Sized to fit comfortably within the ~A$2,500 hardware target. | Low apparent cost, but technically impossible. | High: Exceeds budget (requires server hardware + management overhead + potential multi-user software licensing). |

---

## 6. Preferred Solution Architecture

### 6.1 Architecture Description
The preferred solution is **Option 1: A Dedicated On-Premises Workstation Replacement**.

- **Chassis & Form Factor:** Standard commercial workstation or compact desktop tower adhering strictly to the physical envelope constraint (Width $\le 240\text{ mm}$, Depth $\le 520\text{ mm}$, unconstrained height).
- **Operating Platform:** Standard managed Windows OS environment, integrating seamlessly with archive endpoint management and authentication protocols.
- **Compute Architecture:** Native internal motherboard architecture supporting multi-core desktop CPU, system memory sized to batch image caching requirements, and native internal PCIe slots (permitting an internal discrete GPU if verified as beneficial by software runtime analysis).
- **Storage & I/O:** Local high-speed solid-state drive for OS, ScanFlow Desktop, OCR application binaries, and temporary working scratch space; wired Ethernet NIC connecting to the archive NAS SMB share.

### 6.2 Data and Process Flow
```
 [Scanner / ScanFlow] 
         │
         ▼ (TIFF / PDF Scans)
 ┌────────────────────────────────────────────────────────┐
 │ Existing Archive NAS (SMB Share)                       │
 └──────────────────────────┬─────────────────────────────┘
                            │ (Wired Ethernet / Local RH-7 Boundary)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ New Dedicated Managed Windows Workstation              │
 │ ┌────────────────────────────────────────────────────┐ │
 │ │ Local SSD Scratch Space (Working Temp Buffer)     │ │
 │ └────────────────────────┬───────────────────────────┘ │
 │                          ▼                             │
 │ ┌────────────────────────────────────────────────────┐ │
 │ │ OCR Execution Engine                               │ │
 │ │ - Multi-core CPU Execution (Baseline)              │ │
 │ │ - Internal PCIe GPU Acceleration (If supported/opt)│ │
 │ └────────────────────────┬───────────────────────────┘ │
 └──────────────────────────┼─────────────────────────────┘
                            │ (Write-back Search-Ready PDF/Text)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ Archive NAS (Long-Term Storage & Cataloguing)          │
 └────────────────────────────────────────────────────────┘
```

1. **Ingestion:** Digitisation technician initiates batch scans via ScanFlow Desktop; source images (TIFF/PDF) are staged on the NAS SMB share.
2. **Acquisition & Staging:** Workstation reads batch files across the local wired network into local fast SSD scratch storage to prevent network I/O thrashing during optical analysis.
3. **Execution:** Local OCR engine performs document pre-processing, binarization, layout analysis, and character recognition using host CPU cores (augmented by internal PCIe GPU acceleration if confirmed by software license/runtime).
4. **Commit & Storage:** Search-ready PDF/A and text outputs are written directly back to the designated NAS archive SMB share. Intermediate local scratch files are purged.

---

## 7. Component Boundaries and Integration Architecture

| Architectural Layer | Owning Component | Responsibility & Integration Boundary |
|---|---|---|
| **Compute / Processing** | Dedicated Local Workstation | Executes ScanFlow Desktop and OCR recognition engine. Sized to workload upon software runtime verification. |
| **Internal Acceleration** | Workstation PCIe Slot (Optional) | If software supports GPU compute (e.g., CUDA/DirectML), an internal discrete GPU card is housed directly on the motherboard PCIe bus (eliminating external USB/eGPU requirements). |
| **Primary Storage** | Archive NAS (SMB Share) | Authoritative storage for input scan files, master historic images, and finalized searchable text/PDF deliverables. |
| **Scratch / Cache Storage** | Local Workstation Internal SSD | Transient caching for batch processing and active image manipulation to isolate processing from network fluctuations. |
| **Network Fabric** | Local Archive Wired Ethernet | Secure local area network connecting scanner, workstation, and NAS. Bounded strictly on-premises under RH-7. |
| **Security & Compliance** | Archive Infrastructure Policy | Enforces RH-7 compliance (no egress to cloud endpoints). Windows endpoint managed under existing security/patching policies. |
| **User Interaction** | Workstation Local Console | Single-seat interactive batch management by digitisation technician during staffed hours. |

---

## 8. Unknowns and Verification Plan (Architecture Stop-Gate Assessment)

### 8.1 Architecture Stop-Gate Status
**STATUS: STOPPED AT ARCHITECTURE GATE.**
*Procurement activities (market scanning, preparing procurement specifications, shortlisting, and vendor checks) must not proceed until the following software runtime and acceleration unknowns are resolved.*

```
+------------------------------------------------------------------------------------+
|                             ARCHITECTURE STOP GATE                                 |
|                                                                                    |
|  [X] Local Processing Compliance (RH-7) Confirmed                                  |
|  [X] Physical Footprint Constraints Confirmed (240 mm W x 520 mm D)                |
|  [X] Mini-PC + USB eGPU Feasibility Evaluated -> REJECTED (Infeasible)             |
|  [X] Preferred Architecture Selected -> Dedicated Workstation                     |
|                                                                                    |
|  [!] STOP: Sizing & Procurement Spec Gated on Software Selection Dependencies     |
|                                                                                    |
|      1. Confirm exact OCR engine release edition & licensing model.                |
|      2. Verify vendor hardware support matrix (CPU vs. GPU acceleration).          |
|      3. Benchmark representative archive TIFF/PDF document mix.                    |
|      4. Confirm workstation network wall-port link speed (1GbE+).                  |
+------------------------------------------------------------------------------------+
```

### 8.2 Required Verification Actions Prior to Procurement Handoff

| Verification Action | Target Unknown | Required Sourcing Method / Evidence Needed | Downstream Impact on Procurement Specification |
|---|---|---|---|
| **ACT-01: OCR Engine & Licence Selection** | Engine Edition & Hardware Matrix | Obtain vendor software specification sheet for the candidate OCR engine release/tier. | Determines mandatory OS version, minimum CPU instruction sets, RAM requirements, and whether GPU acceleration is supported. |
| **ACT-02: GPU API & Acceleration Validation** | GPU Compute Necessity & Compatibility | Verify whether the specific software tier utilizes GPU acceleration (e.g., NVIDIA CUDA, OpenCL, DirectML) and requires specific GPU architectures. | Determines whether to procure a standard CPU-only workstation (~A$1,500–A$2,000) or a GPU-equipped workstation with dedicated PSU/cooling (~A$2,500). |
| **ACT-03: Workload Bottleneck Benchmarking** | Processing Bottlenecks & Capacity | Execute a test batch of historic bound/loose TIFF/PDF files on representative hardware to determine if workload is CPU-bound, memory-bound, or GPU-bound. | Informs core count, clock frequency priority, memory sizing (e.g., 16 GB vs. 32 GB+), and scratch SSD sizing. |
| **ACT-04: Network Wall-Port Link Rate Check** | Network Throughput Headroom | Inspect physical switch port or run link-speed diagnostics on the workstation Ethernet wall drop. | Verifies if existing network drop is 100 Mbps, 1 Gbps, or higher, ensuring NAS SMB file transfer does not bottleneck batch ingestion. |

---
*Execution terminated at Architecture Stop Gate per dynamic route instructions. Downstream procurement specification (`prepare-procurement-specification`), market expansion (`expand-procurement-market`), and candidate verification (`verify-procurement-options`) are withheld pending resolution of ACT-01 through ACT-04.*
