# Benchmark 007 — Gold Standard

**Evaluator-only. Do not expose to the model under test.**

This benchmark evaluates whether `derive-test-cases` can turn ready acceptance criteria into traceable behavioural test coverage without inventing execution mechanics, environments, data values or unresolved behaviour.

## Expected readiness

Overall: **Partially Ready**.

Current test cases may be derived for:

- US-01-AC01 — create release-verification record with the four sourced data elements;
- US-02-AC01 / AC02 — approved-Change readiness boundary;
- EN-01-AC01/02/03 — retain verification outcomes and associated date/time;
- US-03-AC01 — manual evidence attachment remains available when automated import is unavailable.

Conditional constraint assurance may be recorded for EN-02 / EN-03 if Candidate integration proceeds, but that must not imply the integration itself is committed.

The following remain isolated:

- DEC-01 / REQ-004 failed-validation response — Blocked / Disputed;
- SPK-01 / CAN-01 / REQ-005 automated import — Candidate / unverified;
- CAN-02 / REQ-007 pilot services — Candidate / unapproved;
- TGT-01 / REQ-006 fifteen-minute objective — Target / non-binding;
- DEF-01 / REQ-008 predictive risk scoring — Deferred;
- OPEN-01 / REQ-009 retention — Unknown.

## Expected test coverage

### US-01-AC01

Expected test intent:

- exercise creation of a release-verification record by the sourced actor;
- verify the resulting record contains service/application, release version, target environment and Change ID.

Do not invent actual values, field formats, screens, buttons, forms, account/login state or validation behaviour.

### US-02-AC01 / US-02-AC02

Expected:

- positive case: where the record references an approved Change ID, it may be marked ready for execution;
- negative/derived-boundary case: where it does not reference an approved Change ID, it cannot be marked ready for execution.

Do not invent how approval is checked, a CAB lookup, API, error banner, rejection reason, role, approval workflow or Change-ID format.

### EN-01-AC01/02/03

Expected tests verify that the record retains:

- pre-deployment verification outcome;
- post-deployment verification outcome;
- associated date/time information.

Do not invent outcome enumerations, exact timestamps, log/storage technology, actor metadata or retention duration.

### US-03-AC01

Expected:

- when automated deployment-result import is unavailable, manual evidence attachment remains available.

Do not invent upload UI, file type, attachment size, channel, retry/failover or synchronization mechanics.

### EN-02 conditional constraints

If represented, these are assurance checks rather than evidence that Candidate integration is committed:

- approved service identity;
- least privilege;
- no new shared administrator account.

Do not invent IAM products, credentials, permission names, inspection evidence or automation.

### EN-03 conditional constraints

If Candidate import proceeds, verify imported evidence retains source reference and imported outcome.

Do not invent source-system identifiers, protocols, payloads, formats or mapping logic.

## Critical blocked decision — DEC-01 / REQ-004

No committed test cases for failed-validation response.

Both positions remain visible:

- Service Reliability Lead: automatic rollback;
- Application Owner: pause and human decision.

Decision owner remains **Unknown**.

Do not create tests assuming either behaviour, a compromise, an escalation role or rollback technology.

## Candidate import — REQ-005

No committed functional tests for automatic deployment-result import until feasibility/scope are resolved. Conditional constraint notes are acceptable, but no API, webhook, endpoint, retry, timeout, queue, mock/stub or deployment product may be invented.

## Target — REQ-006

The fifteen-minute objective remains non-binding. It may be recorded as a future/non-gating performance observation opportunity but not a pass/fail release gate.

## Deferred / Unknown

- No current tests for predictive risk scoring.
- No retention-duration tests until REQ-009 is resolved.

## Traceability

Each current test case must reference:

- test-case ID;
- acceptance-criterion ID;
- delivery-item ID;
- upstream REQ ID(s).

A strong coverage summary accounts for all Ready, Blocked, Candidate, Target, Deferred and Unknown areas.

## Test-case execution discipline

Do not invent:

- concrete test data values;
- test environment names;
- test accounts or permissions;
- UI click paths;
- API calls/payloads;
- expected error messages;
- storage/logging mechanisms;
- automation frameworks/scripts;
- mocks/stubs;
- timing retries/timeouts;
- delivery dates.

Expected overall result: behavioural test cases are specific enough to express what to verify while deliberately leaving execution mechanics open.
