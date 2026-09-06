# Benchmark 023 — NimbusHR Identity Change Packet

## User request

Take this packet through an end-to-end BA delivery package, then prepare it for solution/change-readiness review and assess the evidence against relevant ITIL 4 practice concepts. Keep uncertain things uncertain. Do not invent approval owners, CAB requirements, implementation architecture or missing local policy.

## Source packet

NimbusHR is the SaaS HR platform used by approximately 620 employees.

The business objective is to stop relying on NimbusHR-local passwords for employees and move workforce access to corporate identity. The Head of HR said they would like the change completed **before 30 November** because the annual audit cycle begins in December, but the date has not been committed as a delivery deadline.

The Security Standard states that workforce access to SaaS applications containing employee data **must use corporate identity and the organisation's existing MFA policy**. The standard does not specify a federation protocol or product architecture.

The Identity team said an Entra enterprise application **could probably use SAML** because NimbusHR's public product material says SAML is available on its Enterprise plan. Nobody has yet verified that the organisation's NimbusHR tenant has the feature enabled or that the proposed configuration is compatible. Treat SAML/Entra federation as a proposed mechanism, not a confirmed requirement.

A draft user-mapping spreadsheet contains 603 matched employee accounts and 17 accounts that still need identity resolution.

Contractor access is disputed. HR Operations wants contractors to keep NimbusHR-local accounts because they are concerned about guest-account lifecycle effort. Security wants contractors to use corporate guest identities. No source establishes who has authority to settle this decision.

Automated provisioning/deprovisioning through SCIM was suggested for **Phase 2**. Vendor capability and tenant entitlement have not been verified. Phase 2 is not part of the current cutover scope.

The Release Manager proposed a production cutover for **Saturday at 22:00**, but explicitly said the window is not yet approved.

The Service Desk suggested a **45-minute recovery target** if the authentication change needs to be backed out. No source commits that target, and no backout mechanics have been designed.

Operations said this is **probably a Normal Change unless an existing Standard Change template can be shown to apply**. No evidence of a matching Standard Change template is supplied.

The local Change Policy explicitly requires an **approved change record before production implementation of a customer- or workforce-impacting authentication change**. The packet does not identify the Change Authority or say that CAB approval is universally required.

Current evidence does not include:

- an approved production window;
- an approved backout plan;
- final support/user communications;
- a monitoring/validation method;
- resolution of the 17 unmatched employee accounts;
- resolution of the contractor identity dispute;
- verified NimbusHR federation capability/entitlement;
- a named Change Authority.

## Available Skill catalog

- `analyze-requirements` — analyze messy source into a traceable requirements/evidence/status view.
- `decompose-requirements` — turn sufficiently understood requirements into delivery work without inventing scope.
- `elaborate-acceptance-criteria` — create traceable acceptance criteria for sufficiently ready delivery items.
- `derive-test-cases` — derive behavioural tests/assurance coverage from sufficiently ready criteria.
- `prepare-solution-change-readiness` — prepare mature BA evidence for solution/design and Change Enablement handoff without inventing approvals or architecture.
- `assess-itil-alignment` — assess supplied delivery/change evidence against relevant ITIL 4 practice concepts without inventing local policy or formal compliance claims.
