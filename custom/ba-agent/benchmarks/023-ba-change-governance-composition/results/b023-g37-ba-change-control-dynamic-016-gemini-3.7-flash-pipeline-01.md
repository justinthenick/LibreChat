# BA Specialist Pipeline Result

- Pipeline: `Benchmark 023 — Candidate: Composite BA + Change Readiness + ITIL`
- Model: `gemini-3.7-flash`
- Status: `success`
- Run ID: `b023-g37-ba-change-control-dynamic-016`
- Total prompt tokens: `14258`
- Total candidate tokens: `10108`
- Total thought tokens: `4884`
- Total tokens: `29250`

---

## ba-delivery — Composite BA Delivery Analyst v0.2

# Stage 1 — Requirements Analysis

## Overall Readiness
**Partially Ready**
Workforce identity transition requirements and governance constraints are established, but integration capability, contractor access policy, account resolution, and change cutover details remain unverified, disputed, or unapproved.

---

## 1. Requirement & Constraint Register

| ID | Statement / Description | Evidence Class | Requirement Status | Source / Proposer | Notes / Boundaries |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | Transition workforce access for employees from NimbusHR-local passwords to corporate identity. | Explicit | Confirmed | Business Objective | Sourced scope: ~620 total employees; eliminates local password reliance. |
| **REQ-02** | Resolution of corporate identity mappings for the remaining 17 unmatched employee accounts. | Explicit | Unknown | Draft user-mapping spreadsheet | 603 accounts matched; 17 accounts require resolution before full cutover. |
| **REQ-03** | Determine authentication model for contractor access (corporate guest identity vs. NimbusHR-local account). | Disputed | Disputed | HR Operations / Security | HR Ops proposes local accounts (lifecycle effort); Security proposes corporate guest identity. Decision owner: Unknown. |
| **REQ-04** | Implement Entra enterprise application SAML federation with NimbusHR. | Proposed | Candidate | Identity Team | Proposed mechanism based on public documentation; tenant entitlement and compatibility unverified. |
| **REQ-05** | Complete workforce identity transition prior to 30 November. | Explicit | Target | Head of HR | Desired timeline to precede December audit cycle; explicitly not committed as a delivery deadline. |
| **REQ-06** | Automated user provisioning and deprovisioning via SCIM for Phase 2. | Proposed | Deferred | Sourced proposal | Out of scope for current cutover; vendor capability and tenant entitlement unverified. |
| **REQ-07** | Perform production cutover during a Saturday 22:00 window. | Proposed | Candidate | Release Manager | Proposed cutover window; explicitly not yet approved. |
| **REQ-08** | Authentication change backout recovery time of 45 minutes. | Proposed | Target | Service Desk | Suggested recovery target; non-binding, backout mechanics not designed. |
| **CON-01** | Workforce access to SaaS applications containing employee data must use corporate identity and the organisation's existing MFA policy. | Explicit | Confirmed | Security Standard | Mandatory policy constraint; does not mandate specific protocol or product architecture. |
| **CON-02** | An approved change record is required prior to production implementation of customer- or workforce-impacting authentication changes. | Explicit | Confirmed | Change Policy | Mandatory governance constraint; Change Authority not specified, CAB requirement not universally mandated. |

---

## 2. Risk, Dependency & Open Question Register

| ID | Type | Description | Upstream Trace | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DEP-01** | Dependency | NimbusHR tenant entitlement and technical compatibility for federation must be verified. | REQ-04 | Open |
| **DEP-02** | Dependency | 17 unmatched employee accounts must be mapped to corporate identities. | REQ-02 | Open |
| **RSK-01** | Risk | Cutover execution without an approved change record or validated backout mechanism violates policy and risks prolonged downtime. | CON-02, REQ-08 | Open |
| **RSK-02** | Risk | Contractor access model unresolved prior to cutover risks access failure or policy non-compliance. | REQ-03 | Open |
| **OQ-01** | Open Question | Who is the authorized decision maker to resolve the contractor identity dispute? | REQ-03 | Unresolved |
| **OQ-02** | Open Question | What is the designated Change Authority and change model for this implementation? | CON-02 | Unresolved (Operations noted "probably Normal Change") |

---

## Stage 1 Handoff Summary
- **Confirmed Requirements / Constraints:** REQ-01, CON-01, CON-02 (Progress to decomposition).
- **Partially Ready / Open Requirements:** REQ-02 (Requires account resolution).
- **Disputed Requirements:** REQ-03 (Requires explicit decision ownership and resolution; Blocked from functional build).
- **Candidate Scope / Proposals:** REQ-04 (Requires technical spike), REQ-07 (Unapproved cutover window).
- **Targets (Non-binding):** REQ-05 (Date target: < 30 Nov), REQ-08 (Recovery target: 45 min).
- **Deferred Scope:** REQ-06 (Phase 2 SCIM).

---

# Stage 2 — Delivery Decomposition

