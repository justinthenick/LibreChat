# Benchmark 037 Gold Standard — Evaluator Only

## Expected route

Exactly:

1. `reconcile-requirement-changes`
2. `elaborate-acceptance-criteria`
3. `derive-test-cases`

Do not add:

- `analyze-requirements` — the supported new/changed requirements are sufficiently explicit for the requested downstream work.
- `decompose-requirements` — current decomposition is explicitly stated to remain valid for these transport/payload deltas.
- `assess-change-impact` — the current impact assessment is explicitly sufficient for transport/payload-field changes and no later evidence expands system/process/stakeholder scope.

## Supported deltas

- REQ-22: Candidate managed SFTP -> Accepted/Confirmed managed SFTP via AD-12.
- New requirement from PD-51: add `invoice_status`, exact source value, supported `OPEN|PAID|VOID`, null when source unavailable.
- REQ-24: Removed/withdrawn from target release via D-52.

## Unresolved / unchanged

- REQ-20 remains Confirmed at 18:00; 19:00 is an unresolved preference pending confirmation/evidence. Do not assign Finance as Decision Owner absent explicit authority.
- REQ-21 remains Confirmed at 30 days; seven-day retention is an unsupported analyst suggestion.
- REQ-23 remains Confirmed; silence is not removal.

## Expected downstream updates

Acceptance criteria/test coverage should be updated only for supported deltas:

- REQ-22: make the transport-specific acceptance/test expectation concrete for managed SFTP without inventing technical mechanisms beyond the decision.
- New `invoice_status` requirement: create acceptance criteria and tests covering exact passthrough of OPEN/PAID/VOID and null when source is unavailable; no guessed/default status.
- REQ-24: identify AC-24-1 / TC-24-1 as removed/de-scoped rather than continuing them as target-release requirements.

Do not rewrite AC/tests for REQ-20, REQ-21 or REQ-23 from this packet.

## Critical defects

- changing REQ-20 to 19:00 as approved;
- assigning Finance as Decision Owner without authority evidence;
- reducing REQ-21 retention to seven days;
- treating REQ-23 as removed due to silence;
- failing to recognize AD-12, PD-51 or D-52 as supported deltas;
- redoing decomposition or impact analysis despite explicit current sufficiency;
- regenerating unaffected acceptance criteria/tests as though changed;
- inventing invoice-status values/defaulting behavior beyond PD-51.
