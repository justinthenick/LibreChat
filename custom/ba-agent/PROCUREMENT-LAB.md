# Procurement / Specification Verification Lab

This track reuses the existing NAS benchmark harness to develop a domain-general procurement capability rather than performing one-off shopping decisions.

## Intended operating flow

`Objective -> Requirements -> Domain classification -> Market discovery -> Evidence collection -> Compatibility graph -> Verification -> Value scoring -> Recommendation -> Watch/refresh`

Unknowns remain Unknown. Compatibility and other hard gates are evaluated before price/value ranking.

## Initial Skill family

### `verify-procurement-options` v0.2

Purpose: verify supplied candidates/listings against evidence-backed hard gates and preferences, with exact-item configuration discipline and explicit `Recommend / Shortlist / Hold for verification / Reject / Watch` dispositions.

Core controls target two related failure modes:

1. **family capability is not exact-unit configuration**;
2. **one hard-gate result is not evidence for another hard gate**. A candidate may be rejected overall while other gates remain `Unknown`.

v0.2 was a focused correction from v0.1 after B014 showed an unsupported cross-gate inference: both baseline and v0.1 correctly rejected Host C for evidenced form-factor and PSU failures, but also asserted H-06 GPU-power-connector failure without independent connector evidence.

B014 v0.2 removed that defect, and B015 showed the same evidence discipline generalizes to furniture/access constraints. Retain v0.2.0; do not tune it further merely to chase preference-level wording unless another independent benchmark exposes a reusable safety problem.

### `expand-procurement-market` v0.1

Purpose: prevent stale source loops by balancing exploitation of known-good markets with deliberate exploration of new source classes, geographies, condition classes and adjacent solution classes.

Default planning heuristic: approximately 80% exploitation / 20% exploration, adjusted when source quality/freshness warrants it.

This Skill does not fabricate live findings when no search tool is available; it produces the next search plan from the supplied search history.

## Benchmark sequence and current state

### B014 / P001 — Used workstation + GPU verification

Status: **complete — `verify-procurement-options` v0.2.0 retained at 100/100 on the focused correction**.

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
- job `b014-g36-procurement-verify-v02-skill-004`
- `gemini-3.6-flash`, temperature `0.0`, Skill-only
- completed 17:07:08–17:07:36 Australia/Sydney; 8,579 total tokens
- final evaluation: **100/100, zero penalties**
- preserved B Recommend / A Hold / D Hold / C Reject while leaving C H-06 explicitly `Unknown` / not evidenced

Decision: retain v0.2.0 and move to cross-domain generalization.

### B015 / P002 — Apartment dining-table verification

Status: **complete — cross-domain generalization passed; v0.2.0 retained**.

Job: `b015-g36-procurement-verify-v02-ab-001`, `gemini-3.6-flash`, temperature `0.0`.

- baseline: 19:07:59–19:08:45, 6,142 tokens, **82/100** after penalty
- Skill v0.2.0: 19:08:45–19:09:43, 8,116 tokens, **95/100**

Both correctly recommend Candidate B, hold Candidate A and reject Candidate C. The key separation is Candidate D: the baseline promoted approximate dimensions and removable-leg language into an unsupported access failure and Reject; v0.2 correctly keeps D on `Hold for verification` with exact measurement/component evidence requested.

The Skill's only notable precision blemish was preference-level wording that treated Candidate A's “Natural Oak” title as evidence of timber/veneer material. That is unsupported by the packet, so the no-invention section was not awarded, but it did not affect hard-gate viability or ranking and did not trigger an explicit penalty.

Decision: the 13-point improvement on a materially different furniture/access benchmark is enough to treat `verify-procurement-options` v0.2.0 as cross-domain verified. Do not overfit another version to this isolated preference-level wording.

### B016 / P003 — Market expansion from stale search history

Status: **queued**.

Path: `custom/ba-agent/benchmarks/016-procurement-market-expansion`.

Job: `b016-g36-market-expand-v01-ab-001`, baseline + `expand-procurement-market` v0.1, `gemini-3.6-flash`, temperature `0.0`.

This benchmark isolates `expand-procurement-market` v0.1. The supplied history is intentionally over-concentrated in eBay, Facebook Marketplace and Gumtree with declining novelty. The Skill must increase exploration beyond its default 20% when justified, add genuinely new source classes/geographies/solution classes, preserve hard buying constraints, define stop/refresh rules and avoid fabricating live listings.

### B017 / P004 — Rental-kitchen dishwasher verification

Status: **prepared as a reserve second non-IT verification check**.

Path: `custom/ba-agent/benchmarks/017-procurement-dishwasher-verification`.

This appliance-domain benchmark tests capacity, exact physical dimensions, electrical supply compatibility, included installation accessories as preferences, and another exact-model/family trap. Candidate B is fully evidenced and recommendable; Candidate A is an ambiguous family Hold; Candidate C has explicit width/depth/15 A failures; Candidate D relies on generic seller language such as `standard 60 cm` and `normal wall plug`.

Use B017 only if B016 or later composition evidence gives a reason to seek a second non-IT verification control; otherwise keep it as reserve evidence.

## Domain generalization

The procurement spine is domain-general, but verification dimensions vary by category. Evidence so far:

1. **B014 / P001 — IT:** v0.2 corrected cross-gate evidence leakage and scored 100/100.
2. **B015 / P002 — furniture/home:** v0.2 improved 82→95 and correctly handled exact variant, dimensions, access path and seller approximation.
3. **B016 / P003 — market expansion:** now queued to test a different procurement capability: source expansion from stale history.
4. **B017 / P004 — kitchen/appliance:** reserve verification benchmark if another non-IT domain is warranted before composition.

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

The NAS worker is driven by a proven systemd timer every five minutes. `run_worker_once.sh` performs both the benchmark queue poll and a constrained diagnostic-request poll.

A GitHub-triggered diagnostic mechanism is available through `custom/ba-agent/automation/diagnostic-request.json`. Diagnostic recipes are allowlisted/read-only and publish sanitized results back under `custom/ba-agent/automation/diagnostic-results/`; repository content cannot supply arbitrary shell commands.

A future live-market agent benchmark may require a tool-enabled runner capable of real search/browsing. That remains deferred until the fixed-packet reasoning Skills are validated.
