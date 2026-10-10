# Dormant host-only skill bundle snapshots

`packages/api/src/skills/bundles.ts` provides a capture and read boundary for explicit
`name@@skillId@@bundle-v1:digest` selections. It is exported for development use but is
not registered with HTTP routes, the picker, agent initialization, replay, or code execution.
There is no production enablement, storage adapter, database migration, permission change,
or provider call in this implementation.

## Identity and capture

A trusted publisher supplies **one committed manifest**: skill and tenant identity, logical
name, source revision, complete prime definition, and the expected path, MIME type, byte
length and SHA-256 for every file. The publisher must commit the definition and manifest
as one revision before capture. Do not build this manifest by independently reading mutable
Skill and SkillFile rows: the current store updates them separately and cannot establish a
coherent publication that way. A source revision label alone is not proof of an atomic commit.

Capture copies the manifest before awaiting storage. Every streamed file must match its
declared length and hash; missing, replaced, or mixed-revision bytes reject the entire
capture. The snapshot owns immutable manifest JSON and base64 bytes rather than mutable
storage paths, cached text references, or sandbox session IDs. Files are sorted and the
bundle digest binds their manifest and the definition. Limits are 64 files, 5 MiB aggregate
file bytes, and 256 KiB serialized manifest. Capture performs no persistence or authorization;
only a trusted, authorized publisher may call it. Untrusted requests must not provide their
own manifest as evidence of a published revision.

## Supported host reads

`createSkillBundleHost` requires three adapters:

- `getAccess`: authoritative current skill existence, VIEW permission, tenant, activation,
  and agent scope for the authenticated actor. Never supply startup ACL caches or infer
  authority from snapshot possession. Actor identity must come from the authenticated
  request, not user-submitted IDs. Return null for deleted/inaccessible resources.
- `loadSnapshot`: lookup of exactly the requested digest. Missing or evicted snapshots fail
  closed. No fallback to current files, the latest revision, or another same-name skill.
- `inspect`: current content inspection for the whole snapshot before exposing model-bound
  definitions or bytes. Policy failures reject the read without leaking their details.

Each prime/read checks access before loading, copies and validates **the entire** snapshot
(including files not requested), runs current inspection, then checks access again. Tenant,
skill ID, logical name and digest must match the token. Returned buffers and definitions are
fresh copies; callers cannot mutate later reads. `SKILL.md` reads the exact captured body.
Binary and image reads return captured bytes plus MIME type, without live storage URLs.

Publication, sync, or draft edits create a different manifest/snapshot. A retained older pin
continues to identify its original bytes while the actor remains authorized. Deleting a file
from a newer revision does not rewrite a retained snapshot; deleting the skill or revoking
VIEW, tenant membership, activation or agent scope denies subsequent reads. Retention and
eviction policy belong to the future storage adapter. This is content identity, not a claim
that a trial establishes correctness, quality, safety, or author approval.

## Execution and compatibility

`prime` rejects `sandbox-mount` and `execute` before loading any snapshot. Absolute sandbox
paths and traversal are not host bundle paths. No snapshot files are mounted or registered
with execution sessions by this module. It does not revoke content already delivered to a
model or copied by the existing legacy execution flow.

PR #191's `name@@skillId@@definitionDigest` remains definition-only and unchanged. Legacy
name-only behavior remains unchanged. This host service accepts neither format, and the
existing PR #191 resolver rejects `bundle-v1` tokens rather than silently downgrading them.
The current Trial badge remains lifecycle state; it does not certify whole-bundle identity.

Before activation, implement and independently review the committed-manifest publisher and
snapshot storage adapter; authenticated route/actor wiring; actual VIEW/tenant/agent-scope
and current-policy adapters; and snapshot-token persistence through messages/checkpoints.
Every replay path must resolve the same snapshot or reject. Never send a bundle pin through
the existing name-based replay/mount path. Existing reusable sandbox copies bypass the host
reader, so executable pinned bundles additionally require isolated sessions/mounts and
authorization at every execution boundary. That separate work must precede any execution
enablement or revocation guarantee for sandbox reads.

## Offline acceptance

Synthetic tests exercise actual capture, token and read functions with in-memory source,
store, policy and mutable authorization state. They cover byte/definition immutability,
manifest ordering, concurrent draft edits and sync corruption, publication identities,
deleted resources and evicted snapshots, cross-tenant/user/agent reads, revocation during
loading/inspection and after cached reads, whole-bundle corruption, path traversal, capture
limits, policy rejection, legacy/PR #191 compatibility and unsupported execution rejection.
They do not establish production behavior or exercise live provider/storage accounts.
