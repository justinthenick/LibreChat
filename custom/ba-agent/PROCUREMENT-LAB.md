# Procurement / Specification Verification Lab

This track reuses the existing NAS benchmark harness to develop a domain-general procurement capability rather than performing one-off shopping decisions.

## Intended operating flow

`Objective -> Requirements -> Domain classification -> Market discovery -> Evidence collection -> Compatibility graph -> Verification -> Value scoring -> Recommendation -> Watch/refresh`

Unknowns remain Unknown. Compatibility and other hard gates are evaluated before price/value ranking.

## Initial Skill family

### `verify-procurement-options` v0.2

Purpose: verify supplied candidates/listings against evidence-backed hard gates and preferences, with exact-item configuration discipline and explicit `Recommend / Shortlist / Hold for verification / Reject / Watch` dispositions.

Core controls now target two related failure modes:

1. **family capability is not exact-unit configuration**;
2. **one hard-gate result is not evidence for another hard gate**. A candidate may be rejected overall while other gates remain `Unknown`.

v0.2 is a focused correction from v0.1 after B014 showed an unsupported cross-gate inference: both baseline and v0.1 correctly rejected Host C for evidenced form-factor and PSU failures, but also asserted H-06 GPU-power-connector failure without independent connector evidence.

### `expand-procurement-market` v0.1

Purpose: prevent stale source loops by balancing exploitation of known-good markets with deliberate exploration of new source classes, geographies, condition classes and adjacent solution classes.

Default planning heuristic: approximately 80% exploitation / 20% exploration, adjusted when source quality/freshness warrants it.

This Skill does not fabricate live findings when no search tool is available; it produces the next search plan from the supplied search history.

## Benchmark sequence and current state

### B014 / P001 — Used workstation + GPU verification

Status: **focused v0.2 Skill-only correction queued on Gemini 3.6 Flash**.

Gemini 3.5 attempts:

- `b014-g35-procurement-verify-v01-ab-001` — baseline call returned `quota_blocked`; remaining A/B calls stopped deliberately.
- `b014-g35-procurement-verify-v01-ab-002` — baseline call returned `quota_blocked`; remaining A/B calls stopped deliberately.

Both failures were provider quota outcomes, not procurement-Skill results, and are not scoreable.

Clean Gemini 3.6 A/B:

- `b014-g36-procurement-verify-v01-ab-003`
- model `gemini-3.6-flash`, temperature `0.0`
- baseline + `verify-procurement-options` v0.1
- both calls completed successfully
- both made the correct overall decisions: Host B Recommend; Host A Hold; Host D Hold; Host C Reject
- both nevertheless inferred Host C H-06 connector failure without independent evidence, triggering the rubric's critical-fact invention concern
- Skill v0.1 added structure and evidence registers but did not materially improve safety over the strong baseline and used more tokens

Focused correction:

- `verify-procurement-options` revised to v0.2.0 with independent per-gate evidence discipline
- queued job `b014-g36-procurement-verify-v02-skill-004`
- model `gemini-3.6-flash`, temperature `0.0`, Skill-only
- pass condition: preserve B Recommend / A Hold / D Hold / C Reject while leaving C H-06 `Unknown` / not evidenced unless independently supported

If v0.2 clears the defect without regression and reaches the excellent range, retain it and move immediately to B015 cross-domain generalization.

### B015 / P002 — Apartment dining-table verification

Status: **prepared; next verification benchmark after a clean B014 v0.2 result**.

Path: `custom/ba-agent/benchmarks/015-procurement-dining-table-verification`.

This is the first materially different cross-domain verification benchmark. It tests furniture-specific dimensions, six-seat configuration, flat-pack/access-path evidence and exact-variant discipline. Candidate B is fully evidenced and recommendable; Candidate A is an ambiguous family/variant Hold; Candidate C has explicit room/access failures; Candidate D relies on approximate seller claims.

Purpose: establish whether `verify-procurement-options` is genuinely domain-general rather than an IT compatibility prompt.

### B016 / P003 — Market expansion from stale search history

Status: **prepared, deliberately not queued until the verification track has at least one clean cross-domain result**.

Path: `custom/ba-agent/benchmarks/016-procurement-market-expansion`.

This benchmark isolates `expand-procurement-market` v0.1. The supplied history is intentionally over-concentrated in eBay, Facebook Marketplace and Gumtree with declining novelty. The Skill must increase exploration beyond its default 20% when justified, add genuinely new source classes/geographies/solution classes, preserve hard buying constraints, define stop/refresh rules and avoid fabricating live listings.

### B017 / P004 — Rental-kitchen dishwasher verification

Status: **prepared as an optional second non-IT verification check**.

Path: `custom/ba-agent/benchmarks/017-procurement-dishwasher-verification`.

This appliance-domain benchmark tests capacity, exact physical dimensions, electrical supply compatibility, included installation accessories as preferences, and another exact-model/family trap. Candidate B is fully evidenced and recommendable; Candidate A is an ambiguous family Hold; Candidate C has explicit width/depth/15 A failures; Candidate D relies on generic seller language such as `standard 60 cm` and `normal wall plug`.

Use B017 if a second non-IT domain is needed before composition; otherwise retain it as reserve evidence.

## Domain generalization

The procurement spine is domain-general, but verification dimensions vary by category. The deliberate sequence is:

1. **B014 / P001 — IT:** used workstation + GPU compatibility and exact-unit evidence.
2. **B015 / P002 — furniture/home:** dimensions, access path, seating/configuration and exact-variant evidence.
3. **B017 / P004 — kitchen/appliance:** optional second verification domain for dimensions, capacity and electrical/installation compatibility.
4. **B016 / P003 — market expansion:** supplied stale search history; test whether the Skill expands source classes rather than merely rewriting queries.

Only after isolated Skills show reusable value should they be composed into a Procurement Analyst agent.

## Testing discipline

- Same model/settings for baseline vs Skill A/B comparisons.
- Focused defect corrections may use Skill-only reruns against the immediately preceding same-model A/B baseline.
- Fixed evidence packet for verification benchmarks; no hidden web browsing.
- Gold standard and rubric remain evaluator-only.
- Penalize false-positive `buy/recommend` decisions more heavily than cautious but correct Holds.
- Do not reward excessive conservatism: a fully evidenced compatible candidate should still be recommendable.
- Test across materially different procurement domains.
- Test market discovery separately from candidate verification so search diversity and compatibility reasoning are not conflated.
- Do not queue later benchmarks merely to fill the worker; each next run should answer a specific generalization or defect question.
- A provider quota block is an infrastructure outcome, not a model-quality score.
- When switching model because of quota, rerun both baseline and Skill on the replacement model rather than mixing models inside one A/B comparison.

## Runner and NAS automation

Benchmarks live under `custom/ba-agent/benchmarks/` and jobs are queued in `custom/ba-agent/automation/jobs.json`.

The NAS worker is now driven by a proven systemd timer every five minutes rather than relying on the unreliable DSM schedule window. `run_worker_once.sh` performs both the benchmark queue poll and a constrained diagnostic-request poll.

A GitHub-triggered diagnostic mechanism is available through `custom/ba-agent/automation/diagnostic-request.json`. Diagnostic recipes are allowlisted/read-only and publish sanitized results back under `custom/ba-agent/automation/diagnostic-results/`; repository content cannot supply arbitrary shell commands.

A future live-market agent benchmark may require a tool-enabled runner capable of real search/browsing. That is intentionally deferred until the fixed-packet reasoning Skills are validated.
