# Managed skills readiness and capture evidence

Evidence checkpoint: 2026-10-10 08:52 UTC. This is a source/test assessment, not live production acceptance.
The production branch `server/synology` was read at
`20e8dff1d23130fb1360a8596fa4132eb9fc94b9`; the preview source assessed here is
`5bebc29e65da4c8fa40f8ff8608cb3c92e3d61e3`. A branch SHA does not prove the running
deployment, configured credentials, enabled picker state, or successful provider execution.
No live datastore, storage, model/provider, permissions or deployment changes were made.

## Delivered source versus proposed work

| Capability                              | Evidence and status                                                                                                                                                                                    | Remaining limit                                                                                                                                                                                          |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Managed Draft, lifecycle/Trial, Publish | Existing [route handlers](../../api/server/routes/skills.js) create/reuse drafts, change lifecycle and publish GitHub changes.                                                                         | Separate metadata/file reads do not bind Trial or Publish to a coherent captured bundle. Lifecycle labels alone are not acceptance evidence.                                                             |
| Manual selection with definition only   | [PR191](https://github.com/justinthenick/LibreChat/pull/191) merged into preview; selection rejects disallowed manual invocation and binds the selected definition; bundled file bytes are not pinned. | Preview source delivery does not prove current production picker/runtime behavior.                                                                                                                       |
| Immutable bundle capture/read boundary  | [PR195](https://github.com/justinthenick/LibreChat/pull/195), merged into development preview at `5bebc29e` after refreshed review and CI against `cde1271`.                                           | Dormant host-only boundary; no live capture/storage/Trial integration. Does not make existing draft creation atomic.                                                                                     |
| Publication coordinator                 | [PR197](https://github.com/justinthenick/LibreChat/pull/197), head `0cc0409`, reviewed/tested draft; refreshing after PR195 integration.                                                               | Dormant compare-and-swap adapter contract; real persistence and activation remain absent.                                                                                                                |
| Publish source-provenance guard         | [PR199](https://github.com/justinthenick/LibreChat/pull/199), head `bc6bec4`, reviewed/tested draft based on preview.                                                                                  | Rejects invalid/stale provenance before remote writes; allows unrelated changes when the exact skill subtree is unchanged. Does not establish coherent draft capture or prevent later upstream movement. |
| Deterministic backend cache tests       | [PR198](https://github.com/justinthenick/LibreChat/pull/198), head `af96af9`, reviewed/tested, open and unmerged.                                                                                      | Test reliability improvement, not a managed-skills runtime feature.                                                                                                                                      |
| Coherent draft capture                  | Current branch adds characterization tests and this assessment only.                                                                                                                                   | Not delivered. Passing characterization tests reproduce unsafe interleavings; they do not approve those behaviors.                                                                                       |

PR197, PR198, PR199 and PR201 remain unmerged at this checkpoint. Fresh explicit
development approval allowed the same-tool PR195 retry, which succeeded. Remaining
integration requires refreshed review and exact-tree CI; see the linked PRs for later
status. Existing historical tests and provider accounts do not authorize fresh calls and
are not evidence of current end-to-end readiness.

## What the capture tests establish

The [actual route tests](../../api/server/routes/skills.capture.test.js) invoke the existing
`POST /skills/:id/draft` handler with controlled database/permission seams and no provider
calls. They demonstrate:

- A definition and provenance read before a concurrent source change can be combined with
  replaced, added or deleted files read afterward.
- Another Create Draft request can return the same draft before its file copy completes.
- A file-copy failure invokes unconditional cleanup of the new draft, even if a user edit
  arrived after creation. This is a characterized data-loss risk, not a proposed recovery policy.
- Reusing an existing edited Trial draft does not refresh its base or files. A previously
  renamed edited draft survives both success and failure of a fresh draft attempt. The tests
  begin after renaming; they do not exercise the UI rename/sync workflow.

The [datastore tests](../../packages/data-schemas/src/methods/skill.spec.ts), under
`Managed draft capture: datastore characterization`, use real MongoMemoryServer models
and the actual methods. A query-execution barrier pauses only the parent version increment
after the file mutation. Replacement, addition and deletion are visible while the parent
version is unchanged. The barrier uses no sleep-based ordering and releases in cleanup.

Neither suite proves a production deployment reproduces these races, quantifies their
frequency, or verifies stored bytes. The route clones shared storage references rather than
immutable byte snapshots; storage lifetime and integrity need separate acceptance.

## Why this slice contains no capture implementation

[File mutations](../../packages/data-schemas/src/methods/skill.ts) and parent version bumps
are separate operations. [Sync](../../packages/api/src/skills/sync/github.ts) changes files
before committing the definition for existing skills, but creates the parent before files
for new skills. A double-read of parent version can therefore accept a partial generation.
A database snapshot can capture a consistent database instant that is still midway through
that multi-operation sync; snapshot reads alone do not establish a committed source bundle.

Unchanged files can retain older commit metadata because sync skips equal blob SHAs.
Requiring every file commit SHA to equal the parent commit SHA would reject valid bundles.
Moving permission grant later would neither establish source coherence nor solve the
existing-draft path returning a partially initialized draft. No such shortcut or unused
abstract capture layer is introduced.

## Decisions before claiming readiness

1. **Committed bundle representation.** Choose either an immutable manifest with one atomic
   publication pointer, or a transaction protocol covering the relevant sync writes on a
   supported datastore topology. Include all mutation paths and storage retention. This
   choice is not made here; no replica-set migration is assumed or authorized.
2. **Draft initialization and recovery.** Define how incomplete drafts remain unavailable
   to editing/Trial/reuse, how simultaneous creation resolves, and how failed initialization
   preserves any user edits. Unconditional deletion is not an acceptable general policy.
3. **Exact-revision Trial and Publish.** Decide how the committed bundle identity is carried
   through picker selection, Trial evidence and publication, including permission revocation,
   stale provenance, concurrent edits and storage-byte changes. Wire the reviewed boundaries
   to real adapters only after the chosen persistence protocol is proven.
4. **Acceptance scope.** After source integration, explicitly authorize and schedule datastore
   and UI acceptance separately from provider execution. Required negatives include cross-user
   access, stale/missing provenance, initialization failure/retry, lost authorization, and
   mixed-generation capture. Historical success is insufficient.

The next implementation should address the first two decisions together in the existing
draft/sync paths. More dormant contracts would not close the readiness gap. No further
implementation is started by this assessment.
