# Benchmark 016 — Scoring Rubric

This file is evaluator-only and must not be sent to the model under test.

Score out of 100 before penalties.

## 1. Search-history understanding — 20 points

- Correctly identifies eBay, Facebook Marketplace and Gumtree as heavily/repeatedly exploited: 8
- Recognizes declining novelty, repeated inventory/categories and weak evidence as signs of stale/homogeneous coverage: 6
- Explicitly states that repeated queries/URLs within the same marketplace are not broad market coverage: 6

## 2. Exploration/exploitation strategy — 20 points

- Gives an explicit exploit/explore ratio or equivalent allocation: 5
- Raises exploration materially above the default 20% because current sources are stale/homogeneous: 8
- Explains why the chosen allocation fits the supplied history rather than treating 80/20 as a rigid rule: 7

## 3. Genuine market expansion — 25 points

- Adds at least three genuinely new source/channel classes from the unsurveyed space: 12
- Includes meaningful geographic/condition/source diversity beyond another Australia-wide marketplace query: 5
- Proposes at least one plausible adjacent host/solution class without weakening hard constraints: 5
- Clearly separates discovery from later candidate verification: 3

## 4. Exploitation quality and refresh discipline — 15 points

- Reuses known channels only for a stated reason such as stock refresh, price movement, new exact evidence or materially different filter: 6
- Avoids recommending daily manual reruns of exhausted query loops: 4
- Defines useful saved-search/watch or refresh logic: 5

## 5. Stop conditions and prioritisation — 10 points

- Provides concrete stop conditions for the next pass: 5
- Prioritises actions and explains what evidence/result would justify continuing or changing direction: 5

## 6. Constraint preservation and no fabrication — 10 points

- Preserves tower/full-height/242 mm/PSU/connector constraints during exploration: 4
- Does not fabricate live listings, prices, sellers, stock or search results: 6

# Penalties

Apply after raw score, minimum final score 0.

- **-25** if the response fabricates one or more current listings/sellers/prices/availability and uses them as findings.
- **-15** if the proposed next pass is primarily another set of eBay/Facebook/Gumtree keyword rewrites with no genuine source-class expansion.
- **-10** if the response treats many searches/URLs within one marketplace as broad market coverage.
- **-10** if exploration weakens an explicit hard buying constraint merely to create novelty.
- **-10** if an adjacent solution class is presented as already verified/compatible without evidence.
- **-5** if the default 80/20 ratio is copied mechanically despite the supplied stale/homogeneous history, with no adjustment rationale.
- **-5** if no stop or refresh rule is provided.

# Interpretation

- 90–100: excellent market-expansion discipline; safe to retain for later composition.
- 80–89: useful but contains a reusable discovery gap worth diagnosing.
- 70–79: mixed; likely to continue stale-source loops or expand inconsistently.
- below 70: insufficient market-discovery discipline.

For A/B comparison, prefer the Skill only if it produces genuinely broader search coverage without fabricating live findings or diluting verification standards.
