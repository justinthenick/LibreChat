# BA Benchmark Raw Result

> Raw model output. Not an evaluator score.

## Run metadata

- Benchmark: `Benchmark 042 — Multi-Source BA Model Comparison`
- Mode: `skill`
- Provider: `gemini`
- Model: `gemini-3.7-flash`
- Status: `success`
- Started: `2026-09-09T08:42:10Z`
- Ended: `2026-09-09T08:42:35Z`
- Temperature: `0.0`
- Max output tokens: `16384`
- Input SHA-256: `1432330128630c368efc83ea65458ebec990d731cc2dd0b11d77148c13b21af3`
- Prompt SHA-256: `327f4aeb1a6fd16d585800b3706194285a459265cd69d02950e95b5d07b717e1`
- Skill: `/volume1/docker/librechat-ba-lab/custom/ba-agent/skills/prepare-implementation-ready-requirements/SKILL.md`
- Skill version: `0.2.4`
- Skill SHA-256: `a38fda060b2ccaec03fe137dbde1049985dd6971a7dbc2a41ec81d762a037c99`
- Finish reason: `STOP`
- Usage metadata: `{"candidatesTokenCount": 7694, "promptTokenCount": 5986, "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 5986}], "serviceTier": "standard", "thoughtsTokenCount": 969, "totalTokenCount": 14649}`

---

## Model output

# Integrated Change Intake and Site Access — Business Analysis Package

## 1. Source Register

