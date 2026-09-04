# Manuscript Engineering M001 — Provisional Skill-Only Evaluation

Job: `m001-g36-manuscript-structure-v01-ab-001`  
Model: `gemini-3.6-flash`  
Skill: `analyze-manuscript-structure` v0.1.0  
Comparison status: **provisional — baseline unavailable because Gemini returned provider_busy**

## Score

| Category | Score |
|---|---:|
| Manuscript-level reconstruction | 15/15 |
| Chapter-by-chapter fidelity | 18/20 |
| Evidence and uncertainty discipline | 18/25 |
| Character / relationship reconstruction | 7/10 |
| Chronology and causal discipline | 9/10 |
| Motifs / themes with correct confidence | 9/10 |
| Continuity / unresolved-thread register | 3/5 |
| Editorial-brief seed and scope discipline | 4/5 |
| **Raw** | **83/100** |
| Penalty: Peter Rusk / RUSK CIVIL relationship promoted to established fact | **-15** |
| **Provisional final** | **68/100** |

## What worked

The Skill reconstructs the five-chapter investigation spine well, preserves Jonah's unresolved fate, keeps the radio voice and `D` formally unresolved in its uncertainty table, captures the 16/17 and 22:14/22:17 discrepancies, and stays within reconstruction-only scope. It also produces a useful chapter map, chronology, uncertainty register and author-confirmation list.

## Material defect

The main failure is **claim-provenance promotion**. The output states that Peter Rusk is a `head/operator associated with RUSK CIVIL`, even though the manuscript only establishes that `RUSK CIVIL` is written beside two registration numbers in Jonah's notebook, that Peter was municipal engineer, that Peter ordered Theo to remain silent, and that Peter rewrote the technical appendix. Ownership, operation or formal relationship between Peter and `RUSK CIVIL` is not established.

That error is important because the benchmark is specifically intended to create a safe factual substrate for downstream editing. Once an inferred entity relationship is placed in the character map as an explicit fact, later editing agents could silently propagate it as canon.

There are related smaller provenance leaks:

- `E.V.` is treated as definitively Elise rather than preserving that Mara interprets the initials that way;
- Daniel Devlin is described as mayor during the historic storm although only his present mayoral role and historic report-signing are established;
- `RUSK CIVIL` is described as having performed illegal dumping rather than preserving the narrower notebook evidence linking the label to two recorded registrations while dumping is observed;
- the brief calls the municipal report `falsified`, which is stronger than the supplied amendment / false-route evidence alone proves;
- the hospital/radio-warmth item is placed in a contradiction register even though the text only weakens one explanation rather than creating a true contradiction.

## Decision

**Do not promote M001 v0.1 to downstream chapter editing yet.** The overall structural reconstruction is strong, but the Skill currently has exactly the failure mode this track is meant to prevent: an inference can be upgraded into manuscript canon.

Do not patch the Skill until a valid baseline is available. The next version, if still warranted after A/B comparison, should address the generic issue rather than this story specifically: every character/entity relationship and causal claim should retain provenance and confidence, and initials, labels, adjacency in documents, and character interpretation must never become identity/ownership/culpability facts without explicit evidence.
