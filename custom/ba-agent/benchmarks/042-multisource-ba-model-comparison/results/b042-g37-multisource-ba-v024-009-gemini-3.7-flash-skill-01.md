# BA Benchmark Raw Result

> Raw model output. Not an evaluator score.

## Run metadata

- Benchmark: `Benchmark 042 — Multi-Source BA Model Comparison`
- Mode: `skill`
- Provider: `gemini`
- Model: `gemini-3.7-flash`
- Status: `success`
- Started: `2026-09-09T08:47:47Z`
- Ended: `2026-09-09T08:48:14Z`
- Temperature: `0.0`
- Max output tokens: `16384`
- Input SHA-256: `1432330128630c368efc83ea65458ebec990d731cc2dd0b11d77148c13b21af3`
- Prompt SHA-256: `327f4aeb1a6fd16d585800b3706194285a459265cd69d02950e95b5d07b717e1`
- Skill: `/volume1/docker/librechat-ba-lab/custom/ba-agent/skills/prepare-implementation-ready-requirements/SKILL.md`
- Skill version: `0.2.4`
- Skill SHA-256: `a38fda060b2ccaec03fe137dbde1049985dd6971a7dbc2a41ec81d762a037c99`
- Finish reason: `STOP`
- Usage metadata: `{"candidatesTokenCount": 7449, "promptTokenCount": 5986, "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 5986}], "serviceTier": "standard", "thoughtsTokenCount": 1147, "totalTokenCount": 14582}`

---

## Model output

# Business Analysis Package: Integrated Change Intake and Site Access

## 1. Source Register

