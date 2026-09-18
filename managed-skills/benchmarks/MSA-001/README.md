# MSA-001 — Manuscript Structure Evidence Hardening

## Objective

Prevent `analyze-manuscript-structure` from turning unresolved clues into unsupported motive, guilt, deception, fabrication, foreknowledge, complicity or premeditation while preserving its reconstruction-only role.

## Triggering evidence

The MIG-001 runtime fixture preserved the major unresolved identities and causal questions, but the output still used interpretive phrases including `foreknowledge`, `misdirection / fabrication`, and `premeditation or thwarted expectations`. The phrase `premeditation` is not established by the manuscript and is too strong for a reconstruction-only factual map.

A first v0.1.1 runtime rerun improved the evidence discipline substantially, but still introduced unsupported possibilities such as `an accomplice` for Mara's final line and `red herring` for the harbour fabric. It also promoted some details beyond the text, such as treating presence at the cottage as possible residence and `Leon's car` as evidence he drove it. These are small but important canon-contamination risks for a reconstruction skill.

A second v0.1.2 runtime rerun fixed those charged labels and preserved the major unknowns, but still introduced unsupported mechanisms and authorial/candidate framing in the final synthesis. Examples included asking whether the clock was `intentionally manipulated`, whether sightings were `intended` to be Leon or another known/unintroduced person, and whether the scarf/fabric were `intended` to be the same item. The output also described the clock as `stopped or offset` inside a confirmed chronology even though the manuscript only establishes the displayed time, and one continuity note misplaced the ferry receipt as harbour evidence even though the receipt was found in the car on the north road.

## Change

Current hardening through version 0.1.5 strengthens the evidence-discipline rules further:

- ambiguity alone cannot support guilt, deception, fabrication, complicity, foreknowledge, premeditation, intent or motive;
- charged labels such as `fabrication`, `premeditation`, `cover-up`, `alibi`, `deception`, `accomplice`, `conspiracy`, `setup`, and `red herring` require explicit textual support and must not be introduced merely as hypothetical possibilities;
- divergences must be described before explanations are proposed;
- ownership, residence, agency and action must not be promoted beyond what the text establishes;
- unresolved questions should state the unknown directly rather than invent menus of candidate identities, causes, mechanisms or motives;
- the mechanism/state behind a discrepancy must remain unknown unless the text establishes it;
- authorial-purpose language such as `intended`, `intentionally`, `meant as`, `designed to`, `deliberate misdirection` and `intended twist` is prohibited without explicit authorial evidence;
- shared descriptors do not establish a match or identity;
- independent witness reports must remain independent unless the text establishes they concern the same person/object/event;
- evidence location and provenance must be preserved exactly;
- unresolved clues must not be recast as craft devices, continuity errors, deliberate misdirection, authorial choices, red herrings or intended twists without explicit support;
- the final editorial-brief seed must state unresolved items neutrally and must not invent candidate answers or mechanisms.

## Acceptance criteria

1. The skill remains reconstruction-only and introduces no new tool permissions or invocation behavior.
2. Re-running the MIG-001 fixture keeps `M.`, the coat wearer, the ferry passenger, the torn fabric and Mara's final line unresolved unless the text explicitly resolves them.
3. The output does not state or imply that Mara is guilty, deceptive, fabricating, complicit, acting with foreknowledge, or acting with premeditation.
4. The output does not use charged labels such as `fabrication`, `premeditation`, `cover-up`, `alibi`, `deception`, `accomplice`, `conspiracy`, `setup`, or `red herring` as its own characterization unless directly supported by explicit text.
5. Differences between testimony, timestamps and physical evidence are described as discrepancies, conflicts or unresolved divergences rather than proof that a witness lied.
6. The output gives no prose rewrite, developmental-edit recommendation, invented authorial intent, invented craft-device framing, unsupported candidate identities/mechanisms, unsupported promotion of residence/ownership/agency/action, unsupported inference of an object's mechanism/state, or relocation/misstatement of evidence provenance.
7. GitHub Skill Sync on `server/synology` succeeds after promotion with zero skipped skill/file errors attributable to this change.

## Runtime attempts

### Attempt 1 — v0.1.1 — FAIL

The rerun satisfied the main ambiguity-preservation goals, but failed strict criteria 4 and 6 because it introduced unsupported phrases such as `an accomplice` and `red herring`, and promoted some details beyond the source text. The benchmark remains intentionally strict; the result was not reclassified as a pass.

### Attempt 2 — v0.1.2 — FAIL

The rerun passed the core ambiguity and non-accusatory requirements: `M.`, the coat wearer, ferry passenger, torn fabric and Mara's final line remained unresolved; the output did not accuse Mara of guilt, deception, fabrication, complicity, foreknowledge or premeditation; and discrepancies were not treated as proof of lying.

It still failed criterion 6 under the stricter reconstruction standard because it:

- introduced unsupported authorial/candidate framing such as whether items or sightings were `intended` to correspond;
- proposed unsupported mechanisms such as the clock being `intentionally manipulated`;
- introduced unsupported candidate classes such as `another known character` or `an unintroduced party`;
- described the clock as `stopped or offset` in a confirmed chronology despite the mechanism being unknown;
- misplaced the ferry receipt as harbour evidence in one continuity summary even though it was found in the car on the north road.

The benchmark remains failed rather than weakening the acceptance criteria.

### Attempt 3 — v0.1.3 — FAIL

This controlled rerun used Gemini 3.8 Flash in a fresh chat with the loaded skill version explicitly confirmed as v0.1.3. It passed the core ambiguity, non-accusatory, and neutral-unresolved requirements, but still failed strict criterion 6 because it introduced several unsupported factual upgrades:

- the manuscript-level reconstruction grouped the ferry receipt under the harbour even though the receipt was found in the car on the north road;
- it promoted `boarding the 6:40 ferry` into a confirmed `6:40 p.m. departure`;
- it upgraded Mrs Pell's narrow coat recognition into broader familiarity language such as Leon being known to her `by sight and clothing`;
- it continued to include some secondary unknowns (for example vantage point / broader wardrobe familiarity) that are not established as relevant by the manuscript.

The benchmark therefore remains failed rather than accepting small provenance/timing drift into the factual map. Version 0.1.4 adds explicit controls for service-document location, timetable/event wording, and narrow-vs-broad familiarity claims.


### Attempt 4 — v0.1.4 — FAIL

This controlled rerun was materially closer and passed criteria 2–5, but still failed strict criterion 6 on residual factual promotion:

- it stated that the 6:32 receipt was printed before the passenger boarded the `6:40 ferry`, even though the manuscript never states the boarding time;
- it still expanded source labels beyond the manuscript, including `police inspector`, `harbourside employee`, and `inland north road`;
- it added secondary unknowns such as Mrs Pell's vantage point/distance that are conceivable but not created by the manuscript.

The benchmark remains failed. Version 0.1.5 now explicitly prohibits deriving event order from labels/schedules/timestamps alone, expanding role/place labels beyond the source, and adding unnecessary secondary unknowns.

## Promotion rule

Do not merge the semantic hardening change until a fresh runtime invocation of the MIG-001 fixture satisfies criteria 2–6. MIG-001 remains valid as evidence that the GitHub migration/cutover mechanism worked; MSA-001 is the quality gate for the manuscript skill itself.
