# Benchmark 006 — Bulk Site Import Acceptance Criteria

## Upstream decomposition status

**Overall acceptance-criteria readiness: Partially Ready.**

The confirmed bulk-import submission, minimum-row-data boundary, import-result evidence, manual-entry fallback and integration-security/process constraints are ready enough for acceptance-criteria elaboration.

Duplicate-site handling is blocked by an unresolved business decision. Master-registry validation remains Candidate and technically unverified. Suggested pilot states are unapproved. The processing-time objective is a Target. Import-detail retention duration is Unknown. Scheduled recurring imports are Deferred. Validation rules for site name and region remain Unknown.

## Stakeholders established upstream

- Data Operations Analyst
- Data Quality Lead
- Product Owner

No overall decision owner has been established for the disputed duplicate-site handling rule.

## Upstream requirement register

| ID | Status | Requirement |
|---|---|---|
| REQ-001 | Confirmed | A Data Operations Analyst must be able to submit a bulk site import containing site code, site name, state and region for each supplied row. |
| REQ-002 | Confirmed | A bulk site import may proceed only when every supplied row contains a site code and state. |
| REQ-003 | Confirmed | The import result must retain total rows received, rows accepted, rows rejected and associated date/time. |
| REQ-004 | Disputed | Duplicate-site handling is unresolved. The Data Quality Lead says the entire import should be rejected if any supplied site code already exists. The Product Owner says only the duplicate row should be rejected and the remaining rows should continue. |
| REQ-005 | Candidate | Site codes may be validated against the existing Master Site Registry, but integration capability, authentication approach and supported lookup behavior have not been verified. |
| REQ-006 | Target | The Product Owner would like imports of up to 10,000 rows to complete within ten minutes where platform capacity permits. |
| REQ-007 | Candidate | The Product Owner suggested the first release should probably pilot New South Wales and Victoria. This scope is not approved. |
| REQ-008 | Deferred | Scheduled recurring bulk imports are a future capability and are not part of the current release. |
| REQ-009 | Unknown | The required retention period for import-result detail has not been established. |
| REQ-010 | Confirmed | Any Master Site Registry integration must reuse an approved service identity, apply least privilege and must not introduce a new shared administrator account. |
| REQ-011 | Confirmed | This initiative must not modify or write data to the Master Site Registry. Any future integration is read-only from this initiative's perspective. |
| REQ-012 | Confirmed | Manual single-site entry must remain available when bulk import is unavailable. |
| REQ-013 | Unknown | Validation rules for site name and region values have not been established. |

## Upstream delivery decomposition

### Current / Ready items

| ID | Type | Item | Upstream requirement(s) | Delivery status |
|---|---|---|---|---|
| US-01 | User Story | As a Data Operations Analyst, I want to submit a bulk site import containing site code, site name, state and region for each supplied row. | REQ-001 | Ready |
| US-02 | User Story | As a Data Operations Analyst, I want a bulk site import to proceed only when every supplied row contains a site code and state. Validation of site name and region is not yet defined. | REQ-002, REQ-013 | Partially Ready — confirmed minimum-data rule may be elaborated; site-name/region validation remains Unknown |
| EN-01 | Enabler / Technical Task | Retain total rows received, rows accepted, rows rejected and associated date/time for the import result. | REQ-003 | Ready |
| US-03 | User Story | As a Data Operations Analyst, I want manual single-site entry to remain available when bulk import is unavailable. | REQ-012 | Ready |
| EN-02 | Enabler / Technical Task | Apply the confirmed service-identity, least-privilege, no-new-shared-admin-account and read-only-registry constraints to any Master Site Registry integration. | REQ-010, REQ-011 | Ready as constraints applying if integration work proceeds |

### Decision / blocked item

| ID | Type | Item | Upstream requirement(s) | Delivery status |
|---|---|---|---|---|
| DEC-01 | Decision Item | Decide duplicate-site handling: reject the entire import when any supplied site code already exists versus reject only the duplicate row and continue remaining rows. Decision owner: Unknown. | REQ-004 | Blocked |

No duplicate-handling implementation story has been created because the business rule is unresolved.

### Discovery / Candidate items

| ID | Type | Item | Upstream requirement(s) | Delivery status |
|---|---|---|---|---|
| SPK-01 | Spike / Discovery Item | Verify Master Site Registry integration capability, authentication approach and supported lookup behavior. | REQ-005, REQ-010, REQ-011 | Candidate / discovery |
| CAN-01 | Candidate Story | Validate supplied site codes against the Master Site Registry where technically supported. | REQ-005 | Conditional; blocked by SPK-01 and scope approval |
| CAN-02 | Candidate Scope Item | Pilot the bulk-import capability for New South Wales and Victoria. | REQ-007 | Candidate; not approved |

### Target / Deferred / Unknown

| ID | Type | Item | Upstream requirement(s) | Status |
|---|---|---|---|---|
| TGT-01 | Planning / Quality Target | Complete imports of up to 10,000 rows within ten minutes where platform capacity permits. | REQ-006 | Target / non-binding |
| DEF-01 | Deferred Item | Scheduled recurring bulk imports. | REQ-008 | Deferred |
| OPEN-01 | Open Question | Establish the required retention period for import-result detail. Decision owner: Unknown. | REQ-009 | Unknown |
| OPEN-02 | Open Question | Establish validation rules for site name and region values. Decision owner: Unknown. | REQ-013 | Unknown |

## Known boundaries

- No specific file format, delimiter, character encoding, header names, column order, maximum file size, upload page, button, progress display, validation message, rejection-message format, retry behavior, timeout, storage technology, database design, API protocol or workflow engine has been established.
- No duplicate-handling rule has been agreed beyond the two disputed positions in REQ-004.
- No validation rule has been agreed for site name or region values.
- No rule has been agreed for row ordering, whether blank optional values are allowed, or how rejection details are presented.
- No retention duration, regulation or retention owner has been established.
- No estimates, story points, sprint assignments or delivery dates are established.
- The ten-minute objective is explicitly a Target, not a binding SLA.
- Manual single-site entry is confirmed even if bulk import is unavailable.
