# MSA-001 — Manuscript Structure Evidence Hardening

## Objective

Prevent `analyze-manuscript-structure` from turning unresolved clues into unsupported motive, guilt, deception, fabrication, foreknowledge, complicity or premeditation while preserving its reconstruction-only role.

## Triggering evidence

The MIG-001 runtime fixture preserved the major unresolved identities and causal questions, but the output still used interpretive phrases including `foreknowledge`, `misdirection / fabrication`, and `premeditation or thwarted expectations`. The phrase `premeditation` is not established by the manuscript and is too strong for a reconstruction-only factual map.

A first v0.1.1 runtime rerun improved the evidence discipline substantially, but still introduced unsupported possibilities such as `an accomplice` for Mara's final line and `red herring` for the harbour fabric. It also promoted some details beyond the text, such as treating presence at the cottage as possible residence and `Leon's car` as evidence he drove it. These are small but important canon-contamination risks for a reconstruction skill.

A second v0.1.2 runtime rerun fixed those charged labels and preserved the major unknowns, but still introduced unsupported mechanisms and authorial/candidate framing in the final synthesis. Examples included asking whether the clock was `intentionally manipulated`, whether sightings were `intended` to be Leon or another known/unintroduced person, and whether the scarf/fabric were `intended` to be the same item. The output also described the clock as `stopped or offset` inside a confirmed chronology even though the manuscript only establishes the displayed time, and one continuity note misplaced the ferry receipt as harbour evidence even though the receipt was found in the car on the north road.

## Change

Current hardening through version 0.2.9 strengthens the evidence-discipline rules further:

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
- recorded or spoken questions must remain questions and must not populate role/history, goals/beliefs, or relationships/interactions merely because a label appears inside the question; each typed field requires independent declarative support;
- character-map columns are typed: statements, third-party claims, inability to identify/confirm and unresolved questions do not become goals/beliefs merely to fill the column;
- character-map role/history, goals/beliefs and relationships/interactions cells render source IDs only (or `None established`) so free-text paraphrase cannot change the typed-field semantics;
- identity/referent/addressee/meaning uncertainties remain attached to their unresolved subject and are not copied onto candidate characters or the source speaker merely because that character supplied the ambiguous statement;
- factual claim reuse is exact when text is shown; ellipses, shortened inner quotations and fresh bracketed paraphrases are not substitutes for the canonical Claim cell;
- chronology claim bullets do not append parenthetical classifications, and absent established chronology/causality renders as `None established` without explanatory paraphrase;
- evidence-register Claim cells are self-contained: dependent pronouns/deictics must carry the minimum contiguous verbatim antecedent context in the same Claim cell rather than relying on a neighbouring row;
- a time embedded in a service name must not be labelled as boarding/departure/scheduled/event time without explicit source support;
- possessive/document associations must not be promoted into actions such as keeping, owning, carrying, writing or maintaining unless the source states the action;
- point-of-view/structure summaries must not invent scene boundaries or assign whole chapters/sequences to atom-local locations;
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


### Attempt 15 — v0.1.15 — FAIL

This controlled rerun preserved the main ambiguity, chronology, provenance, modality, evidence classification, recipient attribution, and nested-attribution controls. Two residual source-contract failures remained:

- the motifs section still used generic communication wording such as `Mrs Pell's mention` and `the deckhand's mention`, with the deckhand phrasing converting the manuscript's `remembers` predicate into a communication act;
- the chronology and motifs propagated the Chapter 1 clock state into Chapter 3 by saying the kitchen clock was reading 6:45 at the end of Chapter 3. The manuscript only states the 6:45 reading in Chapter 1; Chapter 3 says Mara looks at the clock but gives no reading.

These failures show that local output sections can still paraphrase or inherit state even when the high-level evidence rules are correct. Version 0.1.16 therefore changes execution architecture: first build an atomic source ledger preserving source, predicate, recipient, location, time, object state and modality; then render every visible section only from those atoms. Later object references cannot inherit earlier states unless restated, and motif language must preserve the underlying source predicate.


### Attempt 16 — v0.1.16 — FAIL

This controlled rerun showed that the new atomic source-ledger architecture fixed the prior clock-state propagation and motif-predicate drift. The main ambiguity, chronology, provenance, modality, evidence classification, recipient attribution, and source-predicate controls all held.

One criterion-6/source-contract failure remained in the Chapter 1 `Character-state change` cell:

- it said `Mara phones Vale and says Leon left before six taking the north road`, again compressing Mara's two differently attributed claims so that Leon's reported statement about taking the north road became the route he actually took.

The failure is now isolated to misuse of the chapter-map state-change column. Version 0.1.17 therefore gives that column a strict contract: it may contain only explicit character-state changes; it must not restate dialogue, routes, evidence, phone calls, or inferred transitions, and must use `None established` when no explicit state change exists.


### Attempt 17 — v0.1.17 — FAIL

This controlled rerun fixed the Chapter 1 state-change-column compression and preserved the main ambiguity, chronology, provenance, modality, evidence-classification, recipient-attribution, nested-attribution, clock-state, and predicate controls. Two criterion-6/source-ledger issues remained:

- static states were still expanded into unsupported transitions/processes: `engine is cold` became questions about when/why the engine cooled and who drove/parked the car; `receipt in the glovebox` became questions about who purchased it and whether it was used;
- sentence-local location was still propagated to a separate atom: summaries grouped the deckhand's memory under `at the harbour` / described recollections as situated at the harbour, although the source explicitly locates Vale's fabric discovery there but does not explicitly locate the deckhand or the remembering act.

Version 0.1.18 therefore tightens the atomic ledger itself: states cannot imply prior transitions/actions, and location/time/recipient/state modifiers remain atom-local rather than propagating across adjacent sentences.


### Attempt 18 — v0.1.18 — FAIL

This controlled rerun preserved the main ambiguity, chronology, modality, recipient attribution, nested attribution, chapter-state handling, clock-state isolation, and predicate fidelity. Two source-ledger failures remained:

- static states were still reverse-engineered into unsupported precursor events and processes, including `who drove or parked the car`, `when it arrived`, `when the engine cooled`, `who purchased the receipt`, and `whether it was used`;
- the deckhand memory still inherited an unstated harbour location in aggregate summaries and the living brief, even though only Vale's fabric discovery is explicitly located there.

Related open-thread wording such as `Who left Leon's car...` and `Who obtained the ferry receipt?` came from the same open-world completion behavior.

