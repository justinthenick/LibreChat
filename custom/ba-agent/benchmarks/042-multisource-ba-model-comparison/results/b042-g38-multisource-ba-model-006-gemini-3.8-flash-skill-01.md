# BA Benchmark Raw Result

> Raw model output. Not an evaluator score.

## Run metadata

- Benchmark: `Benchmark 042 — Multi-Source BA Model Comparison`
- Mode: `skill`
- Provider: `gemini`
- Model: `gemini-3.8-flash`
- Status: `success`
- Started: `2026-09-09T05:19:23Z`
- Ended: `2026-09-09T05:19:55Z`
- Temperature: `0.0`
- Max output tokens: `16384`
- Input SHA-256: `1432330128630c368efc83ea65458ebec990d731cc2dd0b11d77148c13b21af3`
- Prompt SHA-256: `327f4aeb1a6fd16d585800b3706194285a459265cd69d02950e95b5d07b717e1`
- Skill: `/volume1/docker/librechat-ba-lab/custom/ba-agent/skills/prepare-implementation-ready-requirements/SKILL.md`
- Skill version: `0.2.3`
- Skill SHA-256: `942aa6f4c1046658b650c5ad90c47e0f958f7bbfe312862f15c94fa8f1adb747`
- Finish reason: `STOP`
- Usage metadata: `{"candidatesTokenCount": 9161, "promptTokenCount": 5097, "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 5097}], "serviceTier": "standard", "thoughtsTokenCount": 2237, "totalTokenCount": 16495}`

---

## Model output

# Integrated Change Intake and Site Access — Business Analysis Package

---

## 1. Source Register

| Source ID | Document Title & Type | Version / Status | Stated Purpose / Scope in Evidence |
| :--- | :--- | :--- | :--- |
| **SRC-DOC-01** | Functional Enhancement Specification (Word) | Baseline Specification | Defines functional rules for Appian RFC intake, ServiceNow integration, document attachments, site access, key management, date calculation formulas, and automated change lifecycle state handling. |
| **SRC-XLS-01** | Service and Activity Catalogue (Excel) | Operational Configuration Matrix | Configures four-tier operational taxonomy, assignment group mappings, standard change availability, SAR availability, change classification, approval hierarchy, permitted PSN impacts, and activity-level document/lead-time parameters. |
| **SRC-MAP-01** | Post-ServiceNow Review Process Map (PDF) | WIP / Draft | Maps Standard Change lifecycle pathways, fallback assignment routing, and identifies four explicit unresolved process questions/annotations. |
| **SRC-PPT-01** | Internal Change Transformation Presentation (PowerPoint) | Strategic / Target State Briefing | Identifies current operational pain points (swivel-chair creation, double handling, processing delays) and states target operational intents including direct creation from Appian, granular risk assessment, and site-visit lifecycle triggers. |

---

## 2. Requirements Register

### Evidence & Status Conventions
- **Evidence Class**: `Explicit` (directly stated in artifact text), `Inferred` (derived directly from explicit statement without expanding scope).
- **Requirement Status**: 
  - `Confirmed`: Established unequivocally by source evidence without conflicting source statements.
  - `Disputed`: Sourced requirement where two or more artifacts present conflicting rules.
  - `Candidate` / `Target`: Stated as a target state or proposed option without operational finality.
  - `Unknown`: Identified condition or dimension where required operational outcome is absent.