| Source ID | Document / Artifact Name | Format / Type | Description / Scope |
| :--- | :--- | :--- | :--- |
| **SRC-DOC-01** | Functional Enhancement Specification | Word Document | Defines RFC intake rules in Appian, ServiceNow linking, catalogue role filtering, multi-company agent association, lead-time rules, document requirements, site access/qualification/key rules, and change lifecycle timeout/transition rules. |
| **SRC-XLS-01** | Service and Activity Catalogue | Excel Workbook | Defines operational configuration matrix: four-tier taxonomy (`u_service_category`, `u_service_subcategory`, `u_service_l1`, `u_service_l2`), default `assignment_group`, Standard Change availability, SAR availability, Change Type, permitted PSN impact (NSA/SA/RA), initial risk level, and per-activity document flags (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`). |
| **SRC-MAP-01** | Post-ServiceNow Review Process Map | PDF (Marked WIP / Draft) | Defines Standard Change state progressions (New $\rightarrow$ Assess $\rightarrow$ Authorise $\rightarrow$ Scheduled vs. direct New $\rightarrow$ Scheduled for site inspection), assignment group fallback routing to PSN Helpdesk, and four explicit unresolved design annotations. |
| **SRC-PPT-01** | Internal Change Transformation Presentation | PowerPoint Presentation | Outlines current pain points (swivel-chair handling, processing time, one-size-fits-all risk assessment) and target-state concepts (direct Appian-to-ServiceNow creation, improved scope/risk classification, first site visit triggering Implement, final site visit triggering NOCC task and Actual End Date population). |

---

## 2. Requirements Register

*Evidence Classes: Explicit, Inferred, Disputed, Unknown*  
*Requirement Statuses: Confirmed, Candidate, Target, Disputed, Deferred, Unknown*

| Req ID | Title / Stated Behaviour | Evidence Class | Status | Source Trace |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-INT-01** | **Appian Intake & ServiceNow Linking**<br>The RFC form is initiated in Appian. A submitted RFC creates a ServiceNow Change Request and links the Appian request number to the ServiceNow CHG number. | Explicit | Confirmed | SRC-DOC-01<br>SRC-PPT-01 |
| **REQ-INT-02** | **Standard Change Catalogue Company Filtering**<br>The Standard Change Catalogue is filtered by the Change Agent's affiliated company. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-INT-03** | **Multi-Company Association for Change Agents**<br>Change Agents may be linked to more than one company for the same activity.<br>*Condition:* Multi-company association exists.<br>*Required outcome:* Unknown / Not established from supplied evidence. | Explicit | Unknown | SRC-DOC-01 |
| **REQ-INT-04** | **Privileged Role Catalogue Visibility**<br>Change Manager and MNP Service Desk roles can view all Standard Change Catalogue entries. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-TAX-01** | **Four-Tier Activity Taxonomy**<br>Activity selection uses a four-tier hierarchy: Change Category (`u_service_category`), Activity Category (`u_service_subcategory`), Activity Subcategory (`u_service_l1`), and Service L2 (`u_service_l2`). | Explicit | Confirmed | SRC-DOC-01<br>SRC-XLS-01 |
| **REQ-TAX-02** | **Activity Operational Configuration Controls**<br>Each catalogue activity row establishes: default `assignment_group`, boolean flags for `Standard Change option available?` and `SAR option available?`, Change Type, permitted PSN impact values (`NSA`, `SA`, `RA`), and initial risk level. | Explicit | Confirmed | SRC-XLS-01 |
| **REQ-ROU-01** | **Assignment Group Routing & Fallback**<br>If an assignment group mapping exists in the catalogue, allocate the CR to the mapped group; if no mapping exists, allocate through PSN Helpdesk. | Explicit | Confirmed | SRC-XLS-01<br>SRC-MAP-01 |
| **REQ-APR-01** | **Change Classification Approval Matrix**<br>Approvals are determined by Change Type:<br>- Standard: Skips manual approval.<br>- Minor: Change Manager approval.<br>- Significant: CAB approval.<br>- Major: CAB + TAEC approval. | Explicit | Confirmed | SRC-DOC-01<br>SRC-XLS-01 |
| **REQ-DOC-01** | **Supporting Document Upload Rules**<br>*SRC-DOC-01 Rule:* MOP upload and SWMS upload are mandatory on the RFC form; Vendor Release Notes are required for Software Update or Software Upgrade activities.<br>*SRC-XLS-01 Rule:* MOP, SWMS, and Release Notes requirement is governed per activity row by operational booleans (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`). | Disputed | Disputed | SRC-DOC-01<br>SRC-XLS-01 |
| **REQ-TIM-01** | **Date Selection & Lead-Time Rules**<br>*SRC-DOC-01 Formula:* Standard = 3 days processing + 1 day (NSA) / 14 days (SA); Minor = 5 days processing + 1 day (NSA); Significant = 10 days post-next CAB + 1 day (NSA) / 14 days (SA); Major = 10 days post-next CAB + 14 days (NSA) / 1 month (SA).<br>*SRC-XLS-01 Values:* Specific activity lead times (e.g. Core Upgrade = 25 days + CAB; CCEP Integration = 54 days + CAB; AC Inspection Minor NSA = 6 days; Windows Patching Standard NSA = 4 days). | Disputed | Disputed | SRC-DOC-01<br>SRC-XLS-01 |
| **REQ-ACC-01** | **Site Access Work Types & Visitor Qualification**<br>If site access is required, at least one Work Type block is required. Visitors selected for a Work Type must be qualified for that Work Type. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-ACC-02** | **Work Type Minimum Crew Requirements**<br>Some Work Types have minimum crew requirements.<br>*Condition:* Work Type with minimum crew requirement selected.<br>*Required outcome:* Specific minimum crew sizes and validation outcomes are Unknown / Not established from supplied evidence. | Explicit | Unknown | SRC-DOC-01 |
| **REQ-KEY-01** | **Site Key Capture Fields**<br>RFC form captures:<br>- Field 67: Whether a site key is required.<br>- Field 68: Key type (`GRN09`, `CyberKey`, `Other`). | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-KEY-02** | **CyberKey Serial Number Conditional Display**<br>Field 69 captures CyberKey serial number.<br>*Validation Note:* "Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68."<br>*Condition:* Contradictory precondition syntax ("Yes is selected for Question 67 is No"). | Disputed | Disputed | SRC-DOC-01 |
| **REQ-LIF-01** | **Implement State Date Locking**<br>For a change in Implement state, Planned Start Date is locked; only Planned End Date may be amended, subject to conflict checking. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-02** | **Scheduled Change Timeout (No Show)**<br>If Current Time > Planned End Date and the Change Request is in Scheduled state, close the CR as No Show and cancel the linked site access request. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-03** | **Implement Change Timeout (NOCC Review)**<br>If Current Time > Planned End Date and the Change Request is in Implement state with no Actual End Time: set Actual End Time to Planned End Time, create a NOCC closure task, move CR to Review, and close CR after the task is completed. | Explicit | Confirmed | SRC-DOC-01 |
| **REQ-LIF-04** | **Standard Change Lifecycle State Progression**<br>*SRC-MAP-01 v1/v2:* New $\rightarrow$ Assess $\rightarrow$ Authorise $\rightarrow$ Scheduled (automatic progression).<br>*SRC-MAP-01 Annotation:* Site inspection only Standard Changes move directly New $\rightarrow$ Scheduled. | Disputed | Disputed | SRC-DOC-01<br>SRC-MAP-01 |
| **REQ-TGT-01** | **First Site Visit State Trigger**<br>First site visit triggers the move to Implement state for changes requiring site attendance. | Explicit | Target | SRC-PPT-01 |
| **REQ-TGT-02** | **Final Site Visit Task & Completion Trigger**<br>Final site visit creates a post-implementation task for NOCC and populates Actual End Date. | Explicit | Target | SRC-PPT-01 |

