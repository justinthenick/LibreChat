# Benchmark 024 Input — Identity Access Delivery Artifact Chain

You are given a set of delivery artifacts from the same initiative. Audit the chain as supplied. Do not assume that later artifacts are more authoritative than earlier ones.

## Artifact A — Requirements analysis

### Stakeholders / source notes

- Priya, IAM engineer: corporate SSO could probably be reused, but IdP compatibility has not been checked.
- Maya, Security engineer: prefers IAM-group mapping rather than HR-attribute mapping. Operations prefers HR attributes. No decision authority for the mapping choice is identified.

### Requirement register

| ID | Statement | Evidence | Status | Source |
|---|---|---|---|---|
| REQ-01 | Administrators must use MFA when accessing the administration console. | Explicit | Confirmed | Security decision note SD-14 |
| REQ-02 | Corporate SSO may be reused for administrator authentication if IdP compatibility is confirmed. | Proposed | Candidate | Priya / IAM note |
| REQ-03 | Access provisioning should aim to complete within 5 minutes. | Explicit | Target | Project planning note |
| REQ-04 | Contractor self-service access is planned for phase 2. | Explicit | Deferred | Scope note |

### Constraint register

| ID | Constraint | Evidence | Status | Source |
|---|---|---|---|---|
| CON-01 | Manual access issuance must remain available when automated provisioning is unavailable. | Explicit | Confirmed | Operations process owner note |

### Decision item

- DEC-01 — Group-mapping approach: HR attributes vs IAM groups.
- Status: Disputed.
- Decision owner: Unknown.

## Artifact B — Delivery decomposition

| ID | Type | Description | Upstream trace | Delivery status |
|---|---|---|---|---|
| WI-01 | User Story | Administrators authenticate with MFA before console access. | REQ-01 | Ready |
| WI-02 | User Story | Administrators authenticate through corporate SSO. | REQ-02 | Ready / Confirmed |
| WI-03 | User Story | Provisioning completes within 5 minutes. | REQ-03 | Ready |
| WI-05 | Decision Item | Select group-mapping approach. | DEC-01 | Blocked pending Security decision |

No item is recorded for REQ-04 or CON-01.

## Artifact C — Acceptance criteria

- AC-01 — For WI-01 / REQ-01: administrator console access requires successful MFA.
- AC-02 — For WI-02 / REQ-02: administrator authentication must use corporate SSO.
- AC-03 — For WI-03 / REQ-03: provisioning must complete in 5 minutes or less.
- AC-04 — For WI-05 / DEC-01: Security must select the IAM-group or HR-attribute mapping approach before implementation.

## Artifact D — Test / assurance cases

- T-01 — Trace: AC-01 -> WI-01 -> REQ-01. Verify console access is unavailable until MFA succeeds.
- T-02 — Trace: AC-02 -> WI-02 -> REQ-02. Verify administrators authenticate using corporate SSO.
- T-03 — Trace: AC-99 -> WI-03 -> REQ-03. Verify provisioning finishes within 5 minutes.
- T-04 — Trace: AC-01 -> WI-01 -> REQ-01. Verify the application writes an immutable audit-log entry after every MFA attempt.

## Artifact E — Solution / Change-readiness handoff

- MFA scope is ready for implementation.
- Corporate SSO is an approved part of the solution and should be implemented.
- The five-minute provisioning SLA is a release acceptance threshold.
- Maya (Security) is the Decision Owner for the group-mapping approach.
- CAB approval is required before deployment because authentication is changing.
- Manual access fallback is not mentioned.
- Contractor self-service is not mentioned.