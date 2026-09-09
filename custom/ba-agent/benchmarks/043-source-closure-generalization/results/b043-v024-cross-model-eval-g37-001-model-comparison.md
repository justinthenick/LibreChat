# Cross-Model Semantic Evaluation

- Job: `b043-v024-cross-model-eval-g37-001`
- Evaluator: `gemini-3.7-flash`
- Left: `gemini-3.7-flash` — **100/100**
- Right: `gemini-3.8-flash` — **100/100**
- Preferred model: `none`
- Decision rule met: `false`

## Rationale

Both models scored 100/100 with zero automatic fail violations. Both demonstrated perfect source closure, exact tabular data operationalisation, rigorous preservation of the evidence contradiction, correct handling of multi-region multiplicity as Unknown, and clean target-state abstraction preservation. Neither model holds a material advantage over the other.

## Left — gemini-3.7-flash

- **Multi-source utilisation:** 10/10 — Materially and accurately utilises all four sources (SRC-DOC-01, SRC-XLS-01, SRC-MAP-01, SRC-PPT-01) with full source attribution.
- **Structured operational controls:** 20/20 — Fully operationalises taxonomy/mappings (4/4), assignment_queue routing (4/4), Permit option available? (3/3), Remote Review available? (3/3), Evidence Required? (3/3), and Risk Band (3/3).
- **Multiplicity discipline:** 20/20 — Preserves multi-region contractor affiliation as an unknown handling outcome without promoting candidate set-handling policies into confirmed requirements or AC.
- **Target-state abstraction discipline:** 20/20 — Retains gate-entry and final-exit events at the target abstraction without introducing unsourced technical transport, polling, API, or reconciliation mechanisms.
- **Naming / field-mapping discipline:** 10/10 — Treats business taxonomy labels and technical u_ field names as direct mappings rather than conflicts or decision items.
- **Explicit contradiction preservation:** 10/10 — Preserves the document-wide evidence upload mandate vs. matrix-level flag contradiction as Disputed, correctly blocking confirmed AC elaboration.
- **Unresolved-cardinality / source closure:** 5/5 — Captures the exact out-of-hours duty supervisor self-approval TBD question from SRC-MAP-01 and introduces zero negative-space/invented questions.
- **Traceability and readiness:** 5/5 — End-to-end traceability across sources, requirements, backlog/decision items, and acceptance criteria is clean, complete, and status-disciplined.

Flawless execution meeting all gold-standard criteria, with strict source closure, excellent operationalisation of tabular data, and precise status preservation.

## Right — gemini-3.8-flash

- **Multi-source utilisation:** 10/10 — Materially and accurately utilises all four sources with precise evidentiary role preservation.
- **Structured operational controls:** 20/20 — Fully operationalises all matrix controls: taxonomy + mappings (4/4), routing queue (4/4), permit option availability (3/3), remote review availability (3/3), evidence required flag (3/3), and risk band (3/3).
- **Multiplicity discipline:** 20/20 — Preserves multi-region handling outcome as Unknown/Candidate without promoting any candidate set policy to confirmed requirements or AC.
- **Target-state abstraction discipline:** 20/20 — Maintains gate-entry and crew-exit target items at stated concept abstraction without technical mechanism assumptions.
- **Naming / field-mapping discipline:** 10/10 — Correctly treats business hierarchy and u_ technical fields as explicit mappings.
- **Explicit contradiction preservation:** 10/10 — Identifies the evidence requirement contradiction between SRC-DOC-01 and SRC-XLS-01, labels it Disputed, and isolates it from confirmed AC.
- **Unresolved-cardinality / source closure:** 5/5 — Strictly isolates the single out-of-hours annotation and sourced ambiguities without adding ungrounded engineering questions.
- **Traceability and readiness:** 5/5 — Exemplary traceability and readiness distinction across confirmed, disputed, unknown, and target items.

Flawless execution meeting all gold-standard criteria, with exact matrix decomposition into discrete Gherkin scenarios and rigorous status boundaries.
