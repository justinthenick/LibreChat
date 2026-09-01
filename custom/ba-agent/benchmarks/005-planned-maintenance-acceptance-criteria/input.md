# Benchmark 005 — Planned Maintenance Notification Acceptance Criteria

## Upstream decomposition status

**Overall acceptance-criteria readiness: Partially Ready.**

The confirmed notice-creation, approved-change reference, publication evidence, manual publication fallback and security/process constraints are ready enough for acceptance-criteria elaboration.

Cancellation handling is blocked by an unresolved business decision. Automated subscriber notification remains Candidate and technically unverified. The suggested pilot services are unapproved. The publication-timing objective is a Target. Retention duration is Unknown. Automatic post-maintenance closure is Deferred.

## Stakeholders established upstream

- Service Desk Analyst
- Change Manager
- Operations Lead
- Product Owner

No overall decision owner has been established for the disputed cancellation-handling rule.

## Upstream requirement register

| ID | Status | Requirement |
|---|---|---|
| REQ-001 | Confirmed | A Service Desk Analyst must be able to create a planned-maintenance notice containing the affected service, maintenance-window start, maintenance-window end and impact summary. |
| REQ-002 | Confirmed | A planned-maintenance notice may be published only when it references an approved Change ID for that maintenance activity. |
| REQ-003 | Confirmed | The notice record must retain the publication outcome and associated date/time. |
| REQ-004 | Disputed | Cancellation handling is unresolved. The Operations Lead says a notice should be withdrawn automatically when the associated change is cancelled. The Change Manager says withdrawal should require human confirmation. |
| REQ-005 | Candidate | Subscriber notifications may be sent through the existing notification platform, but supported channels, integration capability and authentication approach have not been verified. |
| REQ-006 | Target | The Product Owner would like planned-maintenance notices to be published at least 24 hours before the maintenance window where practicable. |
| REQ-007 | Candidate | The Product Owner suggested the first release should probably cover Mobile App and Billing Portal. This scope is not approved. |
| REQ-008 | Deferred | Automatic post-maintenance closure of notices is a future capability and not part of the current release. |
| REQ-009 | Unknown | The required retention period for planned-maintenance notice records has not been established. |
| REQ-010 | Confirmed | Any notification integration must reuse an approved service identity, apply least privilege and must not introduce a new shared administrator account. |
| REQ-011 | Confirmed | This initiative must not redesign the existing Change approval process or alter existing approval authorities. |
| REQ-012 | Confirmed | Manual publication of a planned-maintenance notice must remain available when notification-platform integration is unavailable. |

## Upstream delivery decomposition

### Current / Ready items

| ID | Type | Item | Upstream requirement(s) | Delivery status |
|---|---|---|---|---|
| US-01 | User Story | As a Service Desk Analyst, I want to create a planned-maintenance notice containing the affected service, maintenance-window start, maintenance-window end and impact summary. | REQ-001 | Ready |
| US-02 | User Story | As a Service Desk Analyst, I want a planned-maintenance notice to reference an approved Change ID before it is published. | REQ-002, REQ-011 | Ready |
| EN-01 | Enabler / Technical Task | Retain the publication outcome and associated date/time on the notice record. | REQ-003 | Ready |
| US-03 | User Story | As a Service Desk Analyst, I want manual publication to remain available when notification-platform integration is unavailable. | REQ-012 | Ready |
| EN-02 | Enabler / Technical Task | Apply the confirmed service-identity, least-privilege and no-new-shared-admin-account constraints to any notification integration. | REQ-010 | Ready as a constraint applying if integration work proceeds |

### Decision / blocked item

| ID | Type | Item | Upstream requirement(s) | Delivery status |
|---|---|---|---|---|
| DEC-01 | Decision Item | Decide cancellation handling: automatic withdrawal when the associated change is cancelled versus human confirmation before withdrawal. Decision owner: Unknown. | REQ-004 | Blocked |

No cancellation-handling implementation story has been created because the business rule is unresolved.

### Discovery / Candidate items

| ID | Type | Item | Upstream requirement(s) | Delivery status |
|---|---|---|---|---|
| SPK-01 | Spike / Discovery Item | Verify notification-platform supported channels, integration capability, authentication approach and service coverage. | REQ-005, REQ-010 | Candidate / discovery |
| CAN-01 | Candidate Story | Send subscriber notifications through the existing notification platform where technically supported. | REQ-005 | Conditional; blocked by SPK-01 and scope approval |
| CAN-02 | Candidate Scope Item | Pilot the capability for Mobile App and Billing Portal. | REQ-007 | Candidate; not approved |

### Target / Deferred / Unknown

| ID | Type | Item | Upstream requirement(s) | Status |
|---|---|---|---|---|
| TGT-01 | Planning / Quality Target | Publish planned-maintenance notices at least 24 hours before the maintenance window where practicable. | REQ-006 | Target / non-binding |
| DEF-01 | Deferred Item | Automatic post-maintenance closure of notices. | REQ-008 | Deferred |
| OPEN-01 | Open Question | Establish the required retention period for planned-maintenance notice records. Decision owner: Unknown. | REQ-009 | Unknown |

## Known boundaries

- No specific screen, page, button, field layout, notification channel, message template, confirmation dialogue, validation/error message, retry behavior, timeout, API protocol, storage technology or workflow engine has been established.
- No rule has been agreed that maintenance-window end must be after start, that Change IDs require a particular format, or that duplicate notices are prohibited.
- No retention duration, regulation or retention owner has been established.
- No estimates, story points, sprint assignments or delivery dates are established.
- The 24-hour objective is explicitly a Target, not a binding SLA.
- The manual-publication fallback is confirmed even if automated subscriber notification is not delivered.
