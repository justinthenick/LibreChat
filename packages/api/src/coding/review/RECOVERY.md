# Bounded review response recovery

## Architecture decision

Inspected the existing preview lifecycle in the clean worktree
`/home/justin_kemp/LibreChat-openhands-preview-jobs`, commit
`8a1796e68bda18ba6010b120228fec74a6368211`. Its Python `job_store.py`
provides private SQLite state, exclusive ownership, atomic transitions and restart
interruption. `jobs.py` and `job_worker.py` bind that state to preview generation IDs,
execution profiles and execution-evidence results. This code is outside the review
stack. Reusing its runtime directly would require cross-runtime lifecycle ownership
and a different execution/result contract. It was inspected read-only, not copied.

Also inspected chat `IJobStoreV2`, `InMemoryJobStore`/`RedisJobStore` and capability
checks. They own chat generations, streams, checkpoints and approvals. A review is
not a chat generation. Neither store is imported and no generic queue/store is added.

Instead, extend the existing review ownership map with its request and bounded
terminal result. Retain the same single worker, authorization, limits, cancellation
and cleanup. This closes delivery-loss recovery while that service process survives;
it deliberately does not provide durable execution or restart recovery.

## Retrieval contract

- Browser router POST `/status`: strict `{id, request: {repository, base, head}}`.
- Dedicated service POST `/review/status`: the same fields plus trusted `principal`.
  Both use the existing authentication/ban/tenant or service-token checks. Neither
  route is registered/enabled in the application by this slice.
- ID binds to its immutable admitted request and exact user/tenant, including tenant
  absence. Owner mismatch returns `unknown` without source or result disclosure.
  A matching owner with a different request is rejected as `invalid_request`.
- Retrieval rechecks current repository authorization under a ten-second deadline.
  A pending lookup cannot remove a replacement record after expiry and ID reuse.
- Client checks strict status schema, ID, repository/base/head and result model,
  provider and `human_review_required`. No publication or approval is implied.

States are `unknown`, `running`, `completed` or `failed`. `running` includes pending
authorization and cleanup; `cancelRequested` reports explicit cancellation. Terminal
state is visible only after the underlying worker operation settles, not merely
after a delivery/service response timeout. `failed.code` retains the fixed worker
error, including the difference between `cancelled` and `timeout`. Later cancellation
cannot rewrite an already completed result or renew its retention.

`unknown` intentionally covers never-admitted IDs, pre-cancel-only records, another
owner, expiry and service replacement/restart. It never means "safe to execute again"
or confirms that an old process has stopped. Pre-cancel records still prevent matching
late starts; they are not represented as completed executions.

## Bounds, restart and replay

Up to 64 admitted records can be retained concurrently (including active/failed ones).
Each result JSON is at most 128,000 bytes, giving at most 8,192,000 serialized result
bytes plus bounded metadata and JS object overhead. This is not an 8 MB heap limit.
The complete serialized recovery response has an explicit 132,096-byte cap.
The existing 1,024 total-record limit also covers pre-cancel tombstones. Admission
fails busy when capacity is full; it does not evict unexpired results or queue work.

Terminal records expire exactly ten minutes after settlement. Status reads and
terminal cancels do not extend that deadline. An unref timer removes idle records;
lookup/admission also checks expiration. Timers run when the event loop can execute,
so physical erasure is subject to event-loop scheduling, while reads fail at expiry.
Pre-cancel-only records retain their previous renewable ten-minute race protection.
An uncooperative authorization callback holds its active slot until settlement; it
cannot start a child after cancellation. No background replay is scheduled.

State and replay suppression are process-local. Expiry/restart loses the result and
allows a deliberately reused ID to execute again; this is not durable exactly-once
execution. Clients never retry start automatically, with either old or new IDs.
Replacing the service instance returns unknown without inspecting/resuming old work.
Production crash cleanup and multi-instance ownership remain operator/architecture
requirements; no crash-recovery execution guarantee is added.

## Evidence and next UI slice

Offline fixtures cover lost route responses, real loopback reconnect after accepted
disconnect, exact owner/identity, policy revocation, fixed/idle expiry, service-instance
replacement, pre-cancel unknown, cancellation/timeout settlement, bounded capacity,
malformed/oversized responses and the delayed-authorization replacement race. Service
replacement tests model a fresh process-local map; they do not claim OS-crash cleanup.
All model execution uses synthetic workers, fixture credentials and empty auth roots.

Next: a disabled/gated immutable-pair form with shared primitives and English strings.
Retain the review ID and exact request in user-scoped UI state for an explicit Resume
status check after response loss; never persist findings or credentials there. Poll
status conservatively only while running, below the 60/minute read limit. Show terminal
findings and expiry, explicit Cancel, and unknown/expired state that never auto-starts
another review. Clear recovery state on user/tenant changes. Navigation only detaches
delivery. Add offline UI state/reconnect/identity tests before any registration or activation.

## Canonical durable review IDs

Review UUIDs are validated and lowercased before service map access and every
journal command. Principal, tenant, immutable request, and execution proof
identities retain their exact existing comparisons. The private helper also
validates and normalizes IDs before any journal operation.

On opening a review journal, noncanonical stored job, idempotency, generation,
or reservation IDs fail closed inside the startup transaction, before restart
transitions or reservation backfill. No automatic key migration, merge, replay,
or quarantine release is performed. Such legacy data requires a separately
approved recovery decision; changing letter case is not stop evidence.
