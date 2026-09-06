# BA Specialist Pipeline Stage

## Metadata

```json
{
  "agent_path": "custom/ba-agent/skills/derive-test-cases/SKILL.md",
  "agent_sha256": "5105a2f0965663cf0f7f24ecedd8b8dc11f3d20afdc2815e25a224d7297df995",
  "agent_version": "0.3.0",
  "ended_at": "2026-09-06T01:40:40Z",
  "error": null,
  "finish_reason": "STOP",
  "max_output_tokens": 8192,
  "model": "gemini-3.7-flash",
  "pipeline": "Benchmark 037 \u2014 Fixed selective requirement-delta control",
  "run_id": "b037-g37-a004-control-024",
  "stage_id": "test-cases",
  "stage_index": 3,
  "stage_input_sha256": "42fa701c61c2e4eced31d22cebd0df0afd9d068e33c855f60b7a0b522af306f8",
  "stage_name": "Derive Test Cases",
  "started_at": "2026-09-06T01:40:32Z",
  "status": "success",
  "temperature": 0.0,
  "upstream_output_sha256": "b9bcd59ba7b152dfbf8525e4d07097487ef51bfe4813d310212bc863427f4678",
  "usage": {
    "candidatesTokenCount": 1501,
    "promptTokenCount": 3116,
    "promptTokensDetails": [
      {
        "modality": "TEXT",
        "tokenCount": 3116
      }
    ],
    "serviceTier": "standard",
    "thoughtsTokenCount": 926,
    "totalTokenCount": 5543
  }
}
```

---

## Stage output

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