## 1. Decomposed Work Items

| Work Item ID | Type | Title / Description | Status / Readiness | Traces To | Notes & Constraints |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CAP-01** | Capability | NimbusHR Workforce Identity Integration | Partially Ready | REQ-01, CON-01 | Core capability to transition employee access to corporate identity. |
| **SPK-01** | Spike / Discovery | NimbusHR Tenant Federation Capability & Entitlement Verification | Ready | REQ-04, DEP-01 | Spike to verify tenant enterprise plan entitlements and federation compatibility. |
| **US-01** | User Story | Employee Authentication via Corporate Identity (Matched Accounts) | Partially Ready | REQ-01, CON-01 | Covers 603 matched employee accounts moving to corporate identity with MFA. |
| **TSK-01** | Technical Task | Identity Resolution for Unmatched Employee Accounts | In Progress | REQ-02, DEP-02 | Resolution and corporate identity mapping for the remaining 17 employee records. |
| **DEC-01** | Decision Item | Contractor Authentication Strategy Resolution | Blocked | REQ-03, RSK-02, OQ-01 | Disputed between HR Ops (local) and Security (guest). Decision owner: Unknown. Downstream build blocked. |
| **ENB-01** | Enabler | Entra Enterprise Application SAML Configuration | Candidate | REQ-04, SPK-01 | Candidate implementation mechanism; conditional on SPK-01 discovery outcome. |
| **TGT-01** | Target Item | Pre-December Audit Delivery Window Target | Non-binding Target | REQ-05 | Planning target (< 30 Nov); non-binding delivery milestone. |
| **TGT-02** | Target Item | Cutover Backout Recovery Time Objective | Non-binding Target | REQ-08 | Target recovery duration (45 mins); operational guidance, mechanics not designed. |
| **CAND-01** | Candidate Item | Weekend Production Cutover Window (Saturday 22:00) | Candidate | REQ-07 | Proposed implementation schedule; pending operational and change approval. |
| **DEF-01** | Deferred Item | Automated Lifecycle Provisioning via SCIM (Phase 2) | Deferred | REQ-06 | Out of scope for current delivery cycle. |
| **GOV-01** | Process Constraint | Mandatory Corporate MFA Enforcement | Confirmed Constraint | CON-01 | All SaaS employee access must enforce corporate identity and existing MFA policy. |
| **GOV-02** | Process Constraint | Pre-Implementation Change Record Approval | Confirmed Constraint | CON-02, RSK-01, OQ-02 | Production implementation requires change record approval by designated Change Authority. |

---

## Stage 2 Handoff Summary
- **Ready for Acceptance Criteria:** US-01 (for confirmed matched scope), GOV-01 (MFA constraint), GOV-02 (Change approval constraint).
- **Discovery / Technical Action Required:** SPK-01, TSK-01.
- **Blocked / Not Ready for Criteria:** DEC-01 (Disputed access model), ENB-01 (Candidate mechanism).
- **Retained as Non-binding / External:** TGT-01, TGT-02, CAND-01, DEF-01.

---

# Stage 3 — Acceptance-Criteria Elaboration

Acceptance criteria are elaborated strictly for Ready and confirmed portions of Partially Ready scope, alongside confirmed governance constraints. No criteria are created for candidate mechanisms, disputed paths, or deferred scope.

---

## 1. Acceptance Criteria Register

### Work Item: US-01 — Employee Authentication via Corporate Identity
*Upstream Trace: REQ-01, CON-01 | Capability: CAP-01*

- **AC-US01-01 (Corporate Authentication Enforcement):**
  Workforce authentication for active employees with resolved identity mappings successfully authenticates against the corporate identity provider instead of NimbusHR-local passwords.
  *Traces to: US-01, REQ-01*

- **AC-US01-02 (Local Password Decommissioning - Matched Accounts):**
  Active employees with resolved corporate identities cannot authenticate using NimbusHR-local passwords.
  *Type: Derived boundary | Traces to: US-01, REQ-01*

---

### Work Item: GOV-01 — Mandatory Corporate MFA Enforcement
*Upstream Trace: CON-01 | Capability: CAP-01*

- **AC-GOV01-01 (MFA Policy Invocation):**
  Workforce access to NimbusHR enforces the organisation's existing multi-factor authentication (MFA) policy during the corporate identity authentication sequence.
  *Traces to: GOV-01, CON-01*

- **AC-GOV01-02 (MFA Failure Boundary):**
  Access to NimbusHR is not granted if the corporate MFA requirement is not satisfied during authentication.
  *Type: Derived boundary | Traces to: GOV-01, CON-01*

---

### Work Item: GOV-02 — Pre-Implementation Change Record Approval
*Upstream Trace: CON-02*

- **AC-GOV02-01 (Pre-Implementation Authorization Gate):**
  Production implementation of the authentication change occurs only after an approved change record is established.
  *Traces to: GOV-02, CON-02*

