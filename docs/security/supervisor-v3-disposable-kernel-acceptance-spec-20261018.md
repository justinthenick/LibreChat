# Supervisor v3 — disposable Linux kernel acceptance specification (2026-10-18)

**Design specification only — NOT AUTHORISATION TO EXECUTE.**

Related gating document: [source provenance gate](supervisor-v3-source-provenance-gate-20261018.md). **G0 provenance BLOCKED**; both `privileged_launch()` and the rootless launcher remain disabled. This plan specifies what evidence a future separately approved experiment must produce. It is not a self-executing checklist.

## 1. Execution-environment decision

**Preferred:** a newly provisioned, disposable Linux VM on Clare, isolated from the existing WSL development stack, using an independently reviewed base image, pinned kernel/image/toolchain and a trusted host-side observer. A dedicated **WSL distro is not a separate kernel or a sufficient independent security boundary**; use it only for read-only compatibility discovery or after explicit documented risk acceptance.

**Hard exclusions:** existing `Ubuntu-24.04` WSL production/development services, original private review quarantine/journals (including original review `601ea173-850c-482a-bc8d-8ed05ac8aabf`), NAS, LibreChat production, real API/provider endpoints, live credentials, Windows/WSL `/home`, `/root`, `/mnt`, `/opt`, Docker sockets, SSH agent, host source worktrees, existing project mounts or shared secret stores. Avoid bridged networking, shared clipboard, host-shared folders, and production credentials in the guest. Never touch host firewall policies to force acceptance.

A guest-only scratch directory with a fresh random lease name, restrictive permissions, isolated VM virtual disk and disposable synthetic fixtures is the **sole writable test storage**. Host observation records are kept outside the guest, append-only and hash-pinned; no prompts, tokens or raw secrets in logs.

## 2. Prerequisites / blockers

1. **G0 trusted source** passed by independent build/review evidence. All source, manifest, verified executable and test fixture digests pinned to exact immutable commits.
2. Operator-approved VM creation and privileged/kernel-test scope, separately from this specification. No default authority for root, `sudo`, `setcap`, `unshare`, `bwrap`, kernel settings, API calls or service changes.
3. Verify exact intended process topology: trusted host supervisor → Bubblewrap/bootstrap → unprivileged worker and separately confined mock. The currently assumed direct PID ancestry is **unverified**; test and correct the design before executing.
4. Verify bootstrap capability requirements and exact order: group purge, UID/GID mapping, bounding/effective/permitted/inheritable/ambient drop, `NoNewPrivs`, dumpability, seccomp and isolation, before importing adapter/model code.
5. Confirm **dummy-only, offline, no real-provider** policy; mock fixture cannot open network or receive live credentials. Preparation must be able to stop without touching production.

## 3. Rootless versus privileged topology

**Rootless using Clare's existing user session — NO-GO.** Observed inside Bubblewrap: `uid_map=1000 0 1`, `gid_map=1000 0 1`, `setgroups=deny`, nonempty supplementary groups (including overflow 65534); rootless capability sets zero and `NoNewPrivs=1`, but `Seccomp=0`. With this mapping the planned 60000–64999 target IDs are not mapped and `os.setgroups([])` is unavailable. This is a configuration-specific conclusion, not a general impossibility proof.

A future group-free parent/user-namespace design requires independent threat-model approval and a separately reviewed launcher; **it must not inherit privileged-bootstrap policy by renaming a mode flag**. The privileged-bootstrap design remains `SEALED`; no operator should simply run that reviewed bootstrap with `sudo`.

Linux reference: https://man7.org/linux/man-pages/man7/user_namespaces.7.html

## 4. Required independent host evidence and negative tests

