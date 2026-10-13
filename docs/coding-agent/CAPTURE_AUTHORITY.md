# Dormant capture authorization prerequisite

This implements a **synthetic shared-write fence**, not LibreChat authorization.
`createIsolatedFencedCapturePersistence` and `createIsolatedCaptureAuthority` are
available only through the existing isolated capture subpath. They require a
replica set and an actual database name matching `test_skill_capture_*`. They do
not register models, expose routes, or read or change application grants. Both
activation functions still fail unconditionally. The unfenced storage factory
and validator bridge remain isolated proofs, not authorized application APIs.

## Why the production model is not ready

Inspection at preview `cc45d0fd0abf8f2508063aa2274382cf75f3e218` found:

- `packages/data-schemas/src/methods/aclEntry.ts` grants through upsert, changes
  permission bits, deletes individual entries, deletes many entries, and exposes
  bulk writes. Some accept a session, but none participate in a capture epoch.
  Effective permissions combine multiple principal entries. Adding a capture
  precheck, even inside a snapshot transaction, does not make these writes conflict.
- `packages/data-schemas/src/schema/aclEntry.ts` stores user, group, role and public
  principals and has an `expiredAt` TTL index. Expiry and deletion are separate
  from capture writes. Wall-clock expiry needs an explicit authorization and
  commit policy; a shared write by itself does not prevent time from advancing.
- `packages/api/src/cache/principals.ts` caches resolved group membership, with
  optional shared-cache locking. Cache freshness is not a transactional fence
  for group removal, role change, suspension or tenant reassignment.
- `packages/data-schemas/src/methods/skill.ts` updates skill versions, deletes
  skills and cleans up permissions/files separately. Skill file changes and
  version/file-count updates are also separate operations. These paths do not
  maintain a shared authorization epoch or atomic immutable capture generation.

The live dependency is a defined authoritative user/tenant/resource/owner policy
and complete writer participation: grants, revocation, bulk deletion, role/group
membership, account state, tenant changes, resource deletion/visibility and
expiry. A policy for retention and migrations, deployment transaction support,
and operational failover acceptance is also required. This slice does not modify
any of these paths or claim that a production epoch exists.

## Implemented isolated contract

- Synthetic grants are scoped to the exact tenant (including distinct null),
  owner and source ID, with an explicit operation set. They are fixture data;
  caller-supplied identities are not authenticated users.
- Creation requires epoch zero and uses a unique deterministic key. Replacement
  requires the current epoch and advances it. Revocation is replacement with no
  operations. There is no grant deletion API: tombstones retain epochs across
  regrant to prevent an old ticket becoming valid again.
- A fenced store detaches its expected scope/epoch before awaiting work. Every
  source write, reservation (including ready reuse), completion, failure,
  recovery and edit must match that scope, epoch and operation.
- The capture transaction performs a real `$inc` on the matching grant's use
  counter before writing state. This is not a no-op update or snapshot-only read.
  Grant replacement and capture both write the same document, so concurrent
  stale snapshots conflict. If capture commits first, revocation may follow;
  that earlier commit remains valid in this synthetic ordering. A stale
  revocation transaction must be resolved/retried explicitly before claiming it
  revoked anything. No transaction callback retries are hidden in this adapter.
- The use counter, capture state and operation receipt commit or roll back
  together. The receipt records the scope and epoch actually used. A failed CAS
  cannot consume a use or leave a receipt. Epoch and use exhaustion fail closed.
- Reads and receipt resolution retain the raw store's storage-only semantics.
  They are **not access-controlled responses** and must never be exposed to an
  untrusted caller. Resolving a lost-reply receipt after revocation reports a
  historical commit; it does not renew permission or replay a write. Missing
  receipts are still unresolved outcomes, never permission to retry blindly.
- The [validated fenced factory](./CAPTURE_INTEGRATION.md) now composes this store
  with full bundle validation. The raw store remains opaque, and the original
  validator factory remains unfenced. Neither path connects to a live policy,
  proves upstream provenance, or authorizes publishing.

## Evidence

`packages/data-schemas/src/skills/authority.spec.ts` uses the existing disposable
MongoDB replica-set test dependency, synthetic actors and only isolated
collections. Tests cover grant absence, operation restrictions, epoch CAS,
revocation/regrant, owner/tenant/source boundaries, input detachment, transaction
rollback, ready reuse, all draft transitions, recovery and historical receipts.
Deterministic transactions establish an older snapshot, commit the conflicting
writer, and then assert MongoDB write conflict in both orderings. The previous
snapshot-read-only counterexample remains in `persistence.spec.ts`.

These single-node tests do not prove multi-node failover, real unknown-commit
outcomes, wall-clock expiry, or participation by production authorization writers.
No new dependencies, actual grants, security settings, providers, credentials,
production collections or migration are involved.
