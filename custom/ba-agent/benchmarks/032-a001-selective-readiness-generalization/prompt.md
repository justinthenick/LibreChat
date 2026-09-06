# A001 selective-routing generalization task

Plan the minimum correct Skill route for the user's requested outcome using only the supplied Skill catalog.

This packet is deliberately different from Benchmark 023: it already contains a normalized BA baseline, acceptance criteria, executed test evidence and traceability. The user explicitly does **not** want those artifacts regenerated.

Do **not** perform the detailed readiness or ITIL assessment in the routing response. Return only:

1. Objective interpreted.
2. Selected Skills in exact execution order.
3. Why each selected Skill is needed.
4. Skills deliberately not selected, with reason.
5. Stop/conditional rules that downstream stages must preserve.
6. Expected final artifact.

Select the minimum route that satisfies the request. Do not invoke a Skill merely because it is available. Do not invent approvals, architecture, owners, policy, rollback mechanics or test evidence.
