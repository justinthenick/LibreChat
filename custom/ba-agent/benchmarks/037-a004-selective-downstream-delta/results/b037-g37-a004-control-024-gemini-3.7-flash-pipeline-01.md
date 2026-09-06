# BA Specialist Pipeline Result

- Pipeline: `Benchmark 037 — Fixed selective requirement-delta control`
- Model: `gemini-3.7-flash`
- Status: `success`
- Run ID: `b037-g37-a004-control-024`
- Total prompt tokens: `10116`
- Total candidate tokens: `5386`
- Total thought tokens: `2853`
- Total tokens: `18355`

---

## requirement-reconciliation — Reconcile Requirement Changes

### 1. Reconciliation summary

| Delta Class | Count | Description of Material Change |
|---|---|---|
| **Added** | 1 | Addition of `invoice_status` row-level export field copied from source ERP (`OPEN`, `PAID`, `VOID`, or null if unavailable) via Product Decision PD-51. |
| **Modified** | 1 | REQ-22 status resolved from `Candidate` to `Confirmed`, establishing the existing managed SFTP gateway as the approved transport via Architecture Decision AD-12. |
| **Removed / withdrawn** | 1 | REQ-24 (weekly manual pilot report) explicitly withdrawn from target release scope upon automated export go-live via Sponsor Decision D-52. |
| **Confirmed unchanged** | 1 | REQ-23 (failure email alert to Operations) remains unchanged; silence in later notes is not removal. |
| **Disputed / Unresolved proposal** | 2 | Operations proposal to shift export time from 18:00 to 19:00 (REQ-20) left open pending Finance confirmation; Analyst suggestion to reduce retention from 30 days to 7 days (REQ-21) lacks governance approval. Baseline values (18:00 Sydney, 30 days) remain in effect. |

---

### 2. Delta register

| Delta ID | Baseline ID / New ID | Delta Class | Baseline Statement, Status & Source | New Evidence Statement, Status & Source | Authority & Evidence Basis | Downstream Impact |
|---|---|---|---|---|---|---|
| **DEL-01** | REQ-20 | Disputed / Unresolved proposal | Daily invoice-exception export runs at 18:00 Australia/Sydney. (Status: Confirmed, Source: Decision D-41) | Operations lead suggested 19:00; Product Owner stated to leave open until Finance confirms overnight consumption timing. (Source: Product meeting notes, 6 Sept) | Unresolved proposal. Confirmation dependency noted (Finance overnight consumption timing), but Finance decision authority is not documented. `Decision owner: Unknown`. Baseline remains 18:00 Australia/Sydney. | `blocked pending decision/evidence` (no baseline change) |
| **DEL-02** | REQ-21 | Disputed / Unresolved proposal | Export files are retained for 30 days. (Status: Confirmed, Source: Data decision D-42) | Analyst suggested cutting retention to seven days. (Source: Product meeting notes, 6 Sept) | Unresolved proposal. No data-governance decision or approval provided. `Decision owner: Unknown`. Baseline remains 30-day retention. | `blocked pending decision/evidence` (no baseline change) |
| **DEL-03** | REQ-22 | Modified | Managed SFTP is the proposed transport, pending architecture decision. (Status: Candidate, Source: Solution note S-20) | Use the existing managed SFTP gateway for the daily export. Resolves REQ-22. (Status: Accepted, Source: Architecture decision AD-12, 6 Sept) | Explicit decision authority (Architecture Decision AD-12). REQ-22 is resolved and confirmed. | `update required` (AC-22-1, TC-22-1) |
| **DEL-04** | REQ-23 | Confirmed unchanged | Operations receives an email when the daily export job fails. (Status: Confirmed, Source: Operations decision D-43) | Not mentioned in 6 September evidence packet. | Silence does not constitute change or withdrawal. Baseline remains Confirmed. | `none` |
| **DEL-05** | REQ-24 | Removed / withdrawn | During pilot, Operations produces a weekly manual exception report. (Status: Confirmed, Source: Pilot decision D-44) | Weekly manual pilot report is withdrawn when the automated daily export goes live; explicitly removes REQ-24 from target release scope. (Source: Sponsor decision D-52, 6 Sept) | Explicit decision authority (Sponsor decision D-52). Requirement withdrawn from release scope. | `update required` (Retire/Withdraw AC-24-1, TC-24-1) |
| **DEL-06** | REQ-25 (New) | Added | N/A (Field not in version 4 baseline). | Add `invoice_status` to each exported row, copied from source ERP status (`OPEN`, `PAID`, `VOID`). If unavailable, value must be null. (Status: Approved, Source: Product decision PD-51, 6 Sept) | Explicit decision authority (Product decision PD-51). New export field added to scope. | `update required` (Create AC-25-1, TC-25-1) |