- **AC-GOV02-02 (Unapproved Implementation Prevention):**
  Production cutover must not proceed in the absence of an approved change record.
  *Type: Derived boundary | Traces to: GOV-02, CON-02*

---

## Stage 3 Handoff Summary
- **Ready Acceptance Criteria for Test Derivation:** AC-US01-01, AC-US01-02, AC-GOV01-01, AC-GOV01-02, AC-GOV02-01, AC-GOV02-02.
- **Excluded from Test Derivation:**
  - Contractor authentication paths (DEC-01 / REQ-03: Disputed).
  - Unmatched 17 employee accounts (TSK-01 / REQ-02: Pending identity resolution).
  - Entra SAML specific mechanics (ENB-01 / REQ-04: Candidate / unverified).
  - Production cutover timing & backout duration (CAND-01, TGT-01, TGT-02: Unapproved / Non-binding).
  - SCIM provisioning (DEF-01 / REQ-06: Deferred).

---

# Stage 4 — Behavioural Test & Assurance Derivation

Test cases and assurance verifications are derived strictly from Ready acceptance criteria and confirmed constraints. No concrete test payloads, UI scripts, automation frameworks, mock endpoints, or uncommitted execution mechanics are invented.

---

## 1. Test & Assurance Register

| Test / Assurance ID | Delivery Item ID | Upstream Trace | Criteria Trace | Condition / Setup | Action / Event | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-AUTH-01** | US-01 | REQ-01 | AC-US01-01 | Employee has a matched and resolved corporate identity record. | Employee initiates authentication to NimbusHR. | Authentication is routed to and completed via corporate identity. |
| **TC-AUTH-02** | US-01 | REQ-01 | AC-US01-02 | Employee has a matched corporate identity record. | Employee attempts authentication using a NimbusHR-local password. | Authentication using the local password is not permitted. |
| **TC-SEC-01** | GOV-01 | CON-01 | AC-GOV01-01 | Corporate identity authentication is initiated by an employee subject to corporate MFA policy. | Employee successfully satisfies primary corporate credentials and prompt for corporate MFA. | MFA requirement is enforced and access to NimbusHR is granted upon successful MFA completion. |
| **TC-SEC-02** | GOV-01 | CON-01 | AC-GOV01-02 | Corporate identity authentication is initiated by an employee subject to corporate MFA policy. | Employee fails or does not complete the corporate MFA prompt. | Authentication is terminated; access to NimbusHR is not granted. |
| **ASR-GOV-01** | GOV-02 | CON-02 | AC-GOV02-01, AC-GOV02-02 | Implementation package prepared for workforce-impacting authentication change. | Production cutover readiness check is conducted. | Approved change record must be present prior to initiating production implementation. |

---

## 2. Non-Testable / Unverified Scope Boundaries

| Item Ref | Status | Reason Not Testable / Excluded |
| :--- | :--- | :--- |
| **REQ-02 / TSK-01** | Unknown (17 Accounts) | Accounts unresolved; test cases apply only to resolved identities. |
| **REQ-03 / DEC-01** | Disputed (Contractors) | Contractor authentication model is disputed and authority is unknown. |
| **REQ-04 / ENB-01** | Candidate (SAML/Entra) | Protocol implementation mechanism unverified on tenant. |
| **REQ-05 / TGT-01** | Target (< 30 Nov) | Non-binding schedule target; not a functional test condition. |
| **REQ-06 / DEF-01** | Deferred (SCIM) | Phase 2 scope; excluded from current cutover verification. |
| **REQ-07 / CAND-01** | Candidate (Cutover Window) | Schedule proposed but unapproved. |
| **REQ-08 / TGT-02** | Target (45m Backout) | Suggested recovery duration; backout mechanics not designed. |

---

# End-to-End Traceability Summary

| Stage 1 (REQ / CON) | Stage 2 (Delivery Work Item) | Stage 3 (Acceptance Criteria) | Stage 4 (Test / Assurance) | Lifecycle Status |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | CAP-01, US-01 | AC-US01-01, AC-US01-02 | TC-AUTH-01, TC-AUTH-02 | Confirmed / Ready (Matched scope) |
| **REQ-02** | TSK-01 | — | — | Unknown (17 accounts unmapped) |
| **REQ-03** | DEC-01 | — | — | Disputed (Decision owner: Unknown) |
| **REQ-04** | SPK-01, ENB-01 | — | — | Candidate (Pending discovery) |
| **REQ-05** | TGT-01 | — | — | Target (Non-binding milestone) |
| **REQ-06** | DEF-01 | — | — | Deferred (Phase 2) |
| **REQ-07** | CAND-01 | — | — | Candidate (Unapproved window) |
| **REQ-08** | TGT-02 | — | — | Target (Non-binding recovery target) |
| **CON-01** | GOV-01 | AC-GOV01-01, AC-GOV01-02 | TC-SEC-01, TC-SEC-02 | Confirmed Constraint |
| **CON-02** | GOV-02 | AC-GOV02-01, AC-GOV02-02 | ASR-GOV-01 | Confirmed Constraint |

