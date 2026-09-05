# Dynamic Agent Invocation Result

- Agent: `ba-change-delivery-orchestrator`
- Run ID: `a001-g37-dynamic-invocation-016`
- Model: `gemini-3.7-flash`
- Status: `success`
- Operational status: `none`
- Selected Skills: `analyze-requirements -> decompose-requirements -> elaborate-acceptance-criteria -> derive-test-cases -> prepare-solution-change-readiness -> assess-itil-alignment`
- Total prompt tokens: `39531`
- Total candidate tokens: `18924`
- Total thought tokens: `9230`
- Total tokens: `67685`

## Agent routing decision

```json
{
  "objective": "Deliver an end-to-end BA requirements and testing baseline for the NimbusHR corporate identity migration, prepare a solution and change-readiness handoff, and assess evidence alignment against ITIL 4 practice concepts while preserving all uncertain states, target dates, disputes, and explicit local policy constraints without inventing architecture or approvals.",
  "selected_skills": [
    "analyze-requirements",
    "decompose-requirements",
    "elaborate-acceptance-criteria",
    "derive-test-cases",
    "prepare-solution-change-readiness",
    "assess-itil-alignment"
  ],
  "not_selected": [],
  "stop_rules": [
    "The 30 November date is a desired target date, not a committed delivery deadline; downstream stages must not treat it as a hard constraint.",
    "Entra SAML federation is a proposed mechanism with unverified tenant entitlement and must not be hardened into a confirmed architectural requirement.",
    "Contractor access is Disputed with an Unknown decision authority, and the 17 unmatched accounts remain unresolved; neither may be forced into Ready delivery items or committed acceptance criteria.",
    "SCIM automated provisioning is Deferred to Phase 2 and excluded from current cutover scope.",
    "The Saturday 22:00 cutover window and 45-minute recovery target remain unapproved proposals without committed mechanics.",
    "Preserve confirmed source-backed outcomes: the Security Standard mandating corporate identity and existing MFA for SaaS employee data access, and the local Change Policy requiring an approved change record prior to production implementation.",
    "Do not invent a named Change Authority, mandatory CAB sign-off, or unevidenced Standard Change template."
  ],
  "expected_final_artifact": "A complete, traceable BA delivery package comprising normalized requirements, delivery work decomposition, acceptance criteria, and behavioral test cases for ready items, alongside a solution and change-readiness assessment highlighting known gaps and an ITIL 4 practice alignment evaluation."
}
```

---

## 1 — analyze-requirements

- Status: `success`
- Skill SHA-256: `9b3033fb72fff244c170fa49e5719db5bbb10b9f0b5694d151f2445b3a844130`

# Requirements Analysis: NimbusHR Corporate Identity Migration

## 1. Executive summary

This analysis evaluates the requirements for transitioning workforce access for the NimbusHR SaaS human resources platform from application-local passwords to corporate identity. The analysis baseline establishes confirmed organizational security and change policy mandates while strictly preserving the uncommitted status of proposed cutover timing, proposed technical mechanisms (Entra ID / SAML), unresolved employee identity mapping (17 accounts), deferred Phase 2 scope (SCIM), and an active policy dispute regarding contractor access where decision authority is currently unassigned.

---

## 2. Source register

| Source ID | Source Name / Reference | Description |
|---|---|---|
| **S1** | Benchmark 023 — NimbusHR Identity Change Packet | Primary source packet containing stakeholder statements, security standard extract, policy rules, and mapping data status. |

---

## 3. Business objective and scope

### Problem / Opportunity
Employees currently access the SaaS HR platform (NimbusHR) using application-local passwords, presenting security and compliance risks ahead of the annual audit cycle.

### Intended business outcome
Transition employee authentication from NimbusHR-local credentials to corporate identity backed by the organization's existing Multi-Factor Authentication (MFA) policy.

### Scope boundaries
- **In-Scope (Current Phase):** Transition of employee access to corporate identity and resolution of 603 matched employee identities (plus resolution of 17 currently unmatched employee accounts).
- **Disputed Scope:** Inclusion of contractor access within corporate guest identity versus retention of NimbusHR-local accounts.
- **Out of Scope (Deferred to Phase 2):** Automated user provisioning and deprovisioning via SCIM.
- **Delivery Timeframe Boundary:** A target delivery date of prior to 30 November (desired by HR for audit preparation), which remains an uncommitted target.

---

## 4. Stakeholders / actors

| Stakeholder / Actor | Evidenced activity / responsibility | Established decision authority |
|---|---|---|
| **Head of HR** | Expressed business need to eliminate local passwords and stated a desired completion target before 30 November for audit prep. | None established in evidence. |
| **Security (Team / Standard)** | Mandates corporate identity and existing MFA for SaaS containing employee data; advocates corporate guest identities for contractors. | Standard mandates authentication controls; authority over contractor dispute is not established. |
| **Identity Team** | Reviewed public product documentation and identified Entra ID SAML integration as a candidate mechanism. | Technical evaluation; no architectural or policy approval authority established. |
| **HR Operations** | Manages day-to-day HR admin; advocates local accounts for contractors due to guest lifecycle effort concerns. | None established in evidence. |
| **Release Manager** | Proposed a candidate cutover execution window (Saturday at 22:00). | None established in evidence (explicitly noted window is unapproved). |
| **Service Desk** | Suggested a candidate 45-minute recovery target for rollback. | None established in evidence. |
| **Operations** | Identified change profile as likely Normal Change in the absence of a Standard Change template. | None established in evidence. |
| **Change Authority** | Required by local Change Policy to approve change record prior to production implementation. | **Unknown** (role/body not identified in source). |
| **Employees (~620)** | End users of NimbusHR platform subject to authentication migration. | N/A (End-user population). |
| **Contractors** | External personnel accessing NimbusHR; identity handling method disputed. | N/A (Subject population). |

---

## 5. Requirements register

| ID | Requirement | Type | Evidence class | Requirement status | Source | Evidence / rationale | Confidence |
|---|---|---|---|---|---|---|---|
| **REQ-001** | Workforce access to SaaS applications containing employee data must use corporate identity and the organization's existing MFA policy. | Security/compliance requirement | Explicit | Confirmed | S1 | Directly mandated by the organizational Security Standard. Protocol is unspecified. | High |
| **REQ-002** | Production implementation of customer- or workforce-impacting authentication changes must have an approved change record prior to execution. | Constraint | Explicit | Confirmed | S1 | Directly mandated by local Change Policy. Specific Change Authority role is not named. | High |
| **REQ-003** | Workforce authentication transition should target completion before 30 November to support the annual audit cycle. | Business requirement | Explicit | Target | S1 | Desired by Head of HR; source explicitly confirms this is not a committed delivery deadline. | High |
| **REQ-004** | The authentication solution may utilize Microsoft Entra ID enterprise application SAML federation if tenant entitlement and technical compatibility are verified. | Functional requirement | Explicit | Candidate | S1 | Proposed by Identity Team based on public product documentation; tenant feature enablement remains unverified. | High |
| **REQ-005** | The migration scope shall include 603 verified employee accounts and must determine the disposition/mapping of 17 currently unresolved accounts. | Functional requirement | Explicit | Candidate | S1 | Draft mapping contains 603 matches and 17 unresolved records requiring identity resolution prior to cutover. | High |
| **REQ-006** | Contractor identity handling shall adhere to an agreed organizational policy determining whether contractors retain NimbusHR-local accounts or transition to corporate guest identities. | Business rule | Disputed | Disputed | S1 | HR Operations and Security hold conflicting positions; governance authority to settle dispute is unassigned. | High |
| **REQ-007** | Automated user provisioning and deprovisioning via SCIM is deferred to Phase 2 and is excluded from the current cutover scope. | Functional requirement | Explicit | Deferred | S1 | Suggested for Phase 2; vendor capability and tenant entitlement unverified; explicitly excluded from current scope. | High |
| **REQ-008** | Production cutover is proposed to execute within a Saturday 22:00 window, subject to formal change review and approval. | Constraint | Explicit | Candidate | S1 | Proposed by Release Manager; source explicitly states window is not yet approved. | High |
| **REQ-009** | Authentication rollback procedures aim to achieve a target recovery duration of approximately 45 minutes if backout is required. | Non-functional requirement | Explicit | Target | S1 | Suggested by Service Desk; no backout mechanics exist and no commitment has been established. | High |
| **REQ-010** | Change enablement governance should treat this implementation as a Normal Change unless an applicable Standard Change template is evidenced. | Constraint | Inferred | Candidate | S1 | Operations noted change is probably Normal unless a Standard Change template applies; no template was provided. | Medium |

---

## 6. Contradictions and ambiguities

### 1. Contractor Access Model Dispute
- **Competing positions:** 
  - *HR Operations:* Wants contractors to retain NimbusHR-local accounts to avoid administrative guest-account lifecycle overhead.
  - *Security:* Requires contractor access to be routed through corporate guest identities with existing MFA controls.
- **Required outcome / decision:** Establish whether contractor accounts are in scope for corporate identity migration or exempted via local accounts.
- **Decision owner:** **Unknown** (no authority is established in supplied evidence).

### 2. Status of the 30 November Target Date
- **Competing positions / ambiguity:** Head of HR expressed a strong preference for completion before 30 November for the annual audit, but the date has not been formally committed by delivery teams.
- **Required outcome / decision:** Establish a committed delivery baseline schedule and determine whether failing to meet 30 November is a hard release blocker or an operational risk.
- **Decision owner:** **Unknown**.

