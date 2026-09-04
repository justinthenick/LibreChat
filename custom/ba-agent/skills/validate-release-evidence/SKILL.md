---
name: validate-release-evidence
description: Validate supplied implementation, deployment, test, monitoring, change-record, rollback, defect and post-release evidence to determine what a release actually demonstrates, using Verified, Partially evidenced, Not evidenced and Failed states without inventing success, execution, approvals or missing evidence.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Validate Release Evidence

Version: **0.1.0**

## Purpose

Assess what supplied release evidence actually proves. Separate demonstrated outcomes from claims, missing evidence, failed checks and unresolved defects.

This Skill is evidence validation, not deployment execution, approval, incident response, or retrospective invention.

## Core principle

**A release is only as successful as the evidence demonstrates. Absence of evidence is not proof of failure, and a claim is not proof of success.**

## Evidence states

Use:

- `Verified` — supplied evidence directly demonstrates the stated condition.
- `Partially evidenced` — some relevant evidence exists but does not fully establish the condition.
- `Not evidenced` — the packet does not demonstrate the condition.
- `Failed` — supplied evidence directly demonstrates that the condition was not met.
- `Not applicable / out of scope` — explicitly outside the assessed release scope.

Do not use `Passed` merely because someone wrote that a test passed; distinguish assertion from corroborating evidence where relevant.

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
- Do not infer execution from a plan. A deployment plan is not deployment evidence.
- Do not infer success from absence of incident reports.
- Do not infer failure from missing screenshots/logs; use `Not evidenced`.
- A failed check remains Failed even if the overall release was declared successful by a stakeholder.
- Preserve known defects and accepted deviations exactly; do not silently downgrade or close them.
- Do not invent rollback execution, rollback success, monitoring checks, approvals, CAB decisions, sign-offs, timestamps, environments, test data or defect severity.
- If evidence conflicts, preserve the conflict and mark the affected conclusion unresolved/partially evidenced as appropriate.
- Distinguish current release evidence from future remediation commitments.

## Output contract

Return:

### 1. Release evidence verdict

`Evidence supports release success`, `Evidence partially supports release success`, `Evidence does not establish release success`, or `Evidence demonstrates release failure`, with concise rationale. Use the strongest statement the packet supports, not the stakeholder's preferred wording.

### 2. Evidence inventory

List supplied evidence artifacts and what each can establish.

### 3. Validation matrix

For each material release condition:

- Evidence ID / condition;
- upstream requirement/AC/test/change reference where supplied;
- evidence state;
- source evidence;
- conclusion;
- limitation/gap.

### 4. Failed or conflicting evidence

Explicitly surface all Failed checks, contradictory records and unresolved deviations.

### 5. Not-evidenced items

List material claims that the packet asks the reviewer to accept but does not demonstrate. Do not convert them into mandatory future gates unless source policy says so.

### 6. Known defects / residual risk

Preserve supplied defect/deviation status and any explicitly stated acceptance decision/owner.

### 7. Handoff

State what can safely be reported as demonstrated and what remains unproven for operational readiness / ITIL / release reporting.

## Self-check

Before returning, verify no plan was treated as execution evidence, no missing evidence became a failure, no stakeholder declaration overrode contrary evidence, no defect was silently closed, and no approval/rollback/monitoring/test execution detail was invented.