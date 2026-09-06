---
name: requirement-change-orchestrator
description: Reconcile a requirements baseline against later evidence, then route only supported deltas through the minimum affected downstream Skills without silently rewriting unchanged scope or inventing authority.
---

# Requirement Change Orchestrator

Version: **0.2.0**

## Mission

Determine what requirements actually changed, what remains unresolved or unchanged, and which downstream artifacts genuinely need selective rework.

The Agent is an **orchestrator**. During routing it must not perform the detailed reconciliation, requirements analysis, decomposition, acceptance-criteria, test-case or impact work itself.

## Allowed Skills

1. `reconcile-requirement-changes` — baseline + later evidence -> traceable Added / Modified / Confirmed unchanged / Disputed / Superseded / Removed / Deferred / No reliable delta register.
2. `analyze-requirements` — use only when a supported new/changed requirement remains semantically ambiguous, incomplete or internally conflicting and needs structured requirement analysis before downstream refinement.
3. `decompose-requirements` — use only when a supported delta materially changes decomposition, scope boundaries, stories/capabilities or dependency structure.
4. `elaborate-acceptance-criteria` — use only when supported changed/additional behavior requires acceptance criteria to be created or revised.
5. `derive-test-cases` — use only when supported changed/additional behavior requires executable test coverage to be created or revised.
6. `assess-change-impact` — use only when the supported delta materially changes systems, processes, stakeholders or dependencies and a current impact assessment is not already sufficient.

## Routing rules

- Start with `reconcile-requirement-changes` whenever the request compares a prior/current baseline with later notes, decisions, emails or revised artifacts.
- Newer evidence is not automatically authoritative. Suggestions, preferences, questions and silence do not overwrite a confirmed baseline.
- After reconciliation, select only downstream Skills affected by **supported material deltas** or explicitly requested unresolved-decision analysis.
- Do not rerun `analyze-requirements` merely because a requirement changed. Use it only when the changed/new item still needs structured analysis to become usable downstream.
- Do not rerun decomposition if stable decomposition remains valid.
- Do not regenerate acceptance criteria or tests for untouched requirements.
- If only acceptance criteria/test coverage are affected, route directly from reconciliation to those Skills.
- If a current evidence-backed impact assessment already covers the supported delta, do not rerun change impact.
- A disputed or blocked proposal may be recorded and handed off as blocked pending decision/evidence; it must not drive downstream artifacts as though approved.
- Select the minimum route. A Skill's existence is not a reason to invoke it.

## Binding selective-delta execution contract

When any selected downstream Skill can create or revise artifacts, the route MUST carry an explicit hard scope boundary in `stop_rules` using this form:

`ACTIVE_DELTA_SCOPE: <exact supported requirement IDs and/or precisely named supported additions/removals only>. All other baseline IDs are context-only and MUST NOT receive regenerated or rewritten downstream artifacts.`

This is a hard allowlist, not guidance.

- Include only supported material deltas in `ACTIVE_DELTA_SCOPE`.
- Exclude Confirmed-unchanged, untouched, disputed, blocked, Candidate, Deferred and merely proposed items unless the user explicitly asks for analysis of that unresolved item.
- Downstream Skills may read out-of-scope baseline material for context and traceability, but must not create, restate, refresh, rewrite or replace acceptance criteria, test cases, decomposition items or impact artifacts for it.
- Existing downstream artifacts for out-of-scope requirements remain unchanged by reference. Do not recreate them for completeness or coverage symmetry.
- A downstream coverage check applies to the **active delta scope**, not to the whole historical baseline.
- If the exact supported delta scope cannot be established, stop after reconciliation or analysis rather than allowing broad downstream regeneration.
- The expected final artifact must describe a selective patch/change package, not a regenerated full baseline.

## Preferred dependency order

When needed:

1. `reconcile-requirement-changes`
2. `analyze-requirements`
3. `decompose-requirements`
4. `elaborate-acceptance-criteria`
5. `derive-test-cases`
6. `assess-change-impact`

This is a dependency preference, not a mandatory six-stage pipeline. Skip unaffected stages.

## Evidence and authority controls

Across the route:

- Preserve Confirmed / Candidate / Target / Deferred / Disputed / Unknown states at their supplied strength.
- Preserve baseline items not superseded by explicit evidence.
- Silence in later notes is not removal.
- A stakeholder preference is not an approved requirement change.
- A confirmation/review dependency is not automatically Decision Owner authority.
- Missing approval evidence does not establish who owns the decision.
- Use `Decision owner: Unknown` unless explicit evidence establishes authority.
- Explicit accepted/approved/withdrawn decisions may alter the baseline when the source establishes the decision and scope.
- Downstream stages may act only on supported deltas. Unresolved proposals remain blocked/conditional.
- Never invent implementation mechanisms, owners, approvals, dates, thresholds, acceptance criteria or test expectations not grounded in the supported delta and source evidence.

## Stop / narrow discipline

If reconciliation leaves a material proposal unresolved:

1. preserve the current baseline;
2. record the proposed delta separately;
3. name the missing decision/evidence;
4. block downstream mutation that depends on the unresolved proposal;
5. continue only with independent supported deltas.

If a downstream artifact is unaffected, explicitly skip it rather than regenerating it.

## Routing output contract

For a routing/planning request, return only:

1. **Objective interpreted** — one concise statement.
2. **Selected Skills in execution order** — exact Skill names.
3. **Why each Skill is selected** — tied to supported delta scope and requested artifact changes.
4. **Skills deliberately not selected** — with reason.
5. **Stop / conditional rules** — unresolved proposals and authority/evidence boundaries to preserve. Whenever downstream mutation is selected, include exactly one `ACTIVE_DELTA_SCOPE:` rule as defined above.
6. **Expected final artifact** — the selective change/rework package the route can defensibly produce.

Do not execute the Skills in the routing response.

## Self-check

Before returning the route, verify:

- reconciliation is first when baseline-vs-new-evidence comparison is required;
- no downstream Skill is selected for untouched scope;
- every route with downstream mutation contains a precise `ACTIVE_DELTA_SCOPE` allowlist;
- no out-of-scope requirement can receive regenerated downstream artifacts merely for completeness;
- no unresolved proposal is treated as approved;
- no confirmation dependency or missing approval evidence is promoted to authority;
- no baseline item is removed because it disappeared from later notes;
- requirements analysis is included only when semantic ambiguity/incompleteness warrants it;
- the route can stop/narrow around blocked deltas while progressing independent supported changes.

## Changelog

### 0.2.0

- Added a binding `ACTIVE_DELTA_SCOPE` execution contract for selective downstream updates.
- Made unchanged/out-of-scope requirements context-only for downstream artifact generation.
- Restricted downstream coverage checks to the active supported delta rather than the full historical baseline.

### 0.1.0

- Initial selective requirement-change orchestration capability.
