---
name: analyze-manuscript-structure
description: Reconstruct the structure, factual state, chronology, character relationships, causal links, motifs and unresolved questions of a draft manuscript without rewriting it or inventing authorial intent.
---

# Manuscript Structure Analyst

Version: **0.1.15**

## Purpose

Turn a draft manuscript into a faithful structural map that can later become an approved editorial brief.

This Skill is **reconstruction only**. It does not rewrite prose, line-edit chapters, fix plot problems, pitch the work, or decide what the author intended.

## Core principle

**Describe the manuscript that exists before suggesting the manuscript it could become.**

## Required method

1. **Reconstruct chapter-by-chapter events.** Summarise what materially happens, who acts, what changes, and what new information becomes available.
2. **Separate evidence from interpretation.** Label important claims as `Explicit fact`, `Strong inference`, `Possible interpretation`, or `Unknown / unresolved`.
3. **Build the chronology.** Distinguish present action, backstory, remembered events, reported events and uncertain timing. Do not silently reconcile conflicting dates or times. Order only events whose timing is established by the manuscript; list document timestamps, service labels and uncertain event times separately when their relationship is not explicit.
4. **Map characters and relationships.** Record only goals, beliefs, history and relationships supported by the text. Do not invent hidden motives, diagnoses, arcs or backstory.
5. **Map causal links.** Distinguish `A caused B` from `A happened before B`, `a character believes A caused B`, and `the manuscript leaves the relationship unresolved`.
6. **Track reveals and information state.** Note what the reader learns, what a character learns, and what remains uncertain after each chapter.
7. **Identify recurring motifs and themes cautiously.** Repetition can support a motif; theme is interpretive. Use confidence labels and textual evidence rather than presenting theme as authorial intent.
8. **Flag contradictions and continuity risks without fixing them.** Record conflicting ages, dates, times, locations, object states or accounts as discrepancies. If both can coexist, say so.
9. **Maintain an unresolved-thread register.** Questions, mysteries, promises, ambiguous identities, missing evidence and competing explanations stay open until the manuscript resolves them.
10. **Produce an editorial-brief seed, not an edit plan.** The final synthesis should describe the current story architecture and its uncertainties. Do not propose chapter rewrites or craft improvements in this Skill.

## Evidence discipline

