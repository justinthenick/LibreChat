# BA Specialist Pipeline Result

- Pipeline: `Benchmark 038 — Fixed auditor-access delta control`
- Model: `gemini-3.7-flash`
- Status: `success`
- Run ID: `b038-g37-a004-control-025`
- Total prompt tokens: `12190`
- Total candidate tokens: `7257`
- Total thought tokens: `2256`
- Total tokens: `21703`

---

## requirement-reconciliation — Reconcile Requirement Changes

### 1. Reconciliation summary

- **Added:** 1 (External auditor time-limited access capability, approved under SD-77)
- **Modified:** 0
- **Confirmed unchanged:** 0 (Explicit reaffirmation not issued, but baseline maintained)
- **Disputed:** 0
- **Superseded:** 0
- **Removed / withdrawn:** 0
- **Deferred / Blocked pending decision/evidence:** 1 (Service desk suggestion to reduce temporary access expiration to 30 days — unresolved/no baseline change)
- **Untouched / No delta:** 4 (IAM-10, IAM-11, IAM-12, IAM-13)

**Summary of material change:**
Security decision SD-77 approves adding support for external auditors who require time-limited application access within 15 minutes of an approved audit request. Contractor scope (IAM-12), MFA requirements (IAM-11), employee onboarding SLA (IAM-10), and temporary privileged access duration (IAM-13) remain in force as established in baseline version 7.

---

### 2. Delta register

| Delta ID | Baseline / New ID | Delta Class | Baseline Statement, Status & Source | New Evidence Statement, Status & Source | Authority & Evidence Basis | Downstream Impact |
|---|---|---|---|---|---|---|
| **DEL-01** | `IAM-NEW` (Auditor Access) | **Added** | *None (new requirement).* | Support external auditors with time-limited application access during approved audit activity, available within 15 minutes of an approved audit request.<br>Status: Approved.<br>Source: Security decision SD-77 (6 Sept). | Explicit decision authority via SD-77 approving the capability. Note: specific operational semantics remain incomplete. | `update required` (requires workflow, provisioning path, and audit trail design once semantic unknowns resolve). |
| **DEL-02** | `IAM-13` / `PROP-30D` | **No reliable delta** (Suggestion / No change) | Temporary privileged access expires after 90 days unless explicitly renewed.<br>Status: Confirmed.<br>Source: Security decision D-72. | Service desk lead suggested changing all temporary access expiration to 30 days. Security architect noted this requires a separate decision and to leave IAM-13 alone.<br>Status: Proposal only / Not approved.<br>Source: Operations meeting notes. | Informal stakeholder suggestion rejected/deferred by Security Architect; lacks decision authority. IAM-13 stands at 90 days. | `none` (IAM-13 remains active baseline; no downstream update). |
| **DEL-03** | `IAM-12` | **No reliable delta** (Untouched) | External contractors are out of scope for the current onboarding workflow.<br>Status: Confirmed.<br>Source: Scope decision D-71. | SD-77 does not state that contractor scope changes.<br>Status: Confirmed unchanged.<br>Source: SD-77. | Explicit retention; SD-77 scope addition applies specifically to external auditors, not contractors. | `none` |
| **DEL-04** | `IAM-11` | **No reliable delta** (Untouched) | MFA is required for all interactive application access.<br>Status: Confirmed.<br>Source: Security policy SP-14. | IAM-11 MFA was not discussed in operations notes or altered by SD-77.<br>Status: Confirmed unchanged.<br>Source: Baseline v7 / SP-14. | Baseline authority remains in effect; silence in later notes is not withdrawal or modification. | `none` |
| **DEL-05** | `IAM-10` | **No reliable delta** (Untouched) | Employees receive standard application access within one business day of an approved onboarding request.<br>Status: Confirmed.<br>Source: IAM decision D-70. | No mentions or conflicts in later notes.<br>Status: Confirmed unchanged.<br>Source: Baseline v7 / D-70. | Baseline authority remains in effect. | `none` |

