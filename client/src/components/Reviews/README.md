# Inactive review UI slice

Stacked on the disabled review backend port to `feature/openhands-preview-jobs`.

`ReviewPanel` is deliberately unmounted and defaults to `enabled=false`. A future
caller must supply authenticated identity and server-authorized repository IDs.
`/api/reviews` is reserved by the client helpers; the server factory remains
unregistered. This checkpoint is not an end-to-end usable review feature.

The panel accepts exact base/head commit SHAs and an optional existing review ID.
Starting creates one UUID. Retrieval only fetches status/result; it does not resume
the model. React Query retries and offline queuing are disabled. The request helper
uses the existing authenticated Axios instance and marks sent requests non-replayable
for the 401 interceptor; its delivery timeout is 180 seconds. Navigating, changing
identity/tenant or editing selection aborts delivery and discards stale replies,
without cancelling accepted work. Cancellation is explicit and its acknowledgement
is separate from confirmed settlement. The ID is not persisted; users must retain
it with the exact selection for manual retrieval after navigation.

Results show repository, immutable pair, model, status, evidence and recommendations
as text. Empty findings never imply approval. Coverage, uncertainty, process-local
retention/restart limits, and lack of remote PR-head freshness are visible.

## Offline validation and remaining integration

Component tests run through the normal client Jest configuration; request tests use
its shared authenticated Axios implementation. The backend's reusable offline
composition runner is `custom/coding-agent/orchestrator/tests/review/run.cjs`.
It exercises seven contract scenarios in CI with scripted SDK responses and no
browser, provider credentials, external network or publication.

Earlier isolated missing-dependency reports were resolved using already-installed
workspace dependencies. Full frontend typecheck, shared-client build and normal
frontend build passed on the source checkpoint. Seven local full-frontend browser
scenarios also passed: completion/repeated clicks, disconnect/retrieve, explicit
cancel, stale selection, account switch, unknown ID and expiry. They use real
React/AuthContext/Axios, JWT middleware, HTTP/worker/CLI interfaces; user lookup,
ban checks and model responses are fixtures. The publication PR records validation
of the final port; historical results alone do not validate a new base.

The browser harness is external evaluation tooling and is not run by PR CI.
Component tests cover UI ordering; the dedicated backend runner covers contract
behavior. Neither proves persistent authentication/bans, remote-head freshness,
restart recovery, real subscription authentication or deployment wiring.

Before activation, define the server-authorized repository list and gate, then
validate deployment-specific routing and recovery in a separately authorized
environment. Authorization, allowlisting, limits, immutable identity, evidence
validation, cancellation, cleanup and finish-only controls remain in place.
