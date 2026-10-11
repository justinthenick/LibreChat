# Pinned GitHub generations

`prepareGitHubSkillGeneration` closes the source-acquisition prerequisite for
managed capture: it reads one selected commit through the existing GitHub
adapter, builds a complete bundle, and prepares the existing validated source
generation transaction. It does not assemble a generation from mutable Skill
and SkillFile rows. The caller retains the existing CAS and receipt-resolution
protocol; an unknown commit outcome never authorizes blind replay.

The selected host mapping must match configured tenant, source ID, repository
and permitted path. The commit must be a full GitHub SHA-1 commit ID. This
mapping is internal data, not a request capability: the future production
adapter must load and authorize it from authoritative state. No source owner or
new PUBLIC grant is synthesized.

Strict Git verification is opt-in and leaves legacy mirror synchronization
unchanged. Every traversed nonrecursive tree is checked against its Git tree
hash. Blob identity, canonical base64, declared and actual byte lengths and Git
blob hash must agree. The commit-to-root-tree association still trusts GitHub's
authenticated commit response; this is not independent commit-object or commit
signature verification. Hashes establish content integrity, not application
authorization or permission to execute the content.

The selected package must contain exactly one direct case-insensitive SKILL.md.
Unsupported paths, case collisions, symlinks, submodules, truncated trees and
incomplete or mismatched blobs reject the entire generation. The reader bounds
tree depth/entries, streamed response size, file count and total package bytes
(5 MiB including SKILL.md, at most 64 auxiliary files). It retains validated
frontmatter and derived invocation/tool declarations. Before recursive validation
or manifest serialization, frontmatter is projected with at most 4,096 expanded
values, depth 5, and a 128 KiB string/key budget; cycles reject. Canonical
repository-root source paths are accepted after schema normalization. Strict
HTTP error responses cancel their unread bodies. Auxiliary bytes use an
opaque MIME type; this path neither renders nor executes them. Version 1 is the
immutable upstream definition baseline; the existing generation counter tracks
successive publications.

Offline tests use real Git objects, the real adapter with an injected HTTP
boundary, and a real Mongo replica set. They exercise generation CAS, preservation
of a draft's original generation during later source sync, exact historical
receipt recovery and zero publication on malformed acquisition.

## Remaining activation prerequisites

The approved first release is Create Draft, view/edit and safe recovery from
selected tenant-local GitHub sources with existing direct nonexpiring PUBLIC
VIEW. Drafts require a private direct nonexpiring USER owner grant, with current
SKILLS USE/CREATE requirements. Source access must survive through successful
copy completion. After completion the draft remains the owner's copy; source
revocation alone must not prohibit later owner-authorized access. The current
synthetic source-scoped edit fence is not that production contract.

An expired, deleted, banned or otherwise ineligible account must not complete a
copy or later access its draft. Eligibility must participate at commit, not be
approximated by a precheck or delayed TTL cleanup. Do not activate this producer
as a route, scheduler or editor backend until the following work is complete:

- Load the selected source mapping and publish immutable generations under
  current authority; compose the existing route/editor/recovery state machine
  with atomic private-draft creation and its USER owner ACL.
- Separate source-access authority before completion from owner/account/draft
  authority afterwards; enforce both against concurrent writer changes.
- Implement coordinated participation for the writers catalogued in
  [CAPTURE_INTEGRATION.md](CAPTURE_INTEGRATION.md), including direct/bulk and
  background paths. Cache invalidation is still required, but is not the fence.
- Define durable ban authority and ordering with every relevant ban writer.
  Current cache-backed bans cannot atomically conflict with a Mongo capture
  transaction. Preserve current enforcement while preparing a coordinated
  design; do not install a weaker precheck-only fallback.
- Resolve user-expiry compatibility: createUser can set expiresAt seven days in
  the future, the schema adds a seven-day TTL offset, and updateUser unsets
  expiresAt even for preference updates. A commit-time eligibility definition
  must not silently reinterpret existing accounts or deployed indexes.

The proposed coordinated security change needs an explicit writer/reader
inventory, migration and rollback plan, cache/DB dual-state ordering, TTL and
clock rules, concurrent ban/unban/delete/expiry tests, and compatibility evidence
for existing workflows. Development design is authorized; changing real ban or
account settings, production collections/indexes/grants, deployment and
activation require separate approval. No migration or policy writer is changed
here. Existing activation functions remain unconditionally disabled. Trial,
Publish and sharing are outside this new flow.
