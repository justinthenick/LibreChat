# Benchmark 009 — Gold Standard

**Evaluator-only. Do not expose this file to the model under test.**

This benchmark tests whether the composite BA Delivery Analyst generalizes from site-access work to a materially different service-data/governance problem without losing uncertainty or inventing downstream behavior.

## Expected Stage 1 — Requirements analysis

Overall readiness: **Partially Ready**.

Expected requirements/constraints, allowing equivalent IDs and wording:

- **Confirmed:** an ownership-change request records application/service identifier, current support owner, proposed support-owner team, requested effective date, and reason.
- **Confirmed:** normal ownership changes require current Application Owner approval before the ownership record is updated.
- **Disputed:** emergency/Severity 1 approval authority is unresolved. Major Incident Manager proposes emergency approval; Service Governance Lead says ownership authority should remain with current Application Owner or an explicitly established delegate. Decision owner: **Unknown**.
- **Confirmed:** manual service-register update remains available when automation is unavailable.
- **Candidate:** ownership updates may be automated through the existing Service Registry, but integration capability, authentication, supported record types and writable ownership fields are unverified.
- **Confirmed:** retain request, approval/rejection outcome, ownership-update outcome, and associated date/time evidence.
- **Confirmed conditional traceability:** where an update comes through another system, retain source reference and resulting ownership-update outcome.
- **Target:** approved changes completed within one business day where practicable; non-binding.
- **Candidate:** Finance Applications / Network Tools first-release pilot; not approved.
- **Deferred:** quarterly automated ownership recertification.
- **Unknown:** evidence retention period.
- **Confirmed security constraint:** any integration uses approved service identity, least privilege, and no new shared administrator account.
- **Confirmed process boundary:** do not redesign service-ownership governance, HR organisation model, application lifecycle process, or existing Change approval authorities.

Do not invent normal-hours/emergency timing definitions, team naming rules, effective-date validation, forms, notifications, Service Registry APIs, queues, storage designs, workflow engines, approval escalation or retention rules.

## Expected Stage 2 — Delivery decomposition

Suitable current work may include variants of:

- Ownership Change Request & Standard Approval;
- Ownership Update & Evidence;
- Automation Enablement / Discovery.

Current delivery work may include:

- request-capture story for the five sourced data elements;
- normal approval boundary story/rule;
- manual ownership-update fallback;
- evidence/traceability enabler or story;
- confirmed process/security constraints.

Required uncertainty handling:

- emergency approval dispute -> Decision Item, Decision owner Unknown, downstream emergency behavior Blocked;
- Service Registry automation -> Spike/Discovery + Candidate work, not committed build work;
- Finance Applications / Network Tools pilot remains Candidate;
- one-business-day objective remains Target;
- quarterly recertification remains Deferred;
- evidence retention period remains Unknown/open.

No estimates, API/protocol design, UI design, routing engine, storage model, governance redesign or invented actors.

## Expected Stage 3 — Acceptance criteria

Acceptance-criteria readiness: **Partially Ready**.

Ready/current criteria may cover:

### Ownership-change request

- request contains application/service identifier, current support owner, proposed support-owner team, requested effective date, and reason.

Do not invent naming formats, date rules, field validation, completeness rejection or UI.

### Normal approval boundary

- ownership record is updated only after current Application Owner approval for a normal ownership change;
- a negative `Derived boundary` may state that without that approval the normal ownership record cannot be updated.

Do not invent routing, notification, escalation, delegate rules or approval interfaces.

### Manual fallback

- manual service-register ownership update remains available when automation is unavailable.

No manual channel/UI mechanism should be invented.

### Evidence

- retain request;
- retain approval/rejection outcome;
- retain ownership-update outcome;
- retain associated date/time information.

Do not invent immutability, purge/delete behavior, storage/logging, retention duration or owner.

### Conditional imported-update traceability

If an ownership update is performed/imported through another system, retain source reference and resulting ownership-update outcome. This may be represented as a conditional constraint without committing Candidate Service Registry automation.

### Security/process constraints

If integration proceeds: approved service identity, least privilege, no new shared administrator account. The initiative must not redesign the four explicit process/governance boundaries.

No committed criteria for emergency approval behavior, Candidate Service Registry automation/pilot, Deferred recertification, or Unknown retention. The Target remains non-binding.

## Expected Stage 4 — Test / assurance derivation

Test-design readiness: **Partially Ready**.

Committed behavioural tests should trace Test ID -> AC ID -> work item -> REQ/CON ID.

Expected coverage:

- request contains the five sourced data elements;
- positive normal-approval boundary;
- negative/derived boundary without current Application Owner approval;
- evidence retention for request, approval/rejection outcome, ownership-update outcome and associated date/time;
- manual ownership-update fallback when automation is unavailable.

Conditional assurance may cover imported-update source traceability and security/process constraints, but must state what must hold rather than invent inspection mechanisms.

No committed tests for emergency approval behavior, Service Registry automated updates, proposed pilot groups, quarterly recertification or retention duration.

The one-business-day Target is not a pass/fail SLA gate.

Do not invent concrete application names, owner-team values, dates, environments, accounts, UI actions, API calls, payloads, error text, mocks/stubs or test tooling.

## Cross-stage integrity

A strong response keeps status and meaning stable from Stage 1 through Stage 4. In particular:

- emergency approval remains unresolved and Decision owner Unknown;
- Candidate Service Registry automation never becomes committed functionality;
- proposed pilot groups remain Candidate;
- one-business-day objective remains a Target;
- quarterly recertification stays Deferred;
- retention period stays Unknown and does not become a temporary no-delete rule;
- process/security constraints remain visible downstream;
- every material committed test traces to its source requirement/constraint.
