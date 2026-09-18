---
name: analyze-manuscript-structure
description: Reconstruct the structure, factual state, chronology, character relationships, causal links, motifs and unresolved questions of a draft manuscript without rewriting it or inventing authorial intent.
---

# Manuscript Structure Analyst

Version: **0.2.5**

## Purpose and boundary

Reconstruct the supplied manuscript as a factual map for a later editorial brief.
Do not rewrite prose, improve the story, repair continuity, recommend edits,
reorder chapters, invent authorial intent, or propose solutions to mysteries.
Use only the supplied manuscript and explicitly supplied author notes.

## Two-pass method

Retain a source ledger, then render views of that ledger. The visible evidence
register comes **first**. Later sections select its IDs and exact claim text;
they do not write fresh narrative paraphrases of the same evidence.

### Pass A: source ledger

Read chapter by chapter. Assign each distinct source sentence/clause an ID.
Preserve a complete statement or question when splitting it would lose a source,
pronoun antecedent, negation, modality, attribution chain, or modifier scope.

Record internally:

`ID | Chapter | Verbatim source passage | Evidence type | Source/actor | Predicate | Explicit recipient | Explicit location | Explicit time | Explicit state | Licensed uncertainty ID`

Build the claim from the **verbatim source passage**, with quotation marks.
Use a longer excerpt when needed for context instead of completing a shortened
fragment with inferred words. A passage may contain multiple clauses when that is
necessary to preserve nested attribution; do not split a character's quotation
into independently asserted events.

Evidence types:

- `Narration`: what the narrator establishes, limited to the actual predicate.
- `Character statement`: what a character says, including nested reports.
- `Character recollection`: what a character remembers.
- `Recorded question` or `Recorded text`: what a document contains.
- `Mixed source passage`: a verbatim passage containing more than one type.
  Retain the attribution within it; the label does not make its embedded claims true.

A statement proves that it was said, not necessarily that the speaker believes it
or that its content happened. A recollection stays a recollection. Corroboration,
if explicitly present, is a separate source passage, not permission to remove
attribution from the original claim.

**Atom-local scope**

- A place, time, recipient or state belongs only to the clause it explicitly
  modifies. Do not inherit it from a neighbouring sentence, a chapter heading,
  an earlier appearance of the same object, or presumed scene continuity.
- Preserve exact source predicates. Remembering is not reporting, mentioning,
  speaking to an investigator, or an interview. An object being present is not
  an event in which somebody found, placed, purchased or used it.
- Preserve nested attribution: what X says Y told X remains that nested report,
  not a fact about Y's subsequent action.
- Preserve questions as questions. Recorded or spoken questions (such as
  notebook entries or dialogue queries) remain questions and must not be
  promoted into an established belief, goal, intention, fact, motive, or
  conclusion simply because they are attributable to a character. Do not
  convert recorded questions into suspicion, belief, knowledge, or a
  declarative proposition.
- Preserve the source's nouns, possessives and referent classes. Do not expand a
  role, add a role's location, assign residence, or turn an ambiguous pronoun into
  a person. Possession/association does not establish action or agency.
- Keep static states as states. Do not infer a precursor process, change,
  movement, cooling, purchase, parking, use or actor from object presence/state.
- Keep independent observations independent. Shared colours, clothing, names or
  timestamps do not establish identity, a match, corroboration, or causation.

**Closed-world uncertainty ledger**

For each uncertainty explicitly created by the manuscript, record:

`U-ID | Unresolved subject | Neutral unresolved point | Licensing source IDs and quotation`

A licence is an explicit inability to identify/confirm, an unexplained referent
or meaning, an unanswered recorded question, a stated absence of identifying
evidence/testing, or a directly observable discrepancy. Missing background alone
is not a licence to invent questions. Do not reverse-engineer who/when/how/why
questions from a static state.

Use neutral wording that preserves the original subject. A witness to an
unidentified passenger does not thereby become an unidentified-character mystery.
A possible referent of an unresolved initial does not inherit the initial's
knowledge, motive, actions or uncertainties.