PIPELINE_HANDOFF_COMPLETE: BA_DELIVERY_4_STAGE

---

## change-readiness — Prepare Solution / Change Readiness v0.2

# Solution / Change-Readiness Handoff

## 1. Overall Handoff Readiness

**Overall State:** **Partially ready**

- **Readiness for Solution / Design Review:** **Partially ready**  
  Core functional scope for matched employee accounts (REQ-01, US-01) and confirmed security constraints (CON-01, GOV-01) are defined alongside a specific discovery spike (SPK-01). However, the technical federation mechanism (REQ-04, ENB-01) remains candidate, the contractor authentication model (REQ-03, DEC-01) remains disputed with unknown decision authority (OQ-01), and 17 employee accounts remain unmapped (REQ-02, TSK-01).
- **Readiness for Change Submission / Production:** **Not ready**  
  Production implementation is constrained by mandatory change approval (CON-02, GOV-02), but the change record is unapproved, the Change Authority is unassigned (OQ-02), the cutover schedule is unapproved (REQ-07, CAND-01), backout mechanics are undesigned (REQ-08, TGT-02, RSK-01), and no test execution evidence exists.

---

## 2. Evidence Ready for Handoff

The following confirmed scope, constraints, acceptance criteria, and assurance designs are supplied and verified:

- **Confirmed Scope & Governance Constraints:**
  - Transition workforce access for ~620 employees from NimbusHR-local passwords to corporate identity (`REQ-01`, `CON-01`).
  - Mandatory enforcement of corporate identity and existing MFA policy for workforce access to SaaS containing employee data (`CON-01`, `GOV-01`).
  - Mandatory requirement for an approved change record prior to production implementation of workforce-impacting authentication changes (`CON-02`, `GOV-02`).
- **Ready Delivery & Discovery Items:**
  - `SPK-01`: Spike to verify NimbusHR tenant federation capability and enterprise plan entitlement (`REQ-04`, `DEP-01`).
  - `US-01`: Authentication via corporate identity for the 603 matched employee accounts (`REQ-01`, `CON-01`).
- **Elaborated Acceptance Criteria:**
  - `AC-US01-01` & `AC-US01-02`: Corporate authentication routing and local password decommissioning for matched employee accounts (`US-01`, `REQ-01`).
  - `AC-GOV01-01` & `AC-GOV01-02`: Corporate MFA policy invocation and access termination upon MFA failure (`GOV-01`, `CON-01`).
  - `AC-GOV02-01` & `AC-GOV02-02`: Pre-implementation change record authorization gate and unapproved implementation prevention (`GOV-02`, `CON-02`).
- **Test & Assurance Design (Specifications only; no execution evidence supplied):**
  - `TC-AUTH-01` & `TC-AUTH-02`: Verification of corporate identity routing and local password prevention.
  - `TC-SEC-01` & `TC-SEC-02`: Verification of corporate MFA success and failure handling.
  - `ASR-GOV-01`: Assurance verification of approved change record presence prior to production cutover.
- **Explicit Decisions Established:**
  - Employee authentication will move to corporate identity with MFA (`REQ-01`, `CON-01`).
  - SCIM automated provisioning is excluded from current cutover and deferred to Phase 2 (`REQ-06`, `DEF-01`).

---

## 3. Unresolved / Non-Committed Register

| Item ID | Category | Current Status | Description / Notes | Upstream Trace |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-03 / DEC-01** | Decision | Disputed | Contractor authentication model disputed (HR Ops proposes local accounts; Security proposes corporate guest identity). Authorized decision maker is unknown (`OQ-01`). | REQ-03, RSK-02, OQ-01 |
| **REQ-02 / TSK-01** | Account Data | Unknown | 17 employee records remain unmatched in corporate identity mapping spreadsheet. | REQ-02, DEP-02 |
| **REQ-04 / ENB-01** | Technical Design | Candidate | Entra enterprise application SAML federation mechanism proposed from public docs; tenant entitlement and compatibility unverified. | REQ-04, SPK-01, DEP-01 |
| **REQ-07 / CAND-01** | Cutover Window | Candidate | Proposed Saturday 22:00 production cutover window; explicitly unapproved. | REQ-07 |
| **REQ-05 / TGT-01** | Schedule | Target | Desired completion prior to 30 November audit cycle; non-binding milestone. | REQ-05 |
| **REQ-08 / TGT-02** | Operational Target | Target | Suggested 45-minute authentication backout recovery time; non-binding target, mechanics not designed. | REQ-08, RSK-01 |
| **REQ-06 / DEF-01** | Scope | Deferred | Phase 2 automated provisioning/deprovisioning via SCIM; excluded from current scope. | REQ-06 |
| **OQ-02** | Governance | Unknown | Designated Change Authority and formal change model (noted informally as "probably Normal Change") unconfirmed. | CON-02, RSK-01 |

