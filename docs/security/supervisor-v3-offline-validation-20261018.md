# Supervisor v3 offline correction checkpoint — 2026-10-18

**Status: REVIEW-ONLY. No kernel acceptance, privileged launch, credential release or production integration.**

## Attached source baseline
Operator-uploaded `LibreChat-Pilot-Kernel-Supervisor-Review-v2(1).zip` matched previously reported archive SHA-256 `ab4e6cee4ea5136ddc3aef1dde2a37fbf59b2e67b61a6f83c401cce91a7034a7`, and original manifest SHA-256 `385d310d310e438ea4b782a64854c7787a27ac1e92844bc386f7af39449b06cd`. All 27 files matched the embedded manifest; this **does not establish independent provenance**.

## Corrective working copy completed

A new, **local review candidate** was derived from that upload. It is **not committed to this public repository** pending provenance and source sanitisation. The actual candidate and unified patch were supplied as downloadable conversation artifacts, not imported into the production repo.

Changed code:
- `supervisor/trusted_plan.py`: compare stage binding to expected reservation binding; require independently host-observed controller/Bubblewrap/worker chain, pinned argv digest and descriptor snapshot; verify CapInh and seccomp.
- `isolation/adapter_bootstrap.py`: derive capability drop range from `/proc/sys/kernel/cap_last_cap` rather than hardcoded 0–40.
- `isolation/boundary.py`: refuse if non-dumpability is not established; check CapInh.
- `supervisor/test_trusted_plan.py`: 14 new fail-closed negative regressions.

Results from unprivileged sandbox tests with `PYTHONDONTWRITEBYTECODE=1`:
- Supervisor suite: **33 passed**.
- Adapter isolated-entry suite: **51 passed**.
- Preflight: **PASS**, validating 29 included source/docs files, with `privileged_launch=SEALED`, `actual_host_changes=false`, `mock_endpoint=NOT_RUN`.
- Candidate ZIP SHA-256: `283bfc72add32bdcf48592d9bd31d556927397f547cf10cbeaf1fc3a6d499a4e`.
- Candidate `MANIFEST.json` SHA-256: `262d85e7955b3dd57f056082c0286acd189c9efaad33a8877e8b1b23cd0b5e08`.
- Unified patch SHA-256: `3ba3c0ec76af542fb52dd803a4a12fe8b0a69936d416411a075bfe124b2302fb`.

## Remaining blockers
- Neither source nor candidate has been authenticated by a *trusted independent* signing/checksum channel.
- Structural host-evidence validators do not independently collect `/proc` observations or establish their provenance.
- Durable lease ownership, exact mount inode verification, mock isolation, host seccomp policy, process ancestry collection and cleanup evidence remain unimplemented.
- No actual kernel containment tests, root launch, real provider calls or credential release were performed.

Next: review the candidate diff and source provenance, then stage code on a separately controlled non-production test branch after secure source sanitisation and an independent Linux acceptance plan. **Do not unseal `privileged_launch()`.**