### 3. Identity Resolution for 17 Unmatched Accounts
- **Competing positions / ambiguity:** 603 accounts are mapped, but 17 accounts in the draft mapping spreadsheet lack identity resolution.
- **Required outcome / decision:** Validate the 17 records to determine if they represent active employees, stale accounts, contractors, or data discrepancies, and establish a resolution protocol.
- **Decision owner:** **Unknown**.

### 4. Entra ID / SAML Technical and Commercial Feasibility
- **Competing positions / ambiguity:** SAML federation via Entra ID was identified as a candidate solution from public documentation, but the organization's NimbusHR tenant subscription/tier entitlement and technical configuration compatibility are unverified.
- **Required outcome / decision:** Verify NimbusHR tenant licensing entitlement and confirm protocol compatibility before committing to a technical architecture.
- **Decision owner:** **Unknown**.

### 5. Production Cutover Window and Recovery Duration
- **Competing positions / ambiguity:** Release Manager suggested Saturday at 22:00 (unapproved); Service Desk suggested a 45-minute recovery target (uncommitted, with no designed backout mechanism).
- **Required outcome / decision:** Formally define and approve the implementation window, recovery duration objective, and rollback procedures.
- **Decision owner:** **Unknown**.

---

## 7. Assumptions

| ID | Assumption Statement | Rationale |
|---|---|---|
| **ASM-001** | The total workforce population requiring NimbusHR access is approximately 620 employees (based on 603 matched + 17 unmatched accounts). | Derived directly from the preliminary user mapping spreadsheet in S1. |
| **ASM-002** | "Workforce access to SaaS applications containing employee data" encompasses all employee users logging into NimbusHR. | The Security Standard applies corporate identity and MFA mandates to all employee data SaaS platforms. |
| **ASM-003** | Standard Change governance cannot be applied until an approved, pre-authorized Standard Change model/template is produced. | Operations suggested a Normal Change path by default; no Standard Change template exists in the evidence. |

---

## 8. Analyst proposals

*Note: The following items are non-binding analyst suggestions and must not be treated as confirmed requirements or stakeholder decisions.*

- **PRO-001 (Governance):** Convene an authorized joint session between HR Leadership, Security Leadership, and IT Operations to formally assign decision ownership for the contractor access dispute and sign off on the 30 November schedule commitment.
- **PRO-002 (Technical Discovery):** Conduct an administrative tenant audit of NimbusHR to inspect the current subscription plan, verify whether SAML 2.0 Single Sign-On is unlocked, and perform a non-production federation handshake proof-of-concept.
- **PRO-003 (Data Remediation):** Provide the list of 17 unresolved accounts to HR Operations for manual data cleansing and verification against the corporate HRIS/directory prior to cutover planning.
- **PRO-004 (Rollback Design):** Develop a documented backout procedure that preserves NimbusHR-local credential fallback until corporate identity stability is proven, validating whether a 45-minute target is technically feasible.

---

## 9. Open questions — prioritized

1. **[Governance / Policy]** Who owns the formal authority to resolve the contractor identity model dispute between Security and HR Operations?
2. **[Governance / Change]** Who is the designated Change Authority responsible for approving the change record for this workforce-impacting authentication change?
3. **[Scope / Schedule]** Is the 30 November target date a hard audit cut-off, or can delivery proceed past this date under a formal risk acceptance?
4. **[Data / Operations]** What is the identity status and business classification of the 17 unmatched accounts in the mapping spreadsheet?
5. **[Technical / Commercial]** Does the organization's current NimbusHR tenant subscription include SAML SSO capabilities, or does it require a commercial tier upgrade?
6. **[Operations / Change]** Does an approved Standard Change template exist for enterprise SaaS identity migrations, or must this proceed through Normal Change governance?
7. **[Service Continuity]** What specific technical mechanism will be used to execute a rollback within the proposed 45-minute recovery window if authentication fails during cutover?

---

## 10. Not established / out of scope

### Not established in source evidence
- The specific identity of the **Change Authority** or required approval body (CAB is not universally specified).
- Confirmation of NimbusHR tenant feature enablement or commercial tier for SAML SSO.
- An approved production cutover window or schedule.
- A designed and validated technical rollback/recovery procedure.
- Final user support models, Service Desk scripts, or workforce communication plans.
- Telemetry, logging, or operational monitoring validation methods during cutover.
- Decision authority for policy conflicts.

### Explicitly out of scope
- **SCIM automated user provisioning/deprovisioning** (explicitly deferred to Phase 2).

---

## 11. Readiness for decomposition

**Status:** **Partially ready**

**Reason:** 
Core security compliance constraints (REQ-001) and change policy rules (REQ-002) are confirmed and ready for baseline governance tracking. However, decomposition into final delivery work and acceptance criteria for cutover execution is blocked by significant unknowns and uncommitted dependencies:
1. Contractor scope is actively **Disputed** with an **Unknown** decision authority.
2. 17 employee accounts remain unresolved.
3. Federation mechanism (SAML via Entra ID) remains an unverified **Candidate**.
4. Cutover window and recovery duration remain unapproved **Proposals / Targets**.
5. Automated provisioning (SCIM) is explicitly **Deferred**.

Downstream stages must preserve these boundaries and avoid hardening candidate mechanisms, unassigned authorities, or target dates into committed acceptance criteria.

---

## 2 — decompose-requirements

- Status: `success`
- Skill SHA-256: `51ca53c4113d96ccb60d87988d2c66c089b99274fc439ffaefbcec4e9085e9b5`

# Delivery Decomposition: NimbusHR Corporate Identity Migration

## 1. Decomposition readiness

**Status:** **Partially Ready**

**Rationale:**  
The confirmed core security policy outcome (REQ-001: workforce authentication via corporate identity and existing MFA) and change governance constraint (REQ-002: approved change record prior to production implementation) are sufficiently understood to establish baseline delivery items. 

However, full execution readiness is constrained because:
- Technical federation feasibility and tenant entitlement (REQ-004) remain an unverified candidate mechanism requiring discovery.
- Contractor access model (REQ-006) is disputed with an **Unknown** decision authority.
- 17 employee accounts (REQ-005) remain unresolved.
- Implementation timing (Saturday 22:00 window, REQ-008) and recovery duration (45-minute target, REQ-009) remain unapproved proposals/targets without committed mechanics.
- Phase 2 automated provisioning via SCIM (REQ-007) is explicitly deferred.

---

## 2. Upstream requirement-status map

| Upstream ID | Requirement Summary | Upstream Status | Delivery Disposition |
|---|---|---|---|
| **REQ-001** | Workforce access to SaaS with employee data must use corporate identity and existing MFA policy. | Confirmed | Decomposed into committed User Story (`US-01`), blocked on technical feasibility spike. |
| **REQ-002** | Customer- or workforce-impacting authentication changes require an approved change record prior to production implementation. | Confirmed | Decomposed into Technical/Governance Enabler (`TASK-01`) and external Dependency (`DEP-01`). |
| **REQ-003** | Transition should target completion before 30 November for the annual audit cycle. | Target | Preserved as Planning Target (`CAND-05`), Decision Item (`DEC-03`), and Delivery Risk (`RISK-01`). |
| **REQ-004** | Authentication may use Microsoft Entra ID enterprise app SAML federation if tenant entitlement and compatibility are verified. | Candidate | Decomposed into Discovery Spike (`SPIKE-01`), Candidate Item (`CAND-01`), and Dependency (`DEP-03`). |
| **REQ-005** | Migration scope includes 603 verified employee accounts and must determine disposition of 17 unresolved accounts. | Candidate | Verified mapping decomposed into Technical Task (`TASK-02`); unresolved accounts isolated in Decision Item (`DEC-02`), Dependency (`DEP-02`), and Candidate Scope (`CAND-02`). |
| **REQ-006** | Contractor identity handling policy (NimbusHR-local accounts vs corporate guest identities). | Disputed | Isolated into Decision Item (`DEC-01`), Candidate Scope (`CAND-04`), and Delivery Risk (`RISK-02`). |
| **REQ-007** | Automated user provisioning/deprovisioning via SCIM deferred to Phase 2. | Deferred | Isolated into Deferred Backlog (`DEF-01`). Excluded from current cutover scope. |
| **REQ-008** | Production cutover proposed for Saturday at 22:00, subject to approval. | Candidate | Isolated into Decision Item (`DEC-03`) and Candidate Scope (`CAND-03`). |
| **REQ-009** | Authentication rollback procedures target a recovery duration of approximately 45 minutes. | Target | Preserved as Discovery Spike (`SPIKE-02`), Planning Target (`CAND-06`), and Delivery Risk (`RISK-03`). |
| **REQ-010** | Change governance treats change as Normal Change unless a Standard Change template is evidenced. | Candidate | Decomposed into Decision Item (`DEC-04`) and Enabler Task alignment (`TASK-01`). |

---

## 3. Epics / capabilities

- **EPIC-01: Workforce Identity Authentication Transition**  
  *Outcome:* Transition employee access to NimbusHR from local credentials to corporate identity backed by the organization's existing MFA policy.
- **EPIC-02: Change Enablement and Implementation Governance**  
  *Outcome:* Prepare, validate, and satisfy organizational change governance requirements to obtain required change record approval prior to production execution.

