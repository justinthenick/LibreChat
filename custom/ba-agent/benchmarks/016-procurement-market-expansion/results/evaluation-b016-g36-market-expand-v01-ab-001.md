# Benchmark 016 Evaluation — Procurement Market Expansion

Job: `b016-g36-market-expand-v01-ab-001`  
Model: `gemini-3.6-flash`  
Temperature: `0.0`

## Scores

| Run | Score | Penalties | Tokens | Decision |
|---|---:|---:|---:|---|
| Baseline | **100/100** | 0 | 4,491 | Excellent market-expansion plan without the Skill. |
| `expand-procurement-market` v0.1.0 | **100/100** | 0 | 5,091 | Excellent, but no measurable score improvement over the baseline. |

## Evaluation

Both runs correctly identify eBay Australia, Facebook Marketplace and Gumtree as heavily exploited and stale/homogeneous. Both explicitly reject the idea that more keyword variants inside those marketplaces constitute broad market coverage.

Both increase exploration materially above the Skill default, choosing **30% exploitation / 70% exploration** with a history-specific rationale. Both add genuine new source classes including ITAD/ex-lease suppliers, surplus/auction channels and recycler/refurbisher or specialist channels, while retaining targeted exploitation of known marketplaces only for changed filters, new inventory or stronger evidence.

Both preserve the hard host constraints, propose adjacent host classes only as exploratory, avoid fabricated live listings, and define usable stop/refresh logic.

The Skill output is slightly more systematic about channel-state tabulation and watch cadence, but the baseline independently reaches the same substantive strategy and full rubric coverage. The Skill uses 600 more total tokens (about 13% more).

## Decision

**Do not tune or freeze `expand-procurement-market` v0.1.0 from B016 alone.** The method is sound, but B016 is too easy for the Gemini 3.6 baseline to demonstrate measurable Skill value.

Next: run a harder cross-domain market-expansion benchmark with a **mixed search history**: some sources remain productive while others are exhausted, and some tempting unexplored channels violate hard buying constraints. The test should require calibrated exploration rather than simply maximizing novelty.