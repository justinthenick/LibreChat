# Benchmark 027 Evaluation — Change Impact Assessment

Evaluator-only record. Raw model outputs remain unchanged.

## Common control

- Model: `gemini-3.6-flash`
- Temperature: `0.0`
- Baseline: 2026-09-05 00:54:19–00:55:22 Australia/Sydney, 3,129 total tokens
- Baseline score: **98/100**, zero critical penalties

The baseline correctly preserved the mobile dependency as unverified, OIDC fallback as unresolved, reporting identifier mapping as undecided, payroll/API non-impacts, contractor deferral, Security authority uncertainty, unsupported CAB wording, and the implementation window as an unapproved planning target. Its main weakness was `Formalize implementation window approvals`, which subtly presumed an approval workflow that the source did not establish.

## Skill v0.1

- Execution: 2026-09-05 00:55:22–00:57:08 Australia/Sydney
- Total tokens: 6,424
- Score: **97/100**, zero critical penalties

v0.1 preserved the scored source states but showed two reusable defects: it labelled wholly unreferenced infrastructure/security domains as `not impacted/out of scope`, and it turned an unapproved planning Target into an instruction to obtain formal approval. v0.1 was not retained.

## Skill v0.2 focused rerun

- Job: `b027-g36-change-impact-v02-skill-002`
- Execution: 2026-09-05 07:27:19–07:27:59 Australia/Sydney
- Total tokens: 6,516
- Score: **95/100**, zero critical penalties

Breakdown:

- A. Confirmed direct impacts: 30/30
- B. Candidate / Unknown discipline: 20/20
- C. Non-impact / exclusion discipline: 20/20
- D. Governance / planning-state integrity: 15/15
- E. Risks / handoff quality: 10/15

The focused correction worked: unreferenced infrastructure is no longer asserted as non-impact, and Sunday 22:00–23:00 remains explicitly non-binding/unapproved rather than becoming an approval task. Mobile remains Candidate, fallback and identifier mapping remain unresolved, payroll/API remain explicitly unchanged, and Security/CAB are not presented as established authority/gates.

A smaller handoff tendency remains: the output assigns `Verification target` roles such as Solution Designer/Data Lead, Operations/Service Owner and Project Manager/Governance Lead, calls unresolved items `Non-Blocking Tasks` without evidence that they are non-blocking, and introduces `training` wording in the confirmed implementation scope. These are not status/authority promotions under the B027 critical rubric and do not invalidate the primary gate, but they are explicit generalization watch-items.

## Decision

**Primary B027 gate passed at v0.2.** Do not tune the same synthetic packet again. Retain v0.2 as the candidate for a materially different generalization benchmark that specifically tests:

- no inferred verification/action owners;
- no unsupported blocker/non-blocker classification;
- no implementation/training/communications tasks invented from an impact statement;
- preservation of explicit non-impacts versus merely unassessed domains.

Only after that generalization passes should `assess-change-impact` enter the Delivery Assurance Agent route.