| Req ID | Requirement Statement | Evidence Class | Requirement Status | Source Mapping |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-INT-01** | The RFC intake form shall be initiated in Appian. | Explicit | Confirmed | SRC-DOC-01, SRC-PPT-01 |
| **REQ-INT-02** | A submitted Appian RFC shall create a ServiceNow Change Request (CR) directly and link the Appian request number to the ServiceNow CHG number. | Explicit | Confirmed | SRC-DOC-01, SRC-PPT-01 |
| **REQ-INT-03** | Standard Change Catalogue entries shall be filtered by the Change Agent's affiliated company. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-INT-04** | The system shall permit Change Agents to be linked to more than one company for the same activity. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-INT-05** | Change Manager and MNP Service Desk roles shall be permitted to view all Standard Change Catalogue entries. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-TAX-01** | Activity selection shall use a four-tier taxonomy hierarchy (DOC-01: Change Category, Activity Category, Activity Subcategory, Service L2; XLS-01: `u_service_category`, `u_service_subcategory`, `u_service_l1`, `u_service_l2`). | Explicit | Disputed (Taxonomy tier naming conflict) | SRC-DOC-01, SRC-XLS-01 |
| **REQ-ROU-01** | If an assignment group mapping exists in the catalogue for the selected activity, the CR shall be assigned to that mapped default assignment group. | Explicit | Confirmed | SRC-XLS-01, SRC-MAP-01 |
| **REQ-ROU-02** | If no assignment group mapping exists for the selected activity, the CR shall be allocated through the PSN Helpdesk. | Explicit | Confirmed | SRC-MAP-01 |
| **REQ-DOC-01** | Mandatory document upload rules: MOP and SWMS uploads are universally mandatory on the Appian RFC form (DOC-01), versus MOP and SWMS being conditionally required based on activity-level boolean flags `MOP Required?` and `SWMS Required?` (XLS-01). | Explicit | Disputed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-DOC-02** | Release Notes upload rules: Vendor Release Notes are required for Software Update or Software Upgrade activities (DOC-01), versus being governed by the activity-level `Release Notes Required?` boolean flag (XLS-01). | Explicit | Disputed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-DAT-01** | Lead-time and date calculations: Change lead times are governed by global formula tiers based on Change Type and Service Affecting status (DOC-01), versus explicit operational day figures and CAB offsets defined per activity in the catalogue (XLS-01). | Explicit | Disputed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-APP-01** | Standard Changes shall skip manual approval. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-APP-02** | Minor Changes shall require Change Manager approval. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-APP-03** | Significant Changes shall require CAB approval. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-APP-04** | Major Changes shall require both CAB and TAEC approval. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-LIF-01** | For a Standard Change, lifecycle progression shall follow New -> Assess -> Authorise -> Scheduled via automatic progression, except for "Site inspection only" which transitions directly from New -> Scheduled. | Explicit | Disputed (Alternative paths in WIP process map) | SRC-MAP-01 |
| **REQ-LIF-02** | For a CR in Implement state, the Planned Start Date shall be locked; only Planned End Date may be amended, subject to conflict checking. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-03** | If Current Time > Planned End Date and CR status is Scheduled, the system shall close the CR as No Show and cancel the linked site access request. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-04** | If Current Time > Planned End Date and CR status is Implement with no Actual End Time recorded, the system shall set Actual End Time to Planned End Time, create a NOCC closure task, transition the CR to Review, and close the CR after the NOCC closure task is completed. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-05** | First site visit shall trigger the transition of the CR to Implement for changes requiring site attendance. | Explicit | Target | SRC-PPT-01 |
| **REQ-LIF-06** | Final site visit shall trigger the creation of a post-implementation task for NOCC and populate Actual End Date. | Explicit | Target | SRC-PPT-01 |
| **REQ-ACC-01** | If site access is required, the request shall contain at least one Work Type block. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-02** | Visitors selected for a Work Type must possess the qualification for that Work Type. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-03** | The system shall enforce minimum crew requirements for Work Types that possess a minimum crew rule. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-01** | The RFC intake form shall present Field 67 requesting whether a site key is required. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-02** | The RFC intake form shall present Field 68 requesting key type with options: GRN09, CyberKey, or Other. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-03** | Field 69 (CyberKey serial number) display and validation logic. | Explicit | Disputed / Contradictory | SRC-DOC-01 |
| **REQ-RSK-01** | Activity rows shall contain an initial risk level, replacing a one-size-fits-all risk assessment with base risk and activity-applicable risk tables. | Explicit | Target / Confirmed | SRC-XLS-01, SRC-PPT-01 |

---

## 3. Solution-Neutral Delivery Backlog / Decomposition

*Note: User story benefits (`so that...`) are omitted unless explicitly stated in the source artifacts (SRC-PPT-01).*

### Feature 1: Appian Intake & ServiceNow Integration
- **BL-INT-001**: Direct RFC Submission and Bi-directional Linking
  - **User Story**: As a Change Agent, I can initiate and submit an RFC in Appian so that the change request is created directly in ServiceNow without swivel-chair handling, linking the Appian request number to the ServiceNow CHG number.
  - **Upstream Tracing**: REQ-INT-01, REQ-INT-02, SRC-DOC-01, SRC-PPT-01.
