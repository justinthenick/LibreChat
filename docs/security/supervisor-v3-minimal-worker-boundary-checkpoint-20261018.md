# Supervisor v3 — minimal worker source boundary checkpoint (2026-10-18)

**REVIEW ONLY — G0 provenance BLOCKED; privileged launch SEALED; rootless launch NOT IMPLEMENTED; no kernel acceptance.** Production, Clare's WSL development environment, original quarantine and credentials were not changed.

## Source base and local artifacts

Derived from the previously reported rootless-feasibility review ZIP SHA-256 `2e9000921bf5194ac3be93e1f8feb6dadb0c7d5af10a8df16fb199554000ad15` (48 original files; 47 manifest hashes matched). Local continuity is not independent publisher/author provenance.

- **Complete updated v3 review candidate ZIP SHA-256**: `b2f75e62524db1b6e5d8705eaf370506c27b81e597d3fb3c4ac8bea209998875`.
- Revised `MANIFEST.json` SHA-256: `89022f2d185cff64055d59e783dc735df307fe3957b1c3e1e72fc27607fe8a3f`.
- **Nine-module minimal worker-stage review ZIP SHA-256**: `fdc7c5d0c525715a86dce3969511fbd04221af062321cc0c0b1cf47198698241`.
- Incremental patch SHA-256: `7155c000e49570fc28bae6bf2764390cc26bfecf22a481fff2c49933a6ef7c71`.
- Local review report SHA-256: `d40fa82790c6ead2aee624fbce317d08f46124ff6e2b5162ef33e38b4a85b1ad`.

The complete source, worker stage and patch remain outside the public GitHub repository, available only as conversation artifacts pending independent security/licensing review. Never infer original authoring provenance from these local digests.

## Code changes — staged review candidate, not committed here

1. Added `adapter/response_codec.py`, a bounded HTTP response parser that no longer imports the historical `legacy/wire.py -> legacy/pilot.py` chain.
2. Added `v2/offline_runtime.py` for narrow adapter-required process identity/usage/cleanup functions, with live TLS admission explicitly refused. This module still contains identity-checked process-signal cleanup and needs independent scrutiny before execution.
3. Changed `adapter/engine.py` and `adapter/transport.py` to import only the narrow modules; `engine.build_hash()` now covers exactly nine worker files and refuses missing inputs. `v2/broker.py`, `legacy/pilot.py` and `legacy/wire.py` no longer form the worker import closure.
4. Changed `supervisor/trusted_plan.py::plan_worker` to construct **nine per-file `--ro-bind` worker source mounts**, never whole `adapter`, `isolation`, `legacy` or `v2` directory binds; sole planned writable bind remains disposable state. Standard system library mounts and the read-only config bind remain broad/subject to review. This is **planned configuration only**, not proven kernel enforcement.
5. Read-only `supervisor/preflight.py` checks all proposed source names are present/syntactically parseable, in addition to existing exact manifest membership checks. Added six static/offline tests in `supervisor/test_minimal_runtime_boundary.py`.

### Exact nine-file worker source list

```text
adapter/isolated_entry.py
adapter/engine.py
adapter/transport.py
adapter/response_codec.py
v2/controls.py
v2/offline_runtime.py
isolation/adapter_bootstrap.py
isolation/boundary.py
legacy/isolation.py
```

The separately staged worker review ZIP contains **only those nine source files plus its self-describing `STAGE_MANIFEST.json`** (10 ZIP entries). Historical `isolation/privileged_probe.py`, pilot/broker/wire code, tests and the mock endpoint are excluded from the worker stage; the **full v3 review ZIP preserves historical evidence unchanged where applicable**. The separately confined mock requires independent plan/review.

## Reproduced unprivileged tests — sandbox, NOT Clare

- Supervisor: **152 PASS**.
- Adapter isolated-entry: **51 PASS**.
- Total: **203 unit tests PASS**, `PYTHONDONTWRITEBYTECODE=1`, `runuser -u nobody`.
- Read-only manifest preflight: **PASS**, 50/50 files; `privileged_launch=SEALED`, `rootless_launch=NOT_IMPLEMENTED`, `mock_endpoint=NOT_RUN`, `actual_host_changes=false`.
- Worker plan static boundary: **nine per-file source binds, no directory bind**; no `--share-net`; PASS.
- Nine-module staged imports work without `pilot`, `wire`, `broker` or privileged probe: PASS.
- Stage hashes and archive contents: PASS.
- Incremental patch applied to the prior candidate and reproduced **51/51 files byte-for-byte**, including the revised manifest: PASS.

## Blockers

- **G0 independent source provenance, source licence and an independent code/security reviewer remain BLOCKED.** A created artifact/hash or ChatGPT source audit is not third-party attestation.
- Actual Bubblewrap/kernel mounts, process identities, source inodes, seccomp, pipe peer authority, mock isolation, cleanup and no-egress **NOT RUN**.
- Existing Clare rootless UID/GID maps, nonempty supplementary groups and `setgroups=deny` still do not meet the zero-group worker contract.
- `offline_runtime` still contains signal-based cleanup and `v2/controls.py` retains broader policy vocabulary; further review and minimisation needed.
- No privileged worker, rootless launcher, dummy/live credential or model/provider traffic was executed.

**Decision: static code surface reduction PASS for continued security review ONLY. Do not publish/release executable code or perform kernel acceptance before independently reviewed source baseline and separate authorisation.**
