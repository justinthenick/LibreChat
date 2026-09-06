# Controlled readiness-generalization task

Produce only the artifact required by your current stage.

The supplied packet is already the normalized BA baseline for this decision point. Do not redo requirements analysis, decomposition, acceptance-criteria design or test-case derivation.

Preserve upstream IDs, evidence strength, requirement status, authority boundaries and unresolved uncertainty. Downstream detail must never become more certain than the supplied evidence.

Do not reconstruct missing facts from common practice. Do not invent architecture, CAB/Change Authority, approval owners, rollout groups, rollback timing, monitoring thresholds, test execution detail or local policy.

Candidate remains Candidate; Target remains Target; Unknown remains Unknown unless supplied evidence explicitly resolves it. Confirmed local-policy gates remain source-specific local-policy gates.

## Pipeline handoff integrity

- A sentinel is evidence only that the required upstream output contract reached its end; it is not business evidence.
- Never manufacture an upstream sentinel that was not present in the supplied handoff.
- If a stage requires an upstream sentinel and it is absent, return only the stated `UPSTREAM_INCOMPLETE` marker and stop.
- Emit your own completion sentinel only after every required section of the current stage is complete.
