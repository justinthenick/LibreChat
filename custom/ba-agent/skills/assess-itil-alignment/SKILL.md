---
name: assess-itil-alignment
description: Assess BA, solution-handoff, release, deployment, configuration and change-readiness evidence for ITIL 4 practice alignment without falsely claiming formal compliance, inventing governance or treating missing evidence as a proven failure.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Assess ITIL Alignment

Version: **0.2.0**

## Purpose

Assess supplied delivery/change evidence against relevant **ITIL 4 practice concepts** and identify supported alignment, missing evidence, potential conflicts and follow-up questions.

This skill is an **alignment/readiness assessment**, not a certification audit and not a claim that an organisation, process or change is formally `ITIL compliant`.

## Core principle

**ITIL guidance informs the assessment; it does not create organisation-specific policy, approval authority or missing evidence.**

The assessment must remain traceable to supplied evidence and must distinguish:

- what the source demonstrates;
- what is not evidenced;
- what appears to conflict with an established organisational rule;
- what is merely a stakeholder proposal;
- what requires clarification.

## Relevant practice lens

Use only practices that are materially relevant to the supplied scenario. Commonly relevant practices for BA / solution / change-readiness work include:

- **Change Enablement** — successful change through appropriate risk assessment, authorisation and change-schedule coordination;
- **Release Management** — making new or changed services/features available for use in line with organisational policies and agreements;
- **Deployment Management** — moving new or changed components into target environments;
- **Service Configuration Management** — maintaining accurate and reliable information about services, configuration items and their relationships when needed;
- **IT Asset Management** — where the supplied change materially affects managed IT assets;
- **Continual Improvement** — where the supplied evidence establishes review/improvement activity;
- **Information Security Management** — only where security requirements, risks or constraints are explicitly in scope.

Do not mechanically list every ITIL practice.

## Alignment statuses

Use these assessment statuses:

- **Aligned / evidenced** — supplied evidence positively supports the relevant practice concern.
- **Partially evidenced** — some relevant evidence exists but a material element remains unresolved or unverified.
- **Not evidenced** — the supplied material does not establish the relevant evidence. This is **not automatically non-compliance**.
- **Potential conflict** — supplied evidence appears inconsistent with an explicit organisational policy, authority rule or sourced constraint.
- **Not applicable / out of scope** — the practice concern is not material to this scenario.

Do not use `Compliant` / `Non-compliant` as default statuses.

## Non-negotiable rules

1. **Do not invent ITIL mandates.**
   Do not claim ITIL universally requires a CAB, a particular change category, rollback plan, PIR, approval role, number of approvers, implementation template, CMDB product, test environment, maintenance window or other organisation-specific mechanism unless the supplied source explicitly establishes that rule.

2. **Do not invent authority.**
   ITIL practice concepts do not assign the organisation's Change Authority, Emergency Change Authority, CAB membership, Service Owner, Product Owner, Security approver or other decision owner. Preserve sourced authority exactly. If authority is unresolved, state `Decision owner: Unknown`.

3. **Missing evidence is not proof of failure.**
   If risk assessment, authorisation evidence, schedule coordination, configuration impact or another relevant artifact is absent, mark it `Not evidenced` or `Partially evidenced`. Do not infer that the activity did not happen.

4. **Do not promote gaps into unsourced gates.**
   A practice concern or missing evidence category may be relevant without being a mandatory local prerequisite. Do not label a missing item `Evidence required`, a mandatory gate, approval condition, sign-off, pre-authorisation prerequisite or blocking governance requirement unless explicit organisational policy, authority rules or supplied source evidence establishes that status. If the source does not establish mandatory status, use `Not evidenced`, `Partially evidenced`, `Readiness question` or `Clarification required` instead.

   In particular, do not turn a missing recovery/backout approach, PIR, configuration-update owner/timing, support plan, communications plan or other sensible practice concern into a mandatory pre-authorisation requirement merely because it is relevant to ITIL. A stakeholder proposal remains a proposal.

5. **Separate ITIL guidance from organisational policy.**
   Explicit internal policy/process requirements take their own sourced status. A stakeholder saying `ITIL requires X` is not proof that ITIL requires X and is not proof that X is organisational policy.

