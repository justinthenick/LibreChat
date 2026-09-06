# Autonomous A001–A004 Portfolio Completion Plan

Status date: 2026-09-06

## Objective

Complete the first four dynamic BA Agent orchestrators through independent evidence gates, then integrate only clean release candidates to `main` and `server/synology` without requiring routine user intervention.

## Control plane

- **NAS one-minute loop:** execution, operational retry/fallback, dynamic invocation, semantic evaluation, bounded Skill revision where already supported, diagnostics and result publication.
- **ChatGPT Skill Lab Autopilot:** hourly programme-level inspection and engineering: queue/control repair, new benchmark design, Agent defect correction, freeze/release decisions, PR review/integration and escalation only when a genuinely external/manual dependency remains.

## Non-negotiable quality policy

For each Agent release candidate:

1. routing/selectivity evidence must be credible;
2. true dynamic invocation must actually execute only the selected validated Skills in returned order;
3. at least one materially different independent generalization must pass;
4. semantic Skill/Agent score must be at least 90/100;
5. Agent must not trail the appropriate control by more than 10 points;
6. zero critical authority/evidence/state-preservation penalties are required;
7. failed or contaminated experiments remain preserved and are never reclassified as passes;
8. operational model fallback may step 3.7 -> 3.6 -> 3.5, but model shopping must never be used to escape a weak semantic result;
9. do not lower gates to hit a timeline.

## Current programme frontier

### A001 — BA Change Delivery Orchestrator

Routing, controlled composition, true dynamic invocation and independent selective generalization have passed. Treat as freeze candidate pending portfolio release packaging.

### A002 — Solution Procurement Orchestrator

Architecture-stop routing/dynamic gates passed. Procurement-only generalization dynamic run completed. The original fixed control was rejected because it lost candidate evidence between pipeline stages. The replacement evidence-preserving control is the only valid semantic comparison target.

Active corrected semantic job: `sem-a002-generalization-g37-004`.

### A003 — Release Assurance Orchestrator

Routing passed and true dynamic execution `a003-g37-dynamic-assurance-021` completed. The remaining wave is predeclared:

- fixed evidence-preserving control `b035-g37-a003-control-022`;
- dynamic semantic gate `sem-a003-dynamic-g37-002`;
- independent Benchmark 036 fixed control `b036-g37-a003-control-023`;
- independent dynamic run `a003-g37-generalization-023`;
- independent semantic gate `sem-a003-generalization-g37-003`.

### A004 — Requirement Change Orchestrator

Agent v0.1 and two independent benchmark shapes are seeded.

Benchmark 037 tests selective downstream propagation:

`reconcile-requirement-changes -> elaborate-acceptance-criteria -> derive-test-cases`

while deliberately skipping unnecessary requirements analysis, decomposition and change impact.

Benchmark 038 tests a materially different approved-but-incomplete auditor-access delta:

`reconcile-requirement-changes -> analyze-requirements -> assess-change-impact`

and requires a stop before decomposition/acceptance/test work until semantic Unknowns are resolved.

Active jobs include A004 routing, fixed controls, dynamic invocation and both semantic gates.

## Release decision

Do not promote merely because executions completed. After all required semantic artifacts exist:

1. inspect every Agent gate and critical penalty;
2. inspect route choice, ordering, stop discipline and token/complexity overhead;
3. revise an Agent only for an evidence-backed reusable defect;
4. rerun with a fresh ID after revision;
5. freeze Agent versions only when primary + generalization evidence is clean;
6. update evidence/timeline/workflow documentation;
7. open a focused PR from the workbench to `main`;
8. review changed files and merge only if the release package matches validated evidence;
9. reconcile `main` into `server/synology` using the documented branch model;
10. perform available deployment/health/smoke validation and preserve proof.

## Escalation boundary

Do not ask the user for routine approval, model choices, retry permission, queue changes, Agent edits, PR creation/merge, or release housekeeping within the above policy. Escalate only for a dependency that cannot be resolved with repository/NAS automation and would require a secret, account-side setting, DSM/manual operation, unavailable external authority, or a deliberate change to the quality policy.
