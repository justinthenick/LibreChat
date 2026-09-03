# Manuscript Engineering Lab

This track develops a controlled manuscript-analysis and editing workflow that can eventually accept a draft book, reconstruct what is actually on the page, work against an approved editorial brief, propagate approved changes safely, and support final pre-publication review.

## Governing sequence

`Draft manuscript -> Structural reconstruction -> Author-approved living editorial brief -> Chapter-level editing -> Change-impact analysis -> Whole-manuscript consistency pass -> Pre-publication edit -> Pitch/publishing support`

The governing principle is: **reconstruct before editing; edit against an approved brief; do not turn interpretation into canon without author confirmation.**

## M001 — Manuscript Structure Reconstruction

First capability: `analyze-manuscript-structure` v0.1.0.

Scope is deliberately narrow:

- reconstruct chapter-level events and reveals;
- map characters, relationships, chronology and causal claims;
- distinguish explicit fact, character belief, inference and Unknown;
- identify motifs/themes cautiously;
- flag contradictions and unresolved threads;
- produce a neutral living editorial-brief seed.

Explicitly out of scope for M001:

- rewriting;
- developmental or line-edit recommendations;
- chapter reordering;
- pitch/query writing;
- publishing-market advice;
- legal/copyright conclusions;
- cross-manuscript change propagation.

### Benchmark design

M001 uses a synthetic five-chapter mini-novel with evaluator-known ground truth. It contains:

- a clear present-day investigation and backstory;
- multiple evidence types with different reliability;
- an unnamed/uncertain radio voice;
- ambiguous initials;
- conflicting timing/accounts;
- a deliberately unresolved disappearance;
- recurring motifs and plausible themes that must not be presented as certain authorial intent.

The baseline and Skill receive the same manuscript and analysis request. Success is measured on reconstruction fidelity and uncertainty discipline, not eloquence.

### Pass gate

Prefer the Skill only if it materially improves faithful reconstruction and uncertainty handling without adding editorial invention. A high-scoring result should be safe to use as the factual substrate for later editing.

## Planned progression

Do not build all later stages at once. Progress only after the previous capability has strong evidence.

1. **M001 — Structure reconstruction**: prove faithful decomposition.
2. **M002 — Chapter developmental edit against an approved brief**: bounded chapter sample; suggestions must trace back to brief and evidence.
3. **M003 — Change-impact analysis**: given one approved story change, identify affected earlier/later chapters, facts, motivations, foreshadowing and continuity points without silently rewriting them.
4. **M004 — Multi-chapter consistency/edit composition**: combine reconstruction + approved brief + chapter edit + impact map.
5. **Later — Full-document pre-publication pass**: consistency, prose/copy-editing layers and publication-readiness checklist.
6. **Later — Pitch/submission support**: synopsis/query/pitch generated from the approved manuscript state, not from guessed intent.
7. **Later — Rights/copyright support**: bounded administrative/checklist support only; legal conclusions remain outside the agent's authority unless separately reviewed by a qualified professional.

## Long-term agent concept

A future Manuscript Engineering agent may orchestrate specialist Skills rather than one monolithic editor:

`Structure Analyst -> Editorial Brief -> Chapter Editor -> Change Impact -> Consistency/QA -> Pre-publication -> Pitch support`

The agent should maintain a clear distinction between:

- manuscript canon;
- author-approved interpretation/brief;
- proposed edits awaiting approval;
- applied changes;
- unresolved questions.

This separation is essential for preventing one speculative edit from silently becoming fact throughout the manuscript.