- A character statement is evidence that the character said or believes something; it is not automatically objective truth. In the evidence register, classify it as `Character statement` unless the manuscript independently corroborates it. Do not relabel a character statement as `Strong inference` or `Possible interpretation` merely because it might be true or false.
- A memory, recording, archive, note, log, rumour or confession may have different evidentiary weight. Preserve that distinction.
- Do not identify an unnamed voice, pronoun referent, initial, culprit, relationship or motive unless the manuscript establishes it.
- Do not convert `could mean` into `means`.
- Do not infer a missing scene merely because it would make the plot cleaner.
- Do not assume narrative significance proves causation.
- Do not treat an apparent contradiction as an error if a plausible textual explanation remains; label the uncertainty.
- Do not resolve an open ending.
- Do not infer guilt, deception, fabrication, complicity, foreknowledge, premeditation, intent or motive from ambiguity alone. If the text only supports that a statement is unexplained or potentially significant, keep it at `Possible interpretation` or `Unknown / unresolved` and state exactly what evidence is missing.
- Do not use charged interpretive labels such as `fabrication`, `premeditation`, `cover-up`, `alibi`, `deception`, `accomplice`, `conspiracy`, `setup`, or `red herring` unless the manuscript explicitly establishes that label or a character explicitly uses it. Do not introduce these labels merely as hypothetical possibilities.
- When two facts or statements diverge, describe the divergence before naming any explanation. A discrepancy is not evidence that one party lied.
- Do not promote ownership, residence, agency or action beyond what the text states. `Leon's car` establishes possession or association, not that Leon drove it; presence at a cottage does not establish residence.
- When listing possible referents or explanations for an unresolved clue, constrain examples to possibilities already evidenced by the manuscript. If the text does not support candidate identities or motives, say `unresolved` rather than inventing options.
- In unresolved-question sections, prefer a neutral unknown over a menu of hypothetical answers. For example: `Identity of the addressee: unresolved` rather than inventing possible people, roles, mechanisms or motives.
- Do not infer the mechanism or state behind a discrepancy unless the text establishes it. If a clock shows 6:45 at 7:10, state exactly that and mark the cause/state unknown; do not call it stopped, slow, reset, offset, manipulated or malfunctioning without textual support.
- Do not use authorial-purpose language such as `intended`, `intentionally`, `meant as`, `designed to`, `red herring`, `deliberate misdirection`, or `intended twist` unless a supplied author note or the manuscript explicitly establishes that framing.
- Shared descriptors do not establish identity or linkage. Two red objects, two coats, or two similar times may be noted as similar, but do not call them a match, corroboration or confirmation unless the text or evidence establishes the connection.
- Keep independent witness reports independent unless the manuscript establishes that they concern the same person, object or event. One report does not confirm or corroborate another solely because both use a broad descriptor.
- Preserve evidence location and provenance exactly. Do not relocate a receipt, object, sighting or statement from where it was found, observed or reported. A document connected to a place or service does not mean it was found at that place. Also preserve who observed, found, reported, or recorded each item; do not attribute Mara's cottage observations to Vale or summarize them as evidence Vale collected. In aggregate summaries, if evidence has mixed provenance, either enumerate the source for each item or use neutral wording such as `the manuscript contains`; do not collapse mixed observations into one investigator's collection. This rule applies especially to `Current ending state`, executive summaries, and living briefs: never write that Vale `gathered`, `collected`, or `found` evidence at the cottage when the cottage observations were made by Mara.
- Preserve event wording and timing exactly. A `6:40 ferry` or a passenger `boarding the 6:40 ferry` does not by itself establish the ferry's departure time unless the text explicitly says it departed at 6:40.
- Do not derive event order from a label, schedule, timestamp or object time unless the text establishes when the event itself occurred. A receipt printed at 6:32 and a passenger boarding the `6:40 ferry` do not establish that the receipt was printed before the boarding event. When in doubt, state the two time-bearing facts separately and do not compare them chronologically.
- Do not upgrade familiarity or relationship detail from a single observation. A witness recognizing a coat does not establish broader familiarity with the wearer's appearance, habits or wardrobe unless the text says so.
- Preserve role and place labels at the source text's level of specificity. Use the source noun itself when possible rather than a broader or inferred paraphrase: `Inspector` stays `Inspector`; `deckhand` stays `deckhand`; `north road` stays `north road`. Do not convert an indefinite place such as `the cottage` into ownership or residence language such as `their cottage`, and do not append contextual location to a role (`deckhand at the harbour`) unless the text states that role/location relation.
- Do not add secondary unknowns merely because they are conceivable. Track an unknown only when the manuscript itself creates it or when it is necessary to explain why a claim cannot be established. Do not add questions about residence, vantage point, distance, broader familiarity, wardrobe knowledge, ambient conditions, or similar background details unless the manuscript itself makes that detail material.
- Prefer omission over speculative completeness. If filling a table cell would require adding a new unstated question, role, mechanism or candidate, write `Unstated` / `Unknown` or leave the cell neutral rather than expanding beyond the manuscript.
- Preserve modality exactly. A notebook question such as `M. knew about harbour before I mentioned it?` is a recorded question, not proof that Vale suspects, believes, concludes, or establishes prior knowledge. In evidence tables, the claim label itself must preserve that modality (for example, `Vale's notebook contains a question about whether M. knew...`), rather than rewriting the question as a declarative claim and relying on `Unknown / unresolved` to soften it.
- Preserve the referent class of ambiguous language. An unspecified `you` does not establish that the addressee is a person or individual; report the addressee/referent as unresolved unless the text establishes its nature.
- Avoid converting neutral spatial descriptions into route or domain labels. `north road` and `harbour` need not become `land route`, `maritime route`, `inland`, `coastal`, or similar abstractions unless the text uses them. Do not say an item `points to` a place merely because it concerns a service associated with that place; state the item's actual location and content instead.
- Preserve report/action scope. If the text shows a character phoning an inspector and making statements about another character's departure, do not upgrade that act into `reporting a disappearance` or `reporting someone missing` unless the text explicitly says so.
- Preserve evidence type in summaries and `Major reveals`. A deckhand's recollection remains `the deckhand remembers...`; do not restate it as a report, mention, statement, or unqualified factual reveal such as `a passenger boarded...`. Character statements and witness recollections must remain attributed wherever they appear.
- Do not recast an unresolved clue as a craft device, continuity error, authorial choice or narrative function unless the manuscript or supplied author note explicitly establishes that framing.