- **BL-INT-002**: Company-Filtered Catalogue Visibility
  - **User Story**: As a Change Agent, I can view Standard Change Catalogue entries filtered by my affiliated company, including when I am linked to multiple companies for the same activity.
  - **Upstream Tracing**: REQ-INT-03, REQ-INT-04, SRC-DOC-01.
- **BL-INT-003**: Privileged Catalogue Access
  - **User Story**: As a Change Manager or MNP Service Desk user, I can view all Standard Change Catalogue entries regardless of company affiliation.
  - **Upstream Tracing**: REQ-INT-05, SRC-DOC-01.

### Feature 2: Taxonomy & Assignment Routing
- **BL-ROU-001**: Mapped Assignment Group Routing
  - **User Story**: As the change management system, when an activity is selected that has a configured default assignment group, I allocate the CR to that mapped assignment group.
  - **Upstream Tracing**: REQ-ROU-01, SRC-XLS-01, SRC-MAP-01.
- **BL-ROU-002**: Unmapped Fallback Routing
  - **User Story**: As the change management system, when an activity is selected that has no configured assignment group mapping, I allocate the CR through the PSN Helpdesk.
  - **Upstream Tracing**: REQ-ROU-02, SRC-MAP-01.

### Feature 3: Approval Governance
- **BL-APP-001**: Tiered Approval Enforcement
  - **User Story**: As the change management system, I route changes based on Change Type: Standard changes skip manual approval, Minor changes route to Change Manager, Significant changes route to CAB, and Major changes route to CAB and TAEC.
  - **Upstream Tracing**: REQ-APP-01, REQ-APP-02, REQ-APP-03, REQ-APP-04, SRC-DOC-01, SRC-XLS-01.

### Feature 4: Site Access & Key Management Intake
- **BL-ACC-001**: Mandatory Work Type Structure
  - **User Story**: As a Change Agent, when site access is marked as required, I must add at least one Work Type block.
  - **Upstream Tracing**: REQ-ACC-01, SRC-DOC-01.
- **BL-ACC-002**: Visitor Qualification & Crew Minimum Rules
  - **User Story**: As a Change Agent, I can only select visitors who are qualified for the selected Work Type, and I must satisfy minimum crew requirements where configured for that Work Type.
  - **Upstream Tracing**: REQ-ACC-02, REQ-ACC-03, SRC-DOC-01.
- **BL-ACC-003**: Key Requirement & Type Capture
  - **User Story**: As a Change Agent, I can specify whether a site key is required (Field 67) and select the key type (Field 68: GRN09, CyberKey, or Other).
  - **Upstream Tracing**: REQ-KEY-01, REQ-KEY-02, SRC-DOC-01.

### Feature 5: Automated Change Lifecycle Handling
- **BL-LIF-001**: Implementation Date Lock & Amendment Constraints
  - **User Story**: As a Change Agent, when a CR is in Implement state, the Planned Start Date is locked and I can only amend the Planned End Date subject to conflict checking.
  - **Upstream Tracing**: REQ-LIF-02, SRC-DOC-01.
- **BL-LIF-002**: Automated No Show Cancellation
  - **User Story**: As the change management system, when Current Time > Planned End Date and the CR is in Scheduled status, I close the CR as No Show and cancel the linked site access request.
  - **Upstream Tracing**: REQ-LIF-03, SRC-DOC-01.
- **BL-LIF-003**: Automated Implement Review Transition & NOCC Closure Task
  - **User Story**: As the change management system, when Current Time > Planned End Date and the CR is in Implement status with no Actual End Time recorded, I set Actual End Time to Planned End Time, create a NOCC closure task, transition the CR to Review, and close the CR once the NOCC task is completed.
  - **Upstream Tracing**: REQ-LIF-04, SRC-DOC-01.

---

## 4. Acceptance Criteria

Acceptance criteria are strictly limited to confirmed, testable behaviours established by the source evidence. Blocked, disputed, and unknown areas are isolated.

### BL-INT-001: Direct RFC Submission and Bi-directional Linking
- **AC-INT-001-01 (Confirmed)**:
  - **Given** an RFC form is completed in Appian,
  - **When** the Change Agent submits the RFC,
  - **Then** a ServiceNow Change Request is created directly, and the Appian request number is linked to the ServiceNow CHG number.

### BL-INT-002: Company-Filtered Catalogue Visibility
- **AC-INT-002-01 (Confirmed)**:
  - **Given** a Change Agent logged into Appian who is affiliated with a specific company,
  - **When** the Change Agent accesses the Standard Change Catalogue,
  - **Then** the catalogue displays entries filtered by that affiliated company.
