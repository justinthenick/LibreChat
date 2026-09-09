# BA Benchmark Raw Result

> Raw model output. Not an evaluator score.

## Run metadata

- Benchmark: `Benchmark 042 — Multi-Source BA Model Comparison`
- Mode: `skill`
- Provider: `gemini`
- Model: `gemini-3.8-flash`
- Status: `success`
- Started: `2026-09-09T04:24:54Z`
- Ended: `2026-09-09T04:25:17Z`
- Temperature: `0.0`
- Max output tokens: `8192`
- Input SHA-256: `1432330128630c368efc83ea65458ebec990d731cc2dd0b11d77148c13b21af3`
- Prompt SHA-256: `327f4aeb1a6fd16d585800b3706194285a459265cd69d02950e95b5d07b717e1`
- Skill: `/volume1/docker/librechat-ba-lab/custom/ba-agent/skills/prepare-implementation-ready-requirements/SKILL.md`
- Skill version: `0.2.3`
- Skill SHA-256: `942aa6f4c1046658b650c5ad90c47e0f958f7bbfe312862f15c94fa8f1adb747`
- Finish reason: `MAX_TOKENS`
- Usage metadata: `{"candidatesTokenCount": 6858, "promptTokenCount": 5097, "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 5097}], "serviceTier": "standard", "thoughtsTokenCount": 1330, "totalTokenCount": 13285}`

---

## Model output

# Integrated Change Intake and Site Access — Business Analysis Package

## 1. Source Register

