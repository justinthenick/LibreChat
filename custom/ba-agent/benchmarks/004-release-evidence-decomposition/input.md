# Benchmark 004 — Release Evidence and Deployment Validation Decomposition

## Business objective

Standardise deployment evidence for software releases so teams can show what was checked before, during and after a deployment without redesigning the existing Change Enablement approval process.

Today evidence is spread across change records, deployment output and manually collected notes/screenshots. The desired outcome is a clearer, traceable deployment-evidence flow with automation where proven feasible and a manual path where it is not.

## Stakeholders represented in the analysis

- Release Coordinator
- Deployment Engineer
- Change Manager
- Application Owner
- Service Reliability Lead
- Product Owner

No overall decision owner has been established for the disputed failed-validation response described below.

## Requirement register

| ID | Status | Evidence | Confidence | Type | Requirement |
|---|---|---|---|---|---|
| REQ-001 | Confirmed | Explicit | High | Functional | A Release Coordinator must be able to create a deployment-evidence record containing the change ID, service/application, release version and target environment. |
| REQ-002 | Confirmed | Explicit | High | Functional / Audit | The deployment-evidence record must retain the pre-deployment validation outcome, deployment outcome, post-deployment validation outcome and associated date/time information. |
| REQ-003 | Confirmed | Explicit | High | Business rule | For a production deployment, the evidence record must reference an approved change record before the deployment is treated as ready to execute. |
| REQ-004 | Disputed | Disputed | High | Business rule | The response to a failed post-deployment validation is unresolved. The Service Reliability Lead says rollback should start automatically. The Application Owner says the deployment should pause and a human should decide whether to rollback or continue. |
| REQ-005 | Confirmed | Explicit | High | Functional | Manual evidence entry or attachment must remain available when automated evidence collection is unavailable. |
| REQ-006 | Candidate | Explicit | Medium | Functional / Integration | Deployment results may be imported automatically from the existing deployment platform, but integration capability, authentication approach and supported services have not been verified. |
| REQ-007 | Target | Explicit | High | Non-functional | The Product Owner would like the deployment evidence pack to be complete within fifteen minutes after deployment completion. |
| REQ-008 | Candidate | Explicit | High | Business / Scope | The Product Owner suggested the first release should probably pilot Billing API and Customer Portal. This pilot scope is not approved. |
| REQ-009 | Deferred | Explicit | High | Functional | Predictive deployment-risk scoring is a future capability and is not part of the current release. |
| REQ-010 | Unknown | Unknown | High | Audit | The required retention period for deployment-evidence records has not been established. |
| REQ-011 | Confirmed | Explicit | High | Security / Compliance | Any integrations must reuse approved service identities, apply least privilege and must not introduce a new shared administrator account. |
| REQ-012 | Confirmed | Explicit | High | Constraint | This initiative must not redesign the existing Change Advisory Board / change-approval process or alter existing approval authorities. |
| REQ-013 | Confirmed | Explicit | High | Audit / Traceability | Where evidence is imported from another system, the evidence record must retain the source reference and the imported outcome. |

## Known dependencies and observations

- Teams currently collect evidence differently across services.
- Manual evidence collection is currently possible for all services.
- Existing deployment-platform integration capability may differ by service and has not been verified for the candidate pilot services.
- No specific UI, storage technology, notification mechanism, rollback technology, API protocol, pipeline product or integration architecture has been established.
- No story points, estimates, sprint sequence or delivery dates have been agreed.
- No decision owner is established for REQ-004.

## Upstream analyst proposal

The analyst suggested starting with services proven technically feasible for evidence import and retaining manual evidence collection for the rest.

This is a **Proposed analyst mechanism**, not an agreed requirement or mandatory release sequence.

## Upstream readiness assessment

**Partially Ready.**

The confirmed evidence record, production change reference, manual evidence path, audit/traceability and security boundaries are sufficiently clear to decompose.

The failed-validation response is blocked by REQ-004; automated evidence import is conditional on REQ-006; the suggested pilot services in REQ-008 are uncommitted; and the retention period in REQ-010 remains unknown.