---

### 3. Conflicts / unresolved decisions

| Topic | Conflicting Positions / Proposals | Confirmation & Review Dependencies | Decision Owner | Current Status |
|---|---|---|---|---|
| **Temporary access expiration period (30 days vs. 90 days)** | Service desk suggested 30-day expiration for all temporary access. Security architect required leaving IAM-13 (90 days) unchanged pending a separate decision. | None formally logged. | `Unknown` | `No baseline change` (IAM-13 remains 90 days). |
| **Audit access request approval authority** | Audit programme manager coordinates dates and provides visiting auditor lists, but evidence does not establish approval authority. | Programme Manager provides auditor list. | `Unknown` | `Blocked pending decision/evidence` |
| **Timer start trigger (15-minute SLA)** | Unclear whether 15-minute timer starts upon ticket submission, approval timestamp, or scheduled audit start window. | Operational workflow dependency. | `Unknown` | `Blocked pending decision/evidence` |
| **Auditor access duration & renewal** | SD-77 specifies "time-limited" access but defines no default/maximum duration or extension rules. | Security policy / Audit governance review. | `Unknown` | `Blocked pending decision/evidence` |
| **Identity path & credentialing model** | Unresolved whether auditors authenticate via existing directory/identity sources or a separate guest identity path. | Architecture & Identity engineering review. | `Unknown` | `Blocked pending decision/evidence` |
| **Privileged access boundary** | Unresolved whether external auditor access can ever include privileged roles subject to IAM-13. | Security / IAM governance. | `Unknown` | `Blocked pending decision/evidence` |

---

### 4. Baseline items not mentioned in new evidence

- **IAM-10 (Employee Onboarding SLA - 1 business day):** Not discussed in SD-77 or subsequent notes; remains active and untouched in baseline.
- **IAM-11 (MFA Requirement for Interactive Access):** Not discussed in operations notes; remains active and untouched in baseline. Silence does not constitute removal or exemption for auditors.

---

### 5. Downstream selective-update handoff

- **Artifacts requiring update/evaluation:**
  - IAM Onboarding & Provisioning Architecture (to incorporate SD-77 external auditor workflow).
  - IAM Change-Impact Assessment (to cover the new external auditor actor, request path, SLA, and support burden).
- **Artifacts remaining untouched:**
  - Employee standard onboarding workflow (IAM-10).
  - Contractor onboarding scope exclusions (IAM-12).
  - Privileged access expiration baseline rules (IAM-13).

---

### 6. Structured requirements analysis (Approved auditor access requirement)

- **Approved outcome:** Provide external auditors with time-limited application access during approved audit activity within 15 minutes of an approved audit request (Source: SD-77).
- **Actor:** External Auditor (distinct from internal employees covered by IAM-10 and external contractors excluded by IAM-12).
- **Identified ambiguities / missing parameters (without decomposition):**
  - *Trigger condition:* Event marking the beginning of the 15-minute SLA window is unspecified.
  - *Duration boundary:* No default or maximum time limit defined.
  - *Approval authority:* Role/entity authorized to approve audit access requests is unspecified.
  - *Identity/Access path:* Identity source (standard corporate directory vs. federated/guest identity path) is unspecified.
  - *Renewal/Extension logic:* Rules governing access extensions or re-authorizations are missing.
  - *Privilege scope:* Permission ceiling (standard read-only vs. temporary privileged access under IAM-13) is unspecified.

---

### 7. Change-impact assessment (Auditor actor & capability)

- **Actor & Scope Addition:** Introduces an external auditor persona into operational scope while maintaining the out-of-scope status of external contractors (IAM-12).
- **SLA & Operational Burden:** Accelerates provisioning turnaround from standard 1 business day (IAM-10) to 15 minutes for approved audit requests, impacting operational response paths and automated provisioning infrastructure.
- **Security & Compliance Controls:** Interactive access remains bound by MFA policy (IAM-11). Time-bounding mechanisms must be integrated into lifecycle management without modifying IAM-13 90-day privileged access thresholds.

