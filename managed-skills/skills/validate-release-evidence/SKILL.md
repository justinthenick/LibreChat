---
name: validate-release-evidence
description: Validate supplied implementation, deployment, test, monitoring, change-record, rollback, defect and post-release evidence to determine what a release or release decision actually demonstrates, using Verified, Partially evidenced, Not evidenced and Failed states without inventing success, execution, approvals or missing evidence.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Validate Release Evidence

Version: **0.3.1**

## Purpose

Assess what supplied release evidence actually proves. Separate demonstrated outcomes from claims, plans, missing evidence, failed checks and unresolved defects.

This Skill is evidence validation, not deployment execution, approval, incident response, or retrospective invention.

## Core principle

**A release or release decision is only as strong as the evidence demonstrates. Absence of evidence is not proof of failure, a claim or plan is not proof of execution/success, and evidence for one decision phase must not be used as though it belonged to another phase.**

## Source-closure rule — mandatory

Assess only conditions created by the supplied evidence, the explicit assurance question, or an explicitly supplied local policy/control/acceptance criterion. Evidence categories in this Skill are classification aids, **not a checklist of topics that must be present**.

Do not scan the negative space for ordinary release controls merely because the user asks for go/no-go or release readiness. Unless the supplied source or policy makes them material, **omit** rollback/backout, monitoring, runbooks, support/on-call readiness, communications, security testing, regression testing, performance/non-functional testing, full-scope testing, CAB, approval roles, environment parity, deployment-log proof, smoke-test proof, alerting and other operational controls from gaps, blockers, residual risks and next-evidence requirements.

If a condition cannot be mapped to a supplied fact, the explicit decision question, or supplied policy/criteria, do not introduce it as an assurance dimension.

A narrow supplied result remains narrow without creating new requirements. For example, `UAT passed for 8 sample inspections` does not create a requirement for broader regression, security, non-functional, environment-parity or operational-readiness evidence unless the source/policy establishes those dimensions.

## Decision frame

Before grading evidence, identify the decision being asked:

1. **Pre-deployment go/no-go readiness** — whether supplied evidence is sufficient to support, reject or leave unresolved a decision to enter the production change window.
2. **Deployment execution** — whether the production deployment actually ran and what happened during execution.
3. **Post-deployment verification** — whether production checks demonstrate the implemented change is healthy after deployment.
4. **Release success** — whether the completed release is evidenced as successful overall.

Do not collapse these phases.

- If production deployment is still future, lack of post-deployment verification is expected future state and must **not** by itself count against pre-deployment readiness.
- A future production deployment means deployment execution and post-deployment success are **not yet established**; it does not prove a pre-deployment no-go.
- Conversely, pre-deployment evidence cannot establish production success before production execution and verification occur.

## Evidence states

Use:

- `Verified` — supplied underlying evidence directly demonstrates the stated condition.
- `Partially evidenced` — some relevant evidence supports the condition, including stakeholder/status assertions that are not independently demonstrated by an underlying result artifact.
- `Not evidenced` — the packet does not demonstrate a source-relevant condition or execution being assessed.
- `Failed` — supplied evidence directly demonstrates that a source-relevant condition was not met.
- `Not applicable / out of scope` — the supplied release scope/evidence explicitly establishes that the condition is not applicable or excluded.

`Not applicable / out of scope` is never inferred merely because an activity was not executed, a control was unnecessary during this run, or evidence is absent.

## Provenance strength

Preserve the difference between a **reported result** and a **demonstrated result**.

- A test report, execution record, log, screenshot, signed result, named test artifact or equivalent source that directly demonstrates the outcome may support `Verified`.
- A bare stakeholder statement, status summary or prompt assertion such as “Implementation status: Complete”, “deployment succeeded in test”, or “UAT passed for 8 sample inspections” supports the fact only as **reported / Partially evidenced** unless underlying result evidence is also supplied.
- Do not upgrade a reported assertion to `Verified` merely because it appears in the supplied packet.
- Conversely, do not weaken a directly demonstrated narrow result merely because it is insufficient for a broader release decision.

## Claim evidence versus decision sufficiency

Keep these separate:

