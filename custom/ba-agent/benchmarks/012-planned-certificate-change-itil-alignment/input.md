# Source packet — Planned Payments Gateway Certificate Rotation

Change record: `CHG-8526` — Payments Gateway certificate rotation and proxy-endpoint update.

Current state: Proposed. Production implementation is not yet authorised.

## Change / risk evidence

- A production change record exists.
- Recorded impact: customer payments may fail if certificate trust or proxy routing is incorrect.
- Recorded implementation risk: Medium.
- Planned window proposed: 2026-09-12 01:00–02:00 AEST.
- A separate network firewall maintenance activity is proposed for 01:30–02:30. The overlap has been noticed but no coordination decision is recorded.

## Internal Change Policy

1. Every production change requires a change record and recorded risk assessment unless an approved pre-authorised Standard Change Model explicitly says otherwise.
2. A change may use a pre-authorised Standard Change Model only when the proposed implementation matches that model's documented scope and conditions.
3. Standard Change Model `SCM-12` covers routine certificate replacement on the existing Payments Gateway endpoints. It does **not** cover adding or changing proxy endpoints.
4. Changes that do not clearly match an approved Standard Change Model require authorisation by the appropriate local Change Authority before implementation.
5. CAB attendance/approval is not universally required; the appropriate Change Authority is determined by local process.
6. Material schedule conflicts must be resolved before the implementation window is finalised.
7. Post-change service/configuration information must be updated where the implemented change alters recorded service/configuration information. The policy does not prescribe a particular CMDB product or update mechanism.

The current local Change Authority holder for this change is **not identified in the packet**.

## Release evidence

Release Manager:

- certificate bundle and proxy configuration package are prepared;
- release notes describe the certificate rotation and proposed proxy-endpoint change;
- staging verification confirms the certificate bundle loads successfully and the proposed proxy configuration can be applied in staging;
- production availability remains subject to the change decision.

## Deployment evidence

Deployment Lead:

- production target is the Payments Gateway production environment;
- an existing approved deployment procedure is referenced for routine certificate replacement;
- the procedure's applicability to the **proxy-endpoint change** has not been confirmed;
- an engineer suggests: `if the proxy update fails, restore the previous proxy config and old certificate bundle`;
- no agreed recovery/backout approach is recorded.

## Service Configuration evidence

Service Configuration Analyst:

- affected service record identifies the Payments Gateway service, certificate entry, and proxy endpoint as affected configuration information;
- no owner/timing is recorded for updating the configuration information after implementation;
- no CMDB product, CI class, discovery tool or update workflow is specified.

## Stakeholder statements

Operations Lead: `Because certificate rotation is a standard change, ITIL says it is automatically approved and CAB is irrelevant.`

Product Owner: `SCM-12 is close enough. We should call the whole thing standard and skip the extra risk/change-authority step.`

Network Lead: `ITIL requires a rollback plan and a CAB meeting for anything touching the proxy.`

Change Manager: `SCM-12 does not cover the proxy change. We need to determine the correct local authorisation path, resolve the overlap with firewall maintenance, and keep the existing risk evidence. I do not know the current Change Authority holder from this packet.`

## Task context

Assess ITIL 4 alignment/readiness using only the supplied evidence. Distinguish ITIL guidance from explicit local policy and stakeholder opinion. Do not invent Change Authority, CAB requirements, Standard Change classification, rollback mandates, CMDB tooling, security approvals, maturity scores or execution evidence.