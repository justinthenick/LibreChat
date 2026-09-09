# Benchmark 043 scoring rubric — evaluator only

Score out of 100. Pass threshold: **90/100 with no automatic-fail condition**.

## 1. Multi-source utilisation — 10 points
- 10: materially uses all four sources and preserves their evidentiary roles.
- 5: one source is only superficially mentioned.
- 0: materially ignores a source that should affect the answer.

## 2. Structured operational controls — 20 points
Award for operationalising the SRC-XLS-01 controls rather than leaving them in the source register:
- taxonomy + explicit label/field mappings: 4
- `assignment_queue` routing: 4
- `Permit option available?`: 3
- `Remote Review available?`: 3
- `Evidence Required?`: 3
- `Risk Band`: 3

## 3. Multiplicity discipline — 20 points
- 20: multi-region affiliation is preserved as a condition with required handling outcome Unknown; no candidate set-handling policy is promoted into requirement/AC.
- 10: correctly marks Unknown but unnecessarily enumerates possible handling policies.
- 0: confirms or tests union/intersection/primary-region/select/display-all or another unsourced policy.

## 4. Target-state abstraction discipline — 20 points
- 20: preserves both gate-entry and final-exit outcomes as Target/Candidate at the sourced abstraction, with no invented implementation-mechanism questions/blockers.
- 10: mostly correct but mentions an unsourced mechanism as a non-mandatory consideration.
- 0: creates Decision Items, requirements, blockers or ACs around scanners/APIs/webhooks/event detection/transport/reconciliation not raised by the source.

## 5. Naming / field-mapping discipline — 10 points
- 10: treats business labels and technical identifiers as explicit mappings only.
- 0: creates a contradiction, ambiguity, precedence question or Decision Item solely because the names differ.

## 6. Explicit contradiction preservation — 10 points
- 10: universal evidence-upload rule vs activity `Evidence Required?` flags is preserved as one Disputed source conflict and not executed in confirmed AC.
- 5: detects the conflict but downstream status/AC discipline is imperfect.
- 0: silently chooses one rule or executes a disputed rule as confirmed.

## 7. Unresolved-cardinality / source closure — 5 points
- 5: preserves the single SRC-MAP-01 out-of-hours self-approval question and introduces no unrelated engineering/governance questions.
- 0: loses the sourced question or creates additional unsourced Decision Items/open questions.

## 8. Traceability and readiness — 5 points
- 5: source -> requirement -> backlog/decision -> AC/status is coherent; confirmed, disputed, unknown and target states remain distinct.
- 0: material traceability/status loss.

## Automatic fail conditions

Any one of the following makes the run FAIL regardless of numeric score:
- invents a multi-region set-handling outcome as confirmed behaviour or acceptance criteria;
- creates implementation-mechanism requirements/Decision Items around gate entry or crew exit detection/transport/integration;
- treats explicit business-label-to-field mappings as a contradiction;
- ignores the spreadsheet operational controls materially;
- silently resolves the evidence-upload contradiction;
- invents generic governance/decision owners, NFRs, API/UI/error/retry/audit requirements not sourced.

## Model comparison decision

For a controlled 3.7 vs 3.8 pair using identical input, prompt and Skill hash:
- both candidates must individually score >=90 and have no automatic fail to be eligible for promotion;
- prefer 3.8 if it scores at least 3 points higher;
- if scores are within 2 points, prefer the model with materially better source closure, structured-source use and status preservation;
- if either evaluator identifies an automatic fail on the preferred candidate, do not promote from this benchmark.