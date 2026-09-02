# Procurement / Specification Verification Lab

This track reuses the existing NAS benchmark harness to develop a domain-general procurement capability rather than performing one-off shopping decisions.

## Intended operating flow

`Objective -> Requirements -> Domain classification -> Market discovery -> Evidence collection -> Compatibility graph -> Verification -> Value scoring -> Recommendation -> Watch/refresh`

Unknowns remain Unknown. Compatibility and other hard gates are evaluated before price/value ranking.

## Initial Skill family

### `verify-procurement-options` v0.1

Purpose: verify supplied candidates/listings against evidence-backed hard gates and preferences, with exact-item configuration discipline and explicit `Recommend / Shortlist / Hold for verification / Reject / Watch` dispositions.

Key failure mode targeted first: **family capability is not exact-unit configuration**.

### `expand-procurement-market` v0.1

Purpose: prevent stale source loops by balancing exploitation of productive sources with deliberate exploration of new source classes, geographies, condition classes and adjacent solution classes.

Default planning heuristic: approximately 80% exploitation / 20% exploration, adjusted when source quality/freshness warrants it.

This Skill does not fabricate live findings when no search tool is available; it produces the next search plan from the supplied search history.

## Domain generalization

The procurement spine is domain-general, but verification dimensions vary by category. Early generalization benchmarks should deliberately cross domains rather than overfit to IT:

1. **B014 / P001 — IT:** used workstation + GPU compatibility and exact-unit evidence.
2. **Next verification benchmark — furniture/home:** dimensions, access path, load/fit/assembly and condition evidence.
3. **Next verification benchmark — kitchen/appliance:** dimensions, utilities, ventilation/installation/capacity and commercial evidence.
4. **Market expansion benchmark:** supplied stale search history across repeated sources; test whether the Skill expands source classes rather than merely rewriting queries.

Only after isolated Skills show reusable value should they be composed into a Procurement Analyst agent.

## Testing discipline

- Same model/settings for baseline vs Skill.
- Fixed evidence packet for verification benchmarks; no hidden web browsing.
- Gold standard and rubric remain evaluator-only.
- Penalize false-positive `buy/recommend` decisions more heavily than cautious but correct Holds.
- Do not reward excessive conservatism: a fully evidenced compatible candidate should still be recommendable.
- Test across materially different procurement domains.
- Test market discovery separately from candidate verification so search diversity and compatibility reasoning are not conflated.

## Runner

No new NAS runner is required for the initial Skills. Benchmarks live under `custom/ba-agent/benchmarks/` and jobs are queued in the existing `custom/ba-agent/automation/jobs.json` so the existing DSM worker can refresh and execute them.

A future live-market agent benchmark may require a tool-enabled runner capable of real search/browsing. That is intentionally deferred until the fixed-packet reasoning Skills are validated.