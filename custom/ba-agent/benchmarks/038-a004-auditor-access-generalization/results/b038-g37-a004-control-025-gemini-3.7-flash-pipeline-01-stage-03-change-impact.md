# BA Specialist Pipeline Stage

## Metadata

```json
{
  "agent_path": "custom/ba-agent/skills/assess-change-impact/SKILL.md",
  "agent_sha256": "7beae99136a52ac2e0ab484ed9fcdd8311ec0951e54b74a4dcadbc52e9412437",
  "agent_version": "0.2.0",
  "ended_at": "2026-09-06T01:41:31Z",
  "error": null,
  "finish_reason": "STOP",
  "max_output_tokens": 8192,
  "model": "gemini-3.7-flash",
  "pipeline": "Benchmark 038 \u2014 Fixed auditor-access delta control",
  "run_id": "b038-g37-a004-control-025",
  "stage_id": "change-impact",
  "stage_index": 3,
  "stage_input_sha256": "8964e56caac519410ebdfe3968f68e4083918cac32b974f1d37b7e126ba1bf78",
  "stage_name": "Assess Change Impact",
  "started_at": "2026-09-06T01:41:21Z",
  "status": "success",
  "temperature": 0.0,
  "upstream_output_sha256": "a3cd9773775f7fbfb11e4d72b4879fe670a2c4b81d8a3fe8495278a52a61d0a6",
  "usage": {
    "candidatesTokenCount": 2195,
    "promptTokenCount": 4309,
    "promptTokensDetails": [
      {
        "modality": "TEXT",
        "tokenCount": 4309
      }
    ],
    "serviceTier": "standard",
    "thoughtsTokenCount": 452,
    "totalTokenCount": 6956
  }
}
```

---

## Stage output

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