---

## 4. Solution / Design Review Handoff

Downstream technical architecture and solution design review must address the following bounded outcomes and constraints:

- **Authentication & MFA Enforcement:** Must design corporate identity integration satisfying `CON-01` and `AC-GOV01-01`/`02` for all active employees (`REQ-01`), preventing local password bypass (`AC-US01-02`).
- **Design Questions to Resolve (Spike / Discovery Outcomes Required):**
  - *Spike SPK-01:* Does the current NimbusHR tenant enterprise subscription entitle and support SAML federation, or is a configuration/plan adjustment required (`REQ-04`, `DEP-01`)?
  - *Contractor Scope (DEC-01):* What technical integration is required once the authorized decision maker (`OQ-01`) determines whether contractors use corporate guest identity or local accounts (`REQ-03`)?
  - *Data Mapping (TSK-01):* What technical identity attributes resolve the remaining 17 unmatched employee accounts (`REQ-02`, `DEP-02`)?

---

## 5. Change-Readiness Evidence Matrix

| Evidence Area | State | Evidence Available | Missing / Unresolved | Traceability |
| :--- | :--- | :--- | :--- | :--- |
| **Implementation Approach** | Partial | Core requirement confirmed (`REQ-01`); candidate SAML mechanism identified (`REQ-04`, `ENB-01`). | Verification of tenant compatibility (`SPK-01`); concrete implementation procedure to be established downstream. | REQ-01, REQ-04, SPK-01, ENB-01 |
| **Governance & Authorization** | Partial | Mandatory change record approval policy constraint confirmed (`CON-02`, `GOV-02`, `ASR-GOV-01`). | Change Authority designation (`OQ-02`), change model confirmation, change record submission, and formal approval. | CON-02, GOV-02, ASR-GOV-01, OQ-02 |
| **Deployment / Cutover Window** | Partial | Proposed window: Saturday 22:00 (`REQ-07`, `CAND-01`); non-binding schedule target `< 30 Nov` (`REQ-05`, `TGT-01`). | Operational and change approval of cutover window; final deployment sequencing to be established downstream. | REQ-05, REQ-07, CAND-01, TGT-01 |
| **Backout / Rollback Approach** | Partial | Non-binding backout recovery duration target of 45 minutes proposed (`REQ-08`, `TGT-02`). | Backout/rollback mechanics, trigger criteria, and operational recovery procedures are missing / to be established downstream. | REQ-08, TGT-02, RSK-01 |
| **Testing & Assurance Evidence** | Partial | Test cases and assurance criteria designed (`TC-AUTH-01/02`, `TC-SEC-01/02`, `ASR-GOV-01`). | Actual test execution evidence and assurance run results are missing (no executions recorded). | TC-AUTH-01, TC-AUTH-02, TC-SEC-01, TC-SEC-02, ASR-GOV-01 |
| **Operational & Support Readiness** | Missing | None supplied. | Service Desk triage, operational support procedures, and incident handling to be established downstream. | REQ-08, RSK-01 |
| **Communications & User Readiness** | Missing | None supplied. | End-user communications, cutover notifications, and password transition guidance to be established downstream. | REQ-01, CAP-01 |

---

## 6. Source-Evidenced Blockers / Dependencies

### Source-Evidenced Blockers
- **Contractor Functional Build Blocked (`DEC-01`):** Functional design and build for contractor access paths are blocked until the dispute between HR Ops and Security is resolved by an authorized decision maker (`REQ-03`, `RSK-02`, `OQ-01`).
- **Production Implementation Blocked (`CON-02`, `GOV-02`, `ASR-GOV-01`):** Production cutover is explicitly blocked from proceeding in the absence of an approved change record (`AC-GOV02-02`).

### Source-Evidenced Dependencies
- **DEP-01 (Tenant Entitlement / Capability):** Candidate configuration (`ENB-01`) depends on discovery findings from `SPK-01` (`REQ-04`).
- **DEP-02 (Identity Resolution):** Full workforce cutover depends on resolving mappings for the 17 unmatched employee records in `TSK-01` (`REQ-02`).

---

## 7. Missing Downstream Evidence

*(Note: These are missing information categories to be established downstream, not manufactured governance gates)*

1. **Test Execution Evidence:** Execution logs and signed-off test results for `TC-AUTH-01`, `TC-AUTH-02`, `TC-SEC-01`, and `TC-SEC-02`.
2. **Technical Spike Outcome:** Documented outcome of `SPK-01` confirming NimbusHR federation support and tenant entitlements.
3. **Account Resolution Records:** Completed identity mapping for the 17 employee records under `TSK-01`.
4. **Contractor Strategy Decision:** Formal determination of contractor authentication model under `DEC-01`.
5. **Change Record & Authority Designation:** Formally submitted change record, designated Change Authority, and change model resolution (`OQ-02`).
6. **Rollback / Backout Procedure:** Concrete backout procedure, technical steps, and verification checks (`RSK-01`, `REQ-08`).
7. **Operational Handover Material:** Service Desk support documentation and operational readiness details.
8. **Workforce Communication Plan:** Notification and support instructions for transitioning employees.

