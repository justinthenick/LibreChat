# Supervisor v3 — source provenance gate (2026-10-18)

**Decision: BLOCKED / UNAUTHENTICATED SOURCE.** This is a documentation-only checkpoint. It authorises no code execution, credential release, privileged launch, production integration, or quarantine modification.

## Scope and observed evidence

| Evidence | Observed value | Trust conclusion |
|---|---|---|
| Original `LibreChat-Pilot-Kernel-Supervisor-Review-v2.zip` | SHA-256 `ab4e6cee4ea5136ddc3aef1dde2a37fbf59b2e67b61a6f83c401cce91a7034a7`; 84,516 bytes | Operator download and later upload matched this previously observed digest; continuity only |
| Original `MANIFEST.json` | SHA-256 `385d310d310e438ea4b782a64854c7787a27ac1e92844bc386f7af39449b06cd`; 2,928 bytes; 27 declared files | Internal hash self-consistency, not external authenticity |
| Latest v3 rootless-feasibility candidate | SHA-256 `2e9000921bf5194ac3be93e1f8feb6dadb0c7d5af10a8df16fb199554000ad15` | Derived in conversation from the prior local review candidates; continuity only |
| Latest v3 candidate manifest | SHA-256 `6bd254430df02b179aebcc44a898b9d46ff4ed1c1ca40796ce0de07bf6ea5cd1` | Self-describing; not independent trust |
| Latest v3 incremental patch | SHA-256 `cadbfdc9ce216ec565e7ebc9f47a87adafbf611c6d75cdc7324208c6b5e01a26` | Derived artifact, not a separately attested source |
| Offline tests | 146 supervisor + 51 adapter (197 total), reported PASS | Functional regression evidence **only** |

These values are observations from the operator's console and previous review checkpoints. Do not label them independently verified publishing provenance.

## Repository/history check performed

Repository: `justinthenick/LibreChat`; operational development baseline `server/synology`. Current dedicated branch `review/supervisor-v3-corrections-20261017` contains **documentation**, not Supervisor Python source.

GitHub searches for supervisor, pilot kernel, quarantine, and rootless source commits/branches found no separately attributable original v2 package source commit. This is a scoped search, **not** proof that no unindexed/private history exists.

Related development work is not a substitute for this provenance:
- PR #236 is a separate **draft review-stack integration candidate**, not a source attestation for the supervisor ZIP: https://github.com/justinthenick/LibreChat/pull/236
- PR #233 concerns private review-service identity and durable quarantine; it does not authenticate this ZIP: https://github.com/justinthenick/LibreChat/pull/233
- PR #210 defines a dormant executor containment protocol; it does not prove Supervisor v3 kernel integration: https://github.com/justinthenick/LibreChat/pull/210

The original ZIP manifest exposes no externally verifiable authoring Git commit, signed release, builder identity or cryptographic build attestation.

## Two permitted routes to a verifiable baseline

**Route A — recover original provenance (preferred if possible):**
1. Obtain the original authoring repository and **immutable commit/tree SHA**, from a party or system independent of the ZIP contents.
2. Obtain trusted publisher/CI build records binding that exact tree, toolchain, input manifest and output SHA-256. Verify signature/issuer, immutable CI run and artifact storage independently.
3. Rebuild in a clean isolated environment, compare source tree and archive reproducibly or explicitly explain nondeterministic archive metadata. Perform a separate security review before acceptance.
4. Preserve the original package and journal immutably; record every comparison and reviewer/sign-off identity.

**Route B — establish a newly reviewed source baseline if A is unavailable:**
1. Treat the v2/v3 archives as **untrusted proposed code**, not a signed release. Never relabel its origin as independently authenticated.
2. Independently inspect full source for secrets, unsafe imports, privileged actions, dependencies, malicious behaviour, licenses, symlink/archive hazards, test fixtures and side effects. Require review by someone or a controlled process that did not create the artifact.
3. Create a new isolated **private or explicitly approved** repository/branch with the exact reviewed source, separated from deployment, and record immutable commit and tree IDs. Do not automatically push the raw ZIP to this public repository.
4. Add reproducible build instructions, test inventory, machine-readable results and signed or independently witnessed source/artifact digests. Independent trusted evidence for **the newly reviewed baseline** begins at this point; it does not retro-authenticate v2.
5. Require an independent negative/security review on the exact tree before allowing any discretionary root/kernel acceptance.

**Never use:** ZIP-embedded checksum as external trust pin; local hash copied into an "expected" field; successful unit tests; a ChatGPT-generated artifact; or the documentation branch itself as proof of original authorship.

## Gate checklist

- [ ] Authoring source tree/commit independently authenticated **or** new exact reviewed source baseline independently approved.
- [ ] Controlled builder and dependencies pinned (versions and digests).
- [ ] Build/attestation bound to exact commit, manifest, artifact hash and reviewer.
- [ ] No credentials, tokens, private journal/quarantine records, personal information or live endpoints in the source/workspace.
- [ ] Independent code/security review includes all executable files and changed patches.
- [ ] All 197 known offline regressions repeated against the exact new tree, plus provenance tampering negatives.
- [ ] Gate approval in a signed, immutable record with named scope and expiration. No approval inferred from silence.

**Status: G0 SOURCE PROVENANCE = BLOCKED.** Until G0 is satisfied, any host inspection must remain unprivileged and read-only. Real kernel/credential acceptance must not begin.