---

## 4. Current delivery backlog

| ID | Type | Item | Upstream requirement(s) | Delivery status | Blocker / dependency |
|---|---|---|---|---|---|
| **US-01** | User Story | As an employee, I want to authenticate to NimbusHR using corporate identity and the organisation's existing MFA policy, so that I no longer rely on NimbusHR-local passwords. | REQ-001 | Blocked | Blocked on `SPIKE-01` (tenant federation feasibility), `DEC-02` (resolution of 17 accounts), and `DEP-01` (change approval). |
| **TASK-01** | Enabler / Technical Task | Prepare change record documentation satisfying local Change Policy for a workforce-impacting authentication transition prior to production execution. | REQ-002, REQ-010 | Blocked | Blocked on `DEC-03` (cutover window definition), `DEC-04` (change model selection), and `SPIKE-02` (rollback procedure definition). |
| **TASK-02** | Enabler / Technical Task | Map the 603 verified employee identity records from the draft mapping spreadsheet to corresponding corporate identities. | REQ-005 | Ready | None. (Applies strictly to the 603 confirmed matching records). |

*Note on Acceptance Anchors:*  
- `US-01`: Authentication succeeds via corporate identity; existing corporate MFA policy is enforced; NimbusHR-local passwords are no longer used for verified employees.  
- `TASK-01`: A formal change record is submitted and approved prior to cutover execution.  
- `TASK-02`: 603 employee records have verified 1:1 corporate identity mappings.

---

## 5. Decision items

| ID | Decision required | Competing options / positions | Decision owner | Blocked / conditional items | Upstream requirement(s) |
|---|---|---|---|---|---|
| **DEC-01** | Contractor Identity Access Model | **Option A:** Retain NimbusHR-local accounts (HR Operations position to reduce guest lifecycle effort).<br>**Option B:** Transition to corporate guest identities with MFA (Security position). | **Unknown** | `CAND-04`, contractor scope cutover. | REQ-006 |
| **DEC-02** | Resolution and Disposition of 17 Unmatched Employee Accounts | Establish classification and disposition for the 17 unverified records (e.g., active employees requiring data correction, inactive/stale accounts, or contractors). | **Unknown** | `CAND-02`, complete employee population transition. | REQ-005 |
| **DEC-03** | Production Cutover Window and Delivery Schedule Baseline | Evaluate and agree production execution schedule (including the proposed Saturday 22:00 window) and assess schedule viability against the 30 November audit target. | **Unknown** | `TASK-01`, `CAND-03`, `CAND-05`. | REQ-003, REQ-008 |
| **DEC-04** | Change Governance Path Selection | Determine whether the implementation proceeds under Normal Change governance or if an applicable approved Standard Change template exists. | **Unknown** | `TASK-01`. | REQ-010 |

---

## 6. Spikes / discovery items

| ID | Question to answer | Evidence / output needed | Unblocks / informs | Upstream requirement(s) |
|---|---|---|---|---|
| **SPIKE-01** | Does the organisation's NimbusHR tenant have SAML/SSO federation enabled/entitled, and is it compatible with the corporate identity provider? | Verified tenant feature entitlement status, subscription tier confirmation, and protocol compatibility evidence. | `US-01`, `CAND-01` (Technical configuration and implementation). | REQ-004 |
| **SPIKE-02** | What technical backout mechanism is available to revert authentication to local credentials if cutover fails, and can it support the 45-minute recovery target? | Documented, feasible rollback procedure with estimated recovery steps and verification criteria. | `TASK-01`, `CAND-06` (Change record backout plan and recovery target validation). | REQ-009 |

---

## 7. Dependencies and risks

### Dependencies

| ID | Dependency description | Responsible party / owner | Upstream requirement(s) |
|---|---|---|---|
| **DEP-01** | Formal approval of the change record by the designated Change Authority prior to production implementation. | **Unknown** (Change Authority role not identified in source) | REQ-002 |
| **DEP-02** | Source data remediation providing confirmed identity details for the 17 unmatched employee accounts. | **Unknown** | REQ-005 |
| **DEP-03** | Confirmation of NimbusHR subscription tier capabilities and federation enablement. | Identity Team / NimbusHR Tenant Administrator | REQ-004 |

### Risks

| ID | Risk statement | Upstream requirement(s) |
|---|---|---|
| **RISK-01** | The 30 November target date is uncommitted; failure to achieve production cutover prior to December may impact the annual audit cycle. | REQ-003 |
| **RISK-02** | Disputed contractor access handling with an unassigned decision owner may stall delivery scope agreement or result in inconsistent security control application. | REQ-006 |
| **RISK-03** | Lack of a designed and validated technical rollback mechanism introduces operational recovery uncertainty if cutover fails. | REQ-009 |

---

## 8. Candidate backlog / conditional scope

The following items are proposed or candidate scope and are **not committed** to the delivery baseline:

| ID | Candidate item description | Condition for activation | Upstream requirement(s) |
|---|---|---|---|
| **CAND-01** | Implementation of Entra ID SAML enterprise application federation. | Conditional on positive verification from `SPIKE-01` and tenant entitlement confirmation (`DEP-03`). | REQ-004 |
| **CAND-02** | Transition and mapping of the 17 unresolved employee accounts. | Conditional on resolution of account identities via `DEC-02` and data delivery via `DEP-02`. | REQ-005 |
| **CAND-03** | Execution of cutover within the Saturday 22:00 window. | Conditional on cutover schedule decision `DEC-03` and change approval `DEP-01`. | REQ-008 |
| **CAND-04** | Contractor authentication transition to corporate guest identities. | Conditional on policy dispute decision `DEC-01` favoring corporate guest identity model. | REQ-006 |
| **CAND-05** | *Planning Target:* Complete workforce authentication cutover prior to 30 November. | Non-binding business target desired for audit cycle; subject to `DEC-03` schedule baseline. | REQ-003 |
| **CAND-06** | *Planning Target:* Complete authentication rollback within 45 minutes if backout is triggered. | Non-binding operational target suggested by Service Desk; subject to feasibility outcome in `SPIKE-02`. | REQ-009 |

---

## 9. Deferred / future backlog

| ID | Item | Rationale / evidence | Upstream requirement(s) |
|---|---|---|---|
| **DEF-01** | Automated user provisioning and deprovisioning via SCIM (Phase 2). | Explicitly deferred to Phase 2; vendor capability and tenant entitlement are unverified. Excluded from current cutover scope. | REQ-007 |

---

## 10. Traceability summary

| Upstream Requirement ID | Upstream Requirement Status | Decomposed Work Item ID(s) | Work Item Status / Type |
|---|---|---|---|
| **REQ-001** | Confirmed | `EPIC-01`, `US-01` | Epic, User Story (Blocked) |
| **REQ-002** | Confirmed | `EPIC-02`, `TASK-01`, `DEP-01` | Epic, Enabler Task (Blocked), Dependency |
| **REQ-003** | Target | `DEC-03`, `CAND-05`, `RISK-01` | Decision Item, Planning Target, Risk |
| **REQ-004** | Candidate | `SPIKE-01`, `CAND-01`, `DEP-03` | Discovery Spike, Candidate Item, Dependency |
| **REQ-005** | Candidate | `TASK-02`, `DEC-02`, `DEP-02`, `CAND-02` | Enabler Task (Ready), Decision Item, Dependency, Candidate Scope |
| **REQ-006** | Disputed | `DEC-01`, `CAND-04`, `RISK-02` | Decision Item, Candidate Scope, Risk |
| **REQ-007** | Deferred | `DEF-01` | Deferred Item |
| **REQ-008** | Candidate | `DEC-03`, `CAND-03` | Decision Item, Candidate Scope |
| **REQ-009** | Target | `SPIKE-02`, `CAND-06`, `RISK-03` | Discovery Spike, Planning Target, Risk |
| **REQ-010** | Candidate | `TASK-01`, `DEC-04` | Enabler Task (Blocked), Decision Item |

---

## 11. Readiness for acceptance-criteria elaboration

- **Items Ready for Acceptance-Criteria Elaboration:**
  - `US-01`: Baseline authentication behavior (corporate identity authentication and MFA enforcement vs local password elimination for verified employees).
  - `TASK-01`: Core change record submission requirements under local Change Policy.
  - `TASK-02`: Mapping criteria and verification rules for the 603 matched employee accounts.

- **Items NOT Ready for Acceptance-Criteria Elaboration (Must remain blocked):**
  - Contractor access rules (blocked by `DEC-01`).
  - Account mapping criteria for the 17 unmatched accounts (blocked by `DEC-02` and `DEP-02`).
  - Specific technical federation protocol configurations / SAML assertions (blocked by `SPIKE-01` and `DEP-03`).
  - Hardened delivery deadline of 30 November (remains non-binding target `CAND-05` / `RISK-01`).
  - Hardened 45-minute recovery SLA (remains non-binding target `CAND-06` / `SPIKE-02`).
  - Automated provisioning / SCIM rules (deferred via `DEF-01`).

---

## 3 — elaborate-acceptance-criteria

- Status: `success`
- Skill SHA-256: `852acfee189a2b88418f3f2fd948ff96ddaee23f9e6a620563bf06a94c380d0d`

# Acceptance Criteria: NimbusHR Corporate Identity Migration