Version 0.2.0 formalizes the source ledger as closed-world. Each atom now carries a `Source-licensed unresolved point` field; open threads, unknowns, evidence-register unresolved cells, and author-confirmation items may render only those licensed uncertainties. Static states/object presence cannot generate reverse-engineered driver/parking/arrival/cooling/purchase/use events, and adjacent statements cannot inherit scene location unless their own atoms carry it.


### Attempt 19 — v0.2.0 — FAIL

This controlled rerun showed that the closed-world unresolved ledger fixed the earlier reverse-engineered parking/cooling/purchase/use questions in the evidence register and substantially reduced speculative open-thread generation. Two rendering-layer criterion-6 issues remained:

- aggregate location grouping still attached the deckhand recollection to the harbour in the current-ending-state and living-brief prose, even though the deckhand-memory atom itself has no explicit harbour location;
- the Deckhand character-map row introduced `Identity of the deckhand` as an unknown even though the manuscript does not create that identity as a mystery; the licensed unresolved point is the passenger identity, not the deckhand's identity.

Version 0.2.1 therefore requires location-homogeneous grouped prose and restricts character-map unknowns to source-licensed unresolved points tied to that character's own atoms or explicit referent uncertainty.


## v0.2.2 renderer change

The [Codex handoff](https://github.com/justinthenick/LibreChat/pull/91#issuecomment-5725214523)
reports continued aggregate-location drift, an invented deckhand identity unknown,
and lost recollection attribution in an evidence-register Claim cell. This is
handoff-reported failure evidence; no complete v0.2.1 capture is archived here,
so this entry does not invent a separately verified attempt or passing score.

v0.2.2 retains the two-pass ledger and adds reusable, self-contained canonical
claims, separate summary units, and unresolved-subject/licensing-passage fields.
It also reconciles the initial evidence labels and unresolved-thread instructions
with the later source-preserving contract. Tool permissions and invocation are unchanged.

### Repeatable preflight

From the repository root (Python 3.8+; no third-party packages):

```sh
python3 -m unittest discover -s managed-skills/benchmarks/MSA-001 -p 'test_*.py' -v
python3 managed-skills/benchmarks/MSA-001/triage.py /path/to/complete-runtime-response.md
```

The test suite pins the original MIG-001 fixture's Git blob and exercises known
location, attribution, invented-unknown, question-to-belief, typed-character-map,
question-to-other-field, source-speaker-uncertainty, service-time and
shortened-claim regressions. Test strings are synthetic minimal
examples, not claimed runtime captures. The triage tool scans captured Markdown
and reports line-numbered review candidates for those known failure families. It can miss paraphrases and flag quoted or negated examples; review each
finding against the source. Exit 1 means candidates were found, exit 0 means none
were detected, and exit 2 is invalid CLI input. Every report remains
`REVIEW_REQUIRED` with `semantic_pass: false`.

These checks do not evaluate all of criteria 2–6 and cannot establish semantic
PASS, model identity, skill loading, or live sync success. The GitHub workflow
runs these same checks without model credentials.

### Fresh runtime procedure

1. Sync this branch through the existing managed-skills source; verify the
   loaded skill version and source revision. Do not manually edit the synced skill.
2. Start a fresh LibreChat chat using the Google connector and Gemini 3.8 Flash.
   Invoke the managed skill with the unchanged manuscript from
   [MIG-001/fixture.md](../MIG-001/fixture.md); do not send evaluator guidance or
   expected answers as manuscript content.
3. Preserve the complete response, exact prompt, connector/model, loaded version,
   branch SHA and sync result. Run triage and independently score every criterion
   2–6, including every output section. Record failures as failures.
4. Keep the PR draft until a fresh runtime passes all of criteria 2–6 unchanged.
5. After an authorized merge, restore the managed-skills sync branch to
   `server/synology`, run sync, and record the source commit, updated skill
   version, and zero attributable skipped skills/files for criterion 7.


### Attempt 20 — v0.2.2 — FAIL (controlled, 2026-09-18)

Fresh LibreChat chat on Google / `gemini-3.8-flash`, skill explicitly selected
through the skill picker. The runtime confirmed `0.2.2` before receiving the
unchanged MIG-001 manuscript and the instruction to reconstruct it exactly.
Tested commit: `f086ced11b00c70cab607481fff3bdd4117701d1`.
Skill blob: `84a9f39c9db4999ceab16193c6d93d0316c6291f`.

Complete response remains in the
[validation conversation](http://192.168.1.5:3200/c/bd31aec9-f17e-51cc-a618-1afbea52635e).
This is a private deployment link, not a public archival capture.

Criteria 2–5 preserved the central ambiguities and avoided accusing Mara.
Criterion 6 failed across the reconstructed premise, chronology, motifs,
continuity register and living brief:

- `Leon left before six taking the north road` collapsed nested testimony into action.
- `their cottage` added ownership/residence.
- `Mrs Pell sees` lost statement attribution in chronology/motifs.
- `when Mara enters` invented an entry action.
- `Scheduled ferry reference` promoted a source time-bearing name into a schedule.
- `who purchased or possessed the receipt` invented precursor uncertainty.
- Chapter 3 story movement grouped the deckhand under the harbour again.
- `Vale makes/has an entry` weakened the distinction between a document containing text and a writing act.
- Author-confirmation wording added `unintroduced party` and `intended resolution`.

The evidence-register passenger claim retained recollection attribution, and
the deckhand Unknowns cell was `None established`. Those improvements do not
compensate for failures elsewhere.

The direct-Google preflight without explicit skill selection could not load
the skill. That preflight contained no manuscript and is not a scored attempt.

### Attempt 21 — v0.2.3 — FAIL (controlled, 2026-09-18)

Fresh runtime validation preserved the major unresolved points, avoided the
historical charged labels and speculative mechanisms, kept source claims
verbatim, and did not invent a confirmed global chronology or causal map.

Strict criterion 6 still failed in the Character and relationship map. ID-13,
the recorded notebook question `"M. knew about harbour before I mentioned it?"`,
was placed under `Explicit goals/beliefs` for Inspector Vale. The source
establishes that the notebook contains a question; it does not independently
establish the corresponding belief or goal. Putting that question in a
goals/beliefs field therefore promotes its modality through table semantics even
though the quotation itself remains verbatim.

The benchmark remains failed rather than accepting the column-level semantic
promotion.

### Attempt 22 — v0.2.4 — FAIL (controlled, 2026-09-18)

The fresh v0.2.4 runtime fixed the immediate ID-13 defect: Inspector Vale's
`Explicit goals/beliefs` cell was `None established`. The output also continued
to avoid the historical charged labels and speculative global chronology.

Strict criterion 6 still failed on typed-field and canonical-reuse discipline:

- Mara's statement that Leon hated boats was placed under `Explicit goals/beliefs`
  for both Mara and Leon, even though a statement is not automatically the
  speaker's belief and a third-party statement does not establish the subject's
  belief or goal.
- The deckhand's inability to tell whether the passenger was Leon was placed under
  the deckhand's `Explicit goals/beliefs`, although it is an epistemic limitation
  supporting the passenger-identity uncertainty rather than a goal/belief.
- U-04, whose unresolved subject is the referent `M.`, was copied onto Mara and
  Mrs Pell as candidate referents. Candidate identities must not inherit the
  unresolved subject's U-ID.
- The chronology labelled the `6:40 ferry` reference as a `boarding time`,
  promoting a time embedded in a service name into an event time.
- Some chronology/motif reuses shortened canonical claims or used ellipses rather
  than reusing the complete evidence-register Claim cell.

The benchmark remains failed rather than accepting column semantics, uncertainty
propagation, service-time promotion or shortened evidence reuse.

### Attempt 23 — v0.2.5 — FAIL (controlled, 2026-09-18)

The fresh v0.2.5 runtime fixed the v0.2.4 typed-field, uncertainty-scope,
service-time and shortened-claim failures. Every character `Explicit
goals/beliefs` cell was `None established`; U-IDs remained attached to their
unresolved subjects; chronology reused complete source claims and did not label
the 6:40 ferry as a boarding/departure/scheduled time.

Two narrower criterion-6 promotions remained:

- Inspector Vale's relationship/interaction cell converted the source wording
  `Vale's notebook contains...` into `keeps a notebook`. The possessive/document
  association does not establish a keeping/maintaining action.
- The living editorial-brief `Point of view / structure` line said presentation
  order followed scenes at the cottage, north road, harbour and cottage. This
  assigned chapter/scene locations from individual atom-local locations even
  though other atoms in those chapters are unlocated or differently located.

The benchmark remains failed rather than accepting inferred biography/action or
scene-location propagation.

### Attempt 24 — v0.2.6 — FAIL (controlled, 2026-09-18)

The fresh v0.2.6 runtime cleared the v0.2.5 possessive/document-action and
scene-location failures. It also preserved the earlier gains: every
`Explicit goals/beliefs` cell was `None established`, the 6:40 ferry remained a
service reference rather than an event time, canonical claims were reused
completely, and the major ambiguities remained unresolved.

Two narrower typed-field/uncertainty-scope failures remained:

- The `"M."` character/source row cited the recorded notebook question ID 13
  under both `Explicit role/history` and
  `Explicit relationships/interactions`. The question establishes an unresolved
  referent/question, not independent role/history or relationship evidence.
- Mara's row inherited U-6 even though U-6 concerns the addressee and meaning of
  Mara's whisper. Supplying an ambiguous utterance does not make the resulting
  addressee/meaning uncertainty an uncertainty about the speaker.

The uncertainty ledger also reduced the recorded notebook question to only the
referent of `M.`; v0.2.7 explicitly requires an unanswered question's unresolved
proposition to remain represented without asserting it as fact.

The benchmark remains failed rather than accepting typed-field reuse of a
question or source-speaker uncertainty propagation.

### Attempt 25 — v0.2.7 — FAIL (controlled, 2026-09-18)

The fresh v0.2.7 runtime fixed the v0.2.6 question-to-other-field and
source-speaker uncertainty failures. The `M.` row kept its typed fields neutral,
Mara no longer inherited the whisper addressee/meaning uncertainty, and the
notebook question preserved both referent uncertainty and the questioned prior
knowledge without asserting that proposition as fact.

Strict criterion 6 still failed through free-text rendering:

- The Deckhand row populated `Explicit goals/beliefs` with the deckhand's
  recollection and inability to identify the passenger. Neither is an established
  goal/belief.
- `Explicit role/history` for Leon and Inspector Vale became a generic
  association bucket (`possessive association with car/coat/scarf/notebook`)
  rather than role/history evidence; some associated content originated inside
  attributed character statements.
- Character-map typed fields used fresh descriptive paraphrases beside source IDs,
  allowing semantic promotion even when the cited source was correct.
- Time-bearing chronology bullets appended parenthetical classifications after
  canonical claims, and the `Established event chronology` / causal sections
  added explanatory paraphrase even though no cross-source chronology or causal
  relationship was established.

The benchmark remains failed rather than accepting semantic drift through
free-text attached to otherwise correct source IDs.

### Attempt 26 — v0.2.8 — FAIL (controlled, 2026-09-18)

The fresh v0.2.8 runtime fixed the v0.2.7 rendering failures. Character-map typed
fields were ID-only/neutral, the `M.` and final-whisper uncertainties remained on
their unresolved subjects, time-bearing claims carried no appended annotations,
and established chronology/causality rendered as `None established`.

One source-register contract failure remained: several Claim cells were exact
source sentences but were not self-contained because their pronoun antecedents
lived only in neighbouring rows. Examples include `"Her brother Leon is not
there."`, `"She could not see the person's face."`, and `"She whispers, “You
were supposed to be late.”"`. The skill already requires a longer verbatim
excerpt when splitting would lose a pronoun antecedent, so accepting this run
would weaken the existing gate.

### v0.2.9 candidate — runtime pending

v0.2.9 makes source-atom construction explicit: a dependent sentence is merged
backward to the minimum contiguous verbatim span that makes its antecedent
explicit, is not also emitted as a standalone claim, and is labelled
`Mixed source passage` when the combined span contains multiple evidence types.
Existing acceptance criteria and the MIG-001 fixture remain unchanged.

## Promotion rule

Do not merge the semantic hardening change until a fresh runtime invocation of the MIG-001 fixture satisfies criteria 2–6. MIG-001 remains valid as evidence that the GitHub migration/cutover mechanism worked; MSA-001 is the quality gate for the manuscript skill itself.
