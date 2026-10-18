# Supervisor v3 running-executable and pipe-peer checkpoint — 2026-10-18

**REVIEW ONLY — privileged launch SEALED, kernel acceptance NOT RUN.** The original quarantine, protected journals, production environment and live credentials were not accessed or modified.

## Input and artifact continuity

- Prior v3 executable-identity review candidate (input): `cea37060fc3a0bad0b141aeefd0da905fe7452590a388f07e3023c68f02c6fc8` SHA-256.
- **New complete local review candidate ZIP:** `d7bc174b301e0e335e280b627651c5c025927d8579e409a8670223b27b3a5791` SHA-256.
- **New MANIFEST.json:** `3c47dd12bcf49d615eedbac16cf3d37f4505edeb79ce69b12140c697ba8eec46` SHA-256.
- **Incremental patch from previous candidate:** `f1a320852fee1f18187e4a80cac652535fdf27da89055b9aca47ea380b50a9f0` SHA-256.
- ZIP has 42 entries, of which 41 source/doc files match the regenerated manifest.
- `git apply --check` and `git apply` succeeded in a clean replay of the prior ZIP; **all 42 files reproduced byte-for-byte**.
- These hashes prove **local continuity only**, not independent provenance. Source and patch are held as conversation attachments, not pushed to the public repository.

## Added functionality — offline review prerequisites

- New `supervisor/runtime_binding.py` inspects explicitly nominated `/proc/<pid>/exe` with PIDFD liveness, PID/start-tick checks, bounded binary hashing and device/inode/size/content equality against separately verified binary evidence. Access denial (including protected nondumpable processes), unreadable image, stale PID, changed inode or digest **refuse**. No elevated fallback.
- Peer evidence collection uses **only independently nominated** peer PIDs and FDs, PIDFD lifetimes, repeated PID/FD snapshots. No unrelated process scanning.
- Five worker pipe-role endpoints are checked against explicitly pinned peer PID/start-ticks/FD, matching pipe inode and complementary read/write access. Pipe inode equality is **not** authority or proof of who provisioned the pipe.
- A supplemental review-evidence validator requires running-image and peer-binding observations in addition to the previous durable admission checks. It is not a kernel acceptance gate and never authorises a credential.
- Added `supervisor/test_runtime_binding.py` with 25 unique positive/negative tests and `supervisor/RUNTIME_BINDING_REVIEW.md`.

## Validation in local sandbox — not Clare

- **104 supervisor tests PASS**, Python 3.13.5, unprivileged account `nobody`, bytecode disabled.
- **51 adapter isolated-entry tests PASS**, same unprivileged context.
- **155/155 offline unit tests PASS**.
- Unprivileged self-process `/proc/self/exe` read-only smoke PASS; its self-measured reference SHA is **not independent provenance**.
- Manifest source preflight **PASS** (41 files); `privileged_launch=SEALED`, `actual_host_changes=false`, `mock_endpoint=NOT_RUN`.
- No Bubblewrap execution, root launch, disposable kernel acceptance, live credentials, model traffic or production changes.

## Blocked gates

1. Independently authenticated source and runtime binary reference pins, and separately trusted host observer identity.
2. Exact controlled Bubblewrap PID/exec and ancestry topology verified against the actual Linux process tree. Caller-supplied PIDs alone cannot establish authority.
3. Real mount-source/inode binding, procfs provenance, lease and mock isolation, effective seccomp/no-egress evidence, host-policy preservation, and failure cleanup.
4. Review and execution of a disposable authorised kernel acceptance harness **on Clare**, with the original quarantine and production kept strictly excluded.

**Never unseal `privileged_launch()` or treat the 155 tests as proof of kernel containment.**
