# MSA-001 — Manuscript Structure Evidence Hardening

## Objective

Prevent `analyze-manuscript-structure` from turning unresolved clues into unsupported motive, guilt, deception, fabrication, foreknowledge, complicity or premeditation while preserving its reconstruction-only role.

## Triggering evidence

The MIG-001 runtime fixture preserved the major unresolved identities and causal questions, but the output still used interpretive phrases including `foreknowledge`, `misdirection / fabrication`, and `premeditation or thwarted expectations`. The phrase `premeditation` is not established by the manuscript and is too strong for a reconstruction-only factual map.

## Change

Version 0.1.1 adds explicit evidence-discipline rules:

- ambiguity alone cannot support guilt, deception, fabrication, complicity, foreknowledge, premeditation, intent or motive;
- charged labels such as `fabrication`, `premeditation`, `cover-up`, `alibi` and `deception` require explicit textual support or clear attribution to a character's belief;
- divergences must be described before explanations are proposed;
- the final editorial-brief seed must not convert unresolved clues into motive or hidden intent.

## Acceptance criteria

1. The skill remains reconstruction-only and introduces no new tool permissions or invocation behavior.
2. Re-running the MIG-001 fixture keeps `M.`, the coat wearer, the ferry passenger, the torn fabric and Mara's final line unresolved unless the text explicitly resolves them.
3. The output does not state or imply that Mara is guilty, deceptive, fabricating, complicit, acting with foreknowledge, or acting with premeditation.
4. The output does not use charged labels such as `fabrication`, `premeditation`, `cover-up`, `alibi` or `deception` as its own characterization unless directly supported by explicit text.
5. Differences between testimony, timestamps and physical evidence are described as discrepancies, conflicts or unresolved divergences rather than proof that a witness lied.
6. The output gives no prose rewrite, developmental-edit recommendation or invented authorial intent.
7. GitHub Skill Sync on `server/synology` succeeds after promotion with zero skipped skill/file errors attributable to this change.

## Promotion rule

Do not merge the semantic hardening change until a fresh runtime invocation of the MIG-001 fixture satisfies criteria 2–6. MIG-001 remains valid as evidence that the GitHub migration/cutover mechanism worked; MSA-001 is the quality gate for the manuscript skill itself.
