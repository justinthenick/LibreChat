# Benchmark 008 — Gold Standard

**Evaluator-only. Do not expose this file to the model under test.**

This benchmark tests whether an end-to-end BA agent can carry a messy source packet through requirements analysis, decomposition, acceptance criteria and behavioural test design without losing uncertainty or inventing downstream detail.

## Expected Stage 1 — Requirements analysis

Overall readiness: **Partially Ready**.

Expected requirement register, allowing equivalent wording:

- **REQ-001 — Confirmed:** a temporary site-access request records site code, contractor company, visiting engineer name, planned arrival, planned departure, and work/Change reference.
- **REQ-002 — Confirmed:** normal-hours access requires Site Access Team approval before temporary access is issued.
- **REQ-003 — Disputed:** after-hours approval is unresolved: Site Access Lead says on-call Site Access approval; Security Manager says Security approval. Decision owner: **Unknown**.
- **REQ-004 — Confirmed:** manual temporary-access issuance remains available when automation is unavailable.
- **REQ-005 — Candidate:** temporary access may be issued automatically through the existing Building Access Platform, but site support, integration capability and authentication are unverified.
- **REQ-006 — Confirmed:** retain request submission, approval/rejection outcome, access-issuance outcome and associated date/time as evidence.
- **REQ-007 — Target:** complete requests should receive approval/rejection response within two business hours where practicable; non-binding.
- **REQ-008 — Candidate:** Sydney Metro / Newcastle first-release pilot; not approved.
- **REQ-009 — Deferred:** automatic revocation when the planned access window ends; future scope.
- **REQ-010 — Unknown:** evidence retention period.
- **REQ-011 — Confirmed constraint:** any integration uses an approved service identity, least privilege and no new shared administrator account.
- **REQ-012 — Confirmed constraint:** do not redesign contractor onboarding, security vetting, building-owner approval or existing Change approval.

Do not create additional mandatory requirements for notifications, forms, validation, access-card formats, escalation, retries, audit immutability, or integration protocols.

## Expected Stage 2 — Delivery decomposition

Suitable capabilities may include variants of:

- Site Access Request & Standard Approval;
- Access Issuance & Evidence;
- Automation Enablement.

Likely current delivery work:

- story for creating/submitting the request with the six sourced data elements — REQ-001;
- story/business-rule work for normal-hours Site Access Team approval before issuance — REQ-002;
- story for manual temporary-access issuance fallback — REQ-004;
- enabler/task for evidence retention of submission, approval/rejection, issuance outcome and date/time — REQ-006;
- integration security/process constraints as Enabler/Constraint — REQ-011 / REQ-012.

Required uncertainty handling:

- **DEC-01** or equivalent for REQ-003, preserving both positions and `Decision owner: Unknown`; after-hours implementation remains Blocked/Conditional.
- **SPK-01** or equivalent for REQ-005 to verify Building Access Platform capability, authentication and supported sites; automated issuance stays Candidate/Conditional.
- REQ-008 pilot stays Candidate.
- REQ-007 stays a Target, not SLA.
- REQ-009 stays Deferred.
- REQ-010 stays Unknown/open.

No estimates, architecture, protocol, UI, notification or workflow-engine design.

## Expected Stage 3 — Acceptance criteria

Acceptance-criteria readiness: **Partially Ready**.

Ready/current criteria may cover:

### Request creation — REQ-001

- a supported requester/actor from the decomposition can create/submit a temporary site-access request;
- the request contains site code, contractor company, visiting engineer name, planned arrival, planned departure and work/Change reference.

Do not invent field formats, mandatory-screen behavior, ordering rules, timezones, validation or UI.

### Normal-hours approval boundary — REQ-002

- normal-hours temporary access is issued only after Site Access Team approval;
- a negative `Derived boundary` is acceptable: without that approval, normal-hours temporary access cannot be issued.

Do not invent how normal-hours is calculated, approval UI, notification/error behavior, escalation or Change validation.

### Manual fallback — REQ-004

- manual temporary-access issuance remains available when automation is unavailable.

No mechanism/channel should be invented.

### Evidence — REQ-006

- retain request submission;
- retain approval/rejection outcome;
- retain temporary-access issuance outcome;
- retain associated date/time information.

Do not invent immutable logs, actor/IP/device metadata, storage or retention duration.

### Conditional integration constraints — REQ-011 / REQ-012

If integration proceeds, criteria/constraints may state:

- approved service identity;
- least privilege;
- no new shared administrator account;
- no redesign of contractor onboarding, security vetting, building-owner approval or Change approval.

Do not imply Candidate automation is committed.

No committed criteria for REQ-003, REQ-005, REQ-008, REQ-009 or REQ-010. REQ-007 remains non-binding.

## Expected Stage 4 — Test / assurance derivation

Test-design readiness: **Partially Ready**.

Committed behavioural tests should trace Test ID -> AC ID -> work item -> REQ ID.

Expected coverage:

- request creation with the six sourced data elements;
- positive normal-hours approval boundary;
- negative/derived boundary where normal-hours access lacks Site Access Team approval;
- evidence retention for submission, approval/rejection, issuance outcome and associated date/time;
- manual issuance fallback when automation is unavailable.

Conditional assurance checks may cover REQ-011 / REQ-012 only if clearly labelled conditional and must state **what** must hold, not inspection mechanics.

No committed tests for after-hours approval behavior, automated Building Access Platform issuance, pilot locations, automatic revocation or retention duration.

The two-business-hour Target may be noted as non-binding but not used as a pass/fail gate.

Do not invent concrete test values, environments, accounts, UI paths, error text, API calls, Building Access Platform behavior, badge/card formats, retries, mocks/stubs or automation tooling.

## Cross-stage integrity

A strong response keeps the same status and meaning from Stage 1 through Stage 4. In particular:

- REQ-003 never becomes a selected approval rule downstream;
- REQ-005 never becomes committed automated issuance;
- REQ-007 never becomes an SLA/test gate;
- REQ-008 never becomes committed pilot scope;
- REQ-009 never enters current backlog/criteria/tests;
- REQ-010 remains Unknown;
- decision ownership for REQ-003 remains Unknown;
- all material committed tests can be traced end-to-end to their source requirement.
