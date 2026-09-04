---
name: validate-release-evidence
description: Validate supplied implementation, deployment, test, monitoring, change-record, rollback, defect and post-release evidence to determine what a release actually demonstrates, using Verified, Partially evidenced, Not evidenced and Failed states without inventing success, execution, approvals or missing evidence.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Validate Release Evidence

Version: **0.2.0**

## Purpose

Assess what supplied release evidence actually proves. Separate demonstrated outcomes from claims, plans, missing evidence, failed checks and unresolved defects.

This Skill is evidence validation, not deployment execution, approval, incident response, or retrospective invention.

## Core principle

**A release is only as successful as the evidence demonstrates. Absence of evidence is not proof of failure, and a claim or plan is not proof of execution/success.**

## Evidence states

Use:

- `Verified` — supplied evidence directly demonstrates the stated condition.
- `Partially evidenced` — some relevant evidence directly supports part of a broader condition, but material aspects remain unproven.
- `Not evidenced` — the packet does not demonstrate the condition or execution being assessed.
- `Failed` — supplied evidence directly demonstrates that the condition was not met.
- `Not applicable / out of scope` — the supplied release scope/evidence explicitly establishes that the condition is not applicable or excluded.

`Not applicable / out of scope` is never inferred merely because an activity was not executed, a control was unnecessary during this run, or evidence is absent.

## Evidence categories

Assess only categories relevant to the supplied release:

- deployment/change execution;
- functional/acceptance test outcomes;
- non-functional/assurance outcomes;
- service health / monitoring evidence;
- known defects / deviations;
- rollback/backout evidence;
- configuration/version evidence;
- user/business validation;
- operational handover/support readiness;
- change record / authorization evidence where supplied.

## Rules

- Tie every conclusion to a supplied artifact, timestamp, result, screenshot/log excerpt description, test ID, change record or other evidence reference.
- Do not infer execution from a plan. A deployment/rollback/test/monitoring plan proves only that the activity/control was planned or documented.
- **Planned-but-unexecuted:** when the assessed question is whether an activity actually ran or succeeded, a supplied plan plus no execution evidence is `Not evidenced`, not `Verified` and not `Not applicable`.
- Do not infer success from absence of incident reports.
- Do not infer failure from missing screenshots/logs; use `Not evidenced`.
- A failed check remains Failed even if the overall release was declared successful by a stakeholder.
- Preserve known defects and accepted deviations exactly; do not silently downgrade or close them.
- Do not invent rollback execution, rollback success, monitoring checks, approvals, CAB decisions, sign-offs, timestamps, environments, test data or defect severity.
- If evidence conflicts, preserve the conflict and mark the affected conclusion unresolved/partially evidenced as appropriate.
- **Aggregate evidence:** a broad condition may be `Partially evidenced` when one evidenced layer is healthy (for example process/container/endpoint health) but other material layers (for example transaction/customer/business health) remain unproven. Keep the narrower unproven layers individually `Not evidenced`; do not let partial technical proof become full service/business proof.
- Distinguish current release evidence from future remediation commitments.

## Output contract

Return:

### 1. Release evidence verdict

`Evidence supports release success`, `Evidence partially supports release success`, `Evidence does not establish release success`, or `Evidence demonstrates release failure`, with concise rationale. Use the strongest statement the packet supports, not the stakeholder's preferred wording.

### 2. Evidence inventory

List supplied evidence artifacts and what each can establish. A plan establishes planned intent/availability of a procedure, not execution.

### 3. Validation matrix

For each material release condition:

- Evidence ID / condition;
- upstream requirement/AC/test/change reference where supplied;
- evidence state;
- source evidence;
- conclusion;
- limitation/gap.

Where useful, separate a broad condition (for example `service health`) from narrower layers (technical endpoint/container health vs transaction/customer/business health) so partial evidence is not flattened into either full success or total absence.

### 4. Failed or conflicting evidence

Explicitly surface all Failed checks, contradictory records and unresolved deviations.

### 5. Not-evidenced items

List material claims/conditions that the packet asks the reviewer to accept or assess but does not demonstrate. Planned-but-unexecuted activity belongs here when execution matters. Do not convert missing evidence into mandatory future gates unless source policy says so.

### 6. Known defects / residual risk

Preserve supplied defect/deviation status and any explicitly stated acceptance decision/owner.

### 7. Handoff

State what can safely be reported as demonstrated, partially evidenced, failed, and unproven for operational readiness / ITIL / release reporting.

## Self-check

Before returning, verify:

- no plan was treated as execution evidence;
- no planned-but-unexecuted activity was mislabeled `Not applicable/out of scope` without explicit scope evidence;
- no partial technical-health evidence became proof of complete service/business health;
- no missing evidence became a failure;
- no stakeholder declaration overrode contrary evidence;
- no defect was silently closed;
- no approval/rollback/monitoring/test execution detail was invented.

## Changelog

### 0.2.0

- Reserved `Not applicable / out of scope` for explicitly established scope states.
- Made planned-but-unexecuted activities `Not evidenced` for execution questions.
- Added aggregate/partial-evidence handling so scoped technical health can coexist with unproven transaction/business health.

### 0.1.0

- Initial evidence-backed release validation capability.
