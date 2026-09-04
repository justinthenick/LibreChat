# Benchmark 015 — Scoring Rubric

This file is evaluator-only and must not be sent to the model under test.

Score out of 100 before penalties.

## 1. Requirements and evidence discipline — 20 points

- Preserves H-01 through H-05 as hard gates and P-01 through P-04 as preferences: 8
- Distinguishes exact listing/model evidence, family evidence, seller approximation/claim and Unknown: 8
- Does not silently add new room, chair, assembly or material hard gates: 4

## 2. Candidate A family-vs-exact-variant trap — 25 points

- Does not assume A-LISTING is the six-seat A-180E variant: 10
- Correctly identifies exact seating/variant as unresolved: 5
- Correctly identifies H-05 component-width/access evidence as unresolved despite family flat-pack claim: 6
- Uses `Hold for verification` or equivalent and asks for exact variant plus component-width evidence: 4

## 3. Candidate B verified compatible recommendation — 20 points

- Correct landed total A$580 and budget Pass: 4
- Correctly establishes six-seat suitability from exact model evidence: 4
- Correctly establishes 85 cm width and 170 cm length against hard limits: 5
- Correctly establishes flat-pack/access from 74 cm widest rigid component: 4
- `Recommend` or clearly best defensible option: 3

## 4. Candidate C explicit hard failures — 12 points

- Recognizes 100 cm tabletop width exceeds 90 cm hard gate: 5
- Recognizes one-piece 100 cm tabletop fails 78 cm access gate: 4
- Rejects despite low price: 3

## 5. Candidate D uncertainty discipline — 10 points

- Does not treat “about 175 x 88”, “seats six comfortably” or “should fit” as exact proof: 5
- Identifies unresolved dimensions/access and gives focused verification action: 3
- `Hold for verification` or equivalent: 2

## 6. Ranking and usability — 8 points

- Ranks B first after hard-gate evaluation: 3
- Keeps A/D as unresolved rather than treating them as cheaper winners: 3
- Explains that cost/material preference cannot override hard fit/access uncertainty or failure: 2

## 7. No invention — 5 points

- No unsupported room geometry, chair size, component dimensions, material, delivery, warranty or assembly facts: 5

# Penalties

Apply after raw score, minimum final score 0.

- **-25** if Candidate A is recommended/buy-rated by assuming the ambiguous family listing is the six-seat A-180E variant.
- **-15** if Candidate A H-05 is Passed merely because the family is described as flat-pack.
- **-20** if Candidate C is recommended/shortlisted despite the explicit 100 cm room-width and access failures.
- **-15** if Candidate D is recommended as buy-ready based primarily on approximate seller statements.
- **-15** if Candidate B is rejected or held despite the supplied exact-model six-seat/dimension/access evidence without a source-based reason.
- **-10 each** for invented critical dimensions, seating capacity, component widths or access facts used to determine viability.
- **-5 each** for invented commercial facts that affect ranking.
- **-5** if low price or a material preference overrides an explicit hard-gate failure or critical Unknown.

# Interpretation

- 90–100: strong cross-domain procurement verification; supports generalization of the Skill.
- 80–89: useful but contains a reusable precision gap worth diagnosing.
- 70–79: mixed; material procurement risk remains.
- below 70: not reliable for cross-domain procurement recommendations.

For A/B comparison, prefer the Skill only if it reduces false-positive recommendations and unsupported fit/access assumptions without withholding fully evidenced Candidate B.