---

## SUPPORTED_DELTA_HANDOFF
- **Added Requirement:** External Auditor Access Capability (SD-77)
  - *Statement:* External auditors receive time-limited application access during approved audit activity, available within 15 minutes of an approved audit request.
  - *Status:* Approved (SD-77).
- **Preserved Baseline Requirements:**
  - `IAM-10`: Standard employee access SLA (1 business day) — Unchanged.
  - `IAM-11`: MFA required for all interactive application access — Unchanged.
  - `IAM-12`: External contractors out of scope — Unchanged.
  - `IAM-13`: Temporary privileged access expires after 90 days — Unchanged.

## SEMANTIC_UNKNOWNS_HANDOFF
- **Timer Start Trigger:** Event defining the start of the 15-minute SLA window (`Unknown`).
- **Access Duration & Limits:** Default and maximum allowable access duration for external auditors (`Unknown`).
- **Approval Authority:** Authorized role/entity required to approve audit access requests (`Decision owner: Unknown`).
- **Identity Path:** Mechanism/source for auditor provisioning (existing directory vs. guest identity store) (`Unknown`).
- **Renewal / Extension Rules:** Policy and procedure for extending auditor access beyond the initial approved period (`Unknown`).
- **Privileged Role Eligibility:** Applicability of privileged roles to external auditors and intersection with IAM-13 (`Unknown`).

PIPELINE_HANDOFF_COMPLETE: REQUIREMENT_RECONCILIATION

---

## requirements-analysis — Analyze Requirements

# Requirements Analysis Report: External Auditor Access Delta

## 1. Executive summary

Security Decision SD-77 approves adding an access capability for external auditors who require time-limited application access during approved audit activity, available within 15 minutes of an approved audit request. Baseline requirements IAM-10 (standard employee onboarding SLA of 1 business day), IAM-11 (MFA required for all interactive access), IAM-12 (external contractors excluded from onboarding workflow), and IAM-13 (temporary privileged access expires after 90 days) remain in effect and unchanged.

While SD-77 establishes the high-level requirement and performance SLA, critical operational semantics remain unresolved: the 15-minute timer start event, default and maximum allowable access durations, request approval authority, identity provisioning path, renewal/extension rules, and privileged-role boundaries are not established in the evidence and are tracked as `Unknown`.

---

## 2. Source register

| Source ID | Source Name / Reference | Description / Context |
|---|---|---|
| **S1** | Security Decision SD-77 (6 Sept) | Explicit decision approving time-limited application access for external auditors within 15 minutes of an approved request. |
| **S2** | Baseline v7 / Decision D-70 | Baseline decision establishing standard employee application access SLA within one business day of approved onboarding request (IAM-10). |
| **S3** | Baseline v7 / Security Policy SP-14 | Baseline security policy requiring MFA for all interactive application access (IAM-11). |
| **S4** | Baseline v7 / Scope Decision D-71 | Baseline decision confirming external contractors are out of scope for onboarding workflow (IAM-12). |
| **S5** | Baseline v7 / Security Decision D-72 | Baseline decision establishing temporary privileged access expiration after 90 days unless renewed (IAM-13). |
| **S6** | Operations Meeting Notes | Meeting notes recording Service Desk Lead suggestion to reduce temporary access expiration to 30 days, and Security Architect response to defer pending separate decision. |

---

## 3. Business objective and scope

### Business Objective
Enable external auditors to receive time-limited application access during approved audit activity within 15 minutes of an approved audit request, without compromising baseline access controls or baseline identity security policies.

