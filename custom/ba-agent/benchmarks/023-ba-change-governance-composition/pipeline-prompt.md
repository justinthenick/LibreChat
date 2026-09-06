# Controlled composition task

Produce only the artifact required by your current stage.

Preserve upstream IDs, evidence strength, requirement status, authority boundaries and unresolved uncertainty. Downstream detail must never become more certain than the supplied upstream artifact.

Do not reconstruct missing facts from common practice. Do not invent architecture, CAB/Change Authority, approval owners, rollback mechanics, monitoring methods, test execution detail or local policy.

Candidate remains Candidate; Target remains Target; Deferred remains Deferred; Disputed remains Disputed; Unknown remains Unknown unless the supplied upstream artifact explicitly contains new evidence resolving it.

## Pipeline handoff integrity

This benchmark uses explicit transport sentinels so a downstream stage can distinguish a complete upstream artifact from a provider response that stopped early while still reporting a successful HTTP/model status.

- A sentinel is evidence only that the required upstream output contract reached its end; it is not business evidence and must not change requirement/readiness status.
- Never manufacture an upstream sentinel that was not present in the supplied handoff.
- If your stage instruction requires an upstream sentinel and it is absent, return only the stated `UPSTREAM_INCOMPLETE` marker and stop. Do not reconstruct or continue the missing upstream work.
- Emit your own completion sentinel only after every section required by your current stage contract has actually been produced.
