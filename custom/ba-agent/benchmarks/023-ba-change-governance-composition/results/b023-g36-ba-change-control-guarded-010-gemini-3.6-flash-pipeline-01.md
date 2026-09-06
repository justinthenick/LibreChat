# BA Specialist Pipeline Result

- Pipeline: `Benchmark 023 — Control: Composite BA + Change Readiness`
- Model: `gemini-3.6-flash`
- Status: `incomplete`
- Run ID: `b023-g36-ba-change-control-guarded-010`
- Total prompt tokens: `2959`
- Total candidate tokens: `3408`
- Total thought tokens: `4780`
- Total tokens: `11147`

---

## ba-delivery — Composite BA Delivery Analyst v0.2

# BA Delivery Package — NimbusHR Identity Change

---

## Stage 1 — Requirements Analysis

### Overall Readiness State
**Partially Ready**

The core business objective and security requirement (moving workforce access for matched employee accounts to corporate identity with MFA) are clearly defined. However, full implementation readiness is blocked by unverified tenant capabilities for the proposed federation mechanism, 17 unresolved employee identities, an open dispute regarding contractor accounts with an unknown decision owner, unapproved cutover/backout targets, and an unapproved change record.

---

### Requirement & Constraint Register

| ID | Category | Description | Source / Proposer | Evidence Class | Requirement Status | Decision Owner |
|---|---|---|---|---|---|---|
| **REQ-01** | Functional | Transition workforce access for NimbusHR from local passwords to corporate identity enforcing the organisation's existing MFA policy. | Security Standard / Business Objective | Explicit | Confirmed | N/A |
| **REQ-02** | Proposed Mechanism | Use Entra enterprise application with SAML federation for NimbusHR identity integration. | Identity Team | Proposed | Candidate | Unknown |
| **REQ-03** | Functional / Data | Map employee accounts for corporate identity access (603 matched employee accounts confirmed; 17 accounts pending identity resolution). | Draft user-mapping spreadsheet | Explicit (603 matched) / Unknown (17 unmatched) | Confirmed (603 accounts) / Unknown (17 accounts) | Unknown |
| **REQ-04** | Functional Scope | Determine identity model for contractor access (HR Ops proposes local accounts; Security proposes corporate guest identities). | HR Operations vs Security | Disputed | Disputed | Unknown |
| **CON-01** | Security Constraint | Workforce access to SaaS applications containing employee data must use corporate identity and existing MFA policy. | Security Standard | Explicit | Confirmed | N/A |
| **CON-02** | Process Constraint | Production implementation of a customer- or workforce-impacting authentication change requires an approved change record prior to execution. | Local Change Policy | Explicit | Confirmed | Unknown (Named Change Authority not identified) |
| **TGT-01** | Planning Target | Target completion before 30 November prior to the annual audit cycle. | Head of HR | Explicit | Target (Non-binding) | N/A |
| **TGT-02** | Execution Target | Production cutover proposed for Saturday at 22:00. | Release Manager | Proposed | Candidate / Target (Unapproved window) | Unknown |
| **TGT-03** | Service Target | 45-minute recovery target if authentication change must be backed out. | Service Desk | Proposed | Target (Uncommitted, mechanics undesigned) | Unknown |
| **DEF-01** | Deferred Scope | Automated user provisioning and deprovisioning via SCIM for Phase 2. | Source packet suggestion | Proposed | Deferred | N/A |

---

### Dependencies, Risks, and Open Questions

- **DEP-01 (Technical Dependency):** Verification of NimbusHR Enterprise plan entitlement and SAML feature capability/compatibility within the organisation's tenant.
- **DEP-02 (Governance Dependency):** Submission and approval of a formal change record and production execution window.
- **RSK-01 (Operational Risk):** Authentication disruption or access denial for the 17 unresolved employee accounts if cutover occurs prior to identity resolution.
- **OQ-01 (Open Question):** Who holds the authority to decide contractor identity policy (HR Operations vs Security)?
- **OQ-02 (Open Question):** What is the applicable Change Authority and change pathway (Normal Change vs existing Standard Change template) for this record?

---

### Stage 1 Handoff Summary
- **Confirmed Requirements / Constraints:** REQ-01, REQ-03 (603 matched accounts), CON-01, CON-02.
- **Candidate / Proposed Mechanisms:** REQ-02 (SAML / Entra integration).
- **Disputed / Unknown Items:** REQ-04 (Contractor access model; Decision owner: Unknown), REQ-03 (17 unmatched accounts).
- **Planning & Operational Targets:** TGT-01 (30 Nov target date), TGT-02 (Sat 22:00 cutover window), TGT-03 (45-min recovery target).
- **Deferred Work:** DEF-01 (Phase 2 SCIM provisioning).

---

## Stage 2 — Delivery Decomposition

### Work Item Breakdown