### Stated Delivery Boundaries & Scope
- **In Scope:** Provisioning time-limited application access for external auditors during approved audit activities within 15 minutes of an approved request.
- **Out of Scope:** External contractors (explicitly excluded via IAM-12 / D-71). Standard employee onboarding workflows (governed separately under IAM-10 / D-70).
- **Unchanged Baseline Controls:** Multi-factor authentication (IAM-11) and 90-day temporary privileged access expiration (IAM-13).

---

## 4. Stakeholders / actors

| Stakeholder / Actor | Category | Evidenced Activity / Responsibility | Established Decision Authority |
|---|---|---|---|
| **External Auditor** | Persona / Actor | Requires time-limited application access during approved audit activity. | None established. |
| **Employee** | Persona / Actor | Receives standard application access within 1 business day of approved request. | None established. |
| **External Contractor** | Persona / Actor | Excluded from current onboarding workflow. | None established. |
| **Audit Programme Manager** | Role | Coordinates audit dates and provides visiting auditor lists. | **Unknown** (Evidence does not establish request approval authority). |
| **Service Desk Lead** | Role | Suggested reducing temporary access expiration period to 30 days. | **Unknown** (Does not own policy decisions). |
| **Security Architect** | Role | Noted that changing temporary access expiration requires a separate decision; directed leaving IAM-13 unchanged. | **Unknown** (Authority to decide audit request approval or policy change not established). |

---

## 5. Requirements register

| ID | Requirement | Type | Evidence class | Requirement status | Source | Evidence / rationale | Confidence |
|---|---|---|---|---|---|---|---|
| **IAM-NEW** | External auditors must receive time-limited application access during approved audit activity, available within 15 minutes of an approved audit request. | Functional requirement | Explicit | Confirmed | S1 (SD-77) | SD-77 explicitly approves time-limited access within 15 minutes for approved audit activity. | High |
| **IAM-10** | Employees must receive standard application access within one business day of an approved onboarding request. | Business requirement | Explicit | Confirmed | S2 (D-70) | Established in baseline v7; untouched by SD-77. | High |
| **IAM-11** | MFA is required for all interactive application access. | Security/compliance requirement | Explicit | Confirmed | S3 (SP-14) | Baseline security policy; untouched by SD-77 or operational notes. | High |
| **IAM-12** | External contractors are out of scope for the current onboarding workflow. | Constraint | Explicit | Confirmed | S4 (D-71) | Baseline scope boundary; explicitly maintained as separate from external auditor scope. | High |
| **IAM-13** | Temporary privileged access expires after 90 days unless explicitly renewed. | Security/compliance rule | Explicit | Confirmed | S5 (D-72) | Baseline rule confirmed active; proposed 30-day change rejected/deferred. | High |
| **PROP-30D** | Temporary access expiration could be reduced from 90 days to 30 days. | Business rule | Explicit | Candidate | S6 (Meeting notes) | Suggested by Service Desk Lead; explicit statement that this requires a separate decision and is not approved. | High |

---

## 6. Contradictions and ambiguities

### 6.1 Temporary access expiration duration (30 days vs. 90 days)
- **Positions / Uncertainty:** Service Desk Lead proposed shortening temporary access expiration to 30 days across all temporary access. Security Architect noted this requires a separate decision and kept IAM-13 at 90 days.
- **Required outcome:** Establish whether temporary access expiration rules remain at 90 days (IAM-13) or are modified via formal governance.
- **Decision owner:** `Unknown`

### 6.2 Audit access request approval authority
- **Positions / Uncertainty:** SD-77 requires an "approved audit request," and the Audit Programme Manager coordinates schedules and auditor lists, but the evidence does not state who holds approval authority to authorize access requests.
- **Required outcome:** Establish the authorized role or governance entity required to approve external auditor access requests.
- **Decision owner:** `Unknown`

### 6.3 15-minute SLA start trigger event
- **Positions / Uncertainty:** SD-77 specifies availability "within 15 minutes of an approved audit request," but does not define whether the timer starts at ticket submission, approval grant timestamp, or the scheduled audit window start time.
- **Required outcome:** Establish the precise operational lifecycle event that starts the 15-minute fulfillment SLA.
- **Decision owner:** `Unknown`

