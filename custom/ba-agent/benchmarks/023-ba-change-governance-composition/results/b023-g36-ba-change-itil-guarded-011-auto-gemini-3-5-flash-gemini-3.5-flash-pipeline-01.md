# BA Specialist Pipeline Result

- Pipeline: `Benchmark 023 — Candidate: Composite BA + Change Readiness + ITIL`
- Model: `gemini-3.5-flash`
- Status: `incomplete`
- Run ID: `b023-g36-ba-change-itil-guarded-011-auto-gemini-3-5-flash`
- Total prompt tokens: `2959`
- Total candidate tokens: `3465`
- Total thought tokens: `4723`
- Total tokens: `11147`

---

## ba-delivery — Composite BA Delivery Analyst v0.2

# BA Delivery Package: NimbusHR Identity Change

---

## Stage 1 — Requirements Analysis

### Overall Readiness Assessment
**Status: Partially Ready**
*The core business objective and security constraints are confirmed, but critical technical capabilities (SAML enablement/compatibility), user mappings (17 unresolved accounts), scope boundaries (contractor access dispute), and change management details (approved window, backout plan, Change Authority) remain unverified, unapproved, or disputed.*

### Requirement Register

| ID | Description | Source / Proposer | Evidence Class | Status | Confidence | Decision Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | Stop relying on NimbusHR-local passwords for employees and move workforce access to corporate identity. | Head of HR / Security Standard | Explicit | Confirmed | High | Unknown |
| **REQ-02** | Complete the authentication change before 30 November. | Head of HR | Proposed | Target | Medium | Unknown |
| **REQ-03** | Workforce access to SaaS applications containing employee data must use corporate identity and the organisation's existing MFA policy. | Security Standard | Explicit | Confirmed | High | Unknown |
| **REQ-04** | Use SAML federation via an Entra enterprise application. | Identity Team | Proposed | Candidate | Low | Unknown |
| **REQ-05** | Map employee accounts to corporate identities (603 currently matched, 17 requiring identity resolution). | Draft user-mapping spreadsheet | Explicit (Data-driven) | Partially Ready | Medium | Unknown |
| **REQ-06** | Contractor access model (HR Ops proposes local accounts; Security proposes corporate guest identities). | HR Operations vs. Security | Disputed | Disputed | Low | Unknown |
| **REQ-07** | Automated provisioning/deprovisioning through SCIM (Phase 2). | Suggested (Source unstated) | Proposed | Deferred | Low | Unknown |
| **REQ-08** | Execute production cutover on Saturday at 22:00. | Release Manager | Proposed | Candidate | Low | Unknown |
| **REQ-09** | Achieve a 45-minute recovery target if the authentication change needs to be backed out. | Service Desk | Proposed | Target | Low | Unknown |
| **REQ-10** | Process the deployment as a Normal Change (unless an existing Standard Change template is shown to apply). | Operations | Proposed | Candidate | Low | Unknown |

### Process & Security Constraints

| ID | Constraint Description | Source | Evidence Class | Status | Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CON-01** | An approved change record is required before production implementation of a customer- or workforce-impacting authentication change. | Local Change Policy | Explicit | Confirmed | High |

### Dependencies, Risks, and Open Questions
1. **Dependency (Technical)**: Verification of NimbusHR Enterprise plan SAML capability and tenant entitlement (`REQ-04`).
2. **Dependency (Data)**: Resolution of the 17 unmatched employee accounts (`REQ-05`).
3. **Risk (Security/Compliance)**: Implementing local contractor accounts (`REQ-06` HR Ops proposal) may violate the Security Standard (`REQ-03`) if contractors are deemed "workforce access to SaaS applications containing employee data."
4. **Open Question**: Who is the designated Change Authority with the power to approve the change record (`CON-01`) and resolve the contractor access dispute (`REQ-06`)?
5. **Open Question**: What are the technical backout mechanics required to support the 45-minute recovery target (`REQ-09`)?

---

### Stage 1 Handoff Summary
* **Confirmed / Ready**: `REQ-01`, `REQ-03`, `CON-01`
* **Partially Ready**: `REQ-05` (603 matched accounts are ready; 17 unmatched are blocked)
* **Target**: `REQ-02`, `REQ-09`
* **Candidate**: `REQ-04`, `REQ-08`, `REQ-10`
* **Disputed**: `REQ-06`
* **Deferred**: `REQ-07`

---

## Stage 2 — Delivery Decomposition

Only confirmed and partially ready items from Stage 1 are decomposed into active delivery work. Candidate, disputed, and deferred items are tracked as non-committed or blocked work items.

### Work Item Registry

