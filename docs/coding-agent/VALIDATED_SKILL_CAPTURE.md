# Isolated bundle validation and persistence

`packages/api/src/skills/persistence.ts` connects the existing bundle and capture
validators to the isolated MongoDB adapter. Its factory remains outside the API
barrel and all routes. `activateValidatedSkillCapture` always throws through the
existing hard-disabled activation boundary. No feature flag enables it.

The data-schemas package exposes an explicit `isolated-capture` subpath so the API
workspace can import the storage implementation and types without importing a
sibling workspace's source. This subpath has no initialization side effects. It
does not register models, connect to a database or change its configuration.
The factory still requires an existing connection to `test_skill_capture_*` and
transaction-capable MongoDB; tests use disposable replica sets only.

`createIsolatedFencedValidatedCapture` uses the same validators and prepared
operations with the existing synthetic fenced store. Its grant write, capture
state and receipt share one transaction. The original factory remains unfenced.
Neither factory authenticates application users or authorizes diagnostic reads.
See the [remaining integration checklist](./CAPTURE_INTEGRATION.md) for production
writer dependencies and approval boundaries. Activation stays disabled.

## Validation and concurrency

- Source preparation detaches and validates the complete snapshot before its
  first await. Source ID, tenant, logical/definition name and upstream revision
  must agree with storage metadata. `commitSkillSource` checks the loaded source
  generation; MongoDB still decides the winner with its original generation CAS.
- Every source read checks both the payload's storage digest and bundle revision,
  manifest and all file bytes. It also checks the retained generation record.
  SHA-256 storage integrity alone never makes arbitrary JSON a valid bundle.
- Draft preparation requires the selected committed `sourceGeneration` and
  `sourceDigest` alongside `sourceId`. It validates that retained generation in
  the actor's tenant; missing or mismatched references reject without a latest
  source fallback. Inputs are detached before the first await. `beginSkillDraft`
  pins those bytes even if sync advances before or during preparation or commit.
  Existing ready drafts retain their edited
  snapshot and original source base; pending/failed drafts cannot be reused.
- Completion uses `completeSkillDraft` to require the exact definition, manifest
  and file set derived from the pinned source. A separately valid bundle with a
  different body, file set, bytes, identity, tenant or provenance is rejected.
- Failure and recovery use the existing capture transitions. Edits require ready
  state and validate the full edited bundle while preserving identity, name and
  base provenance. Renaming is not implemented. Draft state transitions retain
  the loaded attempt and revision as CAS expectations; preparation never silently
  rebases them. Ready-draft reuse may return newer ready edits at commit without
  overwriting them.
- Every loaded draft, including a receipt result, is validated against its retained
  source generation and digest. Ready snapshot provenance must identify that
  original source generation and bundle revision.

## Logical draft reservation discovery

`readDraftReservation(actor, { sourceId, name })` locates the existing
tenant/owner/name reservation without requiring its ID. It returns a frozen
metadata-only handle: ID, name, source ID, status, attempt and revision. It does
not read source or draft payloads. A matching name owned by the same actor but
bound to another source rejects instead of appearing absent. Different names
for the same source remain valid; there is no one-draft-per-source constraint.

This is an isolated diagnostic read, not an access-controlled response. Actor
filtering does not authenticate the caller, and a `ready` status in the handle
neither validates content nor grants permission. Pending/failed metadata can
identify a reservation for a separately requested recovery; it is not usable
draft content and discovery never recovers or changes state.

`prepareDraftByName` accepts the same explicit selection and candidate ID as
`prepareDraft`. It validates and detaches the actor, name, IDs, selected source
generation and digest before discovery. When a reservation exists, it substitutes
only the canonical draft ID and calls the existing `prepareDraft`. Full bundle
validation and the original commit transaction still apply. Ready reuse preserves
the draft's edits and original source generation, including newer ready edits
committed after discovery; pending and failed reservations reject. Revocation
after discovery still prevents a fenced commit. There is no direct return of
discovered content and no new authorization mechanism.

Concurrent absent lookups can prepare distinct candidate IDs. The existing unique
tenant/owner/name index chooses one commit winner; the other operation conflicts.
There is no automatic retry, deletion, rebase or recovery. An uncertain result
must be resolved using the original operation ID and request digest, not another
lookup or newly prepared operation. A missing receipt remains unresolved.

## Receipts and restart

Preparation returns a frozen operation with `operationId`, `requestDigest`,
`commit()` and `resolve()`. Its private write inputs are detached from caller
objects. Save the operation ID and request digest before attempting a write.
Repeated `commit()` calls use the same ID; the store rejects replay.

`resolve()` validates the historical receipt result, not the current source or
draft. Later edits, recovery and sync do not replace that result. A reconstructed
isolated client can call `resolveReceipt(actor, operationId, requestDigest)` without
preparing/replaying the old mutation. A missing receipt means unresolved, not
permission to retry. Corrupt payloads and mismatched request digests fail closed.

Actor fields provide identity filtering only. Neither those fields nor a receipt
digest authenticate a caller or grant access. The full application authorization
fence remains missing, including every ACL/user/group/role/visibility revocation
writer and a defined expiry policy. No live authorization safety is claimed.

The producer must still assemble each source from one immutable upstream revision.
Matching a supplied revision string is consistency validation, not independent
GitHub provenance verification. Migration, live writer participation, retention,
multi-node failover acceptance and activation remain separate work.

## Evidence

The API integration suite uses actual bundle/capture functions and the packaged
storage subpath with `MongoMemoryReplSet`, not mocked CAS or database calls. It
covers valid lifecycle, invalid source/draft bundles, pinned-generation mismatch,
stale prepared writes, preserved ready edits, caller mutation, recovery, historical
receipts and reconstruction of the receipt reader. No provider or production
database is involved. CI results must be attributed to their exact tested tree.