- **Claim evidence state** asks whether a specific supplied fact is demonstrated and at what provenance strength.
- **Decision sufficiency** asks whether that fact is enough for the broader release decision.

Example:
- If an underlying UAT artifact directly shows 8 identified sample inspections passed, the narrow claim **“8 sample inspections passed”** may be `Verified`.
- If the packet only states **“UAT passed for 8 sample inspections”** without the underlying result artifact, the narrow claim is `Partially evidenced / reported`.
- In either case, whether **8 samples are sufficient acceptance coverage for release approval** remains `Unknown` or `Not established` unless acceptance scope, decision criteria or policy establishes sufficiency.

## Evidence categories

Use these only to classify dimensions that are already made relevant by the supplied evidence/question/policy:

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

**The presence of a category in this list never makes it required for a release assessment.**

## Rules

- Tie every conclusion to a supplied artifact, timestamp, result, screenshot/log excerpt description, test ID, change record, status assertion or other evidence reference.
- Do not infer execution from a plan. A deployment/rollback/test/monitoring plan proves only that the activity/control was planned or documented.
- **Planned-but-unexecuted:** when the assessed question is whether an activity actually ran or succeeded, a supplied plan plus no execution evidence is `Not evidenced`, not `Verified` and not `Not applicable`.
- **Future-phase discipline:** when an activity is intentionally future relative to the decision being assessed, report that future state separately. Do not convert it into a present pre-deployment blocker, readiness penalty or required pre-deployment evidence unless supplied policy or source evidence explicitly makes it a prerequisite.
- Do not infer success from absence of incident reports.
- Do not infer failure from missing evidence; use `Not evidenced` only for source-relevant conditions.
- A failed check remains `Failed` even if the overall release was declared successful by a stakeholder.
- **Failed does not automatically mean NO-GO.** Preserve failure as evidence, then separately determine whether supplied release criteria, change policy, acceptance rules or another source-backed decision framework explicitly establishes that failed condition as an applicable release-blocking gate.
- Preserve known defects and accepted deviations exactly; do not silently downgrade or close them.
- Do not invent rollback execution, rollback success, monitoring checks, approvals, CAB decisions, sign-offs, timestamps, environments, test data, defect severity or release requirements.
- If evidence conflicts, preserve the conflict and mark the affected conclusion unresolved/partially evidenced as appropriate.
- **Aggregate evidence:** a broad source-relevant condition may be `Partially evidenced` when one evidenced layer is healthy but other source-established material layers remain unproven. Do not manufacture additional layers merely to reduce confidence.
- Distinguish current release evidence from future remediation commitments.
- An `Unknown` Change Authority means the authority identity/approval state cannot be evidenced. It does **not** by itself prove that release is blocked, forbidden, unable to proceed or that identifying the authority is a mandatory next-evidence requirement unless supplied policy or source evidence establishes that authority as a gate.
- Generic rollback, monitoring, support, security, non-functional, full-UAT, environment-parity, CAB or other best-practice evidence must not be introduced as a gap, residual risk, blocker or required next evidence unless the supplied release criteria, change classification, policy or explicit question makes that dimension material.

## Output contract

Return only sections needed by the supplied evidence and decision question.

### 1. Decision-framed verdict

Name the decision frame first, then use the strongest defensible verdict for that frame.

For **pre-deployment go/no-go readiness**, prefer one of:

- `Evidence supports a GO decision`
- `Evidence supports a NO-GO decision`
- `Evidence partially supports readiness but does not establish a GO decision`
- `GO/NO-GO approval status is Unknown / not established from supplied evidence`

Use `NO-GO` only when **both** are established by supplied evidence:

1. a condition is demonstrated as failed; and
2. supplied release criteria, change policy, acceptance rules or another source-backed decision framework establishes that condition as an applicable release-blocking gate.

A failed diagnostic, observation or non-gating check remains `Failed` evidence but does not by itself establish NO-GO. Missing evidence alone is not automatically NO-GO.

For **deployment execution / post-deployment verification / release success**, use the strongest supported statement such as:

- `Evidence supports release success`
- `Evidence partially supports release success`
- `Evidence does not establish release success`
- `Evidence demonstrates release failure`

Do not answer a pre-deployment readiness question with a post-deployment-success verdict unless the user actually asked both.

