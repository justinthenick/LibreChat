# Workflow Strengthening Lab

## Objective

Strengthen the existing BA -> solution -> procurement -> change workflow by adding narrow, independently benchmarkable capabilities at the seams where semantic drift, unsupported hardening, or weak evidence handoff is most likely.

## Priority capabilities

1. `audit-artifact-traceability`
2. `prepare-procurement-specification`
3. `analyze-nonfunctional-requirements`
4. `assess-change-impact`

These are Skills first. They are not new Agents. Each must demonstrate standalone value before being added to an Agent route.

## Engineering rules

- Benchmark baseline vs Skill on the same model and generation settings.
- Gold standard and scoring rubric remain evaluator-only.
- Do not tune a Skill merely to mirror one synthetic case; any correction must be generic.
- Candidate, Target, Deferred, Disputed and Unknown states must never be silently hardened.
- Source/proposer is never decision authority unless explicit evidence says so.
- Missing evidence may produce a question or `Not evidenced`; it may not become invented governance, approval, architecture, validation method, or mandatory gate.
- Record token/call cost as well as score.
- If a provider/model is quota-blocked or busy, create a fresh job ID on an alternate available model rather than waiting for quota reset. Do not silently mix models inside a paired A/B result.

## Model substitution discipline

Provider availability is operational, not experimental evidence. A blocked run has no quality score.

When `provider_busy` or `quota_blocked` occurs:

1. preserve the failed manifest as operational evidence;
2. create a new job ID;
3. move to another available model, including an older model if necessary;
4. keep baseline and Skill on the same substitute model;
5. evaluate only complete same-model comparisons.

Do not fallback for semantic failures, weak scores, or ordinary model output defects.

## Release gates

A Skill is eligible for release when it:

- passes its primary benchmark with zero critical semantic/authority penalties;
- clears a materially different generalization benchmark where the capability is high-risk or domain-sensitive;
- improves or materially stabilizes the simpler baseline enough to justify the extra instruction surface;
- has no known defect that would corrupt downstream evidence state.

## Planned Agent use

Once validated:

- `audit-artifact-traceability` becomes a cross-workflow assurance gate.
- `prepare-procurement-specification` sits between solution design and procurement search/verification.
- `analyze-nonfunctional-requirements` strengthens requirements and architecture inputs.
- `assess-change-impact` strengthens change-readiness and operational handoff.

These capabilities are intended to support a future Solution Architecture / Procurement Orchestrator and Delivery Assurance Orchestrator, but Agent construction waits for standalone evidence.