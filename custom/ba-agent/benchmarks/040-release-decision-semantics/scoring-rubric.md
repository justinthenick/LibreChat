# Benchmark 040 scoring rubric — Release decision semantics

Score out of 100.

## 1. Correct decision frame — 15
- 15: Explicitly frames the task as **pre-deployment go/no-go readiness**.
- 8: Implied but not explicit.
- 0: Treats the task primarily as completed release success/post-deployment verification.

## 2. GO / NO-GO semantics — 20
- 20: Concludes that **neither GO nor NO-GO is established** from the supplied evidence.
- 10: Correctly withholds GO but ambiguously suggests a blocker/no-go.
- 0: Declares GO or NO-GO without source-backed decision evidence.

## 3. UAT provenance and sufficiency — 15
- 15: Treats the bare “8 sample inspections passed” status assertion as **reported / Partially evidenced**, and separately keeps acceptance sufficiency Unknown/not established.
- 8: Avoids overgeneralization but does not clearly distinguish reported assertion from demonstrated result.
- 0: Upgrades the bare assertion to Verified or treats the 8 samples as proof of full UAT/production readiness.

## 4. Failed evidence vs gate applicability — 15
- 15: Preserves the optional-browser diagnostic as **Failed**, explicitly states release-gate applicability is not established, and does not infer NO-GO from the failure alone.
- 8: Preserves the failure but is ambiguous about whether it blocks release.
- 0: Treats any failed diagnostic/check as sufficient for NO-GO without source-backed applicability as a release-blocking gate.

## 5. Future-phase discipline — 10
- 10: Treats production deployment/verification as future-phase evidence and not automatic present blockers.
- 5: Notes they are future but still uses them to weaken pre-deployment readiness materially.
- 0: Uses absent production verification as a reason the pre-deployment decision fails.

## 6. Authority discipline — 10
- 10: Reports Change Authority as Unknown without inventing a mandatory approval gate.
- 5: Mostly correct but implies approval cannot proceed without identifying authority.
- 0: Invents CAB/authority requirements or treats Unknown authority as a mandatory blocker.

## 7. Generic-gap discipline — 10
- 10: Does not call rollback, monitoring, support, security or non-functional evidence mandatory without supplied policy; may list them only as unevidenced/applicability-to-confirm dimensions.
- 5: Includes them but with mixed “required” language.
- 0: Converts generic best-practice categories into mandatory blockers.

## 8. Evidence-state clarity — 5
- 5: Clearly distinguishes reported/partial, Failed, Unknown/not established and future-phase states and ties them to supplied facts.
- 2: Mostly clear with minor state conflation.
- 0: Materially upgrades/downgrades evidence or invents facts.

## Automatic fail conditions

Benchmark fails regardless of numeric score if the response:
- declares NO-GO solely because production verification has not yet occurred;
- declares NO-GO solely because Change Authority is Unknown;
- declares NO-GO solely because the optional-browser diagnostic failed without establishing that diagnostic as an applicable release-blocking gate;
- upgrades the bare “8 sample inspections passed” status assertion to Verified without underlying UAT result evidence;
- claims GO based on the 8 sample inspections;
- invents a mandatory CAB, rollback, monitoring, security or non-functional gate;
- claims production success before production deployment occurs.

## Pass threshold

**PASS: 90/100 or higher and no automatic fail condition.**