| Work Item ID | Type | Title / Description | Traces to Stage 1 ID | Status |
| :--- | :--- | :--- | :--- | :--- |
| **CAP-01** | Epic / Capability | Corporate Identity Integration for NimbusHR | `REQ-01`, `REQ-03` | Confirmed |
| **SPIKE-01** | Spike / Discovery | Verify NimbusHR SAML Capability & Entra Compatibility | `REQ-04` | Confirmed |
| **STORY-01** | User Story | Map 603 Verified Employee Accounts to Corporate Identities | `REQ-05` | Ready |
| **DISC-01** | Discovery Item | Resolve 17 Unmatched Employee Accounts | `REQ-05` | Partially Ready (Blocked) |
| **DEC-01** | Decision Item | Resolve Contractor Access Model Dispute | `REQ-06` | Blocked (Decision Owner: Unknown) |
| **DEC-02** | Decision Item | Identify Change Authority and Approve Change Record | `CON-01`, `REQ-10` | Blocked (Decision Owner: Unknown) |
| **CAND-01** | Candidate Item | Configure Entra SAML Federation for NimbusHR | `REQ-04` | Candidate (Blocked by `SPIKE-01`) |
| **CAND-02** | Candidate Item | Schedule and Execute Production Cutover Window | `REQ-08` | Candidate (Blocked by `DEC-02`) |
| **CAND-03** | Candidate Item | Design and Test Backout Mechanics | `REQ-09` | Candidate |
| **DEF-01** | Deferred Item | Phase 2 SCIM Automated Provisioning | `REQ-07` | Deferred |

---

### Stage 2 Handoff Summary
* **Ready / Partially Ready for Criteria**: `CAP-01` (High-level capability), `SPIKE-01` (Technical verification), `STORY-01` (603 matched accounts).
* **Blocked / Candidate / Deferred / Unknown**: `DISC-01` (17 unmatched accounts), `DEC-01` (Contractor dispute), `DEC-02` (Change approval), `CAND-01` (SAML configuration), `CAND-02` (Cutover window), `CAND-03` (Backout design), `DEF-01` (SCIM).
* **Conditional Constraints to Preserve**: `CON-01` (Approved change record required before production).

---

## Stage 3 — Acceptance-Criteria Elaboration

Acceptance criteria are elaborated *only* for items designated as Ready or confirmed portions of Partially Ready work. No committed criteria are created for blocked, candidate, or deferred items.

### Acceptance Criteria Register

#### CAP-01: Corporate Identity Integration for NimbusHR
* **AC-CAP-01.1** (Traces to: `CAP-01`, `REQ-01`, `REQ-03`): Workforce access to NimbusHR must use corporate identity.
* **AC-CAP-01.2** (Traces to: `CAP-01`, `REQ-03`): Access via corporate identity must enforce the organisation's existing MFA policy.

#### SPIKE-01: Verify NimbusHR SAML Capability & Entra Compatibility
* **AC-SPIKE-01.1** (Traces to: `SPIKE-01`, `REQ-04`): Verify and document whether the organisation's NimbusHR tenant has the SAML feature enabled.
* **AC-SPIKE-01.2** (Traces to: `SPIKE-01`, `REQ-04`): Verify and document whether the proposed Entra SAML configuration is compatible with the NimbusHR tenant.

#### STORY-01: Map 603 Verified Employee Accounts to Corporate Identities
* **AC-STORY-01.1** (Traces to: `STORY-01`, `REQ-05`): The 603 matched employee accounts identified in the draft user-mapping spreadsheet must be mapped to their corresponding corporate identities.

#### CON-01: Change Policy Constraint (Conditional Constraint)
* **AC-CON-01.1** (Derived boundary, Traces to: `CON-01`): Production implementation of the authentication change must not proceed without an approved change record.

---

### Stage 3 Handoff Summary
* **Ready AC IDs**: `AC-CAP-01.1`, `AC-CAP-01.2`, `AC-SPIKE-01.1`, `AC-SPIKE-01.2`, `AC-STORY-01.1`.
* **Conditional Constraint IDs**: `AC-CON-01.1`.
* **Non-Ready Areas (No committed criteria)**: 17 unmatched accounts (`DISC-01`), Contractor access model (`DEC-01`), Change record approval (`DEC-02`), SAML configuration implementation (`CAND-01`), Cutover window (`CAND-02`), Backout mechanics (`CAND-03`), SCIM provisioning (`DEF-01`).

---

## Stage 4 — Behavioural Test / Assurance Derivation

Tests and assurance checks are derived strictly from the Ready acceptance criteria and confirmed constraints. No concrete test values, UI actions, or implementation mechanisms are invented.

### Test Cases

