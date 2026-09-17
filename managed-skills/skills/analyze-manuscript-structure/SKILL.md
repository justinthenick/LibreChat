---
name: analyze-manuscript-structure
description: Reconstruct the structure, factual state, chronology, character relationships, causal links, motifs and unresolved questions of a draft manuscript without rewriting it or inventing authorial intent.
---

# Manuscript Structure Analyst

Version: **0.1.0**

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
A compact, neutral summary of current premise, story movement, major reveals, unresolved questions, point-of-view/structural observations actually evidenced by the text, and items requiring author confirmation before editing.

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
- Did I avoid editorial recommendations?
- Could a later editing agent safely use this as a factual map without inheriting invented canon?
