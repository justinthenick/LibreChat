# BA Specialist Pipeline Result

- Pipeline: `Benchmark 023 — Candidate: Composite BA + Change Readiness + ITIL`
- Model: `gemini-3.5-flash`
- Status: `success`
- Run ID: `b023-g35-ba-change-itil-guarded-015`
- Total prompt tokens: `14260`
- Total candidate tokens: `9500`
- Total thought tokens: `11274`
- Total tokens: `35034`

---

## ba-delivery — Composite BA Delivery Analyst v0.2

# BA Delivery Package: NimbusHR Identity Change

---

## Stage 1 — Requirements Analysis

### Overall Readiness: Partially Ready
*The core security mandate is clear, but critical technical capabilities (SAML enablement on the tenant), user mapping completeness, contractor scope, and change approvals remain unverified, disputed, or unapproved.*

### Requirement Register

| ID | Category | Description | Source / Proposer | Evidence Class | Status | Decision Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | Functional | Stop relying on NimbusHR-local passwords for employees and migrate workforce access to corporate identity. | Head of HR / Security Standard | Explicit | Confirmed | N/A |
| **REQ-02** | Security | Workforce access to NimbusHR must enforce the organisation's existing MFA policy. | Security Standard | Explicit | Confirmed | N/A |
| **REQ-03** | Mechanism | Use Entra ID enterprise application with SAML federation for authentication. | Identity Team | Proposed | Candidate | Unknown |
| **REQ-04** | Functional | Map and resolve employee accounts for corporate identity access (603 currently matched, 17 currently unmatched). | Draft User-Mapping Spreadsheet | Explicit | Partially Ready | Unknown |
| **REQ-05** | Scope | Contractor authentication model (HR Ops proposes local accounts; Security proposes corporate guest identities). | HR Operations / Security | Disputed | Disputed | Unknown |
| **REQ-06** | Functional | Automated provisioning and deprovisioning via SCIM (Phase 2). | Stakeholder Suggestion | Proposed | Deferred | Unknown |

### Process and Security Constraints

| ID | Category | Constraint Description | Source / Proposer | Evidence Class | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CON-01** | Schedule | Complete the identity change before 30 November (prior to the December annual audit cycle). | Head of HR | Explicit | Target (Non-binding) |
| **CON-02** | Release | Production cutover window proposed for Saturday at 22:00. | Release Manager | Proposed | Candidate (Unapproved) |
| **CON-03** | Recovery | Achieve a 45-minute recovery target (backout) if the authentication change fails. | Service Desk | Proposed | Target (Non-binding) |
| **CON-04** | Governance | An approved change record is required before production implementation of workforce-impacting authentication changes. | Local Change Policy | Explicit | Confirmed |

---

### Stage 1 — Handoff Summary to Stage 2
* **Confirmed/Ready for Decomposition**: `REQ-01`, `REQ-02`, `REQ-04` (603 matched accounts), `CON-04`.
* **Partially Ready / Candidate**: `REQ-03` (SAML/Entra mechanism), `REQ-04` (17 unmatched accounts), `CON-02` (Cutover window).
* **Disputed / Blocked**: `REQ-05` (Contractor access).
* **Deferred**: `REQ-06` (SCIM Phase 2).
* **Targets (Non-binding)**: `CON-01` (30 Nov date), `CON-03` (45-min recovery).

---

## Stage 2 — Delivery Decomposition

### Work-Item Registry

```
[EPIC-01: NimbusHR Corporate Identity Integration] (Confirmed)
  ├── [SPIKE-01: Verify NimbusHR SAML & Entra Compatibility] (Confirmed Spike)
  ├── [STORY-01: Map and Migrate 603 Matched Employee Accounts] (Ready)
  ├── [DISCOVERY-01: Resolve 17 Unmatched Employee Accounts] (Partially Ready)
  ├── [DECISION-01: Contractor Identity Authentication Model] (Disputed / Blocked)
  ├── [TASK-01: Draft Production Cutover and Backout Plan] (Candidate)
  └── [TASK-02: Change Record Submission and Approval] (Candidate)

[DEFERRED-01: Phase 2 SCIM Automated Provisioning] (Deferred)
```

### Work-Item Details

#### EPIC-01: NimbusHR Corporate Identity Integration
* **Type**: Epic / Capability
* **Status**: Confirmed
* **Upstream Tracing**: `REQ-01`, `REQ-02`
* **Description**: Transition employee authentication from local passwords to corporate identity with MFA enforcement.

#### SPIKE-01: Verify NimbusHR SAML & Entra Compatibility
* **Type**: Spike / Discovery Item
* **Status**: Confirmed
* **Upstream Tracing**: `REQ-03`
* **Description**: Verify if the organisation's NimbusHR tenant has the Enterprise plan SAML feature enabled and confirm compatibility with Entra ID.