| Source ID | Title / Artifact Name | Format / Type | Authority / State | Sourced Scope Summary |
|---|---|---|---|---|
| **SRC-DOC-01** | Functional Enhancement Specification | Word Document | Baseline specification | RFC intake in Appian; ServiceNow linking; company-based catalogue filtering; 4-tier activity hierarchy; date/lead-time rules; document upload rules (MOP, SWMS, Vendor Release Notes); site access Work Types, visitor qualifications, minimum crew; Field 67–69 key logic; lifecycle state transitions, locks, timeout closures. |
| **SRC-XLS-01** | Service and Activity Catalogue | Excel Workbook | Operational configuration matrix | Operational catalogue schema: 4-tier taxonomy (`u_service_category`, `u_service_subcategory`, `u_service_l1`, `u_service_l2`), default `assignment_group`, Standard Change availability, SAR availability, Change Type, permitted PSN impact (NSA/SA/RA), initial risk level, activity-specific document requirement booleans (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`), approval matrix by Change Type, activity-specific lead-time formulas. Precedence between XLS and DOC is unspecified. |
| **SRC-MAP-01** | Post-ServiceNow Review Process Map | PDF Process Map | Draft / WIP | Standard Change progression states (v1/v2 New -> Assess -> Authorise -> Scheduled via automatic progression; Site Inspection annotation New -> Scheduled); assignment group fallback routing to PSN Helpdesk; four explicit unresolved design annotations (poor performance blocking, post-site visit task quota/SLA, task approval trigger system, date change amendment state). |
| **SRC-PPT-01** | Internal Change Transformation Presentation | PowerPoint Slide Deck | Strategy / Target-state briefing | Target business drivers (eliminate swivel-chair Service Desk creation, reduce processing time and double handling); 4-tier taxonomy intent for classification/allocation; site visit event integration (first site visit triggers Implement; final site visit creates NOCC task and populates Actual End Date). Explicitly notes no NFRs, API schemas, retry logic, or database architectures are defined. |

---

## 2. Requirements Register

*Evidence Classes: Explicit, Inferred, Proposed, Assumption, Disputed, Unknown*  
*Statuses: Confirmed, Candidate, Target, Disputed, Deferred, Unknown*

| Req ID | Requirement Statement | Evidence Class | Status | Source Reference |
|---|---|---|---|---|
| **REQ-INT-01** | The RFC intake form shall be initiated in Appian. | Explicit | Confirmed | SRC-DOC-01, SRC-PPT-01 |
| **REQ-INT-02** | A submitted Appian RFC shall create a ServiceNow Change Request and link the Appian request number to the ServiceNow Change Request number (CHG). | Explicit | Confirmed | SRC-DOC-01, SRC-PPT-01 |
| **REQ-CAT-01** | Activity selection on the intake form shall use a four-tier taxonomy: Change Category / `u_service_category`, Activity Category / `u_service_subcategory`, Activity Subcategory / `u_service_l1`, and Service L2 / `u_service_l2`. | Explicit | Confirmed | SRC-DOC-01, SRC-XLS-01, SRC-PPT-01 |
| **REQ-CAT-02** | Standard Change Catalogue entries shall be filtered by the Change Agent's affiliated company. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-CAT-03** | Change Manager and MNP Service Desk roles shall be permitted to view all Standard Change Catalogue entries. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-CAT-04** | Handling of Standard Change Catalogue filtering when a Change Agent is linked to more than one company for the same activity. | Explicit | Unknown | SRC-DOC-01 |
| **REQ-ROU-01** | If an assignment group mapping exists in the catalogue for the selected activity, the change request shall be allocated to that mapped assignment group. | Explicit | Confirmed | SRC-MAP-01, SRC-XLS-01 |
| **REQ-ROU-02** | If no assignment group mapping exists in the catalogue for the selected activity, the change request shall be allocated through PSN Helpdesk. | Explicit | Confirmed | SRC-MAP-01 |
| **REQ-DOC-01** | Document upload requirement determination (global mandatory MOP and SWMS uploads on the RFC form, and Vendor Release Notes for Software Update/Upgrade vs catalogue activity-level boolean flags `MOP Required?`, `SWMS Required?`, `Release Notes Required?`). | Disputed | Disputed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-TIM-01** | Minimum lead-time calculation and validation rules (specification-level formula by Change Type and impact vs catalogue activity-row explicit lead-time figures/formulas). | Disputed | Disputed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-ACC-01** | If site access is required for a change, the intake submission shall require at least one Work Type block. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-02** | Visitors selected for a Work Type must be qualified for that Work Type. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-03** | Selected Work Types shall enforce their configured minimum crew requirements. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-01** | The intake form shall capture whether a site key is required via Field 67. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-02** | When a site key is requested, Field 68 shall capture the key type with options: GRN09, CyberKey, or Other. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-03** | Visibility and validation condition for Field 69 (CyberKey serial number) given the contradictory rule text ("Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68"). | Disputed | Disputed | SRC-DOC-01 |
| **REQ-APR-01** | Minor changes shall require Change Manager approval. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-APR-02** | Significant changes shall require CAB approval. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-APR-03** | Major changes shall require CAB and TAEC approval. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-LIF-01** | Standard Changes shall bypass manual approval. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-02** | Standard Change lifecycle state path (Process Map v1/v2 New -> Assess -> Authorise -> Scheduled with auto-progression vs Site inspection annotation New -> Scheduled). | Disputed | Disputed | SRC-MAP-01 |
| **REQ-LIF-03** | For a change in Implement state, the Planned Start Date shall be locked against modification. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-04** | For a change in Implement state, the Planned End Date may be amended, subject to conflict checking. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-05** | If Current Time > Planned End Date and the Change Request is in Scheduled state, the system shall close the Change Request as No Show and cancel the linked site access request. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-06** | If Current Time > Planned End Date and the Change Request is in Implement state with no Actual End Time, the system shall set Actual End Time to Planned End Time, create a NOCC closure task, transition the Change Request to Review state, and close the Change Request after the NOCC task is completed. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-07** | Transition of change request needing site attendance to Implement state upon first site visit. | Proposed | Target | SRC-PPT-01 |
| **REQ-LIF-08** | Population of Actual End Date and generation of post-implementation NOCC task upon final site visit. | Proposed | Target | SRC-PPT-01 |
| **REQ-UNC-01** | Eligibility of users or organisations flagged for poor performance or bad change practice to proceed with change creation. | Explicit | Unknown | SRC-MAP-01 |
| **REQ-UNC-02** | Execution quota (10% action vs 90% auto-close) and SLAs for post-site-visit tasks. | Explicit | Unknown | SRC-MAP-01 |
| **REQ-UNC-03** | Governing system (ServiceNow, Appian, or other) for change task triggering a change approval. | Explicit | Unknown | SRC-MAP-01 |
| **REQ-UNC-04** | State progression for minor change amendments (e.g. date changes): transition to Authorise vs transition to new dedicated state (e.g. "Amend"). | Explicit | Unknown | SRC-MAP-01 |

---

## 3. Delivery Decomposition (Solution-Neutral Backlog)

### Epic 1: Intake & Cross-System Record Linking (INT)
- **BL-INT-01: Appian Intake Initiation and Cross-System Record Linking**
  - *Description:* Change Agents initiate the RFC intake form in Appian. Upon submission, a corresponding ServiceNow Change Request is created and linked directly to the Appian request identifier.
  - *Tracing:* REQ-INT-01, REQ-INT-02.

### Epic 2: Catalogue Filtering & Assignment Routing (CAT)
- **BL-CAT-01: Four-Tier Activity Hierarchy Navigation**
  - *Description:* Change Agents select change activities via a 4-tier taxonomy structure matching `u_service_category`, `u_service_subcategory`, `u_service_l1`, and `u_service_l2`.
  - *Tracing:* REQ-CAT-01.
- **BL-CAT-02: Single-Affiliation Standard Change Catalogue Visibility**
  - *Description:* Filter available Standard Change Catalogue items based on the Change Agent’s single affiliated company. Change Manager and MNP Service Desk roles have visibility across all Standard Change Catalogue items regardless of company affiliation.
  - *Tracing:* REQ-CAT-02, REQ-CAT-03.
- **BL-ROU-01: Activity Assignment Group Allocation & Fallback**
  - *Description:* Route submitted change requests to the default assignment group configured for the selected 4-tier activity row. If no assignment group is configured in the matrix row, route the change request to PSN Helpdesk.
  - *Tracing:* REQ-ROU-01, REQ-ROU-02.

### Epic 3: Site Access & Key Management (ACC)
- **BL-ACC-01: Work Type and Visitor Qualification Enforcement**
  - *Description:* Capture required site access details on the intake form. If site access is marked as required, enforce selection of at least one Work Type block, enforce that selected visitors meet qualification rules for that Work Type, and enforce configured minimum crew size rules.
  - *Tracing:* REQ-ACC-01, REQ-ACC-02, REQ-ACC-03.
- **BL-ACC-02: Site Key Requirement and Type Capture**
  - *Description:* Capture key requirement indicator (Field 67) and, where requested, capture key type selection (Field 68) among GRN09, CyberKey, or Other.
  - *Tracing:* REQ-KEY-01, REQ-KEY-02.

### Epic 4: Approval Routing & Automated Lifecycle Governance (LIF)
- **BL-APR-01: Multi-Tier Change Approval Gate Enforcement**
  - *Description:* Route change requests for manual approvals based on Change Type: Minor changes require Change Manager approval; Significant changes require CAB approval; Major changes require CAB and TAEC approval. Standard Changes skip manual approval gates.
  - *Tracing:* REQ-APR-01, REQ-APR-02, REQ-APR-03, REQ-LIF-01.
- **BL-LIF-01: Implement State Schedule Amendment Locks**
  - *Description:* While a Change Request is in Implement state, prevent updates to Planned Start Date. Permit updates to Planned End Date subject to conflict checking.
  - *Tracing:* REQ-LIF-03, REQ-LIF-04.
- **BL-LIF-02: Automated Scheduled Change Timeout (No Show)**
  - *Description:* For Change Requests in Scheduled state where Current Time exceeds Planned End Date, automatically close the Change Request with close code No Show and cancel any linked site access request.
  - *Tracing:* REQ-LIF-05.
- **BL-LIF-03: Automated In-Flight Timeout, NOCC Task Creation & Closure**
  - *Description:* For Change Requests in Implement state with no Actual End Time where Current Time exceeds Planned End Date, automatically populate Actual End Time with the Planned End Time value, generate a NOCC closure task, transition the change request to Review state, and close the change request once the NOCC closure task is marked complete.
  - *Tracing:* REQ-LIF-06.

---

## 4. Acceptance Criteria

Acceptance criteria are elaborated only for Confirmed items with source-established testable outcomes. Disputed, Target, and Unknown items are excluded from testable criteria and isolated in Section 6.

### BL-INT-01: Appian Intake Initiation and Cross-System Record Linking
- **AC-INT-01-01 (Appian Form Submission & Linking):**
  - **Given** an RFC form is completed in Appian,
  - **When** the user submits the RFC form,
  - **Then** a ServiceNow Change Request is created,
  - **And** the Appian request number is linked to the ServiceNow CHG number.

### BL-CAT-01: Four-Tier Activity Hierarchy Navigation
- **AC-CAT-01-01 (Four-Tier Hierarchy Navigation):**
  - **Given** an RFC form is open in Appian,
  - **When** the user selects an activity,
  - **Then** the selection is navigated across four sequential tiers: Change Category (`u_service_category`), Activity Category (`u_service_subcategory`), Activity Subcategory (`u_service_l1`), and Service L2 (`u_service_l2`).

### BL-CAT-02: Single-Affiliation Standard Change Catalogue Visibility
- **AC-CAT-02-01 (Catalogue Filtering by Affiliated Company):**
  - **Given** a Change Agent affiliated with a single company accesses the Standard Change Catalogue,
  - **When** the catalogue is presented,
  - **Then** only entries matching the Change Agent's affiliated company are displayed.
- **AC-CAT-02-02 (Privileged Role Full Catalogue Visibility):**
  - **Given** a user with the Change Manager or MNP Service Desk role accesses the Standard Change Catalogue,
  - **When** the catalogue is presented,
  - **Then** all Standard Change Catalogue entries are displayed regardless of company affiliation.

### BL-ROU-01: Activity Assignment Group Allocation & Fallback
- **AC-ROU-01-01 (Default Assignment Group Allocation):**
  - **Given** an activity is selected that has a configured default assignment group in the catalogue,
  - **When** the change request is created,
  - **Then** the change request is allocated to that mapped assignment group.
- **AC-ROU-01-02 (Fallback Allocation to PSN Helpdesk):**
  - **Given** an activity is selected that has no configured default assignment group mapping,
  - **When** the change request is created,
  - **Then** the change request is allocated through PSN Helpdesk.

### BL-ACC-01: Work Type and Visitor Qualification Enforcement
- **AC-ACC-01-01 (Site Access Requires Work Type):**
  - **Given** an RFC where site access is indicated as required,
  - **When** the user submits the request without adding at least one Work Type block,
  - **Then** the submission is prevented.
- **AC-ACC-01-02 (Visitor Qualification Verification):**
  - **Given** a Work Type block is added to a site access request,
  - **When** visitors are selected for that Work Type,
  - **Then** only visitors qualified for that Work Type are accepted.
- **AC-ACC-01-03 (Minimum Crew Size Verification):**
  - **Given** a Work Type that has a configured minimum crew requirement,
  - **When** visitors are assigned to that Work Type block,
  - **Then** the assignment is accepted only if the number of assigned visitors satisfies the minimum crew requirement.

### BL-ACC-02: Site Key Requirement and Type Capture
- **AC-ACC-02-01 (Key Requirement and Type Capture):**
  - **Given** an RFC form is open,
  - **When** the user reaches the key access section,
  - **Then** Field 67 captures whether a site key is required,
  - **And** Field 68 provides the key type options: GRN09, CyberKey, and Other.

### BL-APR-01: Multi-Tier Change Approval Gate Enforcement
- **AC-APR-01-01 (Standard Change Skips Approval):**
  - **Given** a change classified as Standard Change,
  - **When** the change request is submitted,
  - **Then** it skips manual approval.
- **AC-APR-01-02 (Minor Change Approval Gate):**
  - **Given** a change classified as Minor,
  - **When** approval routing is initiated,
  - **Then** approval is required from the Change Manager.
- **AC-APR-01-03 (Significant Change Approval Gate):**
  - **Given** a change classified as Significant,
  - **When** approval routing is initiated,
  - **Then** approval is required from the CAB.
- **AC-APR-01-04 (Major Change Approval Gate):**
  - **Given** a change classified as Major,
  - **When** approval routing is initiated,
  - **Then** approvals are required from both CAB and TAEC.

### BL-LIF-01: Implement State Schedule Amendment Locks
- **AC-LIF-01-01 (Planned Start Date Lock in Implement):**
  - **Given** a Change Request is in Implement state,
  - **When** a user attempts to edit the Planned Start Date,
  - **Then** the Planned Start Date is locked against modification.
- **AC-LIF-01-02 (Planned End Date Amendment in Implement):**
  - **Given** a Change Request is in Implement state,
  - **When** a user updates the Planned End Date,
  - **Then** the update is permitted subject to conflict checking.

### BL-LIF-02: Automated Scheduled Change Timeout (No Show)
- **AC-LIF-02-01 (Timeout for Scheduled Change):**
  - **Given** a Change Request is in Scheduled state,
  - **When** Current Time > Planned End Date,
  - **Then** the Change Request is closed as No Show,
  - **And** the linked site access request is cancelled.

### BL-LIF-03: Automated In-Flight Timeout, NOCC Task Creation & Closure
- **AC-LIF-03-01 (Timeout for In-Flight Implement Change):**
  - **Given** a Change Request is in Implement state with no Actual End Time,
  - **When** Current Time > Planned End Date,
  - **Then** Actual End Time is set to Planned End Time,
  - **And** a NOCC closure task is created,
  - **And** the Change Request is transitioned to Review state.
- **AC-LIF-03-02 (Closure Following NOCC Task Completion):**
  - **Given** a Change Request has transitioned to Review state following automated timeout,
  - **When** the linked NOCC closure task is completed,
  - **Then** the Change Request is closed.

---

## 5. Requirements Traceability Matrix (RTM)

| Source ID | Req ID | Delivery Backlog Item | Acceptance Criteria / Downstream Status | Status |
|---|---|---|---|---|
| SRC-DOC-01, SRC-PPT-01 | REQ-INT-01 | BL-INT-01 | AC-INT-01-01 | Confirmed |
| SRC-DOC-01, SRC-PPT-01 | REQ-INT-02 | BL-INT-01 | AC-INT-01-01 | Confirmed |
| SRC-DOC-01, SRC-XLS-01, SRC-PPT-01 | REQ-CAT-01 | BL-CAT-01 | AC-CAT-01-01 | Confirmed |
| SRC-DOC-01 | REQ-CAT-02 | BL-CAT-02 | AC-CAT-02-01 | Confirmed |
| SRC-DOC-01 | REQ-CAT-03 | BL-CAT-02 | AC-CAT-02-02 | Confirmed |
| SRC-DOC-01 | REQ-CAT-04 | N/A (Blocked) | Blocked (Multi-company catalogue filtering rule unknown) | Unknown |
| SRC-MAP-01, SRC-XLS-01 | REQ-ROU-01 | BL-ROU-01 | AC-ROU-01-01 | Confirmed |
| SRC-MAP-01 | REQ-ROU-02 | BL-ROU-01 | AC-ROU-01-02 | Confirmed |
| SRC-DOC-01, SRC-XLS-01 | REQ-DOC-01 | N/A (Blocked) | Blocked (Specification mandatory rules vs catalogue matrix booleans conflict) | Disputed |
| SRC-DOC-01, SRC-XLS-01 | REQ-TIM-01 | N/A (Blocked) | Blocked (Specification formulas vs catalogue row lead-time values conflict) | Disputed |
| SRC-DOC-01 | REQ-ACC-01 | BL-ACC-01 | AC-ACC-01-01 | Confirmed |
| SRC-DOC-01 | REQ-ACC-02 | BL-ACC-01 | AC-ACC-01-02 | Confirmed |
| SRC-DOC-01 | REQ-ACC-03 | BL-ACC-01 | AC-ACC-01-03 | Confirmed |
| SRC-DOC-01 | REQ-KEY-01 | BL-ACC-02 | AC-ACC-02-01 | Confirmed |
| SRC-DOC-01 | REQ-KEY-02 | BL-ACC-02 | AC-ACC-02-01 | Confirmed |
| SRC-DOC-01 | REQ-KEY-03 | N/A (Blocked) | Blocked (Contradictory conditional text for Field 69 visibility) | Disputed |
| SRC-XLS-01 | REQ-APR-01 | BL-APR-01 | AC-APR-01-02 | Confirmed |
| SRC-XLS-01 | REQ-APR-02 | BL-APR-01 | AC-APR-01-03 | Confirmed |
| SRC-XLS-01 | REQ-APR-03 | BL-APR-01 | AC-APR-01-04 | Confirmed |
| SRC-DOC-01 | REQ-LIF-01 | BL-APR-01 | AC-APR-01-01 | Confirmed |
| SRC-MAP-01 | REQ-LIF-02 | N/A (Blocked) | Blocked (Process Map v1/v2 vs Site inspection progression path conflict) | Disputed |
| SRC-DOC-01 | REQ-LIF-03 | BL-LIF-01 | AC-LIF-01-01 | Confirmed |
| SRC-DOC-01 | REQ-LIF-04 | BL-LIF-01 | AC-LIF-01-02 | Confirmed |
| SRC-DOC-01 | REQ-LIF-05 | BL-LIF-02 | AC-LIF-02-01 | Confirmed |
| SRC-DOC-01 | REQ-LIF-06 | BL-LIF-03 | AC-LIF-03-01, AC-LIF-03-02 | Confirmed |
| SRC-PPT-01 | REQ-LIF-07 | N/A (Target) | Deferred / Target (Site visit Implement trigger mechanism not established) | Target |
| SRC-PPT-01 | REQ-LIF-08 | N/A (Target) | Deferred / Target (Site visit Actual End Date & NOCC task mechanism not established) | Target |
| SRC-MAP-01 | REQ-UNC-01 | N/A (Blocked) | Blocked (Process Map annotation 1 unanswered) | Unknown |
| SRC-MAP-01 | REQ-UNC-02 | N/A (Blocked) | Blocked (Process Map annotation 2 unanswered) | Unknown |
| SRC-MAP-01 | REQ-UNC-03 | N/A (Blocked) | Blocked (Process Map annotation 3 unanswered) | Unknown |
| SRC-MAP-01 | REQ-UNC-04 | N/A (Blocked) | Blocked (Process Map annotation 4 unanswered) | Unknown |

---

## 6. Source-Created Contradictions, Ambiguities, and Unresolved Decisions

### DEC-01: Supporting Document Attachment Rules Precedence
- **Source Conflict:**
  - `SRC-DOC-01` states MOP upload is mandatory on the RFC form, SWMS upload is mandatory on the RFC form, and Vendor Release Notes are required for Software Update or Software Upgrade activities.
  - `SRC-XLS-01` defines activity-specific booleans (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`) where rows vary (e.g., Maintenance Air Conditioning requires SWMS but not MOP or Release Notes; Windows Patching requires Release Notes but neither MOP nor SWMS; Motorola Upgrade requires MOP and Release Notes but not SWMS).
  - No precedence rule is provided to resolve whether global document mandates override catalogue booleans or vice versa.
