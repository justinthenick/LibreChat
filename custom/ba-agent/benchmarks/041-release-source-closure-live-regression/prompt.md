# Benchmark 041 prompt — Release source-closure live regression

Using the supplied input and `validate-release-evidence`, assess the pre-deployment go/no-go approval state.

Required behaviours:

1. Treat `Implementation is now complete` as a bare status assertion and therefore **reported / Partially evidenced**, not Verified, because no underlying completion artifact is supplied.
2. Treat development's successful test-deployment statement as **reported / Partially evidenced**.
3. Treat `UAT passed for 8 sample inspections` as **reported / Partially evidenced** and keep acceptance sufficiency Unknown because no acceptance criteria establish that 8 samples are sufficient.
4. Treat production deployment and production verification as future-phase states; do not use their absence as a current pre-deployment blocker, readiness penalty or required evidence.
5. Preserve Change Authority as **Unknown** without inventing CAB, governance prerequisites or mandatory authority evidence.
6. Do not introduce rollback, monitoring, runbooks, support staffing, security testing, non-functional testing, full-UAT coverage, smoke-test/deployment-log proof, environment parity or other generic best-practice dimensions unless the supplied source makes them relevant.
7. Do not invent residual risks from generic missing controls or from the mere narrowness of the 8-sample result.
8. Do not generate a generic `required evidence` checklist. Request next evidence only for source-created decision dimensions.
9. State the final decision as **GO/NO-GO approval status: neither is established from supplied evidence** (or semantically equivalent Unknown/not established wording).