---

## 3. Solution-Neutral Delivery Backlog / Decomposition

### Decomposition Readiness
- **Partially Ready**: Sourced confirmed behaviours are decomposed into implementation-ready backlog items. Sourced unresolved rules, conditions with unknown outcomes, and source-to-source contradictions are preserved as explicit Decision Items.

```
Epic 1: Intake Integration & Dynamic Catalogue
├── US-INT-01: Appian to ServiceNow Request Creation & Linkage
├── US-INT-02: Role & Company Catalogue Filtering
├── US-INT-03: Four-Tier Taxonomy & Operational Controls Configuration
├── US-ROU-01: Assignment Group Allocation & Fallback Routing
├── DEC-INT-01: Multi-Company Filtering Handling Policy
├── DEC-DOC-01: Document Upload Mandatory Rules vs. Matrix Booleans
└── DEC-TIM-01: Standard Lead-Time Formulas vs. Catalogue Lead-Time Overrides

Epic 2: Approval Matrix & Lifecycle Progression
├── US-APR-01: Classification Approval Routing
├── US-LIF-01: Implement State Date Modification & Locking
├── US-LIF-02: Scheduled State Timeout Closure (No Show)
├── US-LIF-03: Implement State Timeout Closure (NOCC Review)
├── DEC-LIF-01: Standard Change Lifecycle State Path
└── DEC-MAP-04: Minor Date Modifications Workflow & State Path

Epic 3: Site Access & Key Management
├── US-ACC-01: Work Type Selection & Visitor Qualification
├── US-KEY-01: Key Requirement & Key Type Field Capture
├── DEC-ACC-01: Minimum Crew Requirements per Work Type
└── DEC-KEY-01: CyberKey Serial Field Conditional Display Precondition

Epic 4: Target Site-Attendance Automated Transitions (Target Scope)
├── TGT-LIF-01: First Site Visit Progression to Implement
└── TGT-LIF-02: Final Site Visit NOCC Task & Actual End Date Population
```

### Backlog Item Specifications

#### US-INT-01: Appian to ServiceNow Request Creation & Linkage
- **Scope**: Intake RFC initiation in Appian, create corresponding Change Request in ServiceNow, and maintain bidirectional identifier linkage (Appian request number $\leftrightarrow$ ServiceNow CHG number).
- **Traced Req**: REQ-INT-01

