# BA Benchmark Raw Result

> Raw model output. Not an evaluator score.

## Run metadata

- Benchmark: `Benchmark 042 — Multi-Source BA Model Comparison`
- Mode: `skill`
- Provider: `gemini`
- Model: `gemini-3.7-flash`
- Status: `success`
- Started: `2026-09-09T05:05:50Z`
- Ended: `2026-09-09T05:06:15Z`
- Temperature: `0.0`
- Max output tokens: `16384`
- Input SHA-256: `1432330128630c368efc83ea65458ebec990d731cc2dd0b11d77148c13b21af3`
- Prompt SHA-256: `327f4aeb1a6fd16d585800b3706194285a459265cd69d02950e95b5d07b717e1`
- Skill: `/volume1/docker/librechat-ba-lab/custom/ba-agent/skills/prepare-implementation-ready-requirements/SKILL.md`
- Skill version: `0.2.3`
- Skill SHA-256: `942aa6f4c1046658b650c5ad90c47e0f958f7bbfe312862f15c94fa8f1adb747`
- Finish reason: `STOP`
- Usage metadata: `{"candidatesTokenCount": 7143, "promptTokenCount": 5097, "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 5097}], "serviceTier": "standard", "thoughtsTokenCount": 1460, "totalTokenCount": 13700}`

---

## Model output

# Integrated Change Intake and Site Access — Business Analysis Package

---

## 1. Source Register

| Source ID | Title / Artifact Name | Format / Type | Description & Evidence Scope |
| :--- | :--- | :--- | :--- |
| **SRC-DOC-01** | Functional Enhancement Specification | Word Document | Defines Appian RFC intake, ServiceNow integration linkage, company catalogue filtering, multi-company agent linkage, role catalogue visibility, 4-tier hierarchy naming, date selection lead times, blanket supporting document rules, site access / Work Type / visitor qualification / crew rules, Field 67–69 key logic, and lifecycle transition/closure rules. |
| **SRC-XLS-01** | Service and Activity Catalogue | Excel Workbook | Operational configuration matrix defining 4-tier field taxonomy (`u_service_category`, `u_service_subcategory`, `u_service_l1`, `u_service_l2`), default `assignment_group`, Standard Change availability, SAR availability, Change Type, permitted PSN impact values (NSA / SA / RA), initial risk level, per-activity document requirement flags, per-activity lead times, and Change classification approval matrix (Minor, Significant, Major). |
| **SRC-MAP-01** | Post-ServiceNow Review Process Map | PDF (Draft/WIP) | Defines assignment routing fallback (PSN Helpdesk), Standard Change automated state progressions (New $\rightarrow$ Assess $\rightarrow$ Authorise $\rightarrow$ Scheduled vs. New $\rightarrow$ Scheduled for site inspection), and records four explicit unresolved design annotations. |
| **SRC-PPT-01** | Internal Change Transformation Presentation | PowerPoint Slide Deck | Defines business context, reduction of swivel-chair intake/double handling, target direct Appian-to-ServiceNow creation, improved scope classification, multi-table risk assessment target, and site-visit-triggered state transitions (first visit $\rightarrow$ Implement; final visit $\rightarrow$ NOCC closure task & Actual End Date). |

---

## 2. Requirements Register

*Classification Model:*
- **Evidence Class:** Explicit | Inferred | Disputed | Unknown
- **Status:** Confirmed | Candidate | Disputed | Target | Unknown

