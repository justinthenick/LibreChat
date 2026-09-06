# Benchmark 037 Input — Vendor Export Selective Downstream Update

A mature requirement baseline already has decomposition, acceptance criteria, tests and a current impact assessment. Later evidence introduces a mix of supported changes and unresolved proposals. Update only what the evidence justifies.

## Current baseline — version 4

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-20 | Daily invoice-exception export runs at 18:00 Australia/Sydney. | Confirmed | Decision D-41 |
| REQ-21 | Export files are retained for 30 days. | Confirmed | Data decision D-42 |
| REQ-22 | Managed SFTP is the proposed transport, pending architecture decision. | Candidate | Solution note S-20 |
| REQ-23 | Operations receives an email when the daily export job fails. | Confirmed | Operations decision D-43 |
| REQ-24 | During pilot, Operations produces a weekly manual exception report. | Confirmed | Pilot decision D-44 |

Current decomposition is explicitly stated to remain valid if transport and payload-field details change. A current impact assessment dated 5 September covers the export service, vendor intake process and Operations support flow and is explicitly stated to remain sufficient for transport/payload-field changes in this release. Do not rerun it unless later evidence changes system/process/stakeholder scope beyond those boundaries.

## Current acceptance/test artifacts

- AC-22-1: export is delivered using the transport approved for REQ-22.
- TC-22-1: verify the approved transport can deliver a representative export and the vendor can retrieve it.
- AC-24-1 / TC-24-1 cover production of the weekly manual pilot report.
- There is no acceptance criterion or test case yet for invoice-status data because that field is not in the baseline.

## Later evidence packet

### Architecture decision AD-12 — 6 September

Status: Accepted.

Decision: use the existing managed SFTP gateway for the daily export. This resolves REQ-22.

### Product decision PD-51 — 6 September

Status: Approved.

Add `invoice_status` to each exported row. The value must be copied from the source ERP status exactly. Supported source values for this release are `OPEN`, `PAID`, and `VOID`. If the source status is unavailable, the exported field must be null rather than guessed or defaulted.

### Sponsor decision D-52 — 6 September

The weekly manual pilot report is withdrawn when the automated daily export goes live. This explicitly removes REQ-24 from target release scope.

### Product meeting notes — 6 September

- Operations lead: "I'd prefer the export at 19:00 instead of 18:00."
- Product owner: "Leave that open until Finance confirms the overnight consumption timing."
- Finance decision authority is not otherwise documented.
- Analyst: "We can probably cut retention to seven days now." No data-governance decision or approval is supplied.
- REQ-23 is not mentioned.

## Request

Reconcile the baseline against the later evidence, then update only the downstream **acceptance criteria and test coverage** affected by supported material deltas. Do not redo stable decomposition or the current impact assessment. Do not propagate the unresolved 19:00 or seven-day proposals as approved changes.
