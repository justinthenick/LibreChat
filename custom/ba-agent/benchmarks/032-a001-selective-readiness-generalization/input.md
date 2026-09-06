# FreshFields Distribution — warehouse scanner certificate rotation

## User request

The BA work is already complete enough for this decision point. **Do not redo the requirements analysis, decomposition, acceptance criteria or test-case design.**

I need two things from the supplied baseline:

1. a solution/change-readiness handoff for the proposed production certificate rotation; and
2. an ITIL 4 practice-alignment assessment suitable for the go/no-go pack.

Keep unresolved items unresolved. We need to know whether the evidence is ready, not make it look ready.

---

## Context

FreshFields Distribution operates three temperature-controlled warehouses. Warehouse staff use 186 managed Android handheld scanners to record pallet receipt, picking and dispatch events against the StockFlow service.

The current device client certificate used for mutual TLS authentication expires on **18 October 2026**.

### Confirmed organisational constraints

- **SEC-12 Device Authentication Standard** requires managed warehouse handhelds accessing StockFlow to authenticate using a device-bound certificate. Shared credentials are prohibited.
- **CHG-04 Production Change Policy** requires an approved change record before a production authentication change is implemented.
- The organisation has not supplied evidence naming the approving **Change Authority** for this change.
- There is no supplied evidence that a CAB meeting is universally mandatory for this class of change.

---

# Existing normalized BA baseline

The following requirements package is the current working baseline. Its structure, acceptance criteria and tests have already been reviewed by the BA and application teams for this decision point.

## Requirements

### R-01 — Preserve certificate-based device authentication
**Status:** Confirmed  
**Evidence:** SEC-12 Device Authentication Standard; current StockFlow interface design.

All managed warehouse handhelds must continue to use device-bound certificate authentication when connecting to StockFlow after the rotation.

### R-02 — Complete rotation before certificate expiry
**Status:** Target  
**Target date:** 10 October 2026  
**Evidence:** Operations planning note.

The programme aims to complete production rotation by 10 October to retain contingency before the 18 October certificate expiry. The 10 October date is a target, not a committed implementation approval.

### R-03 — Use the existing MDM certificate payload capability
**Status:** Confirmed capability; rollout design partly Candidate  
**Evidence:** Endpoint engineering confirmation dated 1 September.

The existing MDM platform can deploy the replacement client certificate and trust payload to enrolled scanners. The proposal is to deploy in staged groups, but the final number and composition of rollout groups has not been approved.

### R-04 — Maintain scanning service during rollout
**Status:** Confirmed outcome; recovery detail incomplete  
**Evidence:** Warehouse operations requirement.

Pallet receipt, picking and dispatch scanning must remain available during the rollout except for device-local interruption required to apply the certificate payload.

A previous certificate can be re-pushed through MDM while it remains valid. The exact rollback execution time for the full fleet has not been measured.

### R-05 — Observe authentication failures during rollout
**Status:** Confirmed monitoring capability; threshold Candidate  
**Evidence:** StockFlow support runbook.

The existing gateway dashboard shows certificate-authentication failures by device. A proposed alert threshold of **more than 5 failed devices in 10 minutes** has not been approved as the production threshold.

### R-06 — Production window
**Status:** Candidate  
**Evidence:** Endpoint engineering proposal.

A **Sunday 02:00–04:00** production window has been proposed. There is no supplied evidence that the window is approved.

### R-07 — Change governance
**Status:** Confirmed local-policy gate / authority Unknown  
**Evidence:** CHG-04 Production Change Policy.

An approved change record is required before implementation. The Change Authority for this change is Unknown from the supplied evidence.

---

## Delivery decomposition already agreed for this decision point

- D-01: issue replacement production client certificate and validate expiry/chain.
- D-02: prepare MDM payload for replacement certificate and trust chain.
- D-03: validate authentication on representative pilot devices.
- D-04: define production rollout grouping and sequence.
- D-05: define rollback decision criteria and measured rollback timing.
- D-06: prepare monitoring and support coverage for the rollout window.
- D-07: obtain the production change record approval required by CHG-04.

D-04, D-05 and D-07 are not complete.

---

## Acceptance criteria already baselined

### AC-01
Given a managed pilot scanner with the replacement certificate, when it connects to StockFlow, then mutual TLS authentication succeeds without shared credentials.

### AC-02
Given an authenticated scanner after certificate replacement, when a warehouse operator performs receipt, pick and dispatch scan transactions, then StockFlow accepts the transactions and returns the normal success response.

### AC-03
Given a scanner with the replacement certificate, when network connectivity is interrupted and restored, then the scanner can re-establish authenticated StockFlow connectivity.

### AC-04
Given the production rollout is in progress, when certificate-authentication failures occur, then support staff can identify affected device IDs using the existing gateway dashboard.

### AC-05
Given rollback is required while the previous certificate remains valid, when the previous certificate payload is re-pushed to a device, then that device can re-establish authenticated StockFlow connectivity using the previous certificate.

No acceptance criterion asserts that the proposed production window, alert threshold, rollout group design or Change Authority is approved.

---

## Test evidence already executed

### T-01 — Replacement certificate authentication
- Sample: 20 managed scanners across the three warehouses.
- Result: **PASS**.
- Evidence: all 20 authenticated to StockFlow using the replacement device certificate.

### T-02 — Core scanning transactions
- Sample: same 20 pilot scanners.
- Result: **PASS**.
- Evidence: receipt, pick and dispatch transactions completed successfully.

### T-03 — Reconnect after network interruption
- Sample: 20 pilot scanners.
- Result: **PASS**.
- Evidence: all devices reconnected and authenticated after Wi-Fi interruption.

### T-04 — Authentication-failure visibility
- Sample: 3 deliberately invalid pilot certificates.
- Result: **PASS**.
- Evidence: the gateway dashboard displayed the three affected device IDs.

### T-05 — Per-device rollback
- Sample: 5 pilot scanners.
- Result: **PASS**.
- Evidence: previous certificate payload re-pushed and StockFlow connectivity restored.
- Limitation: this does **not** establish fleet-wide rollback duration.

### T-06 — Full-fleet rollout and rollback timing
- Result: **NOT RUN**.
- Reason: final rollout grouping is not yet approved and a production-like full-fleet timing exercise has not been scheduled.

---

## Current traceability summary

- R-01 -> AC-01 -> T-01 PASS
- R-02 -> planning target only; no approval evidence
- R-03 -> AC-01/AC-02 -> T-01/T-02 PASS; rollout grouping remains Candidate
- R-04 -> AC-02/AC-03/AC-05 -> T-02/T-03/T-05 PASS; fleet rollback timing remains Unknown
- R-05 -> AC-04 -> T-04 PASS; alert threshold remains Candidate
- R-06 -> proposed production window only; approval Unknown
- R-07 -> CHG-04 requires approved change record; Change Authority Unknown; approval not evidenced

---

## Current planning notes

- Endpoint engineering prefers three rollout groups, one per warehouse, but this remains a proposal.
- Warehouse Operations has said the Sunday 02:00–04:00 window “looks workable”; this is not recorded as formal approval.
- The StockFlow support lead will be available that weekend if the date proceeds. This does not establish that they are the Change Authority.
- No evidence has been supplied for a mandatory CAB meeting.

Produce only the requested readiness and ITIL-alignment outputs through the minimum appropriate route.
