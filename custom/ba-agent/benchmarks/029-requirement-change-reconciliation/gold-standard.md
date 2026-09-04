# Benchmark 029 Gold Standard — Evaluator Only

## Expected delta summary

Material supported deltas:

- REQ-12: Candidate transport -> Accepted/Confirmed managed SFTP via AD-7.
- New requirement: invoice status added to each exported row, Approved in 5 September meeting; assign a new requirement ID only if the reconciliation output needs a local ID, while preserving source provenance.
- REQ-15: explicitly Removed/withdrawn from target release via sponsor decision D-36.
- CON-02: Confirmed unchanged by explicit Legal note.

Unresolved / not-authorized proposals:

- REQ-10 schedule change from 18:00 to 19:00 is **not approved**. Baseline 18:00 remains the current Confirmed requirement, while a proposed change/dispute is open pending decision. Do not infer Finance as Decision Owner merely because Finance needs to confirm consumption impact; authority is not otherwise documented.
- REQ-11 30-day retention is **not removed**. Analyst says it can probably be dropped, but no decision/data-owner authority is supplied. Baseline Confirmed 30-day retention remains current; proposal to remove is unapproved/disputed/candidate.

Untouched by silence:

- REQ-13 failure email remains Confirmed. It is absent from later meeting notes, but silence is not removal.

## Expected downstream selective-update handoff

- REQ-12 downstream artifacts require update because transport status changed to Accepted/Confirmed managed SFTP.
- New invoice-status requirement needs downstream analysis/decomposition.
- REQ-15 downstream artifacts need removal/de-scope review because withdrawal is explicit.
- REQ-10 downstream artifacts should **not yet be changed to 19:00**; mark schedule proposal/decision pending and review once resolved.
- REQ-11 downstream artifacts should **not remove 30-day retention**; record the proposal/question only.
- REQ-13 no downstream update required from this packet.
- CON-02 no change required; remains Confirmed and should continue to be preserved.

## Critical defects

- changing REQ-10 to 19:00 as if approved;
- assigning Finance as Decision Owner without explicit authority evidence;
- deleting/reducing REQ-11 retention from the analyst suggestion;
- treating REQ-13 as removed because it was not mentioned;
- failing to recognize AD-7 as resolving REQ-12;
- failing to recognize D-36 as explicit withdrawal of REQ-15;
- silently removing CON-02 or other baseline evidence not superseded.