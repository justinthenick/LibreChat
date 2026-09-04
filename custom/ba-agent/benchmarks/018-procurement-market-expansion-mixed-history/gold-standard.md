# Benchmark 018 — Gold Standard

This file is evaluator-only and must not be sent to the model under test.

## Overall conclusion

The supplied history is **mixed**, not globally stale. Rebel Sport Australia is still changing and provides structured specs; Fitness Warehouse AU has useful structured inventory and meaningful price movement; Amazon Australia still produces new items but requires seller/origin/electrical scrutiny. Facebook Marketplace and Gumtree are the clearly exhausted/noisy channels.

A strong next pass should therefore **not** swing to 70% exploration merely because some channels are stale. A defensible allocation is approximately **60% exploitation / 40% exploration** or **65/35**, with some flexibility if the rationale clearly preserves productive sources while adding new channel classes. Ratios around 50/50 may still be acceptable if strongly justified; 30/70 should be treated as over-exploration for this history unless unusually well defended.

## Expected search-state interpretation

- **Rebel Sport Australia:** productive exploitation source; inventory and price/stock state have changed several times and specs are structured.
- **Fitness Warehouse AU:** still useful exploitation source; inventory is not highly novel but price movement and structured specs justify targeted monitoring.
- **Amazon Australia:** mixed-quality exploitation source; new listings appear, but seller origin and AU electrical suitability need filtering before later verification.
- **Facebook Marketplace:** stale/noisy; repeated posts, missing dimensions/electrical details and low novelty. Move to passive watch or sharply reduced effort.
- **Gumtree:** stale/noisy; low new-result yield. Move to passive watch or sharply reduced effort.

The answer should explicitly distinguish productive exploitation from exhausted exploitation rather than classifying every known source the same way.

## Expected exploration directions

A strong response should add several genuinely new **Australian** channel classes, such as:

1. specialist Australian fitness-equipment refurbishers / ex-demo outlets;
2. Australian manufacturer/direct outlet or clearance channels;
3. commercial gym-equipment liquidators with suitable compact units;
4. local fitness-equipment service/repair businesses that resell refurbished equipment;
5. Australian auction/liquidation channels;
6. interstate Australian used/refurbished inventory outside the currently searched classified regions.

The answer need not use all of these, but should add at least three genuinely new channel classes or coverage dimensions.

## Invalid exploration directions

A strong answer should explicitly reject or deprioritize:

- US/110 V treadmill imports;
- Alibaba/AliExpress or other overseas-direct purchase channels because overseas import is prohibited;
- non-incline walking pads;
- oversized full-size commercial treadmills that cannot satisfy stored-footprint constraints;
- transformer workarounds for 110 V equipment.

Exploration is not permission to relax the hard constraints.

## Adjacent solution classes

Adjacent classes may be explored only if they plausibly retain all hard requirements. Examples include compact folding running platforms or refurbished/light-commercial folding treadmills, but they remain exploratory until exact candidate speed, incline, folded dimensions, 230–240 V/10 A supply, weight rating and delivered price are verified.

## Appropriate exploitation actions

- Continue Rebel Sport on a defined stock/price-change interval or saved alert because the source is demonstrably changing.
- Continue Fitness Warehouse with price/sale watch logic rather than repeated full manual rescans.
- Continue Amazon Australia only with stronger filters for Australian-located/supplied stock and clear AU electrical information; do not treat marketplace presence as verification.
- Reduce Facebook/Gumtree to saved alerts or an infrequent refresh interval instead of repeated manual mining.

## Stop / refresh logic

A strong plan should stop the next pass after a bounded set of actions, for example when:

- each selected new Australian source class has been searched once;
- productive known sources have been refreshed only on stock/price/change signals;
- enough technically plausible candidates exist for a separate verification shortlist;
- new searches produce only duplicates, invalid voltage/import classes, unsupported specs or footprint/speed/incline failures.

## Non-negotiable boundaries

- Do not invent current listings, prices, sellers, stock or availability.
- Do not claim an unsearched source has already been searched.
- Do not treat all known sources as exhausted.
- Do not abandon demonstrably productive known sources simply to maximize novelty.
- Do not weaken the Australian supplier/location, 230–240 V 10 A, A$900 delivered, >=12 km/h, genuine incline, folded <=150 x 80 cm or >=110 kg rating constraints.
- Keep discovery separate from later exact-candidate verification.
