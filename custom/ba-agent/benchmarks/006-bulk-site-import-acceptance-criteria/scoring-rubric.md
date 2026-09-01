# Benchmark 006 — Scoring Rubric

**Evaluator-only. Do not expose to the model under test.**

Total before penalties: **100 points**.

## 1. Readiness and status preservation — 20 points

- 5 — correctly states overall acceptance-criteria readiness as Partially Ready or clearly equivalent.
- 10 — preserves Ready / Partially Ready / Blocked / Candidate / Target / Deferred / Unknown / Disputed status.
- 5 — does not promote unresolved or non-committed items into mandatory acceptance conditions.

## 2. Acceptance-criteria quality for Ready / Partially Ready work — 30 points

- 7 — US-01 covers supported bulk submission and four supplied row elements without inventing file-format/UI rules.
- 8 — US-02 elaborates only the confirmed site-code/state minimum-data boundary and keeps site-name/region validation Unknown.
- 5 — EN-01 covers total/accepted/rejected counts plus associated date/time without inventing rejection-detail/storage behavior.
- 5 — US-03 preserves manual single-site entry when bulk import is unavailable without inventing mechanism.
- 5 — EN-02 carries all four confirmed security/read-only constraints without implying Candidate registry integration is committed.

## 3. Traceability and criterion structure — 15 points

- 10 — mandatory criteria consistently reference delivery item ID and upstream REQ ID(s).
- 3 — criterion IDs are stable/clear and conditions are reasonably atomic.
- 2 — traceability summary or equivalent accounts for non-ready items as well as Ready/Partially Ready work.

## 4. Uncertainty and blocker discipline — 15 points

- 6 — DEC-01 / REQ-004 produces no committed duplicate-handling criteria; both positions preserved; decision owner remains Unknown.
- 3 — SPK-01/CAN-01 / REQ-005 remain Candidate/Conditional pending feasibility; no lookup/integration mechanics invented.
- 2 — CAN-02 / REQ-007 pilot states remain Candidate/unapproved.
- 2 — OPEN-01 / REQ-009 retention remains Unknown with no duration/owner guessed.
- 2 — OPEN-02 / REQ-013 site-name/region validation remains Unknown; no rules invented.

## 5. Target / deferred / process-boundary discipline — 10 points

- 4 — TGT-01 / REQ-006 remains a non-binding processing Target, not a hard SLA/acceptance commitment.
- 2 — DEF-01 / REQ-008 remains Deferred with no current acceptance criteria.
- 4 — REQ-011 read-only Master Site Registry boundary is preserved; no write/update behavior is invented.

## 6. No-invention and downstream usability — 10 points

- 4 — no unsupported file format, delimiter, encoding, headers, column order, size, UI, progress, error/rejection-message, retry/timeout or validation behavior.
- 3 — no unsupported architecture/storage/database/API/protocol/vendor detail.
- 2 — Given/When/Then, if used, contains only evidenced preconditions/actions/outcomes; otherwise concise declarative criteria are used.
- 1 — readiness for test-case elaboration is stated sensibly.

# Penalties

Apply after the 100-point score. Minimum final score is zero.

- **-12 each** — silently resolves REQ-004 duplicate handling or writes committed criteria assuming whole-import rejection / duplicate-row-only continuation.
- **-10 each** — serious invented current-scope capability, actor, permission, governance authority or business rule presented as fact.
- **-8** — treats REQ-005 Master Site Registry validation as Ready/Confirmed committed behavior.
- **-8** — treats New South Wales / Victoria pilot scope as approved committed scope.
- **-8** — elaborates REQ-008 scheduled recurring imports as current criteria.
- **-5** — converts the 10,000-row / ten-minute Target into a hard SLA or mandatory acceptance criterion.
- **-5 each** — invents file format, delimiter, encoding, headers, column order, maximum file size, row ordering, blank-value rule, rejection-detail format, validation/error message, retry/timeout behavior, site-name/region validation, retention duration/regulation/owner or other unsupported behavior.
- **-5 each** — invents API protocol/endpoint, webhook, queue, database/storage design, cache, workflow engine, product/vendor or other architecture component.
- **-5** — invents write/update behavior against the Master Site Registry.
- **-5** — creates estimates, points, sprint assignments, delivery dates or test-automation implementation.
- **-5** — creates detailed unsupported Given/When/Then relying on invented UI/actions/errors/batch mechanics.
- **-3 each** — meaningful status/readiness promotion or downgrade without evidence.
- **-3 each** — material mandatory criterion lacks delivery-item/upstream traceability.
- **-3 each** — references a non-existent work-item/criterion ID.

# Interpretation

- **90-100:** excellent; strong generalized acceptance-criteria discipline.
- **80-89:** good; useful with limited correction.
- **70-79:** acceptable experiment; notable gaps remain.
- **50-69:** weak; significant BA/product review required.
- **Below 50:** unreliable for this workflow.

A response that resolves duplicate handling, commits Candidate registry validation, invents material file/validation/architecture behavior, writes to the Master Site Registry, or turns the Target into a binding SLA should not be considered production-ready regardless of numeric score.

# Comparison rule

Benchmark 006 is a generalization test for `elaborate-acceptance-criteria` v0.1 after a very strong Benchmark 005 baseline.

Run the same model/settings/input in baseline and Skill modes. Do not modify the Skill between paired runs.

Retain v0.1 as generalized only if it preserves or improves discipline on this materially different batch-data problem without increasing invention, status promotion or decision resolution.