| Contract | Evidence source and positive criterion | Negative cases (must refuse) |
|---|---|---|
| Ownership and provenance | Immutable source manifest, exact Git tree, independent published build attestation and reviewer-approved input hashes | Wrong/missing signatures, wrong tree, manifest drift, unknown binary |
| Process identity | Trusted host observer captures PIDFDs, start ticks, executable inode/content, parentage, launcher args digest and process lifecycle for exact controlled claim | PID recycle, wrong parent, process substitution, unknown child, observer disconnect |
| Leased state | Owner-verified fresh lease; stable source/config/stat identities; no symlink path races; durable SQLite `RESERVED` matches phase, grant, pilot, binding, amount and controlled process claim | Reused lease, changed inode, mismatched stage vs reservation, old journal, SQLite sidecars, ambiguous writes |
| Identity/capabilities | Host-observed real/effective/saved/fs UID/GID as appropriate; **no supplementary groups**, CapInh/CapPrm/CapEff/CapBnd/CapAmb all zero, `NoNewPrivs=1`, nondumpable | Nonempty/overflow group list, nonzero CapInh or any cap, unmapped ID, privilege rebound |
| Namespaces and mounts | Host `/proc/<pid>/ns/*` + mountinfo and source dev/inode prove exact expected process/mount graph; readonly code and only the explicitly allowed state bind | Exposed host home/SSH/Docker socket, unexpected rw bind, shared propagation, symlink/mount substitution |
| Pipes and mock | Exactly five pinned worker pipe endpoints; independent owner/peer PIDFDs, fd numbers, pipe inodes and read/write directions; separately confined mock with bounded I/O | Socket/extra FD, mismatched peer, leak to mock, unexpected stdin/out/err socket, unbounded response |
| Seccomp and egress | Independently tested **effective deny rules** and isolated network namespace. Validate syscall outcomes (including AF_INET/AF_INET6/AF_UNIX as policy requires), inherited FDs and mock's zero egress; `Seccomp:2` alone is insufficient | Can create/connect socket, retain inherited network FD, absent filter, bypass using alternate syscall path |
| Admission/credential | No secret bytes, even dummy, delivered before matching `ADMITTED`, owner-verified durable `RESERVED`, host proofs and single-byte trusted proceed signal | Early credential read, wrong phase/pilot/UID, replay, timeout or missing observer |
| Failure and cleanup | Observer records bounded timeouts, exact claim-owned process/namespace/lease disposal, fresh host policy snapshot; quarantine ambiguous states | Unexpected child survives, changed host policy, incomplete cleanup, unknown stop proof or unrelated PID action |

Source-of-truth documentation: 
- https://man7.org/linux/man-pages/man2/pidfd_open.2.html
- https://man7.org/linux/man-pages/man7/mount_namespaces.7.html
- https://www.man7.org/linux/man-pages/man5/proc_pid_fdinfo.5.html

## 5. Evidence quality and sign-off

- Capture **before/during/after** snapshots from the independent observer: source/VM/binary digests, guest kernel, VM image, host/guest policy, claimed process/lease identities, observation timestamps, test identifiers, actual run results, cleanup status and complete refusals. All secrets redacted.
- Every check must distinguish `OBSERVED`, `INFERRED`, `NOT_RUN`, `BLOCKED` and `PASS`. A configured argument, worker self-report or synthetic unit test is never kernel PASS.
- Fail closed on missing/mismatched/inaccessible evidence. Never reopen the original quarantine, remove a protected journal, replay uncertain provider requests or invent remote STOP.
- Test harness **must not delete or terminate resources it cannot prove it owns**; retain or seal ambiguous test evidence for review.
- Observe source and host config prior to and after tests; do not use Docker/NAS or existing WSL executor as an implicit observer.

## 6. Stage gates — current decisions

| Gate | Acceptance threshold | Current status |
|---|---|---|
| G0 — provenance | Original trusted attestation **or** new independently reviewed exact-source baseline | **BLOCKED** |
| G1 — static/replay | Exact-tree security review, unprivileged regression tests, manifest/preflight reproducibility | Offline tests reported; exact trusted baseline not established |
| G2 — VM preflight | Explicit authorisation, clean disposable guest, independent observer, immutable inputs | **NOT RUN** |
| G3 — kernel boundary | All positive/negative host-observed checks and cleanup evidence; no real credentials | **NOT AUTHORISED / NOT RUN** |
| G4 — dummy credential protocol | Separate approved mock-only exercise with durable reservation, no production endpoint | **NOT AUTHORISED / NOT RUN** |
| G5 — live integration | Separate architecture, deployment, secrets and operational approval | **NO-GO** |

A failed G0 prevents G2–G5. **Do not schedule or invoke a privileged test until a separate approval identifies exact target VM, files, permissions, expected side effects, rollback and evidence-collection plan.**

## 7. Minimum next action

Locate independent v2 authoring/build evidence; failing that, perform an independent source security review and establish a **new** immutable, attestable baseline. Only after G0 clears, specify the guest image and observer identity, then seek explicit authorisation for disposable VM creation. No further production or Clare kernel commands are warranted by this checkpoint alone.