#### US-INT-02: Role & Company Catalogue Filtering
- **Scope**: Filter Standard Change Catalogue entries by Change Agent affiliated company. Allow Change Manager and MNP Service Desk roles full visibility across all catalogue entries.
- **Traced Req**: REQ-INT-02, REQ-INT-04

#### US-INT-03: Four-Tier Taxonomy & Operational Controls Configuration
- **Scope**: Provide selection across Tier 1 (`u_service_category`), Tier 2 (`u_service_subcategory`), Tier 3 (`u_service_l1`), and Tier 4 (`u_service_l2`). For each activity, apply mapped controls: `assignment_group`, `Standard Change option available?`, `SAR option available?`, Change Type, permitted PSN impact values (`NSA`/`SA`/`RA`), and initial risk level.
- **Traced Req**: REQ-TAX-01, REQ-TAX-02

#### US-ROU-01: Assignment Group Allocation & Fallback Routing
- **Scope**: Route Change Request to catalogue mapped `assignment_group`. If no mapping exists on the selected activity, route to PSN Helpdesk.
- **Traced Req**: REQ-ROU-01

#### US-APR-01: Classification Approval Routing
- **Scope**: Direct Change Requests based on Change Type: Standard skips manual approval; Minor routes to Change Manager; Significant routes to CAB; Major routes to CAB + TAEC.
- **Traced Req**: REQ-APR-01

#### US-LIF-01: Implement State Date Modification & Locking
- **Scope**: When CR is in Implement state, enforce Planned Start Date locking. Allow Planned End Date amendments subject to conflict checking.
- **Traced Req**: REQ-LIF-01

#### US-LIF-02: Scheduled State Timeout Closure (No Show)
- **Scope**: Automatically evaluate CRs in Scheduled state. If Current Time > Planned End Date, close CR with status No Show and cancel the linked site access request.
- **Traced Req**: REQ-LIF-02

#### US-LIF-03: Implement State Timeout Closure (NOCC Review)
- **Scope**: Automatically evaluate CRs in Implement state where Actual End Time is empty. If Current Time > Planned End Date, set Actual End Time = Planned End Time, create NOCC closure task, advance CR to Review, and close CR upon completion of the NOCC task.
- **Traced Req**: REQ-LIF-03

#### US-ACC-01: Work Type Selection & Visitor Qualification
- **Scope**: Require at least one Work Type block when site access is required. Ensure visitors selected for a Work Type are qualified for that Work Type.
- **Traced Req**: REQ-ACC-01

#### US-KEY-01: Key Requirement & Key Type Field Capture
- **Scope**: Render Field 67 (site key required boolean) and Field 68 (key type: `GRN09`, `CyberKey`, `Other`).
- **Traced Req**: REQ-KEY-01

---

## 4. Acceptance Criteria

### Ready / Confirmed Backlog Items

#### US-INT-01: Appian to ServiceNow Request Creation & Linkage
```gherkin
Scenario: Successful RFC intake and ServiceNow record linkage
  Given an RFC is initiated and submitted in Appian
  When the ServiceNow Change Request is created
  Then the Appian request number is linked to the ServiceNow CHG number
```

#### US-INT-02: Role & Company Catalogue Filtering
```gherkin
Scenario: Catalogue filtering for Change Agent with single company affiliation
  Given a Change Agent affiliated with a single company accesses the Standard Change Catalogue
  When the catalogue entries are retrieved
  Then only entries associated with that company are displayed

Scenario: Privileged role catalogue access
  Given a user with the Change Manager or MNP Service Desk role accesses the Standard Change Catalogue
  When the catalogue entries are retrieved
  Then all Standard Change Catalogue entries are displayed regardless of company affiliation
```