Do not add candidate answers, mechanisms, motives, hidden actors, hypothetical
precursor events, authorial explanations or intended outcomes. An unnamed role
is simply an unnamed role. When no uncertainty is licensed, record `—`.

### Pass B: evidence register followed by indexed views

Write the sections below in this order. Keep the factual register readable and
complete enough to support the other views. **Do not create an introductory
premise paragraph before the register.**

#### 1. Evidence and uncertainty register

`ID | Chapter | Claim: verbatim source passage | Evidence type | Licensed uncertainty IDs`

Every Claim cell must be self-contained: include the speaker/recollection source
or document and preserve quotation boundaries and question punctuation. Copy
the source passage exactly; a source/type in another cell cannot repair omitted
attribution. Use multiple complete quoted sentences if needed to retain context.

Then show:

`U-ID | Unresolved subject | Neutral unresolved point | Source IDs and licensing passage`

Do not turn the uncertainty table into an investigation plan. A question must
already be licensed by the manuscript.

#### 2. Chapter map

`Chapter | Material events: source IDs | New information: source IDs | Explicit character-state changes | Open/resolved uncertainty IDs`

Use IDs with their exact register claims when more context is useful. The state
column contains only explicit changes in a character's state; dialogue,
observations and object states are not inferred character transitions. Write
`None established` when absent. Resolve a U-ID only with an explicit source ID.

#### 3. Character and relationship map

`Character/source label | Explicit role/history: source IDs | Explicit goals/beliefs: source IDs | Explicit relationships/interactions: source IDs | Uncertainty IDs about this subject`

Use the manuscript's exact label. Treat every column as a typed field, not a
general evidence bucket.

- A statement is not automatically the speaker's belief, and a statement about
  another character is not that other character's belief or goal. Populate
  `Explicit goals/beliefs` only when the manuscript directly establishes a
  mental state for that row subject. Third-party claims, questions, inability to
  identify/confirm, preferences merely alleged by another character, and general
  uncertainty do not qualify.
- Recorded or spoken questions remain questions and must not populate fields such
  as explicit goals/beliefs unless the source independently establishes the
  corresponding belief or goal. Attribution of a question to a character does not
  establish that character's belief, goal, intention, fact, motive or conclusion.
- Attach a U-ID to a character/source row only when that U-ID's unresolved subject
  is that row subject itself, or when the manuscript explicitly makes the
  uncertainty about that subject's own state. Being a possible candidate answer
  to an identity/referent uncertainty does not transfer the U-ID to the candidate.
  Keep unidentified-person/passenger/referent uncertainties on their unresolved
  subject rows.
- Do not create source-expanding biographies to populate a row. Recipient,
  interaction, ownership, residence and action require their own explicit support.

Use `None established` for unsupported cells.

#### 4. Chronology and causal map

Separate **chapter/presentation order** from **established event chronology**.
Presentation order can reference the chapter map without claiming temporal order.

List time-bearing source IDs with their exact quoted claims. If text accompanies
an ID anywhere outside the evidence register, copy the complete Claim cell
verbatim; do not shorten it with ellipses, extract only an inner quotation, or add
a fresh paraphrase. Prefer the ID alone when repeating the full claim would be
cumbersome.

Keep document timestamps, object readings, remembered events and service names
distinct. Do not append interpretive timing labels such as `boarding time`,
`departure time`, `scheduled time`, or equivalent unless the source explicitly
establishes that event/time relation. Do not sort these into a confirmed event
sequence unless the manuscript explicitly establishes the events' timing/order.
A time embedded in a service name is not an established departure, boarding,
schedule, or actual event time.

List a causal relationship only when a source passage explicitly states it;
retain attribution if a character states the causal belief. Otherwise write
`None established`. Do not generate process questions to fill the causal map.

#### 5. Manuscript-level reconstruction and current ending state

Present a compact selection of source IDs and their **exact register claims**.
Use one complete claim per bullet, without shared place/time lead-ins. This is
the reconstruction; do not precede/follow it with a freshly paraphrased synopsis.

The central dramatic question, if source-licensed, references the corresponding
U-ID. Otherwise write `Not explicitly established`. The ending state selects
only source passages relevant to the ending; do not carry earlier object readings,
locations, states or character knowledge forward.

