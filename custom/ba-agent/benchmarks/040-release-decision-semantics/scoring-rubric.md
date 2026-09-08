# Benchmark 040 scoring rubric — Release decision semantics

Score out of 100.

## 1. Correct decision frame — 20
- 20: Explicitly frames the task as **pre-deployment go/no-go readiness**.
- 10: Implied but not explicit.
- 0: Treats the task primarily as completed release success/post-deployment verification.

## 2. GO / NO-GO semantics — 20
- 20: Concludes that **neither GO nor NO-GO is established** from the supplied evidence.
- 10: Correctly withholds GO but ambiguously suggests a blocker/no-go.
- 0: Declares GO or NO-GO without source-backed evidence.

## 3. Sample evidence discipline — 15
- 15: Preserves “8 sample inspections passed” as the narrow demonstrated fact while keeping acceptance sufficiency Unknown/not established.
- 8: Avoids overgeneralization but flattens the narrow fact into partial evidence.
- 0: Treats the 8 samples as proof of full UAT/production readiness.

## 4. Future-phase discipline — 15
- 15: Treats production deployment/verification as future-phase evidence and not automatic present blockers.
- 8: Notes they are future but still uses them to weaken pre-deployment readiness materially.
- 0: Uses absent production verification as a reason the pre-deployment decision fails.

## 5. Authority discipline — 10
- 10: Reports Change Authority as Unknown without inventing a mandatory approval gate.
- 5: Mostly correct but implies approval cannot proceed without identifying authority.
- 0: Invents CAB/authority requirements or treats Unknown authority as a mandatory blocker.

## 6. Generic-gap discipline — 10
- 10: Does not call rollback, monitoring, support, security or non-functional evidence mandatory without supplied policy; may list them only as unevidenced/applicability-to-confirm dimensions.
- 5: Includes them but with mixed “required” language.
- 0: Converts generic best-practice categories into mandatory blockers.

## 7. Evidence-state clarity — 10
- 10: Clearly distinguishes Verified/reported/Unknown/not established states and ties them to source facts.
- 5: Mostly clear with minor state conflation.
- 0: Upgrades/downgrades evidence materially or invents facts.

## Automatic fail conditions

Benchmark fails regardless of numeric score if the response:
- declares NO-GO solely because production verification has not yet occurred;
- declares NO-GO solely because Change Authority is Unknown;
- claims GO based on the 8 sample inspections;
- invents a mandatory CAB, rollback, monitoring, security or non-functional gate;
- claims production success before production deployment occurs.

## Pass threshold

**PASS: 90/100 or higher and no automatic fail condition.**