### 6.4 Auditor access duration limits & renewal rules
- **Positions / Uncertainty:** SD-77 specifies access is "time-limited" but specifies no default lifespan, maximum duration, or renewal/extension conditions.
- **Required outcome:** Establish default access duration, maximum permissible duration, and re-authorization/extension policies for external auditors.
- **Decision owner:** `Unknown`

### 6.5 Identity path and credentialing model
- **Positions / Uncertainty:** The source does not specify whether external auditors are provisioned via the standard enterprise identity directory, a guest identity path, or a federated external identity store.
- **Required outcome:** Establish the identity source and provisioning path for external auditor accounts.
- **Decision owner:** `Unknown`

### 6.6 Privileged role boundaries for external auditors
- **Positions / Uncertainty:** It is unestablished whether external auditor access is strictly standard/read-only application access or if it may include privileged roles governed by IAM-13.
- **Required outcome:** Establish the maximum privilege boundary and applicable role catalog for external auditors.
- **Decision owner:** `Unknown`

---

## 7. Assumptions

- **ASM-01:** Interactive access for external auditors remains subject to baseline MFA requirements (IAM-11) as no policy exemption was stated in SD-77.
- **ASM-02:** Auditor access is strictly intended for the duration of the approved audit activity and is not permanent.

---

## 8. Analyst proposals

- **PROP-AN-01:** Conduct a targeted requirements clarification session with the IAM product owner, audit governance, and security stakeholders to formalize the approval matrix, duration limits, and SLA trigger events.
- **PROP-AN-02:** When defining operational workflows, evaluate whether automated pre-scheduling of audit accounts (prior to the audit start window) satisfies the 15-minute availability requirement without requiring purely real-time manual approvals.

---

## 9. Open questions — prioritized

1. **Governance & Approval:** Who is the authoritative decision owner with the mandate to approve external auditor access requests?
2. **SLA Trigger:** What specific system or workflow event initiates the 15-minute provisioning SLA (e.g., formal approval timestamp vs. scheduled audit start datetime)?
3. **Lifespan Boundaries:** What are the mandatory default and maximum allowable access durations for external auditor sessions?
4. **Lifecycle & Extensions:** What process and authorization are required if an audit engagement exceeds its initial approved duration?
5. **Entitlements & Privileges:** Are external auditors eligible for privileged application roles, and if so, how does this interact with baseline rule IAM-13?
6. **Identity Architecture:** What identity source / account store (e.g., federated guest identity vs. internal directory) is mandated for external auditor credentialing?

---

## 10. Not established / out of scope

### Not Established in Supplied Evidence
- Specific approval authority role or committee for audit access requests.
- Identity store / directory integration mechanism for external auditor provisioning.
- Precise duration caps (hours, days, weeks) for external auditor accounts.
- Extension / renewal workflow for expiring auditor access.
- Scope of accessible roles / permissions (standard vs. privileged).
- Specific ticketing tool, workflow engine, or technical provisioning system.

### Out of Scope
- External contractors (IAM-12 confirms external contractors remain excluded from onboarding workflows).
- Changes to standard employee onboarding timelines (IAM-10 remains 1 business day).
- Changes to baseline temporary privileged access expiration (IAM-13 remains 90 days; PROP-30D is unapproved).

---

## 11. Readiness for decomposition

**Status:** **Not ready**

**Rationale:** While the high-level business requirement for external auditor access is approved under SD-77, the critical operational parameters—including request approval authority, SLA start trigger event, access lifespan/duration limits, renewal rules, identity provisioning mechanism, and privilege boundaries—remain completely unknown. Decomposing this requirement into user stories, acceptance criteria, or technical design prior to resolving these semantic unknowns would require unverified assumptions and risk building non-compliant access pathways.

