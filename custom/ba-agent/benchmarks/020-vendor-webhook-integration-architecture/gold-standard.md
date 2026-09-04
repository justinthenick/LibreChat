# Benchmark 020 — Gold Standard

This file is evaluator-only and must not be sent to the model under test.

## Overall conclusion

The user's automation **outcome is feasible**, but the proposed mechanism of configuring an outbound webhook in the vendor SaaS is **infeasible from the supplied capabilities** because the vendor exposes no webhook/event/subscription mechanism.

The preferred design is a small **polling integration worker** on the existing corporate Linux VM/container host:

`Vendor SaaS REST API -> polling/adapter worker -> internal REST API`

The worker should query vendor records incrementally using `updated_since`, use stable `record_id` as the internal `external_id`, and perform idempotent upserts into the internal system. The existing runtime host already has the required network reachability, so no hardware procurement is indicated.

## Expected feasibility reasoning

A strong answer should state:

1. Direct webhook delivery is unavailable because the vendor has no outbound webhook/event/subscription feature.
2. This blocks the proposed mechanism, not the automation objective.
3. The vendor read API plus `updated_since`, stable `record_id`, timestamps and the internal idempotent upsert API provide the necessary primitives for incremental synchronization.
4. The existing corporate host can reach both systems and is therefore a sensible integration boundary.
5. The hourly CSV export is technically usable as a fallback but cannot normally satisfy the roughly 10-minute freshness objective.
6. Browser automation/RPA is unnecessary and less maintainable because supported APIs are available.

Do not add fictional webhook endpoints or other unsupported vendor capabilities.

## Preferred architecture

### Integration worker role

- runs on the existing always-on corporate Linux VM/container host;
- authenticates outbound to the vendor using the supplied OAuth client-credentials capability;
- requests records changed since a durable checkpoint/watermark using `updated_since`;
- transforms/maps fields required by the internal mirror record;
- upserts to the internal system using vendor `record_id` as `external_id`;
- advances its synchronization checkpoint only after the corresponding work has been safely processed;
- emits sufficient operational logging/status so failures are observable and can be retried.

The answer does not need to prescribe a specific language, queue, database, scheduler, container platform or secret store.

## Polling cadence discipline

The user accepts polling if changes normally arrive within roughly 10 minutes, but the packet does not provide the vendor rate limit or change volume.

A strong answer may propose a **candidate polling cadence within the 10-minute objective** only if clearly labelled subject to rate-limit/volume validation. It should not declare, for example, that 5-minute polling is definitely safe from the supplied evidence.

## State / idempotency / recovery

Useful design points include:

- stable vendor `record_id` mapped to internal `external_id`;
- idempotent upsert means a repeated poll does not need to create duplicates;
- retain a durable last-success watermark/checkpoint so restarts do not lose the polling position;
- overlap/re-read around the checkpoint may be proposed as a robustness option, but exact overlap duration must not be invented as a requirement;
- failed records should remain visible/retryable rather than being silently skipped;
- exact retry count/backoff/dead-letter technology remains an implementation choice unless further evidence is supplied.

## Security boundary

The evidence supports:

- credentials are not embedded in source code;
- the worker needs authenticated access to both APIs;
- the worker sits inside the corporate LAN and initiates outbound HTTPS to the vendor.

Do not invent a required secret-management product, firewall rule, identity provider, certificate scheme or public inbound endpoint.

## Important Unknowns / validation actions

A strong answer should identify architecture-relevant Unknowns such as:

- vendor API rate limits and whether a candidate <=10-minute polling cadence is permitted at expected volume;
- expected number of changed records per interval / pagination behavior if relevant;
- exact field mapping and mandatory internal fields;
- deletion/cancellation semantics if mirrored records can later disappear or be withdrawn;
- timestamp/checkpoint edge cases and ordering guarantees;
- operational ownership/alerting expectations;
- exact credential storage mechanism approved for the existing host.

These should become verification or implementation tasks, not invented facts.

## Alternatives

Useful alternatives may include:

- hourly scheduled CSV export: lower implementation complexity but fails the desired freshness target under normal operation;
- future vendor-native webhook capability: preferable if the vendor later supplies it, but not available now;
- managed integration/iPaaS: conceptually possible, but unnecessary to require or procure from the supplied evidence and may introduce unresolved corporate-network/security questions;
- RPA/browser automation: not preferred because supported APIs already exist.

## Handoff conclusion

A strong answer should explicitly state that **no hardware procurement is required from the current evidence**. The next step is an implementation/design validation handoff, not product shopping.

The implementation handoff should specify capabilities rather than products: scheduled incremental REST polling, OAuth client credentials, checkpoint state, mapping, idempotent upsert, observable retries, and secure credential injection/storage using the organization's approved mechanism once identified.

## Forbidden errors

- inventing a webhook/event endpoint;
- saying the overall automation objective is impossible because webhook support is absent;
- recommending the hourly CSV export as though it meets the ~10-minute target;
- using browser automation/RPA as the preferred design despite supported APIs;
- inventing API rate limits, record volumes, exact retry/backoff values, queue/database products or secret-store products;
- requiring new hardware or jumping into product procurement without evidence that the existing host is insufficient.