## 1. Acceptance-criteria readiness

**Status:** **Partially Ready**

**Rationale:**  
Acceptance criteria can be elaborated for confirmed, source-backed outcomes:
- Mapping of the 603 verified employee identities (`TASK-02`).
- Confirmed baseline authentication outcomes under the Security Standard (corporate identity authentication and corporate MFA enforcement for employees, eliminating reliance on NimbusHR-local passwords for verified employees under `US-01`).
- Confirmed governance constraint under local Change Policy (production implementation requires an approved change record under `TASK-01`).

Criteria cannot be finalized for technical federation mechanism specifics (`REQ-004`), contractor access model (`REQ-006`), the 17 unmatched accounts (`REQ-005`), production implementation schedule (`REQ-008`), recovery mechanics (`REQ-009`), or automated provisioning (`REQ-007`).

---

## 2. Item/readiness map

| Item ID | Item type | Delivery status | Upstream requirement ID(s) | Elaboration readiness |
|---|---|---|---|---|
| **TASK-02** | Technical Task | Ready | REQ-005 | **Ready** — Elaborate full criteria for the 603 verified employee records. |
| **US-01** | User Story | Blocked | REQ-001, REQ-004 | **Partially Ready** — Elaborate baseline policy conditions; isolate technical mechanism, contractor, and unresolved account criteria as Blocked. |
| **TASK-01** | Technical / Governance Enabler | Blocked | REQ-002, REQ-010 | **Partially Ready** — Elaborate core policy approval constraint; isolate change model and execution window criteria as Blocked. |
| **DEC-01** | Decision Item | Disputed / Unknown | REQ-006 | **Not Ready (Blocked)** — Preserved as open dispute. |
| **DEC-02** | Decision Item | Blocked | REQ-005 | **Not Ready (Blocked)** — Preserved pending source remediation. |
| **DEC-03** | Decision Item | Candidate / Target | REQ-003, REQ-008 | **Not Ready (Conditional / Target)** — Handled under candidate and target sections. |
| **DEC-04** | Decision Item | Candidate | REQ-010 | **Not Ready (Blocked)** — Preserved pending standard template evidence. |
| **SPIKE-01** | Discovery Spike | Candidate | REQ-004 | **Not Ready (Candidate)** — Feasibility investigation. |
| **SPIKE-02** | Discovery Spike | Target | REQ-009 | **Not Ready (Target)** — Rollback feasibility investigation. |
| **DEF-01** | Deferred Item | Deferred | REQ-007 | **Deferred** — Excluded from current criteria elaboration. |

---

## 3. Acceptance criteria for Ready items and confirmed baseline behavior

| Criterion ID | Delivery item | Acceptance condition | Evidence basis | Upstream requirement(s) | Status |
|---|---|---|---|---|---|
| **TASK02-AC01** | TASK-02 | Exactly 603 verified employee records from the draft mapping spreadsheet are mapped to corresponding corporate identity accounts. | Explicit | REQ-005 | Ready |
| **TASK02-AC02** | TASK-02 | Each of the 603 verified employee records establishes a unique 1:1 association between the NimbusHR account and the corporate identity. | Explicit | REQ-005 | Ready |
| **US01-AC01** | US-01 | A mapped employee accessing NimbusHR authenticates successfully via corporate identity. | Explicit | REQ-001 | Ready (Baseline) |
| **US01-AC02** | US-01 | A mapped employee accessing NimbusHR is required to satisfy the organisation's existing MFA policy during authentication. | Explicit | REQ-001 | Ready (Baseline) |
| **US01-AC03** | US-01 | *Derived boundary:* A mapped employee is not permitted to authenticate to NimbusHR using a NimbusHR-local password. | Derived boundary | REQ-001 | Ready (Baseline) |
| **TASK01-AC01** | TASK-01 | *Derived boundary:* Production implementation of the NimbusHR workforce authentication change does not proceed without an approved change record. | Derived boundary | REQ-002 | Ready (Baseline) |

---

## 4. Partially Ready / blocked criteria and open questions

The following criteria cannot be finalized as pass/fail conditions because their underlying behaviors, configurations, or authority decisions remain unresolved:

| Item ID | Unresolved condition / blocked criteria | Blocker / open question / dependency | Upstream requirement(s) |
|---|---|---|---|
| **US-01 / CAND-01** | Federation protocol configuration criteria (e.g., Entra ID SAML enterprise app integration, assertion attributes, endpoints). | **SPIKE-01 / DEP-03:** Tenant entitlement and protocol compatibility on the organisation's NimbusHR tenant have not been verified. | REQ-004 |
| **US-01 / CAND-02** | Authentication criteria for the 17 unmatched employee accounts. | **DEC-02 / DEP-02:** Decision on identity classification and source data remediation for the 17 unresolved accounts is pending (decision owner **Unknown**). | REQ-005 |
| **US-01 / CAND-04** | Contractor authentication behavior (whether contractors authenticate via corporate guest identities with MFA or retain NimbusHR-local credentials). | **DEC-01 / RISK-02:** Disputed policy between HR Operations (local accounts) and Security (corporate guest identities). Decision owner is **Unknown**. | REQ-006 |
| **TASK-01 / DEC-04** | Change submission criteria specific to Normal Change vs Standard Change path. | **DEC-04:** Operations indicates Normal Change unless an applicable Standard Change template is evidenced; no template evidence is supplied. | REQ-010 |
| **TASK-01 / DEP-01** | Change approval workflow and sign-off criteria. | **DEP-01:** Local Change Policy mandates an approved change record, but the specific Change Authority is **Unknown** and mandatory CAB approval is not evidenced. | REQ-002 |
| **TASK-01 / SPIKE-02** | Implementation rollback procedure acceptance criteria. | **SPIKE-02 / RISK-03:** Technical backout mechanics are unevidenced and unapproved. | REQ-009 |

---

## 5. Candidate / conditional acceptance notes

These conditions are candidate proposals and are non-committed. They become active only upon resolution of specific preconditions:

- **COND-01 (Entra SAML Federation — CAND-01):**  
  *Condition:* If `SPIKE-01` confirms that the organisation's NimbusHR tenant supports and is entitled to SAML enterprise application federation, acceptance criteria will specify Entra ID SAML authentication endpoints and token exchange.  
  *Traceability:* REQ-004, SPIKE-01.

- **COND-02 (Unmatched 17 Accounts — CAND-02):**  
  *Condition:* If `DEC-02` resolves the identity status of the 17 unmatched records and data is supplied via `DEP-02`, acceptance criteria will be extended to cover mapping and authentication for those confirmed accounts.  
  *Traceability:* REQ-005, DEC-02, DEP-02.

- **COND-03 (Cutover Window Execution — CAND-03):**  
  *Condition:* If `DEC-03` and the designated Change Authority approve the Release Manager's proposed window, production execution criteria will anchor to Saturday at 22:00.  
  *Traceability:* REQ-008, DEC-03, DEP-01.

- **COND-04 (Contractor Identity Model — CAND-04):**  
  *Condition:* If `DEC-01` is resolved by the authorized owner in favor of Security's position, criteria will require corporate guest identities and MFA for contractors; if resolved in favor of HR Operations, criteria will verify retention of local credentials.  
  *Traceability:* REQ-006, DEC-01.

---

## 6. Planning / quality targets

The following non-binding targets are preserved for planning, monitoring, and quality evaluation. They are explicitly **not** mandatory pass/fail acceptance criteria for baseline delivery items:

- **TGT-01 (Schedule Target — CAND-05):**  
  *Description:* Complete workforce authentication transition prior to 30 November to support the annual audit cycle.  
  *Status:* Desired business target; non-binding on acceptance.  
  *Traceability:* REQ-003, RISK-01.

- **TGT-02 (Recovery Duration Target — CAND-06):**  
  *Description:* Execute authentication rollback within an operational duration of approximately 45 minutes if cutover failure occurs.  
  *Status:* Service Desk operational target; non-binding SLA pending feasibility outcome in `SPIKE-02`.  
  *Traceability:* REQ-009, SPIKE-02, RISK-03.

---

## 7. Deferred items

- **DEF-01 (Automated Provisioning via SCIM):**  
  *Description:* Automated user provisioning and deprovisioning via SCIM is deferred to Phase 2.  
  *Action:* No acceptance criteria are elaborated in the current baseline. Vendor capability and tenant entitlement remain unverified.  
  *Traceability:* REQ-007.

---

## 8. Traceability summary

| Upstream Requirement ID | Delivery Item ID | Acceptance Criterion / Condition ID | Criterion Type | Criterion Status |
|---|---|---|---|---|
| **REQ-001** | US-01 | `US01-AC01` | Functional outcome | Ready (Baseline) |
| **REQ-001** | US-01 | `US01-AC02` | Security / compliance constraint | Ready (Baseline) |
| **REQ-001** | US-01 | `US01-AC03` | Business-rule boundary (Derived boundary) | Ready (Baseline) |
| **REQ-002** | TASK-01 | `TASK01-AC01` | Business-rule boundary (Derived boundary) | Ready (Baseline) |
| **REQ-003** | CAND-05 | `TGT-01` | Planning / quality target | Target (Non-binding) |
| **REQ-004** | US-01, CAND-01 | `COND-01` | Candidate / conditional note | Blocked on SPIKE-01 |
| **REQ-005** | TASK-02 | `TASK02-AC01` | Data / audit outcome | Ready |
| **REQ-005** | TASK-02 | `TASK02-AC02` | Business-rule boundary | Ready |
| **REQ-005** | CAND-02 | `COND-02` | Candidate / conditional note | Blocked on DEC-02 |
| **REQ-006** | CAND-04 | `COND-04` | Candidate / conditional note | Blocked on DEC-01 (Disputed) |
| **REQ-007** | DEF-01 | — | Deferred item | Deferred (Phase 2) |
| **REQ-008** | CAND-03 | `COND-03` | Candidate / conditional note | Blocked on DEC-03 |
| **REQ-009** | CAND-06 | `TGT-02` | Planning / quality target | Target (Non-binding) |
| **REQ-010** | TASK-01 | `DEC-04` alignment | Blocked criterion | Blocked on template evidence |

