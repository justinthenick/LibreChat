# Benchmark 042 gold standard — Multi-Source BA Model Comparison

Evaluator-only. Do not send to the model under test.

## Required source treatment

All four sources must be materially used:
- `SRC-DOC-01` for form mechanics, baseline lead-time rules, document rules, site/key logic and lifecycle rules.
- `SRC-XLS-01` as an operational configuration/decision source, not background data. It must materially influence requirements/RTM for taxonomy, assignment routing, Standard Change eligibility, SAR eligibility, document flags, change type/approval and lead-time values.
- `SRC-MAP-01` for state paths, mapped/unmapped assignment routing and the four explicit unresolved annotations.
- `SRC-PPT-01` for the explicitly stated business outcomes/benefits and target-state rationale.

## Required contradiction / ambiguity handling

### G1 — Lead-time discrepancy
Must identify a source conflict between:
- DOC business-day/approval-based formulas; and
- XLS static/example values such as 6 days, 4 days, `25 + days to next CAB`, `54 + days to next CAB`.

The affected lead-time requirement must not be Confirmed as one selected formula. No source precedence is supplied.

### G2 — Document-rule discrepancy
Must identify that DOC says MOP and SWMS are mandatory globally while XLS contains activity rows where one or both flags are false. The model must not silently collapse these into one rule.

### G3 — Standard Change state-path discrepancy
Must preserve the conflict between:
- New -> Assess -> Authorise -> Scheduled; and
- Site-inspection Standard Change New -> Scheduled.

Do not select a single state path as universally confirmed.

### G4 — CyberKey wording contradiction
The Field 69 validation sentence is internally contradictory. The correct BA treatment is to flag the condition as ambiguous/defective and set the required outcome to Unknown / not established. Do not "correct" it to Q67=Yes AND Q68=CyberKey unless the source itself resolves that.

## Required source-created unresolved dimensions

The output must preserve the following unresolved dimensions from the process map without inventing answers:
1. Whether a flagged user/org may proceed with change creation — outcome Unknown.
2. Post-site-visit task sampling/quota — 10% action / 90% auto-close is posed as a question, not a decided requirement; outcome Unknown.
3. Post-site-visit task target channel/entity — SNOW/Appian/other is unresolved; outcome Unknown.
4. Minor date-change target state — Authorise versus new `Amend` state is unresolved; outcome Unknown.

These may be represented as four Decision Items or equivalent one-for-one unresolved dimensions. Do not add adjacent generic engineering questions.

## Required XLS-derived confirmed atoms

Where not contradicted by another source, the output should surface at least these XLS-backed requirements/rules:
- four-tier taxonomy dependency;
- default assignment-group routing by selected activity;
- PSN Helpdesk fallback for unmapped assignment groups, using the process map plus XLS mapping context;
- Standard Change eligibility driven by the workbook boolean;
- SAR availability driven by the workbook boolean;
- activity-specific MOP/SWMS/Release Notes flags, while preserving the DOC-vs-XLS document-rule conflict;
- Change Type and approval matrix: Minor -> Change Manager, Significant -> CAB, Major -> CAB + TAEC;
- permitted impact/configuration values as catalogue-controlled data where relevant.

## Benefits discipline

Only source-backed benefits/outcomes may be stated. Examples explicitly supported by `SRC-PPT-01`:
- reduce processing time and double handling;
- improve classification and allocation of work;
- replace one-size-fits-all risk assessment with more applicable risk treatment.

Do not invent generic benefits such as improved auditability, security, compliance, accountability, resilience, reduced alarm fatigue, legal protection, customer satisfaction, operational excellence, or elimination of zombie records unless directly tied to supplied wording.

## Negative-space prohibition

Do not create missing requirements, gaps, risks or questions for unsupplied topics such as:
- API design;
- database design;
- retries/errors;
- logging/audit;
- telemetry;
- security;
- performance/availability;
- environment parity;
- test data;
- deployment/rollback;
- ownership/governance beyond explicitly named source roles.

## Decomposition and acceptance criteria

Backlog items must remain solution-neutral and trace to source-backed requirements.
Acceptance criteria must test only established source outcomes. Do not create acceptance criteria that decide G1-G4 or any unresolved process-map dimension.

A valid AC can test, for example:
- company-filtered Standard Change catalogue;
- mapped assignment group lookup where mapping exists;
- PSN Helpdesk allocation where no mapping exists;
- qualified visitors for selected Work Type;
- No Show closure when Scheduled after Planned End Date;
- activity eligibility/flags where the underlying source rule is not itself disputed.

## Readiness assessment

Implementation-ready areas may include source-closed form mechanics, taxonomy structure, mapped assignment routing, site qualification, and established closure rules.

Not implementation-ready without resolution:
- final lead-time algorithm/source precedence;
- final global-vs-activity-specific MOP/SWMS rule;
- universal Standard Change state path;
- CyberKey Field 69 display condition;
- flagged-user outcome;
- post-visit quota;
- post-visit task entity/channel;
- minor date-change target state.

The readiness assessment must not manufacture blockers for generic missing engineering detail.