#### STORY-01: Map and Migrate 603 Matched Employee Accounts
* **Type**: User Story
* **Status**: Ready
* **Upstream Tracing**: `REQ-04`
* **Description**: Configure authentication mapping for the 603 successfully matched employee accounts identified in the draft mapping spreadsheet.

#### DISCOVERY-01: Resolve 17 Unmatched Employee Accounts
* **Type**: Spike / Discovery Item
* **Status**: Partially Ready
* **Upstream Tracing**: `REQ-04`
* **Description**: Investigate and resolve the identity mapping for the remaining 17 unmatched accounts in the draft spreadsheet.

#### DECISION-01: Contractor Identity Authentication Model
* **Type**: Decision Item
* **Status**: Disputed (Blocked)
* **Upstream Tracing**: `REQ-05`
* **Description**: Resolve the conflict between HR Operations (local accounts) and Security (corporate guest identities). 
* **Decision Owner**: Unknown

#### TASK-01: Draft Production Cutover and Backout Plan
* **Type**: Technical Task
* **Status**: Candidate
* **Upstream Tracing**: `CON-02`, `CON-03`
* **Description**: Define the technical steps for the Saturday 22:00 cutover and design the backout mechanics to meet the 45-minute recovery target.

#### TASK-02: Change Record Submission and Approval
* **Type**: Technical Task
* **Status**: Candidate
* **Upstream Tracing**: `CON-04`
* **Description**: Prepare and submit the change record for approval by the Change Authority prior to production implementation.

#### DEFERRED-01: Phase 2 SCIM Automated Provisioning
* **Type**: Deferred Item
* **Status**: Deferred
* **Upstream Tracing**: `REQ-06`
* **Description**: Automated provisioning/deprovisioning via SCIM. Out of scope for current cutover.

---

### Stage 2 — Handoff Summary to Stage 3
* **Ready for Acceptance Criteria**: `EPIC-01` (Core authentication requirements), `SPIKE-01` (SAML verification), `STORY-01` (603 matched accounts), `DISCOVERY-01` (17 unmatched accounts).
* **Blocked / Candidate / Deferred (No committed criteria)**: `DECISION-01` (Contractors), `TASK-01` (Cutover/Backout), `TASK-02` (Change approval), `DEFERRED-01` (SCIM).
* **Conditional Constraints to Preserve**: Change record must be approved before production implementation (`CON-04`).

---

## Stage 3 — Acceptance-Criteria Elaboration

### Acceptance Criteria Register

#### EPIC-01: NimbusHR Corporate Identity Integration
* **AC-EPIC-01-01**: Employee authentication requests must be redirected to the corporate identity provider. (Traces to: `EPIC-01`, `REQ-01`)
* **AC-EPIC-01-02**: Access to NimbusHR for employees must enforce the organisation's existing MFA policy during the corporate identity login flow. (Traces to: `EPIC-01`, `REQ-02`)
* **AC-BOUND-01 (Derived Boundary)**: Employee access via NimbusHR-local passwords must be disabled once corporate identity integration is active. (Traces to: `EPIC-01`, `REQ-01`)

#### SPIKE-01: Verify NimbusHR SAML & Entra Compatibility
* **AC-SPIKE-01-01**: Technical confirmation must be documented showing whether the organisation's NimbusHR tenant has the SAML feature enabled. (Traces to: `SPIKE-01`, `REQ-03`)
* **AC-SPIKE-01-02**: Technical compatibility between Entra ID SAML configuration and the NimbusHR tenant must be verified and documented. (Traces to: `SPIKE-01`, `REQ-03`)

#### STORY-01: Map and Migrate 603 Matched Employee Accounts
* **AC-STORY-01-01**: The 603 matched employee accounts identified in the draft mapping spreadsheet must successfully authenticate using their corporate identity. (Traces to: `STORY-01`, `REQ-04`)

#### DISCOVERY-01: Resolve 17 Unmatched Employee Accounts
* **AC-DISCOVERY-01-01**: A resolved identity mapping or remediation path for each of the 17 unmatched accounts must be documented and agreed upon by the identity and HR teams. (Traces to: `DISCOVERY-01`, `REQ-04`)

#### DECISION-01: Contractor Identity Authentication Model (Non-Committed / Boundary)
* **AC-BOUND-02 (Derived Boundary)**: Contractor accounts must remain on local NimbusHR authentication and must not be migrated to corporate identity until `DECISION-01` is formally resolved by an authorized decision owner. (Traces to: `DECISION-01`, `REQ-05`)

---

