# Offline review transport checkpoint

`createReviewService` composes the existing Linux/WSL review worker with an
authenticated Web Request/Response handler. `createReviewClient` calls that
handler through a fixed destination. Both remain disabled unless `enabled: true`
is explicitly configured. This slice registers no HTTP listener, LibreChat route,
health endpoint or UI and does not activate a service.

## Contract

- POST to the configured `/review` URL with a dedicated service bearer token.
  HTTPS is required except literal loopback HTTP. URL credentials, query and
  fragment are rejected. Client redirects and automatic retries are disabled.
- Strict JSON envelope: `{request: {repository, base, head}, principal:
{userId, tenantId}}`. Commit IDs are immutable full SHAs. The caller must derive
  principal from authenticated server context; this is not a browser API.
- The service authenticates before reading the body and uses the existing worker
  authorization callback and repository allowlist. A single admission slot covers
  body reading, authorization and execution. There is no queue.
- Request limit: 4,096 bytes. Result/error limit: 128,000 bytes. Service deadline:
  165 seconds; client deadline: 170 seconds. The worker retains its 150-second
  execution deadline, process limits, process-group cancellation and cleanup.
- Results use the shared strict `CodeReviewResult` schema. The client checks
  repository, base, head, provider, model and `human_review_required` status against
  its request/configuration. Findings are never approval or publication.
- Errors contain only an existing fixed worker failure code. Invalid request 400,
  forbidden 403, busy 409, cancelled 499, timeout 504, worker/output/response errors
  502 and configuration 503. Responses request no caching.

Direct in-memory cancellation propagates through the request signal to the existing worker.
Identified HTTP runs instead detach execution from delivery disconnects and require an
explicit authorized cancel request; see [HTTP.md](./HTTP.md).
An authorization callback that ignores cancellation keeps the admission slot
occupied until it settles, even after the response deadline. This prevents
accumulating pending authorization work; callback implementations should still
bound their own external I/O. Once cancelled, a late callback cannot start a child.

## Verification and limits

`transport.spec.ts` uses in-memory Web Request/Response objects, fixture tokens,
an empty disposable auth directory and synthetic executables. It checks auth,
repository denial, exact identities, malformed/oversized streams, deadlines,
busy handling, cancellation and descendant cleanup. No model call is required.
These tests do not validate a deployed HTTP server or real proxy disconnects.

The original finish-only backend, source-evidence checks, diff limits and cleanup
remain in place. Unsupported/deletion-only evidence and over-budget diffs are not
silently compressed. Immutable input does not establish that a remote PR head is
still current; PR URL resolution/freshness checking remains a separate feature.

The next isolated slice adds an unregistered HTTP bridge and authenticated route
factory with rate limiting and offline tests; see [HTTP.md](./HTTP.md) for its
delivery-disconnect and explicit-cancellation semantics. Sanitized audit integration
and UI remain future work.
Operator configuration still needs a dedicated transport credential, approved
private network/TLS path, repository policy, host lifecycle/resource controls and
proxy timeout verification. None is provisioned by this slice. Existing model
authentication stays host-owned and is neither read nor copied by these fixtures.
