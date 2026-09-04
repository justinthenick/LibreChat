# Benchmark 024 Gold Standard — Evaluator Only

The correct audit verdict is at least **Needs correction**. The chain contains multiple material semantic and lineage defects.

## Expected findings

### F-01 — REQ-02 Candidate promoted to Confirmed / mandatory

- Severity: Critical.
- Upstream: REQ-02 is Proposed / Candidate and conditional on IdP compatibility.
- Downstream drift:
  - WI-02 is `Ready / Confirmed`;
  - AC-02 says authentication `must use` corporate SSO;
  - T-02 tests SSO as committed behavior;
  - Change-readiness says SSO is approved and should be implemented.
- Correct conclusion: this is unsupported status and scope hardening. Compatibility remains unverified.

### F-02 — REQ-03 Target promoted to mandatory SLA / release threshold

- Severity: Critical.
- Upstream: REQ-03 is explicitly a Target: `should aim to complete within 5 minutes`.
- Downstream drift:
  - WI-03 is Ready without preserving Target status;
  - AC-03 makes <=5 minutes mandatory;
  - T-03 tests it as a pass/fail condition;
  - Change-readiness calls it a `five-minute provisioning SLA` and release threshold.
- Correct conclusion: Target-to-gate promotion.

### F-03 — Phantom AC reference

- Severity: Critical or Major, but must be treated as materially invalid assurance lineage.
- T-03 references AC-99, which does not exist.
- Its stated behavior corresponds to AC-03, but the auditor must not silently repair the reference.

### F-04 — DEC-01 authority invented / dispute mishandled

- Severity: Critical.
- Upstream: DEC-01 is Disputed and `Decision owner: Unknown`.
- Maya is a Security engineer who prefers one option; she is not established as decision authority.
- Downstream drift:
  - WI-05 says `Blocked pending Security decision`;
  - AC-04 says `Security must select` the approach;
  - Change-readiness makes Maya the Decision Owner.
- Correct conclusion: proposer/participant has been converted into authority without evidence.

### F-05 — CAB gate invented

- Severity: Critical.
- No source establishes CAB approval as a mandatory gate.
- Change-readiness invents CAB approval solely because authentication is changing.

### F-06 — CON-01 confirmed fallback constraint disappears

- Severity: Major.
- CON-01 is Confirmed and should survive decomposition/criteria/assurance/change-readiness where applicable.
- It disappears entirely after Artifact A.
- Correct conclusion: lost confirmed constraint / coverage failure.

### F-07 — REQ-04 Deferred scope disappears without explicit preservation

- Severity: Major or Minor depending evaluator judgment, but it must be noticed.
- Deferred work does not require current delivery criteria/tests, but it should remain visibly Deferred/out of current scope so its disappearance is not mistaken for cancellation.

### F-08 — T-04 invents immutable audit logging

- Severity: Major.
- REQ-01 only establishes MFA before console access.
- No upstream artifact establishes audit logging, immutability, or per-attempt logging.
- T-04 therefore creates new product/assurance behavior rather than verifying sourced behavior.

## Expected healthy lineage

- REQ-01 -> WI-01 -> AC-01 -> T-01 is materially sound.
- MFA can be described as ready for implementation based on the supplied chain, subject to the audit not inventing unrelated gates.

## Expected state-integrity summary

Must explicitly call out:

- Candidate -> Confirmed: REQ-02;
- Target -> mandatory/SLA: REQ-03;
- Disputed/Unknown authority -> Security/Maya authority: DEC-01;
- Deferred REQ-04 lost from downstream visibility.

## Expected authority-integrity summary

Must explicitly state:

- Maya is not evidenced as Decision Owner;
- `Security` is not established as the decision authority for DEC-01;
- CAB approval is invented.

## Important evaluator boundaries

Do not reward an answer that repairs AC-99 to AC-03 without first identifying the phantom reference.
Do not reward generic claims that every requirement must have an AC/test; Deferred and blocked items may legitimately not have committed downstream work.
Do not reward invented remediation owners, governance bodies, architecture, implementation steps, or validation methods.