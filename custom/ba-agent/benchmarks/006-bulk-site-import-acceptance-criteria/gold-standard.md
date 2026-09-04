# Benchmark 006 — Gold Standard

**Evaluator-only. Do not expose this file to the model under test.**

This benchmark evaluates whether `elaborate-acceptance-criteria` generalizes from service-notification work into bulk-data processing while preserving partial readiness and refusing to invent file, validation, duplicate, storage or integration behavior.

## Expected readiness

Overall: **Partially Ready**.

Acceptance criteria may be elaborated for:

- US-01 — submit a bulk site import with the four sourced row data elements;
- the confirmed portion of US-02 — every supplied row must contain site code and state before the import may proceed;
- EN-01 — retain total rows received, rows accepted, rows rejected and associated date/time;
- US-03 — manual single-site entry remains available when bulk import is unavailable;
- EN-02 — security and read-only constraints if Master Site Registry integration proceeds.

The following must remain isolated:

- DEC-01 / REQ-004 duplicate-site handling — Blocked / Disputed;
- SPK-01 and CAN-01 / REQ-005 Master Site Registry validation — Candidate / technically unverified;
- CAN-02 / REQ-007 pilot states — Candidate / unapproved;
- TGT-01 / REQ-006 processing objective — Target / non-binding;
- DEF-01 / REQ-008 recurring imports — Deferred;
- OPEN-01 / REQ-009 retention — Unknown;
- OPEN-02 / REQ-013 site-name/region validation — Unknown.

## Expected Ready / Partially Ready criteria

### US-01 / REQ-001

Expected:

- a Data Operations Analyst can submit a bulk site import;
- each supplied row contains site code, site name, state and region.

Do not invent CSV/XLSX, delimiter, encoding, headers, column order, file size, upload UI, progress behavior or batch limits beyond the non-binding Target.

### US-02 / REQ-002 + REQ-013

Expected mandatory boundary:

- a bulk import may proceed only when every supplied row contains site code and state.

A negative/derived boundary is acceptable because it is logically required by the explicit `may proceed only when` wording.

Do not invent validation rules for site name or region. Those remain Unknown under REQ-013 / OPEN-02.

### EN-01 / REQ-003

Expected:

- retain total rows received;
- retain rows accepted;
- retain rows rejected;
- retain associated date/time.

Do not invent rejection reasons, row-level storage design, immutable logs, database schema or retention duration.

### US-03 / REQ-012

Expected:

- manual single-site entry remains available when bulk import is unavailable.

Do not invent form/UI/channel or synchronization mechanics.

### EN-02 / REQ-010 + REQ-011

Expected conditional constraints if registry integration proceeds:

- use an approved service identity;
- apply least privilege;
- introduce no new shared administrator account;
- do not modify/write to the Master Site Registry; use is read-only from this initiative's perspective.

Do not imply Candidate registry integration is committed merely because its constraints are Confirmed.

## Critical disputed item — DEC-01 / REQ-004

Expected:

- no committed duplicate-handling acceptance criteria;
- both positions remain visible:
  - Data Quality Lead: reject entire import if any supplied site code already exists;
  - Product Owner: reject only duplicate row and continue remaining rows;
- Decision owner remains Unknown;
- duplicate-handling criteria remain Blocked.

Do not invent a compromise, precedence rule, threshold, partial-commit behavior or escalation authority.

## Candidate registry validation — REQ-005

Automated/master-registry validation remains Candidate/Conditional pending SPK-01. Do not invent REST/webhook/API endpoints, lookup matching rules, caching, retries, timeouts or data-write behavior.

## Candidate pilot — REQ-007

New South Wales and Victoria remain Candidate only.

## Target — REQ-006

The up-to-10,000-rows-within-ten-minutes objective remains a non-binding Target where platform capacity permits. It is not a mandatory pass/fail acceptance criterion.

## Deferred — REQ-008

No current acceptance criteria for scheduled recurring imports.

## Unknown — REQ-009 / REQ-013

Do not guess retention duration/owner/regulation or site-name/region validation rules.

## Traceability

Each mandatory criterion should reference its delivery item and upstream REQ ID(s). Strong output accounts for Ready, Partially Ready, Blocked, Candidate, Target, Deferred and Unknown items.

## Expected test-case readiness

Overall: **Partially Ready**. Confirmed submission/minimum-data/result/manual-fallback/constraint behavior may proceed to test-case elaboration. Duplicate handling, registry validation, pilot scope, retention and site-name/region validation remain unresolved or non-committed.