### Stage 3 — Handoff Summary to Stage 4
* **Ready for Test/Assurance Derivation**: `AC-EPIC-01-01`, `AC-EPIC-01-02`, `AC-BOUND-01`, `AC-SPIKE-01-01`, `AC-SPIKE-01-02`, `AC-STORY-01-01`, `AC-DISCOVERY-01-01`.
* **Preserved Boundaries (Non-committed/Untestable)**: Contractor authentication remains local (`AC-BOUND-02`).
* **Conditional Assurance Constraints**: Production implementation is blocked until an approved change record is verified (`CON-04`).

---

## Stage 4 — Behavioural Test / Assurance Derivation

### Test Cases (Ready Criteria)

#### TEST-01: Employee Redirection to Corporate Identity
* **Traceability**: Traces to `AC-EPIC-01-01`, `EPIC-01`, `REQ-01`
* **Condition**: An employee attempts to access NimbusHR.
* **Action**: The employee enters their corporate identifier or initiates the login flow.
* **Outcome**: The authentication session is redirected to the corporate identity provider login page.

#### TEST-02: Corporate MFA Enforcement
* **Traceability**: Traces to `AC-EPIC-01-02`, `EPIC-01`, `REQ-02`
* **Condition**: An employee authenticates via the corporate identity provider.
* **Action**: The employee completes primary authentication.
* **Outcome**: The corporate identity provider challenges the employee for MFA in accordance with the organisation's existing MFA policy before granting access to NimbusHR.

#### TEST-03: Mapped Employee Account Authentication
* **Traceability**: Traces to `AC-STORY-01-01`, `STORY-01`, `REQ-04`
* **Condition**: A user account belongs to the list of 603 matched employee accounts.
* **Action**: The user authenticates via the corporate identity provider.
* **Outcome**: The user is successfully logged into their corresponding NimbusHR account.

#### TEST-BOUND-01: Local Password Disablement
* **Traceability**: Traces to `AC-BOUND-01`, `EPIC-01`, `REQ-01`
* **Condition**: Corporate identity integration is active for employees.
* **Action**: An employee attempts to log in using a previously active NimbusHR-local password.
* **Outcome**: The login attempt is rejected, and local password authentication is unavailable for that employee account.

---

### Assurance Checks (Conditional Constraints)

#### ASSURE-CON-04: Pre-Implementation Change Record Verification
* **Traceability**: Traces to `CON-04`
* **Constraint State**: Prior to executing any production cutover activities, a change record for this authentication change must exist in the system of record.
* **Required Status**: The change record must be in an "Approved" state.
* **Verification Boundary**: The identity of the Change Authority and the specific approval workflow must be verified against local policy once identified (currently unknown).

---

### Non-Committed / Untestable Areas
* **Contractor Authentication**: Untestable. No test cases are derived for contractor login flows due to the unresolved dispute (`REQ-05`, `DECISION-01`).
* **SCIM Provisioning**: Untestable. Deferred to Phase 2 (`REQ-06`, `DEFERRED-01`).
* **Cutover and Backout Execution**: Untestable. The cutover window (`CON-02`) and backout plan (`CON-03`) are unapproved and lack technical designs.

---

## End-to-End Traceability Summary

| Stage 1 (REQ/CON) | Stage 2 (Work Item) | Stage 3 (Acceptance Criteria) | Stage 4 (Test / Assurance) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | `EPIC-01` | `AC-EPIC-01-01`, `AC-BOUND-01` | `TEST-01`, `TEST-BOUND-01` | Confirmed / Ready |
| **REQ-02** | `EPIC-01` | `AC-EPIC-01-02` | `TEST-02` | Confirmed / Ready |
| **REQ-03** | `SPIKE-01` | `AC-SPIKE-01-01`, `AC-SPIKE-01-02` | N/A (Spike/Discovery) | Confirmed Spike |
| **REQ-04** (603 accounts) | `STORY-01` | `AC-STORY-01-01` | `TEST-03` | Ready |
| **REQ-04** (17 accounts) | `DISCOVERY-01` | `AC-DISCOVERY-01-01` | N/A (Discovery) | Partially Ready |
| **REQ-05** | `DECISION-01` | `AC-BOUND-02` | N/A (Disputed) | Blocked / Disputed |
| **REQ-06** | `DEFERRED-01` | N/A | N/A | Deferred |
| **CON-01** | N/A | N/A | N/A | Target (Non-binding) |
| **CON-02** | `TASK-01` | N/A | N/A | Candidate (Unapproved) |
| **CON-03** | `TASK-01` | N/A | N/A | Target (Non-binding) |
| **CON-04** | `TASK-02` | N/A | `ASSURE-CON-04` | Confirmed Constraint |

---

## Solution & Change-Readiness Review

