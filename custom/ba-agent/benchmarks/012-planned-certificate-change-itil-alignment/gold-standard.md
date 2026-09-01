# Benchmark 012 — Gold Standard

**Evaluator-only. Do not expose to the model under test.**

Expected overall conclusion: **Partially evidenced / not yet ready for implementation authorisation.**

## Change Enablement

- Positive evidence: `CHG-8526` exists; risk assessment exists; impact/risk are recorded.
- Do **not** classify the whole change as an approved/pre-authorised Standard Change. `SCM-12` explicitly excludes proxy-endpoint changes.
- The correct local authorisation path therefore remains to be established under policy; current Change Authority holder is **Unknown from the packet**.
- Proposed window overlaps firewall maintenance; policy requires material schedule conflicts resolved before window finalisation.
- Stakeholder claim that ITIL makes the change automatically approved is unsupported.
- Stakeholder claim that CAB is universally required is unsupported; local policy explicitly says CAB is not universally required.
- Product Owner proposal to skip the risk/change-authority step conflicts with explicit local policy.

## Release Management

- Certificate bundle + proxy configuration package and release notes are prepared.
- Staging verification passed for loading/applying the package in staging.
- Production availability remains conditional on the change decision.
- Do not infer implementation authorisation from release-package readiness.

## Deployment Management

- Target production environment is known.
- Existing approved deployment procedure is evidenced for routine certificate replacement.
- Its applicability to the proxy-endpoint change is **not evidenced** and needs clarification.
- Engineer's restore-old-config/certificate suggestion is a proposal only, not an agreed recovery approach.
- Do not claim ITIL universally mandates rollback/backout.

## Service Configuration Management

- Affected service/configuration information is identified: Payments Gateway, certificate entry, proxy endpoint.
- Post-change update responsibility/timing are not evidenced.
- Local policy requires information to be updated if implementation alters recorded information, but does not prescribe tooling/mechanism.
- Do not invent CMDB product, CI class, discovery tool, API or workflow.

## Policy vs guidance

Strong answers clearly distinguish explicit local policy from ITIL practice guidance and stakeholder opinions. Missing evidence is not formal ITIL non-compliance.

## Required readiness dependencies

1. determine the appropriate local authorisation path / authority holder (currently Unknown);
2. resolve the schedule overlap before finalising the window;
3. preserve the recorded risk assessment;
4. clarify whether the routine deployment procedure applies to the proxy-endpoint change;
5. clarify configuration-information update responsibility/timing;
6. keep production availability conditional on authorisation.

A recovery/backout approach may be raised as a focused readiness question, but the engineer's proposal must not be promoted into an agreed plan and ITIL must not be cited as universally mandating one.
