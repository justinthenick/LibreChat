# Isolated capture persistence

This is a dormant storage implementation, not a live managed-skills adapter. The
factory in `packages/data-schemas/src/skills/persistence.ts` is absent from package
barrels, model registration and routes. It accepts only an already-connected
database whose actual name starts with `test_skill_capture_`, and requires a
replica set with sessions. `activateSkillCapturePersistence` always throws
`skill_capture_authorization_unavailable`. There is no feature flag to bypass it.

## Implemented storage guarantees

- One transaction commits immutable content-addressed payloads, source pointers,
  retained source generations, draft state and operation receipts as applicable.
  Transactions use primary reads, snapshot read concern and majority journaled
  writes. The adapter does not use automatic transaction callback retries.
- Source writes compare the current generation and tenant. Generation history
  binds source identity, tenant, generation, payload digest and producer revision.
  A draft can pin a retained older generation, but cannot mix its digest with a
  different generation. Counters fail closed on exhaustion.
- MongoDB enforces unique draft IDs and unique tenant/owner/name reservations.
  Completion, failure, recovery and editing compare the entire expected draft,
  including status, attempt and revision. Recovery advances the attempt; edits
  advance the revision. Ready reuse preserves edits and the original pinned base.
- Staged bytes and receipts roll back if a later operation fails. Payload inserts
  never overwrite existing bytes, and reads check their SHA-256 digest. There is
  no deletion or garbage collection API, so this slice cannot reset counters or
  discard pinned generations. Retention is deliberately unbounded in this proof.
- A receipt binds the operation ID to actor, tenant, operation and all normalized
  inputs, and stores the original result in the same transaction. `resolve` reads
  it from the primary with majority concern, even after later state advancement.
  Repeating a mutation with that operation ID rejects rather than replaying it.
  A missing receipt during an uncertain commit is **not** proof of failure: wait
  for authoritative resolution; never blindly restart capture or recovery.

The request digest uses the ordered JSON tuple with recursively sorted object
keys built by `captureRequestDigest`; retain inputs before starting an operation.
The helper shares the mutation methods' operation-specific field projections and
normalizes omitted transition payloads to null. Full draft records are accepted
as reservation inputs; extra fields do not change the reservation receipt digest.
It is an identity check, not an authorization capability. These isolated APIs have
no authorization boundary and must not be exposed to an untrusted caller.

## Explicitly missing before activation

The [isolated validator bridge](./VALIDATED_SKILL_CAPTURE.md) now connects the
existing validators to this store and is tested separately. The raw storage
module remains deliberately opaque; the bridge is not connected to live routes.

The payload is opaque JSON with an independent storage digest. This module does
not replace `validateSkillBundle`, `beginSkillDraft` or `completeSkillDraft`.
Application integration must validate complete bundle semantics, match the draft
definition and files to its pinned source at completion, and assemble input from
one immutable upstream commit/writer generation. A well-formed upstream revision
string is a producer claim, not GitHub provenance verification. Storage hashes
cannot detect a producer that already assembled a self-consistent mixed bundle.

The existing ACL methods support optional transaction sessions, but grants,
revocations, user/role/group membership and source visibility do not all write a
shared capture authorization fence. Existing MCP authority revision/snapshot
mechanisms are not a substitute for such participation. Reading authorization
inside a transaction snapshot and then writing an unrelated draft can still
commit after revocation. The real-database counterexample test demonstrates this.
The positive test demonstrates a shared write conflict in an isolated authority
model; it does **not** wire or certify the application's ACL writers.

A live adapter needs an authoritative current user/tenant/source/owner check plus
a shared write/conflict fence observed by every relevant revocation and mutation
path. Group removal, role change, account suspension, tenant reassignment, public
visibility changes, expiry and deletion must be included. Expiry additionally
needs an explicit time/commit policy; a write conflict alone does not stop time.
No production MongoDB mode, existing service, schema, ACL or security setting is
changed here. Migration, application writer integration, retention policy and
operational failover acceptance remain separate prerequisites.

## Verification boundary

`persistence.spec.ts` uses the existing `mongodb-memory-server` dependency with a
single-node disposable `MongoMemoryReplSet`. It also starts a disposable standalone
server to prove unavailable-state rejection. No provider calls, production URI,
credentials or existing database are used. A single-node test verifies transaction
semantics, not multi-node failover durability. Lost acknowledgement is simulated
by dropping the reply after an actual database commit, then reading its receipt;
this is not a network partition or driver unknown-commit-result test.

Run with the repository's existing data-schemas Jest job. This slice adds no
dependencies, production configuration, migrations or automatic activation.
