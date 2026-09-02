# Procurement / Specification Verification Lab

This track reuses the existing NAS benchmark harness to develop a domain-general procurement capability rather than performing one-off shopping decisions.

## Intended operating flow

`Objective -> Requirements -> Domain classification -> Market discovery -> Evidence collection -> Compatibility graph -> Verification -> Value scoring -> Recommendation -> Watch/refresh`

Unknowns remain Unknown. Compatibility and other hard gates are evaluated before price/value ranking.

## Initial Skill family

### `verify-procurement-options` v0.2.0

Purpose: verify supplied candidates/listings against evidence-backed hard gates and preferences, with exact-item configuration discipline and explicit `Recommend / Shortlist / Hold for verification / Reject / Watch` dispositions.

Core controls:

1. **family capability is not exact-unit configuration**;
2. **one hard-gate result is not evidence for another hard gate**. A candidate may be rejected overall while other gates remain `Unknown`.

B014 v0.2 removed an unsupported cross-gate connector inference and scored 100/100. B015 then generalized the same discipline to furniture/access constraints, improving baseline 82/100 to Skill 95/100. Retain v0.2.0; do not tune it further merely to chase isolated preference-level wording.

### `expand-procurement-market` v0.1.0

Purpose: prevent stale source loops by balancing exploitation of known-good markets with deliberate exploration of new source classes, geographies, condition classes and adjacent solution classes.

Default planning heuristic: approximately 80% exploitation / 20% exploration, adjusted when source quality/freshness warrants it.

The Skill does not fabricate live findings when no search tool is available; it produces the next search plan from supplied search history.

B016 confirmed that the method itself is sound, but **did not establish measurable Skill value**: baseline and Skill both scored 100/100. Therefore v0.1.0 is not yet frozen and is being challenged with a harder mixed-history cross-domain benchmark rather than tuned against an easy control.

## Benchmark sequence and current state

### B014 / P001 — Used workstation + GPU verification

Status: **complete — `verify-procurement-options` v0.2.0 retained at 100/100**.

Relevant run: `b014-g36-procurement-verify-v02-skill-004`, `gemini-3.6-flash`, temperature `0.0`, Skill-only.

- completed 17:07:08–17:07:36 Australia/Sydney;
- 8,579 total tokens;
- final evaluation **100/100, zero penalties**;
- preserved B Recommend / A Hold / D Hold / C Reject;
- corrected the reusable defect by leaving Host C H-06 explicitly `Unknown` / not evidenced rather than inferring failure from unrelated evidence.

Decision: retain v0.2.0 and move to cross-domain verification.

### B015 / P002 — Apartment dining-table verification

Status: **complete — cross-domain generalization passed; v0.2.0 retained**.

Job: `b015-g36-procurement-verify-v02-ab-001`, `gemini-3.6-flash`, temperature `0.0`.

- baseline: 19:07:59–19:08:45, 6,142 tokens, **82/100** after penalty;
- Skill v0.2.0: 19:08:45–19:09:43, 8,116 tokens, **95/100**.

The important separation was Candidate D. The baseline promoted approximate seller dimensions/removable-leg language into an unsupported access failure and Reject; v0.2 correctly kept D on `Hold for verification` pending exact measurement/component evidence. Candidate B remained Recommend, A Hold and C Reject.

Decision: the 13-point improvement on a materially different furniture/access benchmark is sufficient to treat verification v0.2.0 as cross-domain verified.

### B016 / P003 — Market expansion from stale search history

Status: **complete — method passed, Skill value not demonstrated**.

Job: `b016-g36-market-expand-v01-ab-001`, baseline + `expand-procurement-market` v0.1.0, `gemini-3.6-flash`, temperature `0.0`.

- baseline: 20:53:37–20:54:10, 4,491 tokens, **100/100**, zero penalties;
- Skill v0.1.0: 20:54:10–20:54:37, 5,091 tokens, **100/100**, zero penalties.

Both correctly recognized the eBay/Facebook/Gumtree search loop as stale, moved to roughly 30% exploitation / 70% exploration, added genuine new channel classes, preserved hard buying constraints, defined stop/watch logic and avoided fabricated live findings.

