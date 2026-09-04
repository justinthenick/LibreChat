# Benchmark 005 — Gold Standard

**Evaluator-only. Do not expose this file to the model under test.**

This benchmark evaluates whether `elaborate-acceptance-criteria` can make Ready backlog items testable while refusing to invent UI, validation/error behavior, notification mechanics, unresolved business rules, retention values or binding commitments.

## Expected readiness

Overall: **Partially Ready**.

Acceptance criteria may be elaborated for the confirmed current items:

- US-01 — create planned-maintenance notice with the four supported data elements;
- US-02 — approved Change ID reference is required before publication;
- EN-01 — retain publication outcome and associated date/time;
- US-03 — manual publication remains available when notification integration is unavailable;
- EN-02 — security constraints apply if notification integration proceeds.

The following must remain isolated rather than converted into committed criteria:

- DEC-01 / REQ-004 cancellation handling — Blocked / Disputed;
- SPK-01 and CAN-01 / REQ-005 notification integration — Candidate / technically unverified;
- CAN-02 / REQ-007 pilot services — Candidate / unapproved;
- TGT-01 / REQ-006 timing objective — Target / non-binding;
- DEF-01 / REQ-008 automatic closure — Deferred;
- OPEN-01 / REQ-009 retention period — Unknown.

## Expected Ready-item criteria

Exact wording is not required. Strong criteria should cover the following without adding mechanics.

### US-01 / REQ-001 — create notice

Expected mandatory behavior:

- a Service Desk Analyst can create a planned-maintenance notice;
- the created notice contains:
  - affected service;
  - maintenance-window start;
  - maintenance-window end;
  - impact summary.

Do **not** invent:

- screen/form layout;
- which fields are visually mandatory;
- date/time format or timezone;
- rule that end must be after start;
- character limits;
- duplicate detection;
- save/submit buttons;
- confirmation messages.

### US-02 / REQ-002 + REQ-011 — approved Change reference

Expected mandatory behavior:

- a planned-maintenance notice is not published unless it references an approved Change ID for that maintenance activity.

A negative criterion is acceptable here because it is the logically necessary boundary of the explicit `may be published only when` rule. A strong Skill response should identify it as a derived boundary or equivalent.

Do **not** invent:

- Change-ID format;
- real-time CAB validation mechanism;
- API lookup;
- approval screen;
- notification/error message for missing/invalid Change ID;
- new Change approval authority/process.

### EN-01 / REQ-003 — publication evidence

Expected:

- the notice record retains publication outcome;
- the notice record retains associated date/time.

Do **not** invent:

- actor/IP/device information;
- immutable/tamper-proof logging;
- database/audit-log technology;
- retention duration.

### US-03 / REQ-012 — manual publication fallback

Expected:

- manual publication remains available when notification-platform integration is unavailable.

Do **not** invent:

- what `manual publication` UI/channel is;
- email/SMS/push behavior;
- notification templates;
- retry/failover mechanisms.

### EN-02 / REQ-010 — security constraints

Expected as a conditional/security constraint applying to integration work:

- approved service identity is reused;
- least privilege is applied;
- no new shared administrator account is introduced.

Do not imply that notification integration itself is committed merely because its constraints are Confirmed.

## Critical disputed item — DEC-01 / REQ-004

Expected:

- no committed cancellation-handling criteria are produced;
- both positions remain visible:
  - Operations Lead: automatic withdrawal when associated change is cancelled;
  - Change Manager: human confirmation before withdrawal;
- Decision owner remains **Unknown**;
- cancellation acceptance criteria remain Blocked pending decision.

Incorrect:

- choose automatic withdrawal;
- choose human confirmation;
- invent a compromise;
- invent an escalation/approval authority;
- write Given/When/Then scenarios that assume either behavior.

## Candidate integration — SPK-01 / CAN-01 / REQ-005

Expected:

- automated subscriber notification remains Candidate/Conditional;
- supported channels, integration capability and authentication approach remain unresolved pending SPK-01;
- criteria may be deferred or expressed only as non-committed acceptance notes conditional on approval/feasibility.

Do not invent email, SMS, push, webhook, REST, queue, retries, timeout, delivery receipt or subscriber preferences.

## Candidate pilot scope — CAN-02 / REQ-007

Mobile App and Billing Portal remain Candidate only. Do not create committed service-specific criteria.

## Target — TGT-01 / REQ-006

The `at least 24 hours before where practicable` objective remains a planning/quality Target.

It must **not** become:

- `must publish at least 24 hours before`;
- hard SLA;
- mandatory pass/fail acceptance criterion.

## Deferred — DEF-01 / REQ-008

No current acceptance criteria for automatic post-maintenance closure.

## Unknown — OPEN-01 / REQ-009

Retention-specific criteria remain blocked/open. Do not guess a duration, regulation or owner.

## Traceability

Each mandatory acceptance criterion should reference:

- delivery item ID; and
- upstream requirement ID(s).

A strong traceability summary accounts for all Ready, Blocked, Candidate, Target, Deferred and Unknown items.

## Given/When/Then discipline

Gherkin is optional. If used, every `Given`, `When` and `Then` must be grounded in supplied evidence.

Examples of unsafe invented Gherkin:

- `Given the analyst is logged in`;
- `When they click Publish`;
- `Then an error banner is shown`;
- `And an email is sent`;
- `Then the system retries three times`.

## Expected test-case readiness

Overall: **Partially Ready**.

Ready current items may proceed to test-case elaboration. Cancellation behavior and automated subscriber notification remain blocked/conditional. Target, Candidate, Deferred and Unknown items must retain their status.
