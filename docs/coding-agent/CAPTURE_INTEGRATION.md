# Managed capture integration checklist

## Closed in the isolated path

`createIsolatedFencedValidatedCapture(connection, authorization)` composes the
existing validator with the existing synthetic fenced store. No new policy,
collection, grant type or transaction implementation is added. Prepared writes
validate complete bundles, then commit through the same grant/state/receipt
transaction. This closes the previously untested connection between those two
prerequisites.

Real MongoDB tests cover malformed bundles, revocation during copying, a
revocation transaction overlapping actual validated completion, ready reuse with
newer edits, historical lost-reply resolution after sync/edit/revocation, and
fresh-epoch recovery. The overlap test holds a synthetic revocation write and
expects MongoDB lock timeout/write conflict, then commits revocation. It does
not simulate every distributed failure or wall-clock expiry ordering.

The unfenced factory remains an isolated fixture. Activation still throws
unconditionally. Reads and receipt resolution remain diagnostics, not authorized
response APIs. Synthetic identities/grants are not production authentication.

## Remaining production dependencies

Observed at preview `c2f132febb09faf9e372f496a41b4e0d443b3372`. This names known
entry points, not certified coverage: audit direct model/bulk callers before
enforcing the contract at a common database boundary. Route-only checks cannot
prove participation. `methods/*` and `config/*` below are under
`packages/data-schemas/src/`.

| Writer/dependency                         | Concrete entry points                                                                                                                                                                             | Required participation and proof                                                                                                                                                                                           |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ACL grants, revocation, public visibility | `methods/aclEntry.ts`: grant, bit modification, revoke, delete-many, bulk writes; `api/server/services/PermissionService.js`; `packages/api/src/acl/accessControlService.ts`                      | Atomically change authoritative permissions and the shared fence. Cover user/group/role/public and inherited entries. Define permission bits per capture operation.                                                        |
| Group membership and external sync        | `methods/userGroup.ts`: add/remove, `syncUserEntraGroups`, update/bulk update/delete/remove-all; `packages/api/src/admin/groups.ts`                                                               | Principal removal must conflict with in-flight capture, including external member IDs. Preserve post-commit cache invalidation; it is not the fence.                                                                       |
| Roles and assignments                     | `methods/role.ts`: updates/deletion, `updateUsersByRole`, `updateUsersRoleByIds`; `methods/accessRole.ts`; admin roles                                                                            | Fence role-derived access and assignment changes. Audit access-role propagation to stored ACL bits. Preserve auth-cache invalidation.                                                                                      |
| Account and tenant state                  | `methods/user.ts`: `updateUser`, `claimSamlIdentity`, `deleteUserById`; admin user deletion; `config/tenantContext.ts`, tenant-isolation plugin                                                   | Define current-user eligibility and tenant/owner policy. Include identity/role/tenant changes, deletion and any suspension writers found. Cached `req.user` and unrelated admission fences do not prove capture authority. |
| Skill lifecycle and source generation     | `methods/skill.ts`: create/update/delete, `deleteUserSkills`, file mutations; `api/server/routes/skills.js`; `packages/api/src/skills/sync/orchestrator.ts`; `api/server/services/Skills/sync.js` | Bind ownership/visibility/deletion to the fence. Publish one immutable validated source generation; separate file/version updates must not create mixed bundles. Provider provenance remains a separate proof.             |
| Expiry and automatic deletion             | ACL `expiredAt` TTL index; user expiry/deletion paths                                                                                                                                             | Specify a time/commit rule and authoritative invalidation. A counter does not stop time and TTL cleanup can lag. Test expiry crossing copy/commit.                                                                         |
| Protected reads and recovery              | Validator reads, prepared `resolve`, `resolveReceipt`                                                                                                                                             | Define current access independently of historical commit evidence. Never expose raw diagnostic reads or treat a digest as a capability. Resolve unknown commits without blind replay.                                      |
| Deployment and history                    | Replica-set support, indexes, epochs/tombstones, immutable generations/blobs, receipts                                                                                                            | Plan migration, retention, rollback and rollout; prove failover and unknown-result behavior before activation.                                                                                                             |

## Approval boundaries

- Read-only inventory, offline design and further isolated tests are authorized.
- Production ACL/membership/account/deletion writer edits are explicitly outside
  this task. Obtain authorization for a concrete proposed code change before
  integrating those paths.
- Permission semantics, actual grants, account/tenant state, public visibility,
  access/security settings and expiry policy changes need explicit user approval.
- Production migration, deployment/activation, retention deletion, credentials,
  provider calls or spending require separate authorization. Green development
  CI does not authorize them.

The smallest next prerequisite is a complete read-only writer/caller inventory
and proposed fence scope/expiry contract, followed by isolated contract tests.
The synthetic per-owner/source grant is not a replacement for the production
multi-principal ACL model.
