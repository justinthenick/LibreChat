# Benchmark 040 prompt — Release decision semantics

Using the supplied input and the `validate-release-evidence` skill, produce the release assurance assessment.

Required behaviours:

1. Identify the question as **pre-deployment go/no-go readiness**, not completed release success.
2. Treat the bare status assertion **“8 sample inspections passed”** as reported / Partially evidenced because no underlying UAT result artifact is supplied; separately assess whether that sample size is sufficient for approval.
3. Preserve the diagnostic compatibility check as **Failed** evidence, but do not treat it as a NO-GO unless supplied evidence also establishes that condition as an applicable release-blocking gate.
4. Treat future production deployment and future post-deployment verification as future-phase evidence, not automatic present blockers.
5. Preserve **Change Authority: Unknown** without inventing CAB, approval prerequisites or a mandatory authority gate.
6. Do not label generic rollback, monitoring, support, security or non-functional evidence as mandatory blockers because no source policy establishes those requirements.
7. Do not return **NO-GO** unless supplied evidence establishes both a failed condition and that condition's applicability as a release-blocking gate/decision rule.
8. State whether GO is established, NO-GO is established, or neither is established from the supplied evidence.
