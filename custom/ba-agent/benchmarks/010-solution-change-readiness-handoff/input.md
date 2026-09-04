# Source packet — Customer Portal Password Reset Change

The delivery team has finished BA analysis for a proposed self-service password-reset change to the Customer Portal.

## Confirmed current scope

- REQ-01 — A signed-in customer can initiate a password-reset request for their own Customer Portal account. Status: Confirmed.
- REQ-02 — Before a password is changed, the customer must complete the organisation's existing identity-verification process. Status: Confirmed.
- REQ-03 — The password-reset outcome and associated date/time must be recorded. Status: Confirmed.
- REQ-04 — The existing Service Desk-assisted reset process must remain available when self-service is unavailable. Status: Confirmed.
- CON-01 — The initiative must not redesign the existing identity-verification policy or Service Desk operating model. Status: Confirmed.
- CON-02 — Any implementation must follow existing security standards and must not introduce a new shared administrator credential. Status: Confirmed.

## Unresolved / non-committed material

- REQ-05 — Product Owner proposes SMS as the first delivery channel for reset verification. Status: Candidate. Security Architecture has not approved a channel or mechanism.
- REQ-06 — Whether password reset should invalidate all active sessions is disputed. Security Operations says yes; Customer Experience says customers should remain signed in on trusted devices. Decision owner: Unknown. Status: Disputed.
- REQ-07 — Product Owner target: complete a successful self-service reset within two minutes where practicable. Status: Target / non-binding.
- REQ-08 — Native mobile-app password reset is Deferred.
- REQ-09 — Retention period for password-reset evidence is Unknown.

## Delivery / acceptance evidence

- US-01 Ready — initiate own-account reset. Traces REQ-01, REQ-02.
- US-02 Ready — record reset outcome/date-time. Traces REQ-03.
- US-03 Ready — retain Service Desk fallback. Traces REQ-04.
- DEC-01 Blocked — session invalidation rule. Traces REQ-06. Decision owner Unknown.
- CAN-01 Candidate — SMS verification mechanism. Traces REQ-05.
- TGT-01 Target — two-minute objective. Traces REQ-07.
- DEF-01 Deferred — mobile-app reset. Traces REQ-08.
- DEC-02 Open — evidence retention period. Traces REQ-09.

Acceptance criteria:

- AC-01 — A signed-in customer may initiate a password-reset request only for their own account. Traces US-01 / REQ-01.
- AC-02 — Password change occurs only after completion of the existing identity-verification process. Traces US-01 / REQ-02.
- AC-03 — Reset outcome and associated date/time are recorded. Traces US-02 / REQ-03.
- AC-04 — Service Desk-assisted reset remains available when self-service is unavailable. Traces US-03 / REQ-04.
- AC-CON-01 — Existing identity-verification policy and Service Desk operating model are not redesigned. Traces CON-01.
- AC-CON-02 — Implementation conforms to existing security standards and introduces no new shared administrator credential. Traces CON-02.

Test/assurance designs exist for AC-01 through AC-04 and both constraints. They have not yet been executed. There is no supplied implementation design, deployment plan, maintenance window, rollback/backout plan, production validation evidence, support transition plan, communications plan, CAB/Change approval, risk rating or release date.

The Technical Lead says: "We can probably use the same reset service as another product, but I haven't checked whether it supports Customer Portal or how identity verification plugs into it."

The Change Coordinator says the team should prepare a Change package once the solution approach and implementation/backout details exist. No Change approver or CAB decision has been supplied.
