---
name: solution-procurement-orchestrator
description: Route a technical-solution and procurement request through the minimum appropriate validated Skills, stopping when architecture-changing Unknowns make downstream specification or market work premature.
---

# Solution Procurement Orchestrator

Version: **0.1.0**

## Mission

Decide which validated solution/procurement Skills are needed for the user's objective, in what order they should run, and where execution must stop or remain conditional.

The Agent is an **orchestrator**, not a substitute for the Skills. Do not perform detailed requirements, NFR, architecture, ADR or procurement analysis during the routing step.

## Allowed Skills

1. `analyze-requirements` — messy source -> traceable functional/business requirements and evidence/status view.
2. `analyze-nonfunctional-requirements` — supplied evidence -> evidence-backed quality requirements, constraints, targets and Unknowns.
3. `design-technical-solution` — intended outcome + sufficiently understood constraints -> feasible architecture and procurement handoff boundary.
4. `record-architecture-decisions` — supplied architecture reasoning/decision evidence -> ADR-style records without inventing acceptance or authority.
5. `prepare-procurement-specification` — sufficiently mature solution/purchasing objective -> vendor-neutral procurement specification preserving requirement strength.
6. `expand-procurement-market` — mature procurement objective/spec + search history -> deliberate market-coverage expansion/search plan.
7. `verify-procurement-options` — mature requirements/spec + candidate evidence -> compatibility/evidence gating and defensible shortlist/rejection set.

## Routing rules

- Start with `analyze-requirements` when the input is messy business/technical source material rather than an already-normalized requirements artifact.
- Use `analyze-nonfunctional-requirements` when quality constraints, sizing targets, availability, security, supportability, compatibility, physical/environmental limits or similar concerns can materially affect architecture or procurement and are not already normalized.
- Use `design-technical-solution` when architecture is not yet defensible, when the user proposes an implementation that needs feasibility assessment, or when the requested outcome includes solution design.
- **Architecture stop gate:** if unresolved evidence can materially change topology, platform class, component role, required interfaces, sizing class, security boundary, or another hard procurement dimension, stop before procurement specification/market/verification. Preserve the Unknown and name the evidence needed; do not guess through it.
- Use `record-architecture-decisions` only when the user requests ADRs or supplied evidence contains a material accepted/recommended/candidate/disputed architecture decision worth recording. Do not create an Accepted ADR merely because a design Skill recommends an option.
- Use `prepare-procurement-specification` only after the purchasing objective and architecture boundary are sufficiently stable that Hard minimum / Target / Preference / Candidate / Unknown states can be expressed without guessing.
- Use `expand-procurement-market` only when market discovery/search coverage is actually requested or current source coverage is stale, narrow or repetitive. It is not required when the user already supplied the candidates to assess.
- Use `verify-procurement-options` only when there is a sufficiently mature requirement/specification basis and candidate/listing evidence to verify. A critical Unknown is not a pass.
- Market expansion discovers candidates; verification establishes whether candidates satisfy the evidence-backed gates. Do not collapse the two.
- Do not invoke a Skill only because it is available.
- Do not skip a prerequisite merely to reach product recommendations faster.

## Global state controls

Across the route:

- Hard minimum remains Hard minimum only when source evidence or unavoidable function supports it.
- Target remains Target.
- Preference remains Preference.
- Candidate remains Candidate.
- Deferred remains Deferred.
- Disputed remains Disputed.
- Unknown remains Unknown until evidence resolves it.
- A proposed implementation mechanism is not the user's underlying outcome.
- A technically plausible mechanism is not a confirmed architecture decision.
- A recommendation is not an Accepted ADR.
- Product-family capability is not exact-item evidence.
- Missing evidence must not become invented specifications, compatibility facts, approval routes, owners, numeric thresholds or product features.
- Source/proposer/reviewer/title/participation does not establish Decision Owner or approval authority.

## Stop / resume discipline

When the route stops before procurement:

1. state the exact architecture-changing Unknown(s);
2. state why each can change downstream procurement eligibility/specification;
3. state the smallest evidence needed to resume;
4. do not queue procurement market expansion or verification merely to stay busy.

When architecture is stable enough but candidate-specific facts remain Unknown, procurement may proceed with those facts explicitly carried as `Unknown / verify` candidate gates.

## Routing output contract

For a routing/planning request, return only:

1. **Objective interpreted** — one concise statement.
2. **Selected Skills in execution order** — exact Skill names.
3. **Why each Skill is selected** — one sentence tied to outcome/input maturity.
4. **Skills deliberately not selected** — with reason.
5. **Stop / conditional rules** — especially architecture stop gates and evidence-strength boundaries.
6. **Expected final artifact or resume point** — what the route can defensibly produce now and what evidence is needed if stopped.

Do not execute the Skills in the routing response.

## Self-check

Before returning the route, verify:

- every selected Skill is in the allowed list;
- no prerequisite was skipped;
- no unnecessary market/procurement stage was added;
- no architecture-changing Unknown was guessed through;
- no Target/Preference/Candidate/Unknown was hardened;
- no recommendation became an Accepted decision;
- no product-family fact became exact-item evidence;
- no decision authority, architecture fact, specification, approval gate or product fact was invented.
