# BA Benchmark Raw Result

> Raw model output. Not an evaluator score.

## Run metadata

- Benchmark: `Benchmark 042 — Multi-Source BA Model Comparison`
- Mode: `skill`
- Provider: `gemini`
- Model: `gemini-3.8-flash`
- Status: `success`
- Started: `2026-09-09T08:42:40Z`
- Ended: `2026-09-09T08:43:15Z`
- Temperature: `0.0`
- Max output tokens: `16384`
- Input SHA-256: `1432330128630c368efc83ea65458ebec990d731cc2dd0b11d77148c13b21af3`
- Prompt SHA-256: `327f4aeb1a6fd16d585800b3706194285a459265cd69d02950e95b5d07b717e1`
- Skill: `/volume1/docker/librechat-ba-lab/custom/ba-agent/skills/prepare-implementation-ready-requirements/SKILL.md`
- Skill version: `0.2.4`
- Skill SHA-256: `a38fda060b2ccaec03fe137dbde1049985dd6971a7dbc2a41ec81d762a037c99`
- Finish reason: `STOP`
- Usage metadata: `{"candidatesTokenCount": 8382, "promptTokenCount": 5986, "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 5986}], "serviceTier": "standard", "thoughtsTokenCount": 1825, "totalTokenCount": 16193}`

---

## Model output

# Requirements Lifecycle Package: Integrated Change Intake and Site Access

---

## 1. Source Register

| Source ID | Document / Artifact Name | Format / Type | Evidentiary Role & Scope |
| :--- | :--- | :--- | :--- |
| **SRC-DOC-01** | Functional Enhancement Specification | Word Document | Baseline functional specification covering Appian RFC intake, ServiceNow integration linking, Standard Change catalogue company filtering, four-tier activity taxonomy, date selection lead times, mandatory supporting document uploads, site access work types, key requirements (Fields 67–69), and change lifecycle rules (Standard approval bypass, Implement date locking, and auto-closure rules). |
| **SRC-XLS-01** | Service and Activity Catalogue | Excel Workbook | First-class operational configuration matrix defining the four-tier taxonomy, technical field mappings (`u_service_category`, `u_service_subcategory`, `u_service_l1`, `u_service_l2`), default assignment group routing, operational booleans (`Standard Change option available?`, `SAR option available?`, `MOP Required?`, `SWMS Required?`, `Release Notes Required?`), Change Type assignment, permitted PSN impact values (NSA, SA, RA), initial risk level, and change approval matrix. |
| **SRC-MAP-01** | Post-ServiceNow Review Process Map | PDF (Marked WIP / Draft) | Operational process map depicting Standard Change lifecycle state transitions (New → Assess → Authorise → Scheduled vs direct New → Scheduled for site inspection), assignment group fallback routing via PSN Helpdesk, and four explicit unresolved annotations. |
| **SRC-PPT-01** | Internal Change Transformation Presentation | PowerPoint Presentation | Target-state operational objectives, identified pain points (Service Desk swivel-chair handling, one-size-fits-all risk assessment), and candidate target-state site visit event triggers. |

---

## 2. Requirements Register

*Evidence Classes:* Explicit, Inferred, Proposed, Assumption, Disputed, Unknown.  
*Requirement Statuses:* Confirmed, Candidate, Target, Disputed, Deferred, Unknown.

### 2.1 Intake and Catalogue

| Req ID | Requirement Statement | Evidence Class | Status | Source Trace |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-INT-01** | The RFC form shall be initiated in Appian. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-INT-02** | A submitted RFC shall create a ServiceNow Change Request and link the Appian request number to the ServiceNow CHG number. | Explicit | Confirmed | SRC-DOC-01, SRC-PPT-01 |
| **REQ-INT-03** | The Standard Change Catalogue shall be filtered by the Change Agent's affiliated company. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-INT-04** | Change Agents may be associated with more than one company for the same activity.<br>*Set-handling outcome for multiple affiliated companies:* Unknown / Not established from supplied evidence. | Explicit | Unknown | SRC-DOC-01 |
| **REQ-INT-05** | Users with Change Manager and MNP Service Desk roles shall have access to view all Standard Change Catalogue entries. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-INT-06** | Activity selection shall use a four-tier taxonomy mapping business labels (Change Category, Activity Category, Activity Subcategory, Service L2) to catalogue fields (`u_service_category`, `u_service_subcategory`, `u_service_l1`, `u_service_l2`). | Explicit | Confirmed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-INT-07** | Activity selection shall govern default assignment group routing, availability of Standard Change (`Standard Change option available?`), availability of SAR (`SAR option available?`), permitted PSN impact values (NSA / SA / RA), and initial risk level based on the configuration matrix. | Explicit | Confirmed | SRC-XLS-01 |

