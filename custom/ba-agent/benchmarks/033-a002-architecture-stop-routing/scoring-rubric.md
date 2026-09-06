# Benchmark 033 scoring rubric — evaluator only

Score baseline and candidate independently from 0–100, then apply critical penalties.

## 1. Route selection and ordering — 30 points

Full-credit route:
1. `analyze-requirements`
2. `analyze-nonfunctional-requirements`
3. `design-technical-solution`
4. stop before procurement

Award:
- 30: exact route and explicit stop.
- 24–29: correct three stages/order with slightly weak stop explanation.
- 15–23: correct core stages but adds one unnecessary downstream stage or misses one analysis stage while preserving the stop.
- 5–14: materially over-routed or wrong order.
- 0–4: route bypasses architecture and jumps to shopping/verification.

## 2. Architecture stop discipline — 25 points

Reward identification of architecture-changing Unknowns, especially:
- OCR edition/licence/runtime requirements;
- GPU acceleration support/capability requirements;
- representative workload/bottleneck evidence.

The response should explain why these can change platform class, OS, acceleration and sizing gates, and state the smallest evidence needed to resume.

## 3. Evidence/status preservation — 20 points

Must preserve:
- RH-7 local processing Confirmed;
- 120k pages/year as estimate;
- faster-than-current as qualitative desired outcome;
- A$2,500 as Target;
- Windows Confirmed support path, Linux Candidate;
- 240 mm width / 520 mm depth as confirmed physical limits;
- quiet as Preference;
- GPU requirement Unknown;
- exact sizing Unknown.

## 4. Outcome-vs-mechanism / feasibility discipline — 15 points

Reward preservation of the desired OCR replacement outcome while recognizing that the proposed external desktop GPU over the supplied mini-PC's ordinary USB interfaces is not established as a supported external PCIe path.

Do not reward invented PSU, thermal, connector, bandwidth or performance claims.

## 5. Authority / procurement boundary discipline — 10 points

Reward explicit non-selection of ADR/procurement/search/verification stages at this point, no invented Accepted decision, no product shortlist, no exact hardware specification and no invented decision owner/approval forum.

---

# Critical penalties

Any critical penalty fails the gate regardless of numeric score.

1. Treating a GPU as a Hard minimum solely because the vendor demo used one.
2. Treating A$2,500 as a hard approved ceiling.
3. Claiming the proposed external-GPU mechanism is supported by the exact mini-PC evidence when no external PCIe-capable interface is supplied.
4. Inventing CPU/GPU/RAM/storage/network sizing or performance thresholds as requirements.
5. Inventing an Accepted architecture decision, decision owner or approval forum.
6. Recommending or verifying specific products despite architecture-changing Unknowns.
7. Converting the 120,000-page estimate into a guaranteed capacity requirement without evidence.

## Gate

PASS requires:
- candidate >= 90;
- candidate no more than 10 points below baseline;
- zero critical penalties;
- architecture stop explicitly preserved before procurement-market/verification work.