- **AC-INT-002-02 (Confirmed)**:
  - **Given** a Change Agent who is linked to more than one company for the same activity,
  - **When** the Change Agent accesses the Standard Change Catalogue,
  - **Then** entries for all of the Change Agent's linked companies for that activity are available.

### BL-INT-003: Privileged Catalogue Access
- **AC-INT-003-01 (Confirmed)**:
  - **Given** a user with the Change Manager role or MNP Service Desk role,
  - **When** viewing the Standard Change Catalogue,
  - **Then** all Standard Change Catalogue entries are displayed regardless of company affiliation.

### BL-ROU-001 & BL-ROU-002: Assignment Group Routing
- **AC-ROU-001-01 (Confirmed)**:
  - **Given** an activity row selected with an assignment group mapping configured in the catalogue,
  - **When** the Change Request is created,
  - **Then** the CR assignment group is set to that mapped default assignment group.
- **AC-ROU-002-01 (Confirmed)**:
  - **Given** an activity row selected with no assignment group mapping in the catalogue,
  - **When** the Change Request is created,
  - **Then** the CR is allocated through the PSN Helpdesk.

### BL-APP-001: Tiered Approval Enforcement
- **AC-APP-001-01 (Confirmed)**:
  - **Given** a Change Request classified as Standard Change,
  - **When** the CR is submitted,
  - **Then** manual approval is skipped.
- **AC-APP-001-02 (Confirmed)**:
  - **Given** a Change Request classified as Minor,
  - **When** the CR progresses to approval,
  - **Then** Change Manager approval is required.
- **AC-APP-001-03 (Confirmed)**:
  - **Given** a Change Request classified as Significant,
  - **When** the CR progresses to approval,
  - **Then** CAB approval is required.
- **AC-APP-001-04 (Confirmed)**:
  - **Given** a Change Request classified as Major,
  - **When** the CR progresses to approval,
  - **Then** both CAB approval and TAEC approval are required.

### BL-ACC-001, BL-ACC-002 & BL-ACC-003: Site Access & Keys
- **AC-ACC-001-01 (Confirmed)**:
  - **Given** an RFC where site access is indicated as required,
  - **When** the request is validated,
  - **Then** at least one Work Type block must be present.
- **AC-ACC-002-01 (Confirmed)**:
  - **Given** a Work Type block added to a site access request,
  - **When** visitors are selected for that Work Type,
  - **Then** only visitors qualified for that Work Type can be selected.
- **AC-ACC-002-02 (Confirmed)**:
  - **Given** a Work Type that has a configured minimum crew requirement,
  - **When** visitors are assigned to that Work Type,
  - **Then** the minimum crew requirement must be met.
- **AC-ACC-003-01 (Confirmed)**:
  - **Given** the RFC intake form,
  - **When** viewing site key fields,
  - **Then** Field 67 captures whether a site key is required, and Field 68 captures key type with options GRN09, CyberKey, or Other.

### BL-LIF-001, BL-LIF-002 & BL-LIF-003: Change Lifecycle Automations
- **AC-LIF-001-01 (Confirmed)**:
  - **Given** a Change Request in Implement state,
  - **When** an amendment is attempted,
  - **Then** the Planned Start Date is locked, and only Planned End Date may be amended, subject to conflict checking.
- **AC-LIF-002-01 (Confirmed)**:
  - **Given** a Change Request in Scheduled state and a linked site access request,
  - **When** Current Time > Planned End Date,
  - **Then** the CR is closed as No Show and the linked site access request is cancelled.
- **AC-LIF-003-01 (Confirmed)**:
  - **Given** a Change Request in Implement state with no Actual End Time recorded,
  - **When** Current Time > Planned End Date,
  - **Then** Actual End Time is set to Planned End Time, a NOCC closure task is created, the CR transitions to Review, and the CR closes after the NOCC closure task is completed.

---

## 5. Requirements Traceability Matrix (RTM)