| Req ID | Requirement Statement | Evidence Class | Status | Source Trace |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-INT-01** | The RFC intake form shall be initiated in Appian. | Explicit | Confirmed | SRC-DOC-01, SRC-PPT-01 |
| **REQ-INT-02** | Submission of an RFC in Appian shall create a ServiceNow Change Request and link the Appian request number to the ServiceNow CHG number. | Explicit | Confirmed | SRC-DOC-01, SRC-PPT-01 |
| **REQ-CAT-01** | The Standard Change Catalogue shall be filtered by the Change Agent's affiliated company. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-CAT-02** | The system shall support Change Agents being linked to more than one company for the same activity. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-CAT-03** | Change Manager and MNP Service Desk roles shall be permitted to view all Standard Change Catalogue entries. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-CAT-04** | Activity selection shall follow a four-tier taxonomy: Change Category (`u_service_category`), Activity Category (`u_service_subcategory`), Activity Subcategory (`u_service_l1`), and Service L2 (`u_service_l2`). | Explicit | Confirmed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-ROU-01** | If an assignment group mapping exists in the Service and Activity Catalogue for the selected activity, the CR shall be assigned to that mapped `assignment_group`. | Explicit | Confirmed | SRC-XLS-01, SRC-MAP-01 |
| **REQ-ROU-02** | If no assignment group mapping exists for the selected activity, the CR shall be routed to the PSN Helpdesk. | Explicit | Confirmed | SRC-MAP-01 |
| **REQ-DAT-01** | Lead-time calculation for RFC date selection: Disputed between general formula rules (SRC-DOC-01) and catalogue-level explicit/formula values (SRC-XLS-01). | Disputed | Disputed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-DOC-01** | Supporting document mandatory upload rules: Disputed between blanket form requirements (MOP and SWMS mandatory on all RFCs; Release Notes mandatory for Software Update/Upgrade) and activity-specific catalogue booleans (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`). | Disputed | Disputed | SRC-DOC-01, SRC-XLS-01 |
| **REQ-ACC-01** | If site access is required on the RFC, at least one Work Type block shall be required. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-02** | Visitors selected for a Work Type must be qualified for that Work Type. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-03** | Minimum crew requirements for Work Types: Sourced condition established ("Some Work Types have minimum crew requirements"), but specific per-Work-Type minimum crew numbers and rules are not established. | Explicit | Unknown | SRC-DOC-01 |
| **REQ-KEY-01** | Field 67 shall capture whether a site key is required. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-02** | Field 68 shall capture the key type with options: GRN09, CyberKey, Other. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-03** | Field 69 (CyberKey serial number) conditional visibility logic: Disputed/Ambiguous due to specification contradiction ("Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68"). | Disputed | Disputed | SRC-DOC-01 |
| **REQ-APR-01** | Standard Changes shall skip manual approval. | Explicit | Confirmed | SRC-DOC-01, SRC-MAP-01 |
| **REQ-APR-02** | Change approvals for non-standard changes shall follow the classification matrix: Minor $\rightarrow$ Change Manager approval; Significant $\rightarrow$ CAB approval; Major $\rightarrow$ CAB + TAEC approval. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-STA-01** | Standard Change state progression: Candidate Path A: New $\rightarrow$ Assess $\rightarrow$ Authorise $\rightarrow$ Scheduled (automatic progression); Candidate Path B: New $\rightarrow$ Scheduled directly (for "Site inspection only"). | Explicit | Candidate | SRC-MAP-01 |
| **REQ-STA-02** | For a Change Request in `Implement` state, the Planned Start Date shall be locked, and only Planned End Date may be amended, subject to conflict checking. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-STA-03** | If Current Time > Planned End Date and the Change Request is in `Scheduled` state, the system shall close the CR as `No Show` and cancel the linked site access request. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-STA-04** | If Current Time > Planned End Date and the Change Request is in `Implement` state with no Actual End Time recorded, the system shall set Actual End Time to Planned End Time, create a NOCC closure task, transition the CR to `Review`, and close the CR after the NOCC closure task is completed. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-STA-05** | For changes requiring site attendance, first site visit triggers transition of the CR to `Implement`. | Explicit | Target | SRC-PPT-01 |
| **REQ-STA-06** | Final site visit creates a post-implementation task for NOCC and populates Actual End Date. | Explicit | Target | SRC-PPT-01 |

---

## 3. Solution-Neutral Delivery Backlog

### Backlog Item 1: Appian RFC Intake & ServiceNow Integration
- **ID:** `BL-INT-01`
- **Type:** Feature
- **Requirement Trace:** `REQ-INT-01`, `REQ-INT-02`
- **Status:** Ready
- **Summary:** Initiate RFC form in Appian, create linked ServiceNow Change Request upon submission, and link Appian request number with ServiceNow CHG number.

### Backlog Item 2: Company-Filtered Standard Change Catalogue & Role Visibility
- **ID:** `BL-CAT-01`
- **Type:** Feature
- **Requirement Trace:** `REQ-CAT-01`, `REQ-CAT-02`, `REQ-CAT-03`
- **Status:** Ready
- **Summary:** Filter Standard Change Catalogue by the Change Agent's affiliated company (allowing multiple company affiliations for an agent on the same activity) while granting Change Manager and MNP Service Desk visibility to all catalogue entries.

### Backlog Item 3: Four-Tier Activity Taxonomy & Assignment Routing
- **ID:** `BL-ROU-01`
- **Type:** Feature
- **Requirement Trace:** `REQ-CAT-04`, `REQ-ROU-01`, `REQ-ROU-02`
- **Status:** Ready
- **Summary:** Present four-tier activity hierarchy (Change Category, Activity Category, Activity Subcategory, Service L2) and route assignment to the mapped `assignment_group` from configuration, defaulting to PSN Helpdesk if unmapped.

### Backlog Item 4: Lead-Time Calculation Engine
- **ID:** `BL-DAT-01`
- **Type:** Decision Item / Feature
- **Requirement Trace:** `REQ-DAT-01`
- **Status:** Blocked (Pending source precedence / rule resolution)
- **Summary:** Implement lead-time date calculation rules once the conflict between SRC-DOC-01 general rules and SRC-XLS-01 catalogue rules is resolved.

### Backlog Item 5: Supporting Document Validation
- **ID:** `BL-DOC-01`
- **Type:** Decision Item / Feature
- **Requirement Trace:** `REQ-DOC-01`
- **Status:** Blocked (Pending source precedence / rule resolution)
- **Summary:** Enforce mandatory attachment rules (MOP, SWMS, Release Notes) once the contradiction between blanket form rules and catalogue boolean flags is resolved.

### Backlog Item 6: Site Access Work Types & Visitor Qualification
- **ID:** `BL-ACC-01`
- **Type:** Feature
- **Requirement Trace:** `REQ-ACC-01`, `REQ-ACC-02`, `REQ-ACC-03`
- **Status:** Partially Ready (Work Type requirement and visitor qualification Ready; crew minimums Blocked/Unknown)
- **Summary:** Require at least one Work Type block when site access is requested, validate that selected visitors hold qualifications for the selected Work Type, and enforce minimum crew requirements where established.

### Backlog Item 7: Site Key Selection & CyberKey Logic
- **ID:** `BL-KEY-01`
- **Type:** Decision Item / Feature
- **Requirement Trace:** `REQ-KEY-01`, `REQ-KEY-02`, `REQ-KEY-03`
- **Status:** Partially Ready (Key questions Ready; Field 69 display condition Blocked/Disputed)
- **Summary:** Capture site key requirement (Field 67) and key type selection (Field 68: GRN09, CyberKey, Other); apply Field 69 CyberKey serial number conditional display once contradictory validation logic is resolved.

### Backlog Item 8: Change Approval Matrix
- **ID:** `BL-APR-01`
- **Type:** Feature
- **Requirement Trace:** `REQ-APR-01`, `REQ-APR-02`
- **Status:** Ready
- **Summary:** Bypass manual approvals for Standard Changes; route Minor Changes to Change Manager, Significant Changes to CAB, and Major Changes to CAB + TAEC.

### Backlog Item 9: Standard Change State Progression
- **ID:** `BL-STA-01`
- **Type:** Decision Item / Feature
- **Requirement Trace:** `REQ-STA-01`
- **Status:** Candidate / Partially Ready
- **Summary:** Automate Standard Change progression across lifecycle states (New $\rightarrow$ Assess $\rightarrow$ Authorise $\rightarrow$ Scheduled vs. direct New $\rightarrow$ Scheduled for site inspection).

### Backlog Item 10: In-Flight Schedule Amendments & Auto-Closure Lifecycle
- **ID:** `BL-STA-02`
- **Type:** Feature
- **Requirement Trace:** `REQ-STA-02`, `REQ-STA-03`, `REQ-STA-04`
- **Status:** Ready
- **Summary:** Lock Planned Start Date during `Implement` state while permitting Planned End Date amendments with conflict checking; auto-close Scheduled CRs exceeding Planned End Date as No Show (with site access cancellation); auto-transition overdue Implement CRs without Actual End Time to Review with NOCC closure task.

### Backlog Item 11: Site Visit Lifecycle Triggers
- **ID:** `BL-STA-03`
- **Type:** Target Feature
- **Requirement Trace:** `REQ-STA-05`, `REQ-STA-06`
- **Status:** Target (Pending operational design)
- **Summary:** Trigger transition to `Implement` on first site visit; populate Actual End Date and generate NOCC closure task upon final site visit.

---

## 4. Acceptance Criteria

### `BL-INT-01`: Appian RFC Intake & ServiceNow Integration

#### Scenario AC-INT-01.1: Successful RFC submission creates linked ServiceNow CR
- **Given** an RFC form is initiated and submitted in Appian,
- **When** the submission is processed,
- **Then** a ServiceNow Change Request is created,
- **And** the Appian request number is linked to the ServiceNow CHG number.

---

### `BL-CAT-01`: Standard Change Catalogue Filtering & Role Visibility

#### Scenario AC-CAT-01.1: Change Agent catalogue filtering
- **Given** a Change Agent accessing the Standard Change Catalogue,
- **When** the catalogue entries are loaded,
- **Then** only entries matching the Change Agent's affiliated company (or companies, if linked to more than one for the activity) are displayed.

#### Scenario AC-CAT-01.2: Elevated role catalogue visibility
- **Given** a user with the role of Change Manager or MNP Service Desk,
- **When** the Standard Change Catalogue is viewed,
- **Then** all Standard Change Catalogue entries are visible.

---

### `BL-ROU-01`: Four-Tier Taxonomy & Assignment Routing

#### Scenario AC-ROU-01.1: Four-tier taxonomy hierarchy
- **Given** an activity selection on the RFC intake form,
- **When** the user selects the activity,
- **Then** the selection follows the four-tier hierarchy: Change Category (`u_service_category`), Activity Category (`u_service_subcategory`), Activity Subcategory (`u_service_l1`), and Service L2 (`u_service_l2`).

#### Scenario AC-ROU-01.2: Assignment to mapped group
- **Given** an activity selection that has a mapped `assignment_group` in the catalogue,
- **When** the Change Request is routed,
- **Then** the CR is assigned to the mapped `assignment_group`.

#### Scenario AC-ROU-01.3: Fallback assignment when unmapped
- **Given** an activity selection that does not have an `assignment_group` mapping,
- **When** the Change Request is routed,
- **Then** the CR is assigned to the PSN Helpdesk.

---

### `BL-ACC-01`: Site Access Work Types & Visitor Qualification

#### Scenario AC-ACC-01.1: Mandatory Work Type when site access required
- **Given** site access is indicated as required on the RFC form,
- **When** the site access section is validated,
- **Then** at least one Work Type block must be provided.

#### Scenario AC-ACC-01.2: Visitor qualification check
- **Given** a Work Type block on the site access request,
- **When** visitors are selected for that Work Type,
- **Then** each selected visitor must be qualified for that Work Type.

#### Sourced Unresolved Condition AC-ACC-01.3: Minimum crew requirements
- **Condition:** Some Work Types have minimum crew requirements.
- **Required outcome:** `Unknown / Not established from supplied evidence`.

---

### `BL-KEY-01`: Site Key Selection

#### Scenario AC-KEY-01.1: Site key requirement and key type selection
- **Given** the RFC intake form,
- **When** the key selection section is accessed,
- **Then** Field 67 captures whether a site key is required,
- **And** Field 68 provides key type options: GRN09, CyberKey, and Other.

#### Sourced Unresolved Condition AC-KEY-01.2: CyberKey serial number display
- **Condition:** Field 69 (CyberKey serial number) display rule states "Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68."
- **Required outcome:** `Unknown / Not established from supplied evidence` (Blocked pending resolution of contradictory condition logic).

---

### `BL-APR-01`: Change Approval Matrix

#### Scenario AC-APR-01.1: Standard Change manual approval bypass
- **Given** a Change Request classified as Standard Change,
- **When** the Change Request is processed,
- **Then** manual approval is skipped.

#### Scenario AC-APR-01.2: Minor Change approval
- **Given** a Change Request classified as Minor,
- **When** the Change Request enters approval,
- **Then** approval is routed to the Change Manager.

#### Scenario AC-APR-01.3: Significant Change approval
- **Given** a Change Request classified as Significant,
- **When** the Change Request enters approval,
- **Then** approval is routed to CAB.

#### Scenario AC-APR-01.4: Major Change approval
- **Given** a Change Request classified as Major,
- **When** the Change Request enters approval,
- **Then** approval is routed to CAB and TAEC.

---

### `BL-STA-02`: In-Flight Amendments & Automated Closure

#### Scenario AC-STA-02.1: Date amendment in Implement state
- **Given** a Change Request in `Implement` state,
- **When** date fields are edited,
- **Then** the Planned Start Date is locked and cannot be amended,
- **And** the Planned End Date may be amended, subject to conflict checking.

#### Scenario AC-STA-02.2: Scheduled CR past Planned End Date (No Show)
- **Given** a Change Request in `Scheduled` state,
- **When** Current Time > Planned End Date,
- **Then** the Change Request is closed as `No Show`,
- **And** the linked site access request is cancelled.

#### Scenario AC-STA-02.3: Overdue Implement CR without Actual End Time
- **Given** a Change Request in `Implement` state with no Actual End Time recorded,
- **When** Current Time > Planned End Date,
- **Then** Actual End Time is set to Planned End Time,
- **And** a NOCC closure task is created,
- **And** the Change Request moves to `Review` state,
- **And** the Change Request is closed after the NOCC closure task is completed.

---

## 5. Requirements Traceability Matrix (RTM)

| Source ID | Req ID | Backlog Item ID | Acceptance Criteria ID / Status | Lifecycle State |
| :--- | :--- | :--- | :--- | :--- |
| SRC-DOC-01, SRC-PPT-01 | `REQ-INT-01` | `BL-INT-01` | `AC-INT-01.1` | Implementation-Ready |
| SRC-DOC-01, SRC-PPT-01 | `REQ-INT-02` | `BL-INT-01` | `AC-INT-01.1` | Implementation-Ready |
| SRC-DOC-01 | `REQ-CAT-01` | `BL-CAT-01` | `AC-CAT-01.1` | Implementation-Ready |
| SRC-DOC-01 | `REQ-CAT-02` | `BL-CAT-01` | `AC-CAT-01.1` | Implementation-Ready |
| SRC-DOC-01 | `REQ-CAT-03` | `BL-CAT-01` | `AC-CAT-01.2` | Implementation-Ready |
| SRC-DOC-01, SRC-XLS-01 | `REQ-CAT-04` | `BL-ROU-01` | `AC-ROU-01.1` | Implementation-Ready |
| SRC-XLS-01, SRC-MAP-01 | `REQ-ROU-01` | `BL-ROU-01` | `AC-ROU-01.2` | Implementation-Ready |
| SRC-MAP-01 | `REQ-ROU-02` | `BL-ROU-01` | `AC-ROU-01.3` | Implementation-Ready |
| SRC-DOC-01, SRC-XLS-01 | `REQ-DAT-01` | `BL-DAT-01` | Blocked (Disputed Source Logic) | Unresolved / Blocked |
| SRC-DOC-01, SRC-XLS-01 | `REQ-DOC-01` | `BL-DOC-01` | Blocked (Disputed Source Logic) | Unresolved / Blocked |
| SRC-DOC-01 | `REQ-ACC-01` | `BL-ACC-01` | `AC-ACC-01.1` | Implementation-Ready |
| SRC-DOC-01 | `REQ-ACC-02` | `BL-ACC-01` | `AC-ACC-01.2` | Implementation-Ready |
| SRC-DOC-01 | `REQ-ACC-03` | `BL-ACC-01` | `AC-ACC-01.3` (Outcome Unknown) | Unresolved / Sourced Condition |
| SRC-DOC-01 | `REQ-KEY-01` | `BL-KEY-01` | `AC-KEY-01.1` | Implementation-Ready |
| SRC-DOC-01 | `REQ-KEY-02` | `BL-KEY-01` | `AC-KEY-01.1` | Implementation-Ready |
| SRC-DOC-01 | `REQ-KEY-03` | `BL-KEY-01` | `AC-KEY-01.2` (Outcome Unknown) | Unresolved / Disputed Logic |
| SRC-DOC-01, SRC-MAP-01 | `REQ-APR-01` | `BL-APR-01` | `AC-APR-01.1` | Implementation-Ready |
| SRC-XLS-01 | `REQ-APR-02` | `BL-APR-01` | `AC-APR-01.2`, `01.3`, `01.4` | Implementation-Ready |
| SRC-MAP-01 | `REQ-STA-01` | `BL-STA-01` | Candidate Progression Paths | Candidate / Partially Ready |
| SRC-DOC-01 | `REQ-STA-02` | `BL-STA-02` | `AC-STA-02.1` | Implementation-Ready |
| SRC-DOC-01 | `REQ-STA-03` | `BL-STA-02` | `AC-STA-02.2` | Implementation-Ready |
| SRC-DOC-01 | `REQ-STA-04` | `BL-STA-02` | `AC-STA-02.3` | Implementation-Ready |
| SRC-PPT-01 | `REQ-STA-05` | `BL-STA-03` | Blocked (Target State Rule) | Target Scope |
| SRC-PPT-01 | `REQ-STA-06` | `BL-STA-03` | Blocked (Target State Rule) | Target Scope |

---

## 6. Source-Created Contradictions, Ambiguities, and Unresolved Decisions

### Contradictions & Precedence Ambiguities

1. **Lead-Time Calculation Discrepancy:**
   - *SRC-DOC-01:* Standard = 3 business days processing + 1 day NSA / 14 days SA; Minor = 5 business days processing + 1 day NSA; Significant = 10 business days after next CAB + 1 day NSA / 14 days SA; Major = 10 business days after next CAB + 14 days NSA / 1 month SA.
   - *SRC-XLS-01:* Activity rows define distinct fixed/formula lead times (e.g., Air Conditioning Inspection [Minor] = 6 days NSA; Windows Patching [Standard] = 4 days NSA; Motorola Upgrade [Significant] = 25 + CAB days; New Site Integration [Major] = 54 + CAB days).
   - *Ambiguity:* Neither artifact defines precedence rules between the specification and catalogue matrix.

2. **Supporting Document Upload Rules Discrepancy:**
   - *SRC-DOC-01:* MOP and SWMS uploads are stated as mandatory on the RFC form; Vendor Release Notes are required for Software Update or Upgrade activities.
   - *SRC-XLS-01:* Contains explicit boolean columns (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`) where individual activities vary (e.g., Air Conditioning has MOP = false, SWMS = true; Windows Patching has MOP = false, SWMS = false, Release Notes = true).
   - *Ambiguity:* Precedence between blanket RFC mandatory flags and catalogue-driven boolean flags is not established.