---

## 9. Readiness for test-case elaboration

- **Ready for Test-Case Elaboration:**
  - `TASK02-AC01` & `TASK02-AC02`: Test cases covering verification and validation of the 603 matched employee identity mappings.
  - `US01-AC01`, `US01-AC02`, & `US01-AC03`: Test cases verifying corporate identity authentication success, corporate MFA enforcement, and the prohibition of NimbusHR-local passwords for verified employees.
  - `TASK01-AC01`: Test / assurance verification confirming change record approval exists prior to production implementation.

- **NOT Ready for Test-Case Elaboration (Gated):**
  - Protocol-specific SAML assertion/attribute test cases (gated by `SPIKE-01`).
  - Test cases for the 17 unmatched employee accounts (gated by `DEC-02` and `DEP-02`).
  - Contractor authentication test cases (gated by `DEC-01`).
  - Production schedule timing assertions (gated by `DEC-03`).
  - Timed backout execution test cases against a 45-minute pass/fail SLA (gated by `SPIKE-02`).
  - SCIM provisioning test cases (deferred under `DEF-01`).

---

## 4 — derive-test-cases

- Status: `success`
- Skill SHA-256: `5105a2f0965663cf0f7f24ecedd8b8dc11f3d20afdc2815e25a224d7297df995`

# Test Cases and Assurance Baseline: NimbusHR Corporate Identity Migration

## 1. Test-design readiness

**Status:** **Partially Ready**

**Rationale:**  
Test cases and assurance checks are derived strictly for confirmed, Ready baseline acceptance criteria:
- Identity mapping verification for the 603 confirmed employee records (`TASK-02`).
- Successful corporate identity authentication, corporate MFA enforcement, and elimination of NimbusHR-local password authentication for mapped employees (`US-01`).
- Governance assurance requiring an approved change record prior to production implementation under local Change Policy (`TASK-01`).

Test cases cannot be derived for protocol-specific SAML mechanics (`REQ-004`), contractor authentication (`REQ-006`), the 17 unmatched employee records (`REQ-005`), production cutover execution timing (`REQ-008`), recovery execution mechanics (`REQ-009`), or automated provisioning (`REQ-007`).

---

## 2. Acceptance-criterion readiness map

| Acceptance criterion ID | Delivery item | Upstream requirement ID(s) | Criterion status | Test derivation status |
|---|---|---|---|---|
| **TASK02-AC01** | TASK-02 | REQ-005 | Ready | **Derivable** — Covered by functional test case |
| **TASK02-AC02** | TASK-02 | REQ-005 | Ready | **Derivable** — Covered by functional test case |
| **US01-AC01** | US-01 | REQ-001 | Ready (Baseline) | **Derivable** — Covered by functional test case |
| **US01-AC02** | US-01 | REQ-001 | Ready (Baseline) | **Derivable** — Covered by functional test case |
| **US01-AC03** | US-01 | REQ-001 | Ready (Baseline) | **Derivable** — Covered by negative boundary test case |
| **TASK01-AC01** | TASK-01 | REQ-002 | Ready (Baseline) | **Derivable** — Covered by governance assurance check |
| **COND-01** (`CAND-01`) | US-01 | REQ-004 | Blocked (`SPIKE-01`) | **Untestable** — Gated on tenant entitlement / protocol feasibility |
| **COND-02** (`CAND-02`) | US-01 | REQ-005 | Blocked (`DEC-02`) | **Untestable** — Gated on resolution of 17 unmatched accounts |
| **COND-03** (`CAND-03`) | CAND-03 | REQ-008 | Candidate (`DEC-03`) | **Untestable** — Window is an unapproved proposal |
| **COND-04** (`CAND-04`) | CAND-04 | REQ-006 | Disputed (`DEC-01`) | **Untestable** — Gated on contractor access decision |
| **TGT-01** (`CAND-05`) | CAND-05 | REQ-003 | Target | **Non-binding** — Planning target, not a pass/fail test |
| **TGT-02** (`CAND-06`) | CAND-06 | REQ-009 | Target | **Non-binding** — Operational target, not a pass/fail test |
| **DEF-01** | DEF-01 | REQ-007 | Deferred | **Excluded** — Deferred to Phase 2 |

---

## 3. Test cases for Ready / confirmed portions

| Test ID | AC ID | Delivery item | Test condition | Expected outcome | Evidence basis | Upstream REQ(s) |
|---|---|---|---|---|---|---|
| **TC-01** | `TASK02-AC01` | TASK-02 | Draft user-mapping dataset for employee accounts is evaluated. | Exactly 603 verified employee records from the draft mapping spreadsheet are mapped to corresponding corporate identity accounts. | Explicit | REQ-005 |
| **TC-02** | `TASK02-AC02` | TASK-02 | Verified mapping dataset of 603 employee records is evaluated for identity association. | Each of the 603 verified employee records has a unique 1:1 association between the NimbusHR account and the corporate identity. | Explicit | REQ-005 |
| **TC-03** | `US01-AC01` | US-01 | A mapped employee attempts access to NimbusHR. | The mapped employee authenticates successfully via corporate identity. | Explicit | REQ-001 |
| **TC-04** | `US01-AC02` | US-01 | A mapped employee authenticates to NimbusHR via corporate identity. | The employee is required to satisfy the organisation's existing MFA policy during authentication. | Explicit | REQ-001 |
| **TC-05** | `US01-AC03` | US-01 | A mapped employee attempts to authenticate to NimbusHR using a NimbusHR-local password. | Authentication using the NimbusHR-local password is not permitted. | Derived boundary | REQ-001 |

---

## 4. Constraint / assurance checks

| Assurance Check ID | AC ID | Delivery item | Required condition / state to assure | Evidence basis | Upstream REQ(s) |
|---|---|---|---|---|---|
| **CHK-01** | `TASK01-AC01` | TASK-01 | An approved change record exists prior to production implementation of the NimbusHR workforce authentication change. | Derived boundary | REQ-002 |

---

## 5. Blocked and unresolved coverage

The following areas are preserved as untestable until upstream blockers and authority decisions are resolved:

- **Contractor access authentication (`DEC-01` / `REQ-006`):**  
  Untestable. Dispute between HR Operations (local credentials) and Security (corporate guest identities) remains open with an **Unknown** decision authority. No test cases can be derived until the access model is formally decided.
- **Unmatched employee records (`DEC-02` / `REQ-005`):**  
  Untestable. Identity resolution and data remediation for the 17 unmatched accounts remain unresolved (decision authority **Unknown**).
- **Federation protocol specifics (`SPIKE-01` / `REQ-004`):**  
  Untestable. Entra SAML integration endpoints, assertion attributes, and token exchange remain candidate mechanisms pending verification of NimbusHR tenant entitlement.
- **Change path and approval authority (`DEC-04` / `DEP-01` / `REQ-002`, `REQ-010`):**  
  Untestable. Normal Change classification is assumed absent evidence of an applicable Standard Change template, and the specific Change Authority is **Unknown**.
- **Rollback execution procedure (`SPIKE-02` / `REQ-009`):**  
  Untestable. Technical backout mechanics remain unevidenced and unapproved.

---

## 6. Candidate / conditional coverage notes

- **COND-01 (Entra SAML Federation — `CAND-01`):**  
  *Trigger:* If `SPIKE-01` confirms SAML feature availability and tenant entitlement on the organisation's NimbusHR tenant, derive protocol-specific federation test cases.
- **COND-02 (Unmatched 17 Accounts — `CAND-02`):**  
  *Trigger:* If `DEC-02` and `DEP-02` resolve the 17 unmatched accounts, derive mapping and authentication test cases for the remediated records.
- **COND-03 (Cutover Window Execution — `CAND-03`):**  
  *Trigger:* If `DEC-03` and the designated Change Authority formally approve the Saturday 22:00 window, derive execution schedule test conditions.
- **COND-04 (Contractor Identity Model — `CAND-04`):**  
  *Trigger:* If `DEC-01` is resolved, derive test cases verifying either corporate guest identity + MFA (Security model) or NimbusHR-local credential retention (HR Operations model).

---

## 7. Target / deferred coverage notes

- **TGT-01 (Schedule Target — `CAND-05` / `REQ-003`):**  
  *Status:* Completion before 30 November is a non-binding desired business target to precede the annual audit. It is preserved for project tracking and observation, not as a pass/fail test case or delivery gate.
- **TGT-02 (Recovery Duration Target — `CAND-06` / `REQ-009`):**  
  *Status:* The 45-minute rollback duration suggested by the Service Desk is a non-binding operational target. It is preserved for operational observation during recovery discovery (`SPIKE-02`), not as a committed test assertion.
