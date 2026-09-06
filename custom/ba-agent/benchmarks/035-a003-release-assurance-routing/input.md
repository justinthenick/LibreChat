# Coastal Water — FieldOps Mobile 4.8 release assurance

## User request

The change-impact work is already complete enough for this release decision. **Do not redo the impact assessment.**

I need the supplied release packet checked for:

1. artifact traceability and coverage gaps;
2. what the release evidence actually proves;
3. operational readiness; and
4. a consolidated solution/change-readiness handoff for the go/no-go discussion.

Do **not** add an ITIL assessment to this task. Keep failed, missing, Candidate and Unknown evidence in those states.

---

## Current change scope

FieldOps Mobile 4.8 updates the Android field application used by 420 maintenance technicians and introduces a matching API change in the FieldOps Sync service.

The current impact register was reviewed on 3 September 2026 and is supplied as complete for this decision point.

### Impact register — supplied as current

- Managed Android field devices — affected.
- FieldOps API Gateway route set — affected.
- FieldOps Sync service — affected.
- Offline job cache schema — affected.
- Service Desk knowledge article — update required.
- Existing web dispatch console — no functional change identified from supplied design review.
- No additional consuming systems were identified in the current dependency register.

The user is not asking for this impact register to be re-derived.

---

## Requirements and release traceability baseline

### R-01 — Preserve offline work capture
**Status:** Confirmed

Field technicians must be able to create and update work notes while offline and synchronize them after connectivity returns.

Traceability supplied: R-01 -> AC-01 -> T-01.

### R-02 — Prevent duplicate job-note creation during retry
**Status:** Confirmed

A reconnect/retry must not create duplicate work-note records.

Traceability supplied: R-02 -> AC-02 -> T-02.

### R-03 — Enforce minimum supported Android version
**Status:** Confirmed

FieldOps Mobile 4.8 supports managed devices on Android 13 or later.

Traceability supplied: R-03 -> AC-03 -> T-03.

### R-04 — Support rollback to 4.7 during the agreed recovery period
**Status:** Confirmed outcome; full rollback rehearsal evidence missing

Traceability supplied: R-04 -> AC-04 -> T-04.

### R-05 — Detect synchronization failure after release
**Status:** Confirmed monitoring outcome; alert threshold Candidate

The monitoring platform exposes failed sync counts. A proposed alert threshold of more than 20 failed syncs in 5 minutes is **Candidate**, not approved.

Traceability supplied: R-05 -> AC-05 -> T-05.

---

## Acceptance criteria / test evidence

### T-01 — Offline create/update and later synchronization
- Environment: release-candidate test environment.
- Result: **PASS**.
- Evidence: 40-device pilot across two maintenance depots; offline notes synchronized after connectivity restoration.

### T-02 — Retry duplicate prevention
- Result: **PASS**.
- Evidence: 250 forced reconnect/retry cases; no duplicate note IDs recorded.

### T-03 — Android-version enforcement
- Result: **PASS**.
- Evidence: managed Android 13/14 devices admitted; Android 12 test device blocked as expected.

### T-04 — Full rollback rehearsal to 4.7
- Result: **NOT RUN**.
- Reason: production-like device rollback exercise was deferred pending final release window confirmation.

A rollback procedure exists in draft form, but no supplied evidence demonstrates fleet rollback duration or successful production-like execution.

### T-05 — Sync-failure monitoring visibility
- Result: **PASS** for visibility.
- Evidence: injected sync failures appeared in the monitoring dashboard.
- Limitation: the proposed alert threshold remains Candidate and has not been approved or tested as the production threshold.

### T-06 — Production deployment
- Result: **NOT RUN**.
- This is a pre-production release decision packet.

---

## Release / operational evidence

### Build and deployment evidence

- Release build identifier: `fieldops-mobile-4.8.0+312` — Confirmed.
- API deployment package identifier: `fieldops-sync-2026.09.03.2` — Confirmed.
- Test-environment deployment of both packages — **PASS**.
- Production deployment — **NOT RUN**.

### Defects

- DEF-11 — medium severity UI alignment defect — closed with retest PASS.
- DEF-17 — **high severity**, intermittent loss of queued photo attachment after app process termination while offline — **OPEN**.
- Product owner has stated that DEF-17 is “unlikely in normal use”; this is not evidence of closure, acceptance authority or technical mitigation.

### Monitoring

- Existing dashboard shows sync success/failure counts — Confirmed.
- Proposed threshold >20 failed syncs / 5 minutes — **Candidate**.
- No supplied evidence of an approved production threshold.

### Support and runbook

- Service Desk weekend coverage for the proposed release weekend — Confirmed.
- Field application support engineer on-call — Confirmed.
- Release runbook — draft supplied.
- Rollback section exists, but fleet rollback timing remains **Unknown** because T-04 was not run.

### Change governance

- Change record CHG-9481 exists in **Draft** state.
- Local policy requires an **approved change record before production implementation**.
- No supplied evidence identifies the approving Change Authority for CHG-9481.
- Proposed production window: Saturday 22:00–23:30 — **Candidate**, not approved.
- No evidence is supplied for a universally mandatory CAB meeting.

---

## Authority and evidence boundaries

- A draft change record is not approval.
- A Product Owner comment is not defect closure or risk acceptance unless authority/evidence explicitly supports that conclusion.
- `NOT RUN` is not PASS.
- A draft rollback procedure is not evidence that rollback succeeds or meets any timing expectation.
- A monitoring dashboard is not an approved alert threshold.
- Pilot/test-environment success is not production deployment evidence.
- Support availability does not make a named person the Change Authority.

Produce only the requested assurance route. The correct route may legitimately lead to a not-ready or conditional outcome.