---

## ANALYZED_DELTA_FOR_IMPACT

### 1. Scope & Actor Delta Assessment
- **Added Actor/Capability:** External Auditor capability approved under SD-77. Confirmed scope requires providing time-limited application access during approved audit activity within 15 minutes of an approved request.
- **Preserved Baseline Invariants:**
  - `IAM-10`: Standard employee onboarding SLA remains 1 business day.
  - `IAM-11`: MFA requirement remains mandatory for all interactive access.
  - `IAM-12`: External contractors remain strictly out of scope.
  - `IAM-13`: Temporary privileged access expiration remains 90 days (the 30-day proposal PROP-30D is unapproved and does not modify the baseline).

### 2. Operational & Architecture Impact
- **Fulfillment Velocity:** Moving from a 1-business-day turnaround (IAM-10) to a 15-minute SLA (SD-77) for approved auditor requests requires a rapid provisioning mechanism.
- **Workflow & Lifecycle Integration:** Requires integrating time-limited deprovisioning/expiration controls specifically for auditors without altering existing 90-day privileged rules (IAM-13).

### 3. Preserved Semantic Unknowns (Pre-Decomposition Boundaries)
- **Approval Authority:** `Unknown` (Audit Programme Manager coordinates schedules, but request approval authority is unestablished).
- **15-Minute SLA Trigger Event:** `Unknown` (Ticket submission vs. approval timestamp vs. audit window start).
- **Default & Maximum Access Duration:** `Unknown` ("Time-limited" stated, but exact bounds are undefined).
- **Renewal / Extension Rules:** `Unknown` (Re-approval and extension conditions undefined).
- **Identity Source / Provisioning Path:** `Unknown` (Guest identity vs. internal directory unassigned).
- **Privileged Role Eligibility:** `Unknown` (Applicability of privileged roles and intersection with IAM-13 unestablished).

PIPELINE_HANDOFF_COMPLETE: REQUIREMENTS_ANALYSIS

---

## change-impact — Assess Change Impact

# Change Impact Assessment: External Auditor Access Capability

---

## 1. Change objective / boundary

### What is changing
- **Addition of External Auditor Access Capability (SD-77 / IAM-NEW):** Implementation of time-limited application access for external auditors during approved audit activities, with a fulfillment performance requirement of availability within 15 minutes of an approved audit request.

### What is explicitly excluded / deferred
- **External Contractors:** Explicitly excluded from onboarding workflows (Baseline v7 / Scope Decision D-71 / IAM-12).
- **Standard Employee Onboarding SLA:** Standard employee onboarding SLA remains unchanged at 1 business day (Baseline v7 / Decision D-70 / IAM-10).
- **Interactive Access MFA Policy:** Baseline policy requiring MFA for all interactive application access remains unchanged (Baseline v7 / Security Policy SP-14 / IAM-11).
- **Baseline Privileged Access Expiration Duration:** Baseline 90-day expiration rule for temporary privileged access (Baseline v7 / Security Decision D-72 / IAM-13) remains in effect. The proposal to reduce temporary access expiration to 30 days (PROP-30D) is unapproved and deferred pending separate governance.

---

## 2. Impact register

