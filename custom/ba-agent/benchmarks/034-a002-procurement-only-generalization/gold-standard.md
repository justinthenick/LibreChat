# Evaluator-only gold standard — Benchmark 034

## Correct routing outcome

The minimum correct route is exactly:

1. `prepare-procurement-specification`
2. `expand-procurement-market`
3. `verify-procurement-options`

The Agent should deliberately **not** select:

- `analyze-requirements` — the procurement requirements are already normalized.
- `analyze-nonfunctional-requirements` — the quality/constraint dimensions relevant to this purchase are already normalized at procurement strength.
- `design-technical-solution` — this is a stable furniture procurement boundary with no architecture work requested.
- `record-architecture-decisions` — no ADR is requested or relevant.

There is no architecture stop gate in this packet. Candidate-specific missing evidence may remain `Unknown / verify` during procurement verification and does not justify sending the workflow back through solution architecture.

## State-preservation ground truth

- P-02 through P-08 are **Hard minimums**.
- P-09 A$750 is a **Target**, not a Hard minimum.
- P-10 10 weeks is a **Target**, not a Hard minimum.
- P-11 >=30% recycled content is a **Preference**, not a Hard minimum.
- P-12 upholstery colour is **Unknown / non-eligibility** and should remain deferred to post-shortlist configuration.
- No procurement approval authority is supplied.
- The incumbent reseller has no inferred decision authority or preferred-supplier status.

## Candidate verification ground truth

### C-01 ErgoNova E8 Commercial
Eligible against all supplied Hard minimums.

Evidence also supports the stated price Target, delivery Target and recycled-content Preference, but those are not what make it eligible.

### C-02 ArcSeat Pro 5
Ineligible because the exact model's supplied maximum user rating is 135 kg, below the 150 kg Hard minimum P-06.

Its lower price, faster delivery and longer warranty cannot compensate for failing a Hard minimum.

Missing recycled-content evidence does not independently cause rejection because P-11 is only a Preference.

### C-03 WorkForm Flex 2
Do **not** mark fully eligible yet. Armrest lateral-width adjustment is absent from supplied exact-model evidence, so P-05 remains `Unknown / verify` for this candidate.

The 12-week quoted delivery misses the 10-week Target but is not a Hard-minimum failure.

The 20% recycled-content declaration misses the 30% Preference but is not a Hard-minimum failure.

## Market-expansion ground truth

Because all supplied candidates came from one incumbent reseller and the user explicitly requested broader coverage, `expand-procurement-market` is required.

A strong output should diversify search/source coverage by manufacturer-direct sources, additional independent commercial-furniture suppliers/resellers, relevant workplace-furniture catalogues or comparable evidence channels. It may define search lanes and candidate-discovery criteria, but it must **not invent newly verified products or facts** that are absent from the supplied packet.

Market expansion discovers candidates; verification establishes whether candidate evidence satisfies gates. The two stages must remain distinct.

## Critical errors

Treat any of the following as critical:

- converting P-09, P-10 or P-11 into a Hard minimum or rejection gate;
- treating omitted C-03 armrest-width evidence as confirmed;
- marking C-02 eligible despite the explicit 135 kg Hard-minimum failure;
- inventing candidate specifications, product facts, approval authority or preferred-supplier status;
- selecting unnecessary architecture/ADR stages despite the explicit mature procurement baseline;
- skipping market expansion despite the user's explicit request to broaden beyond the incumbent-reseller set;
- treating market-discovered possibilities as verified candidates without evidence.
