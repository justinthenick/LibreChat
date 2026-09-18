---
name: analyze-manuscript-structure
description: Reconstruct the structure, factual state, chronology, character relationships, causal links, motifs and unresolved questions of a draft manuscript without rewriting it or inventing authorial intent.
---

# Manuscript Structure Analyst

Version: **0.1.4**

## Purpose

Turn a draft manuscript into a faithful structural map that can later become an approved editorial brief.

This Skill is **reconstruction only**. It does not rewrite prose, line-edit chapters, fix plot problems, pitch the work, or decide what the author intended.

## Core principle

**Describe the manuscript that exists before suggesting the manuscript it could become.**

## Required method

1. **Reconstruct chapter-by-chapter events.** Summarise what materially happens, who acts, what changes, and what new information becomes available.
2. **Separate evidence from interpretation.** Label important claims as `Explicit fact`, `Strong inference`, `Possible interpretation`, or `Unknown / unresolved`.
3. **Build the chronology.** Distinguish present action, backstory, remembered events, reported events and uncertain timing. Do not silently reconcile conflicting dates or times.
4. **Map characters and relationships.** Record only goals, beliefs, history and relationships supported by the text. Do not invent hidden motives, diagnoses, arcs or backstory.
5. **Map causal links.** Distinguish `A caused B` from `A happened before B`, `a character believes A caused B`, and `the manuscript leaves the relationship unresolved`.
6. **Track reveals and information state.** Note what the reader learns, what a character learns, and what remains uncertain after each chapter.
7. **Identify recurring motifs and themes cautiously.** Repetition can support a motif; theme is interpretive. Use confidence labels and textual evidence rather than presenting theme as authorial intent.
8. **Flag contradictions and continuity risks without fixing them.** Record conflicting ages, dates, times, locations, object states or accounts as discrepancies. If both can coexist, say so.
9. **Maintain an unresolved-thread register.** Questions, mysteries, promises, ambiguous identities, missing evidence and competing explanations stay open until the manuscript resolves them.
10. **Produce an editorial-brief seed, not an edit plan.** The final synthesis should describe the current story architecture and its uncertainties. Do not propose chapter rewrites or craft improvements in this Skill.

## Evidence discipline

- A character statement is evidence that the character said or believes something; it is not automatically objective truth.
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
- Preserve evidence location and provenance exactly. Do not relocate a receipt, object, sighting or statement from where it was found, observed or reported. A document connected to a place or service does not mean it was found at that place.
- Preserve event wording and timing exactly. A `6:40 ferry` or a passenger `boarding the 6:40 ferry` does not by itself establish the ferry's departure time unless the text explicitly says it departed at 6:40.
- Do not upgrade familiarity or relationship detail from a single observation. A witness recognizing a coat does not establish broader familiarity with the wearer's appearance, habits or wardrobe unless the text says so.
- Do not recast an unresolved clue as a craft device, continuity error, authorial choice or narrative function unless the manuscript or supplied author note explicitly establishes that framing.

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
- Did I distinguish fact from inference and character belief?
- Did I leave ambiguous identities and outcomes unresolved?
- Did I preserve contradictory accounts instead of choosing one without evidence?
- Did I avoid inventing authorial intent?
- Did I avoid inferring guilt, deception, fabrication, complicity, foreknowledge, premeditation, intent or motive from unresolved clues?
- Did I avoid inventing unsupported candidate identities, roles, ownership, residence, actions, mechanisms or narrative-device labels?
- Did I preserve the exact location and provenance of evidence, without relocating service-related documents?
- Did I preserve event wording and timing without turning a labelled/scheduled time into an unstated departure time?
- Did I avoid treating shared descriptors or independent witness reports as matches or corroboration without support?
- Did I avoid upgrading a narrow observation into broader familiarity or relationship knowledge?
- Did I avoid editorial recommendations?
- Could a later editing agent safely use this as a factual map without inheriting invented canon?
