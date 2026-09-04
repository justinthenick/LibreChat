# Benchmark 007 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Readiness and status preservation — 15 points

- 5 — correctly states overall test-design readiness as Partially Ready or clearly equivalent.
- 6 — preserves Ready / Blocked / Candidate / Target / Deferred / Unknown / Disputed states.
- 4 — does not promote unresolved or non-committed areas into mandatory tests.

## 2. Test-case quality for Ready work — 35 points

- 8 — US-01-AC01 is covered with a behavioural test that verifies the sourced actor/outcome/data elements without inventing UI or concrete values.
- 9 — US-02-AC01/02 are covered with the supported positive and negative readiness boundary without inventing Change-approval lookup mechanics or error behaviour.
- 8 — EN-01-AC01/02/03 are covered for the two outcomes and associated date/time without inventing outcome values, storage/logging or retention behaviour.
- 5 — US-03-AC01 verifies manual evidence attachment remains available when automated import is unavailable without inventing attachment mechanics.
- 5 — EN-02/EN-03 conditional constraints are represented appropriately without implying Candidate import is committed.

## 3. Traceability and coverage integrity — 20 points

- 12 — every material current test references AC ID, delivery item and upstream REQ ID(s).
- 4 — stable test IDs and reasonably atomic cases.
- 4 — coverage summary or equivalent accounts for Ready, blocked, Candidate, Target, Deferred and Unknown areas.

## 4. Uncertainty and blocker discipline — 15 points

- 6 — DEC-01 / REQ-004 produces no committed test assuming rollback or human-decision behaviour; both positions remain visible and Decision owner remains Unknown.
- 4 — SPK-01/CAN-01 / REQ-005 remain Candidate/Conditional; no automatic-import functional tests or integration mechanics invented.
- 2 — CAN-02 / REQ-007 remains Candidate/unapproved.
- 1 — TGT-01 / REQ-006 remains non-binding rather than pass/fail.
- 1 — DEF-01 / REQ-008 remains Deferred.
- 1 — OPEN-01 / REQ-009 remains Unknown with no duration/owner guessed.

## 5. No-invention / execution-mechanics discipline — 15 points

- 5 — no unsupported UI actions, login/account state, roles/permissions or error-message behaviour.
- 4 — no invented concrete test data values, formats, environment names or boundary numbers.
- 4 — no invented APIs, payloads, storage, queues, retry/timeout, mocks/stubs, automation frameworks or test tooling.
- 2 — cases remain useful as behavioural/assurance intent without pretending execution design is known.

# Penalties

Apply after the 100-point score. Minimum final score is zero.

- **-12 each** — silently resolves REQ-004 or creates committed failed-validation tests assuming automatic rollback / human decision.
- **-10 each** — serious invented current-scope capability, actor, permission, governance authority or business rule presented as fact.
- **-8** — treats Candidate automated deployment-result import as Ready/Confirmed and creates committed import-functional test cases.
- **-8** — treats Billing API / Customer Portal pilot as approved committed scope.
- **-8** — creates current predictive-risk tests for Deferred REQ-008.
- **-5** — converts the fifteen-minute Target into a mandatory pass/fail test or release gate.
- **-5 each** — invents concrete test data values, Change-ID format, date/time format/timezone, outcome enumeration, retention duration/regulation/owner, attachment format/size, validation/error text or other unsupported behavioural detail.
- **-5 each** — invents API protocol/endpoint/payload, webhook, queue, database/storage design, retry/timeout, mock/stub architecture, automation framework/tool or other execution mechanism.
- **-5** — redesigns Change approval or invents a new approval authority/process.
- **-5** — creates estimates, sprint assignments, test-execution dates or delivery dates.
- **-3 each** — meaningful readiness/status promotion or downgrade without evidence.
- **-3 each** — material current test lacks AC/work-item/REQ traceability.
- **-3 each** — references a non-existent AC/work-item/test ID.

# Interpretation

- **90-100:** excellent; strong test/assurance traceability discipline.
- **80-89:** good; useful with limited correction.
- **70-79:** acceptable experiment; notable gaps remain.
- **50-69:** weak; significant BA/test review required.
- **Below 50:** unreliable for this workflow.

A response that resolves failed-validation behaviour, commits Candidate import, invents material execution mechanics or makes the Target a release gate should not be considered production-ready regardless of numeric score.

# Comparison rule

Benchmark 007 is the first benchmark for `derive-test-cases` v0.1.

Run the same model/settings/input in baseline and Skill modes. Do not modify the Skill between paired runs.

If v0.1 materially improves traceability/coverage while reducing execution-mechanism invention, retain it for a second materially different test-design benchmark before declaring the capability generalized.