3. **Field 69 (CyberKey Serial Number) Validation Syntax Contradiction:**
   - *SRC-DOC-01:* The validation note reads: *"Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68."*
   - *Ambiguity:* The rule states both "Yes is selected" and "is No" for Question 67 simultaneously.

4. **Standard Change State Progression Models:**
   - *SRC-MAP-01 Process Map v1/v2:* Shows automated sequence `New` $\rightarrow$ `Assess` $\rightarrow$ `Authorise` $\rightarrow$ `Scheduled`.
   - *SRC-MAP-01 Annotation:* Shows a direct transition `New` $\rightarrow$ `Scheduled` for "Site inspection only".

### Unresolved Process Map Annotations (SRC-MAP-01)

5. **Poor Performance / Bad Change Practice Flag:**
   - *Source Text:* "For user/org that has been flagged for poor performance or bad change practice. Can they proceed with change creation."
   - *Required outcome:* `Unknown / Not established from supplied evidence`.

6. **Post Site Visit Task Quota & SLAs:**
   - *Source Text:* "Post site visit tasks – Quota? 10% action – 90% Auto close? SLAs to be defined."
   - *Required outcome:* `Unknown / Not established from supplied evidence`.

7. **Change Task Approval Trigger System:**
   - *Source Text:* "Question – SNOW, Appian or other? Change task trigger a change approval."
   - *Required outcome:* `Unknown / Not established from supplied evidence`.