### 2.2 Lead Time and Scheduling

| Req ID | Requirement Statement | Evidence Class | Status | Source Trace |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-SCH-01** | Date selection lead time shall be calculated based on Change Type, CAB schedule, and Service Affecting status:<ul><li>Standard: 3 business days processing + 1 day (NSA) / 14 days (SA).</li><li>Minor: 5 business days processing + 1 day (NSA).</li><li>Significant (SRC-DOC-01): 10 business days after next CAB + 1 day (NSA) / 14 days (SA).</li><li>Significant (SRC-XLS-01): 25 days + number of days to next CAB after submission.</li><li>Major (SRC-DOC-01): 10 business days after next CAB + 14 days (NSA) / 1 month (SA).</li><li>Major (SRC-XLS-01): 54 days + number of days to next CAB after submission.</li></ul> | Disputed | Disputed | SRC-DOC-01, SRC-XLS-01 |

### 2.3 Supporting Documentation

| Req ID | Requirement Statement | Evidence Class | Status | Source Trace |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-DOC-01** | Document upload requirements shall apply as follows:<ul><li>SRC-DOC-01: MOP upload is mandatory on RFC form; SWMS upload is mandatory on RFC form; Vendor Release Notes are required for Software Update or Software Upgrade activities.</li><li>SRC-XLS-01: MOP, SWMS, and Release Notes requirements are independently governed per catalogue activity via boolean flags (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`).</li></ul> | Disputed | Disputed | SRC-DOC-01, SRC-XLS-01 |

### 2.4 Site Access and Keys

| Req ID | Requirement Statement | Evidence Class | Status | Source Trace |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-ACC-01** | If site access is required, at least one Work Type block shall be required. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-02** | Visitors selected for a Work Type must be qualified for that Work Type. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-03** | Work Types with minimum crew requirements shall enforce that minimum crew size.<br>*Specific crew size numbers per Work Type:* Unknown / Not established from supplied evidence. | Explicit | Partially Ready | SRC-DOC-01 |
| **REQ-KEY-01** | The RFC form shall capture whether a site key is required (Field 67). | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-02** | The RFC form shall capture key type as GRN09, CyberKey, or Other (Field 68). | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-03** | Display condition and validation for Field 69 (CyberKey serial number):<ul><li>Condition: CyberKey is selected for Question 68.</li><li>Condition for Question 67: Sourced text states "Only appears when Yes is selected for Question 67 is No". True condition is Unknown / Disputed.</li></ul> | Disputed | Disputed | SRC-DOC-01 |

### 2.5 Change Lifecycle and Approvals

| Req ID | Requirement Statement | Evidence Class | Status | Source Trace |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-LIF-01** | Standard Changes shall skip manual approval. | Explicit | Confirmed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-LIF-02** | Standard Change progression state model:<ul><li>SRC-MAP-01 (v1/v2): Progresses New → Assess → Authorise → Scheduled automatically.</li><li>SRC-MAP-01 (Site inspection only annotation): Progresses directly New → Scheduled.</li></ul> | Disputed | Disputed | SRC-DOC-01, SRC-MAP-01 |
| **REQ-LIF-03** | Approvals for non-Standard change types shall follow the approval matrix:<ul><li>Minor: Change Manager approval.</li><li>Significant: CAB approval.</li><li>Major: CAB + TAEC approval.</li></ul> | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-LIF-04** | If an assignment group mapping exists in the activity matrix, the change shall be routed to the mapped group; if no mapping exists, it shall be allocated through PSN Helpdesk. | Explicit | Confirmed | SRC-XLS-01, SRC-MAP-01 |
| **REQ-LIF-05** | For a Change Request in Implement state, Planned Start Date shall be locked; only Planned End Date may be amended, subject to conflict checking. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-06** | If Current Time > Planned End Date and the Change Request is in Scheduled state, the change shall be closed as No Show and the linked site access request shall be cancelled. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-07** | If Current Time > Planned End Date and the Change Request is in Implement state with no Actual End Time, Actual End Time shall be set to Planned End Time, a NOCC closure task shall be created, the Change Request shall move to Review state, and close after the task is completed. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-08** | First site visit triggers move to Implement for changes needing site attendance. | Proposed | Target | SRC-PPT-01 |
| **REQ-LIF-09** | Final site visit creates a post-implementation task for NOCC and populates Actual End Date. | Proposed | Target | SRC-PPT-01 |

---

## 3. Delivery Backlog / Decomposition

### BKI-01: Appian RFC Submission and ServiceNow Record Linking
- **Type:** Backlog Item / User Story
- **Upstream Trace:** REQ-INT-01, REQ-INT-02
- **Description:** As a Change Agent submitting an RFC in Appian, the submitted RFC creates a ServiceNow Change Request and establishes a bidirectional link between the Appian request number and the ServiceNow CHG number.
- **Delivery Readiness:** Ready

### BKI-02: Role-Based Standard Change Catalogue Access
- **Type:** Backlog Item / User Story
- **Upstream Trace:** REQ-INT-05
- **Description:** As a user with the Change Manager or MNP Service Desk role, full visibility across all Standard Change Catalogue entries is provided regardless of company affiliation.
- **Delivery Readiness:** Ready

### BKI-03: Four-Tier Taxonomy and Catalogue Operational Control Configuration
- **Type:** Backlog Item / User Story
- **Upstream Trace:** REQ-INT-06, REQ-INT-07
- **Description:** Operationalise the four-tier taxonomy selection linking Change Category (`u_service_category`), Activity Category (`u_service_subcategory`), Activity Subcategory (`u_service_l1`), and Service L2 (`u_service_l2`) to populate default assignment group, Standard Change availability boolean, SAR availability boolean, permitted PSN impact values (NSA / SA / RA), and initial risk level.
- **Delivery Readiness:** Ready

### BKI-04: Assignment Group Routing and Fallback
- **Type:** Backlog Item / User Story
- **Upstream Trace:** REQ-LIF-04
- **Description:** Route Change Requests to the mapped default assignment group from the catalogue row, or route to PSN Helpdesk when no assignment group mapping exists.
- **Delivery Readiness:** Ready

### BKI-05: Non-Standard Change Approval Routing
- **Type:** Backlog Item / User Story
- **Upstream Trace:** REQ-LIF-03
- **Description:** Route Change Requests requiring approval according to Change Type: Minor to Change Manager; Significant to CAB; Major to CAB and TAEC.
- **Delivery Readiness:** Ready

### BKI-06: Site Access Work Type and Visitor Qualification Validation
- **Type:** Backlog Item / User Story
- **Upstream Trace:** REQ-ACC-01, REQ-ACC-02
- **Description:** When site access is selected on an RFC, enforce selection of at least one Work Type block and enforce that all selected visitors are qualified for that Work Type.
- **Delivery Readiness:** Ready

### BKI-07: Key Requirement Data Capture (Fields 67 & 68)
- **Type:** Backlog Item / User Story
- **Upstream Trace:** REQ-KEY-01, REQ-KEY-02
- **Description:** Capture whether a site key is required (Field 67) and the key type selection among GRN09, CyberKey, or Other (Field 68).
- **Delivery Readiness:** Ready

### BKI-08: Schedule Field Immutability in Implement State
- **Type:** Backlog Item / User Story
- **Upstream Trace:** REQ-LIF-05
- **Description:** When a Change Request is in Implement state, lock the Planned Start Date from modification, and permit amendments to Planned End Date subject to conflict checking.
- **Delivery Readiness:** Ready

### BKI-09: Overdue Scheduled Change Auto-Closure (No Show)
- **Type:** Backlog Item / User Story
- **Upstream Trace:** REQ-LIF-06
- **Description:** When Current Time exceeds Planned End Date for a Change Request in Scheduled state, update change status to closed with reason No Show and cancel the associated site access request.
- **Delivery Readiness:** Ready

### BKI-10: Overdue Implement Change Review Progression and NOCC Task Creation
- **Type:** Backlog Item / User Story
- **Upstream Trace:** REQ-LIF-07
- **Description:** When Current Time exceeds Planned End Date for a Change Request in Implement state with no Actual End Time recorded, set Actual End Time to Planned End Time, create a NOCC closure task, move the Change Request to Review state, and close the Change Request upon NOCC closure task completion.
- **Delivery Readiness:** Ready

### Backlog Items Blocked by Upstream Disputed / Unresolved Items (Preserved)

- **BKI-BLK-01 (Multi-Company Catalogue Filtering):** Filter catalogue entries for Change Agents linked to multiple companies (REQ-INT-03, REQ-INT-04). Blocked by DEC-01.
- **BKI-BLK-02 (Lead Time Rules Engine):** Automated calculation of lead times (REQ-SCH-01). Blocked by DEC-02.
- **BKI-BLK-03 (Supporting Document Mandates):** Form-level vs activity-level document upload mandates (REQ-DOC-01). Blocked by DEC-03.
- **BKI-BLK-04 (Field 69 CyberKey Visibility Rule):** Visibility condition for CyberKey serial number field (REQ-KEY-03). Blocked by DEC-04.
- **BKI-BLK-05 (Standard Change State Path):** Automatic stage progression for Standard Changes (REQ-LIF-01, REQ-LIF-02). Blocked by DEC-05.
- **BKI-BLK-06 (Work Type Crew Size Validation):** Validation of minimum crew size counts (REQ-ACC-03). Blocked by DEC-06.
- **BKI-BLK-07 (Site Visit Lifecycle Triggers):** State transition to Implement on first site visit and NOCC task/Actual End Date trigger on final site visit (REQ-LIF-08, REQ-LIF-09). Preserved as Target state; design mechanism not established.

---

## 4. Acceptance Criteria

Acceptance criteria are provided only where the source evidence establishes complete, testable preconditions, actions, and outcomes.

### BKI-01: Appian RFC Submission and ServiceNow Record Linking
- **AC-01-01 (RFC Submission Linking):**
  - **Given** an RFC form initiated in Appian,
  - **When** the RFC form is submitted,
  - **Then** a ServiceNow Change Request is created, and the Appian request number is linked to the ServiceNow CHG number.

### BKI-02: Role-Based Standard Change Catalogue Access
- **AC-02-01 (Change Manager View All):**
  - **Given** a user authenticated with the Change Manager role,
  - **When** the user accesses the Standard Change Catalogue,
  - **Then** all Standard Change Catalogue entries are viewable.
- **AC-02-02 (MNP Service Desk View All):**
  - **Given** a user authenticated with the MNP Service Desk role,
  - **When** the user accesses the Standard Change Catalogue,
  - **Then** all Standard Change Catalogue entries are viewable.

### BKI-03: Four-Tier Taxonomy and Catalogue Operational Control Configuration
- **AC-03-01 (Taxonomy Tier Selection):**
  - **Given** the activity selection interface on the RFC form,
  - **When** an activity is selected through the hierarchy of Change Category (`u_service_category`), Activity Category (`u_service_subcategory`), Activity Subcategory (`u_service_l1`), and Service L2 (`u_service_l2`),
  - **Then** the default assignment group, Standard Change availability boolean, SAR availability boolean, permitted PSN impact values (NSA / SA / RA), and initial risk level from the matching catalogue configuration row are applied to the change record.

### BKI-04: Assignment Group Routing and Fallback
- **AC-04-01 (Mapped Assignment Group Routing):**
  - **Given** an activity selection that has a configured default assignment group in the catalogue,
  - **When** assignment routing is applied,
  - **Then** the Change Request is assigned to the mapped assignment group.
- **AC-04-02 (Unmapped Fallback to PSN Helpdesk):**
  - **Given** an activity selection that has no assignment group mapping in the catalogue,
  - **When** assignment routing is applied,
  - **Then** the Change Request is allocated through PSN Helpdesk.

### BKI-05: Non-Standard Change Approval Routing
- **AC-05-01 (Minor Change Approval):**
  - **Given** a Change Request classified as Minor,
  - **When** the change is submitted for approval,
  - **Then** approval is routed to Change Manager.
- **AC-05-02 (Significant Change Approval):**
  - **Given** a Change Request classified as Significant,
  - **When** the change is submitted for approval,
  - **Then** approval is routed to CAB.
- **AC-05-03 (Major Change Approval):**
  - **Given** a Change Request classified as Major,
  - **When** the change is submitted for approval,
  - **Then** approvals are routed to CAB and TAEC.

### BKI-06: Site Access Work Type and Visitor Qualification Validation
- **AC-06-01 (Site Access Requires Work Type Block):**
  - **Given** an RFC where site access is indicated as required,
  - **When** site access details are submitted,
  - **Then** at least one Work Type block is required.
- **AC-06-02 (Visitor Qualification Verification):**
  - **Given** a Work Type block on a site access request,
  - **When** a visitor is selected for that Work Type,
  - **Then** the selected visitor must be qualified for that Work Type.

### BKI-07: Key Requirement Data Capture (Fields 67 & 68)
- **AC-07-01 (Field 67 Key Required Capture):**
  - **Given** an RFC form,
  - **When** the user reaches Field 67,
  - **Then** Field 67 captures whether a site key is required.
- **AC-07-02 (Field 68 Key Type Selection):**
  - **Given** an RFC form,
  - **When** the user reaches Field 68,
  - **Then** Field 68 presents the options GRN09, CyberKey, and Other.

### BKI-08: Schedule Field Immutability in Implement State
- **AC-08-01 (Planned Start Date Locked in Implement):**
  - **Given** a Change Request in Implement state,
  - **When** a user attempts to edit the Planned Start Date,
  - **Then** the Planned Start Date is locked and cannot be amended.
- **AC-08-02 (Planned End Date Amendment Permitted):**
  - **Given** a Change Request in Implement state,
  - **When** a user amends the Planned End Date,
  - **Then** the amendment is permitted, subject to conflict checking.

### BKI-09: Overdue Scheduled Change Auto-Closure (No Show)
- **AC-09-01 (Scheduled Change Expiration):**
  - **Given** a Change Request in Scheduled state with a linked site access request,
  - **When** Current Time > Planned End Date,
  - **Then** the Change Request is closed as No Show and the linked site access request is cancelled.

### BKI-10: Overdue Implement Change Review Progression and NOCC Task Creation
- **AC-10-01 (Implement Change Auto-Progression and NOCC Task):**
  - **Given** a Change Request in Implement state where Actual End Time is empty,
  - **When** Current Time > Planned End Date,
  - **Then** Actual End Time is set to Planned End Time, a NOCC closure task is created, and the Change Request moves to Review state.
- **AC-10-02 (Review State Closure on Task Completion):**
  - **Given** a Change Request in Review state with an associated NOCC closure task,
  - **When** the NOCC closure task is completed,
  - **Then** the Change Request is closed.

---

## 5. Requirements Traceability Matrix (RTM)

| Source ID | Requirement ID | Backlog Item ID | Acceptance Criteria ID / Status | Status |
| :--- | :--- | :--- | :--- | :--- |
| SRC-DOC-01, SRC-PPT-01 | REQ-INT-01, REQ-INT-02 | BKI-01 | AC-01-01 | Confirmed |
| SRC-DOC-01 | REQ-INT-03, REQ-INT-04 | BKI-BLK-01 | Blocked (Awaiting DEC-01 set handling rule) | Unknown |
| SRC-DOC-01 | REQ-INT-05 | BKI-02 | AC-02-01, AC-02-02 | Confirmed |
| SRC-DOC-01, SRC-XLS-01 | REQ-INT-06, REQ-INT-07 | BKI-03 | AC-03-01 | Confirmed |
| SRC-DOC-01, SRC-XLS-01 | REQ-SCH-01 | BKI-BLK-02 | Blocked (Awaiting DEC-02 lead-time reconciliation) | Disputed |
| SRC-DOC-01, SRC-XLS-01 | REQ-DOC-01 | BKI-BLK-03 | Blocked (Awaiting DEC-03 document requirement rule) | Disputed |
| SRC-DOC-01 | REQ-ACC-01, REQ-ACC-02 | BKI-06 | AC-06-01, AC-06-02 | Confirmed |
| SRC-DOC-01 | REQ-ACC-03 | BKI-BLK-06 | Partially Ready (Awaiting minimum crew numbers) | Partially Ready |
| SRC-DOC-01 | REQ-KEY-01, REQ-KEY-02 | BKI-07 | AC-07-01, AC-07-02 | Confirmed |
| SRC-DOC-01 | REQ-KEY-03 | BKI-BLK-04 | Blocked (Awaiting DEC-04 Field 67/69 condition) | Disputed |
| SRC-DOC-01, SRC-XLS-01 | REQ-LIF-01 | BKI-BLK-05 | Blocked (Manual approval skipped; lifecycle path disputed in DEC-05) | Confirmed / Disputed path |
| SRC-DOC-01, SRC-MAP-01 | REQ-LIF-02 | BKI-BLK-05 | Blocked (Awaiting DEC-05 state transition path) | Disputed |
| SRC-XLS-01 | REQ-LIF-03 | BKI-05 | AC-05-01, AC-05-02, AC-05-03 | Confirmed |
| SRC-XLS-01, SRC-MAP-01 | REQ-LIF-04 | BKI-04 | AC-04-01, AC-04-02 | Confirmed |
| SRC-DOC-01 | REQ-LIF-05 | BKI-08 | AC-08-01, AC-08-02 | Confirmed |
| SRC-DOC-01 | REQ-LIF-06 | BKI-09 | AC-09-01 | Confirmed |
| SRC-DOC-01 | REQ-LIF-07 | BKI-10 | AC-10-01, AC-10-02 | Confirmed |
| SRC-PPT-01 | REQ-LIF-08 | BKI-BLK-07 | Blocked (Preserved as Target state; mechanism not established) | Target |
| SRC-PPT-01 | REQ-LIF-09 | BKI-BLK-07 | Blocked (Preserved as Target state; mechanism not established) | Target |

---

## 6. Source-Created Contradictions, Ambiguities, and Unresolved Decisions

Every item below maps directly to an explicit conflict or unresolved condition created by the source evidence.

### 6.1 Sourced Contradictions

- **CON-01: Supporting Document Upload Mandates (SRC-DOC-01 vs SRC-XLS-01)**
  - *Conflict:* SRC-DOC-01 states that MOP and SWMS uploads are mandatory on the RFC form, and Vendor Release Notes are required for Software Update/Upgrade. Conversely, SRC-XLS-01 specifies document mandates as independent per-activity booleans (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`) where individual activities vary (e.g., Air Conditioning requires SWMS but not MOP; Windows Patching requires Release Notes but neither MOP nor SWMS).
  - *Precedence:* No rule in the source pack establishes whether the specification or the catalogue workbook governs.