- **DEF-01 (Automated Provisioning via SCIM — `REQ-007`):**  
  *Status:* Deferred to Phase 2. No test cases are derived for the current delivery baseline.

---

## 8. Traceability and coverage summary

| Upstream REQ ID | Delivery item | Acceptance criterion | Test / Check ID | Coverage type | Coverage status |
|---|---|---|---|---|---|
| **REQ-001** | US-01 | `US01-AC01` | `TC-03` | Functional test | Covered |
| **REQ-001** | US-01 | `US01-AC02` | `TC-04` | Functional test | Covered |
| **REQ-001** | US-01 | `US01-AC03` | `TC-05` | Boundary test | Covered |
| **REQ-002** | TASK-01 | `TASK01-AC01` | `CHK-01` | Assurance check | Covered |
| **REQ-003** | CAND-05 | `TGT-01` | — | Target observation | Preserved (Non-binding) |
| **REQ-004** | US-01 / SPIKE-01 | `COND-01` | — | Candidate test note | Blocked on SPIKE-01 |
| **REQ-005** | TASK-02 | `TASK02-AC01` | `TC-01` | Functional / Data test | Covered |
| **REQ-005** | TASK-02 | `TASK02-AC02` | `TC-02` | Functional / Data test | Covered |
| **REQ-005** | CAND-02 / DEC-02 | `COND-02` | — | Candidate test note | Blocked on DEC-02 |
| **REQ-006** | CAND-04 / DEC-01 | `COND-04` | — | Candidate test note | Blocked on DEC-01 (Disputed) |
| **REQ-007** | DEF-01 | — | — | Deferred item | Excluded (Phase 2) |
| **REQ-008** | CAND-03 / DEC-03 | `COND-03` | — | Candidate test note | Blocked on DEC-03 |
| **REQ-009** | CAND-06 / SPIKE-02 | `TGT-02` | — | Target observation | Preserved (Non-binding) |
| **REQ-010** | TASK-01 / DEC-04 | `DEC-04` alignment | — | Governance check | Blocked on template evidence |

---

## 9. Sourced blockers to further test derivation

The following explicit upstream items prevent deriving additional delivery test cases:

1. **`DEC-01` (Contractor Identity Dispute):** Access model is actively disputed between HR Operations and Security; decision authority is **Unknown**.
2. **`DEC-02` / `DEP-02` (17 Unmatched Accounts):** Source data resolution and mapping for 17 employee records remain incomplete; decision authority is **Unknown**.
3. **`SPIKE-01` / `DEP-03` (Tenant Entitlement & Protocol Capability):** Entra ID SAML federation capability on the organisation's NimbusHR tenant is unverified.
4. **`DEP-01` / `DEC-04` (Change Authority & Template Evidence):** Local Change Policy mandates an approved change record, but the Change Authority is **Unknown** and no matching Standard Change template is evidenced.
5. **`SPIKE-02` / `RISK-03` (Backout Mechanics):** Technical backout steps are unevidenced and unapproved.

---

## 5 — prepare-solution-change-readiness

- Status: `success`
- Skill SHA-256: `b18b5fc6db55de3c58c5af8af867352f37e8cb63998b33d4b464e88cf3cb8e5e`

# Solution and Change-Readiness Handoff: NimbusHR Corporate Identity Migration

## 1. Overall handoff readiness

**Overall status:** **Partially ready**

**Readiness rationale:**
- **Solution / design review readiness: Partially ready.** Confirmed business requirements (`REQ-001`), data mapping for 603 employee accounts (`REQ-005`), and mandatory security/governance constraints (`REQ-002`) are fully specified with traceable acceptance criteria and test designs. However, the technical integration mechanism (Entra SAML federation, `REQ-004`) remains a candidate hypothesis pending tenant entitlement verification (`SPIKE-01`), and contractor scope (`REQ-006`) is actively disputed.
- **Change enablement review readiness: Partially ready.** The policy requirement for an approved change record prior to production implementation is established (`REQ-002`, `TASK-01`, `CHK-01`). However, implementation procedures, backout mechanics, validation methods, communications, cutover window approval, and the specific Change Authority remain unevidenced and unapproved.
- **Test execution status:** Test designs (`TC-01` through `TC-05`) and assurance check (`CHK-01`) are defined for baseline items; no execution runs or test execution evidence have been supplied.

---

## 2. Evidence ready for handoff

The following baseline evidence is confirmed from upstream stages and ready for downstream technical and operational review:

### Confirmed scope and constraints
- **Mandatory Corporate Identity & MFA (`REQ-001` / `CON-01`):** Workforce access to SaaS applications containing employee data must use corporate identity and the organisation's existing MFA policy. NimbusHR-local password authentication must be discontinued for mapped workforce users.
- **Change Record Prerequisite (`REQ-002` / `CON-02`):** Local Change Policy mandates an approved change record prior to production implementation of customer- or workforce-impacting authentication changes.
- **Confirmed Identity Mapping Baseline (`REQ-005`):** 603 employee accounts in the draft mapping dataset are matched 1:1 with corporate identities.

### Ready delivery items & acceptance criteria
- **`US-01` (Workforce Corporate Authentication):** Criteria `US01-AC01` (successful corporate identity authentication), `US01-AC02` (enforcement of corporate MFA), and `US01-AC03` (prohibition of local password authentication).
- **`TASK-01` (Change Record Preparation):** Criterion `TASK01-AC01` (approved change record in place prior to production cutover).
- **`TASK-02` (User Account Mapping Verification):** Criteria `TASK02-AC01` (exact verification of 603 mapped records) and `TASK02-AC02` (unique 1:1 identity pairing).

### Test and assurance design baseline (non-executed)
- **Functional & Boundary Tests:** `TC-01`, `TC-02` (account mapping data validation), `TC-03`, `TC-04`, `TC-05` (corporate authentication, MFA enforcement, local password rejection).
- **Governance Assurance:** `CHK-01` (verification of approved change record before cutover).

---

## 3. Unresolved / non-committed register

| Item ID | Item category | Description | Current state | Known authority / owner | Upstream reference |
|---|---|---|---|---|---|
| **DEC-01** | Disputed scope | Contractor access model: HR Operations wants NimbusHR-local accounts; Security wants corporate guest identities. | Disputed | **Unknown** | `REQ-006` / `CAND-04` |
| **DEC-02** | Unresolved data | Remediate and map 17 unresolved employee accounts. | Unknown | **Unknown** | `REQ-005` / `CAND-02` / `DEP-02` |
| **SPIKE-01** | Candidate mechanism | Verification of NimbusHR Enterprise plan SAML capability and tenant entitlement for Entra federation. | Candidate | Identity Team / Vendor (unverified) | `REQ-004` / `CAND-01` / `DEP-03` |
| **DEC-03** | Unapproved proposal | Proposed production cutover window: Saturday at 22:00. | Candidate | Change Authority (**Unknown**) | `REQ-008` / `CAND-03` |
| **TGT-01** | Planning target | Complete change before 30 November (preceding annual December audit cycle). | Target (non-binding) | Head of HR (desire, not hard constraint) | `REQ-003` / `CAND-05` |
| **TGT-02** | Operational target | Service Desk suggested 45-minute recovery/rollback duration. | Target (non-binding) | Service Desk (desire, not committed) | `REQ-009` / `CAND-06` |
| **SPIKE-02** | Missing mechanism | Technical backout and recovery mechanics definition. | Missing evidence | Unassigned | `REQ-009` / `RISK-03` |
| **DEC-04** | Governance alignment | Change classification (assumed Normal Change absent Standard Change template) and Change Authority identification. | Partial / Unknown | Change Authority (**Unknown**) | `REQ-002` / `REQ-010` / `DEP-01` |
| **DEF-01** | Deferred scope | SCIM automated user provisioning and deprovisioning. | Deferred (Phase 2) | Excluded from current scope | `REQ-007` |

---

## 4. Solution/design review handoff

The downstream Solution / Design Review must evaluate the technical delivery package against the following constraints and open design questions:

### Functional and security constraints to satisfy
1. Must enforce corporate identity authentication and existing organizational MFA for all in-scope employee access to NimbusHR (`REQ-001`).
2. Must eliminate reliance on NimbusHR-local passwords for verified employee accounts (`REQ-001`).
3. Must ensure 1:1 account integrity across the verified 603 employee dataset (`REQ-005`).

### Technical design questions to resolve downstream (not invented here)
1. **Federation mechanism:** Is SAML 2.0 active and entitled on the specific NimbusHR tenant instance, and does Entra ID enterprise application configuration satisfy the authentication and assertion requirements (`SPIKE-01`)?
2. **Account remediation:** What mechanism will resolve the 17 unmatched employee identities (`DEP-02`)?
3. **Contractor identity handling:** Once `DEC-01` is resolved by appropriate authority, what technical access path (guest federation vs. local credential management) will be configured (`REQ-006`)?
4. **Technical backout procedure:** What is the technical step-by-step mechanism to restore NimbusHR-local authentication if corporate federation fails (`SPIKE-02`)?

---

## 5. Change-readiness evidence matrix