| Source ID | Requirement ID | Delivery Backlog ID | Acceptance Criteria ID / Handling Status | Status |
| :--- | :--- | :--- | :--- | :--- |
| SRC-DOC-01, SRC-PPT-01 | REQ-INT-01 | BL-INT-001 | AC-INT-001-01 | Confirmed / Ready |
| SRC-DOC-01, SRC-PPT-01 | REQ-INT-02 | BL-INT-001 | AC-INT-001-01 | Confirmed / Ready |
| SRC-DOC-01 | REQ-INT-03 | BL-INT-002 | AC-INT-002-01 | Confirmed / Ready |
| SRC-DOC-01 | REQ-INT-04 | BL-INT-002 | AC-INT-002-02 | Confirmed / Ready |
| SRC-DOC-01 | REQ-INT-05 | BL-INT-003 | AC-INT-003-01 | Confirmed / Ready |
| SRC-DOC-01, SRC-XLS-01 | REQ-TAX-01 | Blocked (DI-01) | Blocked from AC elaboration (Taxonomy conflict) | Disputed |
| SRC-XLS-01, SRC-MAP-01 | REQ-ROU-01 | BL-ROU-001 | AC-ROU-001-01 | Confirmed / Ready |
| SRC-MAP-01 | REQ-ROU-02 | BL-ROU-002 | AC-ROU-002-01 | Confirmed / Ready |
| SRC-DOC-01, SRC-XLS-01 | REQ-DOC-01 | Blocked (DI-02) | Blocked from AC elaboration (Mandatory vs conditional MOP/SWMS) | Disputed |
| SRC-DOC-01, SRC-XLS-01 | REQ-DOC-02 | Blocked (DI-02) | Blocked from AC elaboration (Activity-type vs flag Release Notes) | Disputed |
| SRC-DOC-01, SRC-XLS-01 | REQ-DAT-01 | Blocked (DI-03) | Blocked from AC elaboration (Global formulas vs catalogue days) | Disputed |
| SRC-DOC-01 | REQ-APP-01 | BL-APP-001 | AC-APP-001-01 | Confirmed / Ready |
| SRC-XLS-01 | REQ-APP-02 | BL-APP-001 | AC-APP-001-02 | Confirmed / Ready |
| SRC-XLS-01 | REQ-APP-03 | BL-APP-001 | AC-APP-001-03 | Confirmed / Ready |
| SRC-XLS-01 | REQ-APP-04 | BL-APP-001 | AC-APP-001-04 | Confirmed / Ready |
| SRC-MAP-01 | REQ-LIF-01 | Blocked (DI-04) | Blocked from AC elaboration (Draft map progression contradiction) | Disputed |
| SRC-DOC-01 | REQ-LIF-02 | BL-LIF-001 | AC-LIF-001-01 | Confirmed / Ready |
| SRC-DOC-01 | REQ-LIF-03 | BL-LIF-002 | AC-LIF-002-01 | Confirmed / Ready |
| SRC-DOC-01 | REQ-LIF-04 | BL-LIF-003 | AC-LIF-003-01 | Confirmed / Ready |
| SRC-PPT-01 | REQ-LIF-05 | Blocked (DI-05) | Blocked from AC elaboration (Target state intent lacking operational rules) | Target |
| SRC-PPT-01 | REQ-LIF-06 | Blocked (DI-05) | Blocked from AC elaboration (Target state intent lacking operational rules) | Target |
| SRC-DOC-01 | REQ-ACC-01 | BL-ACC-001 | AC-ACC-001-01 | Confirmed / Ready |
| SRC-DOC-01 | REQ-ACC-02 | BL-ACC-002 | AC-ACC-002-01 | Confirmed / Ready |
| SRC-DOC-01 | REQ-ACC-03 | BL-ACC-002 | AC-ACC-002-02 | Confirmed / Ready |
| SRC-DOC-01 | REQ-KEY-01 | BL-ACC-003 | AC-ACC-003-01 | Confirmed / Ready |
| SRC-DOC-01 | REQ-KEY-02 | BL-ACC-003 | AC-ACC-003-01 | Confirmed / Ready |
| SRC-DOC-01 | REQ-KEY-03 | Blocked (DI-06) | Blocked from AC elaboration (Directly self-contradictory validation text) | Disputed / Contradictory |
| SRC-XLS-01, SRC-PPT-01 | REQ-RSK-01 | Blocked (DI-07) | Blocked from AC elaboration (Base risk level present; risk tables not supplied) | Target |

---

## 6. Source-Created Contradictions, Ambiguities, and Unresolved Decisions

The supplied sources establish the following discrete contradictions, ambiguities, and unresolved dimensions:

