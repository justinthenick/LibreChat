# Supervisor v3 executable-file identity checkpoint — 2026-10-18

**REVIEW-ONLY / NO-GO.** No privileged launch, host kernel acceptance, credential release, real provider traffic, production or original quarantine changes.

## Input continuity

The prior PIDFD/readiness candidate ZIP was verified locally at SHA-256 `c40626691882e3647b70c7e2f65938854c1a241bd9f37960e2251a338d2ce1d5`. This is a continuity marker, **not an independent source-authenticity proof**.

## New bounded, read-only disk executable checks

- `supervisor/binary_identity.py`: compare on-disk `/usr/bin/bwrap` and `/usr/bin/python3` against **externally supplied** SHA-256 pins; verify owner, writable bits, trusted path components, symlink restrictions, file-descriptor-based digest and before/after inode/metadata consistency.
- `supervisor/operator_readiness.py` now accepts paired `--bwrap-sha` and `--python-sha` inputs. If either is missing the new mandatory `operator_binary_hashes_matched` gate is false and readiness remains `BLOCKED`. Invalid/mismatched pins refuse. `source_provenance=UNVERIFIED` remains explicit.
- Added `supervisor/test_binary_identity.py` and added readiness negative tests. These checks are **on-disk file checks only**, **not** proof of the running process's executable or mount identity.

## Tests and artifacts

- Supervisor tests: **79 PASS** under unprivileged `nobody`, bytecode disabled.
- Adapter isolated-entry tests: **51 PASS** under unprivileged `nobody`, bytecode disabled.
- Total unit tests: **130 PASS**, Python **3.13.5** in this sandbox, **not on Clare**.
- Manifest entries: **38**, read-only preflight **PASS** and `privileged_launch=SEALED`.
- Readiness here: **BLOCKED**, Bubblewrap not installed and operator binary pins not provided; `kernel_acceptance=NOT_RUN`.
- Replaying the incremental patch on a pristine prior v3 candidate reproduced all 39 archive entries (including the manifest) byte-for-byte.

**Updated candidate ZIP SHA-256:** `cea37060fc3a0bad0b141aeefd0da905fe7452590a388f07e3023c68f02c6fc8`.

**Updated candidate manifest SHA-256:** `c8fd706946a51c1c80b5606be86430fb6398f546ff30599e4227aadce257ae2a`.

**Incremental patch SHA-256:** `a08c1badbd5156d2460389f29502bbd94894709cf6aade2e9d834f105baf4606`.

Candidate source and patch remain as conversation artifacts and have **not** been pushed to the public repository.

## Remaining blocking risks

- Independent original package provenance and externally trusted binary pins are not established.
- Pinned **disk** binary files do not establish exact `/proc/<pid>/exe` for the controlled process, runtime mount identity or trusted observer authority.
- Actual bind mount/source inode attestation, cross-process pipe peer identity, seccomp policy effectiveness, no-egress testing, disposal and failure cleanup still require an authorised controlled Linux harness.
- Direct controller -> bwrap -> worker ancestry model must be checked against actual reviewed launch topology.
- Host/production policies, protected journals, original quarantine and credentials remain out of scope.

**Do not unseal `privileged_launch()`, substitute self-calculated hashes for independent provenance, or call this kernel acceptance.**