### 1. Solution Readiness Assessment
The solution is **not fully ready** for implementation due to several critical gaps:
* **Technical Feasibility Gap**: The proposed SAML/Entra integration (`REQ-03`) is unverified. We do not know if the organisation's NimbusHR tenant has the Enterprise plan or if SAML is enabled.
* **Scope Gap**: The contractor authentication model (`REQ-05`) is disputed. Proceeding without resolving this risks either locking contractors out or leaving a security vulnerability (local passwords) active.
* **Data Quality Gap**: 17 employee accounts (`REQ-04`) remain unmatched, risking immediate lockout for those individuals post-cutover.

### 2. Change-Readiness Gap Analysis
To satisfy the local Change Policy (`CON-04`) and prepare for a successful change review, the following artifacts must be produced and approved:
* **Approved Production Window**: The Saturday 22:00 window (`CON-02`) must be formally scheduled and approved.
* **Approved Backout Plan**: A detailed technical backout procedure must be designed to support the 45-minute recovery target (`CON-03`).
* **Change Authority Identification**: The specific Change Authority (e.g., a named role or board) must be identified to obtain the required pre-implementation approval.
* **Communications Plan**: Support and user communications must be finalized to manage the transition for the 620 employees.

---

## ITIL 4 Practice Alignment Assessment

### 1. Change Enablement
* **Change Classification**: Operations suggested this is "probably a Normal Change." Under ITIL 4, a **Normal Change** requires full scheduling, risk assessment, and authorization because it is not a pre-authorized Standard Change and no matching Standard Change template has been identified.
* **Policy Compliance**: The local Change Policy requirement for an approved change record prior to production implementation aligns with ITIL 4's focus on risk management and governance. Implementation cannot proceed as a "Standard Change" without an established, proven template.

### 2. Service Validation and Testing
* **Utility and Warranty**: The utility (what the service does) is defined by moving to corporate identity (`REQ-01`). The warranty (how the service performs) is defined by enforcing the MFA policy (`REQ-02`).
* **Spike-First Approach**: ITIL 4 advocates for reducing risk early. Executing `SPIKE-01` to verify SAML capability before scheduling the change record prevents the risk of scheduling a change that is technically impossible on the current subscription plan.

### 3. Information Security Management
* **Policy Alignment**: The requirement to enforce corporate MFA (`REQ-02`) directly supports Information Security Management practices by ensuring SaaS applications containing sensitive employee data align with corporate security standards.
* **Contractor Risk**: The contractor dispute (`REQ-05`) represents a security policy conflict. Leaving local accounts active for contractors bypasses corporate MFA, violating the security standard. This must be escalated to a security authority for resolution.

### 4. Identity and Access Management (IAM)
* **Account Lifecycle**: The 17 unmatched accounts (`REQ-04`) and the contractor guest-account lifecycle concerns (`REQ-05`) are core IAM practice challenges. ITIL 4 emphasizes that IAM must manage the full lifecycle of identities; leaving these unresolved introduces operational risk (lockouts) and security risk (orphaned accounts).

---

PIPELINE_HANDOFF_COMPLETE: BA_DELIVERY_4_STAGE

---

## change-readiness — Prepare Solution / Change Readiness v0.2

# Solution & Change-Readiness Handoff: NimbusHR Identity Change

---

## 1. Overall handoff readiness

*   **Solution/Design Review Readiness**: **Partially ready**
    *   *Justification*: The core workforce identity migration requirements (`REQ-01`, `REQ-02`) and the mapping for 603 employee accounts (`REQ-04` / `STORY-01`) are confirmed and decomposed with defined acceptance criteria and test designs. However, the technical mechanism (`REQ-03` SAML/Entra ID) remains a Candidate pending compatibility verification (`SPIKE-01`), 17 employee accounts remain unmatched (`DISCOVERY-01`), and the contractor authentication model is disputed (`REQ-05` / `DECISION-01`).
*   **Change Submission/Production Readiness**: **Not ready**
    *   *Justification*: Material prerequisites for Change Enablement review are absent. The change record (`TASK-02`) and the production cutover window (`CON-02`) are unapproved Candidates. The technical backout plan to meet the 45-minute recovery target (`CON-03`) has not been designed (`TASK-01`). No test execution evidence exists, and the specific Change Authority and approval workflow required by `CON-04` are currently Unknown.

---

## 2. Evidence ready for handoff

The following verified and confirmed evidence is ready to be handed over to downstream teams:

*   **Confirmed Scope and Constraints**:
    *   Migration of workforce access from local passwords to corporate identity (`REQ-01`).
    *   Enforcement of the organisation's existing MFA policy during corporate login (`REQ-02`).
    *   The governance requirement that an approved change record must exist prior to production implementation (`CON-04`).