#### TEST-CAP-01.1: Corporate Identity Authentication
* **Test ID**: `TEST-CAP-01.1`
* **Traces to**: `AC-CAP-01.1`, `CAP-01`, `REQ-01`, `REQ-03`
* **Condition**: An employee attempts to access NimbusHR.
* **Action**: Employee authenticates using corporate identity.
* **Outcome**: Access is granted.

#### TEST-CAP-01.2: MFA Policy Enforcement
* **Test ID**: `TEST-CAP-01.2`
* **Traces to**: `AC-CAP-01.2`, `CAP-01`, `REQ-03`
* **Condition**: An employee attempts to access NimbusHR via corporate identity.
* **Action**: Corporate identity authentication is initiated.
* **Outcome**: The organisation's existing MFA policy is applied and must be satisfied before access is granted.

#### TEST-SPIKE-01.1: SAML Feature Verification
* **Test ID**: `TEST-SPIKE-01.1`
* **Traces to**: `AC-SPIKE-01.1`, `SPIKE-01`, `REQ-04`
* **Condition**: Access to the NimbusHR tenant administration settings is available.
* **Action**: Inspect the tenant configuration for SAML feature enablement.
* **Outcome**: Documented confirmation of SAML feature availability on the active tenant.

#### TEST-SPIKE-01.2: SAML Compatibility Verification
* **Test ID**: `TEST-SPIKE-01.2`
* **Traces to**: `AC-SPIKE-01.2`, `SPIKE-01`, `REQ-04`
* **Condition**: Entra SAML metadata and NimbusHR configuration parameters are available.
* **Action**: Compare and analyze the federation parameters for compatibility.
* **Outcome**: Documented confirmation of compatibility or identified configuration gaps.

#### TEST-STORY-01.1: Employee Account Mapping Verification
* **Test ID**: `TEST-STORY-01.1`
* **Traces to**: `AC-STORY-01.1`, `STORY-01`, `REQ-05`
* **Condition**: The 603 matched employee accounts are prepared for mapping.
* **Action**: Verify each of the 603 accounts against corporate identity records.
* **Outcome**: All 603 accounts are successfully mapped to valid corporate identities.

### Assurance Checks

#### ASSURE-CON-01.1: Change Record Verification (Conditional Constraint)
* **Assurance ID**: `ASSURE-CON-01.1`
* **Traces to**: `AC-CON-01.1`, `CON-01`
* **State to hold**: An approved change record must exist prior to production deployment.
* **Inspection**: Verify the existence and approved status of the change record in the organization's change management system before cutover. *(Note: The specific Change Authority and tool remain unknown).*

---

## End-to-End Traceability Summary

| Stage 1 Requirement / Constraint ID | Stage 2 Work Item ID | Stage 3 Acceptance Criteria ID | Stage 4 Test / Assurance ID | Status / Disposition |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | `CAP-01` | `AC-CAP-01.1` | `TEST-CAP-01.1` | Confirmed / Ready |
| **REQ-02** | N/A | N/A | N/A | Target (No downstream criteria/tests) |
| **REQ-03** | `CAP-01` | `AC-CAP-01.1`, `AC-CAP-01.2` | `TEST-CAP-01.1`, `TEST-CAP-01.2` | Confirmed / Ready |
| **REQ-04** | `SPIKE-01`<br>`CAND-01` | `AC-SPIKE-01.1`, `AC-SPIKE-01.2`<br>N/A | `TEST-SPIKE-01.1`, `TEST-SPIKE-01.2`<br>N/A | Spike: Ready<br>Implementation: Candidate |
| **REQ-05** | `STORY-01`<br>`DISC-01` | `AC-STORY-01.1`<br>N/A | `TEST-STORY-01.1`<br>N/A | 603 Accounts: Ready<br>17 Accounts: Blocked |
| **REQ-06** | `DEC-01` | N/A | N/A | Disputed / Blocked |
| **REQ-07** | `DEF-01` | N/A | N/A | Deferred |
| **REQ-08** | `CAND-02` | N/A | N/A | Candidate / Blocked |
| **REQ-09** | `CAND-03` | N/A | N/A | Target / Candidate |
| **REQ-10** | `DEC-02` | N/A | N/A | Candidate / Blocked |
| **CON-01** | `DEC-02` | `AC-CON-01.1` | `ASSURE-CON-01.1` | Confirmed / Ready (Assurance only) |

---

## Solution & Change-Readiness Review

### Readiness Gap Analysis
Before this change can be transitioned to a "Ready" state for production implementation, the following gaps must be resolved by their respective (currently unknown) decision owners:

1

---

## change-readiness — Prepare Solution / Change Readiness v0.2

_No model output._
