# Benchmark 002 — Gold Standard

**Evaluator-only. Do not expose this file to the model under test.**

This is not a required wording template. A strong answer may organize the material differently, but it should preserve the evidential strength, uncertainty and conflicts below.

## 1. Expected business objective

Improve the speed, consistency and freshness of major-incident communications by deriving suitable updates from incident information, while preserving the existing incident-management/bridge process and retaining required human review boundaries.

Supported problems include:

- internal audiences can receive late or inconsistent status;
- manual rewriting/copying creates stale or incorrect information;
- early impact information may change;
- recipients/channels are not consistently current;
- communication triggers/cadence are not fully defined.

Do not invent quantified benefits such as a percentage reduction in MTTR, incident duration, call volume or cost.

## 2. Expected stakeholders / actors

Supported roles include:

- Head of Service Reliability;
- Incident Manager;
- Customer Communications Lead;
- Service Desk Lead;
- Product Owner;
- Platform Engineer;
- Security and Privacy Representative;
- Agile Lead;
- Service Desk agents/internal leaders as communication audiences where useful.

Do not invent a CAB, Major Incident Board, Executive Steering Committee, Architecture Board, Legal approver or other governance body.

The source does not establish an ultimate owner for the disputed internal-communication approval rule.

## 3. Confirmed requirements / constraints that should be captured

Strong analysis should identify most of the following as current confirmed requirements/constraints where appropriate:

- Existing incident-management process and incident bridge must not be replaced/redesigned by this initiative (Source A).
- External customer-facing messages require human review before publication; Incident Manager and Customer Communications Lead agree automation must not directly send unreviewed external communications (Source B; current process in Source C reinforces this).
- Customer-facing wording must use approved customer terminology (Source B).
- Personal information, internal hostnames and restricted internal operational detail must not appear in external communications (Source B).
- Approved authentication patterns and least-privilege access are required (Source B).
- The system must not invent a next-update time when one has not been established (Source B).
- Manual/current process evidence shows external wording is reviewed before publication (Source C), but the exact detailed approval workflow is not established beyond the supplied statements.

A strong answer may also represent the requested communication data fields as explicit requested/candidate first-release content:

- incident ID;
- affected service;
- impact summary;
- current status;
- next update time **if known**.

The evaluator should accept either Confirmed or Candidate for those fields if the response clearly preserves the Product Owner's wording and does not pretend broader stakeholder agreement exists. The key correctness point is the conditional **if known** and the no-invention rule.

## 4. Candidate / target / deferred items

These should not be hardened into committed requirements:

### Target

- A useful first release in **about eight weeks** (Source A) is a desired delivery target, not a hard deadline.
- **Five minutes after a material status change** for an internal update is a desired performance/cadence target from the Product Owner, not an SLA; "material status change" is undefined and source-data latency is unverified.

### Candidate

- Starting with **Severity 1 incidents only** is a suggested initial scope, not settled scope (Source A).
- ITSM core incident data is said to be available, but use of particular integration mechanisms should not be over-specified.
- CMDB relationships, collaboration platform and public status page are candidate sources/channels with unverified APIs/permissions (Source B).
- The Agile Lead's preference for **one internal communication path plus drafted external messaging** is explicitly a delivery suggestion, not an agreed requirement (Source D).

### Deferred

- Reusable templates for different customer segments and multilingual communications are future ideas and should be Deferred, not current requirements (Source B).

## 5. Critical unresolved disagreement

### Internal communication approval / auto-send

This is the main benchmark trap.

- Service Desk Lead prefers automatic sending of internal Service Desk updates once impact is known.
- Incident Manager wants Incident Manager confirmation before internal distribution because impact information is often corrected early in an incident.

The analyst must **not choose a side** or silently invent a compromise such as tiered approval, time-based auto-send, severity-based auto-send, or automatic send after a fixed delay.

Expected treatment:

- Evidence: explicit/disputed as appropriate.
- Requirement status: Disputed.
- Required outcome: establish the approval/send rule for internal communications and the conditions under which an update is eligible to distribute.
- **Decision owner: Unknown** unless the source is supplemented.

A proposed mechanism may be offered only in Analyst proposals and must remain clearly proposed.

## 6. Other important ambiguities / unknowns

A strong answer should capture several of these:

- No agreed definition of **material status change**.
- Incident severity can change during the incident lifecycle; the effect on scope/communication behavior is not defined.
- Impact information may be incomplete/revised early in an incident.
- No standard internal communication cadence exists.
- Internal recipients, distribution lists and channel membership are not settled/current.
- Exact channels for the first release are not confirmed.
- The authoritative source for recipient membership is not established.
- Candidate API/permission feasibility is incomplete.
- CMDB/CI relationship quality may affect impacted-service accuracy.
- The exact external approval workflow beyond Communications approval/review is not fully defined.
- No decision owner for cross-role policy disputes is established.
- Success criteria for "faster" and "more consistent" communications are not quantified.

## 7. Activity/responsibility versus authority

Benchmark 002 intentionally tests this distinction.

Supported activities include:

- Platform Engineer evaluates candidate integrations/API feasibility.
- Customer Communications reviews/approves external wording.
- Security/Privacy reviews what channels/data leave the company and imposes security/privacy constraints.
- Agile Lead provides delivery guidance.

Do not automatically convert those activities into authority over unrelated business decisions.

Examples of incorrect overreach:

- Platform Engineer owns the five-minute SLA decision.
- Security Representative owns the internal auto-send policy.
- Agile Lead approves MVP scope.
- Head of Service Reliability is automatically final approver for all requirements.

## 8. Required outcome versus proposed mechanism

Benchmark 002 also tests whether the analyst separates **what must be established** from **how the analyst suggests doing it**.

Correct required outcomes include:

- Establish the internal approval/auto-send rule.
- Define what constitutes a material status change.
- Confirm first-release incident severities/channels/audiences.
- Verify candidate data-source/API/permission feasibility.
- Define handling when next-update time is unknown.
- Define or confirm the security/privacy data boundary for each channel.

The following are analyst mechanisms unless explicitly sourced and must not be presented as required decisions:

- run a workshop;
- create a RACI;
- conduct a two-week spike;
- implement event-driven architecture;
- use async queues;
- create a tiered approval model;
- build a notification microservice;
- use a specific collaboration/status-page vendor.

## 9. Acceptable inferences if labelled

Examples that may be useful if explicitly labelled Inferred/Assumption:

- A communication run/update may need traceability to the source incident and publication time.
- Different internal/external audiences may require different data filtering rules.
- Distribution membership may require an authoritative source to avoid stale recipients.
- A rerun/update mechanism may be needed when incident impact/status changes.

These are not Confirmed requirements unless the answer shows supporting evidence and labels the inference correctly.

## 10. Open questions expected

A strong question set should cover most of:

1. Who owns the decision on internal auto-send versus human confirmation?
2. What conditions make an internal update eligible for distribution?
3. What exactly is a "material status change"?
4. Which incident severities are in the initial release? Is Severity 1-only accepted or just a candidate?
5. Which internal communication channel/audience is in MVP scope?
6. Which fields are mandatory/optional for internal versus external messages?
7. What happens when next-update time is unknown?
8. Which recipient lists/channels are authoritative and how are they maintained?
9. Which ITSM/CMDB/collaboration/status-page capabilities and permissions are actually available?
10. What data is prohibited from each channel and what evidence does Security/Privacy require for sign-off?
11. Is the five-minute expectation a target, and how is it measured when source data is late/incomplete?
12. What measurable success criteria define faster/more consistent communications?
13. How should severity changes affect communication scope or triggers?

## 11. Not established / out of scope

A strong answer should not invent:

- exact vendor/platform names;
- exact API endpoints/payloads/auth protocols;
- a hard eight-week deadline;
- a five-minute SLA;
- an automatic external publishing capability;
- decision owners not named in the evidence;
- retention periods/immutability requirements;
- specific UI designs;
- specific architecture patterns;
- fixed distribution lists;
- fixed communication cadence;
- legal/regulatory requirements not supplied;
- multilingual/customer-segment templates as Phase 1 obligations;
- stories, epics, estimates or implementation plans.

## 12. Readiness for decomposition

Expected overall assessment: **Partially Ready** (or equivalent).

Rationale should mention that the business objective and several security/external-approval boundaries are clear, but meaningful decomposition/acceptance criteria remain blocked or constrained by unresolved internal approval rules, undefined trigger semantics/material change, unsettled first-release scope/channels/recipients and incomplete integration/data-quality feasibility.