#### US-INT-03: Four-Tier Taxonomy & Operational Controls Configuration
```gherkin
Scenario: Activity taxonomy selection and operational controls association
  Given an activity is selected via Tier 1 u_service_category, Tier 2 u_service_subcategory, Tier 3 u_service_l1, and Tier 4 u_service_l2
  When the operational configuration is loaded
  Then the default assignment_group, Standard Change option availability, SAR option availability, Change Type, permitted PSN impact values (NSA/SA/RA), and initial risk level from the catalogue are applied
```

#### US-ROU-01: Assignment Group Allocation & Fallback Routing
```gherkin
Scenario: Mapped assignment group routing
  Given an activity selection with an explicit assignment group mapping
  When assignment routing is evaluated
  Then the Change Request is allocated to the mapped assignment group

Scenario: Unmapped assignment group fallback routing
  Given an activity selection with no assignment group mapping
  When assignment routing is evaluated
  Then the Change Request is allocated to PSN Helpdesk
```

#### US-APR-01: Classification Approval Routing
```gherkin
Scenario Outline: Approval routing by Change Type
  Given a Change Request with Change Type <change_type>
  When the approval step is evaluated
  Then the required approval is <approval_action>

  Examples:
    | change_type | approval_action                  |
    | Standard    | Skip manual approval             |
    | Minor       | Change Manager approval          |
    | Significant | CAB approval                     |
    | Major       | CAB approval and TAEC approval   |
```

#### US-LIF-01: Implement State Date Modification & Locking
```gherkin
Scenario: Planned Start Date locked in Implement state
  Given a Change Request in Implement state
  When a user attempts to edit the Planned Start Date
  Then the Planned Start Date cannot be modified

Scenario: Planned End Date amendment in Implement state
  Given a Change Request in Implement state
  When a user submits an amended Planned End Date
  Then the amendment is processed subject to conflict checking
```

#### US-LIF-02: Scheduled State Timeout Closure (No Show)
```gherkin
Scenario: Scheduled Change Request exceeds Planned End Date
  Given a Change Request is in Scheduled state
  When Current Time is greater than Planned End Date
  Then the Change Request is closed as No Show
  And the linked site access request is cancelled
```

#### US-LIF-03: Implement State Timeout Closure (NOCC Review)
```gherkin
Scenario: Implement Change Request with no Actual End Time exceeds Planned End Date
  Given a Change Request is in Implement state
  And Actual End Time is not populated
  When Current Time is greater than Planned End Date
  Then Actual End Time is set to Planned End Time
  And a NOCC closure task is created
  And the Change Request moves to Review state
  And the Change Request is closed after the NOCC closure task is completed
```

#### US-ACC-01: Work Type Selection & Visitor Qualification
```gherkin
Scenario: Site access requires at least one Work Type
  Given site access is required for an RFC
  When Work Type selections are validated
  Then at least one Work Type block must be present

Scenario: Visitor qualification enforcement
  Given a visitor is selected for a Work Type block
  When visitor eligibility is validated
  Then the visitor must be qualified for that Work Type
```

#### US-KEY-01: Key Requirement & Key Type Field Capture
```gherkin
Scenario: Field 67 and Field 68 presence
  Given the RFC form is opened
  When the key information section is rendered
  Then Field 67 captures whether a site key is required
  And Field 68 captures key type with options GRN09, CyberKey, or Other
```

---

### Sourced Blocked / Disputed / Unknown Items (Criteria Not Ready)

The following items cannot have confirmed testable criteria elaborated because the source evidence contains unresolved outcomes, syntax contradictions, or conflicting business rules:

1. **Multi-Company Filtering Handling Policy (DEC-INT-01 / REQ-INT-03)**
   - *Sourced Condition:* Change Agent is linked to more than one company for the same activity.
   - *Required Outcome:* Unknown / Not established from supplied evidence. (Handling policy—e.g. union of catalogues, company selector prompt, primary company default—is not defined).
