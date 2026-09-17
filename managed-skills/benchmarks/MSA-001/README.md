# MSA-001 — Manuscript Structure Evidence Hardening

## Objective

Prevent `analyze-manuscript-structure` from turning unresolved clues into unsupported motive, guilt, deception, fabrication, foreknowledge, complicity or premeditation while preserving its reconstruction-only role.

## Triggering evidence

The MIG-001 runtime fixture preserved the major unresolved identities and causal questions, but the output still used interpretive phrases including `foreknowledge`, `misdirection / fabrication`, and `premeditation or thwarted expectations`. The phrase `premeditation` is not established by the manuscript and is too strong for a reconstruction-only factual map.

A first v0.1.1 runtime rerun improved the evidence discipline substantially, but still introduced unsupported possibilities such as `an accomplice` for Mara's final line and `red herring` for the harbour fabric. It also promoted some details beyond the text, such as treating presence at the cottage as possible residence and `Leon's car` as evidence he drove it. These are small but important canon-contamination risks for a reconstruction skill.

## Change

Version 0.1.2 strengthens the evidence-discipline rules:

- ambiguity alone cannot support guilt, deception, fabrication, complicity, foreknowledge, premeditation, intent or motive;
- charged labels such as `fabrication`, `premeditation`, `cover-up`, `alibi`, `deception`, `accomplice`, `conspiracy`, `setup`, and `red herring` require explicit textual support and must not be introduced merely as hypothetical possibilities;
- divergences must be described before explanations are proposed;
- ownership, residence, agency and action must not be promoted beyond what the text establishes;
- candidate identities and explanations must be constrained to possibilities already evidenced by the manuscript;
- unresolved clues must not be recast as craft devices, continuity errors, deliberate misdirection, authorial choices, red herrings or intended twists without explicit support;
- the final editorial-brief seed must not convert unresolved clues into motive or hidden intent.

## Acceptance criteria

1. The skill remains reconstruction-only and introduces no new tool permissions or invocation behavior.
2. Re-running the MIG-001 fixture keeps `M.`, the coat wearer, the ferry passenger, the torn fabric and Mara's final line unresolved unless the text explicitly resolves them.
3. The output does not state or imply that Mara is guilty, deceptive, fabricating, complicit, acting with foreknowledge, or acting with premeditation.
4. The output does not use charged labels such as `fabrication`, `premeditation`, `cover-up`, `alibi`, `deception`, `accomplice`, `conspiracy`, `setup`, or `red herring` as its own characterization unless directly supported by explicit text.
5. Differences between testimony, timestamps and physical evidence are described as discrepancies, conflicts or unresolved divergences rather than proof that a witness lied.
6. The output gives no prose rewrite, developmental-edit recommendation, invented authorial intent, invented craft-device framing, or unsupported promotion of residence/ownership/agency/action.
7. GitHub Skill Sync on `server/synology` succeeds after promotion with zero skipped skill/file errors attributable to this change.

## Runtime attempts

### Attempt 1 — v0.1.1 — FAIL

The rerun satisfied the main ambiguity-preservation goals, but failed strict criteria 4 and 6 because it introduced unsupported phrases such as `an accomplice` and `red herring`, and promoted some details beyond the source text. The benchmark remains intentionally strict; the result was not reclassified as a pass.

## Promotion rule

Do not merge the semantic hardening change until a fresh runtime invocation of the MIG-001 fixture satisfies criteria 2–6. MIG-001 remains valid as evidence that the GitHub migration/cutover mechanism worked; MSA-001 is the quality gate for the manuscript skill itself.
