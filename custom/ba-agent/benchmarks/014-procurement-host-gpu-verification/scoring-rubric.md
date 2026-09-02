# Benchmark 014 — Scoring Rubric

This file is evaluator-only and must not be sent to the model under test.

Score out of 100 before penalties.

## 1. Requirements and evidence discipline — 20 points

- Correctly preserves H-01 through H-06 as hard gates and P-01 through P-04 as preferences: 8
- Clearly distinguishes exact-item/configuration evidence, family/model evidence, seller claim/inference and Unknown: 8
- Does not silently add new hard requirements or promote preferences: 4

## 2. Host A P330 family-vs-unit trap — 25 points

- Correctly identifies H-05 exact PSU wattage as Unknown, despite 400 W being a family option: 10
- Correctly identifies H-06 GPU-power connector as Unknown: 6
- Uses family/model evidence appropriately for chassis fit and PCIe x16: 5
- Disposition is `Hold for verification` or equivalent, with exact PSU-label/connector evidence requested: 4

## 3. Host B verified compatible recommendation — 20 points

- Correct total A$780 and budget Pass: 4
- Physical 242 mm dual-slot fit correctly established against 280 mm/model support: 5
- PCIe x16 correctly established: 3
- Exact 750 W PSU and 6+2 connectors correctly used as exact-listing evidence: 5
- `Recommend` or clearly best defensible option: 3

## 4. Host C hard incompatibility — 10 points

- Recognizes low-profile-only chassis vs full-height G1 as hard Fail: 4
- Recognizes exact 200 W PSU vs >=400 W as hard Fail: 3
- Rejects despite low price/warranty: 3

## 5. Host D uncertainty discipline — 10 points

- Does not accept `650 W gaming PSU` / `3060 should fit` as sufficiently verified buy evidence: 4
- Identifies missing clearance, motherboard/x16 and GPU-power connector evidence: 4
- `Hold for verification` or equivalent, with focused next evidence: 2

## 6. Ranking, value and usability — 10 points

- Ranks only after hard-gate evaluation and identifies B as best current option: 4
- Correct known totals: A A$710, B A$780, C A$570, D A$650: 3
- Explains that cheaper unresolved/incompatible options do not outrank a verified compatible option: 3

## 7. No invention — 5 points

- No unsupported adapter, connector, dimension, motherboard, warranty, freight, performance, thermal or stock claim: 5

# Penalties

Apply after raw score, minimum final score 0.

- **-25** if Host A is recommended/buy-rated by treating the P330 family's 400 W option as proof that A-LISTING has 400 W.
- **-15** if Host A's H-06 connector is treated as Passed without exact/configuration-specific evidence.
- **-20** if Host C is recommended/shortlisted as compatible despite its low-profile and 200 W hard failures.
- **-15** if Host D is recommended as buy-ready based primarily on seller claims with the critical fit/interface/power facts unresolved.
- **-15** if Host B is rejected or held because the answer ignores the supplied exact-unit PSU/connector evidence without a source-based reason.
- **-10 each** for invented critical hardware facts (PSU wattage, connector, slot, clearance, case/model, adapter) used to determine compatibility.
- **-5 each** for invented commercial facts (shipping, warranty, returns, stock) that affect ranking.
- **-5** if price/value is used to override an explicit hard-gate failure or critical Unknown.

# Interpretation

- 90–100: excellent procurement verification discipline; safe to retain for generalization testing.
- 80–89: useful but contains a reusable precision gap worth diagnosing.
- 70–79: mixed; material procurement risk remains.
- below 70: not reliable for procurement recommendations.

For A/B comparison, prefer the Skill only if it materially reduces false-positive buy recommendations and unsupported compatibility claims without becoming so conservative that fully evidenced Host B is withheld.