6. **Preserve upstream delivery status.**
   Candidate, Target, Deferred, Disputed and Unknown work remains so. ITIL assessment must not promote or resolve it.

7. **Keep release, deployment and change concerns distinct.**
   Do not collapse release packaging/availability, technical deployment execution and change authorisation/risk/schedule governance into one invented workflow.

8. **Configuration impact is evidence-driven.**
   Where configuration/service records are affected, identify whether required information/impact/update responsibility is evidenced. Do not invent CI classes, CMDB fields, discovery tooling or update mechanisms.

9. **No invented assurance mechanics.**
   State what evidence or condition is relevant without prescribing a tool, API, dashboard, log query, meeting, CAB, form, automation or inspection method unless sourced.

10. **No unofficial maturity score.**
   Do not present a numeric `ITIL maturity` or capability level unless the supplied assessment explicitly uses authorised criteria for the ITIL Maturity Model. This skill's rubric scores are benchmark scores, not ITIL maturity ratings.

11. **Traceability is mandatory.**
    Every material alignment finding should cite the supplied artifact/requirement/change item/evidence ID where IDs exist.

## Assessment workflow

### 1. Scope the relevant practices

Identify only the ITIL practices materially implicated by the supplied evidence and explain why each is relevant in one short phrase.

### 2. Assess evidence by practice concern

For each relevant practice, separate:

- evidenced strengths;
- unresolved/not-evidenced items;
- potential conflicts with sourced organisational constraints;
- explicit stakeholder proposals that are not established policy.

### 3. Identify readiness impacts

Classify each material finding as one of:

- `No current blocker`;
- `Readiness dependency` — only where the supplied source establishes a dependency;
- `Decision required` — only where the supplied source establishes a decision is unresolved;
- `Evidence required` — only where supplied policy/source explicitly makes that evidence required;
- `Clarification required` — relevant but mandatory status is not established;
- `Future / non-current scope`.

Do not claim a release/change is approved or rejected unless the source establishes that decision. Do not infer mandatory readiness gates from generic ITIL relevance.

### 4. Produce focused follow-up questions

Ask only questions whose answers would materially change the alignment/readiness conclusion. Keep unknown ownership Unknown unless sourced. A question may ask whether a practice concern is required locally; it must not presume that it is.

### 5. Perform an anti-invention audit

Before returning the result verify that you have not:

- created a CAB or approval authority;
- converted a proposal into policy;
- treated missing evidence as proven non-compliance;
- promoted a relevant but unsourced gap into a mandatory local gate;
- invented rollback/PIR/change-classification/configuration mechanisms;
- promoted Candidate/Target/Deferred/Unknown scope;
- confused release, deployment and change governance;
- claimed an official ITIL maturity score.

## Default output

1. **Assessment scope and overall alignment readiness**
2. **Applicable ITIL practice map**
3. **Alignment findings**
4. **Readiness dependencies / decisions / evidence gaps**
5. **Organisational-policy vs ITIL-guidance distinctions**
6. **Focused follow-up questions**
7. **Traceability summary**

Recommended table:

`Finding ID | ITIL practice | Evidence / condition | Status | Readiness impact | Source trace`

## Final quality bar

A strong answer helps a Change Manager, BA, Service Owner or delivery lead understand whether the supplied evidence is aligned with relevant ITIL practice concerns **without pretending ITIL supplies local governance that the source never established**.

## Reference basis

Public PeopleCert ITIL 4 descriptions current at skill creation identify Change Enablement, Release Management, Deployment Management, Service Configuration Management and IT Asset Management as closely related Plan/Implement/Control practices. Public Change Enablement material emphasises risk assessment, authorisation and change scheduling; public Service Configuration Management material emphasises accurate and reliable configuration information when and where needed.

## Changelog

### 0.2.0

- Added explicit protection against gap-to-gate promotion after Benchmark 012.
- Missing practice-relevant evidence may not become a mandatory approval/pre-authorisation gate unless supplied local policy/source evidence establishes that status.
- Added `Clarification required` for relevant gaps whose mandatory status is not established.

### 0.1.0

- Initial ITIL 4 alignment/readiness assessment capability.
- Explicitly separates ITIL guidance from organisational policy and authority.
- Prevents false `ITIL compliance` claims and unsupported CAB/rollback/PIR/maturity requirements.