*   **Ready Delivery Items**:
    *   `EPIC-01`: NimbusHR Corporate Identity Integration (Traces to: `REQ-01`, `REQ-02`).
    *   `SPIKE-01`: Verify NimbusHR SAML & Entra Compatibility (Traces to: `REQ-03`).
    *   `STORY-01`: Map and Migrate 603 Matched Employee Accounts (Traces to: `REQ-04`).
*   **Acceptance Criteria**:
    *   `AC-EPIC-01-01`: Redirection of employee authentication to the corporate identity provider.
    *   `AC-EPIC-01-02`: Enforcement of corporate MFA during login.
    *   `AC-BOUND-01`: Disablement of local password access for migrated employees.
    *   `AC-SPIKE-01-01` & `AC-SPIKE-01-02`: Documented technical confirmation of SAML enablement and Entra ID compatibility.
    *   `AC-STORY-01-01`: Successful corporate identity authentication for the 603 matched accounts.
    *   `AC-DISCOVERY-01-01`: Documented remediation path for the 17 unmatched accounts.
    *   `AC-BOUND-02`: Contractor accounts must remain on local authentication until `DECISION-01` is resolved.
*   **Test and Assurance Designs (No execution evidence supplied)**:
    *   `TEST-01`: Employee Redirection to Corporate Identity (Traces to: `AC-EPIC-01-01`).
    *   `TEST-02`: Corporate MFA Enforcement (Traces to: `AC-EPIC-01-02`).
    *   `TEST-03`: Mapped Employee Account Authentication (Traces to: `AC-STORY-01-01`).
    *   `TEST-BOUND-01`: Local Password Disablement (Traces to: `AC-BOUND-01`).
    *   `ASSURE-CON-04`: Pre-implementation verification of an approved change record (Traces to: `CON-04`).
*   **Explicit Decisions Made**: None. All key architectural, scheduling, and scope decisions remain Candidate, Disputed, or have Unknown decision owners.

---

## 3. Unresolved / non-committed register

*   **Disputed Decisions**:
    *   `REQ-05` / `DECISION-01`: Contractor authentication model. HR Operations proposes retaining local accounts; Security proposes corporate guest identities. (Decision Owner: `Unknown`).
*   **Unknown Values**:
    *   Decision Owner for `REQ-03` (SAML/Entra ID mechanism).
    *   Decision Owner for `REQ-04` (User mapping resolution).
    *   Decision Owner for `REQ-05` (Contractor model).
    *   Decision Owner for `REQ-06` (SCIM provisioning).
    *   Identity of the Change Authority and specific approval workflow for `CON-04`.
*   **Candidate Scope / Design**:
    *   `REQ-03`: Use of Entra ID enterprise application with SAML federation as the integration mechanism.
    *   `CON-02` / `TASK-01`: Production cutover window proposed for Saturday at 22:00.
    *   `TASK-02`: Change record submission and approval.
*   **Targets (Non-binding)**:
    *   `CON-01`: Complete the identity change before 30 November.
    *   `CON-03`: Achieve a 45-minute recovery target (backout) if the change fails.
*   **Deferred Items**:
    *   `REQ-06` / `DEFERRED-01`: Automated provisioning and deprovisioning via SCIM (Phase 2).
*   **Discovery / Spike Outcomes Still Required**:
    *   `SPIKE-01`: Technical verification of SAML enablement on the NimbusHR tenant and compatibility with Entra ID.
    *   `DISCOVERY-01`: Investigation and resolution of the 17 unmatched employee accounts.

---

## 4. Solution/design review handoff

Downstream solution and design reviews must account for the following outcomes and constraints:

*   **Redirection & MFA**: Employee authentication must redirect to the corporate identity provider and enforce the existing corporate MFA policy (`REQ-01`, `REQ-02`, `AC-EPIC-01-01`, `AC-EPIC-01-02`).
*   **Local Disablement**: Local password access must be disabled for employees once corporate identity integration is active (`AC-BOUND-01`).
*   **Contractor Isolation**: Contractor accounts must remain on local NimbusHR authentication and must not be migrated to corporate identity until the contractor model dispute is resolved (`AC-BOUND-02`).
*   **Unresolved Design Questions (To be answered downstream)**:
    *   *SAML Capability*: Does the organisation's NimbusHR tenant support and have SAML federation enabled? (Traces to: `SPIKE-01`).
    *   *Unmatched Accounts*: What is the agreed remediation path for the 17 unmatched employee accounts to prevent lockout? (Traces to: `DISCOVERY-01`).
    *   *Contractor Model*: What is the authorized authentication model for contractors? (Traces to: `DECISION-01`).

---

## 5. Change-readiness evidence matrix

