# MSA-001 — Manuscript Structure Evidence Hardening

## Objective

Prevent `analyze-manuscript-structure` from turning unresolved clues into unsupported motive, guilt, deception, fabrication, foreknowledge, complicity or premeditation while preserving its reconstruction-only role.

## Triggering evidence

The MIG-001 runtime fixture preserved the major unresolved identities and causal questions, but the output still used interpretive phrases including `foreknowledge`, `misdirection / fabrication`, and `premeditation or thwarted expectations`. The phrase `premeditation` is not established by the manuscript and is too strong for a reconstruction-only factual map.

A first v0.1.1 runtime rerun improved the evidence discipline substantially, but still introduced unsupported possibilities such as `an accomplice` for Mara's final line and `red herring` for the harbour fabric. It also promoted some details beyond the text, such as treating presence at the cottage as possible residence and `Leon's car` as evidence he drove it. These are small but important canon-contamination risks for a reconstruction skill.

A second v0.1.2 runtime rerun fixed those charged labels and preserved the major unknowns, but still introduced unsupported mechanisms and authorial/candidate framing in the final synthesis. Examples included asking whether the clock was `intentionally manipulated`, whether sightings were `intended` to be Leon or another known/unintroduced person, and whether the scarf/fabric were `intended` to be the same item. The output also described the clock as `stopped or offset` inside a confirmed chronology even though the manuscript only establishes the displayed time, and one continuity note misplaced the ferry receipt as harbour evidence even though the receipt was found in the car on the north road.

## Change

Current hardening through version 0.1.15 strengthens the evidence-discipline rules further:

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


### Attempt 5 — v0.1.5 — FAIL

This controlled rerun again passed criteria 2–5, but strict criterion 6 still failed on residual overreach:

- it stated that the 6:32 receipt was printed before the passenger boarded the `6:40 ferry`, even though the manuscript never states the boarding time;
- it expanded `deckhand` into `harbourside worker / crew member` and treated `6:40 ferry` as a `labelled/scheduled time`, adding specificity not present in the text;
- it continued to introduce secondary unknowns such as Mara's residence status and Mrs Pell's vantage point/distance that are conceivable but not created by the manuscript.

The benchmark remains failed. Version 0.1.6 now requires uncertain time-bearing facts to be stated separately without self-generated ordering, preserves exact role/place nouns, and prefers omission/`Unstated` over speculative completeness.


### Attempt 6 — v0.1.6 — FAIL

This controlled rerun improved chronology handling substantially and kept the central ambiguity constraints intact, but strict criterion 6 still failed on residual classification and wording drift:

- direct character statements were inconsistently reclassified as `Strong inference` or `Possible interpretation` instead of remaining `Character statement`;
- Mara's ambiguous `you` was promoted to an `individual`;
- Vale's notebook question was summarized as Vale `suspects` prior knowledge, which strengthens a question into a belief state;
- the output introduced source-expanding labels such as `their cottage`, `land route`, and `maritime route`.

The benchmark remains failed. Version 0.1.7 now explicitly preserves character-statement classification, modality, ambiguous referent class, exact ownership/residence wording, and source-level spatial labels.


### Attempt 7 — v0.1.7 — FAIL

This controlled rerun was the strongest result so far. It preserved the central ambiguities, used `Character statement` correctly, avoided unsupported chronology, and kept Vale's notebook entry as a question. It still failed strict criterion 6 on narrow provenance and summary-scope drift:

- the ending summary said Vale had collected physical findings at the cottage, north road, and harbour, although the cottage observations were Mara's rather than Vale's;
- the living brief said the harbour was where a ferry receipt `points`, which adds a spatial linkage not established by the manuscript and weakens exact evidence provenance;
- `Mara reports Leon missing` strengthened the text's actual action (phoning Vale and reporting Leon's stated departure/absence) into an explicit missing-person report;
- `deckhand at the harbour` appended a role/location relation beyond the source noun.

The benchmark remains failed. Version 0.1.8 tightens observer/finder attribution, report/action scope, exact role/location wording, and prohibits `points to` spatial summaries for service-related documents.


### Attempt 8 — v0.1.8 — FAIL

This controlled rerun preserved the core ambiguity, chronology, character-statement classification, and exact role/place wording much better, but strict criterion 6 still failed on three narrow provenance/modality issues:

- the ending-state summary said Vale had collected witness statements and physical findings at the cottage, north road, and harbour, collapsing Mara's cottage observations into Vale's evidence collection;
- the evidence register rewrote Vale's notebook question as the declarative claim `"M." knew about the harbour before Vale mentioned it`, even though the strength was marked `Unknown / unresolved`;
- the living brief listed `A passenger in a dark coat boarded the 6:40 ferry` as an unqualified major reveal, dropping attribution to the deckhand's recollection.

The benchmark remains failed. Version 0.1.9 now explicitly preserves mixed provenance in aggregate summaries, requires question modality to survive into table claim labels, and requires witness/character attribution to be retained in summaries and major reveals.


### Attempt 9 — v0.1.9 — FAIL

This controlled rerun fixed the prior notebook-modality and witness-attribution issues and was otherwise clean against criteria 2–5. It still failed strict criterion 6 on one explicit aggregate-provenance error:

- the current-ending-state summary said Vale had `gathered witness statements and found physical items across the cottage, north road, and harbour`, collapsing Mara's cottage observations into Vale's evidence collection.

The benchmark remains failed rather than accepting a known violation of the skill's mixed-provenance rule. Version 0.1.10 adds an explicit summary-section audit for this exact failure mode without broadening the benchmark.


### Attempt 10 — v0.1.10 — FAIL

This controlled rerun fixed the prior aggregate-provenance issue in the current-ending-state summary and remained clean on the main ambiguity, chronology, modality, and evidence-attribution requirements. It still failed strict criterion 6 on two residual table-completion inferences:

- Mara's character-map unknowns included `what she knew about the harbour`, propagating the unresolved `M.` clue onto Mara even though the manuscript does not establish that `M.` is Mara;
- the character/relationship map stated that the deckhand `spoke with Vale at the harbour`, inferring an interaction/location relation that the manuscript does not explicitly establish.

These failures indicate a structural tendency to invent connective tissue when completing table cells rather than a need for more isolated phrase bans. Version 0.1.11 therefore adds a source-preserving output contract: narrator facts stay narrator facts, statements/recollections stay attributed, questions preserve modality, unknowns do not propagate to candidate characters, interactions are not inferred from adjacency, and neutral/empty cells are explicitly allowed.


### Attempt 11 — v0.1.11 — FAIL

This controlled rerun fixed the prior propagated-`M.` unknown in Mara's row and preserved the main chronology, provenance, modality, and witness-attribution requirements. It still failed strict criterion 6 because the output continued to infer recipients/interactions that the manuscript does not explicitly state:

- the character map said the deckhand `spoke to Vale`;
- the chronology said the deckhand `speaks to Vale`;
- the evidence register described the deckhand's memory as a recollection `to Vale`;
- Chapter 2 / relationship wording also treated Mara's statement about Leon hating boats as a statement `to Vale`, although the manuscript only says Mara says it.

Version 0.1.12 tightens the source-preserving contract around recipient attribution: a statement/recollection may only be assigned a recipient when the source explicitly names that recipient. Otherwise the relationship cell must remain neutral (for example, `None established`).


### Attempt 12 — v0.1.12 — FAIL

This controlled rerun fixed the prior inferred-recipient relationships: the deckhand relationship cell remained neutral, Mara's Chapter 2 statement no longer acquired Vale as an unstated recipient, and the main chronology/provenance/modality controls held. One residual criterion-6 action promotion remained:

- the Chapter 3 material-events cell said `A deckhand reports a memory`, converting the manuscript's narrator-established `A deckhand remembers...` into an unsupported communication act.

Everything else in the promotion-critical behavior was clean. Version 0.1.13 therefore tightens the source-preserving contract at the predicate level: attributed evidence must preserve not only the source but also the action type (`remembers`, `says`, `tells X`, `writes`, etc.) unless the manuscript explicitly establishes a different communication act.


### Attempt 13 — v0.1.13 — FAIL

This controlled rerun fixed the prior recipient and relationship inferences and preserved the main ambiguity, chronology, provenance, modality, and evidence-classification requirements. Two residual predicate-fidelity violations remained outside the core evidence tables:

- the living editorial-brief premise said `a boarding is reported`, converting the deckhand's `remembers` into a reporting act;
- the motifs section referred to `the deckhand's mention` of a passenger, again converting memory/recollection into a communication act.

Everything else in the promotion-critical behavior was clean. Version 0.1.14 therefore applies predicate fidelity across every output section, including motifs/themes and living briefs, and explicitly prohibits converting `remembers` into `reports`, `mentions`, or passive reporting language.


### Attempt 14 — v0.1.14 — FAIL

This controlled rerun preserved the main ambiguity, chronology, provenance, modality, evidence classification, recipient attribution, and deckhand relationship controls. Two residual source-contract issues remained:

- the Chapter 1 character-state summary compressed Mara's two statements into `Leon left before six taking the north road`, which promotes Leon's reported statement about taking the north road into the route he actually took;
- the motifs section still used `Mrs Pell's mention` and `the deckhand's mention`, with the latter converting the manuscript's `remembers` predicate into a communication act.

Version 0.1.15 therefore preserves nested attribution/clause boundaries explicitly and removes an internally inconsistent older instruction that still allowed a deckhand recollection to be phrased as `reports/recalls`.

## Promotion rule

Do not merge the semantic hardening change until a fresh runtime invocation of the MIG-001 fixture satisfies criteria 2–6. MIG-001 remains valid as evidence that the GitHub migration/cutover mechanism worked; MSA-001 is the quality gate for the manuscript skill itself.