| Source ID | Document Title & Format | Scope & Core Evidence Provided |
| :--- | :--- | :--- |
| **SRC-DOC-01** | Functional Enhancement Specification (Word) | Defines RFC intake initiation in Appian, Appian-to-ServiceNow record linkage, catalogue filtering by company, 4-tier activity hierarchy labels, lead-time rules by change type, document upload mandates, site access work type/crew rules, key questions (67–69), and change lifecycle / automated closure rules. |
| **SRC-XLS-01** | Service and Activity Catalogue (Excel) | Operational matrix defining 4-tier taxonomy technical fields (`u_service_category`, `u_service_subcategory`, `u_service_l1`, `u_service_l2`), default `assignment_group`, operational flags (`Standard Change option available?`, `SAR option available?`), Change Type, permitted PSN impact (`NSA`, `SA`, `RA`), initial risk level, per-activity document requirement flags (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`), row-specific lead times, and approval authority mappings for Minor, Significant, and Major changes. |
| **SRC-MAP-01** | Post-ServiceNow Review Process Map (PDF; WIP/Draft) | Defines assignment group routing fallback (PSN Helpdesk), Standard Change state progressions (New $\rightarrow$ Assess $\rightarrow$ Authorise $\rightarrow$ Scheduled, and direct New $\rightarrow$ Scheduled for site inspection), and records four explicit unresolved process annotations. |
| **SRC-PPT-01** | Internal Change Transformation Presentation (PowerPoint) | Defines business objectives (reduce processing time, eliminate swivel-chair double handling), target-state direct creation from Appian, target risk-assessment model, and target state-transition triggers based on first and final site visits. |

---

## 2. Requirements Register

*Classification definitions: Evidence Class = Explicit / Inferred / Disputed / Candidate / Unknown. Status = Confirmed / Candidate / Disputed / Blocked / Target.*

| Req ID | Requirement Statement | Evidence Class | Status | Source Reference |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-INT-01** | The RFC intake form shall be initiated in Appian. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-INT-02** | A submitted RFC in Appian shall create a ServiceNow Change Request and link the Appian request number to the ServiceNow CHG number. | Explicit | Confirmed | SRC-DOC-01, SRC-PPT-01 |
| **REQ-CAT-01** | Activity selection shall use a four-tier hierarchy: Change Category (`u_service_category`), Activity Category (`u_service_subcategory`), Activity Subcategory (`u_service_l1`), and Service L2 (`u_service_l2`). | Explicit | Confirmed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-CAT-02** | The Standard Change Catalogue shall be filtered by the Change Agent's affiliated company. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-CAT-03** | Change Manager and MNP Service Desk roles shall be permitted to view all Standard Change Catalogue entries without company filtering. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-CAT-04** | Where a Change Agent is linked to more than one company for the same activity, catalogue filtering handling policy is: *Required outcome: Unknown / Not established from supplied evidence*. | Explicit | Unknown | SRC-DOC-01 |
| **REQ-ROU-01** | Where an assignment group mapping is defined for an activity in the catalogue, the change shall be routed to that mapped `assignment_group`. | Explicit | Confirmed | SRC-XLS-01, SRC-MAP-01 |
| **REQ-ROU-02** | Where no assignment group mapping exists for an activity, the change shall be allocated through PSN Helpdesk. | Explicit | Confirmed | SRC-MAP-01 |
| **REQ-DOC-01** | Required supporting documentation rules (form-wide mandatory MOP/SWMS and Vendor Release Notes for Software Update/Upgrade vs activity-row boolean flags `MOP Required?`, `SWMS Required?`, `Release Notes Required?`) are: *Status: Disputed*. | Disputed | Disputed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-TIM-01** | Lead-time calculation rules (specification formulas vs activity-row explicit lead-time values) are: *Status: Disputed*. | Disputed | Disputed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-APP-01** | Minor changes shall require Change Manager approval. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-APP-02** | Significant changes shall require CAB approval. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-APP-03** | Major changes shall require CAB + TAEC approval. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-APP-04** | Standard Changes shall skip manual approval. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-01** | Standard Change state progression path (New $\rightarrow$ Assess $\rightarrow$ Authorise $\rightarrow$ Scheduled with automated progression vs New $\rightarrow$ Scheduled for site inspection only) is: *Status: Disputed*. | Disputed | Disputed | SRC-DOC-01, SRC-MAP-01 |
| **REQ-LIF-02** | For a Change Request in `Implement` state, the Planned Start Date shall be locked; Planned End Date may be amended subject to conflict checking. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-03** | If Current Time > Planned End Date and the Change Request is in `Scheduled` state, the system shall close the Change Request as `No Show` and cancel the linked site access request. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-04** | If Current Time > Planned End Date and the Change Request is in `Implement` state with no Actual End Time, the system shall set Actual End Time to Planned End Time, create a NOCC closure task, transition the Change Request to `Review`, and close the Change Request after the NOCC closure task is completed. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-05** | Target trigger: First site visit triggers transition of Change Request to `Implement` for changes requiring site attendance. | Explicit | Target | SRC-PPT-01 |
| **REQ-LIF-06** | Target trigger: Final site visit triggers creation of a post-implementation task for NOCC and populates Actual End Date. | Explicit | Target | SRC-PPT-01 |
| **REQ-ACC-01** | If site access is required, at least one Work Type block shall be required. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-02** | Visitors selected for a Work Type must be qualified for that Work Type. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-03** | Specific minimum crew requirements per Work Type are: *Required outcome: Unknown / Not established from supplied evidence*. | Explicit | Unknown | SRC-DOC-01 |
| **REQ-ACC-04** | The RFC form shall capture Question 67 (site key required: Yes/No) and Question 68 (key type: GRN09, CyberKey, Other). | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-05** | Question 69 (CyberKey serial number) conditional visibility validation rule (*"Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68"*) is: *Status: Disputed / Blocked*. | Disputed | Blocked | SRC-DOC-01 |

---

## 3. Solution-Neutral Delivery Backlog & Decomposition

### 3.1 Implementation-Ready Work Items

#### Epic 1: Intake Integration & Classification
- **BL-INT-01: Appian RFC Submission to ServiceNow Creation**
  - *Description:* When an RFC is submitted in Appian, create a ServiceNow Change Request record and link the Appian request number to the ServiceNow CHG number.
  - *Traceability:* Traces to REQ-INT-01, REQ-INT-02.
- **BL-CAT-01: Four-Tier Activity Hierarchy Navigation**
  - *Description:* Provide activity selection structured as Tier 1 (`u_service_category`), Tier 2 (`u_service_subcategory`), Tier 3 (`u_service_l1`), and Tier 4 (`u_service_l2`).
  - *Traceability:* Traces to REQ-CAT-01.
- **BL-CAT-02: Catalogue Role-Based Visibility and Single-Company Filtering**
  - *Description:* Filter the Standard Change Catalogue by the Change Agent's affiliated company. Provide unrestricted visibility of all catalogue entries to Change Manager and MNP Service Desk roles.
  - *Traceability:* Traces to REQ-CAT-02, REQ-CAT-03.
- **BL-ROU-01: Catalogue-Driven Assignment Routing & Fallback**
  - *Description:* Route the Change Request to the `assignment_group` mapped in the catalogue. Where no mapping exists, allocate to PSN Helpdesk.
  - *Traceability:* Traces to REQ-ROU-01, REQ-ROU-02.

#### Epic 2: Governance & Approval Baseline
- **BL-APP-01: Change Type Approval Tier Execution**
  - *Description:* Route Minor changes to Change Manager approval, Significant changes to CAB approval, Major changes to CAB + TAEC approval, and bypass manual approval for Standard Changes.
  - *Traceability:* Traces to REQ-APP-01, REQ-APP-02, REQ-APP-03, REQ-APP-04.

#### Epic 3: Change Lifecycle Automation
- **BL-LIF-01: In-Flight Schedule Lock & Amendment**
  - *Description:* For Change Requests in `Implement` state, lock Planned Start Date and permit amendments to Planned End Date subject to conflict checking.
  - *Traceability:* Traces to REQ-LIF-02.
- **BL-LIF-02: Scheduled No-Show Auto-Closure**
  - *Description:* When Current Time > Planned End Date for a Change Request in `Scheduled` state, close the Change Request as `No Show` and cancel the linked site access request.
  - *Traceability:* Traces to REQ-LIF-03.
- **BL-LIF-03: Overdue Implementation Review & NOCC Task Generation**
  - *Description:* When Current Time > Planned End Date for a Change Request in `Implement` state with no Actual End Time, set Actual End Time to Planned End Time, create a NOCC closure task, transition the CR to `Review`, and close upon task completion.
  - *Traceability:* Traces to REQ-LIF-04.

#### Epic 4: Site Access & Key Intake
- **BL-ACC-01: Site Access Work Type & Visitor Qualification Capture**
  - *Description:* Require at least one Work Type block when site access is selected, and enforce that selected visitors are qualified for that Work Type.
  - *Traceability:* Traces to REQ-ACC-01, REQ-ACC-02.
- **BL-ACC-02: Site Key and Key Type Data Capture**
  - *Description:* Capture Question 67 (site key required) and Question 68 (key type: GRN09, CyberKey, Other).
  - *Traceability:* Traces to REQ-ACC-04.

---

### 3.2 Sourced Decision Items (Blocked / Target Scope)

- **DEC-01: Multi-Company Change Agent Filtering Policy**
  - *Condition:* Change Agents linked to multiple companies for the same activity (REQ-CAT-04).
  - *Required outcome:* Unknown / Not established from supplied evidence.
- **DEC-02: Document Upload Rule Reconciliation**
  - *Condition:* Contradiction between global mandatory document rules in SRC-DOC-01 and per-activity boolean flags in SRC-XLS-01 (REQ-DOC-01).
  - *Required outcome:* Unknown / Not established from supplied evidence.
- **DEC-03: Lead-Time Calculation Precedence**
  - *Condition:* Contradiction between formulaic lead times in SRC-DOC-01 and operational matrix row values in SRC-XLS-01 (REQ-TIM-01).
  - *Required outcome:* Unknown / Not established from supplied evidence.
- **DEC-04: Standard Change State Flow Alignment**
  - *Condition:* Process map progression (New $\rightarrow$ Assess $\rightarrow$ Authorise $\rightarrow$ Scheduled) vs annotation (New $\rightarrow$ Scheduled for site inspection) vs specification skip manual approval (REQ-LIF-01).
  - *Required outcome:* Unknown / Not established from supplied evidence.
- **DEC-05: CyberKey Question 69 Validation Logic Syntax**
  - *Condition:* Text contradiction in SRC-DOC-01 validation note (*"Yes is selected for Question 67 is No"*) (REQ-ACC-05).
  - *Required outcome:* Unknown / Not established from supplied evidence.
- **DEC-06: Work Type Minimum Crew Quantities**
  - *Condition:* Specification states some Work Types have minimum crew requirements without defining values (REQ-ACC-03).
  - *Required outcome:* Unknown / Not established from supplied evidence.
- **DEC-07: Flagged User/Org Change Creation Policy**
  - *Condition:* MAP-01 Annotation 1: *"For user/org that has been flagged for poor performance or bad change practice. Can they proceed with change creation."*
  - *Required outcome:* Unknown / Not established from supplied evidence.
- **DEC-08: Post-Site-Visit Task Quota and SLAs**
  - *Condition:* MAP-01 Annotation 2: *"Post site visit tasks – Quota? 10% action – 90% Auto close? SLAs to be defined."*
  - *Required outcome:* Unknown / Not established from supplied evidence.
- **DEC-09: Task-Triggered Approval System of Record**
  - *Condition:* MAP-01 Annotation 3: *"Question – SNOW, Appian or other? Change task trigger a change approval."*
  - *Required outcome:* Unknown / Not established from supplied evidence.
- **DEC-10: State Handling for Minor/Date Changes**
  - *Condition:* MAP-01 Annotation 4: *"If minor change to change (such as date changes) move to Authorize (Or new state… such as 'Amend'.) TBD."*
  - *Required outcome:* Unknown / Not established from supplied evidence.
- **DEC-11: Site Attendance Automated State Triggers**
  - *Condition:* PPT-01 Target triggers (first site visit $\rightarrow$ Implement; final site visit $\rightarrow$ NOCC task + Actual End Date) (REQ-LIF-05, REQ-LIF-06).
  - *Required outcome:* Candidate/Target architecture; execution mechanism not established.

---

## 4. Acceptance Criteria

### AC-INT-01: Appian to ServiceNow Linkage (Traces to BL-INT-01 / REQ-INT-01, REQ-INT-02)
- **Given** an RFC form is initiated in Appian,
- **When** the RFC is submitted,
- **Then** a Change Request is created in ServiceNow and the Appian request number is linked to the ServiceNow CHG number.

### AC-CAT-01: Four-Tier Taxonomy Structure (Traces to BL-CAT-01 / REQ-CAT-01)
- **Given** an activity is being selected on the RFC intake form,
- **When** the user navigates the activity catalogue hierarchy,
- **Then** the selection tiers follow the sequence: Tier 1 Change Category (`u_service_category`), Tier 2 Activity Category (`u_service_subcategory`), Tier 3 Activity Subcategory (`u_service_l1`), and Tier 4 Service L2 (`u_service_l2`).

### AC-CAT-02: Catalogue Filtering by Single Affiliated Company (Traces to BL-CAT-02 / REQ-CAT-02)
- **Given** a Change Agent affiliated with a single company accesses the Standard Change Catalogue,
- **When** the catalogue is presented,
- **Then** only catalogue entries associated with the Change Agent's affiliated company are displayed.

### AC-CAT-03: Unrestricted Catalogue Access for Privileged Roles (Traces to BL-CAT-02 / REQ-CAT-03)
- **Given** a user with the Change Manager or MNP Service Desk role accesses the Standard Change Catalogue,
- **When** the catalogue is presented,
- **Then** all Standard Change Catalogue entries are displayed without company filtering.

### AC-ROU-01: Mapped Assignment Group Routing (Traces to BL-ROU-01 / REQ-ROU-01)
- **Given** a submitted Change Request has an activity with an `assignment_group` defined in the catalogue,
- **When** assignment routing is evaluated,
- **Then** the Change Request is assigned to that mapped `assignment_group`.

### AC-ROU-02: Fallback Routing to PSN Helpdesk (Traces to BL-ROU-01 / REQ-ROU-02)
- **Given** a submitted Change Request has an activity with no assignment group mapping in the catalogue,
- **When** assignment routing is evaluated,
- **Then** the Change Request is allocated through PSN Helpdesk.

### AC-APP-01: Change Approval Routing by Change Type (Traces to BL-APP-01 / REQ-APP-01 to REQ-APP-04)
- **Scenario 1: Minor Change Approval**
  - **Given** a Change Request classified as Minor,
  - **When** the change moves to approval,
  - **Then** approval is required from the Change Manager.
- **Scenario 2: Significant Change Approval**
  - **Given** a Change Request classified as Significant,
  - **When** the change moves to approval,
  - **Then** approval is required from CAB.
- **Scenario 3: Major Change Approval**
  - **Given** a Change Request classified as Major,
  - **When** the change moves to approval,
  - **Then** approval is required from CAB and TAEC.
- **Scenario 4: Standard Change Approval Bypass**
  - **Given** a Change Request classified as Standard,
  - **When** the change is submitted,
  - **Then** manual approval is skipped.

### AC-LIF-01: In-Flight Schedule Locking and End Date Amendment (Traces to BL-LIF-01 / REQ-LIF-02)
- **Given** a Change Request is in `Implement` state,
- **When** schedule dates are edited,
- **Then** Planned Start Date is locked and cannot be changed, and Planned End Date may be amended subject to conflict checking.

### AC-LIF-02: Scheduled State Overdue Expiry (Traces to BL-LIF-02 / REQ-LIF-03)
- **Given** a Change Request is in `Scheduled` state and has a linked site access request,
- **When** Current Time > Planned End Date,
- **Then** the Change Request is closed as `No Show` and the linked site access request is cancelled.

### AC-LIF-03: Implement State Overdue Transition and NOCC Task Creation (Traces to BL-LIF-03 / REQ-LIF-04)
- **Given** a Change Request is in `Implement` state with no Actual End Time recorded,
- **When** Current Time > Planned End Date,
- **Then** Actual End Time is set to Planned End Time, a NOCC closure task is created, the Change Request transitions to `Review`, and the Change Request closes after the NOCC closure task is completed.

### AC-ACC-01: Mandatory Work Type for Site Access (Traces to BL-ACC-01 / REQ-ACC-01)
- **Given** site access is indicated as required on the intake form,
- **When** site access details are entered,
- **Then** at least one Work Type block must be provided.

### AC-ACC-02: Visitor Qualification Enforcement (Traces to BL-ACC-01 / REQ-ACC-02)
- **Given** a Work Type block is added to a site access request,
- **When** visitors are selected for that Work Type,
- **Then** only visitors qualified for that Work Type are permitted.

### AC-ACC-03: Site Key and Key Type Data Capture (Traces to BL-ACC-02 / REQ-ACC-04)
- **Given** the RFC intake form is accessed,
- **When** the key questions are displayed,
- **Then** Question 67 captures whether a site key is required, and Question 68 captures the key type with options `GRN09`, `CyberKey`, or `Other`.

---

## 5. Requirements Traceability Matrix (RTM)

| Source ID | Requirement ID | Delivery Item ID | Acceptance Criteria ID | Status / Readiness |
| :--- | :--- | :--- | :--- | :--- |
| SRC-DOC-01, PPT-01 | REQ-INT-01, REQ-INT-02 | BL-INT-01 | AC-INT-01 | Implementation-Ready |
| SRC-DOC-01, XLS-01 | REQ-CAT-01 | BL-CAT-01 | AC-CAT-01 | Implementation-Ready |
| SRC-DOC-01 | REQ-CAT-02, REQ-CAT-03 | BL-CAT-02 | AC-CAT-02, AC-CAT-03 | Implementation-Ready |
| SRC-DOC-01 | REQ-CAT-04 | DEC-01 | *None (Outcome Unknown)* | Blocked / Decision Item |
| SRC-XLS-01, MAP-01 | REQ-ROU-01, REQ-ROU-02 | BL-ROU-01 | AC-ROU-01, AC-ROU-02 | Implementation-Ready |
| SRC-DOC-01, XLS-01 | REQ-DOC-01 | DEC-02 | *None (Disputed)* | Blocked / Decision Item |
| SRC-DOC-01, XLS-01 | REQ-TIM-01 | DEC-03 | *None (Disputed)* | Blocked / Decision Item |
| SRC-XLS-01, DOC-01 | REQ-APP-01 – REQ-APP-04 | BL-APP-01 | AC-APP-01 | Implementation-Ready |
| SRC-DOC-01, MAP-01 | REQ-LIF-01 | DEC-04 | *None (Disputed)* | Blocked / Decision Item |
| SRC-DOC-01 | REQ-LIF-02 | BL-LIF-01 | AC-LIF-01 | Implementation-Ready |
| SRC-DOC-01 | REQ-LIF-03 | BL-LIF-02 | AC-LIF-02 | Implementation-Ready |
| SRC-DOC-01 | REQ-LIF-04 | BL-LIF-03 | AC-LIF-03 | Implementation-Ready |
| SRC-PPT-01 | REQ-LIF-05, REQ-LIF-06 | DEC-11 | *None (Target Scope)* | Target / Candidate |
| SRC-DOC-01 | REQ-ACC-01, REQ-ACC-02 | BL-ACC-01 | AC-ACC-01, AC-ACC-02 | Implementation-Ready |
| SRC-DOC-01 | REQ-ACC-03 | DEC-06 | *None (Outcome Unknown)* | Blocked / Decision Item |
| SRC-DOC-01 | REQ-ACC-04 | BL-ACC-02 | AC-ACC-03 | Implementation-Ready |
| SRC-DOC-01 | REQ-ACC-05 | DEC-05 | *None (Disputed/Blocked)* | Blocked / Decision Item |
| SRC-MAP-01 | MAP-01 Annotations 1–4 | DEC-07 – DEC-10 | *None (Process Map WIP)* | Blocked / Decision Items |

---

## 6. Sourced Contradictions, Ambiguities, and Unresolved Decisions

1. **Supporting Document Upload Mandates (SRC-DOC-01 vs SRC-XLS-01):**
   - *Conflict:* SRC-DOC-01 mandates MOP and SWMS uploads globally on the RFC form and Release Notes for Software Update/Upgrade. SRC-XLS-01 controls MOP, SWMS, and Release Notes via per-row boolean flags (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`) where individual activities have false values (e.g., Maintenance Air Conditioning has `MOP Required = false`).
   - *Status:* Disputed. Source precedence is not established.