| Evidence area | State | Evidence available | Missing / unresolved | Traceability |
| :--- | :--- | :--- | :--- | :--- |
| **Implementation Approach** | `Partial` | High-level scope defined in `EPIC-01` and `STORY-01` (603 matched accounts). | Technical configuration steps for SAML/Entra ID integration are unverified. | `REQ-01`, `REQ-03`, `REQ-04` |
| **Deployment/Backout Approach** | `Missing` | None. | Technical cutover steps and backout mechanics to meet the 45-minute recovery target are un-designed. | `CON-02`, `CON-03`, `TASK-01` |
| **Validation Evidence** | `Partial` | Test designs `TEST-01`, `TEST-02`, `TEST-03`, `TEST-BOUND-01` and assurance check `ASSURE-CON-04` are defined. | No test execution evidence or validation results are available. | `Stage 4 Test Cases` |
| **Operational/Support Readiness** | `Missing` | None. | Support transition, service desk procedures, and operational readiness evidence are not supplied. | N/A |
| **Communications** | `Missing` | None. | User and stakeholder communication plans for the migration of 620 employees are not supplied. | N/A |
| **Governance/Approvals** | `Partial` | `CON-04` establishes that an approved change record is required before production implementation. | Change record `TASK-02` is a candidate; Change Authority identity and approval workflow are unknown. | `CON-04`, `TASK-02`, `ASSURE-CON-04` |

---

## 6. Source-evidenced blockers / dependencies

The following blockers and dependencies are explicitly established by the supplied source material:

*   **Approved Change Record (Governance Gate)**: Production implementation is blocked until a change record is in an "Approved" state (`CON-04`, `ASSURE-CON-04`).
*   **Contractor Migration Block**: Contractor accounts must remain on local authentication and must not be migrated until `DECISION-01` is formally resolved by an authorized owner (`AC-BOUND-02`, `REQ-05`).
*   **SAML Compatibility Dependency**: Proceeding with the SAML/Entra ID integration design is dependent on verifying that the NimbusHR tenant has the SAML feature enabled and is compatible with Entra ID (`REQ-03`, `SPIKE-01`).
*   **Unmatched Accounts Dependency**: Migration of the 17 unmatched accounts is blocked until a remediation path is documented and agreed upon (`REQ-04`, `DISCOVERY-01`).

---

## 7. Missing downstream evidence

The following evidence categories are not present in the supplied material and remain to be established downstream (these are not promoted to mandatory gates unless explicitly required by the source):

*   **Technical Cutover and Backout Design**: The specific technical steps for the Saturday 22:00 cutover and the backout mechanics to achieve the 45-minute recovery target are to be established downstream (`TASK-01`, `CON-02`, `CON-03`).
*   **Test Execution Evidence**: Actual execution results for `TEST-01`, `TEST-02`, `TEST-03`, and `TEST-BOUND-01` are to be established downstream.
*   **Change Authority Identity**: The specific role, board, or workflow representing the Change Authority for `CON-04` is to be established downstream.
*   **Operational Support and Communications Plans**: Operational support procedures and user transition communications are to be established downstream.

---

## 8. Traceability summary

```
[Source-Evidenced Blockers & Constraints]
  ├── CON-04 (Approved Change Record) ──> Blocks Production Implementation (ASSURE-CON-04)
  └── REQ-05 (Contractor Dispute) ─────> Blocks Contractor Migration (AC-BOUND-02)

[Missing Downstream Evidence (To be established)]
  ├── SPIKE-01 Outcome ─────────────────> Required to confirm Candidate Mechanism (REQ-03)
  ├── DISCOVERY-01 Outcome ─────────────> Required to complete User Mapping (REQ-04)
  └── TASK-01 Technical Design ─────────> Required to address Cutover (CON-02) & Backout (CON-03)

[Non-Promoted Items (Preserved States)]
  ├── REQ-03 (SAML/Entra ID) ───────────> Remains CANDIDATE Mechanism
  ├── CON-02 (Saturday 22:00 Cutover) ──> Remains CANDIDATE Window
  ├── CON-01 (30 Nov Deadline) ─────────> Remains Non-binding TARGET
  ├── CON-03 (45-Min Recovery) ─────────> Remains Non-binding TARGET
  └── REQ-06 (SCIM Provisioning) ───────> Remains DEFERRED (Phase 2)
```

---

## 9. Recommended next review state

*   **Solution/Design Review**: **Partially Ready**
    *   *Justification*: The review can proceed to evaluate the 603 matched accounts migration and the test designs, but must first address the `SPIKE-01` compatibility outcomes and the `DECISION-01` contractor dispute.
*   **Change Enablement Review**: **Not Ready**
    *   *Justification*: Change Enablement review cannot proceed until the candidate change record (`TASK-02`) is drafted, the technical cutover/backout plan (`TASK-01`) is designed, and test execution evidence is available.

---

