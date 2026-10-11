# Dormant committed skill capture protocol

This slice implements pure source/draft state transitions in
[`capture.ts`](../../packages/api/src/skills/capture.ts). It is deliberately absent from
the package barrel and live routes, sync, datastore adapters and migrations. Its tests
use synthetic state and bytes. They do not establish safe production capture or fix
the existing races characterized by PR201.

## Chosen protocol and invariants

The protocol uses an immutable complete bundle plus an atomic committed pointer,
not a version double-read over independently changing Skill and SkillFile rows.
The physical storage schema and activation remain separate work.

1. Sync stages the entire definition and file manifest and captures all bytes through
   `captureSkillBundle`. A partial or corrupt payload cannot become a committed source.
   `commitSkillSource` validates and detaches the complete snapshot and advances a
   monotonically increasing generation. A source identity or tenant cannot change.
2. Draft reservation pins one committed source snapshot and its generation. A newer
   sync may commit during copying: the draft still captures the complete older generation,
   with that base explicitly retained. No mutable source-row fallback is allowed.
3. An initializing or failed draft is unavailable to editing, Trial, Publish and ordinary
   reuse. Competing Create Draft requests must receive an explicit pending/conflict result;
   they cannot treat the placeholder as a ready draft.
4. Copy validates byte lengths, hashes and the complete pinned manifest. Completion
   requires exactly the expected draft identity, definition and file set. Only successful
   completion changes the state to ready. A failed copy leaves no usable draft.
5. Failure records a failed state; it never deletes a draft or edits. Explicit recovery
   retains the original pinned source and increments the attempt number. This fences
   stale workers, including a worker still copying when recovery starts. Ready drafts
   cannot be failed, restarted or overwritten by capture cleanup.
6. Reusing an existing ready draft preserves its current user-edited snapshot and original
   base. This protocol does not implement user editing; an eventual edit path must retain
   the base and independently serialize its own committed draft generations.
   A rename must update the record name, snapshot logical name and definition name together.

## Required persistence and authorization boundary

The functions return proposed immutable records; they do not persist or authorize them.
Passing a stale record into a pure function is not a database lock. A real adapter must:

- Authenticate and reauthorize the actor, current tenant, source visibility and draft
  ownership at each operation's atomic commit, including recovery and reuse.
- Apply source transitions with an atomic generation compare-and-set; durable snapshot
  bytes and the pointer must become committed together, or immutable durable bytes must
  already exist before the pointer can advance. Preserve old snapshots while referenced.
- Reserve a draft atomically under its owner/tenant/source/name identity and a unique
  draft ID. All writers, including editing, must honor the initialization state.
- Apply completion/failure/recovery against the current stored initializing/failed state
  and attempt in one atomic operation. Calling the reducer outside a transaction and
  unconditionally writing its result is unsafe.
- Never reuse source generations or draft attempts. Preserve counters or tombstones
  across deletion/recreation. Counter exhaustion fails closed.
- Treat a lost commit acknowledgement as uncertain. Read authoritative state and match
  its identity, attempt and snapshot before deciding the outcome; never blindly repeat
  reservation, cleanup or recovery. This module performs no automatic retries.
- Keep staging bytes separate from readable committed bundles. Garbage collection and
  retention must respect active attempts, pinned bases and ready edits; no cleanup adapter
  is included here.

These are adapter obligations, not properties proven by the synthetic tests. A database
transaction, equivalent conditional writes, storage retention and authorization need
their own implementation and acceptance evidence before any live activation.

## Evidence and next bounded adapter work

The tests cover valid completion, incomplete/corrupt sync payloads, stale sync writers,
edit-and-revert generations, source advancement during copy, failed/missing/partial
copies, explicit recovery, stale worker completion/failure, concurrent completion,
identity mismatches, immutable input detachment and ready-edit preservation. Pure helpers
can produce two valid proposals from the same stale input. Explicit synchronous CAS
simulations show where the adapter must select one winner or fence an old proposal;
these simulations are not database concurrency acceptance.

The next slice should implement one isolated persistence adapter and prove its actual
CAS and uniqueness operations under concurrent calls and uncertain acknowledgements.
It must cover all source mutation paths before replacing live sync/draft behavior.
GitHub publication provenance, picker state, exact-revision Trial wiring, deployment
and production/provider acceptance are outside this slice.
