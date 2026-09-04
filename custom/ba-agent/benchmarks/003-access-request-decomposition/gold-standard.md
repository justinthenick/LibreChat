# Benchmark 003 — Gold Standard

**Evaluator-only. Do not expose this file to the model under test.**

This benchmark evaluates **delivery decomposition discipline**, not requirements elicitation. The input already contains an upstream requirements analysis with IDs and statuses.

A strong answer may use different item names or grouping, but it must preserve the distinctions below.

## 1. Expected readiness assessment

Expected overall assessment: **Partially Ready**.

The model should recognize that meaningful decomposition can proceed for the confirmed standard-access path while several items remain blocked/conditional:

- REQ-004 privileged-access approval rule — Disputed;
- REQ-006 automated provisioning — Candidate and technically unverified;
- REQ-009 candidate pilot applications — Candidate, not approved;
- REQ-011 retention period — Unknown.

A strong answer should **not stop decomposition entirely** merely because some items are unresolved.

## 2. Expected requirement-status preservation

The model should preserve:

### Confirmed
- REQ-001 request application + role;
- REQ-002 requester/application/role/business justification data;
- REQ-003 Line Manager approval for standard access;
- REQ-005 manual fulfillment fallback;
- REQ-007 audit outcomes/timestamps;
- REQ-012 approved authentication / least privilege / no highly privileged shared account;
- REQ-013 no HR joiner/mover/leaver redesign.

### Disputed
- REQ-004 privileged-access approval rule.

### Candidate
- REQ-006 automated provisioning where technically supported;
- REQ-009 CRM / Reporting Portal / Dev Wiki pilot scope.

### Target
- REQ-008 four-business-hour desired completion target.

### Deferred
- REQ-010 automatic removal on role change/exit.

### Unknown
- REQ-011 retention period.

No status should be silently promoted.

## 3. Expected decomposition pattern

A strong answer should produce a mix of work item types rather than forcing everything into user stories.

### Likely Epic / Capability groupings

Acceptable groupings include variants of:

- Access Request & Standard Approval;
- Fulfillment & Audit;
- Integration / Automation Enablement.

Do not require these exact names or count.

Avoid horizontal architecture epics such as Frontend / Backend / Database unless directly evidenced.

## 4. Expected current delivery items

Strong answers should include most of the following concepts, with traceability.

### User-visible / workflow behavior

- Employee can submit an access request with application and role (REQ-001).
- Request captures requester/application/role/business justification (REQ-002), either combined with the submission story or as a closely related data requirement.
- Line Manager can review/approve or reject standard access before fulfillment (REQ-003). The exact UI/notification mechanism is not established.
- Approved access can proceed via a manual fulfillment path when automation is unavailable (REQ-005). This may be a story or operational/enabler item depending on wording.

### Enabler / Technical / Security work

- Preserve audit outcomes and associated date/time information on the request record (REQ-007).
- Apply approved authentication / least privilege and avoid a new highly privileged shared account for integrations (REQ-012).
- Preserve the boundary that HR joiner/mover/leaver redesign is outside this initiative (REQ-013), typically as a constraint/dependency rather than a story.

The model should not invent request-status screens, notifications, email reminders, escalation rules, delegation, access catalogs, UI controls or specific provisioning technologies.

## 5. Critical Decision Item

### Privileged-access approval — REQ-004

This is the main business-rule trap.

Expected treatment:

- Type: **Decision Item** (or clearly equivalent unresolved decision).
- Required decision: whether all privileged roles require Security approval or only production-administration roles require the additional Security approval.
- Decision owner: **Unknown**.
- Any privileged-access implementation stories should be Blocked / Conditional, not Ready.

Incorrect treatment:

- selecting either stakeholder position;
- inventing a compromise rule;
- writing a committed user story that assumes one approval flow.

## 6. Critical Spike / Discovery Item

### Automated provisioning feasibility — REQ-006

Expected treatment:

- Type: **Spike / Discovery Item**.
- Question: which applications can be provisioned through the existing identity platform, and what supported integration capability exists?
- Evidence/output: verified capability/constraints per candidate application (or equivalent).
- Downstream automated-provisioning work remains Candidate / Conditional until feasibility is proven.

The model must not invent a vendor, API endpoint, REST/GraphQL protocol, webhook, queue, microservice or architecture.

## 7. Candidate scope handling

### REQ-009 pilot applications

CRM, Reporting Portal and Dev Wiki are **Candidate** pilot scope only.

Expected treatment:

- separate Candidate backlog / conditional scope section;
- may be referenced by the integration spike;
- must not create three committed application implementation stories as though the pilot is approved.

## 8. Target handling

### REQ-008 four business hours

Expected treatment:

- planning / quality target;
- traceable to REQ-008;
- not rewritten as a hard SLA or mandatory acceptance criterion.

The benchmark is specifically looking for preservation of target strength.

## 9. Deferred handling

### REQ-010 automatic deprovisioning

Expected treatment:

- Deferred / future backlog;
- no current implementation story or task.

## 10. Unknown retention handling

### REQ-011 retention period

Expected treatment:

- explicit dependency / open decision / unknown;
- not a guessed retention period;
- no invented legal/regulatory duration.

A strong answer may note that detailed audit-storage acceptance criteria cannot be finalized until retention is established.

## 11. Upstream analyst proposal

The staged pilot mechanism is explicitly **Proposed**, not agreed.

A strong answer may repeat it under Analyst/Delivery proposals, but must not present it as required sequencing or committed release design.

## 12. Traceability expectations

Every story/task/spike/decision/deferred item should trace to one or more REQ IDs.

Traceability should make it possible to determine:

- which requirements have current delivery coverage;
- which requirements are represented by decisions/spikes/candidate/deferred work;
- whether any requirement has been silently dropped.

## 13. Acceptance-criteria discipline

This benchmark is **not** testing detailed acceptance criteria.

Acceptable:

- short evidence-based acceptance anchors such as `request includes application and requested role`.

Incorrect:

- extensive Given/When/Then invented behavior;
- invented UI validations, error messages, notification rules, timeouts or system states.

Expected readiness for acceptance-criteria elaboration: **Partially Ready**. Confirmed standard-access stories may be elaborated later; privileged and integration-dependent items remain blocked/conditional.

## 14. Estimates and sequencing

Do not invent:

- story points;
- T-shirt sizes;
- hours/days/weeks;
- sprint assignments;
- delivery dates;
- team capacity;
- implementation order presented as mandatory unless directly evidenced.

## 15. Serious failure modes

The following should be treated as material failures:

- privileged-access disagreement silently resolved;
- candidate automated provisioning treated as confirmed build work;
- candidate pilot applications treated as committed scope;
- four-hour target converted into SLA/mandatory acceptance criterion;
- deferred deprovisioning pulled into current backlog;
- retention period invented;
- specific vendor/API/architecture invented;
- every requirement forced into a user story;
- missing traceability;
- estimates created despite instruction.
