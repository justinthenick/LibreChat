# Offline HTTP and LibreChat route checkpoint

This slice exports `createReviewHttpHandler(config)` and `createReviewRouter(config,
security)`. The former returns a Node HTTP callback without creating or binding a
server. `api/server/routes/reviews.js` supplies the existing `requireJwtAuth` and
`checkBan` middleware to the router factory. The application now mounts a separate `reviewDevelopment.js` wrapper with
the existing `ACCESS_ADMIN` capability check and validated development-only settings.
See [development wiring](../../../../../custom/coding-agent/orchestrator/REVIEW.md#development-only-application-wiring-default-off). Both sides remain disabled by default;
no credentials or environment settings are provisioned.

## Requests and ownership

The browser-facing router accepts POST `/` with `{id, request: {repository, base,
head}}`, and POST `/cancel` with `{id}`. The ID must be a fresh UUID for an explicitly
requested review. The body cannot supply principal, model, destination or paths.
Identity comes from authenticated `req.user.id` and `resolveRequestTenantId(req)`.
Existing JWT user/account checks, tenant middleware and ban checks precede both
operations. Strict tenant mode still rejects absent tenants. Default single-tenant
mode preserves absence exactly; it does not invent a tenant name. The existing
worker authorization callback receives this identity and must return true.

The dedicated service accepts POST `/review` with the existing strict envelope and
an `x-review-id` UUID header. POST `/review/cancel` accepts `{id, principal}`. Both
require the separate service bearer token. The HTTP callback checks the configured
Host, exact method/path and required start ID, ignoring forwarded host headers.
It uses the fixed configured origin when constructing the Web Request.

The router enforces the existing strict request schema plus a 4,096-byte serialized
body limit even when LibreChat's earlier global parser has already parsed JSON.
Its own parser uses a 4,096-byte raw limit when mounted without that global parser.
Existing `express-rate-limit` provides per-user-and-tenant limits of 10 starts and
60 cancellations and 60 status reads per minute. These stores are process-local. The service retains
its allowlist, single active execution, input/output bounds and deadlines.

## Delivery disconnect versus cancellation

An accepted identified review has an execution controller independent of its HTTP
connection. Browser abort, response close or loss of the NAS-to-Clare connection
stops response delivery without cancelling accepted work. A truncated request body
never reaches worker execution. The 165-second service deadline still cancels work;
the worker retains its 150-second execution limit and cleanup responsibilities.

Only an explicit `/cancel` request from the same authenticated user and exact tenant
can cancel that ID. An absent tenant differs from every named tenant. Cancellation
does not fall back to whichever review happens to be active. Its stable 200
`{cancelled:true}` response acknowledges the cancellation request, not completed
process cleanup. An already finished run also yields that acknowledgement.

A cancellation arriving before admission creates a short-lived record for that
ID/owner, preventing a delayed matching start from executing. Unknown IDs never
cancel another run. Repeated cancellations renew that record. Records retain ID, owner, immutable request, cancellation/controller state and expiry.
Up to 64 admitted reviews additionally retain their validated terminal result or fixed
error for 10 minutes after settlement. Reads and terminal cancellations do not extend
retention. The map is capped at 1,024 total entries including pre-cancel records and
rejects new admissions when full. Active entries cannot be evicted. See [RECOVERY.md](./RECOVERY.md). This is bounded
replay suppression within one process, not a queue or durable exactly-once system.

The prior direct in-memory `run(request, principal, signal)` contract is preserved.
HTTP callers use the fourth `id` argument, and call `client.cancel(id, principal)`
explicitly. A local fetch deadline is an uncertain delivery outcome, not evidence
that remote execution stopped. Neither client operation retries automatically.
After restart or record expiry, reusing an ID can execute again. Owner-scoped POST `/status` can recover retained results after response loss; callers
must not automatically resubmit uncertain work, with either the same ID or a new one.
Expiry or service restart yields `unknown`, not proof that execution never occurred.

## Offline verification and activation limits

The HTTP tests bind ephemeral `127.0.0.1` ports only. They use fake service credentials,
fixture authenticated users, the actual tenant middleware and existing worker with
synthetic executable/empty auth directory. They verify disconnect survival, explicit
cancel and cleanup, owner isolation, pre-cancel race, expiry and capacity bounds,
default off, host/credential/body rejection, uncertain-outcome no-retry and limits.
Separate existing JWT, ban and tenant suites cover those middleware implementations;
the thin-wrapper test verifies composition using fixture security middleware.
No deployed proxy, live identity provider, real credential or model call is involved.

Production activation remains separate:
configure a dedicated service token and repository policy, approved private TLS
path and hosts, single service process ownership, HTTP header/body/socket limits,
proxy timeouts, sanitized audit integration and host lifecycle/aggregate limits.
No production listener or configuration is introduced here. Horizontal deployment
would require a deliberate ownership design; these process-local limits are not
distributed guarantees.

## Original UI requirements (implemented in the development panel)

Add a disabled/gated authenticated review form using existing shared primitives,
English localization and React Query. Submit an authorized repository identifier
and full immutable base/head SHAs with a fresh UUID; retain that ID for the explicit
Cancel action. Derive no identity in browser JSON. Render text findings with exact
commit pair, model and `human_review_required`; zero findings are not approval.
Show busy, forbidden, cancelled, timeout and uncertain-delivery states distinctly.
Leaving the page only detaches delivery. Do not auto-retry or imply cancellation
on navigation, and do not add publication/merge actions. Test these states offline
before proposing route/UI registration or activation. PR URL freshness resolution
remains outside this immutable-pair slice. Lost responses can use status recovery
within the bounded process-local retention window.

## Development PR identity lookup

`POST /api/reviews/selection` accepts exactly:

```json
{"repository":"fixture","pullRequest":7,"expected":{"base":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","head":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}}
```

`expected` is optional. The existing development gate, JWT/user-state validation,
ban checks, capability policy and tenant repository allowlist precede lookup.
The configured repository entry must additionally contain a pinned GitHub binding:

```json
{"id":"fixture","tenantId":"tenant-a","github":{"owner":"fixture","name":"repo","repositoryId":123}}
```

This example is synthetic, not a usable runtime configuration. No binding is
installed by this change. Discovery still exposes only authorized local IDs.
Absent mappings fail closed. The browser cannot supply a host, owner, name,
repository ID, credential or principal. The response's base repository ID and
full name must match the trusted binding, preventing name reuse or wrong-repo
responses from silently changing repository identity.

The module issues one unauthenticated GET to the fixed `api.github.com` origin,
without redirects, retries or application caching. It neither reads credentials
nor uses the coding executor. It bounds the whole lookup to five seconds and the
decoded response body to 64 KiB, with a 30-request/minute user/tenant limit.
Private repositories are deliberately unsupported until an explicitly approved
existing GitHub authorization integration is selected. No new credential or
permission is created. GitHub rate/access/network failures return fixed errors.

The response includes `{request:{repository,base,head,pullRequest:{number,repositoryId}},pullRequest,status,checkedAt}`.
It uses GitHub's actual `base.sha` and `head.sha`, including stacked bases and fork
heads; it never substitutes `merge_commit_sha` or a default branch. Titles, bodies,
URLs and other PR content are discarded. `status` is `resolved` without an expected
pair, `current` only for an exact pair match, `stale` if either SHA changed, or
`closed` for a closed/merged PR. The timestamp records completion of this lookup.

**This is a point-in-time observation, not a lease.** The PR can change immediately
afterward. The request's optional `pullRequest` object is part of immutable run
identity alongside repository/base/head. The server validates its repository ID
against the current tenant mapping and rechecks the exact pair before dispatch.
It rechecks again after successful execution and before returning a retained
outcome. Closed/merged PRs or either changed SHA return `409 stale_review` with no
findings. Lookup failures also withhold findings. Completed PR results include
route-generated `prCheckedAt`; worker transport rejects worker-supplied timestamps.

Recovery checks stored ownership and complete request identity before PR lookup.
Removing or changing the PR binding cannot retrieve a bound result as a local-pair
review. Unknown IDs remain unknown without lookup or resubmission. Cancellation
remains owner-scoped and does not require current PR metadata; a cancellation
recorded during admission lookup prevents the later worker dispatch. No extra
route-local state or persistence is introduced.

The UI resolves PR numbers using the authorized repository mapping. For recovery,
enter the original review ID and commits before resolving: the original pair is
preserved even if GitHub has moved. Selection or session changes clear displayed
findings and invalidate delayed responses. A blank PR number selects explicit
local-pair mode; these results carry no PR freshness claim. Neither mode publishes.

The pre-dispatch check cannot atomically reserve GitHub's head. A change immediately
after checking can still start work, but a changed pair observed at completion or
recovery withholds findings. The UI labels the completion check as point-in-time.
No Git object fetching, private-repository authorization, continuous freshness
monitoring, automatic resubmission, or durable restart recovery is added.

Reference: [GitHub REST: Get a pull request](https://docs.github.com/en/rest/pulls/pulls#get-a-pull-request),
API version `2026-03-10`. Verification uses fake GitHub responses and the actual
authenticated application wrapper with synthetic storage; no live lookup or
model call is needed for these tests.

## Optional durable review recovery (development, default off)

The service can explicitly receive a `journal` opened by `createReviewJournal`
from `@librechat/api/coding`. Configure absolute Linux paths for `python`
(stdlib Python), `sourceRoot` (the orchestrator `src` directory), and `path`
(a dedicated private SQLite database). Await journal creation before accepting
requests and call `journal.close()` during shutdown. This does not add a route,
environment switch, production bootstrap, or automatic activation. Keep the
existing service authentication, repository authorization, PR identity checks,
bounded worker, cancellation, cleanup, result validation and finish-only backend.

The adapter reuses the orchestrator `JobStore` through a single lock-owning,
credential-free Python helper. It persists the external review UUID, owner,
tenant, repository alias, exact base/head, PR binding and configured model in
the admission transaction before dispatch. Successful validated outcomes are
committed after worker settlement and cleanup, before delivery. Completed
recovery still checks the current PR identity. An interrupted response has no
findings or freshness claim and remains observable without a GitHub lookup.

Restart never repeats model dispatch. Previously active jobs become explicit
`interrupted` records; unresolved execution reservations block new admissions.
A helper failure fences its TS service generation permanently, cancels local
work and rejects pending operations without retrying mutations or reconnecting.
Only successful settled execution supplies trusted stop evidence. Failures,
timeouts, cancellation without successful settlement, and process loss do not
prove external quiescence and remain quarantined. If cancellation wins the
terminal commit after successful worker settlement, persist cancelled, withhold
findings, and release the reservation using that settlement evidence.

Cancellation before admission persists a tombstone without taking an execution
slot. No UUID may be replayed, including after finding expiry. Result payloads
expire after 600 seconds (on access/admission and a 30-second maintenance sweep);
identity tombstones remain. Admission is bounded to 64 retained result payloads
and 1,024 lifetime records, failing closed at capacity. This milestone includes
no deletion/reset, automatic reconciliation or reservation-release endpoint.
Do not remove the journal to clear a quarantine: that loses no-replay evidence.

Process crashes can leave orphaned execution or scratch directories. This
milestone deliberately does not infer their termination or automate crash
cleanup; trusted reconciliation and retention/tombstone lifecycle policy remain
follow-up work before activation. Use a dedicated database, not the general job
store database. The helper imports only stdlib persistence code and receives no
provider credentials, executor access or publication capability.

Offline tests use real SQLite/helper processes, fake workers/provider outputs
and empty auth directories. They cover service/helper loss, both commit-before-
acknowledgement windows, owner/tenant/PR/model mismatch, orphaned execution,
precancellation, cancellation racing completion, expiry with no replay, lock
contention and subsequent admission after trusted settlement. No live model or
GitHub publication is part of those fixtures.
