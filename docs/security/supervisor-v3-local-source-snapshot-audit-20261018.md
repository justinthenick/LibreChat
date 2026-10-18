# Supervisor v3 — reproducible local source snapshot and static audit (2026-10-18)

**Outcome:** a byte-for-byte source snapshot exists for independent review, but **G0 independent source provenance remains BLOCKED**. **No new privileged kernel work or production change is authorised.**

## Reproducible, untrusted source snapshot

The user-uploaded v2 ZIP and latest rootless-feasibility v3 ZIP were checked against their existing continuity SHA-256 values. The latest v3 archive has 48 entries, with 47 matching internal-manifest declarations and no duplicate/traversal/symlink ZIP entries. This does not establish publisher authorship.

A local Git repository was created from the **exact v3 candidate archive bytes** with conspicuous unauthenticated author metadata:

- Local review commit: `1fdb1fefb7e6d60dcd1313ae43a4532ac327c68d`
- Local review tree: `2473a775d4358f388c7d17d1645bb3868e64b667`
- Bundle file: `LibreChat-Supervisor-v3-untrusted-source-snapshot.bundle`
- Bundle SHA-256: `c1ec14150427e0250a2c77130e18474bccf8b9518cf0453393f3834963d401d0`
- `git bundle verify`: PASS; independently replayed the bundle into a temporary clone: **48/48 source entries byte-for-byte equal to the input ZIP**.

**This is a new *local snapshot commit*, not an authenticated original authoring commit or independently approved source baseline.** Keep raw bundle out of the public repository until an explicit security/privacy/licensing review.

Offline unit tests on the exact source rerun under unprivileged Linux user `nobody`, bytecode disabled: **146 supervisor and 51 adapter, 197 PASS**. These are not kernel security acceptance tests.

## Material source finding: root-capable legacy harness remains in the ZIP

`isolation/privileged_probe.py` contains a separate root-only main path, historical hardcoded Windows/Clare-mounted source paths and service names, subprocess Bubblewrap launches, synthetic credential transfer, process termination and cleanup logic. It was **not executed** in this audit. The separate `supervisor/trusted_plan.py::privileged_launch` refusal stays sealed, but that cannot seal this stand-alone historical test harness from manual invocation.

**Release block:** future runtime source allowlist MUST exclude this legacy privileged probe and other unreviewed root/test entrypoints, while keeping the complete original ZIP unchanged as evidence. Never describe this whole review ZIP as unable to run privileged code. Do not push its raw source into the public repository.

Other blockers:
- The `/proc` collectors depend on external observer authority and independently pinned expected process, executable and descriptor identities; PIDFD liveness is not authentication.
- `Seccomp=2` and filter counts are not evidence of the actual deny rules or zero egress.
- Clare's existing rootless namespace has `setgroups=deny`, nonempty groups and incompatible UID/GID mapping; the zero-group worker contract remains unsatisfied.
- The review archive has no top-level `LICENSE`/`COPYING`/`NOTICE` file; independently check component redistribution rights.
- No independent reviewer/security sign-off or attested build source exists yet.

## Next gates

1. Independent review and signoff on the exact local commit/tree (or genuinely recover independently attested original source). **Do not use the hash found in the ZIP as a trust pin.**
2. Before public sharing, audit hardcoded paths/credentials/licensing and split historical evidence from a minimal, independently reviewed runtime allowlist.
3. Only after G0 independently clears: proceed to a separately approved disposable VM acceptance harness; real credentials/provider calls remain NO-GO.

Review/report file generated locally: `LibreChat-Supervisor-v3-provenance-and-source-audit-20261018.md`; SHA-256 `f8276e2c5bc8a86080c7ac6851c0edcf5577e7afd44d1747333fa13d0144388c`.

**No executable source or raw bundle uploaded to the public GitHub repository; documentation only.**
