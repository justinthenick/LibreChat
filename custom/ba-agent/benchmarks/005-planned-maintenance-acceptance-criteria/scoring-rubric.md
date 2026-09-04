# Benchmark 005 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Readiness and status preservation — 20 points

- 5 — correctly states overall acceptance-criteria readiness as Partially Ready or clearly equivalent.
- 10 — preserves Ready / Blocked / Candidate / Target / Deferred / Unknown / Disputed status across the supplied decomposition.
- 5 — does not silently promote unresolved or non-committed items into mandatory acceptance conditions.

## 2. Acceptance-criteria quality for Ready work — 30 points

- 8 — US-01 criteria cover the supported notice creation and four supplied data elements without inventing extra validation/UI behavior.
- 7 — US-02 correctly captures the approved Change-reference publication boundary without redesigning Change approval.
- 5 — EN-01 covers publication outcome + associated date/time without adding audit/storage qualities.
- 5 — US-03 preserves manual publication availability when integration is unavailable without inventing channel/mechanism.
- 5 — EN-02 carries the three confirmed security constraints without implying Candidate integration is committed.

## 3. Traceability and criterion structure — 15 points

- 10 — mandatory criteria consistently reference delivery item ID and upstream REQ ID(s).
- 3 — criterion IDs are stable/clear and individual conditions are reasonably atomic.
- 2 — traceability summary or equivalent accounts for the non-ready items as well as Ready work.

## 4. Uncertainty and blocker discipline — 15 points

- 6 — DEC-01 / REQ-004 produces no committed cancellation criteria; both stakeholder positions are preserved; decision owner remains Unknown.
- 4 — SPK-01/CAN-01 / REQ-005 remain Candidate/Conditional pending feasibility; no channels or integration mechanics are invented.
- 2 — CAN-02 / REQ-007 pilot scope remains Candidate/unapproved.
- 2 — OPEN-01 / REQ-009 retention remains Unknown/open with no duration/owner guessed.
- 1 — unresolved items visibly block later test-case elaboration where relevant.

## 5. Target / deferred / process-boundary discipline — 10 points

- 4 — TGT-01 / REQ-006 remains a non-binding 24-hour Target and is not converted to pass/fail acceptance.
- 2 — DEF-01 / REQ-008 remains Deferred with no current acceptance criteria.
- 4 — REQ-011 Change-approval boundary is respected; no CAB/process redesign or approval authority is invented.

## 6. No-invention and downstream usability — 10 points

- 4 — no unsupported UI, notification, error-message, validation, retry, timeout or workflow behavior.
- 3 — no unsupported architecture/storage/API/protocol/vendor detail.
- 2 — Given/When/Then, if used, contains only evidenced preconditions/actions/outcomes; otherwise concise declarative criteria are used.
- 1 — readiness for test-case elaboration is stated sensibly.

# Penalties

Apply after the 100-point score. Minimum final score is zero.

- **-12 each** — silently resolves REQ-004 cancellation handling or writes committed criteria assuming automatic withdrawal / human confirmation.
- **-10 each** — serious invented current-scope capability, actor, permission, governance authority or business rule presented as fact.
- **-8** — treats REQ-005 automated subscriber notification as Ready/Confirmed committed behavior.
- **-8** — treats Mobile App / Billing Portal pilot scope as approved committed scope.
- **-8** — elaborates REQ-008 automatic post-maintenance closure as current acceptance criteria.
- **-5** — converts the 24-hour Target into a hard SLA or mandatory acceptance criterion.
- **-5 each** — invents retention duration/regulation/owner, notification channel, message template, subscriber preference, retry/timeout behavior, Change-ID format, date/time format/timezone, duplicate rule, ordering rule such as end-after-start, character limit, validation/error message or other unsupported behavior.
- **-5 each** — invents API protocol/endpoint, webhook, queue, database/storage design, workflow engine, product/vendor or other architecture component.
- **-5** — redesigns CAB/Change approval or invents a new approval authority/process.
- **-5** — creates estimates, points, sprint assignments, delivery dates or test-automation implementation.
- **-5** — creates detailed unsupported Given/When/Then scenarios relying on invented login/UI/actions/errors/notifications.
- **-3 each** — meaningful status/readiness promotion or downgrade without evidence.
- **-3 each** — material mandatory acceptance criterion lacks delivery-item/upstream traceability.
- **-3 each** — references a non-existent work-item/criterion ID.

# Interpretation

- **90-100:** excellent; strong acceptance-criteria discipline.
- **80-89:** good; useful with limited correction.
- **70-79:** acceptable experiment; notable gaps remain.
- **50-69:** weak; significant BA/product review required.
- **Below 50:** unreliable for this workflow.

A response that resolves REQ-004, commits Candidate notification behavior, invents material UI/error/channel/architecture behavior, or turns the Target into a binding SLA should not be considered production-ready regardless of numeric score.

# Comparison rule

Benchmark 005 is the first benchmark for `elaborate-acceptance-criteria` v0.1.

Run the same model/settings/input in baseline and skill modes. Do not modify the skill between paired runs.

If v0.1 materially improves testability/traceability without increasing invention or status promotion, retain it for a second materially different benchmark before declaring the capability generalized.