---

## 8. Traceability Summary

| Upstream ID | Delivery Item | Criteria Trace | Test / Assurance Trace | Current State | Handoff Disposition |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | CAP-01, US-01 | AC-US01-01, AC-US01-02 | TC-AUTH-01, TC-AUTH-02 | Confirmed / Partially Ready | Hand over matched scope (603 accounts) to design/build |
| **REQ-02** | TSK-01 | — | — | Unknown (17 accounts) | Maintain as dependency `DEP-02`; pending mapping completion |
| **REQ-03** | DEC-01 | — | — | Disputed | Block contractor functional build pending decision resolution (`OQ-01`) |
| **REQ-04** | SPK-01, ENB-01 | — | — | Candidate / Discovery | Hand over `SPK-01` to architecture/engineering; retain `ENB-01` as Candidate |
| **REQ-05** | TGT-01 | — | — | Non-binding Target | Retain as planning target (`< 30 Nov`); non-binding on delivery |
| **REQ-06** | DEF-01 | — | — | Deferred | Retain out of scope (Phase 2 SCIM) |
| **REQ-07** | CAND-01 | — | — | Candidate | Retain as proposed cutover window; pending change/operational review |
| **REQ-08** | TGT-02 | — | — | Non-binding Target | Retain as operational recovery target (45 min); backout plan to be designed |
| **CON-01** | GOV-01 | AC-GOV01-01, AC-GOV01-02 | TC-SEC-01, TC-SEC-02 | Confirmed Constraint | Hand over mandatory MFA enforcement constraint to solution review |
| **CON-02** | GOV-02 | AC-GOV02-01, AC-GOV02-02 | ASR-GOV-01 | Confirmed Constraint | Hand over mandatory change approval constraint to Change Enablement |

---

## 9. Recommended Next Review State

1. **Solution / Technical Design Review:**
   - Execute discovery spike `SPK-01` to establish NimbusHR federation compatibility and tenant entitlement.
   - Establish technical architecture for employee corporate identity routing and MFA enforcement (`REQ-01`, `CON-01`).
   - Identify decision authority for contractor model (`OQ-01`) to enable resolution of `DEC-01`.
2. **Delivery & Data Resolution:**
   - Complete corporate identity mappings for the 17 unmatched employee accounts (`TSK-01`).
3. **Change Enablement Preparation (Downstream items to establish prior to production cutover):**
   - Identify designated Change Authority and formal change model (`OQ-02`).
   - Author detailed technical implementation and backout procedures (`REQ-08`, `RSK-01`).
   - Execute test cases (`TC-AUTH-01/02`, `TC-SEC-01/02`) and compile validation evidence.
   - Formally submit change record for approval (`CON-02`, `GOV-02`, `ASR-GOV-01`).

PIPELINE_HANDOFF_COMPLETE: CHANGE_READINESS

---

## itil-alignment — Assess ITIL Alignment v0.2

# ITIL 4 Alignment & Readiness Assessment

## 1. Assessment Scope and Overall Alignment Readiness

- **Assessment Scope:** Assessment of the workforce authentication transition to corporate identity for NimbusHR (covering ~620 employee accounts, contractor access paths, and federation configuration) against relevant ITIL 4 practice concepts.
- **Overall Alignment Readiness:** **Partially aligned / Readiness incomplete**
  - *Governance & Control:* The requirement for formal change authorisation prior to production is established by organisational policy (`CON-02`, `GOV-02`), but the formal change record, designated Change Authority (`OQ-02`), and change model remain unassigned and unapproved.
  - *Technical & Security Definition:* Information security objectives (MFA enforcement via `CON-01`, `GOV-01`) and functional requirements for 603 matched accounts (`REQ-01`, `US-01`) are well-defined. However, technical federation viability (`REQ-04`, `SPK-01`), contractor authentication strategy (`REQ-03`, `DEC-01`), and cutover timing (`REQ-07`, `CAND-01`) remain candidate, disputed, or unapproved.
  - *Operational & Deployment Enablement:* Test cases and assurance specifications are defined, but execution results, concrete deployment sequencing, operational support handover, and backout mechanics are unevidenced.

---

## 2. Applicable ITIL Practice Map