---

### 3. Conflicts / unresolved decisions

1. **Export Schedule Proposal (REQ-20)**
   - *Baseline position:* 18:00 Australia/Sydney (Confirmed via D-41).
   - *Proposed position:* 19:00 Australia/Sydney (Operations lead suggestion).
   - *Confirmation dependency:* Finance overnight consumption timing confirmation.
   - *Decision owner:* `Unknown` (Finance decision authority is not established).
   - *Status:* Baseline unchanged (18:00 Australia/Sydney); proposal blocked pending confirmation and authorized decision.

2. **Retention Period Proposal (REQ-21)**
   - *Baseline position:* 30 days retention (Confirmed via D-42).
   - *Proposed position:* 7 days retention (Analyst suggestion).
   - *Missing evidence:* No data-governance decision or approval record provided.
   - *Decision owner:* `Unknown`.
   - *Status:* Baseline unchanged (30 days retention); proposal blocked pending authorized decision.

---

### 4. Baseline items not mentioned in new evidence

- **REQ-23 (Operations failure alert email):** Not mentioned in the 6 September evidence packet. In accordance with the core principle that silence is not withdrawal, REQ-23 remains active, Confirmed, and unchanged.

---

### 5. Downstream selective-update handoff

The following downstream artifacts are targeted for selective updates based solely on supported material deltas:

1. **REQ-22 (via AD-12):** Update AC-22-1 and TC-22-1 to bind transport explicitly to the existing managed SFTP gateway.
2. **REQ-24 (via D-52):** Mark AC-24-1 and TC-24-1 as withdrawn/removed from target release scope upon automated export go-live.
3. **REQ-25 / PD-51:** Author new acceptance criteria (AC-25-1) and test cases (TC-25-1) for `invoice_status` row payload formatting and null handling.

---

## Downstream Artifact Updates (Supported Affected Scope Only)

### Acceptance Criteria Updates

- **AC-22-1 (Updated):** The daily invoice-exception export is delivered using the existing managed SFTP gateway.
- **AC-24-1 (Withdrawn):** *Withdrawn from target release scope per Sponsor Decision D-52 upon automated export go-live.*
- **AC-25-1 (New — supporting PD-51):**
  1. Each exported row contains the field `invoice_status` populated with the exact status string from the source ERP.
  2. Supported source ERP status values reflected in the export for this release are `OPEN`, `PAID`, and `VOID`.
  3. If the source ERP status is unavailable for a given row, the exported `invoice_status` field is set to null (no defaulting or inferred value).

### Test Case Updates

- **TC-22-1 (Updated):**
  - *Objective:* Verify export delivery via the existing managed SFTP gateway.
  - *Preconditions:* Automated daily export job configured with the existing managed SFTP gateway endpoint.
  - *Steps:*
    1. Execute the daily invoice-exception export job.
    2. Verify file transmission through the existing managed SFTP gateway.
    3. Retrieve the delivered export file from the vendor intake interface.
  - *Expected Result:* Export file is successfully transmitted through the existing managed SFTP gateway and is fully accessible to the vendor.
- **TC-24-1 (Withdrawn):** *Withdrawn from active release test suite per Sponsor Decision D-52.*
- **TC-25-1 (New — supporting PD-51):**
  - *Objective:* Verify row-level `invoice_status` mapping and null handling in the export payload.
  - *Preconditions:* Test dataset prepared in source ERP containing records with status `OPEN`, `PAID`, `VOID`, and a record with an unavailable status.
  - *Steps:*
    1. Execute the daily export process across the prepared test dataset.
    2. Inspect each row of the generated export payload.
  - *Expected Result:*
    - Rows with source ERP status `OPEN`, `PAID`, and `VOID` show exact string matches in the `invoice_status` column.
    - Rows with unavailable source ERP status have `invoice_status` populated as null.

