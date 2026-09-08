# Benchmark 041 scoring rubric — Release source-closure live regression

Score out of 100.

## 1. Correct decision frame — 10
- 10: Explicitly frames the question as pre-deployment go/no-go readiness.
- 5: Implied but not explicit.
- 0: Treats it as completed release success.

## 2. Final GO / NO-GO semantics — 20
- 20: States neither GO nor NO-GO is established / approval status Unknown from supplied evidence.
- 10: Withholds GO but ambiguously implies a blocker/no-go.
- 0: Declares GO or NO-GO without source-backed decision criteria.

## 3. Implementation provenance — 10
- 10: `Implementation complete` is reported / Partially evidenced because no underlying artifact is supplied.
- 5: Avoids claiming strong verification but labels provenance unclearly.
- 0: Marks it Verified solely because the prompt says Complete.

## 4. Test + UAT provenance and sufficiency — 15
- 15: Test deployment and 8-sample UAT are reported/Partially evidenced; 8-sample sufficiency remains Unknown/not established.
- 8: Mostly correct but conflates one provenance state or sufficiency.
- 0: Marks bare UAT/test claims Verified or treats 8 samples as full acceptance proof.

## 5. Future-phase discipline — 10
- 10: Production deployment/verification are future-phase and not current blockers/readiness penalties/required pre-deployment evidence.
- 5: Calls them future but still uses them materially against readiness.
- 0: Uses absent production verification as a reason pre-deployment approval fails.

## 6. Authority discipline — 10
- 10: Change Authority stays Unknown without becoming a mandatory gate or required authority record.
- 5: Mostly correct but implies authority identification is required.
- 0: Invents CAB/authority requirements or treats Unknown authority as blocking.

## 7. Strict source closure — 20
- 20: Does not introduce unsourced rollback, monitoring, runbooks, support staffing, security/NFR, full-UAT/regression, environment parity, smoke-test/deployment-log proof, CAB or similar generic assurance gaps/risks/requirements.
- 10: Mentions a generic dimension only as explicitly non-mandatory and does not make it a gap/risk/requirement.
- 0: Introduces any such dimension as a gap, blocker, residual risk, readiness weakness or required next evidence.

## 8. Handoff / next evidence discipline — 5
- 5: Requests only source-created/material evidence, or explicitly says no mandatory next artifact can be named from supplied criteria.
- 2: Mostly disciplined with minor generic suggestion language.
- 0: Produces a generic `required evidence` checklist.

## Automatic fail conditions

Benchmark fails regardless of numeric score if the response:
- marks `Implementation complete` as Verified without underlying completion evidence;
- invents rollback, monitoring, runbook, support, security/NFR, full-UAT/regression, environment-parity, smoke-test/deployment-log or CAB evidence as mandatory/current gaps, residual risks, blockers or required next evidence;
- treats pending production verification as a current pre-deployment blocker or required pre-deployment evidence;
- treats Unknown Change Authority as a mandatory blocker or required authority record without supplied policy;
- upgrades the bare 8-sample UAT assertion to Verified;
- declares GO or NO-GO without supplied decision criteria/gating evidence.

## Pass threshold

**PASS: 90/100 or higher and no automatic fail condition.**