| ITIL 4 Practice | Material Relevance to Supplied Scenario |
| :--- | :--- |
| **Change Enablement** | Governs risk assessment, schedule coordination, and mandatory change authorisation prior to production cutover (`CON-02`, `GOV-02`, `REQ-07`). |
| **Information Security Management** | Governs authentication controls, MFA enforcement, and secure access boundaries for workforce and contractor access (`CON-01`, `GOV-01`, `REQ-03`). |
| **Release Management** | Governs making the authentication transition available to end users, user transition guidance, and milestone alignment (`REQ-01`, `REQ-05`, `CAP-01`). |
| **Deployment Management** | Governs technical execution, federation cutover sequencing, environment/tenant configuration, and backout execution (`REQ-04`, `REQ-07`, `REQ-08`, `SPK-01`). |
| **Service Configuration Management** | Governs identity mapping data integrity, tenant configuration baselines, and configuration item dependencies (`REQ-02`, `TSK-01`, `DEP-01`). |

*(Note: Practices such as IT Asset Management and Continual Improvement are out of scope as no material assets or post-implementation review activities are established in the upstream artifact).*

---

## 3. Alignment Findings

| Finding ID | ITIL Practice | Evidence / Condition | Status | Readiness Impact | Source Trace |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F-01** | Information Security Management | Mandatory corporate identity and MFA policy enforcement defined for workforce SaaS access. | **Aligned / evidenced** | No current blocker | CON-01, GOV-01, AC-GOV01-01, AC-GOV01-02 |
| **F-02** | Information Security Management | Contractor authentication architecture is disputed between local accounts and corporate guest identity; decision owner is unknown. | **Partially evidenced** | Readiness dependency | REQ-03, DEC-01, RSK-02, OQ-01 |
| **F-03** | Change Enablement | Explicit organisational policy mandates approved change record prior to production implementation. | **Aligned / evidenced** | Readiness dependency | CON-02, GOV-02, ASR-GOV-01, AC-GOV02-01 |
| **F-04** | Change Enablement | Designated Change Authority and formal change model are unconfirmed; change record is unsubmitted/unapproved. | **Partially evidenced** | Decision required | CON-02, RSK-01, OQ-02, AC-GOV02-02 |
| **F-05** | Change Enablement | Cutover window proposed for Saturday 22:00 is explicitly unapproved and uncoordinated with change schedule. | **Partially evidenced** | Decision required | REQ-07, CAND-01 |
| **F-06** | Service Configuration Management | Account mapping verified for 603 accounts; 17 employee identity mappings remain unmapped/unresolved. | **Partially evidenced** | Readiness dependency | REQ-01, REQ-02, TSK-01, DEP-02 |
| **F-07** | Service Configuration Management | Technical federation compatibility and tenant configuration entitlement are unverified pending spike outcome. | **Partially evidenced** | Readiness dependency | REQ-04, SPK-01, ENB-01, DEP-01 |
| **F-08** | Deployment Management | Backout duration target (45 min) proposed, but technical rollback procedures and trigger mechanics are undesigned. | **Partially evidenced** | Clarification required | REQ-08, TGT-02, RSK-01 |
| **F-09** | Release Management | Non-binding target completion date prior to 30 November audit cycle established; automated SCIM deferred to Phase 2. | **Aligned / evidenced** | No current blocker | REQ-05, TGT-01, REQ-06, DEF-01 |
| **F-10** | Release Management | End-user communications, transition guidance, and Service Desk support handover are completely unevidenced. | **Not evidenced** | Clarification required | REQ-01, CAP-01, RSK-01 |
| **F-11** | Deployment Management | Test and assurance specifications designed (`TC-AUTH-01/02`, `TC-SEC-01/02`); actual test execution results are unevidenced. | **Partially evidenced** | Clarification required | TC-AUTH-01, TC-AUTH-02, TC-SEC-01, TC-SEC-02 |

---

## 4. Readiness Dependencies, Decisions, and Evidence Gaps

### Sourced Readiness Dependencies
- **DEP-01 (Tenant Federation Entitlement):** Deployment design (`ENB-01`) depends on technical validation from `SPK-01` (`REQ-04`).
- **DEP-02 (Identity Baseline Resolution):** Complete user transition depends on resolving the 17 unmatched employee records under `TSK-01` (`REQ-02`).
- **Change Authorisation Constraint (`CON-02` / `GOV-02`):** Production cutover is explicitly blocked until an approved change record is in place (`AC-GOV02-02`, `ASR-GOV-01`).

### Sourced Decisions Required
- **Contractor Authentication Model (`DEC-01`):** Resolution of the dispute between HR Ops (local accounts) and Security (corporate guest identity) by an authorised decision maker (`OQ-01`, `REQ-03`).
- **Change Authority & Model Confirmation (`OQ-02`):** Formal designation of the Change Authority and classification/approval of the change model (`CON-02`, `RSK-01`).
- **Cutover Window Authorisation (`CAND-01`):** Formal operational and change schedule approval of the proposed Saturday 22:00 window (`REQ-07`).

