# Benchmark 042 scoring rubric — Multi-Source BA Model Comparison

Score each model run out of 100.

## 1. Multi-source utilization — 20
- 20: All four sources materially influence the BA package; XLS is treated as a first-class operational decision/configuration source and is directly traced across multiple requirements/RTM rows.
- 14: All sources used, but one source (especially XLS) is mostly summarized rather than operationalized.
- 7: One source is materially underused.
- 0: A major source is effectively ignored or misrepresented.

## 2. Cross-source contradiction detection — 20
Award 5 points each for correctly preserving, without silently resolving:
- DOC vs XLS lead-time conflict;
- DOC vs XLS MOP/SWMS document-rule conflict;
- competing Standard Change state paths;
- CyberKey Field 69 contradictory display wording.

## 3. Unresolved-dimension recall and cardinality — 15
- 15: Preserves exactly the four source-created process-map unresolved dimensions: flagged-user outcome, post-visit quota, post-visit entity/channel, minor date-change target state. No adjacent invented questions.
- 10: Misses one or combines two dimensions without losing their meaning.
- 5: Misses two or introduces extra unsourced questions.
- 0: Resolves or substantially rewrites the unresolved source conditions.

## 4. Source-closure / no invented benefits or governance — 15
- 15: Uses only explicitly sourced benefits/outcomes and does not invent decision owners, generic benefits, governance bodies, NFRs, risks or engineering gaps.
- 10: One minor interpretive benefit/proposal appears but does not affect requirements/readiness.
- 5: Multiple plausible-but-unsourced benefits/questions appear.
- 0: Material negative-space leakage or invented governance/decision ownership.

## 5. XLS-derived operational requirements — 10
- 10: Surfaces taxonomy, assignment routing, Standard eligibility, SAR eligibility, document flags and approval matrix as requirements/rules, while preserving conflicts where applicable.
- 7: Captures most but misses one important XLS-controlled behavior.
- 3: Uses XLS only for taxonomy or examples.
- 0: XLS does not materially drive the requirement set.

## 6. Decomposition and acceptance-criteria discipline — 10
- 10: Backlog remains solution-neutral; ACs test only established outcomes and do not decide disputed/Unknown rules.
- 7: Mostly disciplined with one over-specified item.
- 3: Several ACs or backlog items resolve unknowns or invent mechanisms.
- 0: Decomposition materially departs from source evidence.

## 7. RTM and status preservation — 5
- 5: Strong source -> requirement -> backlog -> AC/status traceability; disputed/unknown states survive into downstream artifacts.
- 3: Traceability present but incomplete or inconsistent.
- 0: Status is lost or RTM materially misstates source certainty.

## 8. Readiness assessment — 5
- 5: Correctly distinguishes source-closed implementation-ready areas from source-created unresolved areas, with no generic missing-engineering blockers.
- 3: Mostly correct with one readiness overreach/omission.
- 0: Declares disputed areas implementation-ready or manufactures generic blockers.

## Automatic fail conditions

Benchmark fails regardless of numeric score if the response:
- silently chooses one lead-time source as the authoritative final algorithm;
- silently converts the DOC/XLS MOP/SWMS conflict into one confirmed universal rule;
- declares one universal Standard Change state path despite the supplied conflict;
- "fixes" the CyberKey Field 69 contradiction to a guessed condition instead of preserving Unknown;
- invents an answer to the flagged-user, post-visit quota/entity, or minor-date-state questions;
- materially ignores `SRC-XLS-01` as an operational source;
- invents decision owners/governance authorities not established by the pack;
- introduces unsourced security, performance, availability, retry, logging, audit, API, database, rollback/deployment or similar engineering requirements/gaps;
- creates acceptance criteria that make a disputed/Unknown business rule executable as if decided.

## Pass threshold

**PASS: 90/100 or higher and no automatic fail condition.**

## Model-comparison decision rule

This benchmark is intended to compare Gemini 3.7 Flash and Gemini 3.8 Flash using the same Skill and temperature.

Prefer 3.8 as the BA Supervisor default if:
- its score is >= 90 with no automatic fail; and
- it beats 3.7 by at least 3 points, or ties within 2 points while showing materially better source utilization/contradiction preservation with no increase in source-closure violations.

Do not change the Skill merely to optimize one model's score unless the benchmark exposes a reusable Skill defect across models.