8. **Minor In-Flight Amendment State Transition:**
   - *Source Text:* "If minor change to change (such as date changes) move to Authorize (Or new state… such as 'Amend'.) TBD."
   - *Required outcome:* `Unknown / Not established from supplied evidence`.

### Sourced Incomplete Conditions

9. **Work Type Minimum Crew Numbers:**
   - *SRC-DOC-01:* Sourced condition states "Some Work Types have minimum crew requirements", but exact numeric thresholds and applicable Work Types are not provided.
   - *Required outcome:* `Unknown / Not established from supplied evidence`.

---

## 7. Completeness and Readiness Assessment

### Implementation-Ready Areas (Ready for Development)
- **Intake & Integration Flow:** Appian RFC initiation, ServiceNow CHG creation, and bi-directional ID linking (`REQ-INT-01`, `REQ-INT-02`).
- **Catalogue Filtering & Visibility:** Filtering Standard Changes by Change Agent company affiliation (including multi-company links) and elevated visibility for Change Manager and MNP Service Desk (`REQ-CAT-01`, `REQ-CAT-02`, `REQ-CAT-03`).
- **Activity Taxonomy & Assignment Routing:** Four-tier category hierarchy structure and default group routing with PSN Helpdesk fallback (`REQ-CAT-04`, `REQ-ROU-01`, `REQ-ROU-02`).
- **Site Access Work Type & Qualification:** Work Type presence check when site access is selected and visitor-to-Work-Type qualification verification (`REQ-ACC-01`, `REQ-ACC-02`).
- **Basic Key Type Capture:** Field 67 and Field 68 capture for site keys (`REQ-KEY-01`, `REQ-KEY-02`).
- **Approval Routing:** Manual approval bypass for Standard Changes; Minor $\rightarrow$ Change Manager, Significant $\rightarrow$ CAB, Major $\rightarrow$ CAB + TAEC (`REQ-APR-01`, `REQ-APR-02`).
- **In-Flight Amendments & Overdue Auto-Closure:** Field locking rules in `Implement` state, `Scheduled` No Show auto-closure with access cancellation, and overdue `Implement` Review transition with NOCC closure task creation (`REQ-STA-02`, `REQ-STA-03`, `REQ-STA-04`).

### Blocked / Source-Created Unresolved Areas (Requires Clarification)
- **Lead-Time Calculation (`REQ-DAT-01`, `BL-DAT-01`):** Blocked pending resolution of precedence between DOC-01 general lead times and XLS-01 catalogue lead times.
- **Document Mandatory Rules (`REQ-DOC-01`, `BL-DOC-01`):** Blocked pending resolution of precedence between DOC-01 blanket mandatory rules and XLS-01 per-activity flags.
- **Field 69 CyberKey Conditional Display (`REQ-KEY-03`, `BL-KEY-01`):** Blocked pending correction of contradictory condition syntax ("Yes is selected for Question 67 is No").
- **Minimum Crew Values (`REQ-ACC-03`):** Blocked pending provision of per-Work-Type crew size rules.
- **Standard Change Lifecycle Path (`REQ-STA-01`, `BL-STA-01`):** Candidate paths (full automatic progression vs. direct New $\rightarrow$ Scheduled for site inspections) require operational alignment.
- **Process Map Annotations 1–4:** Four draft annotations remain unresolved design questions with unknown outcomes.
- **Site Visit Implementation Triggers (`REQ-STA-05`, `REQ-STA-06`):** Target-state concepts from PPT-01 requiring detailed operational trigger definitions.
