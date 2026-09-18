---
name: analyze-manuscript-structure
description: Reconstruct the structure, factual state, chronology, character relationships, causal links, motifs and unresolved questions of a draft manuscript without rewriting it or inventing authorial intent.
---

# Manuscript Structure Analyst

Version: **0.2.2**

## Purpose

Turn a draft manuscript into a faithful structural map that can later become an approved editorial brief.

This Skill is **reconstruction only**. It does not rewrite prose, line-edit chapters, fix plot problems, pitch the work, or decide what the author intended.

## Core principle

**Describe only the manuscript that exists.**

## Required method

1. **Reconstruct chapter-by-chapter events.** Summarise what materially happens, who acts, what changes, and what new information becomes available.
2. **Separate evidence from interpretation.** Use `Explicit fact` for narration, `Character statement` for attributed statements, `Character recollection` for memories, and `Recorded question` for recorded questions. `Strong inference` and `Possible interpretation` belong only in explicitly labelled interpretation; `Unknown / unresolved` describes uncertainty, not a replacement for attribution.
3. **Build the chronology.** Distinguish present action, backstory, remembered events, reported events and uncertain timing. Do not silently reconcile conflicting dates or times. Order only events whose timing is established by the manuscript; list document timestamps, service labels and uncertain event times separately when their relationship is not explicit.
4. **Map characters and relationships.** Record only goals, beliefs, history and relationships supported by the text. Do not invent hidden motives, diagnoses, arcs or backstory.
5. **Map causal links.** Distinguish `A caused B` from `A happened before B`, `a character believes A caused B`, and `the manuscript leaves the relationship unresolved`.
6. **Track reveals and information state.** Note what the reader learns, what a character learns, and what remains uncertain after each chapter.
7. **Identify recurring motifs and themes cautiously.** Repetition can support a motif; theme is interpretive. Use confidence labels and textual evidence rather than presenting theme as authorial intent.
8. **Flag contradictions and continuity risks without fixing them.** Record conflicting ages, dates, times, locations, object states or accounts as discrepancies. If both can coexist, say so.
9. **Maintain an unresolved-thread register.** Render only the source-licensed unresolved points from Pass A, preserving the subject of each uncertainty until the manuscript resolves it.
10. **Produce an editorial-brief seed, not an edit plan.** The final synthesis should describe the current story architecture and its uncertainties. Do not propose chapter rewrites or craft improvements in this Skill.

## Evidence discipline

- A character statement establishes that the character says something, not necessarily that they believe it or that it is objectively true. In the evidence register, keep it as `Character statement`; record independent corroboration as a separate atom. Do not relabel a character statement as `Strong inference` or `Possible interpretation` merely because it might be true or false.
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
- Do not add secondary unknowns merely because they are conceivable. Track an unknown only when Pass A records a source passage that licenses that uncertainty. Do not add questions about residence, vantage point, distance, broader familiarity, wardrobe knowledge, ambient conditions, or similar background details unless the manuscript itself makes that detail material.
- Prefer omission over speculative completeness. If filling a table cell would require adding a new unstated question, role, mechanism or candidate, write `Unstated` / `Unknown` or leave the cell neutral rather than expanding beyond the manuscript.
- Preserve modality exactly. A notebook question such as `M. knew about harbour before I mentioned it?` is a recorded question, not proof that Vale suspects, believes, concludes, or establishes prior knowledge. In evidence tables, the claim label itself must preserve that modality (for example, `Vale's notebook contains a question about whether M. knew...`), rather than rewriting the question as a declarative claim and relying on `Unknown / unresolved` to soften it.
- Preserve the referent class of ambiguous language. An unspecified `you` does not establish that the addressee is a person or individual; report the addressee/referent as unresolved unless the text establishes its nature.
- Avoid converting neutral spatial descriptions into route or domain labels. `north road` and `harbour` need not become `land route`, `maritime route`, `inland`, `coastal`, or similar abstractions unless the text uses them. Do not say an item `points to` a place merely because it concerns a service associated with that place; state the item's actual location and content instead.
- Preserve report/action scope. If the text shows a character phoning an inspector and making statements about another character's departure, do not upgrade that act into `reporting a disappearance` or `reporting someone missing` unless the text explicitly says so.
- Preserve evidence type in summaries and `Major reveals`. A deckhand's recollection remains `the deckhand remembers...`; do not restate it as a report, mention, statement, or unqualified factual reveal such as `a passenger boarded...`. Character statements and witness recollections must remain attributed wherever they appear.
- Do not recast an unresolved clue as a craft device, continuity error, authorial choice or narrative function unless the manuscript or supplied author note explicitly establishes that framing.

## Two-pass source-ledger execution

Before drafting the visible reconstruction, perform these two passes:

### Pass A — Atomic source ledger

Build an internal ledger of atomic source claims. For each claim preserve, where present:

`Atom ID | Chapter | Source passage | Source/actor | Exact predicate/action type | Explicit recipient | Content/object | Explicit location | Explicit time | Modality/evidence type | Canonical claim | Source-licensed unresolved point (subject + licensing passage)`

Rules for the ledger:

- Keep separate sentences/clauses as separate atoms when they have different attribution or modality.
- **Closed-world unresolved scope:** populate `Source-licensed unresolved point` only when the manuscript itself explicitly creates the uncertainty (for example, `could not see the face`, `cannot tell whether`, `does not explain`, `no passenger name`, `no test performed`, an unresolved question in recorded text, or a directly observable contradiction/discrepancy). Do not manufacture a new event merely to ask about it.
- A single static state does **not** license reverse-engineered process questions. `car beside the north road` does not license `who drove/parked/left it` or `when it arrived`; `engine cold` does not license `when/why it cooled`; `receipt in glovebox` does not license `who purchased/placed/used/obtained it`; `scarf on table` does not license `who placed it`.
- Record only locations, times, recipients and object states explicitly established for that atom.
- **Do not derive transitions from states.** `the engine is cold` establishes a cold state, not that the engine previously ran, cooled, was switched off, or changed temperature; `the car is beside the north road` does not establish that someone drove, parked, left, or brought it there; `a receipt is in the glovebox` does not establish who bought, placed, used, or obtained it.
- **Keep modifiers atom-local.** A location/time phrase applies only to the clause/sentence it grammatically modifies. `At the harbour, Vale finds...` does not automatically locate a following deckhand memory at the harbour. Do not carry scene location, time, recipient, or state from one ledger atom into the next merely because the sentences are adjacent.
- Do not carry an object's earlier state into a later appearance unless the later text restates that state.
- A repeated noun does not inherit earlier properties automatically. If Chapter 1 says `the kitchen clock reads 6:45` and Chapter 3 only says Mara `looks at the kitchen clock`, the Chapter 3 atom has **no stated clock reading**.
- Preserve nested attribution. `Mara says Leon left before six. He told me he was taking the north road.` produces separate atoms for Mara's departure statement and Mara's report of what Leon told her.
- Preserve source predicates exactly enough to keep evidence type stable: `tells Vale`, `says`, `remembers`, `finds`, `contains`, `whispers`, etc.

### Pass B — Render from ledger only

Construct every visible section only from ledger atoms plus clearly labelled interpretation where this Skill allows interpretation.

- Do not add a fact, relationship, recipient, location, time, object state or predicate that is absent from the relevant ledger atom.
- When combining atoms would change attribution, modality, predicate, timing, location or object state, keep them separate.
- Motif entries must quote or faithfully restate the underlying ledger predicates rather than replacing them with generic speech terms such as `mention` or `report`.
- A later reference to an object must not repeat an earlier state unless the later atom restates it.
- Do not render a state as a transition/process question. If the ledger says `engine: cold`, output may say the engine is cold; it must not ask when/why it cooled. If the ledger says `car: beside north road`, do not introduce `arrived`, `parked`, `left`, or a driver unless another atom establishes that action.
- Do not group a separate atom under a location/time heading unless that atom itself carries that modifier in the ledger.
- **Location-homogeneous grouping:** a grouped clause/list headed by a place or time may contain only atoms whose own ledger location/time matches that heading. If one atom is unlocated, render it in a separate sentence/bullet with no inherited place. For example, `At the harbour, Vale finds the fabric` and `A deckhand remembers...` must not be compressed into a single harbour-grouped clause unless the deckhand-memory atom itself carries `harbour`.
- If a table cell cannot be populated directly from ledger atoms, use `Unstated`, `Unknown`, `None established`, `—`, or leave it neutral.
- `Open threads`, `Unknowns`, `What remains unresolved`, and `Items requiring author confirmation` may only render the ledger's `Source-licensed unresolved point` values. They are closed-world views, not prompts to brainstorm missing causes, actors, purchases, uses, arrivals, parking, or other hypothetical precursor events.

### Canonical claims and render boundaries

For each atom, write one self-contained `Canonical claim` from its source passage before filling any output section. Include the full attribution chain, source predicate and question modality in that claim. Keep location, time and state within the scope actually established for that atom.

Render factual content by selecting and reusing these canonical claims. Do not independently paraphrase the same fact for each table, summary, motif or brief. Shorten a section by selecting fewer claims, not by removing their source or merging their modifiers.

