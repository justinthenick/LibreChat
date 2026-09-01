# Benchmark 008 — Contractor Site Access End-to-End BA Delivery

## Source packet

The following material was collected from a short discovery session, follow-up email, and existing-process notes. It has not yet been turned into a formal requirements analysis.

### Discovery notes

**Business objective**

Field Operations wants to reduce delays when external contractors need temporary access to network sites for planned work. Today most requests are handled through email, spreadsheets and phone calls. The desired outcome is a clearer, traceable request/approval/access process with automation where it is proven feasible, while keeping a manual path available.

**Field Operations Coordinator**

> For a normal request we need the site code, contractor company, visiting engineer name, planned arrival and departure, and the work or Change reference. The Site Access Team should approve normal-hours access before anything gets issued.

**Site Access Lead**

> For after-hours work our on-call Site Access person can approve it. That is how we should build it.

**Security Manager**

> I disagree. Any after-hours access should require Security approval. I do not want the system assuming the Site Access on-call person is sufficient.

No overall decision owner was identified for this disagreement during discovery.

**Operations Support**

> We cannot depend on automation being available for every site. Manual temporary-access issuance has to remain possible when automation is unavailable.

**Technical Architect**

> We might be able to use the existing Building Access Platform to issue temporary access automatically. I have not verified which sites support it, what integration capability exists, or what authentication approach would be required. We should not pick a protocol or design yet.

**Security Manager**

> If we do integrate, use an approved service identity, least privilege, and do not create a new shared administrator account.

**Change Manager**

> This initiative is not a redesign of contractor onboarding, security vetting, building-owner approval, or the existing Change approval process. Those processes stay as they are.

### Existing-process note

For every temporary-access request, the current team records the request submission, approval or rejection outcome, temporary-access issuance outcome, and associated date/time information. The business wants that evidence retained in the new flow.

The required retention period for that evidence has not been established.

### Product Owner follow-up email

> For the first release I would probably start with Sydney Metro and Newcastle because the team knows those sites best, but I have not had that scope approved yet.
>
> I would also like a complete request to receive an approval/rejection response within two business hours where practicable. Treat that as a target for now, not a contractual SLA.
>
> Longer term it would be useful if temporary access could be revoked automatically when the planned access window ends. That is not for the current release.

### Additional boundaries

- Manual temporary-access issuance is currently possible for all sites.
- No specific screen, form, notification channel, error-message behavior, validation format, Building Access Platform protocol, API, storage technology, queue, workflow engine or integration architecture has been selected.
- No story points, estimates, sprint assignments or delivery dates have been agreed.
- No decision owner has been established for the after-hours approval dispute.
- The suggested Sydney Metro / Newcastle pilot is a proposal only and is not approved scope.
- The two-business-hour objective is explicitly a Target, not a binding SLA.
