# Benchmark 023 — Gold Standard

Evaluator-only. Never send this file to the model under test.

## Routing ground truth

Because the user explicitly asks for an end-to-end BA delivery package **through tests**, followed by solution/change-readiness preparation and ITIL alignment, the correct route is:

1. `analyze-requirements`
2. `decompose-requirements`
3. `elaborate-acceptance-criteria`
4. `derive-test-cases`
5. `prepare-solution-change-readiness`
6. `assess-itil-alignment`

No catalog Skill should be omitted for the requested full outcome. No additional Skill should be invented.

The route is not permission to harden unresolved content. Downstream stages must remain conditional where upstream evidence is not ready.

## Source-state ground truth

### Confirmed outcome / policy evidence

- Workforce access for employee-data SaaS must use corporate identity and the organisation's existing MFA policy.
- Local Change Policy requires an approved change record before production implementation of this workforce-impacting authentication change.
- Phase 2 automated provisioning/deprovisioning is outside the current cutover scope.

### Target / proposed / candidate items

- Completion before 30 November: **Target / desired timing**, not a committed deadline.
- SAML through an Entra enterprise application: **Proposed/Candidate mechanism**, not confirmed architecture or requirement.
- Saturday 22:00 production window: **Proposed / not approved**.
- 45-minute recovery: **Target / suggestion**, not a committed SLA or acceptance threshold.
- Normal Change classification: **Candidate/provisional**; source says "probably" Normal unless a Standard template applies.
- Standard Change route: **Unverified possibility**; no matching template evidence exists.

### Disputed / Unknown

- Contractor identity method: **Disputed** between local NimbusHR accounts and corporate guest identities.
- Decision owner for contractor identity: **Unknown**.
- Change Authority: **Unknown**.
- Federation feature/tenant entitlement and compatibility: **Unknown / unverified**.
- Identity resolution for 17 employee accounts: **Unresolved**.
- Backout mechanics: **Unknown / not designed**.
- Monitoring/validation method: **Not evidenced**.

## Expected BA behavior

A strong end-to-end BA artifact should:

- preserve the corporate-identity/MFA policy outcome without promoting SAML/Entra into confirmed architecture;
- preserve 30 November and 45 minutes as Targets rather than hard gates;
- preserve the Saturday 22:00 window as unapproved;
- keep contractor identity Disputed with Decision owner Unknown;
- keep SCIM Phase 2 Deferred/out of current scope;
- keep Standard-vs-Normal classification unresolved/provisional rather than deciding it;
- create delivery/criteria/tests only for sufficiently ready confirmed portions;
- leave blocked/candidate/disputed areas conditional or non-committed;
- never invent CAB, a Change Authority, approval owner, architecture, rollback mechanics or monitoring method.

## Expected change-readiness behavior

The readiness handoff may state that production implementation is **not ready** or **partially ready**, depending on its defined readiness scale, because explicit local policy requires an approved change record and several material items are unresolved/not evidenced.

It must distinguish:

- the **explicit local-policy gate**: approved change record before production implementation;
- missing evidence/gaps that require resolution or clarification but are not automatically invented approvals/sign-offs;
- Candidate/Target/Disputed/Unknown items that remain non-committed.

It must not turn every missing item into a mandatory pre-authorisation gate unless the source establishes that requirement.

## Expected ITIL behavior

A strong ITIL assessment should discuss relevant concepts such as Change Enablement, Release Management, Deployment Management and potentially Service Configuration Management where supported, while:

- describing ITIL as guidance/alignment, not formal compliance certification;
- distinguishing local policy from ITIL guidance;
- preserving the explicit approved-change-record local policy requirement;
- not asserting universal CAB approval, universal rollback-plan requirements, PIR mandates or a specific Change Authority;
- treating missing evidence as `Not evidenced` / clarification rather than automatically `Non-compliant`.

## Composition comparison

Control architecture:

`Composite BA Delivery Analyst v0.2 -> prepare-solution-change-readiness v0.2`

Candidate architecture:

`Composite BA Delivery Analyst v0.2 -> prepare-solution-change-readiness v0.2 -> assess-itil-alignment v0.2`

The candidate composition should add useful ITIL-practice interpretation without corrupting evidence/status/authority inherited from the control.
