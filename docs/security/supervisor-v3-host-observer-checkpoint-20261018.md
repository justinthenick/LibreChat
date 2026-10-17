# Supervisor v3 host-observer checkpoint — 2026-10-18

**REVIEW-ONLY / NO-GO** for privileged execution, credentials, actual kernel acceptance, billable provider traffic and production.

## Controlled artifacts, held outside the GitHub repository

The complete review candidate and its incremental patch were generated from the operator-uploaded Supervisor v2 ZIP and prior local Supervisor v3 review candidate. No live production or original quarantine sources were modified.

- Baseline v2 ZIP SHA-256: `ab4e6cee4ea5136ddc3aef1dde2a37fbf59b2e67b61a6f83c401cce91a7034a7`.
- Prior v3 candidate ZIP SHA-256: `283bfc72add32bdcf48592d9bd31d556927397f547cf10cbeaf1fc3a6d499a4e`.
- **New v3 host-observer candidate ZIP SHA-256:** `db04c9b06a3f3c537e19f7725499c45c3bfca03eefd47c518754def850ff4f06`.
- **New candidate manifest SHA-256:** `b7481193d6988ebcc4d6976d217c9cd2c524e2feee86835452ca03d766acea04`.
- **Incremental patch SHA-256:** `a72d7857711f85fe806bd1e5d3184415da8983a3f44e2d5ef4c9d25bddc5157e`.

These values are local observations, **not independent signed provenance**. The complete source is not being pushed to the public repository yet.

## Completed offline work

- Implemented `supervisor/host_observer.py`, a bounded, read-only Linux `/proc` snapshot collector for operator-designated controller, Bubblewrap and worker PIDs.
- Snapshot includes PID, PPID, start ticks, status UID/GID, groups, five capability sets, NoNewPrivs, seccomp mode/count, namespaces, Bubblewrap NUL-delimited cmdline digest and worker FD inventory/directions.
- Rejects mismatched controller ancestry, namespace baseline, absent evidence, unexpected descriptors and changes observed in repeat process/status/FD/namespace reads.
- Tightened `supervisor/trusted_plan.py` to reject socket FDs inherited in stdio slots 0–2.
- Added `supervisor/test_host_observer.py` with synthetic /proc fixtures, positive integration with v3's existing verifier and negative tests.

**Validation (unprivileged, bytecode disabled, local sandbox):**
- 49 supervisor tests: **PASS**.
- 51 adapter isolated-entry tests: **PASS**.
- Total: **100 tests PASS**.
- Read-only local `/proc/self` parser smoke: **PASS**, not a containment test.
- Exact manifest internal integrity: **32/32 files PASS**.
- Read-only preflight: **PASS**, `privileged_launch=SEALED`, `actual_host_changes=false`.
- Patch applied to a clean copy of prior v3 candidate, reproducing all file bytes: **PASS**.

## Blockers before any controlled kernel acceptance

- No trusted external provenance for input ZIP or new candidate; operator must establish provenance separately.
- A function reading `/proc` is not itself a trusted observer service. Observer context, mount identity, PID identity via pidfds, process ownership, lease binding, peer pipe endpoints, and atomicity remain open.
- Command-line digest of observed `/proc/<pid>/cmdline` must be compared to an independently pinned exact command, not used as its own authority.
- Current seccomp observation reports **mode/count**, not effective filter instructions or proof of zero network egress.
- Stdio resource identity, mount/source inodes, mock endpoint isolation, post-failure cleanup, and host policy preservation must be established before authorised disposable root tests.
- The direct controller->bwrap->worker ancestry assumption must be tested against the actual reviewed deployment design; if incorrect, revise the model fail-closed rather than loosening checks.

Do not enable `privileged_launch()`, release dummy or real credentials, or modify production. Retain this commit as documentation-only until source provenance and review are resolved.