---

## SUPPORTED_DELTA_HANDOFF
- **AD-12 / REQ-22 (Existing managed SFTP gateway):** Affected downstream artifacts -> `AC-22-1`, `TC-22-1`.
- **PD-51 / REQ-25 (`invoice_status` payload field):** Affected downstream artifacts -> `AC-25-1` (new), `TC-25-1` (new).
- **D-52 / REQ-24 (Withdrawal of weekly manual pilot report):** Affected downstream artifacts -> `AC-24-1` (withdrawn), `TC-24-1` (withdrawn).

## BLOCKED_OR_UNCHANGED_HANDOFF
- **REQ-20 (Export schedule 18:00 Australia/Sydney):** Unchanged baseline. 19:00 proposal is unresolved (`blocked pending decision/evidence`); confirmation dependency on Finance overnight consumption timing; `Decision owner: Unknown`. Downstream artifacts (`AC/TC`) unchanged.
- **REQ-21 (30-day retention):** Unchanged baseline. 7-day retention proposal is unresolved (`blocked pending decision/evidence`); data-governance approval missing; `Decision owner: Unknown`. Downstream artifacts (`AC/TC`) unchanged.
- **REQ-23 (Operations failure alert email):** Unchanged baseline. Not mentioned in later evidence packet; remains Confirmed. Downstream artifacts (`AC/TC`) unchanged.

PIPELINE_HANDOFF_COMPLETE: REQUIREMENT_RECONCILIATION

---

## acceptance-criteria — Elaborate Acceptance Criteria

# Acceptance-Criteria Elaboration (Selective Requirement Delta)

## 1. Acceptance-criteria readiness
**Readiness:** **Partially Ready**
- **Ready for elaboration:** Supported material deltas (REQ-22 / AD-12, REQ-25 / PD-51, REQ-24 / D-52).
- **Preserved unchanged:** Baseline items (REQ-20, REQ-21, REQ-23).
- **Blocked / Non-operative:** Unresolved proposals for REQ-20 (19:00 schedule) and REQ-21 (7-day retention) remain blocked pending authorized governance decisions.

---

## 2. Item/readiness map

| Item ID | Delta Class | Delivery Status | Upstream ID(s) | Criteria Action |
|---|---|---|---|---|
| **REQ-22** | Modified | Ready | AD-12, REQ-22 | Update criterion (transport confirmed as existing managed SFTP gateway) |
| **REQ-25** | Added | Ready | PD-51, REQ-25 | Author new criteria (`invoice_status` mapping and null handling) |
| **REQ-24** | Removed / withdrawn | De-scoped / Withdrawn | D-52, REQ-24 | Mark criteria as Withdrawn upon automated export go-live |
| **REQ-20** | Unresolved proposal | Blocked (proposal) / Baseline active | D-41, Product notes (6 Sept) | Preserve baseline (18:00 Australia/Sydney); proposal blocked |
| **REQ-21** | Unresolved proposal | Blocked (proposal) / Baseline active | D-42, Product notes (6 Sept) | Preserve baseline (30-day retention); proposal blocked |
| **REQ-23** | Confirmed unchanged | Baseline active | D-43, REQ-23 | Preserve baseline unchanged |

---

## 3. Acceptance criteria for Ready items

| Criterion ID | Delivery item | Acceptance condition | Evidence basis | Upstream requirement(s) | Status |
|---|---|---|---|---|---|
| **REQ22-AC01** | REQ-22 | The daily invoice-exception export file is delivered using the existing managed SFTP gateway. | Explicit | AD-12, REQ-22 | Confirmed |
| **REQ25-AC01** | REQ-25 | Each exported row contains the `invoice_status` field populated with the exact status value copied from the source ERP (`OPEN`, `PAID`, or `VOID`). | Explicit | PD-51, REQ-25 | Approved |
| **REQ25-AC02** | REQ-25 | If the source ERP status is unavailable for an exported row, the `invoice_status` field value is set to null. | Explicit | PD-51, REQ-25 | Approved |
| **REQ25-AC03** | REQ-25 | Derived boundary: The `invoice_status` field does not populate default or inferred status values when the source ERP status is unavailable. | Derived boundary | PD-51, REQ-25 | Approved |

---

## 4. Partially Ready / blocked criteria and open questions