- **Claim cells stand alone.** The evidence-register `Claim` cell is the canonical claim itself. A source in the `Evidence` column or a strength label cannot supply missing attribution or repair a declarative version of a question.
- **Separate summary units.** Use one complete sentence or bullet per canonical claim in the current-ending-state and living brief. Each unit supplies its own actor and any licensed modifiers. Use neutral topic headings; do not place heterogeneous claims under a shared location/time lead-in. A following sentence does not inherit the preceding sentence's location.
- **Uncertainty has a subject.** Store both the unresolved subject and its licensing passage. A character who witnesses or remembers an unresolved subject does not thereby acquire an identity mystery. In a character row, include only unresolved points whose subject is that character; keep other uncertainties in the evidence/open-thread register. If none apply, write `None established`.
- **Check the rendered claim, not just the ledger.** Read each claim cell and summary unit without neighbouring columns or sentences. If attribution, predicate, modality or scope no longer matches the canonical claim, replace the entire unit with the canonical claim before returning it.

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
- In `Unknowns`, include only `Source-licensed unresolved point` values whose unresolved subject is that character or an explicitly unresolved referent involving that character. Do not turn an unnamed role into an identity mystery. `A deckhand` does not license `identity of the deckhand`; only the passenger identity is licensed because the deckhand explicitly cannot tell whether the passenger was Leon.

## Chapter-map column contract

For the chapter map, keep each column semantically narrow:

- **Material events:** only actions/observations/statements actually occurring in the chapter, preserving source predicate and attribution.
- **New information / reveal:** only information newly available in that chapter, preserving whether it is narrator-established, a character statement, a memory, or recorded text.
- **Character-state change:** only a state change explicitly established by the manuscript. Do **not** use this column to restate dialogue, routes, evidence, phone calls, investigation activity, or inferred transitions. If no explicit state change is established, write `None established`.
- **Open threads created / resolved:** only the ledger's source-licensed unresolved points or explicit resolutions. If none are licensed for that chapter, write `None established`. Do not generate `who/when/how/why` questions from static states or object presence.

A statement must never be compressed into a stronger action in the character-state column. For example, `Mara says Leon left before six. He told me he was taking the north road.` must not become `Leon left before six taking the north road` anywhere in the chapter map.

## Recommended output

### 1. Manuscript-level reconstruction
A short description of the story as it currently exists, including central dramatic question and current ending state.

### 2. Chapter map
`Chapter | Material events | New information/reveal | Character-state change | Open threads created/resolved`

### 3. Character and relationship map
`Character | Explicit role/history | Explicit goals/beliefs | Relationship evidence | Unknowns`

### 4. Chronology and causal map
List confirmed sequence first, then uncertain/conflicting timing. Include causal claims only when the manuscript explicitly states a causal relation or a character explicitly states a causal belief. If none are established, write `None established`; do not invent causal/process questions from static states.

### 5. Evidence and uncertainty register
`Claim | Strength | Evidence | Source-licensed unresolved point`
Copy the self-contained canonical claim into `Claim`, including its attribution and modality. Use `—` when the ledger licenses no unresolved point for that claim. Do not generate new precursor events or investigative questions to fill the final column.

### 6. Motifs / possible themes
Separate repeated textual motifs from interpretive thematic readings and label confidence.

### 7. Continuity / contradiction register
Record discrepancies without repairing them.

### 8. Living editorial-brief seed
A compact, neutral summary of current premise, story movement, major reveals, source-licensed unresolved points, point-of-view/structural observations actually evidenced by the text, and only those author-confirmation items licensed by the ledger. Do not group statements/recollections under a place unless their own ledger atoms carry that location. Do not propose candidate answers, mechanisms, motives, craft-device labels or authorial explanations unless the source text itself supplies them.

## Out of scope

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
- Did I avoid carrying an earlier object state into a later appearance when the later text does not restate that state (for example, Chapter 1's `clock reads 6:45` must not become a Chapter 3 clock reading merely because Mara looks at the clock again)?
- Could every factual clause in the visible output be traced back to one or more source-ledger atoms without adding recipient, location, time, state, predicate or modality?
- Did I keep static states as states rather than inventing implied transitions/processes (cold→cooled, located→arrived/parked, receipt present→purchased/used)?
- Did every rendered unresolved/open-thread/author-confirmation item come from a `Source-licensed unresolved point` in the ledger, rather than being reverse-engineered from a static state or object presence?
- Did I keep sentence-local location/time modifiers attached only to the atoms they explicitly modify, rather than propagating them to adjacent material?
- Did every location/time-grouped summary contain only atoms that independently carry that same modifier, with unlocated atoms rendered separately?
- In character-map `Unknowns`, did I avoid turning unnamed roles into identity mysteries and restrict entries to source-licensed unresolved points whose subject is that character?
- In the chapter map, did I use `Character-state change` only for explicit state changes and write `None established` rather than using that column to paraphrase events or dialogue?
- Did I preserve nested attribution and clause boundaries, rather than collapsing `X says A; Y told X B` into a single factual claim `A and B`?
- Did I avoid editorial recommendations?
- Could a later editing agent safely use this as a factual map without inheriting invented canon?
