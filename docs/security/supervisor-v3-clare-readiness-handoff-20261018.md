# Supervisor v3 Clare host-readiness handoff — 2026-10-18

**REVIEW-ONLY. No kernel acceptance or privileged launch has taken place on Clare.**

## Verified input
- Most recent v3 review ZIP: `d7bc174b301e0e335e280b627651c5c025927d8579e409a8670223b27b3a5791` SHA-256.
- `MANIFEST.json`: `3c47dd12bcf49d615eedbac16cf3d37f4505edeb79ce69b12140c697ba8eec46` SHA-256.
- All 41 manifest-declared entries match, no additional or duplicate ZIP entries.
- `supervisor/trusted_plan.py` still has `PRIVILEGED_LAUNCH_ENABLED = False`.
- The entire source candidate remains outside this public repository.

## Next required evidence from the actual WSL host, Clare

A separate user-facing diagnostic script, `Clare-Supervisor-v3-readonly-preflight.sh`, was prepared with SHA-256:

`b8eca0d9588de577514369aaf7dd4e8666976f9c787601ba0f1953b512e82b6a`

This script was locally tested under an unprivileged account in a *separate sandbox*; it reported that Bubblewrap was absent **in that sandbox**. No corresponding conclusions about Clare can be drawn until the user runs it there.

The script:
- Reads only fixed system paths and the current process's `/proc` status/namespaces.
- Prints Linux/WSL detection, current UID, fixed binary existence and local SHA-256, installed package metadata, user-namespace settings and PIDFD self-check.
- Does **not** run Bubblewrap, load supervisor modules, use sudo, enumerate unrelated processes, open quarantines, access credentials, alter firewall/network policies, or create files in WSL.
- Always reports `KERNEL_ACCEPTANCE=NOT_RUN`, `SOURCE_AUTHENTICITY=NOT_VERIFIED`.

On Windows PowerShell 5.1 after downloading that separately provided script into Downloads with its exact filename:

```powershell
$probe = Join-Path $HOME 'Downloads\Clare-Supervisor-v3-readonly-preflight.sh'
$expected = 'B8ECA0D9588DE577514369AAF7DD4E8666976F9C787601BA0F1953B512E82B6A'
if ((Get-FileHash -LiteralPath $probe -Algorithm SHA256).Hash -ne $expected) { throw 'STOP: probe differs from reviewed copy' }
Get-Content -LiteralPath $probe -Raw | wsl.exe -d Ubuntu-24.04 -- bash -s
```

An observed on-host binary SHA-256 is **not** an independent trusted reference pin. Do not feed it back as one.

## Pending gates
1. Capture and review host prerequisites **on Clare**; verify WSL target and that the non-root user is intended.
2. Establish trusted independent provenance for source/binaries.
3. Review the exact target Linux mount, procfs, process ancestry, pipe provisioning, host observer authority and cleanup.
4. Only then propose a disposable, separately authorised kernel acceptance exercise. Do not enable privileged launch or use real credentials.

No production changes were made for this checkpoint.