- **REQ-20 Export Schedule (Proposal for 19:00 Australia/Sydney):**
  - *Blocked Condition:* Shifting export runtime from 18:00 to 19:00 cannot be accepted.
  - *Blocker / Dependency:* Finance overnight consumption timing confirmation is pending.
  - *Decision Owner:* `Unknown`.
  - *Baseline Criterion Status:* Baseline runtime (18:00 Australia/Sydney per D-41) remains active.
- **REQ-21 Retention Period (Proposal for 7-day retention):**
  - *Blocked Condition:* Reducing retention from 30 days to 7 days cannot be accepted.
  - *Blocker / Dependency:* Data-governance approval is missing.
  - *Decision Owner:* `Unknown`.
  - *Baseline Criterion Status:* Baseline retention (30 days per D-42) remains active.

---

## 5. Candidate / conditional acceptance notes
*None identified from supplied decomposition.* (REQ-22 resolved from Candidate to Confirmed via AD-12).

---

## 6. Planning / quality targets
*None identified from supplied decomposition.*

---

## 7. Deferred items / Withdrawn scope

| Criterion ID | Delivery item | Status | Reason / Authority |
|---|---|---|---|
| **REQ24-AC01** | REQ-24 (Weekly manual pilot exception report) | Withdrawn | Explicitly withdrawn from target release scope upon automated daily export go-live per Sponsor Decision D-52. |

---

## 8. Traceability summary

- **REQ-22:** Traced to Architecture Decision AD-12 (`REQ22-AC01`).
- **REQ-24:** Traced to Sponsor Decision D-52 (De-scoped/Withdrawn).
- **REQ-25:** Traced to Product Decision PD-51 (`REQ25-AC01`, `REQ25-AC02`, `REQ25-AC03`).
- **REQ-20, REQ-21, REQ-23:** Baseline traceability maintained without alteration.

---

## 9. Readiness for test-case elaboration
**Readiness:** **Ready** for selective test derivation on supported affected scope (`REQ-22`, `REQ-24`, `REQ-25`).

---

## SUPPORTED_DELTA_FOR_TESTS
1. **REQ-22 / AD-12 (Transport Gateway):**
   - Condition: Daily export transmission must use the existing managed SFTP gateway.
   - Traceable AC: `REQ22-AC01`.
2. **REQ-25 / PD-51 (`invoice_status` Field Mapping and Null Handling):**
   - Condition 1: Export rows with source ERP status `OPEN`, `PAID`, or `VOID` must contain the exact string in `invoice_status`.
   - Condition 2: Export rows with unavailable source ERP status must populate `invoice_status` as null (no defaulting or inferred values).
   - Traceable ACs: `REQ25-AC01`, `REQ25-AC02`, `REQ25-AC03`.
3. **REQ-24 / D-52 (Weekly Manual Pilot Report De-scope):**
   - Condition: De-scoped / retired upon automated daily export go-live. Test cases associated with REQ-24 (`TC-24-1`) are withdrawn from the active target release test suite.

PIPELINE_HANDOFF_COMPLETE: ACCEPTANCE_CRITERIA

---

## test-cases — Derive Test Cases

# Test-Case Elaboration (Selective Requirement Delta)

## 1. Test-design readiness
**Readiness:** **Partially Ready**
- **Ready for derivation:** Supported affected delta scope (`REQ-22` / `REQ22-AC01`, `REQ-25` / `REQ25-AC01`, `REQ25-AC02`, `REQ25-AC03`).
- **De-scoped / Retired:** `REQ-24` / `REQ24-AC01` manual pilot report test coverage is withdrawn upon automated export go-live.
- **Preserved unchanged:** Baseline test coverage for `REQ-23` and active baselines for `REQ-20` (18:00 schedule) and `REQ-21` (30-day retention).
- **Blocked from derivation:** Unresolved change proposals for `REQ-20` (19:00 schedule) and `REQ-21` (7-day retention).

---

## 2. Acceptance-criterion readiness map