| Evidence area | State | Evidence available | Missing / unresolved | Traceability |
|---|---|---|---|---|
| **Change Classification & Policy** | Partial | Local Change Policy requirement for approved change record is explicit (`TASK-01`, `CHK-01`). Normal Change path assumed. | Evidence of applicable Standard Change template is absent; named Change Authority is **Unknown**. | `REQ-002`, `REQ-010`, `DEP-01`, `DEC-04` |
| **Cutover Scheduling & Window** | Partial | Saturday 22:00 window proposed by Release Manager (`CAND-03`). Business target before 30 November noted (`TGT-01`). | Formal approval of Saturday 22:00 window is missing; 30 November is non-binding. | `REQ-003`, `REQ-008`, `DEC-03`, `CAND-03` |
| **Implementation Plan & Architecture** | Partial | Core requirement defined (corporate identity + MFA for 603 mapped employees in `US-01`, `TASK-02`). | Technical design unconfirmed; SAML protocol feasibility and tenant entitlement unverified (`SPIKE-01`). | `REQ-001`, `REQ-004`, `REQ-005`, `SPIKE-01` |
| **Rollback / Backout Approach** | Partial | 45-minute operational recovery target proposed by Service Desk (`TGT-02`). | Technical backout steps, rollback trigger criteria, and committed recovery mechanics are unevidenced. | `REQ-009`, `SPIKE-02`, `CAND-06` |
| **Validation & Verification Method** | Partial | Behavioral test designs (`TC-01`–`TC-05`) and governance assurance design (`CHK-01`) defined. | Post-cutover production verification method and test execution evidence are missing. | `TC-01`–`TC-05`, `CHK-01` |
| **Operational & Support Readiness** | Missing | Service Desk recovery interest noted (`REQ-009`). | Service Desk support procedures, hypercare coverage, escalation paths, and operational handover artifacts are unevidenced. | Downstream item to establish |
| **Communications & Stakeholder Readiness** | Missing | Draft user-mapping spreadsheet exists for 603 employees (`TASK-02`). | User communications, notification schedule, and workforce transition instructions are unevidenced. | Downstream item to establish |
| **Automated Provisioning (SCIM)** | Not applicable from supplied scope | Vendor capability and tenant entitlement unverified. | None for current cutover; explicitly deferred to Phase 2. | `REQ-007`, `DEF-01` |

---

## 6. Source-evidenced blockers / dependencies

The following items are explicit upstream blockers and dependencies evidenced by the source packet:

1. **`DEP-01` / Local Change Policy Enforcement:** Production cutover is explicitly blocked until an approved change record exists (`REQ-002`, `TASK-01`, `CHK-01`).
2. **`DEP-02` / Data Mapping Gap:** 17 employee accounts cannot be included in corporate authentication cutover until identity resolution is completed (`REQ-005`, `DEC-02`).
3. **`DEP-03` / Feasibility Spike:** Technical configuration cannot be finalized until NimbusHR tenant entitlement and SAML compatibility are verified (`REQ-004`, `SPIKE-01`).
4. **`DEC-01` / Contractor Dispute:** Contractor authentication model cannot be delivered until the dispute between HR Operations and Security is settled by an authorized decision-maker (`REQ-006`).

---

## 7. Missing downstream evidence

*(Note: These items represent missing evidence categories to be established downstream; they are not invented governance gates unless mandated by explicit source policy.)*

1. **Named Change Authority:** The specific role, body, or individual possessing authority to approve the change record under local Change Policy.
2. **Detailed Implementation Plan:** Step-by-step technical deployment runbook for configuring the NimbusHR tenant and Entra enterprise application.
3. **Engineered Backout Plan:** Documented technical procedure and validation steps for authentication rollback.
4. **Post-Implementation Validation Plan:** Specific production testing procedure to verify live authentication and MFA post-cutover.
5. **Support and Operational Artifacts:** Service Desk triage documentation, incident logging paths, and escalation contacts for authentication failures.
6. **Workforce Communications Plan:** End-user notices regarding local password deprecation and the transition to corporate identity authentication.

---

## 8. Traceability summary

| Delivery / Work item | Upstream REQ / CON | Acceptance criteria | Test / Check ID | Solution review status | Change-readiness status |
|---|---|---|---|---|---|
| **US-01** | `REQ-001`, `CON-01` | `US01-AC01`, `US01-AC02`, `US01-AC03` | `TC-03`, `TC-04`, `TC-05` | Ready (Baseline logic confirmed) | Partial (Deployment mechanics pending) |
| **TASK-01** | `REQ-002`, `CON-02` | `TASK01-AC01` | `CHK-01` | Ready (Policy constraint established) | Blocked on Change Authority approval |
| **TASK-02** | `REQ-005` | `TASK02-AC01`, `TASK02-AC02` | `TC-01`, `TC-02` | Ready (603 records confirmed) | Ready (Mapped dataset available) |
| **SPIKE-01** | `REQ-004` | `COND-01` | — | Candidate (Awaiting SAML verification) | Missing technical evidence |
| **SPIKE-02** | `REQ-009` | `TGT-02` | — | Open (Awaiting backout design) | Missing rollback plan |
| **CAND-02** | `REQ-005`, `DEP-02` | `COND-02` | — | Open (17 accounts unresolved) | Partial data mapping |
| **CAND-03** | `REQ-008` | `COND-03` | — | Proposal (Saturday 22:00 unapproved) | Missing window approval |
| **CAND-04** | `REQ-006` | `COND-04` | — | Disputed (`DEC-01` open) | Scope unresolved |
| **CAND-05** | `REQ-003` | `TGT-01` | — | Target (Before 30 Nov non-binding) | Non-binding schedule target |
| **DEF-01** | `REQ-007` | — | — | Deferred (Phase 2 SCIM) | Excluded from cutover scope |

---

## 9. Recommended next review state

1. **Proceed to Solution / Technical Spike Review (`SPIKE-01`):** Focus technical analysis on verifying tenant entitlement and protocol compatibility for Entra SAML integration without assuming its outcome.
2. **Proceed to Change Enablement Initial Review:** Surface the change package for Change Enablement visibility under the assumed Normal Change path, noting that approval requires resolving the missing Change Authority, implementation runbook, backout mechanics, and cutover window.
3. **Escalate Governance / Authority Gaps:** Route the contractor access dispute (`DEC-01`), 17 unmatched employee identities (`DEC-02`), and Change Authority identification (`DEC-04`) to project governance stakeholders for assignment to appropriate decision authorities.

---

## 6 — assess-itil-alignment

- Status: `success`
- Skill SHA-256: `3adeb63ebe63773137da0e9407d6fac98de1b84737464c2a45286fd1390fef59`

# ITIL 4 Practice Alignment and Readiness Assessment: NimbusHR Corporate Identity Migration

## 1. Assessment Scope and Overall Alignment Readiness

- **Assessment scope:** Evaluation of the supplied delivery, solution, and change-readiness baseline for the NimbusHR corporate identity migration against relevant ITIL 4 practice concepts.
- **Overall alignment readiness:** **Partially evidenced / Not fully aligned**
- **Assessment summary:**
  - Positive alignment is evidenced in **Information Security Management** (formal Security Standard requiring corporate identity and existing MFA for SaaS workforce data access) and the formal recognition of **Change Enablement** governance requirements (explicit local Change Policy requiring an approved change record prior to production cutover).
  - Material evidence gaps exist across **Change Enablement** (unidentified Change Authority, unapproved cutover schedule, absent backout mechanics), **Deployment Management** (unverified tenant capability/entitlement, unevidenced deployment runbook), **Release Management** (unevidenced release communications and hypercare support arrangements), and **Service Configuration Management** (unresolved mapping for 17 employee accounts and missing configuration baseline records).
  - These gaps represent readiness dependencies and areas requiring clarification; they are not classified as proven non-compliance or invented mandatory gates beyond what explicit local policy mandates.

---

## 2. Applicable ITIL Practice Map

Only ITIL 4 practices materially implicated by the supplied delivery scenario are included:

| ITIL 4 Practice | Material Relevance to Scenario |
|---|---|
| **Change Enablement** | Relevant to risk assessment, change classification, change schedule coordination, and securing required authorisation prior to production implementation. |
| **Information Security Management** | Relevant to establishing and maintaining corporate identity authentication and MFA controls across SaaS platforms containing workforce data. |
| **Service Configuration Management** | Relevant to maintaining accurate service/identity records, CI relationships, and workforce account mapping data (620 total employee accounts). |
| **Deployment Management** | Relevant to technical execution mechanics, tenant configuration deployment, and technical recovery/backout execution. |
| **Release Management** | Relevant to making the new corporate authentication capability available to workforce users, including release scheduling, user communication, and operational handover. |

*Note: Practices such as IT Asset Management, Incident Management, and Continual Improvement are not materially evidenced in current cutover artifacts and are treated as out of current scope.*

---

## 3. Alignment Findings