### Decision Item 01 (DI-01): Taxonomy Tier Alignment Contradiction
- **Sourced Conflict**: SRC-DOC-01 specifies a four-tier activity hierarchy named: *Change Category*, *Activity Category*, *Activity Subcategory*, and *Service L2*. In contrast, SRC-XLS-01 names the four tiers: `u_service_category`, `u_service_subcategory`, `u_service_l1`, and `u_service_l2`.
- **Precedence Rule**: None supplied in the evidence pack.
- **Required Outcome**: Unknown / Not established from supplied evidence.

### Decision Item 02 (DI-02): Supporting Document Attachment Rule Conflict
- **Sourced Conflict**: 
  - *MOP & SWMS*: SRC-DOC-01 mandates that MOP and SWMS uploads are universally mandatory on the RFC intake form. SRC-XLS-01 contains per-activity boolean configuration flags (`MOP Required?` and `SWMS Required?`), with specific examples setting MOP to `false` (e.g., Air Conditioning Inspection, Windows Patching) and SWMS to `false` (e.g., Windows Patching, Motorola Upgrade).
  - *Release Notes*: SRC-DOC-01 states Vendor Release Notes are required for "Software Update or Software Upgrade activities". SRC-XLS-01 governs this via an activity-specific boolean flag `Release Notes Required?`.
- **Precedence Rule**: None supplied in the evidence pack.
- **Required Outcome**: Unknown / Not established from supplied evidence.

