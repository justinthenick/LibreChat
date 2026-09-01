# Benchmark 007 — Release Verification Test Cases

## Upstream test-design status

**Overall test-design readiness: Partially Ready.**

The confirmed release-verification record, approved-Change boundary, verification evidence, manual-evidence fallback and conditional integration constraints are ready enough for behavioural test-case derivation.

Failed post-deployment handling is blocked by a disputed business decision. Automated result import remains Candidate and technically unverified. Suggested pilot services are unapproved. The completion-time objective is a Target. Evidence retention is Unknown. Predictive risk scoring is Deferred.

## Stakeholders established upstream

- Release Coordinator
- Service Reliability Lead
- Application Owner
- Product Owner

No overall decision owner has been established for the disputed failed-validation response.

## Upstream requirement register

| ID | Status | Requirement |
|---|---|---|
| REQ-001 | Confirmed | A Release Coordinator must be able to create a release-verification record containing service/application, release version, target environment and Change ID. |
| REQ-002 | Confirmed | A release-verification record may be marked ready for execution only when it references an approved Change ID for that release. |
| REQ-003 | Confirmed | The release-verification record must retain pre-deployment verification outcome, post-deployment verification outcome and associated date/time information. |
| REQ-004 | Disputed | Failed post-deployment handling is unresolved. The Service Reliability Lead says rollback should begin automatically. The Application Owner says execution should pause and a human should decide whether to rollback or continue. |
| REQ-005 | Candidate | Deployment results may be imported automatically from the existing deployment platform, but integration capability, authentication approach and supported services have not been verified. |
| REQ-006 | Target | The Product Owner would like the release-verification record to be complete within fifteen minutes after deployment completion where practicable. |
| REQ-007 | Candidate | The Product Owner suggested the first release should probably cover Billing API and Customer Portal. This scope is not approved. |
| REQ-008 | Deferred | Predictive deployment-risk scoring is a future capability and is not part of the current release. |
| REQ-009 | Unknown | The required retention period for release-verification evidence has not been established. |
| REQ-010 | Confirmed | Any deployment-platform integration must reuse an approved service identity, apply least privilege and must not introduce a new shared administrator account. |
| REQ-011 | Confirmed | This initiative must not redesign the existing Change approval process or alter existing approval authorities. |
| REQ-012 | Confirmed | Manual evidence attachment must remain available when automated deployment-result import is unavailable. |
| REQ-013 | Confirmed | Where deployment evidence is imported from another system, the verification record must retain the source reference and imported outcome. |

## Upstream acceptance criteria

### Ready behavioural criteria

| AC ID | Delivery item | Acceptance condition | Evidence basis | Upstream REQ(s) | Status |
|---|---|---|---|---|---|
| US-01-AC01 | US-01 | A Release Coordinator can create a release-verification record containing service/application, release version, target environment and Change ID. | Explicit | REQ-001 | Ready |
| US-02-AC01 | US-02 | A release-verification record references an approved Change ID before it is marked ready for execution. | Explicit | REQ-002, REQ-011 | Ready |
| US-02-AC02 | US-02 | A release-verification record cannot be marked ready for execution unless it references an approved Change ID. | Derived boundary | REQ-002 | Ready |
| EN-01-AC01 | EN-01 | The verification record retains the pre-deployment verification outcome. | Explicit | REQ-003 | Ready |
| EN-01-AC02 | EN-01 | The verification record retains the post-deployment verification outcome. | Explicit | REQ-003 | Ready |
| EN-01-AC03 | EN-01 | The verification record retains associated date/time information for those outcomes. | Explicit | REQ-003 | Ready |
| US-03-AC01 | US-03 | Manual evidence attachment remains available when automated deployment-result import is unavailable. | Explicit | REQ-012 | Ready |

### Ready constraints that apply if Candidate integration proceeds

| AC ID | Delivery item | Acceptance condition | Evidence basis | Upstream REQ(s) | Status |
|---|---|---|---|---|---|
| EN-02-AC01 | EN-02 | Any deployment-platform integration uses an approved service identity. | Explicit | REQ-010 | Ready as conditional constraint |
| EN-02-AC02 | EN-02 | Any deployment-platform integration applies least privilege. | Explicit | REQ-010 | Ready as conditional constraint |
| EN-02-AC03 | EN-02 | Any deployment-platform integration does not introduce a new shared administrator account. | Derived boundary | REQ-010 | Ready as conditional constraint |
| EN-03-AC01 | EN-03 | Where evidence is imported, the verification record retains the source reference. | Explicit | REQ-013 | Ready as conditional constraint |
| EN-03-AC02 | EN-03 | Where evidence is imported, the verification record retains the imported outcome. | Explicit | REQ-013 | Ready as conditional constraint |

## Non-ready items

| Item ID | Type | Upstream REQ(s) | Status | Reason |
|---|---|---|---|---|
| DEC-01 | Decision Item | REQ-004 | Blocked / Disputed | Failed-validation response unresolved; Decision owner Unknown. |
| SPK-01 | Spike / Discovery | REQ-005, REQ-010 | Candidate / discovery | Deployment-platform integration capability/authentication/service support unverified. |
| CAN-01 | Candidate Story | REQ-005 | Candidate / Conditional | Automated deployment-result import not approved and blocked by SPK-01. |
| CAN-02 | Candidate Scope Item | REQ-007 | Candidate | Billing API / Customer Portal pilot not approved. |
| TGT-01 | Planning / Quality Target | REQ-006 | Target / non-binding | Fifteen-minute objective is not a release gate or SLA. |
| DEF-01 | Deferred Item | REQ-008 | Deferred | Predictive risk scoring is future scope. |
| OPEN-01 | Open Question | REQ-009 | Unknown | Retention duration and owner not established. |

## Known boundaries

- No screen, button, field layout, click path, validation message, error text, test environment, test account, exact test data value, Change-ID format, date/time format, timezone, API protocol, endpoint, payload, storage design, database, queue, workflow engine, deployment product, retry behaviour, timeout or test-automation framework has been established.
- No failed-validation rule has been agreed beyond the two disputed positions.
- No specific mechanism for checking whether a Change ID is approved has been established.
- No retention duration, regulation or retention owner has been established.
- No estimates, sprint assignments, test-execution dates or automation plans are established.
- The fifteen-minute objective is explicitly a non-binding Target.
