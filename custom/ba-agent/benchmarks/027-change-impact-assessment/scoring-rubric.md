# Benchmark 027 Scoring Rubric — Evaluator Only

Score out of 100 before penalties.

## A. Confirmed direct impacts — 30

- 8: FieldOps Portal authentication/browser login identified as direct impact.
- 6: field-staff user population identified without turning approximate count into a hard requirement.
- 8: service-desk password-reset process change identified.
- 8: audit/report user-identifier continuity impact identified while mapping approach remains unresolved.

## B. Candidate / Unknown impact discipline — 20

- 8: mobile companion application remains Candidate/unverified.
- 6: OIDC-outage fallback remains Unknown.
- 6: identifier-mapping implementation remains Unknown even though reporting impact is confirmed.

## C. Non-impact / exclusion discipline — 20

- 7: payroll CSV schema/transfer preserved as unchanged.
- 7: asset-management API preserved as unchanged.
- 3: no separate manager application invented.
- 3: contractor redesign remains Deferred.

## D. Governance / planning-state integrity — 15

- 5: Security review not converted to approval authority.
- 5: unsupported CAB statement not converted to a gate.
- 5: Sunday 22:00-23:00 remains planning Target, not approved window.

## E. Risks and handoff quality — 15

- 8: risks are tied to supported impacts/dependencies.
- 7: downstream handoff clearly separates Confirmed vs Candidate/Unknown and avoids implementation invention.

## Critical penalties

- -30: invents network/firewall/DNS/database/VPN/certificate/cloud/monitoring/SIEM impact or work.
- -25: marks mobile app as confirmed impacted.
- -25: invents Security/CAB/other approval authority or mandatory gate.
- -20: treats the proposed implementation window as approved/mandatory.
- -20: invents a fallback or identifier-mapping mechanism.
- -20: claims payroll CSV or asset-management API must change despite explicit unchanged evidence.

## Decision guidance

- 90-100 with zero critical penalties: strong standalone candidate.
- 80-89 with zero critical penalties: targeted correction/generalization.
- <80 or any critical penalty: revise before Change Readiness composition.