The Skill output was more systematic but did not improve the rubric score and used 600 more tokens (about 13% more). This means B016 is evidence that the **approach works**, not evidence that the Skill materially improves Gemini 3.6 Flash on an obvious stale-history case.

Decision: **do not tune or freeze v0.1.0 from B016 alone**. Challenge it with a harder mixed-history benchmark.

### B017 / P004 — Rental-kitchen dishwasher verification

Status: **prepared as a reserve second non-IT verification check**.

Path: `custom/ba-agent/benchmarks/017-procurement-dishwasher-verification`.

Use B017 only if later composition evidence gives a specific reason to seek another verification-domain control. Verification already has strong IT + furniture generalization evidence, so B017 is deliberately not the next test.

### B018 / P005 — Mixed-history compact treadmill market expansion

Status: **queued — harder generalization test for `expand-procurement-market` v0.1.0**.

Path: `custom/ba-agent/benchmarks/018-procurement-market-expansion-mixed-history`.

Job: `b018-g36-market-expand-v01-ab-001`, baseline + Skill v0.1.0, `gemini-3.6-flash`, temperature `0.0`.

B018 is deliberately different from B016:

- the history is **mixed**, not globally stale;
- Rebel Sport and Fitness Warehouse remain productive and should continue to receive meaningful exploitation effort;
- Facebook Marketplace and Gumtree are stale/noisy and should be reduced to passive or low-frequency watch behavior;
- Amazon Australia remains useful but requires seller/origin/electrical filtering;
- exploration must add genuinely new Australian source classes without overcorrecting to novelty;
- tempting US/110 V, overseas-direct, non-incline walking-pad and oversized treadmill paths explicitly violate hard constraints and should be rejected;
- the expected balance is roughly 60/40 or 65/35 exploit/explore rather than mechanically repeating either 80/20 or B016's 30/70.

Decision rule: if v0.1 materially improves calibration over baseline with no reusable defect, retain it for composition. If baseline is again equally strong, consider the Skill redundant rather than tuning merely to manufacture a score delta.

## Composition gate

The first Procurement Analyst composition benchmark should begin only after the B018 decision. The intended composition must test **Skill selection and sequencing**, not just whether each isolated Skill works:

`request -> classify domain/state -> decide discovery vs verification -> expand market if needed -> verify supplied/discovered candidates -> rank only after hard gates -> preserve Unknowns -> recommend/watch/hold`

The composition benchmark should include cases where the agent should use:

- verification only;
- expansion only;
- both expansion and verification in sequence.

B017 remains reserve evidence rather than a mandatory gate.

## Testing discipline

- Same model/settings for baseline vs Skill A/B comparisons.
- Focused defect corrections may use Skill-only reruns against the immediately preceding same-model A/B baseline.
- Fixed evidence packet for reasoning benchmarks; no hidden web browsing.
- Gold standard and rubric remain evaluator-only.
- Penalize false-positive buy/recommend decisions and hard-constraint relaxation heavily.
- Do not reward excessive conservatism when a candidate is fully evidenced.
- Separate market discovery from candidate verification during isolated Skill testing.
- Do not queue later benchmarks merely to fill the worker; each next run answers a specific generalization or architecture question.
- A provider quota block is infrastructure, not a quality score.
- When switching model because of quota, rerun both baseline and Skill on the replacement model rather than mixing models inside one A/B comparison.

## Runner and NAS automation

Benchmarks live under `custom/ba-agent/benchmarks/` and jobs are queued in `custom/ba-agent/automation/jobs.json`.

The NAS worker is driven by the proven systemd timer every five minutes. `run_worker_once.sh` performs both benchmark queue polling and constrained diagnostic-request polling.

A GitHub-triggered diagnostic mechanism is available through `custom/ba-agent/automation/diagnostic-request.json`. Diagnostic recipes are allowlisted/read-only and publish sanitized results under `custom/ba-agent/automation/diagnostic-results/`; repository content cannot supply arbitrary shell commands.

A future live-market agent benchmark may require a tool-enabled runner capable of actual search/browsing. That remains deferred until fixed-packet reasoning and composition behavior are validated.
