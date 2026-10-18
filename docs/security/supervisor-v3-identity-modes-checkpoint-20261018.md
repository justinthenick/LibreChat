# Supervisor v3 identity-mode separation checkpoint — 2026-10-18

**REVIEW-ONLY / NO-GO:** privileged launch stays SEALED; rootless launch remains NOT_IMPLEMENTED. No credentials, provider traffic, root execution, quarantine modifications or production changes.

## Clare evidence motivating this change

The operator's separate rootless Bubblewrap smoke test succeeded at creating user/network namespaces but reported:

- `uid_map: 1000 0 1`
- `gid_map: 1000 0 1`
- `setgroups: deny`
- `Groups: 65534 65534 65534 65534 65534 65534 1000 65534`

The 60000–64999 post-drop UID/GID of the reviewed privileged-bootstrap plan are **not mapped in this rootless namespace**; its unconditional `os.setgroups([])` cannot work with `setgroups=deny`. In any rootless alternative, the supplementary groups are not empty. User namespace maps are relative to their parent/reader namespace, **not necessarily host root**.

## Correction, complete only for offline review

- `supervisor/identity_modes.py`: strict user/group mapping parser and pure fail-closed compatibility checks for `privileged-bootstrap` and `rootless-review`.
- Privileged mode requires root and target IDs mapped, targets in 60000–64999, and `setgroups=allow`. Rootless-review requires mapped nonzero IDs and already-empty supplementary groups; even compatible data leaves rootless launch unimplemented.
- All results have `launch_authorized=false`, `credential_release_authorized=false`, `kernel_acceptance=NOT_RUN`.
- The existing `supervisor/trusted_plan.py:plan_worker()` refuses `mode='rootless-review'`, so no privileged plan is quietly repurposed as rootless.
- 24 new synthetic negative/positive tests cover Clare's observed mappings, setgroups denial, unmapped IDs, nonempty overflow GIDs, malformed and overlapping maps, inappropriate targets and the sealed execution plans.
- Read-only preflight labels privileged launch SEALED and rootless launch NOT_IMPLEMENTED.

## Unprivileged verification (sandbox, NOT Clare)

- Baseline input candidate SHA-256: `d7bc174b301e0e335e280b627651c5c025927d8579e409a8670223b27b3a5791`.
- New complete candidate ZIP SHA-256: `8297af57c68b8de91b88caafebb809b60e6e51cbb80f974c0db2f2aca506d464`.
- New `MANIFEST.json` SHA-256: `1908ff32f7e652be6c6c838e9c56f2c1497d88f0d37edbc4adbcc62c11f06085`.
- Incremental unified patch SHA-256: `bc3763d910040df114fdce202feb6fa7064c10b10fafd075b0b97b2caaa5bbc1`.
- 128 supervisor tests **PASS** and 51 adapter isolated-entry tests **PASS**, 179 total; executed with bytecode writing disabled and the Linux `nobody` account.
- Manifest file hashes **44/44 PASS**; static preflight **PASS**, `privileged_launch=SEALED`, `rootless_launch=NOT_IMPLEMENTED`.
- Patch replay onto pristine prior review candidate: **PASS**, all 45 archive entries match byte-for-byte.

## Limitations / pending gates

No independent source authenticity trust anchor; locally recorded SHA-256 is continuity only. The module validates caller-provided mappings, **not independently pinned process/namespace identity or capability provenance**. No rootless entrypoint, mount/FD plan or security review exists, and the privileged launcher remains sealed. No integrated acceptance or actual supervisor kernel test was executed on Clare.

Next decision: keep privileged-bootstrap architecture gated and develop a separate rootless proof-of-concept only after its identity and group policy, process topology, mount/pipe/seccomp/cleanup controls and independent provenance have been specified. **Do not change kernel settings, enable sudo launch, inject credentials or alter the existing quarantine.**
