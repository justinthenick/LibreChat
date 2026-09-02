# Benchmark 018 — Scoring Rubric

This file is evaluator-only and must not be sent to the model under test.

Score out of 100 before penalties.

## 1. Mixed search-history understanding — 20 points

- Correctly distinguishes still-productive Rebel Sport / Fitness Warehouse from stale Facebook Marketplace / Gumtree: 8
- Correctly treats Amazon Australia as mixed-quality rather than simply exhausted or fully trusted: 4
- Explains that known-source status should depend on freshness, novelty and evidence quality rather than whether the source was searched before: 4
- Does not classify the entire history as globally stale: 4

## 2. Calibrated exploitation/exploration strategy — 20 points

- Gives an explicit exploit/explore ratio or equivalent allocation: 4
- Keeps exploitation substantial because productive sources are still changing: 7
- Raises exploration above the default 20% because several known channels are exhausted/noisy: 5
- Explains why the chosen balance fits the mixed evidence rather than mechanically applying 80/20 or 30/70: 4

## 3. Genuine constrained market expansion — 20 points

- Adds at least three genuinely new Australian source/channel classes or coverage dimensions: 10
- Adds geographic/condition/source diversity without relying on overseas import: 4
- Includes at least one plausible adjacent solution class while preserving all hard constraints: 3
- Clearly separates discovery from later exact-candidate verification: 3

## 4. Productive-source exploitation and stale-source retirement — 15 points

- Continues Rebel Sport and/or Fitness Warehouse for a stated change-signal reason: 5
- Uses Amazon AU selectively with seller/origin/electrical filtering rather than assuming marketplace presence proves suitability: 3
- Reduces Facebook/Gumtree to passive alerts or lower-frequency refresh rather than repeated manual loops: 4
- Defines useful saved-search/watch or change-trigger logic: 3

## 5. Invalid-expansion rejection and constraint preservation — 15 points

- Explicitly rejects/deprioritizes overseas 110 V/direct-import routes: 4
- Rejects non-incline walking pads and oversized footprint classes when they violate hard gates: 4
- Preserves 230–240 V/10 A, A$900 delivered, >=12 km/h, genuine incline, folded <=150 x 80 cm and >=110 kg constraints during exploration: 5
- Does not propose transformer workarounds or other hard-gate bypasses: 2

## 6. Stop conditions, prioritisation and no fabrication — 10 points

- Provides concrete bounded stop/refresh conditions and prioritises the next pass: 4
- Does not fabricate live listings, sellers, prices, stock or search results: 6

# Penalties

Apply after raw score, minimum final score 0.

- **-20** if the response treats the whole history as exhausted and recommends an exploration-heavy reset (for example around 30/70) without a strong reason for abandoning demonstrably productive sources.
- **-15** if it continues repeated manual Facebook/Gumtree mining as a major part of the next pass despite the supplied stale history.
- **-15** if it recommends US/110 V or overseas-direct import channels despite the explicit no-overseas-import/AU-voltage hard constraints.
- **-15** if it recommends non-incline walking pads or oversized full-size treadmills by weakening explicit speed/incline/footprint constraints.
- **-10** if it proposes a transformer workaround for 110 V equipment.
- **-10** if it treats Amazon AU marketplace presence as proof of Australian electrical suitability or local supplier status.
- **-10** if an adjacent solution class is presented as already verified/compatible without exact evidence.
- **-25** if it fabricates one or more current listings/sellers/prices/availability and uses them as findings.
- **-5** if no explicit stop or refresh rule is provided.

# Interpretation

- 90–100: excellent calibrated market-expansion discipline; strong evidence to retain the Skill for composition.
- 80–89: useful but contains a reusable discovery/calibration gap worth diagnosing.
- 70–79: mixed; risks either stale-source looping or novelty overcorrection.
- below 70: insufficient market-discovery discipline.

For A/B comparison, prefer the Skill only if it improves calibration between productive exploitation and genuine exploration while preserving hard constraints and avoiding fabricated findings.
