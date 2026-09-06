# Benchmark 030 Evaluation — Architecture Decision Recording v0.1

Evaluator-only record. Raw outputs remain unchanged.

## Run

- Model: `gemini-3.5-flash` (fallback after Gemini 3.7 provider-busy pair)
- Temperature: `0.0`
- Baseline: 2026-09-05 07:29:26–07:29:32 Australia/Sydney, 2,026 total tokens
- Skill v0.1: 2026-09-05 07:29:32–07:29:42 Australia/Sydney, 3,577 total tokens

## Scores

### Baseline — 98/100, zero critical penalties

- A. Accepted D-44 ADR: 35/35
- B. Recommendation / candidate discipline: 25/25
- C. Target / Unknown preservation: 15/15
- D. Rationale / consequence discipline: 15/15
- E. ADR quality: 8/10

The baseline records the accepted decision and keeps backoff, queueing and the five-minute goal non-committed without inventing implementation detail. It is slightly less inspectable as a multi-record ADR package but stays very close to the supplied architecture evidence.

### `record-architecture-decisions` v0.1 — 93/100, zero critical penalties

- A. Accepted D-44 ADR: 35/35
- B. Recommendation / candidate discipline: 25/25
- C. Target / Unknown preservation: 15/15
- D. Rationale / consequence discipline: 8/15
- E. ADR quality: 10/10

The Skill handles accepted/recommended/candidate/Target states correctly and does not harden retry, queueing, polling interval or credentials. Its reusable defect is **ADR completeness inflation**: it manufactures plausible trade-offs to fill conventional ADR sections. Examples include `wait for webhook avoids polling overhead` and `new middleware isolates polling logic but introduces operational complexity`; neither trade-off is supplied in the architecture evidence. It also adds `Awaiting Architecture Review Board or designated authority approval` to the candidate ADR even though no source establishes the future decision forum for those unaccepted items.

No critical penalty applies because the candidate authority field itself remains `Unknown`, no implementation mechanism is committed, and no forbidden parameter/product is invented. But ADR records are durable governance artifacts, so plausible-but-unsourced rationale must be removed before Architecture Agent use.

## Decision

Create one focused v0.2 correction that:

- records only evidenced trade-offs/rationale/consequences and allows an ADR section to state `Not evidenced` rather than filling it by architectural common sense;
- keeps the future decision forum/approval path Unknown for recommendations/candidates unless explicitly supplied;
- does not combine unrelated unaccepted items into a pseudo-decision merely to complete an ADR template when a status register is sufficient.

Then run a same-model Skill-only rerun against this preserved Gemini 3.5 baseline.
