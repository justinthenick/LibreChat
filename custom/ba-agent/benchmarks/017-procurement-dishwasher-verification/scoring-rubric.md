# Benchmark 017 — Scoring Rubric

This file is evaluator-only and must not be sent to the model under test.

Score out of 100 before penalties.

## 1. Requirements and evidence discipline — 20 points

- Preserves H-01 through H-06 as hard gates and P-01 through P-04 as preferences: 8
- Distinguishes exact model/listing evidence, family capability, seller description and Unknown: 8
- Does not add new electrical/plumbing/noise/installation hard gates: 4

## 2. Candidate A family-vs-exact-model trap — 25 points

- Does not assume A-LISTING is HC60-B or another compliant family member: 10
- Correctly identifies capacity/exact model as unresolved: 4
- Correctly identifies depth as materially unresolved because HC60-PRO is 620 mm: 4
- Correctly identifies 10 A vs 15 A electrical requirement as materially unresolved: 4
- Uses `Hold for verification` or equivalent with exact model/rating-plate evidence requested: 3

## 3. Candidate B verified compatible recommendation — 20 points

- Correct landed total A$849 and budget Pass: 4
- Correctly establishes 14-place capacity: 3
- Correctly establishes 598/845/600 mm against the three fit limits: 6
- Correctly establishes exact-model 10 A electrical connection: 4
- `Recommend` or clearly best defensible option: 3

## 4. Candidate C explicit hard failures — 12 points

- Recognizes 605 mm width >600 mm: 3
- Recognizes 625 mm depth >610 mm: 3
- Recognizes exact 15 A rating fails 10 A hard gate: 3
- Rejects despite low price/noise/accessories: 3

## 5. Candidate D uncertainty discipline — 10 points

- Does not treat `standard 60 cm`, `about 84 cm`, `normal depth` or `normal wall plug` as exact proof: 5
- Identifies unresolved dimensions/electrical evidence and focused next verification: 3
- `Hold for verification` or equivalent: 2

## 6. Ranking and usability — 8 points

- Ranks B first after hard-gate evaluation: 3
- Keeps A/D unresolved rather than allowing lower price to win: 3
- Keeps noise/hose/warranty preferences subordinate to hard fit/electrical gates: 2

## 7. No invention — 5 points

- No unsupported adapter, circuit, plumbing, dimensions, electrical rating, installation, warranty or freight claims: 5

# Penalties

Apply after raw score, minimum final score 0.

- **-25** if Candidate A is recommended/buy-rated by assuming the ambiguous family listing is a compliant 14-place/10 A model.
- **-15** if Candidate A H-05 or H-06 is treated as Passed without exact-model evidence.
- **-20** if Candidate C is recommended/shortlisted despite explicit width/depth/15 A failures.
- **-15** if Candidate D is recommended as buy-ready based primarily on generic seller descriptions.
- **-15** if Candidate B is rejected or held despite supplied exact-model fit/capacity/electrical evidence without a source-based reason.
- **-10 each** for invented critical dimensions, electrical ratings, model identity or installation facts used to determine viability.
- **-5 each** for invented commercial facts that affect ranking.
- **-5** if price, low noise or accessories override an explicit hard-gate failure or critical Unknown.

# Interpretation

- 90–100: strong appliance-domain procurement verification; supports broader generalization of the Skill.
- 80–89: useful but contains a reusable precision gap worth diagnosing.
- 70–79: mixed; material procurement risk remains.
- below 70: not reliable for appliance procurement recommendations.

For A/B comparison, prefer the Skill only if it reduces false-positive recommendations and unsupported installation assumptions without withholding fully evidenced Candidate B.
