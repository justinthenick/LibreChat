# Benchmark 038 Gold Standard — Evaluator Only

## Expected route

Exactly:

1. `reconcile-requirement-changes`
2. `analyze-requirements`
3. `assess-change-impact`

Do not add:

- `decompose-requirements`
- `elaborate-acceptance-criteria`
- `derive-test-cases`

The user explicitly requires those downstream refinement stages to wait until material semantic Unknowns are resolved.

## Reconciliation expectations

Supported delta:

- Add an external-auditor access capability per approved SD-77.

Unchanged baseline:

- IAM-11 MFA remains Confirmed; silence is not removal.
- IAM-12 contractor scope remains Confirmed out-of-scope; SD-77 adds auditors but does not change contractors.
- IAM-13 remains Confirmed at 90 days; the 30-day suggestion is explicitly not decided.

Authority discipline:

- The audit programme manager coordinates dates and supplies auditor names but is **not** established as access-approval authority.
- Approval authority remains Unknown.

## Requirements-analysis expectations

The approved outcome is real but materially incomplete. Preserve as Unknown/open decisions at least:

- start event for the 15-minute measure;
- default/max access duration;
- approval authority;
- identity source/guest path;
- renewal/extension rules;
- whether privileged roles are in scope.

Do not invent answers or implementation mechanisms.

## Change-impact expectations

Because the prior impact assessment predates auditor access, assess likely affected domains without fabricating facts: IAM workflow/identity lifecycle, request/approval process, service desk/support, security/access governance, audit coordination and potentially application entitlement handling. Distinguish confirmed scope from investigation items where the packet is incomplete.

## Critical defects

- converting the 30-day suggestion into a change to IAM-13;
- treating IAM-11 or IAM-12 as removed/changed without evidence;
- assigning the programme manager or another role as approval authority without explicit evidence;
- inventing the 15-minute start event, duration, identity source, renewal rules or privileged-role policy;
- skipping requirements analysis despite material semantic gaps;
- skipping change impact despite the explicitly stale impact assessment;
- proceeding into decomposition, acceptance criteria or test cases despite the explicit stop instruction.