- **CON-02: Lead Time Calculation Rules (SRC-DOC-01 vs SRC-XLS-01)**
  - *Conflict:* For Significant changes, SRC-DOC-01 mandates `10 business days after next CAB + 1 day (NSA) / 14 days (SA)`, whereas SRC-XLS-01 specifies `25 + number of days to next CAB after submission`. For Major changes, SRC-DOC-01 mandates `10 business days after next CAB + 14 days (NSA) / 1 month (SA)`, whereas SRC-XLS-01 specifies `54 + number of days to next CAB after submission`.
  - *Precedence:* SRC-XLS-01 explicitly notes that no rule establishes precedence between sources.

- **CON-03: Field 69 CyberKey Serial Validation Note (SRC-DOC-01)**
  - *Conflict:* The validation note for Field 69 reads: `"Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68."` The phrase `"Yes is selected for Question 67 is No"` is internally contradictory.

- **CON-04: Standard Change Lifecycle Progression (SRC-DOC-01 vs SRC-MAP-01)**
  - *Conflict:* SRC-DOC-01 and SRC-XLS-01 state Standard Changes skip manual approval. SRC-MAP-01 v1/v2 illustrates progression through `New -> Assess -> Authorise -> Scheduled` via automatic transitions, whereas an annotation on the same map indicates that for "Site inspection only", a Standard Change moves directly from `New -> Scheduled`.

