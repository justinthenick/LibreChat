# Benchmark 040 prompt — Release decision semantics

Using the supplied input and the `validate-release-evidence` skill, produce the release assurance assessment.

Required behaviours:

1. Identify the question as **pre-deployment go/no-go readiness**, not completed release success.
2. Preserve the narrow fact that **8 sample inspections passed** separately from whether that sample size is sufficient for approval.
3. Treat future production deployment and future post-deployment verification as future-phase evidence, not automatic present blockers.
4. Preserve **Change Authority: Unknown** without inventing CAB, approval prerequisites or a mandatory authority gate.
5. Do not label generic rollback, monitoring, support, security or non-functional evidence as mandatory blockers because no source policy establishes those requirements.
6. Do not return **NO-GO** unless supplied evidence demonstrates a failed condition or explicit source-backed gate.
7. State whether GO is established, NO-GO is established, or neither is established from the supplied evidence.
