---
name: validate-release-evidence
description: Validate supplied implementation, deployment, test, monitoring, change-record, rollback, defect and post-release evidence to determine what a release actually demonstrates, using Verified, Partially evidenced, Not evidenced and Failed states without inventing success, execution, approvals or missing evidence.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Validate Release Evidence

Version: **0.2.1**

## Purpose

Assess what supplied release evidence actually proves. Separate demonstrated outcomes from claims, plans, missing evidence, failed checks and unresolved defects.

This Skill is evidence validation, not deployment execution, approval, incident response, or retrospective invention.

## Core principle

**A release is only as successful as the evidence demonstrates. Absence of evidence is not proof of failure, and a claim or plan is not proof of execution/success.**

## Source-closure rule — mandatory

Assess only release conditions that are created by the supplied evidence, the assurance question, or an explicitly supplied local policy/control. The evidence-category list below is a classification aid, **not** a checklist of topics that must be present.

Do not scan the negative space for ordinary release controls merely because the user asks for go/no-go or release readiness. Unless the source or supplied policy makes them material, do not introduce rollback/backout, monitoring, runbooks, support/on-call readiness, communications, security testing, regression testing, performance/non-functional testing, full-scope testing, CAB, approval roles, environment parity, deployment logs, alerting or operational controls as gaps, blockers, residual risks or next-evidence requirements.

If a condition cannot be mapped to a supplied fact, an explicit assurance question, or supplied policy, omit it.

A supplied narrow result remains narrow. For example, `UAT passed for 8 sample inspections` proves only the stated sample result; it does not create an additional requirement for broader regression, security, non-functional or production-parity testing unless the source/policy establishes one.

## Temporal decision rule — mandatory

Keep pre-deployment approval evidence separate from future or post-deployment verification evidence.

If production deployment is planned but has not occurred, a statement that production verification has not yet occurred is an accurate current evidence state. **Do not convert future/post-deployment verification into a prerequisite for a pre-deployment go/no-go decision unless supplied policy explicitly establishes that gate.**

Likewise, a future deployment plan is not evidence of execution or success, but its lack of execution is not itself a failed pre-deployment control unless the decision being assessed is explicitly post-deployment success/readiness.

## Evidence states

Use:

- `Verified` — supplied evidence directly demonstrates the stated condition.
- `Partially evidenced` — some relevant evidence directly supports part of a broader condition, but material aspects remain unproven.
- `Not evidenced` — the packet does not demonstrate the condition or execution being assessed.
- `Failed` — supplied evidence directly demonstrates that the condition was not met.
- `Not applicable / out of scope` — the supplied release scope/evidence explicitly establishes that the condition is not applicable or excluded.

`Not applicable / out of scope` is never inferred merely because an activity was not executed, a control was unnecessary during this run, or evidence is absent.

## Evidence categories

Assess **only categories relevant to the supplied release evidence/question/policy**:

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

The presence of a category in this list does not make it required for every release assessment.

## Rules

- Tie every conclusion to a supplied artifact, timestamp, result, screenshot/log excerpt description, test ID, change record or other evidence reference.
- Do not infer execution from a plan. A deployment/rollback/test/monitoring plan proves only that the activity/control was planned or documented.
- **Planned-but-unexecuted:** when the assessed question is whether an activity actually ran or succeeded, a supplied plan plus no execution evidence is `Not evidenced`, not `Verified` and not `Not applicable`.
- Do not infer success from absence of incident reports.
- Do not infer failure from missing screenshots/logs; use `Not evidenced` only when that condition is actually in scope.
- A failed check remains Failed even if the overall release was declared successful by a stakeholder.
- Preserve known defects and accepted deviations exactly; do not silently downgrade or close them.
- Do not invent rollback execution, rollback success, monitoring checks, approvals, CAB decisions, sign-offs, timestamps, environments, test data or defect severity.
- If evidence conflicts, preserve the conflict and mark the affected conclusion unresolved/partially evidenced as appropriate.
- **Aggregate evidence:** a broad condition may be `Partially evidenced` when one evidenced layer is healthy but other **source-established material layers** remain unproven. Do not manufacture additional layers merely to reduce confidence.
- Distinguish current release evidence from future remediation commitments.
- An Unknown Change Authority means the authority/approval state cannot be evidenced. Do not invent the authority and do not automatically turn Unknown authority into a universal blocker unless policy says it is.
- Do not state that release cannot proceed merely because a source-relevant condition is Unknown; distinguish `approval/readiness not established from supplied evidence` from a policy-defined `No-Go`.

## Output contract

Return only sections needed by the supplied evidence/question:

### 1. Release evidence verdict

Use the strongest evidence statement supported, for example `Evidence supports release success`, `Evidence partially supports release success`, `Evidence does not establish release success/readiness`, or `Evidence demonstrates release failure`. Do not turn an evidence insufficiency verdict into a policy No-Go unless a supplied policy establishes the gate.

### 2. Evidence inventory

List supplied evidence and what each item can establish. Preserve report/claim/sample/plan limitations exactly.

### 3. Validation matrix

For each **source-relevant** release condition:

- Evidence ID / condition;
- evidence state;
- source evidence;
- conclusion;
- limitation/gap.

### 4. Failed or conflicting evidence

Surface only supplied Failed checks, contradictory records and unresolved deviations.

### 5. Source-relevant not-evidenced items

List only claims/conditions that the packet or assurance question actually asks the reviewer to accept or assess but does not demonstrate. Do not populate a generic release-readiness checklist.

### 6. Known defects / residual risk

Preserve supplied defect/deviation/risk status. Do not create residual risks from generic missing controls.

### 7. Handoff / next evidence

State what can safely be reported as demonstrated, partial, failed, Unknown or not yet occurred. Request next evidence only for source-created/material decision dimensions; do not invent generic future evidence requirements.

## Self-check

Before returning, verify:

- no plan was treated as execution evidence;
- no planned-but-unexecuted activity was mislabeled `Not applicable/out of scope` without explicit scope evidence;
- no sample result was generalized beyond the supplied sample;
- no missing evidence became a failure;
- no stakeholder declaration overrode contrary evidence;
- no defect was silently closed;
- no approval/rollback/monitoring/test execution detail was invented;
- no generic rollback, monitoring, support, runbook, security, regression, NFR, CAB or operational-readiness topic was introduced unless source/policy made it relevant;
- no future/post-deployment verification was treated as a pre-deployment gate without supplied policy;
- `Unknown / not established` was not silently upgraded to `No-Go / cannot proceed`.

## Changelog

### 0.2.1

- Added source-closure so evidence categories cannot become a generic release checklist.
- Added temporal separation between pre-deployment go/no-go and future/post-deployment verification.
- Prevented unsourced rollback, monitoring, support, NFR, regression, CAB and operational-readiness gaps.
- Prevented evidence insufficiency from being silently upgraded to policy-defined No-Go.

### 0.2.0

- Reserved `Not applicable / out of scope` for explicitly established scope states.
- Made planned-but-unexecuted activities `Not evidenced` for execution questions.
- Added aggregate/partial-evidence handling so scoped technical health can coexist with unproven transaction/business health.

### 0.1.0

- Initial evidence-backed release validation capability.
