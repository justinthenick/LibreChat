# Benchmark 020 — Scoring Rubric

This file is evaluator-only and must not be sent to the model under test.

Score out of 100 before penalties.

## 1. Outcome vs mechanism separation — 15 points

- Preserves the ~10-minute automated-sync outcome while separating it from the proposed webhook mechanism: 8
- Does not reject the entire objective merely because webhook support is absent: 4
- States useful success criteria: 3

## 2. Feasibility and evidence accuracy — 20 points

- Correctly classifies vendor-native webhook delivery as infeasible from the supplied capabilities: 6
- Identifies absence of webhook/event/subscription support as the actual blocker: 5
- Correctly recognizes `updated_since`, stable `record_id` and internal idempotent upsert as enabling evidence: 5
- Does not invent vendor capabilities or unsupported connectivity: 4

## 3. Alternative architecture quality — 25 points

- Proposes a polling/adapter worker on the existing corporate host: 7
- Shows clear flow from vendor REST API through worker to internal REST API: 5
- Uses incremental polling rather than full blind rescans where appropriate: 4
- Uses stable identity/idempotent upsert to prevent duplicate mirror records: 4
- Selects the polling architecture with a defensible maintainability/freshness rationale: 3
- Gives at least one sensible alternative/fallback with trade-off: 2

## 4. State, failure and operability discipline — 15 points

- Includes a durable checkpoint/watermark or equivalent restart-safe synchronization state: 5
- Makes failures observable/retryable without inventing exact retry technology/policy: 4
- Avoids silently advancing state past failed work: 3
- Does not invent queue/database/scheduler products as mandatory architecture: 3

## 5. Unknowns, security and validation discipline — 15 points

- Keeps rate limit/change volume/pagination or equivalent workload adequacy as Unknowns to validate: 5
- Does not claim a polling cadence is definitely safe without rate-limit/volume evidence: 3
- Preserves credential/non-public-network evidence without inventing a secret-management or firewall product: 3
- Identifies useful mapping/deletion/operational Unknowns and turns them into validation tasks: 4

## 6. Handoff / no unnecessary procurement — 10 points

- Explicitly states no new hardware procurement is indicated from the supplied evidence: 4
- Produces an implementation capability handoff rather than product shopping: 4
- Keeps exact language/runtime/scheduler/secret-store choices downstream unless evidenced: 2

# Penalties

Apply after raw score, minimum final score 0.

- **-30** if a nonexistent vendor webhook/event endpoint is invented or recommended as available.
- **-20** if the answer says the overall automation outcome is impossible rather than designing the polling alternative.
- **-15** if the hourly CSV export is selected as the preferred design while claiming it satisfies the ~10-minute objective.
- **-10** if browser/RPA automation is preferred despite the supplied REST APIs.
- **-10 each** for invented critical API, rate-limit, network or security facts used to determine feasibility.
- **-10** if new hardware/product procurement is recommended without evidence the existing runtime host is insufficient.
- **-5** if an exact polling/retry interval is promoted as proven safe without rate-limit/volume validation.

# Interpretation

- 90–100: excellent cross-domain solution-architecture discipline; strong evidence the Skill generalizes beyond hardware.
- 80–89: useful but contains a reusable evidence/integration gap worth diagnosing.
- 70–79: mixed; material risk of invented integration capabilities or weak recovery design remains.
- below 70: unreliable integration architecture discipline.

For A/B comparison, prefer the Skill only if it materially improves outcome preservation, feasibility accuracy, evidence discipline, state/recovery design and the architecture-to-implementation boundary without unnecessary procurement.
