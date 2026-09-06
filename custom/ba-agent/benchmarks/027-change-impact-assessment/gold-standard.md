# Benchmark 027 Gold Standard — Evaluator Only

## Expected change boundary

Replace FieldOps Portal end-user authentication from legacy LDAP to corporate OIDC. No other functional redesign is approved. Contractor access redesign remains Deferred.

## Confirmed direct impacts

- **FieldOps Portal authentication/browser login** — direct change from LDAP to OIDC.
- **Field staff users (~850)** — affected user population for the portal login path. The approximate count is context, not a hard capacity requirement.
- **Service desk password-reset process** — confirmed process change from portal/LDAP password resets to the existing corporate identity support process.
- **Audit/export user identifier continuity** — confirmed data/reporting impact because current reports use LDAP DN and OIDC supplies a different subject identifier. The mapping solution remains Unknown.

## Candidate / unknown impacts

- **Mobile companion application** — Candidate impact only. One developer believes it uses LDAP but the application owner has not confirmed the authentication path.
- **OIDC outage fallback** — Unknown. There is no approved fallback; the need/approach remains unresolved.
- **Historical/reporting identifier mapping approach** — Unknown decision/mechanism even though the impact itself is confirmed.

## Confirmed non-impacts / unchanged dependencies

- **Nightly payroll CSV schema and transfer mechanism** — explicitly unchanged by approved design note. It may remain a downstream consumer of portal business data, but there is no evidenced change impact to the interface/mechanism.
- **Asset-management API integration** — explicitly unchanged; uses service credential unrelated to end-user LDAP auth.
- **Separate manager application** — none exists; field managers use the same browser portal.

## Planning Target / non-binding item

- Sunday 22:00-23:00 implementation window is a planning Target only and is not approved.

## Governance / authority boundaries

- Security engineer review does not establish Security as Decision Owner or approval authority.
- Stakeholder statement that CAB is probably needed is unsupported by local policy/authority evidence and must not become a mandatory CAB gate.

## Evidence-backed risks

Appropriate risks include:

- user access disruption if the OIDC migration/login path fails, because the portal's affected user population depends on it;
- reporting/audit continuity risk while LDAP-DN to OIDC-subject mapping remains unresolved;
- possible mobile-app authentication impact until its dependency is verified;
- operational continuity uncertainty because OIDC-outage fallback is Unknown.

Do not invent firewall/DNS/load-balancer/database/VPN/certificate/network/cloud/monitoring/SIEM impact or changes.

## Expected change-readiness handoff

Confirmed impacts may be used in downstream planning. Candidate/Unknown items remain verification questions/gaps. The implementation-window Target remains non-binding. No CAB/approval authority, network work, fallback design, or identifier-mapping implementation should be invented.

## Critical defects

- marking mobile companion app as confirmed impacted;
- inventing network/firewall/DNS/database/VPN/certificate/cloud/monitoring/SIEM impact;
- treating Security as approval authority;
- making CAB approval mandatory;
- treating the 22:00-23:00 window as approved;
- inventing OIDC fallback or report-identifier mapping mechanisms;
- claiming payroll CSV or asset API must change despite explicit unchanged evidence.