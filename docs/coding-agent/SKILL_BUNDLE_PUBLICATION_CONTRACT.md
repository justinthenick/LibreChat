# Dormant bundle publication protocol

`packages/api/src/skills/publication.ts` coordinates capture, current inspection and one
atomic publication attempt. It is not exported by the skills barrel or wired to routes,
draft saving, Trial, Publish, sync, storage or a database. It depends on PR #195.

The adapter contract is deliberately stronger than today's mutable Skill/SkillFile store:

1. `loadCandidate` authorizes the authenticated publisher and returns a manifest from one
   committed, immutable draft generation, plus its exact file reader and the observed
   publication digest. Do not manufacture coherence by reading separate live rows.
2. Every edit to the definition, file membership or bytes, including sync and edit/revert,
   commits a fresh generation ID. Never reuse an old generation (the ABA problem).
3. Capture verifies every file against that generation's manifest. Inspection applies the
   current publication policy to the captured snapshot.
4. `compareAndPublish` must perform one atomic transaction: check current publish authority,
   tenant and resource existence; compare both source generation and publication pointer;
   durably store the exact immutable snapshot; advance the publication pointer. Denials and
   conflicts change neither storage nor pointer. A separate check followed by a write does
   not implement this contract. Concurrent deletion/revocation must serialize with commit.
5. A successful result acknowledges durable storage and pointer advancement. Errors are
   not retried, including lost acknowledgements after a commit. Future recovery must query
   authoritative state using an idempotency protocol before deciding to retry.

The coordinator freezes authenticated actor values, rejects mismatched candidate identity,
and returns only the exact inspected snapshot after acknowledged commit. It does not
establish the trustworthiness of an adapter or authenticate caller-supplied identities.

Offline tests use deterministic promise barriers and a synchronous in-memory transaction.
They cover concurrent publishers, source-generation changes, deletion/revocation, corrupt
capture, inspection rejection and acknowledgement uncertainty. These prove coordinator
behavior under the adapter contract, not real database atomicity or production acceptance.
The four generation-change labels exercise the same protocol invariant; they do not test
today's edit or sync endpoints. Durable storage, real authorization serialization, generation
creation and crash recovery require separate implementation and review before activation.
