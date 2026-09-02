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

Purpose: prevent stale source loops by balancing exploitation of known-good markets with deliberate exploration of new source classes, geographies, condition classes and adjacent solution classes.

Default planning heuristic: approximately 80% exploitation / 20% exploration, adjusted when source quality/freshness warrants it.

This Skill does not fabricate live findings when no search tool is available; it produces the next search plan from the supplied search history.

## Benchmark sequence and current state

### B014 / P001 — Used workstation + GPU verification

Status: **queued; no result has published yet**.

Job: `b014-g35-procurement-verify-v01-ab-001`, Gemini 3.5 Flash, temperature `0.0`, baseline + `verify-procurement-options` v0.1.

Primary traps: family-level PSU option mistaken for exact-unit configuration, cheap-but-incompatible SFF host, unsupported seller claims, and the need to recommend a fully evidenced compatible host rather than becoming generically conservative.

Because the result has not appeared after multiple expected DSM poll cycles, do not queue a duplicate retry until NAS worker state is known. The benchmark assets and queue entry remain valid in GitHub.

### B015 / P002 — Apartment dining-table verification

Status: **prepared, deliberately not queued until B014 executes cleanly**.

Path: `custom/ba-agent/benchmarks/015-procurement-dining-table-verification`.

This is the first materially different cross-domain verification benchmark. It tests furniture-specific dimensions, six-seat configuration, flat-pack/access-path evidence and exact-variant discipline. Candidate B is fully evidenced and recommendable; Candidate A is an ambiguous family/variant Hold; Candidate C has explicit room/access failures; Candidate D relies on approximate seller claims.

Purpose: establish whether `verify-procurement-options` is genuinely domain-general rather than an IT compatibility prompt.

### B016 / P003 — Market expansion from stale search history

Status: **prepared, deliberately not queued until the verification track has at least one clean run**.

Path: `custom/ba-agent/benchmarks/016-procurement-market-expansion`.

This benchmark isolates `expand-procurement-market` v0.1. The supplied history is intentionally over-concentrated in eBay, Facebook Marketplace and Gumtree with declining novelty. The Skill must increase exploration beyond its default 20% when justified, add genuinely new source classes/geographies/solution classes, preserve hard buying constraints, define stop/refresh rules and avoid fabricating live listings.

### B017 / P004 — Rental-kitchen dishwasher verification

Status: **prepared, deliberately not queued until the earlier verification benchmarks establish the right Skill version**.

Path: `custom/ba-agent/benchmarks/017-procurement-dishwasher-verification`.

This is the appliance-domain generalization benchmark. It tests capacity, exact physical dimensions, electrical supply compatibility, included installation accessories as preferences, and another exact-model/family trap. Candidate B is the fully evidenced recommendable appliance; Candidate A is an ambiguous family Hold with both compliant and non-compliant family members; Candidate C has explicit width/depth/15 A failures; Candidate D relies on generic seller language such as `standard 60 cm` and `normal wall plug`.

Purpose: test whether the same evidence and hard-gate discipline survives a second non-IT domain with installation constraints.

## Domain generalization

The procurement spine is domain-general, but verification dimensions vary by category. The deliberate sequence is:

1. **B014 / P001 — IT:** used workstation + GPU compatibility and exact-unit evidence.
2. **B015 / P002 — furniture/home:** dimensions, access path, seating/configuration and exact-variant evidence.
3. **B017 / P004 — kitchen/appliance:** dimensions, capacity, electrical/installation compatibility and exact-model evidence.
4. **B016 / P003 — market expansion:** supplied stale search history; test whether the Skill expands source classes rather than merely rewriting queries.

Only after isolated Skills show reusable value should they be composed into a Procurement Analyst agent.

## Testing discipline

- Same model/settings for baseline vs Skill.
- Fixed evidence packet for verification benchmarks; no hidden web browsing.
- Gold standard and rubric remain evaluator-only.
- Penalize false-positive `buy/recommend` decisions more heavily than cautious but correct Holds.
- Do not reward excessive conservatism: a fully evidenced compatible candidate should still be recommendable.
- Test across materially different procurement domains.
- Test market discovery separately from candidate verification so search diversity and compatibility reasoning are not conflated.
- Do not queue later benchmarks merely to fill the worker; each next run should answer a specific generalization or defect question.

## Runner

No new NAS runner is required for the initial Skills. Benchmarks live under `custom/ba-agent/benchmarks/` and jobs are queued in the existing `custom/ba-agent/automation/jobs.json` so the existing DSM worker can refresh and execute them.

A future live-market agent benchmark may require a tool-enabled runner capable of real search/browsing. That is intentionally deferred until the fixed-packet reasoning Skills are validated.

## Worker observability improvement

The current worker keeps attempted-job state locally on the NAS. That makes remote diagnosis difficult when NAS access is unavailable. A planned harness improvement is to publish a **sanitised worker heartbeat/status** to the existing `nas-status` branch, containing only poll time, queue/job IDs, coarse outcome (`success`, `quota_blocked`, `provider_busy`, `failed`, `no_new_jobs`) and return code/error category. It must not publish environment values, API keys, raw prompts or unfiltered provider output.

Implement and deploy this separately from the procurement reasoning experiment so harness observability changes are not confused with Skill quality changes.
