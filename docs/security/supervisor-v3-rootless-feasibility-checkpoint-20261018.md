# Supervisor v3 rootless feasibility — review-only checkpoint (2026-10-18)

**Decision: NO-GO** for the currently observed rootless Bubblewrap configuration on Clare if the worker must have zero supplementary groups. No production, quarantine, credentials or host settings were changed.

## Clare operator observations (not a supervisor launch)

- `uid_map = 1000 0 1`
- `gid_map = 1000 0 1`
- `setgroups = deny`
- `Groups = 65534 65534 65534 65534 65534 65534 1000 65534`
- Rootless smoke test: five capability sets zero and `NoNewPrivs=1`, **but** `Seccomp=0` and `Seccomp_filters=0` (no Supervisor filter was installed).
- These maps are relative to the observing namespace; the second column is **not** evidence of unrestricted host root identity.

With `setgroups=deny`, the rootless process cannot call `setgroups([])` inside that namespace. Its nonempty groups must not be ignored or remapped away for acceptance. Existing privileged-bootstrap target UID/GID 60000–64999 are outside this mapping.

## Review-only changes from prior identity-mode candidate

- Added `supervisor/rootless_feasibility.py`: bounded read-only `/proc/self` snapshot inspection; pure mapping, identity, supplementary group, zero-capability, `NoNewPrivs` and seccomp-evidence checks. It compares repeated, security-relevant status fields while excluding volatile memory counters.
- The CLI does not launch Bubblewrap, create namespaces, call `setgroups`, access credentials, use sudo, or approve any execution. Even fully-green synthetic snapshots remain `BLOCKED`: `launch_authorized=false`, `credential_release_authorized=false`, `kernel_acceptance=NOT_RUN`.
- Added 18 synthetic regressions covering the observed Clare denial, unexpected groups including overflow 65534, changing proc evidence, forged/unstable identity, bad maps/status, missing NNP or seccomp filters, and any attempted acceptance on favorable evidence.
- Added `supervisor/ROOTLESS_FEASIBILITY_REVIEW.md`. The rootless launcher remains **NOT IMPLEMENTED** and privileged launch remains **SEALED**.

## Local validation only — NOT Clare

Executed under the unprivileged Linux account `nobody` with Python bytecode disabled:
- Supervisor **146/146 PASS**
- Adapter **51/51 PASS**
- Total **197/197 offline tests PASS**
- Manifest consistency **47/47 source/docs files PASS**
- Read-only preflight **PASS** (reported `privileged_launch=SEALED`, `rootless_launch=NOT_IMPLEMENTED`).
- Incremental patch applied to untouched prior candidate and reproduced all **48** archive entries/file bytes (**PASS**).
- Local read-only self-diagnostic returned `BLOCKED`; does not constitute Clare or kernel acceptance.

## Artifact fingerprints (local continuity only, NOT independent authenticity)

- Previous candidate ZIP: `8297af57c68b8de91b88caafebb809b60e6e51cbb80f974c0db2f2aca506d464`
- Updated review candidate ZIP: `2e9000921bf5194ac3be93e1f8feb6dadb0c7d5af10a8df16fb199554000ad15`
- Updated manifest: `6bd254430df02b179aebcc44a898b9d46ff4ed1c1ca40796ce0de07bf6ea5cd1`
- Incremental patch: `cadbfdc9ce216ec565e7ebc9f47a87adafbf611c6d75cdc7324208c6b5e01a26`

The code artifacts remain external to the public GitHub repository pending independent provenance and review; this is a documentation-only checkpoint.

## Engineering decision

**Stop pursuing execution from Clare's current rootless login context.** A new, independently provisioned group-free parent process is only a *possible* alternative, not implemented or accepted. Preserve the sealed privileged-bootstrap reference and make the next investment in source provenance and a separately authorised disposable acceptance design, not weakening zero-group identity checks.

Never unseal `privileged_launch()`, release dummy/live credentials, run a real provider or modify protected quarantine, production or host policy to force these tests to pass.

Kernel reference: https://man7.org/linux/man-pages/man7/user_namespaces.7.html