2. **Lead-Time Calculation Rules (SRC-DOC-01 vs SRC-XLS-01):**
   - *Conflict:* SRC-DOC-01 establishes formulas (e.g., Minor NSA = 5 business days processing + 1 day; Major NSA = 10 business days after next CAB + 14 days). SRC-XLS-01 establishes explicit days per row (e.g., Minor NSA = 6 days; Major = `54 + number of days to next CAB after submission`).
   - *Status:* Disputed. Source precedence is not established.
3. **Question 69 Conditional Visibility Syntax (SRC-DOC-01):**
   - *Conflict:* Field 69 validation note states: *"Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68."* This syntax contains contradictory conditions (*"Yes is selected for Question 67 is No"*).
   - *Status:* Disputed / Blocked.
4. **Standard Change State Lifecycle (SRC-DOC-01 vs SRC-MAP-01):**
   - *Conflict:* SRC-MAP-01 process flow shows `New -> Assess -> Authorise -> Scheduled` with automatic progression, while a separate annotation shows `New -> Scheduled` for site inspection only. SRC-DOC-01 states Standard Changes skip manual approval.
   - *Status:* Disputed.
5. **Multi-Company Affiliation Set-Handling (SRC-DOC-01):**
   - *Ambiguity:* SRC-DOC-01 states Change Agents may be linked to more than one company for the same activity, but establishes no set-handling policy (union, selection, primary, fallback).
   - *Required outcome:* Unknown / Not established from supplied evidence.
