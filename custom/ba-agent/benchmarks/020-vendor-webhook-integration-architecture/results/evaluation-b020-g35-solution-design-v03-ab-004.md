# Benchmark 020 Evaluation — `design-technical-solution` v0.3.0

Job: `b020-g35-solution-design-v03-ab-004`  
Model: `gemini-3.5-flash`  
Temperature: `0.0`

## Score

| Run | Raw | Penalties | Final | Tokens | Decision |
|---|---:|---:|---:|---:|---|
| Baseline | 94 | 0 | **94/100** | 5,113 | Strong control; slightly cleaner and cheaper on this case. |
| `design-technical-solution` v0.3.0 | 93 | 0 | **93/100** | 7,354 | Safe cross-domain architecture, but no incremental value over this baseline. |

## Evaluation

Both runs preserve the roughly ten-minute automation outcome while rejecting only the unavailable webhook mechanism. Both select the supplied REST APIs, `updated_since`, stable `record_id`, idempotent upsert and existing dual-connected Linux host to produce the expected polling-adapter architecture. Neither invents a vendor webhook, recommends RPA, accepts the hourly CSV route as meeting the objective, or creates an unnecessary hardware procurement path.

Both runs also keep a restart-safe checkpoint, avoid advancing it after failed work, make retry through safe re-reading possible, and expose rate limits, change volume and credential handling as validation concerns. The baseline is marginally better because it offers a broader alternatives comparison and is less prescriptive in its final handoff.

The Skill run narrows several implementation choices without evidence: a local state file, `cron` or `systemd.timer`, `stderr`/host logging, and Python/Bash/container examples. It also says the ten-minute schedule meets the target before rate-limit and workload adequacy have been validated. Those choices are not used to fabricate feasibility and do not trigger a critical penalty, but they reduce architecture-to-implementation precision. Both runs could better expose pagination, mapping/deletion semantics, timestamp-ordering edge cases and operational ownership/alerting.

## Decision

**B020 closes cleanly as a same-model A/B comparison.** It demonstrates that v0.3 is safe in a software/integration domain and that the B019 hardware-specific invention does not recur as a material architecture failure. It does **not** demonstrate incremental Skill value over a strong baseline, so do not freeze v0.3 as validated and do not tune it against B020.

Retain v0.3 as the current candidate and proceed to the already-agreed third standalone domain before composition. The next test must be materially different, preserve an outcome while rejecting an impossible implementation, expose exact-unit compatibility Unknowns, and keep BA clarification and Procurement candidate verification downstream of architecture.
