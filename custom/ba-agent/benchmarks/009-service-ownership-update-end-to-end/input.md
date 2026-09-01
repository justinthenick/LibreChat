# Benchmark 009 — Service Ownership Update End-to-End BA Delivery

## Source packet

The following material comes from a discovery workshop, a follow-up email, and current-process notes. It has not yet been turned into a formal requirements analysis.

### Business objective

The Service Management team wants to improve the accuracy and traceability of production-application support ownership. Today ownership changes are often coordinated through email and spreadsheets before somebody updates the service register manually. The desired outcome is a clearer request/approval/update process, with automation where proven feasible and a manual update path retained where automation is unavailable.

### Discovery workshop

**Service Portfolio Coordinator**

> For an ownership-change request we need the application or service identifier, current support owner, proposed support-owner team, requested effective date, and the reason for the change.

**Service Governance Lead**

> For a normal ownership change, the current Application Owner needs to approve it before the ownership record is updated.

**Major Incident Manager**

> During a Severity 1 incident, if ownership is obviously wrong, the Major Incident Manager should be able to approve an emergency ownership change so support can be redirected quickly.

**Service Governance Lead**

> I do not agree with that as a standing rule. Even during an incident, ownership authority should remain with the current Application Owner or an explicitly established delegate. We should not build an emergency approval rule until that is settled.

No overall decision owner was identified for this disagreement.

**Service Data Steward**

> We need to keep the manual service-register update option when automation is unavailable. We cannot assume every application or register record will be automatable.

**Platform Architect**

> The existing Service Registry might support automated ownership updates. I have not confirmed its integration capability, authentication approach, supported record types, or whether all required ownership fields can be updated. We should investigate before choosing an interface or design.

**Security Architect**

> If we integrate, use an approved service identity, least privilege, and do not introduce a new shared administrator account.

**Change Enablement Lead**

> This work must not redesign service-ownership governance, the HR organisation model, the application lifecycle process, or existing Change approval authorities. Those boundaries stay as they are.

### Current-process note

For each ownership-change request, the team currently records the request, approval or rejection outcome, ownership-update outcome, and associated date/time information. The business wants that evidence retained in the future process.

The required retention period for that evidence has not been established.

Where an ownership update is imported or performed through another system, the future record should retain the source reference and resulting ownership-update outcome.

### Product Owner follow-up

> I would like approved ownership changes completed within one business day where practicable. Treat that as a target for now, not an SLA.
>
> For a first release, Finance Applications and Network Tools seem like sensible pilot groups, but I have not had that scope approved.
>
> Longer term I would like quarterly ownership recertification to be automated. That is future scope, not part of this release.

### Additional boundaries

- No screen, form, notification channel, validation/error behavior, ownership-team naming rule, effective-date rule, Service Registry protocol, API, payload, storage technology, queue, workflow engine, integration architecture, retry behavior or timeout has been selected.
- No story points, estimates, sprint assignments, delivery dates or test-automation approach have been agreed.
- No decision owner has been established for the emergency-approval dispute.
- The suggested Finance Applications / Network Tools pilot is proposed only and is not approved scope.
- The one-business-day objective is explicitly a Target, not a binding SLA.