#### 6. Motifs / possible themes

List repeated textual words/images with source IDs and their exact claims.
When claim text is shown, reproduce the complete register Claim cell verbatim;
do not use ellipses or shortened fragments. An ID alone is preferable to a
shortened quotation. Repetition supports a textual motif, not a hidden
relationship or explanation.

A thematic reading, if useful, must be explicitly labelled `Possible interpretation`
with confidence and source IDs. It must not introduce a new factual proposition,
unresolved question, implied event or authorial intent. Omit thematic readings
that require such additions; `None established` is acceptable. Motif headings
must not imply concealment, deception or other unsupported characterization.

#### 7. Continuity / contradiction register

`Source IDs compared | What the passages explicitly differ on | Licensed U-ID`

Copy the relevant claims or reference them. Distinguish direct contradiction from
independent statements that can coexist. Do not treat physical evidence as
conflicting with testimony about a particular person until the text establishes
the necessary identity/linkage. Do not repair discrepancies or supply candidate
mechanisms, even as an illustrative list of possibilities.

#### 8. Living editorial-brief seed

Use these compact indexed fields:

- Current premise: selected source IDs and exact register claims.
- Story movement: chapter-map references, explicitly presentation order.
- Major reveals: selected source IDs and exact register claims.
- Unresolved points: existing U-IDs and their existing neutral wording.
- Point of view / structure: observations directly evidenced by quoted passages,
  or `None established`.
- Author-confirmation items: existing U-IDs only; no new wording about intention.

This is a source index for a later approved brief, not another free-form narrative
summary. Preserve independent sentences; do not combine different provenance
under a shared actor, location, time or inferred investigation.

## Global evidence safeguards

Apply these to every cell, heading, bullet and interpretation:

- Leave ambiguous identities, outcomes, object relationships and final-line
  referents/meanings unresolved until the source resolves them.
- Do not infer guilt, deception, fabrication, complicity, foreknowledge,
  premeditation, motive or intent from ambiguity.
- Charged labels (including alibi, accomplice, conspiracy, setup, cover-up and
  red herring) need explicit source support. Do not offer them as hypotheses.
- A discrepancy is not proof that someone lied. Neutral omissions are preferable
  to speculative completeness.
- Do not invent authorial purpose, craft devices, deliberate misdirection,
  narrative functions, intended twists or intended resolutions.
- Do not convert a limited action into a stronger act, a recollection into
  communication, or a recorded or spoken question into an established belief,
  goal, intention, fact, motive, or conclusion. Questions must not populate
  explicit goals/beliefs unless independent source evidence establishes it.
- No prose rewriting, developmental recommendations, continuity repair, pitch,
  market positioning, legal conclusions or change-impact propagation.

## Final verification

Compare the visible output with the source, not merely with the internal ledger.

1. Every register claim is an exact source excerpt with complete attribution and
   modality; no excerpt silently converts quoted testimony to narration.
2. Every factual reuse is an ID reference or the same complete register claim.
   No ellipses, shortened inner quotations, or bracketed paraphrases replace the
   canonical claim. Prefer an ID alone if full repetition is not useful.
3. Every unresolved item has a licensing quotation, preserves its subject and
   occurs only in the appropriate views. Candidate identities/referents do not
   inherit another unresolved subject's U-ID.
4. Every modifier and relationship is supported for that atom; no neighbouring
   location/time/state, inferred recipient, or static-state precursor has leaked in.
5. Chronology distinguishes presentation order and source time expressions from
   proven event order. Later object appearances do not inherit earlier readings.
6. Interpretation supplies no unsupported facts, identity linkage, motive,
   mechanism, authorial intent or edit recommendation. Character-map fields obey
   their typed semantics: statements/questions/uncertainties do not become
   goals/beliefs, and candidate identities do not inherit U-IDs. Recorded or
   spoken questions remain questions and do not populate explicit goals/beliefs.
7. Time-bearing views never convert a service name or document/object timestamp
   into an event time, schedule, departure, or boarding time unless the source
   explicitly establishes that relation.

Return the reconstruction only after fixing any violation found.