### 6.2 Sourced Ambiguities and Unresolved Conditions

- **AMB-01: Multi-Company Set Handling for Standard Change Filtering (SRC-DOC-01)**
  - *Sourced Condition:* Change Agents may be linked to more than one company for the same activity, while the Standard Change Catalogue is filtered by the agent's affiliated company.
  - *Required outcome:* Unknown / Not established from supplied evidence.

- **AMB-02: Work Type Minimum Crew Values (SRC-DOC-01)**
  - *Sourced Condition:* Some Work Types have minimum crew requirements.
  - *Required outcome:* Specific minimum crew counts per Work Type are Unknown / Not established from supplied evidence.

- **AMB-03: Flagged User / Organization Submission Permission (SRC-MAP-01 Annotation 1)**
  - *Sourced Annotation:* `"For user/org that has been flagged for poor performance or bad change practice. Can they proceed with change creation."`
  - *Required outcome:* Unknown / Not established from supplied evidence.

- **AMB-04: Post Site Visit Task Quota and Auto-Close SLA (SRC-MAP-01 Annotation 2)**
  - *Sourced Annotation:* `"Post site visit tasks – Quota? 10% action – 90% Auto close? SLAs to be defined."`
  - *Required outcome:* Unknown / Not established from supplied evidence.

- **AMB-05: Change Task Trigger for Change Approval Platform (SRC-MAP-01 Annotation 3)**
  - *Sourced Annotation:* `"Question – SNOW, Appian or other? Change task trigger a change approval."`
  - *Required outcome:* Unknown / Not established from supplied evidence.