### 2. Evidence inventory

List supplied evidence and what each can establish. A plan establishes planned intent, not execution. Label bare status assertions as reported/Partially evidenced unless underlying artifacts are supplied. Preserve narrow facts separately from broader sufficiency judgments.

### 3. Validation matrix

Include only source-relevant release conditions. For each included condition, show:

- Evidence ID / condition;
- evidence state;
- provenance/source strength;
- source evidence;
- conclusion;
- limitation/gap;
- decision phase where useful.

Do not add rows for generic controls that the source never made relevant.

### 4. Failed or conflicting evidence

Surface only supplied Failed checks, contradictory records and unresolved deviations. For each failed condition relevant to a go/no-go decision, state separately whether its release-gate applicability is `Established`, `Not established`, or `Unknown` from supplied policy/criteria.

### 5. Source-relevant unresolved items

List only claims/conditions that the supplied packet, decision question or supplied policy actually asks the reviewer to accept or assess but does not establish. Future post-deployment checks may be labelled as future-phase state; do not present them as present blockers or required pre-deployment evidence unless source policy says so.

### 6. Known defects / residual risk

Preserve supplied defect/deviation/risk status only. Do not create residual risks from generic missing controls, narrow sample size, unknown authority or future-phase verification unless the source establishes an actual risk or requirement.

### 7. Handoff / next evidence

State what can safely be reported as demonstrated, reported/partial, failed, Unknown or future-phase.

Request next evidence **only** for source-created/material decision dimensions. If no supplied criteria or policy establishes a mandatory next artifact, say so rather than generating a best-practice checklist.

## Self-check

Before returning, verify:

- the requested decision phase was identified correctly;
- no future post-deployment evidence was used as a present pre-deployment blocker, readiness penalty or required evidence without an explicit source-backed gate;
- no pre-deployment evidence was used to claim production success;
- no bare stakeholder/status assertion, including `Implementation status: Complete`, was upgraded to `Verified` without underlying evidence;
- no directly demonstrated narrow fact was weakened merely because broader decision sufficiency remains unknown;
- no plan was treated as execution evidence;
- no planned-but-unexecuted activity was mislabeled `Not applicable/out of scope` without explicit scope evidence;
- no partial technical-health evidence became proof of complete service/business health;
- no missing evidence became a failure or NO-GO by default;
- no failed condition became NO-GO unless its applicability as a release-blocking gate was source-backed;
- no `Unknown` authority became an invented mandatory approval gate or required next-evidence item;
- no generic rollback, monitoring, support, runbook, security, regression, NFR, full-UAT, CAB, environment-parity or operational-readiness topic was introduced unless source/policy made it relevant;
- no generic best-practice evidence category was called mandatory, a blocker, residual risk or required next evidence without supplied policy/criteria;
- no stakeholder declaration overrode contrary evidence;
- no defect was silently closed;
- no approval/rollback/monitoring/test execution detail was invented.

## Changelog

### 0.3.1

- Restored strict source-closure from the validated Synology v0.2.1 behaviour and combined it with v0.3.0 decision semantics.
- Explicitly classified bare implementation-complete status assertions as reported/Partially evidenced without underlying artifacts.
- Prohibited generic rollback, monitoring, security, NFR, full-UAT, CAB, environment-parity and operational-readiness gaps unless source/policy makes them relevant.
- Prevented future production verification and Unknown authority from becoming readiness penalties or mandatory next-evidence requirements without source-backed policy.
- Removed generic “additional assurance dimensions” from the handoff contract; next evidence must now be source-created/material.

### 0.3.0

- Added explicit pre-deployment, execution, post-deployment and release-success decision frames.
- Prevented future post-deployment verification from being treated as an automatic pre-deployment blocker.
- Separated evidence provenance, narrow claim verification and broader decision sufficiency.
- Required underlying result evidence before a bare stakeholder/status assertion can be `Verified`.
- Required both a demonstrated failure and source-backed release-gate applicability before returning NO-GO.
- Prevented Unknown authority and generic missing evidence from being promoted into mandatory release gates without source-backed policy.
- Added pre-deployment GO / NO-GO / Unknown verdict semantics.

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