| Impact ID | Domain | Impacted Item / Group | Impact Class | Evidence / Source Reference | Nature of Impact | Confidence | Downstream Planning Implication |
|---|---|---|---|---|---|---|---|
| **IMP-01** | Users / Customer Groups | External Auditors | Confirmed direct impact | SD-77; IAM-NEW | New user persona receiving time-limited application access for approved audit activity within 15 minutes of approval. | High | Plan onboarding/offboarding lifecycle and credential delivery specifically for external auditor persona. |
| **IMP-02** | Access / Identity / Permissions | Identity Lifecycle & Time-Limited Access Controls | Confirmed direct impact | SD-77; IAM-NEW | Mechanism required to provision and enforce time-limited access boundaries for auditor accounts. | High | Solution must support rapid provisioning and automated or time-bounded access termination without violating baseline controls. |
| **IMP-03** | Access / Identity / Permissions | Multi-Factor Authentication (MFA) | Confirmed indirect impact | SP-14 (IAM-11); SD-77 | External auditor interactive access is subject to mandatory baseline MFA controls. | High | Access delivery path must accommodate external auditor MFA registration/enrollment within fulfillment constraints. |
| **IMP-04** | Business Processes / Operating Procedures | Request & Approval Process | Confirmed direct impact | SD-77 ("approved audit request") | An operational workflow is required to handle audit access requests, record approval, and initiate fulfillment. | High | Define approval flow; decision authority remains unestablished (`Unknown`). |
| **IMP-05** | Business Processes / Operating Procedures | Audit Coordination Process | Confirmed indirect impact | Meeting Notes (Audit Programme Manager); SD-77 | Audit engagement scheduling and visiting auditor list coordination intersect with access request fulfillment. | High | Align audit schedule preparation with access request intake workflows. |
| **IMP-06** | Support / Service Desk / Operations | Fulfillment & Support Operations | Candidate impact | SD-77 (15-min SLA); Meeting Notes (Service Desk Lead) | Rapid fulfillment target (15 minutes) may alter Service Desk operational handling or require automated execution. | Medium | Evaluate whether Service Desk manual handling can meet the 15-minute SLA or if automated provisioning is required. |
| **IMP-07** | Access / Identity / Permissions | Entitlement Handling & Privilege Boundaries | Unknown | SD-77; D-72 (IAM-13) | Specific application roles/entitlements assigned to auditors (read-only vs. privileged) are unevidenced. | Low | Clarify whether auditor roles intersect with baseline 90-day privileged access controls (IAM-13). |
| **IMP-08** | Infrastructure / Platform | Identity Store / Directory Path | Unknown | SD-77 | Directory source (enterprise directory, federated identity, or guest account store) is unevidenced. | Low | Identify architectural identity path for external auditor credentialing. |
| **IMP-09** | Policy / Governance Dependencies | Request Approval Authority | Unknown | SD-77; Meeting Notes | Authority holding formal sign-off right for auditor access requests is not established. | Low | Resolve authorized governance role for audit request approvals. |
| **IMP-10** | Users / Customer Groups | External Contractors | Not impacted / excluded | D-71 (IAM-12) | External contractors remain explicitly out of scope for onboarding workflows. | High | Maintain strict boundary isolating contractor access handling from auditor access changes. |
| **IMP-11** | Business Processes / Operating Procedures | Standard Employee Onboarding | Not impacted / excluded | D-70 (IAM-10) | Standard employee onboarding SLA remains unchanged at 1 business day. | High | Maintain operational separation between employee onboarding and 15-minute auditor provisioning. |
| **IMP-12** | Policy / Governance Dependencies | 90-Day Temporary Privileged Expiration | Not impacted / excluded | D-72 (IAM-13); Meeting Notes | Baseline 90-day privileged access expiration is preserved; 30-day proposal is unapproved. | High | Preserve 90-day expiration rules in baseline access policies. |

---

## 3. Dependency chain

```
[Approved Audit Request] (Trigger - Approval Authority: Unknown)
       │
       ▼
[Request & Approval Workflow] (Confirmed Direct)
       │
       ├───────────────────────────────────────────────┐
       ▼                                               ▼
[15-Minute Fulfillment Mechanism] (Confirmed Direct)  [Audit Programme Manager Schedule] (Confirmed Indirect)
       │
       ├───────────────────────────────────────────────┐
       ▼                                               ▼
[Identity Provisioning & Time-Limited Entitlements]  [MFA Enforcement: IAM-11] (Confirmed Indirect)
(Store / Path: Unknown)
       │
       ▼
[Auditor Interactive Application Access] (Confirmed Direct)
       │
       ▼
[Access Expiration / Termination Control] (Confirmed Direct; Duration Limits: Unknown)
```