| Criterion ID | Delivery Item | Status | Action / Derivation Scope |
|---|---|---|---|
| **REQ22-AC01** | REQ-22 | Ready | Derive transport assurance / test case for existing managed SFTP gateway |
| **REQ25-AC01** | REQ-25 | Ready | Derive test cases for exact source passthrough (`OPEN`, `PAID`, `VOID`) |
| **REQ25-AC02** | REQ-25 | Ready | Derive test case for null value when source ERP status is unavailable |
| **REQ25-AC03** | REQ-25 | Ready | Derived boundary: verify absence of default or inferred status values when unavailable |
| **REQ24-AC01** | REQ-24 | Withdrawn | Retire / de-scope test cases from active target release suite |
| *Proposal (19:00)* | REQ-20 | Blocked | No test cases derived (baseline 18:00 test coverage preserved) |
| *Proposal (7-day)* | REQ-21 | Blocked | No test cases derived (baseline 30-day retention test coverage preserved) |
| *Baseline* | REQ-23 | Baseline active | Preserved unchanged without test rewrites |

---

## 3. Test cases for Ready / confirmed portions

| Test ID | AC ID | Delivery item | Test condition | Expected outcome | Evidence basis | Upstream REQ(s) |
|---|---|---|---|---|---|---|
| **TC-REQ22-01** | REQ22-AC01 | REQ-22 | Daily invoice-exception export file is generated for transmission. | File is delivered using the existing managed SFTP gateway. | Explicit | AD-12, REQ-22 |
| **TC-REQ25-01** | REQ25-AC01 | REQ-25 | Source ERP invoice record has status `OPEN`. | Exported row `invoice_status` field value equals `OPEN`. | Explicit | PD-51, REQ-25 |
| **TC-REQ25-02** | REQ25-AC01 | REQ-25 | Source ERP invoice record has status `PAID`. | Exported row `invoice_status` field value equals `PAID`. | Explicit | PD-51, REQ-25 |
| **TC-REQ25-03** | REQ25-AC01 | REQ-25 | Source ERP invoice record has status `VOID`. | Exported row `invoice_status` field value equals `VOID`. | Explicit | PD-51, REQ-25 |
| **TC-REQ25-04** | REQ25-AC02, REQ25-AC03 | REQ-25 | Source ERP invoice record status is unavailable. | Exported row `invoice_status` field is set to null, with no default or inferred status populated. | Explicit / Derived boundary | PD-51, REQ-25 |

---

## 4. Constraint / assurance checks

| Assurance ID | AC ID | Delivery item | Required condition to be assured | Evidence basis | Upstream REQ(s) |
|---|---|---|---|---|---|
| **AC-REQ22-01** | REQ22-AC01 | REQ-22 | The transmission route for daily invoice-exception export delivery is configured to use the existing managed SFTP gateway. | Explicit | AD-12, REQ-22 |

---

## 5. Blocked and unresolved coverage

- **REQ-20 Export Schedule (Proposal for 19:00 Australia/Sydney):** Untestable / blocked. Finance overnight consumption timing is pending confirmation (`Owner: Unknown`). Baseline 18:00 test coverage remains active.
- **REQ-21 Retention Period (Proposal for 7-day retention):** Untestable / blocked. Data-governance approval is missing (`Owner: Unknown`). Baseline 30-day retention test coverage remains active.

---

## 6. Candidate / conditional coverage notes
*None.* (No candidate or conditional scope items in supported delta).

---

## 7. Target / deferred coverage notes (De-scoped items)

| Criterion ID | Delivery item | Status | Impact on Test Suite | Authority |
|---|---|---|---|---|
| **REQ24-AC01** | REQ-24 | Withdrawn | Test coverage for the weekly manual pilot exception report (`TC-24-1` / manual report checks) is de-scoped and retired from the active target release test suite upon automated daily export go-live. | D-52 |

---

## 8. Traceability and coverage summary

- **REQ-22:** Covered by `TC-REQ22-01` and assurance check `AC-REQ22-01` against `REQ22-AC01` / AD-12.
- **REQ-25:** Covered by `TC-REQ25-01`, `TC-REQ25-02`, `TC-REQ25-03` (`REQ25-AC01`), and `TC-REQ25-04` (`REQ25-AC02`, `REQ25-AC03`) against PD-51.
- **REQ-24:** Identified as de-scoped and marked as retired per D-52.
- **REQ-20, REQ-21, REQ-23:** Baseline coverage preserved intact; unapproved proposals excluded from test execution baseline.

PIPELINE_HANDOFF_COMPLETE: TEST_CASES