#### Epic / Capability 1: Workforce Corporate Identity & MFA Integration
*Upstream Traceability: REQ-01, CON-01*

- **US-01: Employee Corporate Identity Authentication (Matched Accounts)**
  - *Type:* User Story
  - *Upstream Trace:* REQ-01, REQ-03, CON-01
  - *Status:* **Ready** (Applicable to the 603 confirmed matched employee accounts)
  - *Description:* Enable workforce access to NimbusHR using corporate identity integrated with the existing corporate MFA policy, replacing local password authentication for matched accounts.

- **SPK-01: NimbusHR Tenant SAML Capability & Compatibility Spike**
  - *Type:* Spike / Discovery Item
  - *Upstream Trace:* REQ-02, DEP-01
  - *Status:* **Ready for Discovery**
  - *Description:* Verify whether the organization's NimbusHR tenant includes SAML federation entitlement and whether the proposed Entra configuration is compatible.

- **CAN-01: Entra / SAML Single Sign-On Configuration**
  - *Type:* Candidate Item
  - *Upstream Trace:* REQ-02, SPK-01
  - *Status:* **Candidate** (Blocked pending outcome of SPK-01)
  - *Description:* Configure Entra enterprise application SAML federation for NimbusHR once capability and entitlement are verified.

- **SPK-02: Unmatched Accounts Identity Resolution Discovery**
  - *Type:* Spike / Discovery Item
  - *Upstream Trace:* REQ-03, RSK-01
  - *Status:* **Ready for Discovery**
  - *Description:* Investigate and resolve corporate identity mapping for the 17 unmatched employee accounts.

#### Governance & Change Governance Items

- **DEC-01: Contractor Identity Strategy Authority Decision**
  - *Type:* Decision Item
  - *Upstream Trace:* REQ-04, OQ-01
  - *Status:* **Blocked / Disputed** (Decision owner: Unknown)
  - *Description:* Resolve dispute between HR Operations (local accounts) and Security (corporate guest identities). Downstream implementation remains blocked until an authorized decision owner is identified and a decision rendered.

- **CNI-01: Change Record Compliance Constraint**
  - *Type:* Enabler / Constraint Item
  - *Upstream Trace:* CON-02, DEP-02, OQ-02
  - *Status:* **Confirmed Constraint**
  - *Description:* Ensure a formal change record is submitted and approved by the designated Change Authority prior to production implementation.

#### Non-Binding Targets & Deferred Scope

- **TGT-01: Target Delivery Schedule (Before 30 November)**
  - *Type:* Planning Target Item
  - *Upstream Trace:* TGT-01
  - *Status:* **Non-binding Target** (Informational planning target; not a committed delivery deadline)

- **TGT-02: Proposed Cutover Execution Window (Saturday 22:00)**
  - *Type:* Candidate Execution Target
  - *Upstream Trace:* TGT-02, DEP-02
  - *Status:* **Unapproved Target** (Subject to change record approval)

- **TGT-03: Backout Recovery Time Target (45 Minutes)**
  - *Type:* Quality Target Item
  - *Upstream Trace:* TGT-03
  - *Status:* **Non-binding Target** (Target duration only; backout mechanics undesigned)

- **DEF-01: Automated SCIM Provisioning / Deprovisioning**
  - *Type:* Deferred Item
  - *Upstream Trace:* DEF-01
  - *Status:* **Deferred** (Out of scope for current cutover; assigned to Phase 2)

---

### Stage 2 Handoff Summary
- **Ready for Criteria Elaboration:** US-01 (Matched employee corporate authentication), CNI-01 (Change record compliance constraint).
- **Blocked / Candidate / Disputed / Deferred (No committed criteria):**
  - SPK-01 & SPK-02 (Discovery items; outcomes unverified)
  - CAN-01 (Candidate configuration; conditional on SPK-01)
  - DEC-01 (Disputed contractor access; Decision owner: Unknown)
  - TGT-01, TGT-02, TGT-03 (Targets; non-binding)
  - DEF-01 (Deferred to Phase 2)

---

## Stage 3 — Acceptance-Criteria Elaboration

### Committed Acceptance Criteria

#### Item: US-01 — Employee Corporate Identity Authentication (Matched Accounts)
*Upstream Trace: US-01 | REQ-01, REQ-03, CON-01*

- **AC-01.1 (Mandatory Outcome):** Workforce access to NimbusHR for matched employee accounts must authenticate using corporate identity, enforcing the organisation's existing MFA policy.
  - *Traceability:* US-01 -> REQ-01, CON-01
- **AC-01.2 (Scope Boundary):** Corporate identity authentication applies to the 603 matched employee accounts identified in the verified user mapping.
  - *Traceability:* US-01 -> REQ-03
- **AC-01.3 (Derived Boundary):** NimbusHR-local password authentication must not be used for workforce access by matched employee accounts.
  - *Traceability:* US-01 -> REQ-01