*Unverified Links / Dependencies:*
- Request Approval Authority $\rightarrow$ Request Workflow (`Unknown`)
- Fulfillment SLA Timer Start Event $\rightarrow$ 15-Minute Fulfillment (`Unknown`)
- Entitlement Role Catalog $\rightarrow$ Privileged Expiration IAM-13 (`Candidate / Unknown`)

---

## 4. Impact risks

- **Fulfillment SLA Breach Risk:** If manual operational processing (e.g., Service Desk queue handling) is utilized without automation, fulfilling access within the 15-minute requirement from approval may fail.
- **Access Over-Retention Risk:** Because default access lifespans, maximum durations, and termination triggers are unevidenced (`Unknown`), auditor access risks remaining active beyond the approved audit window if automated deprovisioning is not defined.
- **MFA Enrollment Latency Risk:** If external auditor MFA onboarding is not streamlined, baseline MFA compliance (IAM-11) may conflict with or delay the 15-minute access availability SLA.

---

## 5. Unknown / candidate impacts to verify

1. **Request Approval Authority:** Which specific role or committee possesses authority to approve external auditor access requests?
2. **SLA Start Trigger:** What exact workflow event initiates the 15-minute fulfillment timer (ticket creation timestamp, approval timestamp, or scheduled audit start window)?
3. **Identity Store & Provisioning Mechanism:** What directory or identity provider path (internal directory, federated B2B/guest, separate external store) will host external auditor accounts?
4. **Access Duration Limits:** What are the mandatory default and maximum allowable access durations for auditor accounts before automatic expiration?
5. **Entitlement Scope & Privilege Classification:** Are external auditors restricted to standard/read-only application access, or can they receive privileged entitlements governed by IAM-13?
6. **Renewal / Extension Mechanism:** What process governs access extensions if an audit extends beyond its original scheduled duration?
7. **Operational Support Routing:** Does the 15-minute fulfillment obligation sit with the Service Desk, IAM Operations, or an automated workflow?

---

## 6. Explicit non-impacts / exclusions

- **External Contractors:** Confirmed unaffected and excluded (IAM-12 / D-71).
- **Standard Employee Onboarding Workflow & SLA:** Confirmed unaffected; 1-business-day turnaround remains active (IAM-10 / D-70).
- **Baseline Interactive MFA Enforcement:** Confirmed unaffected; mandatory MFA policy applies to all interactive sessions (IAM-11 / SP-14).
- **General Temporary Privileged Access Expiration Duration:** Confirmed unaffected; 90-day baseline rule remains active (IAM-13 / D-72). The 30-day proposal (PROP-30D) is explicitly unapproved.

---

## 7. Change-readiness handoff

### Confirmed Impacts for Readiness Planning
- New external auditor actor requiring time-limited interactive application access.
- 15-minute fulfillment performance SLA upon request approval.
- Application of mandatory baseline MFA controls to all auditor accounts.
- Maintenance of distinct onboarding boundaries for employees (1 business day) and contractors (excluded).

### Candidate / Unknown Impacts Requiring Resolution
- Request approval governance authority and workflow intake mechanism.
- 15-minute SLA timer trigger definition.
- Identity architecture, directory store, and provisioning automation path.
- Specific entitlement catalog (standard vs. privileged) and time-limit lifespan/renewal parameters.
- Operational fulfillment assignment (Service Desk vs. automated orchestration).

### Planning Invariants & Targets
- The 15-minute availability window is a binding performance requirement under SD-77, but its trigger event and fulfillment architecture remain unassigned.
- The 30-day expiration proposal (PROP-30D) remains an unapproved suggestion; downstream planning must not treat 30-day expiration as an approved requirement.

---

PIPELINE_HANDOFF_COMPLETE: CHANGE_IMPACT
