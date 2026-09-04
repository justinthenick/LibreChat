# Benchmark 018 Evaluation — Mixed-History Procurement Market Expansion

Job: `b018-g36-market-expand-v01-ab-001`  
Model: `gemini-3.6-flash`  
Temperature: `0.0`

## Scores

| Run | Score | Penalties | Tokens | Decision |
|---|---:|---:|---:|---|
| Baseline | **95/100** | 0 | 5,147 | Strong mixed-history reasoning, but over-explores at 40/60 and does not add a clear adjacent solution class. |
| `expand-procurement-market` v0.1.0 | **99/100** | 0 | 5,424 | Excellent calibration at 60/40, strong stale-source retirement, constrained expansion and adjacent-class handling. Retain for composition. |

## Baseline evaluation

The baseline correctly reads the history as mixed rather than globally stale: Rebel Sport and Fitness Warehouse remain productive, Amazon AU is mixed-quality, and Facebook Marketplace/Gumtree are stale. It keeps productive-source monitoring, reduces stale classifieds, expands into refurbisher/manufacturer/auction channels, rejects overseas/110 V/non-incline/oversized routes and provides bounded refresh rules.

Its main weakness is calibration. The proposed **40% exploitation / 60% exploration** still preserves productive sources, so no over-exploration penalty applies, but it underweights the supplied evidence that two known retailers are actively changing. The gold-standard balance is closer to 60/40 or 65/35. It also expands source classes well but does not clearly add an adjacent product/solution class as requested by the rubric.

## Skill evaluation

The Skill improves the exact behavior B018 was designed to test. It explicitly classifies the search history source by source, chooses **60% exploitation / 40% exploration**, and explains why neither default 80/20 nor an exploration-heavy reset fits the evidence. It continues Rebel Sport, Fitness Warehouse and filtered Amazon AU for change-signal reasons while pausing routine Facebook/Gumtree polling.

It adds multiple genuine Australian discovery classes and two explicitly labelled adjacent solution classes while preserving all hard gates. It clearly rejects overseas/direct-import, 110 V, transformer, non-incline walking-pad and oversized treadmill directions. Its stop/watch plan is bounded and it does not fabricate live candidates, prices or availability.

A minor precision issue remains: the next-pass table groups a couple of newly named specialist retailers alongside the known productive Fitness Warehouse under `Exploit`, even though those new sources would technically be exploratory until searched. This does not alter the overall calibration or constraint discipline.

## Decision

**Retain `expand-procurement-market` v0.1.0 for Procurement Analyst composition.** B016 proved the method could match an already-strong baseline; B018 now demonstrates incremental value on the harder mixed-history case, particularly in productive-source retention, exploration calibration and adjacent-class discipline.

Next: design the first Procurement Analyst composition benchmark that requires the agent to decide whether the request needs verification only, expansion only, or expansion followed by verification, rather than invoking every procurement capability mechanically.
