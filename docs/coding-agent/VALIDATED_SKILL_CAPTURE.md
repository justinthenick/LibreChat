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

## Validation and concurrency

- Source preparation detaches and validates the complete snapshot before its
  first await. Source ID, tenant, logical/definition name and upstream revision
  must agree with storage metadata. `commitSkillSource` checks the loaded source
  generation; MongoDB still decides the winner with its original generation CAS.
- Every source read checks both the payload's storage digest and bundle revision,
  manifest and all file bytes. It also checks the retained generation record.
  SHA-256 storage integrity alone never makes arbitrary JSON a valid bundle.
- Draft preparation uses `beginSkillDraft`. A new draft pins the loaded generation
  even if sync advances before commit. Existing ready drafts retain their edited
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