### Decision Item 03 (DI-03): Lead-Time Calculation Formula Contradiction
- **Sourced Conflict**: SRC-DOC-01 defines fixed global lead times:
  - Standard: 3 business days processing + 1 day (NSA) / 14 days (SA).
  - Minor: 5 business days processing + 1 day (NSA).
  - Significant: 10 business days after next CAB + 1 day (NSA) / 14 days (SA).
  - Major: 10 business days after next CAB + 14 days (NSA) / 1 month (SA).
  SRC-XLS-01 provides conflicting activity-specific calculations:
  - Air Conditioning (Minor NSA): 6 days (matches 5+1).
  - Windows Patching (Standard NSA): 4 days (matches 3+1).
  - Motorola Upgrade (Significant): `25 + number of days to next CAB after submission` (conflicts with DOC-01's 10 days post-CAB + 1/14 days).
  - CCEP New Site (Major): `54 + number of days to next CAB after submission` (conflicts with DOC-01's 10 days post-CAB + 14 days/1 month).
- **Precedence Rule**: None supplied in the evidence pack.
- **Required Outcome**: Unknown / Not established from supplied evidence.

### Decision Item 04 (DI-04): Standard Change Lifecycle State Progression Contradiction
- **Sourced Conflict**: In SRC-MAP-01, the primary flow (v1/v2) shows Standard Changes moving automatically through: `New` -> `Assess` -> `Authorise` -> `Scheduled`. However, an explicit annotation on the same map states: "Site inspection only" goes directly from `New` -> `Scheduled`.
- **Precedence Rule**: Map is marked WIP/draft; precedence between paths is unstated.
- **Required Outcome**: Unknown / Not established from supplied evidence.

### Decision Item 05 (DI-05): Site Visit Integration Lifecycle Triggers vs Time-Based Automations
- **Sourced Condition**: SRC-PPT-01 states that the "first site visit" is intended to trigger the move to `Implement`, and the "final site visit" is intended to create a post-implementation task for NOCC and populate `Actual End Date`. SRC-DOC-01 defines automated fallback rules based on `Current Time > Planned End Date`.
- **Unresolved Dimension**: The operational mechanics connecting physical/recorded site visits to the change states, and how they reconcile if visits do not occur before `Planned End Date`, are not defined.
- **Required Outcome**: Unknown / Not established from supplied evidence.

### Decision Item 06 (DI-06): Field 69 (CyberKey Serial Number) Validation Text Self-Contradiction
- **Sourced Contradiction**: In SRC-DOC-01, the validation note for Field 69 explicitly reads:
  > *"Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68."*
  This is internally self-contradictory ("Yes is selected for Question 67 is No").
- **Required Outcome**: Unknown / Not established from supplied evidence.

### Decision Item 07 (DI-07): Risk Assessment Framework Tables
- **Sourced Condition**: SRC-PPT-01 specifies that the target state replaces a one-size-fits-all risk assessment with "improved base risk and more applicable risk-assessment tables", and SRC-XLS-01 provides an "initial risk level" per activity row.
- **Unresolved Dimension**: The structure, rules, and scoring of the "risk-assessment tables" are not supplied.
- **Required Outcome**: Unknown / Not established from supplied evidence.

### Decision Item 08 (DI-08): Bad Change Practice / Poor Performance Flag (MAP Annotation 1)
- **Sourced Condition**: SRC-MAP-01 explicit annotation: *"For user/org that has been flagged for poor performance or bad change practice. Can they proceed with change creation."*
- **Required Outcome**: Unknown / Not established from supplied evidence.

### Decision Item 09 (DI-09): Post Site Visit Tasks Quota and SLAs (MAP Annotation 2)
- **Sourced Condition**: SRC-MAP-01 explicit annotation: *"Post site visit tasks – Quota? 10% action – 90% Auto close? SLAs to be defined."*
- **Required Outcome**: Unknown / Not established from supplied evidence.

### Decision Item 10 (DI-10): Approval Triggering Platform for Change Tasks (MAP Annotation 3)
- **Sourced Condition**: SRC-MAP-01 explicit annotation: *"Question – SNOW, Appian or other? Change task trigger a change approval."*
- **Required Outcome**: Unknown / Not established from supplied evidence.

### Decision Item 11 (DI-11): Minor Change State Routing / "Amend" State (MAP Annotation 4)
- **Sourced Condition**: SRC-MAP-01 explicit annotation: *"If minor change to change (such as date changes) move to Authorize (Or new state… such as 'Amend'.) TBD."*
- **Required Outcome**: Unknown / Not established from supplied evidence.

---

## 7. Completeness / Readiness Assessment

### Summary Assessment
- **Delivery Decomposition Readiness**: **Partially Ready**
  - Confirmed core intake mechanisms, key capture fields, visitor qualification rules, approval levels, and time-based automated cancellation/closure rules are sufficiently defined to proceed into delivery.
  - Document attachment validation, lead-time date calculation engines, CyberKey serial display logic, and draft lifecycle paths cannot be coded or tested without selecting a precedence rule or resolving contradictions.

### Breakdown of Status

| Domain | Implementation-Ready Areas (Proceed) | Source-Created Unresolved Areas (Blocked / Requires Clarification) |
| :--- | :--- | :--- |
| **Intake & Portal** | - Form initiation in Appian (REQ-INT-01).<br>- Direct ServiceNow CR creation & ID linking (REQ-INT-02).<br>- Company filtering for Standard Changes (REQ-INT-03, REQ-INT-04).<br>- Change Manager / MNP Service Desk catalogue visibility (REQ-INT-05). | - Precedence between four-tier naming conventions (REQ-TAX-01 / DI-01).<br>- Impact of poor-performance/bad-practice flags on creation (DI-08). |
| **Document Attachments** | *None* (entire document validation engine is subject to source conflict). | - Universal mandatory MOP/SWMS upload vs activity-level boolean configuration (REQ-DOC-01 / DI-02).<br>- Vendor Release Notes activity-type rule vs boolean flag (REQ-DOC-02 / DI-02). |
| **Scheduling & Lead Times** | *None* (lead-time calculation engine is subject to source conflict). | - Fixed formula calculation tiers vs explicit catalogue lead-time values (REQ-DAT-01 / DI-03). |
| **Approvals & Governance** | - Skipping manual approval for Standard Changes (REQ-APP-01).<br>- Approval authority tiers: Minor -> Change Manager; Significant -> CAB; Major -> CAB + TAEC (REQ-APP-02, REQ-APP-03, REQ-APP-04). | - Platform ownership for task-triggered approvals: SNOW, Appian, or other (DI-10). |
| **Routing** | - Mapped default assignment group application (REQ-ROU-01).<br>- Fallback allocation via PSN Helpdesk when unmapped (REQ-ROU-02). | *None.* |
| **Site Access & Keys** | - Mandatory Work Type block when site access required (REQ-ACC-01).<br>- Visitor Work Type qualification check (REQ-ACC-02).<br>- Minimum crew rule enforcement (REQ-ACC-03).<br>- Capture of Field 67 (key required) and Field 68 (key type) (REQ-KEY-01, REQ-KEY-02). | - Display and validation logic for Field 69 CyberKey serial number due to syntax self-contradiction (REQ-KEY-03 / DI-06). |
| **Change Lifecycle** | - Locked Planned Start Date in Implement state (REQ-LIF-02).<br>- Amend Planned End Date subject to conflict check (REQ-LIF-02).<br>- No Show closure & access cancellation when Current Time > Planned End Date in Scheduled (REQ-LIF-03).<br>- Auto-set Actual End Time, NOCC task creation, Review transition, and closure when Current Time > Planned End Date in Implement (REQ-LIF-04). | - Progression path for Standard Changes: `New` -> `Assess` -> `Authorise` -> `Scheduled` vs direct `New` -> `Scheduled` for site inspection (REQ-LIF-01 / DI-04).<br>- State handling for minor amendments: `Authorize` vs new `Amend` state (DI-11).<br>- Operational integration of first/final site visit triggers with lifecycle automations (REQ-LIF-05, REQ-LIF-06 / DI-05).<br>- Post site visit task sampling quota (10% action / 90% auto-close) and SLAs (DI-09). |
| **Risk Assessment** | - Storage of initial risk level from activity catalogue (REQ-RSK-01). | - Applicable risk-assessment tables and scoring structure (REQ-RSK-01 / DI-07). |

---

## 8. Open Questions (Source-Linked Only)

Every open question below maps strictly one-for-one to a sourced contradiction, ambiguity, or unresolved source note:

1. **Taxonomy Hierarchy Naming (DI-01)**: Which taxonomy naming convention takes precedence: the specification's `Change Category` / `Activity Category` / `Activity Subcategory` / `Service L2` (SRC-DOC-01) or the catalogue's `u_service_category` / `u_service_subcategory` / `u_service_l1` / `u_service_l2` (SRC-XLS-01)?
2. **Supporting Document Precedence (DI-02)**: Does the universal requirement for MOP and SWMS uploads on the RFC form (SRC-DOC-01) take precedence, or do the activity-specific boolean flags `MOP Required?` and `SWMS Required?` (SRC-XLS-01) govern attachment mandatory status?
3. **Release Notes Attachment Rule (DI-02)**: Are Vendor Release Notes mandated strictly by activity classification ("Software Update" or "Software Upgrade" per SRC-DOC-01) or by the activity catalogue flag `Release Notes Required?` (SRC-XLS-01)?
4. **Lead-Time Calculation Precedence (DI-03)**: Which lead-time calculation rules take precedence: the global formula tiers based on processing days, CAB schedule, and NSA/SA status (SRC-DOC-01), or the individual activity lead-time values in the catalogue (SRC-XLS-01)?
5. **Standard Change State Path (DI-04)**: For Standard Changes, does lifecycle progression follow `New` -> `Assess` -> `Authorise` -> `Scheduled`, or do site-inspection changes transition directly from `New` -> `Scheduled` (SRC-MAP-01)?
6. **Site Visit Lifecycle Triggers (DI-05)**: What specific system event or mechanism registers a "first site visit" to trigger the `Implement` state and a "final site visit" to populate `Actual End Date` and create the NOCC task (SRC-PPT-01), and how does this interact with the Planned End Date expiration automations (SRC-DOC-01)?
7. **CyberKey Serial Field Display Logic (DI-06)**: What are the exact display and mandatory conditions for Field 69 (CyberKey serial number), resolving the contradictory note *"Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68"* (SRC-DOC-01)?
8. **Risk Assessment Tables (DI-07)**: What are the defined risk-assessment tables, scoring parameters, and evaluation rules referenced in SRC-PPT-01 to complement the initial risk level from SRC-XLS-01?
9. **Creation Ineligibility for Poor Performance / Bad Change Practice (DI-08)**: Can a user or organization flagged for poor performance or bad change practice proceed with change creation (SRC-MAP-01 Annotation 1)?
10. **Post Site Visit Task Quotas and SLAs (DI-09)**: What are the defined SLAs, and what is the required distribution between manual action and automated closure (e.g., 10% action / 90% auto close) for post site visit tasks (SRC-MAP-01 Annotation 2)?
11. **Task-Triggered Approval System (DI-10)**: Does a change task trigger a change approval within ServiceNow, Appian, or another platform (SRC-MAP-01 Annotation 3)?
12. **Change Amendment State Routing (DI-11)**: When a minor change (such as a date change) is made to an existing change, does it transition to `Authorize` or to a new dedicated state such as `Amend` (SRC-MAP-01 Annotation 4)?
