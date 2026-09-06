# Benchmark 027 Input — FieldOps Portal Identity Provider Change

## Change objective

Replace the FieldOps Portal's legacy LDAP login with the corporate OIDC identity provider. No other functional redesign is approved.

## Evidence packet

- FieldOps Portal currently authenticates approximately 850 field staff directly against legacy LDAP.
- The portal's browser login flow will therefore change directly.
- The service desk currently resets FieldOps Portal passwords in LDAP. After the identity change, portal password-reset requests will follow the existing corporate identity support process instead. This process change is confirmed.
- The portal's audit/export report currently identifies users by LDAP distinguished name (DN). The OIDC provider supplies a different subject identifier. The mapping approach for historical/reporting continuity is **not yet decided**.
- A mobile companion application is believed by one developer to use the same LDAP directory, but the application owner has not confirmed its authentication path. Treat this as unverified.
- The nightly payroll CSV export consumes business data produced by FieldOps Portal. The approved design note says the CSV schema and payroll transfer mechanism are unchanged by the authentication change.
- The asset-management API integration uses a service credential unrelated to end-user LDAP authentication. The integration owner has confirmed it is unchanged.
- Field managers use the same browser portal as other field staff; there is no separate manager application.
- There is no evidence in the packet about firewall rules, DNS, load balancers, databases, endpoint-device configuration, VPN, certificates, network routes, cloud infrastructure, monitoring tools, or SIEM changes.
- There is no approved fallback for a corporate OIDC outage. Operations has asked whether one is needed; the answer is Unknown.
- A Security engineer will review the design, but the packet does not establish that Security owns the change decision or approval authority.
- The project manager has pencilled in a Sunday 22:00-23:00 implementation window, but the window has not been approved. Treat it as a planning Target, not a confirmed impact or constraint.
- A stakeholder said "this probably needs CAB because authentication is changing." No local policy or authority record in the packet establishes that statement.
- Contractor access redesign is Deferred to a later phase.

## Request

Assess the change impact for downstream planning and Change Readiness. Identify confirmed direct/indirect impacts, candidate or unknown impacts, explicit non-impacts/exclusions, and evidence-backed risks without filling the packet with generic technology assumptions.