### Downstream Evidence Gaps (Clarification Required)
- *Test Execution Evidence:* Execution logs and verification results for `TC-AUTH-01`, `TC-AUTH-02`, `TC-SEC-01`, and `TC-SEC-02`.
- *Operational & Service Desk Handover:* Operational runbooks, incident triage, and support workflows (`RSK-01`).
- *Rollback / Backout Mechanics:* Detailed procedural steps to meet or evaluate the 45-minute recovery target (`REQ-08`, `TGT-02`).
- *Communications Plan:* Transition instructions and user guidance for affected employees (`CAP-01`).

---

## 5. Organisational-Policy vs. ITIL-Guidance Distinctions

| Area | Sourced Organisational Policy / Explicit Rule | ITIL 4 Guidance Context | Alignment Distinction |
| :--- | :--- | :--- | :--- |
| **Change Approval** | Mandatory: An approved change record is explicitly required before production cutover (`CON-02`, `GOV-02`). | Recommends tailored change authorities and value-protecting governance to enable fast, safe change. | Organisational policy enforces a hard pre-implementation gate; specific Change Authority role remains `Unknown` (`OQ-02`). |
| **Authentication & MFA** | Mandatory: Corporate identity and MFA policy enforcement required for workforce SaaS access (`CON-01`, `GOV-01`). | Information Security Management practice recommends applying authentication controls aligned to risk appetite. | Sourced constraint is a non-negotiable organisational requirement. |
| **Change Scheduling** | Saturday 22:00 is a candidate proposal (`REQ-07`, `CAND-01`), currently unapproved. | Change Enablement emphasises coordinating changes against a schedule to prevent resource and business conflicts. | Proposed window is not yet an approved schedule entry; requires formal organisational scheduling. |
| **Rollback / Recovery** | 45-minute target is a non-binding operational goal (`REQ-08`, `TGT-02`); mechanics undesigned. | Deployment Management practice recommends planning remediation/backout actions to manage release risk. | 45-minute target is an operational goal, not a validated technical rollback plan or mandatory gate. |
| **Support & Communications** | Support and communication plans are currently unevidenced in the upstream record. | Release and Service Desk practices recommend establishing operational and user readiness before release. | Absence of these artifacts represents missing delivery evidence, not proven non-compliance or a local policy violation. |

---

## 6. Focused Follow-Up Questions

1. **Change Authority Designation (`OQ-02`, `CON-02`):** Who is the designated Change Authority for this change, and what formal change model (e.g., Normal Change) will govern submission and approval?
2. **Contractor Decision Authority (`OQ-01`, `REQ-03`):** Which role or governing body is authorised to resolve the disputed contractor authentication model (`DEC-01`) between HR Operations and Information Security?
3. **Cutover Window Commitment (`REQ-07`):** Is the proposed Saturday 22:00 cutover window acceptable to business operations, and what schedule coordination is required for change authorisation?
4. **Tenant Compatibility Outcome (`SPK-01`, `DEP-01`):** Does the outcome of spike `SPK-01` confirm SAML federation entitlement in the current NimbusHR subscription, or are commercial/technical adjustments required?
5. **Operational Handover Scope:** Does organisational policy define specific mandatory operational readiness artifacts (e.g., Service Desk runbook, user communication lead times) required prior to change authorisation?

---

## 7. Traceability Summary

| Upstream ID | Delivery Item | Practice Lens | Status | Handoff & Assessment Disposition |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | CAP-01, US-01 | Release / Information Security | Aligned / evidenced | Matched scope (603 accounts) confirmed; corporate identity routing defined. |
| **REQ-02** | TSK-01 | Service Configuration Management | Partially evidenced | 17 unmatched employee records retained as dependency `DEP-02`. |
| **REQ-03** | DEC-01 | Information Security Management | Partially evidenced | Disputed contractor strategy; requires resolution by unknown authority (`OQ-01`). |
| **REQ-04** | SPK-01, ENB-01 | Deployment Management | Partially evidenced | Candidate SAML federation design retained pending spike `SPK-01` (`DEP-01`). |
| **REQ-05** | TGT-01 | Release Management | Aligned / evidenced | Target audit date (< 30 Nov) retained as non-binding planning milestone. |
| **REQ-06** | DEF-01 | Service Configuration Management | Out of scope | SCIM automated provisioning confirmed deferred to Phase 2. |
| **REQ-07** | CAND-01 | Change Enablement | Partially evidenced | Candidate Saturday 22:00 window retained as unapproved proposal. |
| **REQ-08** | TGT-02 | Deployment Management | Partially evidenced | 45-minute backout target retained as non-binding operational goal. |
| **CON-01** | GOV-01 | Information Security Management | Aligned / evidenced | Mandatory MFA enforcement confirmed and traced to criteria/tests. |
| **CON-02** | GOV-02 | Change Enablement | Partially evidenced | Mandatory change approval constraint confirmed; approval authority unresolved (`OQ-02`). |

PIPELINE_HANDOFF_COMPLETE: ITIL_ALIGNMENT