PIPELINE_HANDOFF_COMPLETE: CHANGE_READINESS

---

## itil-alignment — Assess ITIL Alignment v0.2

# ITIL 4 Alignment & Readiness Assessment: NimbusHR Identity Change

This assessment evaluates the supplied solution and change-readiness evidence against relevant ITIL 4 practice concepts. This is an alignment and readiness review, not a formal certification audit. It is designed to identify strengths, gaps, and key questions to support delivery and governance.

---

## 1. Assessment Scope and Overall Alignment Readiness

*   **Overall ITIL Alignment Readiness**: **Partially Aligned**
    *   *Justification*: The initiative demonstrates strong alignment with ITIL concepts of service definition, security policy enforcement, and structured test design. However, it is not yet ready for formal Change Enablement authorization. Key technical deployment details, configuration baselines, and operational support structures are currently unevidenced or remain candidate proposals.
*   **Change Enablement Readiness**: **Not Ready**
    *   *Justification*: While the requirement for formal governance is recognized (`CON-04`), the change record (`TASK-02`) remains a Candidate, the Change Authority is Unknown, and the technical backout plan required to meet the recovery target (`CON-03`) has not been designed (`TASK-01`).

---

## 2. Applicable ITIL Practice Map

The following ITIL 4 practices are materially relevant to this change scenario:

1.  **Change Enablement**: Materially relevant because local policy (`CON-04`) mandates an approved change record prior to production implementation. This practice governs risk, scheduling, and authorization.
2.  **Release Management**: Materially relevant because the change involves packaging and transitioning user access states (603 matched accounts, 17 unmatched accounts, and isolated contractor accounts) into an active service state.
3.  **Deployment Management**: Materially relevant because it governs the physical/logical transfer of the SAML/Entra ID integration and configuration changes into the production environment during the proposed cutover window (`CON-02`).
4.  **Service Configuration Management**: Materially relevant because the change alters user authentication pathways, identity provider relationships, and configuration items (CIs) associated with the NimbusHR service.
5.  **Information Security Management**: Materially relevant because the change directly implements corporate MFA policies (`REQ-02`) and alters authentication mechanisms (`REQ-01`, `REQ-05`).

---

## 3. Alignment Findings

The table below details the alignment of the supplied evidence against relevant ITIL practice concerns.

| Finding ID | ITIL Practice | Evidence / Condition | Status | Readiness Impact | Source Trace |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FIN-01** | Change Enablement | Governance requirement established: an approved change record must exist prior to production. | **Aligned / evidenced** | `No current blocker` (Governance rule is clear) | `CON-04`, `ASSURE-CON-04` |
| **FIN-02** | Change Enablement | Change record (`TASK-02`) is drafted but remains in a Candidate state; Change Authority and specific approval workflow are unresolved. | **Partially evidenced** | `Decision required` (Identify Change Authority) | `TASK-02`, `CON-04` |
| **FIN-03** | Change Enablement | Proposed cutover window (Saturday 22:00) is defined as a Candidate. | **Partially evidenced** | `Clarification required` (Schedule coordination) | `CON-02` |
| **FIN-04** | Release Management | Scope of release is defined (603 matched accounts) with clear boundary controls (contractors isolated). | **Aligned / evidenced** | `No current blocker` | `EPIC-01`, `STORY-01`, `AC-BOUND-02` |
| **FIN-05** | Release Management | 17 unmatched accounts remain unresolved, presenting a potential service disruption risk upon release. | **Partially evidenced** | `Readiness dependency` (Remediation path needed) | `DISCOVERY-01`, `REQ-04` |
| **FIN-06** | Deployment Management | Technical cutover steps and backout mechanics to meet the 45-minute recovery target are un-designed. | **Not evidenced** | `Clarification required` (Technical design outstanding) | `TASK-01`, `CON-03` |
| **FIN-07** | Service Configuration Management | SAML federation and Entra ID compatibility are Candidate mechanisms pending technical verification. | **Partially evidenced** | `Readiness dependency` (Spike completion required) | `REQ-03`, `SPIKE-01` |
| **FIN-08** | Information Security Management | Alignment with corporate MFA policy and disablement of local password access are defined with test designs. | **Aligned / evidenced** | `No current blocker` | `REQ-02`, `AC-BOUND-01`, `TEST-02`, `TEST-BOUND-01` |
| **FIN-09** | Information Security Management | Contractor authentication model is disputed between HR Operations and Security. | **Potential conflict** | `Decision required` (Resolve contractor model) | `REQ-05`, `DECISION-01` |

---

## 4. Readiness Dependencies, Decisions, and Evidence Gaps

This section classifies outstanding items based on their source-established status. Gaps are not promoted to mandatory gates unless explicitly required by the supplied source.

