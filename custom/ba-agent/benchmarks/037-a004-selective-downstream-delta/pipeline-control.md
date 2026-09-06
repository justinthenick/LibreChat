# Fixed-control selective requirement-delta pipeline

Execute exactly:

1. requirement-change reconciliation;
2. acceptance-criteria updates for supported affected scope only;
3. test-case updates for supported affected scope only.

Do not run requirements analysis, decomposition or change-impact assessment. Preserve unresolved proposals and unaffected baseline items. Do not invent authority, implementation details, acceptance behavior or test expectations beyond the supported deltas.