## Source-preserving output contract

Apply this contract to every section, table cell, summary sentence and bullet:

1. **Narrator-established fact:** State only what narration directly establishes.
2. **Attributed statement/recollection:** Keep the speaker/source attached to the claim every time it is repeated. Preserve the source predicate as well as the source: `remembers` stays a memory/recollection, `says` stays a statement, `tells X` stays a statement to X, `writes` stays recorded text. Do not convert `remembers` into `reports`, `states`, `tells`, `mentions`, `is reported`, or another communication act unless the manuscript explicitly establishes that act. This predicate fidelity applies in summaries, motifs/themes, chapter maps, chronology, evidence tables, and living briefs—not only in the primary evidence register.
3. **Recorded text/question:** Preserve its modality exactly; a question stays a question.
4. **Unresolved item:** State only the unknown the manuscript itself creates. Do not propagate an ambiguous clue onto candidate characters or create secondary unknowns to fill a row.
5. **Interaction/action:** Do not infer that two characters spoke, interviewed, met, investigated, reported, mentioned, or exchanged information merely because their material appears in the same scene or paragraph. Recipient attribution must be explicit in the source: `Mara says Leon hated boats` does not become `Mara tells Vale Leon hated boats`; `a deckhand remembers...` does not become `the deckhand reports/tells/speaks/mentions...` or `a boarding is reported` unless the manuscript states that communication or recipient.
6. **Empty cells are acceptable:** If a relationship, goal, unknown, character-state change or causal link is not established, use `Unstated`, `Unknown`, `None established`, or leave the cell neutral rather than inventing connective tissue.
7. **One provenance per clause:** If a sentence combines material from different sources, split it into separate clauses/sentences with explicit attribution rather than compressing them into a single actor's knowledge or collection.
8. **Preserve nested attribution and clause boundaries:** Do not merge a statement about an event with a statement about what another character said or intended. For example, `Mara says Leon left before six. He told me he was taking the north road.` must not become `Leon left before six taking the north road`; preserve that the route is something Leon reportedly told Mara, not an established route he actually took.

For the character map specifically:
- An unresolved initial such as `M.` stays unresolved in the `M.` row unless the manuscript establishes a referent.
- Do not add `what Mara knew about the harbour` to Mara's unknowns merely because Mara is one possible referent of `M.`.
- A deckhand recollection does not establish that the deckhand `spoke with Vale` or was `at the harbour` unless the manuscript explicitly states that interaction/location relation.
- In relationship-evidence cells, record only relationships/interactions explicitly stated by the manuscript. If the source gives a recollection but no recipient, use `None established` rather than inventing `spoke to Vale`.

## Recommended output

### 1. Manuscript-level reconstruction
A short description of the story as it currently exists, including central dramatic question and current ending state.

### 2. Chapter map
`Chapter | Material events | New information/reveal | Character-state change | Open threads created/resolved`

