# A002 procurement-only generalization task

Plan the minimum correct Skill route for the user's procurement objective using only the supplied Skill catalog.

This packet is deliberately different from Benchmark 033: the requirements and purchasing boundary are already normalized, there is no unresolved architecture-changing Unknown, and the user explicitly does **not** want requirements analysis, NFR analysis, solution design or ADR work repeated.

The user does want a vendor-neutral procurement specification, deliberate market-expansion coverage beyond the incumbent reseller set, and evidence-based verification of the supplied candidate chairs.

Do **not** perform the detailed procurement work in the routing response. Return only:

1. Objective interpreted.
2. Selected Skills in exact execution order.
3. Why each selected Skill is needed.
4. Skills deliberately not selected, with reason.
5. Stop/conditional rules that downstream stages must preserve.
6. Expected final artifact.

Select the minimum route that satisfies the request. Do not invent product facts, approval authority, requirements, thresholds or candidate evidence.