2. **Document Upload Enforcement (DEC-DOC-01 / REQ-DOC-01)**
   - *Sourced Conflict:* SRC-DOC-01 defines mandatory MOP and SWMS form uploads; SRC-XLS-01 specifies row-level booleans (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`) where some activities do not require MOP or SWMS.
   - *Required Outcome:* Unknown / Disputed precedence.
3. **Date Selection & Lead-Time Rules (DEC-TIM-01 / REQ-TIM-01)**
   - *Sourced Conflict:* SRC-DOC-01 standard formula vs. SRC-XLS-01 explicit catalogue lead-time day numbers.
   - *Required Outcome:* Unknown / Disputed precedence.
4. **CyberKey Serial Field Display Validation (DEC-KEY-01 / REQ-KEY-02)**
   - *Sourced Conflict:* Contradictory text in validation note ("Yes is selected for Question 67 is No").
   - *Required Outcome:* Unknown / Blocked until field dependency rule is corrected.
5. **Work Type Minimum Crew Logic (DEC-ACC-01 / REQ-ACC-02)**
   - *Sourced Condition:* Some Work Types have minimum crew requirements.
   - *Required Outcome:* Unknown / Specific crew size counts and threshold validation outcomes not established.
6. **Standard Change State Progression (DEC-LIF-01 / REQ-LIF-04)**
   - *Sourced Conflict:* New $\rightarrow$ Assess $\rightarrow$ Authorise $\rightarrow$ Scheduled (SRC-MAP-01 v1/v2) vs. direct New $\rightarrow$ Scheduled for "Site inspection only" (SRC-MAP-01 annotation).
   - *Required Outcome:* Unknown / Disputed path.

---

## 5. Requirements Traceability Matrix (RTM)

| Source ID | Requirement ID | Backlog Item / Decision ID | Acceptance Criteria / Item Status |
| :--- | :--- | :--- | :--- |
| SRC-DOC-01<br>SRC-PPT-01 | REQ-INT-01 | US-INT-01 | Elaborated (Ready) |
| SRC-DOC-01 | REQ-INT-02 | US-INT-02 | Elaborated (Ready) |
| SRC-DOC-01 | REQ-INT-03 | DEC-INT-01 | Blocked (Required outcome Unknown) |
| SRC-DOC-01 | REQ-INT-04 | US-INT-02 | Elaborated (Ready) |
| SRC-DOC-01<br>SRC-XLS-01 | REQ-TAX-01 | US-INT-03 | Elaborated (Ready) |
| SRC-XLS-01 | REQ-TAX-02 | US-INT-03 | Elaborated (Ready) |
| SRC-XLS-01<br>SRC-MAP-01 | REQ-ROU-01 | US-ROU-01 | Elaborated (Ready) |
| SRC-DOC-01<br>SRC-XLS-01 | REQ-APR-01 | US-APR-01 | Elaborated (Ready) |
| SRC-DOC-01<br>SRC-XLS-01 | REQ-DOC-01 | DEC-DOC-01 | Blocked (Disputed source conflict) |
| SRC-DOC-01<br>SRC-XLS-01 | REQ-TIM-01 | DEC-TIM-01 | Blocked (Disputed source conflict) |
| SRC-DOC-01 | REQ-ACC-01 | US-ACC-01 | Elaborated (Ready) |
| SRC-DOC-01 | REQ-ACC-02 | DEC-ACC-01 | Blocked (Required outcome Unknown) |
| SRC-DOC-01 | REQ-KEY-01 | US-KEY-01 | Elaborated (Ready) |
| SRC-DOC-01 | REQ-KEY-02 | DEC-KEY-01 | Blocked (Disputed precondition syntax) |
| SRC-DOC-01 | REQ-LIF-01 | US-LIF-01 | Elaborated (Ready) |
| SRC-DOC-01 | REQ-LIF-02 | US-LIF-02 | Elaborated (Ready) |
| SRC-DOC-01 | REQ-LIF-03 | US-LIF-03 | Elaborated (Ready) |
| SRC-DOC-01<br>SRC-MAP-01 | REQ-LIF-04 | DEC-LIF-01 | Blocked (Disputed source lifecycle) |
| SRC-MAP-01 | N/A (Process Map Annotation 1) | DEC-MAP-01 | Blocked (Sourced Open Question) |
| SRC-MAP-01 | N/A (Process Map Annotation 2) | DEC-MAP-02 | Blocked (Sourced Open Question) |
| SRC-MAP-01 | N/A (Process Map Annotation 3) | DEC-MAP-03 | Blocked (Sourced Open Question) |
| SRC-MAP-01 | N/A (Process Map Annotation 4) | DEC-MAP-04 | Blocked (Sourced Open Question) |
| SRC-PPT-01 | REQ-TGT-01 | TGT-LIF-01 | Preserved Target State (Candidate) |
| SRC-PPT-01 | REQ-TGT-02 | TGT-LIF-02 | Preserved Target State (Candidate) |

---

## 6. Source-Created Contradictions, Ambiguities, and Unresolved Decisions

Every item listed below maps directly to an explicit conflict, unknown outcome, or annotation created by the source artifacts:

### 1. DEC-DOC-01: Mandatory Supporting Document Rules vs. Catalogue Matrix
- **Sourced Conflict**: SRC-DOC-01 states MOP and SWMS uploads are mandatory on the RFC form. SRC-XLS-01 specifies activity-specific booleans (`MOP Required?`, `SWMS Required?`, `Release Notes Required?`) where some activities evaluate to `false` for MOP and/or SWMS.
- **Unresolved Dimension**: Does the RFC form enforce a global mandatory upload or defer dynamically to the catalogue boolean flags?

### 2. DEC-TIM-01: Lead-Time Formulas vs. Activity Catalogue Values
- **Sourced Conflict**: SRC-DOC-01 defines baseline lead-time calculation formulas by Change Type and impact. SRC-XLS-01 specifies distinct lead-time day numbers (e.g. Core Motorola Upgrade = $25 + \text{days to next CAB}$; CCEP Integration = $54 + \text{days to next CAB}$).
- **Unresolved Dimension**: Which artifact governs lead-time calculation when catalogue values differ from specification baseline formulas?

### 3. DEC-KEY-01: CyberKey Serial Field (Field 69) Conditional Display Precondition
- **Sourced Contradiction**: SRC-DOC-01 validation note contains conflicting syntax: *"Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68."*
- **Unresolved Dimension**: Is Field 69 displayed when Field 67 = Yes or when Field 67 = No (in conjunction with Field 68 = CyberKey)?

### 4. DEC-INT-01: Multi-Company Filtering Policy
- **Sourced Ambiguity**: SRC-DOC-01 establishes that Change Agents can be associated with multiple companies, but establishes no set-handling policy.
- **Unresolved Dimension**: How are catalogue entries presented/filtered when a user has multiple company associations (e.g. union of catalogues, mandatory company picker, primary company default)?

### 5. DEC-ACC-01: Minimum Crew Requirements Specification
- **Sourced Ambiguity**: SRC-DOC-01 states that some Work Types have minimum crew requirements, but specifies neither the crew sizes nor the associated validation rules.
- **Unresolved Dimension**: Which specific Work Types enforce minimum crew sizes, and what are the required numbers?

### 6. DEC-LIF-01: Standard Change Lifecycle Progression
- **Sourced Conflict**: SRC-MAP-01 v1/v2 shows Standard Changes progressing automatically New $\rightarrow$ Assess $\rightarrow$ Authorise $\rightarrow$ Scheduled. An annotation on the same map states "Site inspection only" goes directly New $\rightarrow$ Scheduled.
- **Unresolved Dimension**: Does Standard Change state progression include Assess and Authorise states, or do some/all Standard Changes transition directly from New to Scheduled?

### 7. DEC-MAP-01: Flagged Poor-Performance Change Creation Policy
- **Sourced Question (SRC-MAP-01 Annotation 1)**: *"For user/org that has been flagged for poor performance or bad change practice. Can they proceed with change creation."*
- **Unresolved Dimension**: Can flagged users/organisations initiate change requests?

### 8. DEC-MAP-02: Post-Site Visit Task Quota and Auto-Close SLAs
- **Sourced Question (SRC-MAP-01 Annotation 2)**: *"Post site visit tasks – Quota? 10% action – 90% Auto close? SLAs to be defined."*
- **Unresolved Dimension**: What are the post-site visit task quota percentages and auto-close SLA parameters?

### 9. DEC-MAP-03: System Trigger for Task-Based Change Approval
- **Sourced Question (SRC-MAP-01 Annotation 3)**: *"Question – SNOW, Appian or other? Change task trigger a change approval."*
- **Unresolved Dimension**: Which system (ServiceNow, Appian, or other) handles the trigger for task-based change approvals?

### 10. DEC-MAP-04: Minor Date Modifications State Transition Path
- **Sourced Question (SRC-MAP-01 Annotation 4)**: *"If minor change to change (such as date changes) move to Authorize (Or new state… such as 'Amend'.) TBD."*
- **Unresolved Dimension**: When minor date changes occur, does the CR transition to Authorise, a new 'Amend' state, or remain in its current state subject to conflict checking?

---

## 7. Completeness and Readiness Assessment

```
Integrated Change Intake & Site Access Capability
├── Implementation-Ready Core (Confirmed)
│   ├── Intake & Record Linkage (Appian RFC -> ServiceNow CHG)
│   ├── Privileged Catalogue Access (Change Manager & MNP Service Desk view all)
│   ├── 4-Tier Activity Taxonomy & Assignment Group Routing / Fallback (PSN Helpdesk)
│   ├── Change Classification Approval Routing (Standard skip, Minor CM, Sig CAB, Major CAB+TAEC)
│   ├── Implement State Date Locking (Planned Start locked, Planned End amendable)
│   ├── Scheduled Timeout Auto-Closure (No Show + Cancel Site Access)
│   ├── Implement Timeout Auto-Closure (Set Actual End, NOCC task, Review state, Close)
│   ├── Site Access Work Type Presence & Visitor Qualification Enrolment
│   └── Base Site Key Field Capture (Field 67 boolean, Field 68 type)
│
├── Sourced Unresolved / Disputed Areas (Blocked from Build)
│   ├── DEC-DOC-01: Document upload mandatory enforcement vs. matrix booleans
│   ├── DEC-TIM-01: Baseline lead-time formulas vs. catalogue lead-time day numbers
│   ├── DEC-KEY-01: Field 69 CyberKey serial conditional display syntax glitch
│   ├── DEC-INT-01: Multi-company agent catalogue set-handling policy
│   ├── DEC-ACC-01: Work type minimum crew threshold definitions
│   ├── DEC-LIF-01: Standard change automatic state progression path
│   └── DEC-MAP-01 to 04: Process map WIP draft annotations (flagged users, quotas, trigger system, amend state)
│
└── Target-State Concepts (Candidate / Non-Mandatory)
    ├── TGT-LIF-01: First site visit attendance triggering Implement state
    └── TGT-LIF-02: Final site visit attendance creating NOCC task & populating Actual End Date
```

### Readiness Summary
- **Implementation-Ready**: Core RFC creation, record linking, single-company/privileged catalogue filtering, 4-tier taxonomy structure, assignment routing and PSN Helpdesk fallback, Change Type approval matrix, Implement state start date locking, Scheduled state No Show timeout closure, Implement state NOCC task timeout closure, site access work type visitor qualification enforcement, and base key field rendering.
- **Blocked / Requires Source Clarification**: Resolving the 10 source-created decision items (precedence between Word spec and Excel catalogue for documents and lead times, Field 69 validation condition logic, multi-company handling policy, crew size rules, Standard Change lifecycle state alignment, and the 4 draft process map questions).
- **Target-State (Candidate)**: Site visit triggers for Implement state progression and post-implementation NOCC task generation (preserved at source abstraction).
