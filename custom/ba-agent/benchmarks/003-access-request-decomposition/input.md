# Benchmark 003 — Application Access Request Delivery Decomposition

**Status:** Synthetic benchmark input. Treat this as the complete available upstream requirements analysis.

The requirements-analysis stage has already been completed. Your task in this benchmark will be to decompose the supported requirements into appropriate delivery work without inventing scope or resolving open decisions.

---

## Business objective

Reduce manual handling of employee application-access requests while preserving required approval, security and audit controls.

The current process relies heavily on email and service-desk tickets. The desired future capability is a clearer request-and-fulfillment flow that can use automation where it is feasible, while retaining a manual fulfillment path where automation is unavailable.

---

## Stakeholders / actors supported by the analysis

- **Employee / Requester** — requests application access.
- **Line Manager** — reviews standard access requests before fulfillment.
- **Access Fulfillment Team** — currently performs manual access provisioning and remains the fallback fulfillment path.
- **Security Representative** — has stated a position on privileged-access approval and security constraints.
- **Application Owner** — has stated a different position on privileged-access approval.
- **Product Owner** — proposed candidate pilot applications and a target turnaround time.

No overall decision owner for the disputed privileged-access rule is established.

---

## Requirements register

| ID | Requirement | Type | Evidence class | Requirement status | Confidence |
|---|---|---|---|---|---|
| **REQ-001** | Employees must be able to submit an application-access request containing the application and requested access role. | Functional | Explicit | Confirmed | High |
| **REQ-002** | Each request must record the requester, requested application, requested role and business justification. | Functional | Explicit | Confirmed | High |
| **REQ-003** | Standard access requests require Line Manager approval before fulfillment. | Business rule | Explicit | Confirmed | High |
| **REQ-004** | Privileged-access approval is unresolved. The Security Representative requires Security approval for all privileged roles; the Application Owner says additional Security approval should apply only to production-administration roles. | Business rule | Disputed | Disputed | High |
| **REQ-005** | Approved requests must support manual fulfillment by the Access Fulfillment Team where automated provisioning is unavailable. | Functional | Explicit | Confirmed | High |
| **REQ-006** | Automated provisioning through the existing identity platform may be used for applications that support it, but API capability and supported applications have not yet been verified. | Functional / Integration | Explicit | Candidate | Medium |
| **REQ-007** | The request record must retain the submission outcome, approval/rejection outcome, fulfillment outcome and associated date/time information as audit evidence. | Security / Audit | Explicit | Confirmed | High |
| **REQ-008** | The Product Owner would like standard access requests completed within four business hours after Line Manager approval. | Non-functional | Explicit | Target | High |
| **REQ-009** | The Product Owner suggested that the first release should probably pilot three applications: CRM, Reporting Portal and Dev Wiki. This pilot scope has not been approved. | Business / Scope | Explicit | Candidate | High |
| **REQ-010** | Automatic access removal when an employee changes role or leaves the organization is a desired future capability, not part of the current release. | Functional | Explicit | Deferred | High |
| **REQ-011** | The required retention period for access-request audit records is not established. | Security / Audit | Unknown | Unknown | High |
| **REQ-012** | Integrations must reuse approved authentication patterns, use least privilege and must not introduce a new highly privileged shared account. | Security / Compliance | Explicit | Confirmed | High |
| **REQ-013** | This initiative must not redesign the existing HR joiner/mover/leaver process. | Constraint | Explicit | Confirmed | High |

---

## Known dependencies and observations

- The Access Fulfillment Team currently performs manual provisioning for all applications.
- Existing identity-platform integration capability differs by application and has not yet been verified for the candidate pilot applications.
- The source analysis does not establish a specific vendor, API protocol, architecture pattern, UI design, notification mechanism or workflow engine.
- The source analysis does not establish story points, delivery estimates or sprint sequencing.
- The source analysis does not establish who owns the final decision on REQ-004.

---

## Analyst proposal from the upstream analysis

The analyst suggested using a staged pilot, enabling automated provisioning only for applications whose integration feasibility is proven first.

**This is a Proposed analyst mechanism, not an agreed requirement.**

---

## Readiness assessment from the upstream analysis

**Partially Ready.**

The standard request, manager approval, manual fulfillment, audit and security-control requirements are sufficiently clear to decompose.

The privileged-access flow must remain blocked pending a decision on REQ-004. Automated provisioning must remain conditional pending feasibility evidence for REQ-006. Candidate pilot scope in REQ-009 is not yet committed. Retention in REQ-011 remains unknown.
