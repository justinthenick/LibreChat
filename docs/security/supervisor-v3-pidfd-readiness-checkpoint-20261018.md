# Supervisor v3 PIDFD and Linux readiness checkpoint — 2026-10-18

**REVIEW-ONLY / NO-GO.** No privileged launch, kernel acceptance, credentials, network provider calls or production integration.

## Source continuity and review artifacts

Based on the prior host-observer candidate, whose locally verified ZIP SHA-256 is `db04c9b06a3f3c537e19f7725499c45c3bfca03eefd47c518754def850ff4f06`.

- New PIDFD/readiness review candidate ZIP SHA-256: `c40626691882e3647b70c7e2f65938854c1a241bd9f37960e2251a338d2ce1d5`.
- New manifest SHA-256: `198191ce626803f11cca31034dd8c50c41f9dd94cfddca9f75fa87da4a4ed018`.
- Incremental patch SHA-256: `efff07fb68dc78714508b0caf097c6357d1e3c6b1ffa4f7b10bbe09669f0f563`.
- Patch applies to the unchanged prior candidate and reproduces all files byte-for-byte.
- ZIP internal manifest verification: **35/35 matched**.

All fingerprints are continuity markers generated from available artifacts; independent package provenance is not yet established. The source itself remains outside this public GitHub repository pending review.

## Completed increment

- Added `os.pidfd_open` lifetime pins for separately nominated controller, Bubblewrap and worker processes before reading `/proc`. PIDFD liveness is rechecked during and after collection, with explicit close on completion/refusal; absence of support and process exits refuse rather than falling back.
- Corrected bounded `/proc` reads to limit memory consumption *before* checking content length.
- Added read-only `supervisor/operator_readiness.py` for Linux prerequisites: pinned executable-path presence, procfs, current-process pidfd self-check, capability-range readability, non-root context. It never runs Bubblewrap or accepts a kernel boundary.
- Added/refined negative tests and review documents.

## Tests and gate

Final test execution was explicitly unprivileged via `runuser -u nobody`, Python bytecode disabled:

- **62 supervisor tests passed**.
- **51 adapter isolated-entry tests passed**.
- Total **113 unit tests passed**.
- Read-only manifest preflight **PASS**, all 35 declared files, privileged launch sealed.
- Operator readiness on the container: **BLOCKED** (Bubblewrap executable absent); pidfd self-check PASS; unprivileged check PASS.
- Actual host acceptance: **NOT_RUN**. The checks above were **not run on Clare**.

## Residual gaps

- Independent trusted source provenance and observer authority remain missing.
- PIDFDs pin lifetimes but do not independently authenticate the observer, executable inode, lease, mount source, pipe peer, or command provenance.
- Seccomp filter semantics, actual mounts, mock endpoint isolation, preserved host policy and failure cleanup need independent test evidence.
- Direct controller→bwrap→worker ancestry remains a hypothesis to be validated against the reviewed execution design.
- Before disposable kernel tests: explicit authorisation, security review of exact Bubblewrap mount/device/seccomp/descriptors/cleanup, independently pinned observer and lease. Do not alter original quarantine, privileged service, production credentials or policies.

**Do not enable `privileged_launch()` or use the readiness report as authority for real provider traffic.**