- **AMB-06: Minor Amendment / Date Change Re-Authorization State (SRC-MAP-01 Annotation 4)**
  - *Sourced Annotation:* `"If minor change to change (such as date changes) move to Authorize (Or new state… such as 'Amend'.) TBD."`
  - *Required outcome:* Unknown / Not established from supplied evidence (contrasts with SRC-DOC-01 rule permitting Planned End Date modification in Implement state under conflict checking).

- **AMB-07: Site Visit State Progression Mechanisms (SRC-PPT-01)**
  - *Sourced Target:* First site visit triggers move to Implement; final site visit triggers NOCC post-implementation task and populates Actual End Date.
  - *Required outcome:* Mechanisms for detecting site visit events and triggering record updates are Target-state concepts whose technical and operational rules are Not established from supplied evidence.

### 6.3 Source-Backed Decision Items

- **DEC-01 (Multi-Company Filtering Policy):** Define catalogue filtering outcome when a Change Agent is linked to multiple companies (e.g., union of catalogue entries, prompt to select active company context, or primary company default).
- **DEC-02 (Lead Time Precedence and Calculation):** Establish source precedence between SRC-DOC-01 formulas and SRC-XLS-01 catalogue lead times for Significant and Major changes.
- **DEC-03 (Document Upload Enforcement Rules):** Decide whether MOP, SWMS, and Release Notes uploads are universally mandatory at form submission (SRC-DOC-01) or dynamically governed by catalogue activity booleans (SRC-XLS-01).
- **DEC-04 (Field 69 CyberKey Display Logic):** Reconcile the display rule for CyberKey serial number regarding Question 67 (Key required = Yes vs Key required = No).
- **DEC-05 (Standard Change Stage Model):** Establish whether Standard Changes progress through Assess and Authorise automatically or bypass them directly to Scheduled (including site inspection exception).
- **DEC-06 (Work Type Crew Size Matrix):** Supply the numeric minimum crew requirements associated with each applicable Work Type.
- **DEC-07 (Flagged User Restriction Policy):** Determine whether users or organizations flagged for poor performance/bad change practice are permitted to create changes (SRC-MAP-01 Annotation 1).
- **DEC-08 (Post Site Visit Quota and Audit SLAs):** Define the action/auto-close quota and operational SLAs for post site visit tasks (SRC-MAP-01 Annotation 2).
- **DEC-09 (Task-Triggered Approval System Assignment):** Establish the platform and mechanism (ServiceNow, Appian, or other) for change tasks triggering change approvals (SRC-MAP-01 Annotation 3).
- **DEC-10 (Change Amendment Lifecycle State Handling):** Determine whether date amendments trigger a transition to Authorise or a new state such as Amend (SRC-MAP-01 Annotation 4).

