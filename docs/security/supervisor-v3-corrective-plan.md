# LibreChat Pilot — Supervisor v3 corrective work

Status: **REVIEW ONLY / NO-GO** for privileged launch, credential release, live provider traffic, kernel acceptance, production integration.

## Source and provenance boundary

- Baseline branch: `server/synology`.
- Reviewed local package (operator-reported): `LibreChat-Pilot-Kernel-Supervisor-Review-v2.zip`.
- Observed ZIP SHA-256: `AB4E6CEE4EA5136DDC3AEF1DDE2A37FBF59B2E67B61A6F83C401CCE91A7034A7`.
- Observed internal `MANIFEST.json` SHA-256: `385D310D310E438EA4B782A64854C7787A27AC1E92844BC386F7AF39449B06CD`.
- Operator-reported internal consistency: 27 declared file hashes matched, no duplicate/unlisted ZIP entries.
- **These are observations, not independent authenticity/provenance verification.**
- Supervisor v2 package source has *not* been imported into this branch. Do not reconstruct or copy partial code excerpts as authoritative source.

## P0 fixes, fail-closed regression tests first

1. **Bind durable admission consistently.**
   - Require `stage.binding == reservation.binding == independently expected reservation binding`.
   - Validate grant binding and expected pilot/phase/UID against authoritative, owner-verified state.
   - Reject stage/reservation disagreement even when `reservation.binding` matches the caller expectation.
   - Reject stale grants, duplicate admissions, mismatched amounts, absent or ambiguous records.

2. **Bind host-observed process to the exact controlled launch.**
   - Define controller vs. worker PID semantics before adding an equality assertion.
   - Independently bind controller PID/start ticks, worker PID/start ticks, ancestry, and the exact Bubblewrap instance.
   - Reject PID reuse, swapped/forged observations, process-tree mismatches and missing host evidence.

3. **Independently verify all inherited descriptors.**
   - Prove exactly five distinct, expected pipe endpoints and verified direction/ownership/inheritance.
   - Reject sockets, excess FDs, replaced endpoints and descriptor leaks to the mock responder.

4. **Prove effective isolation from the host, not from worker self-report.**
   - Check actual namespaces, mounts, source inodes/hashes, UID/GID, supplementary groups, capability sets (including `CapInh`), `NoNewPrivs`, effective seccomp restrictions and source/lease identity.
   - Deny dummy credential release until the durable reservation, host observations and supervisor proceed signal are independently satisfied.
   - Treat failures, timeouts and cleanup ambiguity as NO-GO, preserving evidence.

## P1 hardening and test cases

- Require actual non-dumpable state; never only return a diagnostic Boolean.
- Determine supported capability range via `/proc/sys/kernel/cap_last_cap` (with appropriate failure handling), not a hardcoded `range(41)`.
- Review TOCTOU/symlink/inode checks for manifest, leases, DB and mounts; use pinned descriptors or equivalent guarantees.
- Verify seccomp is actually loaded/effective and forbids network creation even when inherited FDs are considered.
- Verify all five capability sets and ensure no privilege rebound after the bootstrap.
- Confirm static preflight cannot be misrepresented as kernel acceptance.

## Required gates

- **A — Internal integrity:** operator-reported PASS; not independent provenance.
- **B — Trusted provenance:** PENDING; obtain independent, authoritative manifest/package digest and original source.
- **C — Offline tests:** PENDING; run no-credential, unprivileged tests against complete verified source with bytecode disabled; capture machine-readable results.
- **D — Kernel acceptance:** BLOCKED pending explicit authorization and separately reviewed disposable test environment. Host-collected evidence required.
- **E — Production/real provider:** NO-GO.

## Restrictions

Do not alter the original quarantine, protected journals, existing production services, active credentials, host firewall, real API projects, or deployment configuration. Do not enable `privileged_launch()`. Do not inject credentials, make model/provider calls, replay ambiguous runs or synthesize STOP evidence. Do not treat a ZIP hash sourced from that ZIP as its own independent trust anchor.

## Next implementation action

Acquire the **complete original Supervisor v2 package** in a controlled, non-production development workspace, verify its provenance against an independently supplied checksum, reproduce baseline offline tests, then add deliberately failing P0 regression tests before making the corresponding code fixes. Preserve the v2 artifact unchanged and work only on a new v3 copy.