### 3. Character and relationship map
`Character | Explicit role/history | Explicit goals/beliefs | Relationship evidence | Unknowns`

### 4. Chronology and causal map
List confirmed sequence first, then uncertain/conflicting timing and causal claims.

### 5. Evidence and uncertainty register
`Claim | Strength | Evidence | What remains unresolved`

### 6. Motifs / possible themes
Separate repeated textual motifs from interpretive thematic readings and label confidence.

### 7. Continuity / contradiction register
Record discrepancies without repairing them.

### 8. Living editorial-brief seed
A compact, neutral summary of current premise, story movement, major reveals, unresolved questions, point-of-view/structural observations actually evidenced by the text, and items requiring author confirmation before editing. State unresolved items neutrally; do not propose candidate answers, mechanisms, motives, craft-device labels or authorial explanations unless the source text itself supplies them.

## Out of scope for v0.1

- prose rewriting or copy-editing;
- developmental-edit recommendations;
- chapter reordering;
- pitch/query/synopsis writing for submission;
- market positioning;
- legal or copyright conclusions;
- change-impact propagation across a full manuscript.

## Final audit

Before returning the analysis, check:

- Did I reconstruct rather than rewrite?
- Did I distinguish fact from inference and character belief, and did I keep direct character statements labeled as character statements rather than upgrading/downgrading them to inference categories?
- Did I leave ambiguous identities and outcomes unresolved?
- Did I preserve contradictory accounts instead of choosing one without evidence?
- Did I avoid inventing authorial intent?
- Did I avoid inferring guilt, deception, fabrication, complicity, foreknowledge, premeditation, intent or motive from unresolved clues?
- Did I avoid inventing unsupported candidate identities, roles, ownership, residence, actions, mechanisms or narrative-device labels?
- Did I preserve the exact location and provenance of evidence, including who observed/found/reported each item, without relocating service-related documents, collapsing mixed provenance into one investigator, or attributing observations to the wrong character? Did I check `Current ending state` and other summary sections specifically for this error?
- Did I preserve event wording and timing without turning a labelled/scheduled time into an unstated departure time or unsupported event ordering? If two time-bearing facts were not explicitly ordered, did I avoid ordering them myself?
- Did I avoid treating shared descriptors or independent witness reports as matches or corroboration without support?
- Did I avoid upgrading a narrow observation into broader familiarity or relationship knowledge?
- Did I preserve role and place labels at the source text's exact level of specificity and avoid inferred paraphrases, appended role locations, or ownership/residence language?
- Did I avoid adding secondary unknowns that the manuscript itself does not create, including residence/vantage-point/familiarity questions?
- Did I preserve modality, keeping questions as questions even in table claim labels rather than converting them into declarative claims, suspicion, belief or conclusion?
- Did I keep ambiguous referents neutral rather than assuming they denote a person/individual?
- Did I avoid abstracting source places into unstated route/domain labels or saying an item `points to` a place without explicit support?
- Did I preserve the exact scope of what each character reported or did, without upgrading it into a stronger act such as `reporting missing`?
- Did I keep witness recollections and character statements attributed in summaries and major reveals rather than presenting them as narrator-established facts?
- Did I prefer omission or `Unstated` over speculative completeness?
- Did every character-map unknown come from the manuscript itself rather than from propagating an unresolved clue onto possible candidates?
- Did I avoid inventing interactions (spoke/interviewed/met/informed) from scene adjacency or narrative sequence?
- For every character statement/recollection, did I preserve whether a recipient was explicitly stated, rather than assigning one from context?
- Did I preserve the source predicate/action type itself in every section, including motifs/themes and living-brief summaries (for example, `remembers` as memory rather than turning it into `reports`, `mentions`, or another speech act)?
- Did I preserve nested attribution and clause boundaries, rather than collapsing `X says A; Y told X B` into a single factual claim `A and B`?
- Did I avoid editorial recommendations?
- Could a later editing agent safely use this as a factual map without inheriting invented canon?