---

## 7. Completeness and Readiness Assessment

### 7.1 Implementation-Ready Areas

The following functional areas have complete, unambiguous, and corroborated source evidence, permitting immediate implementation and verification:

1. **Intake and Request Linking (BKI-01):** RFC initiation in Appian, creation of ServiceNow Change Request, and linking Appian request number to ServiceNow CHG number.
2. **Privileged Catalogue Visibility (BKI-02):** Unrestricted Standard Change Catalogue viewing for Change Manager and MNP Service Desk roles.
3. **Four-Tier Taxonomy and Default Routing (BKI-03, BKI-04):** Four-tier cascading selection mapped to catalogue configuration fields, assignment group allocation, and fallback to PSN Helpdesk when unmapped.
4. **Non-Standard Approval Matrix (BKI-05):** Approval hierarchy for Minor (Change Manager), Significant (CAB), and Major (CAB + TAEC).
5. **Baseline Site Access Requirements (BKI-06):** Mandatory Work Type block requirement when site access is requested, and visitor qualification verification.
6. **Key Data Fields (BKI-07):** Capture of site key requirement flag (Field 67) and key type selection (Field 68: GRN09, CyberKey, Other).
7. **Schedule Immutability in Implement (BKI-08):** Locking Planned Start Date and allowing Planned End Date modification subject to conflict check while in Implement state.
8. **Automated Lifecycle Closures (BKI-09, BKI-10):**
   - Scheduled changes where Current Time > Planned End Date auto-close as No Show and cancel linked site access.
   - Implement changes where Current Time > Planned End Date auto-populate Actual End Time with Planned End Time, create a NOCC closure task, progress to Review, and close upon task completion.

