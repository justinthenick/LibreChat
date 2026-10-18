# Supervisor v3 — second-pass static audit and draft code allowlist (2026-10-18)

**REVIEW ONLY — NO-GO** for privileged/rootless launch, credentials, kernel acceptance and production. This is an assistant second-pass static review, **not an independent third-party sign-off**.

## Source and rerun

- Unauthenticated source snapshot commit `1fdb1fefb7e6d60dcd1313ae43a4532ac327c68d`, tree `2473a775d4358f388c7d17d1645bb3868e64b667`.
- A separate `git archive` export was byte-equal to all **48** source ZIP entries. AST parsing passed for **37** Python files.
- Re-ran unit tests with no bytecode writes under the unprivileged Linux `nobody` account: **146 supervisor + 51 adapter = 197 PASS**. Preflight PASS verified 47 files and explicitly reported `privileged_launch=SEALED`, `rootless_launch=NOT_IMPLEMENTED`, `actual_host_changes=false`.
- **Build boundary discovered:** running the verifier inside a full `.git` checkout is rejected as `unlisted_code_or_files`; a clean `git archive` export with group-writable files is rejected as `writable_manifest_file`. A clean, non-group-writable source export passed. This needs a reproducible builder specification; neither failed run was a regression test failure in executable logic.

## Confirmed review findings

1. **HIGH: root-capable historical entrypoint.** `isolation/privileged_probe.py` is a standalone, root-only subprocess/cleanup harness with a hardcoded personal Windows mount path and historical service references. Sealing `supervisor/trusted_plan.py::privileged_launch()` does not seal this other entrypoint. Keep it in evidence, but never stage it in any runnable package.
2. **HIGH: broad source mounts.** `supervisor/trusted_plan.py::plan_worker()` currently mounts whole `adapter`, `isolation`, `v2`, `legacy` directories. A byte-pinned minimal stage is not enough until the actual mount inputs are narrowed and observed independently.
3. **HIGH: transitive legacy import.** `adapter/transport.py -> legacy/wire.py -> legacy/pilot.py` is an actual import closure. Do not simply delete `legacy/pilot.py` without refactoring the parser; current worker/mock graph conservatively needs **11** Python modules.
4. **HIGH: dormant broad behaviour in reachable modules.** `v2/broker.py` contains process signal/subprocess helpers; `adapter/transport.py` includes a dormant TLS/provider transport and its own mock subprocess constructor; the production vocabulary remains in `v2/controls.py`. The `LIVE_RELEASE=False` flag helps but does not replace a minimal reviewed executable dependency graph.
5. **HIGH: provenance, license and kernel evidence still missing.** No independently trusted original authoring commit/build attestation or top-level license metadata was found. No effective seccomp/mount/pipe/observer kernel acceptance on a dedicated test VM has occurred. Clare's observed existing rootless mapping/group state remains NO-GO.

## Generated private review artifacts (not committed as executable source)

- Second-pass security report: SHA-256 `bcea635f6eb7523848e9329b4d12bf931ac97dea322d14b48dc42cb0c463dc5f`.
- **DRAFT** file allowlist JSON with full exact file hashes/classification and import graph: SHA-256 `dec4334bfbcfc9728539efef5a06e3c45180dd6220b324cd96230bd84be659fb`.
- Read-only static staging verifier (does not import or run candidate modules): SHA-256 `03f9f5b315b046fb5fe8002967c987419a2a8267dd1e30ed6011c1fbddd5605e`.
- Static verifier tests: clean 11-file candidate module staging **PASS**; injected `isolation/privileged_probe.py` **REFUSED**; modified `adapter/engine.py` **REFUSED**.
- The underlying unauthenticated Git source bundle was already preserved in the prior checkpoint; it has not been published in this GitHub branch.

Local artifact SHA-256 values prove continuity, **not** an independent trust anchor. The allowlist is a draft inventory, **not** an approved runtime package.

## Priority corrections before source baseline approval

1. Independent human/security review of the exact snapshot and component licensing/secret exposure; identify original provenance or approve creation of a **new** signed, immutable source baseline (no retroactive provenance claim).
2. Refactor legacy wire parsing and broker/process helpers into minimal, offline-only modules; remove the transitive import of historical `legacy/pilot.py`. Preserve compatibility and run all negative regressions.
3. Narrow worker/mock mounts to verified, non-writable staged inputs. Ensure historical privileged probes, test helpers and host review modules cannot be imported or executed from the worker.
4. Define a clean, immutable Git export, permissions and hash-attestation build that passes exact membership checks.
5. Only after provenance and independent review, propose a separately authorised disposable VM kernel acceptance exercise. Keep existing Clare WSL/production/quarantine excluded.

**No source code was pushed or deployed. No additional privileged execution was performed.**