#### Item: CNI-01 — Change Record Compliance Constraint
*Upstream Trace: CNI-01 | CON-02*

- **AC-CNI-01 (Process Pre-condition):** Production implementation of the authentication change must occur only when an approved change record exists for the change.
  - *Traceability:* CNI-01 -> CON-02

---

### Non-Committed / Preserved Exclusions (No AC Elaborated)

1. **SAML / Entra Configuration Details (CAN-01 / REQ-02):** Excluded from committed AC pending outcome of SPK-01.
2. **17 Unmatched Employee Accounts (SPK-02 / REQ-03):** Excluded from committed AC pending identity resolution.
3. **Contractor Identity Model (DEC-01 / REQ-04):** Excluded from committed AC due to unresolved dispute and unknown decision owner.
4. **Cutover Window and Recovery Target (TGT-02, TGT-03):** Excluded from pass/fail criteria; remain unapproved/uncommitted targets.
5. **Phase 2 SCIM Integration (DEF-01):** Excluded; explicitly deferred.

---

### Stage 3 Handoff Summary
- **Ready AC IDs for Test Derivation:** AC-01.1, AC-01.2, AC-01.3, AC-CNI-01.
- **Conditional / Non-Ready Areas:** Technical protocol specifics, unmatched account access, contractor access rules, execution timing, backout mechanics, and SCIM features remain non-committed and untestable as functional pass/fail criteria.

---

## Stage 4 — Behavioural Test / Assurance Derivation

### Derived Test Cases

#### Test Case ID: TC-01 — Authenticate Matched Employee Account via Corporate Identity
- **AC Reference:** AC-01.1, AC-01.2
- **Delivery Item Reference:** US-01
- **Upstream Traceability:** REQ-01, REQ-03, CON-01
- **Initial Condition:** An employee account is listed among the 603 verified matched accounts.
- **Action / Trigger:** The matched employee initiates authentication to NimbusHR.
- **Expected Outcome:** Authentication is executed via corporate identity with the organisation's existing MFA policy enforced.

#### Test Case ID: TC-02 — Non-reliance on Local Passwords for Matched Accounts
- **AC Reference:** AC-01.3
- **Delivery Item Reference:** US-01
- **Upstream Traceability:** REQ-01
- **Initial Condition:** An employee account is listed among the 603 verified matched accounts.
- **Action / Trigger:** An attempt is made to authenticate to NimbusHR using local password credentials for the matched account.
- **Expected Outcome:** Access using NimbusHR-local passwords is not permitted for the matched account.

---

### Assurance Checks (Conditional Process Constraints)

#### Assurance Check ID: AC-CHK-01 — Pre-Implementation Approved Change Record Verification
- **AC Reference:** AC-CNI-01
- **Delivery Item Reference:** CNI-01
- **Upstream Traceability:** CON-02
- **Assurance Condition (WHAT must hold):** Prior to production execution of the NimbusHR authentication change, an approved change record must exist.
- **Execution Status:** **Conditional Assurance Check** (Execution blocked until change record is formally submitted and approved by the Change Authority).

---

### Untested / Preserved Non-Ready Scope

- **SAML Technical Protocol Execution:** Untestable until SPK-01 verifies tenant enablement and compatibility.
- **17 Unmatched Accounts:** Untestable until identity mapping is completed.
- **Contractor Authentication:** Untestable due to ongoing policy dispute (Decision owner: Unknown).
- **Saturday 22:00 Window / 45-min Recovery:** Untestable as binding criteria (non-committed targets without approved backout design).
- **Automated SCIM Provisioning:** Untestable (Deferred to Phase 2).

---

## End-to-End Traceability Summary

| Upstream ID | Stage 1 Status | Stage 2 Delivery Item | Stage 2 Status | Stage 3 AC ID | Stage 4 Test / Assurance ID | Overall Coverage Status |
|---|---|---|---|---|---|---|
| **REQ-01** | Confirmed | US-01 | Ready | AC-01.1, AC-01.3 | TC-01, TC-02 | Covered |
| **REQ-02** | Candidate | SPK-01 / CAN-01 | Discovery / Candidate | None (Excluded) | None (Excluded) | Pending Discovery |
| **REQ-03 (603)** | Confirmed | US-01 | Ready | AC-01.2 | TC-01 | Covered |
| **REQ-03 (17)** | Unknown | SPK-02 | Discovery | None (Excluded) | None (Excluded) | Pending Discovery |
| **REQ-04** | Disputed | DEC-01 | Blocked | None (Excluded) | None (Excluded) | Blocked (Disputed) |
| **CON-01** | Confirmed | US-01 | Ready | AC-01.1 | TC-01 | Covered |
| **CON-02** | Confirmed | C

---

## change-readiness — Prepare Solution / Change Readiness v0.2

_No model output._
