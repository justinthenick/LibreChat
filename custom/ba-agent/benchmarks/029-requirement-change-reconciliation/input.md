# Benchmark 029 Input — Vendor Export Requirements Delta

Compare the approved/current baseline with the later evidence packet. Do not assume that newer meeting notes automatically supersede the baseline.

## Baseline requirements — version 3

| ID | Statement | Status | Source |
|---|---|---|---|
| REQ-10 | Daily invoice-exception export runs at 18:00 Australia/Sydney. | Confirmed | Decision D-31 |
| REQ-11 | Export files are retained for 30 days. | Confirmed | Data handling decision D-27 |
| REQ-12 | Managed SFTP is the proposed transport, subject to architecture approval. | Candidate | Solution note S-18 |
| REQ-13 | Operations receives an email when the daily export job fails. | Confirmed | Operations decision D-29 |
| REQ-15 | During pilot, Operations also produces a weekly manual exception report. | Confirmed | Pilot scope D-25 |

Constraint CON-02: customer personal data must remain in Australia. Status Confirmed, source Legal L-9.

## Later evidence packet

### Architecture decision AD-7 — 4 September

- Status: Accepted.
- Decision: Use the existing managed SFTP gateway for the daily export transport.
- This explicitly resolves the transport candidate in REQ-12.

### Product meeting — 5 September

- Operations lead: "18:00 is a bit early. I'd rather move the export to 19:00."
- Product owner: "That could work, but Finance needs to confirm because they consume the file overnight. Leave the time open until they respond."
- Finance decision authority for the schedule is not otherwise documented in this packet.
- Analyst: "We can probably drop the 30-day retention now that the vendor imports quickly." No decision record or data-owner approval is supplied.
- Product owner: "Add invoice status to each exported row; that is approved for the next release." Meeting minutes mark this item `Approved`.
- No one mentions REQ-13 email failure notifications.

### Scope decision D-36 — 5 September

- Sponsor decision: the weekly manual pilot report is withdrawn when the automated daily export goes live.
- This explicitly removes REQ-15 from the target release.

### Legal note

- CON-02 Australian data residency remains unchanged.

## Request

Produce a traceable requirement delta suitable for selective downstream updates. Preserve baseline items that were not actually changed, distinguish proposals/disputes from authorized changes, and identify exactly which downstream requirement IDs need review.