| Finding ID | ITIL Practice | Evidence / Condition Evaluated | Status | Readiness Impact | Source Trace |
|---|---|---|---|---|---|
| **ALIGN-01** | Information Security Management | SaaS access for workforce data requires corporate identity and existing MFA policy; NimbusHR-local password authentication discontinued for verified users. | **Aligned / evidenced** | `No current blocker` | `REQ-001`, `CON-01`, `US-01`, `TC-03`, `TC-04`, `TC-05` |
| **ALIGN-02** | Change Enablement | Local Change Policy requires an approved change record before production implementation of customer- or workforce-impacting authentication changes. | **Aligned / evidenced** | `Readiness dependency` (Local policy gate) | `REQ-002`, `CON-02`, `TASK-01`, `CHK-01`, `DEP-01` |
| **ALIGN-03** | Change Enablement | Change classification and Change Authority role/identity: Assumed Normal Change; specific approval authority is unresolved. | **Partially evidenced** | `Decision required` | `REQ-002`, `REQ-010`, `DEC-04` |
| **ALIGN-04** | Change Enablement | Cutover schedule coordination: Saturday at 22:00 proposed by Release Manager; 30 November audit target noted by Head of HR. Neither is approved/committed. | **Partially evidenced** | `Clarification required` | `REQ-003`, `REQ-008`, `TGT-01`, `DEC-03`, `CAND-03` |
| **ALIGN-05** | Service Configuration Management | Account mapping dataset: 603 employee accounts verified 1:1 against corporate identity; 17 accounts unresolved. | **Partially evidenced** | `Readiness dependency` (Data mapping) | `REQ-005`, `TASK-02`, `TC-01`, `TC-02`, `DEP-02`, `DEC-02` |
| **ALIGN-06** | Service Configuration Management / InfoSec | Contractor access model and identity configuration: HR Operations proposes local accounts; Security proposes corporate guest accounts; decision authority unknown. | **Potential conflict** (Unresolved dispute) | `Decision required` | `REQ-006`, `DEC-01`, `CAND-04` |
| **ALIGN-07** | Deployment Management | Technical deployment mechanism: Entra SAML federation proposed; NimbusHR Enterprise plan entitlement and tenant compatibility unverified. | **Partially evidenced** (Spike candidate) | `Readiness dependency` (Technical feasibility) | `REQ-004`, `SPIKE-01`, `DEP-03` |
| **ALIGN-08** | Deployment Management | Technical backout/recovery mechanics: Service Desk proposed a 45-minute recovery target; technical rollback steps are unengineered and uncommitted. | **Not evidenced** | `Clarification required` | `REQ-009`, `SPIKE-02`, `TGT-02`, `CAND-06` |
| **ALIGN-09** | Release Management | Release packaging, workforce communications, and Service Desk operational readiness/support handover artifacts. | **Not evidenced** | `Clarification required` | Upstream Handoff Section 5 & 7 |
| **ALIGN-10** | Release Management / Service Config | Automated provisioning/deprovisioning lifecycle (SCIM). | **Not applicable / out of scope** | `Future / non-current scope` | `REQ-007`, `DEF-01` |

---

## 4. Readiness Dependencies, Decisions, and Evidence Gaps

### Sourced Readiness Dependencies (Mandated by Local Policy / Scope)
1. **`DEP-01` (Change Record Authorisation):** Local Change Policy strictly mandates an approved change record prior to production implementation (`CON-02`, `TASK-01`, `CHK-01`). Cutover cannot proceed without this authorization.
2. **`DEP-02` (Data Mapping Completion):** 17 employee accounts require resolution before those individuals can authenticate via corporate identity (`REQ-005`, `DEC-02`).
3. **`DEP-03` (SAML Entitlement Verification):** Technical deployment feasibility depends on verifying NimbusHR tenant licensing and configuration capability (`REQ-004`, `SPIKE-01`).

### Open Decisions Requiring Assignment / Governance Settlement
1. **`DEC-01` (Contractor Identity Model):** Dispute between HR Operations (local accounts) and Security (corporate guest accounts) must be settled by an authorised decision-maker (`REQ-006`).
2. **`DEC-02` (Unresolved Employee Identities):** Operational remediation owner for the 17 unmatched records must be established (`REQ-005`).
3. **`DEC-04` (Change Authority Identification):** The specific role or body acting as Change Authority under local policy must be identified to evaluate and authorize the change (`REQ-002`, `REQ-010`).

### Relevant Practice Gaps (Clarifications Required, Not Invented Mandatory Gates)
- **Deployment & Recovery Runbooks:** Documented execution steps and technical backout procedures (`SPIKE-02`) are practice-relevant for risk management, but the source does not establish a prescriptive backout template or mandated recovery threshold as a policy gate.
- **Operational Support & Communication Plans:** Service Desk triage procedures and workforce notification schedules are currently unevidenced.

---

## 5. Organisational-Policy vs. ITIL-Guidance Distinctions

To ensure governance rules are not conflated with general framework guidance, the following distinctions are explicitly maintained:

| Concern | Sourced Organisational Rule / Fact | ITIL 4 Guidance Context | Assessment Distinction |
|---|---|---|---|
| **Change Authorisation** | Local Change Policy explicitly mandates an approved change record prior to production implementation of workforce-impacting authentication changes. Change Authority is **Unknown**. | Change Enablement advocates tailored authorization mechanisms (e.g., standard, normal, emergency) to balance risk and velocity. | ITIL does **not** mandate a CAB or specific approval committee. Local policy requires approval, but the specific authority must be sourced locally. |
| **Change Classification** | Operations noted this is "probably a Normal Change unless an existing Standard Change template applies." No template is evidenced. | ITIL recognizes Standard Changes as pre-authorized, low-risk, routine changes with established procedures. | The change is treated as Normal by default due to absence of a Standard template; ITIL does not invent a pre-approved template. |
| **Backout / Rollback Plan** | Service Desk suggested a 45-minute recovery target (`TGT-02`); no backout mechanics exist (`SPIKE-02`). | ITIL Change Enablement and Deployment Management emphasize understanding risk and recovery options where appropriate. | ITIL does **not** universally mandate a 45-minute rollback window. The 45-minute figure remains an uncommitted operational desire. |
| **Architecture / Protocol** | Security Standard mandates corporate identity and existing MFA policy; does not specify SAML or Entra ID. SAML via Entra ID is a proposed mechanism (`SPIKE-01`). | ITIL practice guidance is technology- and vendor-neutral. | ITIL does not validate or mandate Entra ID or SAML; entitlement and compatibility remain technical feasibility spikes. |
| **Schedule / Target Date** | Head of HR requested completion before 30 November (audit cycle). Release Manager proposed Saturday at 22:00. | ITIL emphasizes schedule coordination to minimize business disruption and conflicts. | 30 November is a business target date, not a hard delivery deadline; Saturday 22:00 is an unapproved proposal. |

---

## 6. Focused Follow-up Questions

The following questions address critical gaps whose resolution would materially alter alignment and readiness conclusions:

1. **Change Enablement Authority:** Who is the designated Change Authority (role, individual, or governance body) responsible for reviewing and approving this authentication change under the local Change Policy?
2. **Standard vs. Normal Change Path:** Is there an established, pre-approved Standard Change model for SaaS single sign-on / authentication cutovers, or must this proceed via the full Normal Change workflow?
3. **Contractor Governance Authority:** Which role or governance body has the formal authority to resolve the contractor authentication dispute (`DEC-01`) between HR Operations and Security?
4. **Tenant Technical Feasibility:** What is the outcome of the tenant entitlement check (`SPIKE-01`) regarding whether the NimbusHR instance supports SAML 2.0 federation without tier upgrades?
5. **Operational Recovery Prerequisite:** Does local operational policy establish specific mandatory criteria or time thresholds for authentication rollback plans before a change can be scheduled?
6. **Data Remediation Ownership:** Which team or individual owns the identity resolution for the 17 unmatched employee accounts (`DEC-02`)?

---

## 7. Traceability Summary

```
[Security Standard] ──────► REQ-001 (Corporate MFA) ───► ALIGN-01 (InfoSec Practice: Aligned)
[Local Change Policy] ────► REQ-002 (Approved Record) ─► ALIGN-02 (Change Enablement: Evidenced Gate)
[Identity Team Spike] ───► REQ-004 (SAML Feasibility) ─► ALIGN-07 (Deployment: Partially Evidenced)
[HR Mapping Dataset] ────► REQ-005 (603 Matched) ──────► ALIGN-05 (Config Mgmt: Partially Evidenced)
[HR Mapping Dataset] ────► DEP-02  (17 Unmatched) ─────► DEC-02   (Config Mgmt: Data Gap)
[HR Ops vs Security] ────► REQ-006 (Contractor Scope) ─► ALIGN-06 (Config/InfoSec: Potential Conflict)
[Release Manager] ───────► REQ-008 (Sat 22:00 Window) ─► ALIGN-04 (Change Enablement: Proposal)
[Head of HR Target] ─────► REQ-003 (Target 30 Nov) ────► TGT-01   (Planning Target: Non-binding)
[Service Desk Target] ───► REQ-009 (45-min Recovery) ──► ALIGN-08 (Deployment: Proposal / Unengineered)
[Phase 2 SCIM Sug.] ─────► REQ-007 (SCIM Provisioning) ─► ALIGN-10 (Out of Scope / Deferred)
```

### Summary of Alignment Statuses
- **Aligned / evidenced:** 2 items (`ALIGN-01`, `ALIGN-02`)
- **Partially evidenced:** 4 items (`ALIGN-03`, `ALIGN-04`, `ALIGN-05`, `ALIGN-07`)
- **Not evidenced:** 2 items (`ALIGN-08`, `ALIGN-09`)
- **Potential conflict:** 1 item (`ALIGN-06`)
- **Not applicable / out of scope:** 1 item (`ALIGN-10`)