6. **Work Type Crew Size Thresholds (SRC-DOC-01):**
   - *Ambiguity:* SRC-DOC-01 states *"Some Work Types have minimum crew requirements"* but does not define which Work Types or what minimum quantities apply.
   - *Required outcome:* Unknown / Not established from supplied evidence.
7. **Flagged User/Organization Change Creation (SRC-MAP-01 Annotation 1):**
   - *Annotation:* *"For user/org that has been flagged for poor performance or bad change practice. Can they proceed with change creation."*
   - *Required outcome:* Unknown / Not established from supplied evidence.
8. **Post-Site-Visit Task Quota and SLAs (SRC-MAP-01 Annotation 2):**
   - *Annotation:* *"Post site visit tasks – Quota? 10% action – 90% Auto close? SLAs to be defined."*
   - *Required outcome:* Unknown / Not established from supplied evidence.
9. **Task Approval Trigger System of Record (SRC-MAP-01 Annotation 3):**
   - *Annotation:* *"Question – SNOW, Appian or other? Change task trigger a change approval."*
   - *Required outcome:* Unknown / Not established from supplied evidence.
10. **State Handling for In-Flight Minor/Date Changes (SRC-MAP-01 Annotation 4):**
    - *Annotation:* *"If minor change to change (such as date changes) move to Authorize (Or new state… such as 'Amend'.) TBD."*
    - *Required outcome:* Unknown / Not established from supplied evidence.