### Readiness Dependencies (Source-Established)
*   **SAML Compatibility Verification**: Proceeding with the integration design depends on the outcomes of `SPIKE-01` (`REQ-03`, `SPIKE-01`).
*   **Unmatched Accounts Remediation**: Migration of the 17 unmatched accounts is blocked until a remediation path is documented and agreed (`REQ-04`, `DISCOVERY-01`).
*   **Contractor Isolation**: Contractor accounts must remain on local authentication and must not be migrated until `DECISION-01` is resolved (`AC-BOUND-02`).

### Decisions Required (Source-Established)
*   **Contractor Authentication Model**: Resolution of the dispute between HR Operations and Security regarding local vs. corporate guest identities (`REQ-05`, `DECISION-01`). *Decision Owner: Unknown*.
*   **Change Authority Identification**: Identification of the specific role, board, or workflow representing the Change Authority authorized to approve `TASK-02` (`CON-04`). *Decision Owner: Unknown*.

### Clarifications Required (Relevant Gaps without Source-Mandated Gate Status)
*   **Technical Cutover & Backout Design**: The technical steps for cutover and the backout plan to address the 45-minute recovery target (`CON-03`) are currently un-designed (`TASK-01`). While ITIL recommends robust backout planning, the source does not explicitly establish this as a blocking pre-authorisation gate; clarification is required on whether this is a local policy requirement.
*   **Operational Support & Communications**: No operational support transition plans or user communication plans have been supplied. Clarification is required on whether these are local prerequisites for change approval.

---

## 5. Organisational-Policy vs. ITIL-Guidance Distinctions

To ensure governance remains traceable only to verified facts, we distinguish between generic ITIL guidance and explicit local policies:

*   **Change Authority**: ITIL guidance recommends defining a Change Authority based on risk and organizational context, but it does not mandate a specific role or a Change Advisory Board (CAB). Locally, the Change Authority for `CON-04` remains **Unknown**. We do not invent or assume a CAB or specific approver role.
*   **Change Record Requirement**: The requirement for an approved change record prior to production is an explicit local policy constraint (`CON-04`), not a generic ITIL mandate. This local rule is treated as a mandatory gate.
*   **Recovery Target**: The 45-minute recovery target (`CON-03`) is a non-binding **Target** in the source material. While ITIL practices support service continuity and risk reduction, we do not treat this target as a mandatory, blocking gate for change submission unless local policy explicitly defines it as such.

---

## 6. Focused Follow-Up Questions

The following questions are designed to resolve critical alignment and readiness uncertainties. They do not assume local policy requirements unless sourced.

1.  **Regarding Change Governance (`CON-04`, `TASK-02`)**: Who is the designated Change Authority or authorized decision-maker for approving this change record, and what is the specific approval workflow required?
2.  **Regarding Technical Compatibility (`SPIKE-01`)**: What are the results of the compatibility spike? Has SAML federation been successfully verified on the NimbusHR tenant?
3.  **Regarding Contractor Authentication (`DECISION-01`)**: Who is the authorized decision owner for resolving the contractor authentication model dispute, and what is the target date for this decision?
4.  **Regarding the Recovery Target (`CON-03`)**: Is the 45-minute recovery target a mandatory prerequisite for change approval, and has the technical backout design (`TASK-01`) been scheduled for review?
5.  **Regarding Unmatched Accounts (`DISCOVERY-01`)**: Who is the decision owner responsible for approving the remediation path for the 17 unmatched employee accounts?

---

## 7. Traceability Summary

The mapping below traces the findings of this ITIL alignment assessment back to the upstream source IDs:

```
[Upstream Source Constraints & Items]
  ├── CON-04 (Approved Change Record) ───────> FIN-01 (Change Enablement Governance)
  ├── TASK-02 (Change Record Candidate) ─────> FIN-02 (Unresolved Change Authorization)
  ├── CON-02 (Saturday Cutover Window) ──────> FIN-03 (Candidate Schedule Coordination)
  ├── STORY-01 (603 Matched Accounts) ───────> FIN-04 (Defined Release Scope)
  ├── DISCOVERY-01 (17 Unmatched Accounts) ──> FIN-05 (Release Disruption Risk)
  ├── TASK-01 / CON-03 (Backout & Recovery) ──> FIN-06 (Unevidenced Deployment Recovery)
  ├── SPIKE-01 (SAML/Entra Compatibility) ───> FIN-07 (Candidate Configuration Verification)
  ├── REQ-02 / AC-BOUND-01 (MFA & Passwords) ─> FIN-08 (Aligned Security Enforcement)
  └── REQ-05 / DECISION-01 (Contractors) ────> FIN-09 (Disputed Security Model)
```

---

PIPELINE_HANDOFF_COMPLETE: ITIL_ALIGNMENT
