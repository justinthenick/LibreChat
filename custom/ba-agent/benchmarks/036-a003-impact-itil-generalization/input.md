# Benchmark 036 Input — EdgeAuth Certificate Rotation Assurance

The user needs a focused assurance review for a production certificate rotation. Use the supplied maturity statements; do not rerun work that is explicitly current and complete.

## Current supplied artifacts

### Traceability audit TA-88 — 5 September

Status: Complete and current for this decision point.

- Change CR-221 is linked to requirements AUTH-04 and SEC-11.
- Test evidence expected: staging handshake verification, rollback certificate re-import, production post-change handshake verification.
- No unresolved traceability gaps are recorded.

The user explicitly says: **do not redo traceability.**

### Change scope

- Rotate the public TLS certificate used by EdgeAuth API endpoint `auth.example.net`.
- Private key remains in the existing managed key store.
- DNS, API path, authentication protocol and client credentials are unchanged.
- Two downstream consumers are known: MobileApp and PartnerGateway.
- The packet does not contain a current impact assessment of certificate pinning, trust-store behavior, or maintenance-window sensitivity for either consumer.

### Release / test evidence

- Staging certificate rotation completed successfully on 5 September; TLS handshake and authentication smoke tests PASS.
- Rollback certificate re-import was executed in staging and PASS.
- Production certificate rotation has **not yet occurred**.
- Production post-change handshake verification is therefore **NOT RUN**.
- Change record CHG-2217 exists but status is **Draft**.
- Proposed production window: Sunday 23:00–23:30. Status: **Candidate**.
- No explicit Change Authority is identified in the packet.

### Operational baseline

Operations provides current evidence that the existing certificate-rotation runbook, on-call coverage, monitoring dashboard and escalation path are unchanged and already assessed as operationally ready for this release class. The user says **do not rerun operational-readiness assessment unless the supplied evidence materially contradicts that baseline**. No contradiction is supplied.

### Governance request

The user explicitly asks for an **ITIL 4 practice-alignment assessment** after the evidence review. The packet contains no local policy requiring a CAB, no named Change Authority, and no evidence that the Draft change record is approved.

## Request

Select and execute the minimum validated assurance route needed to:

1. identify material change impacts still needing assessment;
2. validate what the supplied release evidence actually proves; and
3. assess ITIL 4 alignment.

Do not redo the current traceability audit. Do not rerun operational readiness. Do not produce a consolidated go/no-go/change-readiness handoff unless it is actually required by the request.