11. **Target Automated Site Attendance Triggers (SRC-PPT-01):**
    - *Target Concept:* PPT-01 identifies target triggers for first site visit ($\rightarrow$ `Implement`) and final site visit ($\rightarrow$ NOCC task + Actual End Date).
    - *Status:* Candidate / Target state.

---

## 7. Completeness & Readiness Assessment

### 7.1 Assessment Summary: Partially Ready

- **Implementation-Ready Baseline:**
  - Appian-to-ServiceNow RFC intake linkage (REQ-INT-01, REQ-INT-02).
  - 4-tier taxonomy structure (REQ-CAT-01).
  - Catalogue filtering for single-company agents and unrestricted role access (REQ-CAT-02, REQ-CAT-03).
  - Catalogue assignment routing and PSN Helpdesk fallback (REQ-ROU-01, REQ-ROU-02).
  - Baseline approval routing by Change Type (Minor $\rightarrow$ Change Manager, Significant $\rightarrow$ CAB, Major $\rightarrow$ CAB + TAEC, Standard $\rightarrow$ Skip manual) (REQ-APP-01 – REQ-APP-04).
  - Change lifecycle automated rules: Planned Start Date lock during `Implement`, overdue `Scheduled` closure to `No Show` with site access cancellation, and overdue `Implement` review transition with NOCC task generation (REQ-LIF-02, REQ-LIF-03, REQ-LIF-04).
  - Site access Work Type block mandate, visitor qualification check, and key Questions 67/68 data capture (REQ-ACC-01, REQ-ACC-02, REQ-ACC-04).