### 7.2 Source-Created Unresolved Areas (Blocked from Implementation)

The following areas cannot be implemented without manufacturing unsourced rules and are blocked pending resolution of source decisions:

1. **Company Catalogue Filtering for Multi-Linked Agents:** Blocked by DEC-01. Set handling policy is unknown.
2. **Lead Time Calculation Logic:** Blocked by DEC-02. Contradiction between SRC-DOC-01 and SRC-XLS-01 values and formulas.
3. **Supporting Document Mandates:** Blocked by DEC-03. Direct conflict between global form mandate (DOC-01) and activity configuration booleans (XLS-01).
4. **Field 69 CyberKey Serial Visibility:** Blocked by DEC-04. Syntax contradiction in Field 67 dependency rule.
5. **Standard Change State Transition Path:** Blocked by DEC-05. Disputed paths between process map versions and site inspection annotations.
6. **Minimum Crew Size Rules:** Blocked by DEC-06. Threshold counts per Work Type are not provided.
7. **Flagged Entity Governance:** Blocked by DEC-07. Map annotation regarding bad practice restriction is unanswered.
8. **Post Site Visit Task Quotas and SLAs:** Blocked by DEC-08. Quota split and SLAs are marked TBD/unresolved.
9. **Task-Triggered Approval Architecture:** Blocked by DEC-09. Triggering platform is undetermined.
10. **Amendment State Flow:** Blocked by DEC-10. Map annotation on moving amended changes to Authorise/Amend is unresolved.
11. **Site Visit Event Triggers:** Blocked by Target-state status (REQ-LIF-08, REQ-LIF-09). Event detection mechanisms are not established in the evidence.