- **Required outcome:** Unknown / Not established from supplied evidence.

### DEC-02: Lead-Time Calculation Precedence and Formula Conflict
- **Source Conflict:**
  - `SRC-DOC-01` defines fixed category lead-time rules (Standard: 3 processing + 1 NSA / 14 SA; Minor: 5 processing + 1 NSA; Significant: 10 after next CAB + 1 NSA / 14 SA; Major: 10 after next CAB + 14 NSA / 1 month SA).
  - `SRC-XLS-01` defines row-level figures and formulas (e.g., Motorola Upgrade Significant lead time is `25 + number of days to next CAB after submission`; CCEP Major lead time is `54 + number of days to next CAB after submission`).
  - Neither artifact defines precedence, nor does `SRC-DOC-01` define Service Affecting (SA) lead time for Minor changes.
- **Required outcome:** Unknown / Not established from supplied evidence.

### DEC-03: Field 69 (CyberKey Serial Number) Visibility Condition Contradiction
- **Source Contradiction:**
  - `SRC-DOC-01` specifies the validation rule for Field 69 as: `"Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68."`
  - The condition contains contradictory statements regarding Question 67 ("Yes is selected" vs "is No").
- **Required outcome:** Unknown / Not established from supplied evidence.

### DEC-04: Multi-Company Change Agent Catalogue Filtering
- **Source Ambiguity:**
  - `SRC-DOC-01` states the Standard Change Catalogue is filtered by the Change Agent's affiliated company, but also notes Change Agents may be linked to more than one company for the same activity.
  - The filtering outcome when multiple company affiliations exist (e.g., union of catalogue entries, intersection, user prompt, or primary company selection) is unspecified.
- **Required outcome:** Unknown / Not established from supplied evidence.

### DEC-05: Standard Change Lifecycle State Progression Path
- **Source Conflict:**
  - `SRC-MAP-01` Process Map v1/v2 shows Standard Changes progressing automatically: `New -> Assess -> Authorise -> Scheduled`.
  - `SRC-MAP-01` contains a conflicting annotation for "Site inspection only" showing a Standard Change progressing directly: `New -> Scheduled`.
  - `SRC-DOC-01` states Standard Changes skip manual approval, but does not confirm whether Assess and Authorise states are traversed automatically or bypassed entirely.
- **Required outcome:** Unknown / Not established from supplied evidence.

### DEC-06: Process Map WIP Annotation 1 — Poor Performance Handling
- **Source Dimension:**
  - `SRC-MAP-01` records the open question: `"For user/org that has been flagged for poor performance or bad change practice. Can they proceed with change creation."`
- **Required outcome:** Unknown / Not established from supplied evidence.

### DEC-07: Process Map WIP Annotation 2 — Post-Site-Visit Task Quota and SLAs
-
