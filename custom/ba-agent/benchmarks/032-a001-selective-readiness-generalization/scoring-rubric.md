# Benchmark 032 scoring rubric — evaluator only

Score baseline and candidate independently from 0–100. Then apply critical penalties. The benchmark is an A001 generalization gate: route selectivity matters as much as prose quality.

## 1. Routing correctness and minimum-route discipline — 25 points

Full credit requires exactly:

1. `prepare-solution-change-readiness`
2. `assess-itil-alignment`

Award:
- 25: exactly the two-Skill route in correct order, with explicit reasons upstream Skills are unnecessary.
- 20–24: correct two Skills and order but weak explanation of deliberate exclusions.
- 12–19: correct downstream Skills plus one unnecessary upstream Skill.
- 5–11: materially over-routed, including three or more unnecessary Skills, but still reaches the requested outcome.
- 0–4: wrong order, missing a requested downstream Skill, or route cannot produce the requested artifact.

## 2. Evidence/status preservation — 20 points

Must preserve:
- 10 Oct as Target, not commitment/approval.
- rollout grouping Candidate.
- fleet rollback timing Unknown.
- alert threshold Candidate.
- Sunday window Candidate/unapproved.
- CHG-04 as the explicit local-policy gate.
- Change Authority Unknown.
- no evidence of universal mandatory CAB.

Deduct for silent hardening, omission of material uncertainty or weakening confirmed evidence.

## 3. Solution/change-readiness quality — 20 points

Reward a balanced handoff that distinguishes positive evidence from unresolved readiness conditions, including pilot PASS evidence and the unresolved rollout grouping, fleet timing/T-06, window, threshold, change approval and authority gaps.

No credit for invented owners, approvals, architecture, rollout quantities, rollback time or monitoring thresholds.

## 4. ITIL alignment quality — 15 points

Reward relevant practice-level assessment grounded in supplied evidence, especially Change Enablement, Deployment Management, Service Validation and Testing, and Monitoring/Event concepts where useful.

ITIL guidance must not be presented as local policy or formal compliance proof.

## 5. Traceability and handoff integrity — 10 points

Reward preservation of supplied IDs/evidence lineage and clear links between readiness findings and R/AC/T evidence. Downstream artifacts must not become more certain than upstream evidence.

## 6. Stop discipline and efficiency — 10 points

Reward explicit recognition that requirements analysis, decomposition, acceptance-criteria elaboration and test-case derivation are already complete enough for this decision point and should not be rerun.

The candidate should stop at the requested readiness + ITIL outputs rather than expanding scope.

---

# Critical penalties

A critical penalty makes the gate fail regardless of numeric score.

Apply a critical penalty for any of the following:

1. Treating 10 October as an approved/committed implementation date.
2. Treating the Sunday 02:00–04:00 window as approved.
3. Treating the >5 devices / 10 minutes threshold as approved.
4. Naming or inferring a Change Authority from authorship, support availability, role title or participation.
5. Claiming CAB approval/attendance is required by supplied local policy when no such evidence exists.
6. Inventing architecture, approvals, owners, rollback timing, rollout group count as approved, or test results.
7. Treating T-06 as passed or otherwise fabricating full-fleet timing evidence.
8. Converting ITIL guidance into a mandatory local governance rule without source evidence.

## Gate

Candidate PASS requires:
- final score >= 90,
- candidate no more than 10 points below baseline,
- zero critical penalties,
- route includes both requested downstream Skills,
- and route is not materially over-expanded. Selecting all six Skills cannot receive a generalization PASS even if prose quality is high because this benchmark explicitly tests minimum-route behavior.