- **Source-Blocked Areas (Preserved without Invention):**
  - Multi-company filtering set-handling (REQ-CAT-04 / DEC-01).
  - Document upload mandate vs operational matrix flags (REQ-DOC-01 / DEC-02).
  - Specification lead-time formulas vs matrix row values (REQ-TIM-01 / DEC-03).
  - Standard Change intermediate state progression (REQ-LIF-01 / DEC-04).
  - Question 69 conditional visibility syntax (REQ-ACC-05 / DEC-05).
  - Specific Work Type crew minimums (REQ-ACC-03 / DEC-06).
  - Draft process map WIP annotations 1–4 (DEC-07 – DEC-10).
  - Target-state site visit transition mechanics (REQ-LIF-05, REQ-LIF-06 / DEC-11).

---

## 8. Open Questions (Source-Linked One-for-One)

1. **Multi-Company Catalogue Filtering:** What is the required catalogue filtering and selection rule when a Change Agent is linked to multiple companies for the same activity (REQ-CAT-04)?
2. **Document Requirement Source Precedence:** Does the global document mandate from SRC-DOC-01 or the activity-specific boolean configuration from SRC-XLS-01 take precedence for MOP, SWMS, and Release Notes (REQ-DOC-01)?
3. **Lead-Time Calculation Precedence:** Does the lead-time calculation formula from SRC-DOC-01 or the specific numeric/formula value from SRC-XLS-01 govern activity lead times (REQ-TIM-01)?
4. **Question 69 Visibility Logic:** What are the exact display conditions for Question 67 and Question 68 that make Question 69 (CyberKey serial number) visible (REQ-ACC-05)?
5. **Standard Change State Progression:** Does a Standard Change progress through `New -> Assess -> Authorise -> Scheduled` automatically, or transition directly from `New -> Scheduled` (REQ-LIF-01)?
6. **Work Type Crew Minimums:** Which specific Work Types require minimum crew sizes, and what are the required minimum visitor counts for each (REQ-ACC-03)?
7. **Flagged User/Org Change Creation (MAP-01 Annotation 1):** Can a user or organization flagged for poor performance or bad change practice proceed with change creation (DEC-07)?
8. **Post-Site-Visit Task Allocation & SLAs (MAP-01 Annotation 2):** What are the quotas (e.g., 10% action vs 90% auto-close) and SLA definitions for post-site-visit tasks (DEC-08)?
9. **Task Approval Trigger System (MAP-01 Annotation 3):** Which system (ServiceNow, Appian, or other) manages the task trigger for change approval (DEC-09)?
10. **Minor/Date Change State Routing (MAP-01 Annotation 4):** Does a minor modification or date change to an existing change move the record to `Authorise`, a new `Amend` state, or another state (DEC-10)?
