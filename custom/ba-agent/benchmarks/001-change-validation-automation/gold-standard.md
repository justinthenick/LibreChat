# Benchmark 001 — Gold Standard

**Evaluator-only. Do not expose to the model under test.**

This is not the only acceptable wording. Score semantic coverage, evidence handling and discipline rather than exact phrasing.

## 1. Business objective

Improve the reliability and auditability of pre-change validation by automating suitable existing checks, reducing missed/stale evidence and making results easier to review, while retaining the current approval process for the first release.

## 2. Stakeholders / actors identifiable from evidence

- Head of Service Operations — sponsor/business stakeholder.
- Change Manager — governance/change process stakeholder.
- Operations Lead — operational risk stakeholder.
- Platform Engineer — technical feasibility stakeholder.
- Product Owner — product/MVP stakeholder.
- Security Representative — security/identity stakeholder.
- Agile Lead — delivery/decomposition stakeholder.
- Change implementer — primary user running or consuming validation.
- Peer/change reviewer — reviews validation evidence.

Do not invent named teams, approval boards, vendors or specific products beyond the generic systems named in the source.

## 3. Explicit requirements and constraints

A strong response should capture most of these and preserve their evidence status.

| ID | Type | Requirement / constraint | Evidence source |
|---|---|---|---|
| BR-01 | Business | The first release should automate suitable pre-change checks that are already expected in the current process. | A |
| FR-01 | Functional | A user should be able to initiate a validation associated with a change record. | A |
| FR-02 | Functional | The validation result should distinguish at least pass, fail, warning and not-checked outcomes. | A, B |
| FR-03 | Functional | The validation result should be retained/attached to the change record as evidence. | A, B |
| FR-04 | Functional | Stored validation evidence should include the date/time of the validation. | B |
| FR-05 | Functional | The solution should support automated checks against suitable authoritative sources where technically feasible. Candidate sources explicitly mentioned are ITSM/CMDB data, monitoring and the deployment system. | B |
| FR-06 | Functional | The first release must allow checks that cannot be automated to remain manual/not checked automatically. | B |
| C-01 | Constraint | The existing change approval process remains in place for the first release. | A |
| C-02 | Constraint | Phase one is validation only and must not make production configuration changes/remediate failures. | B |
| C-03 | Security | The solution must use approved authentication patterns, avoid a new highly privileged shared account, and follow least privilege. | B |
| NFR-01 | Auditability | Reviewers must be able to determine what validation was performed and when; results need an auditable association with the change. | A, B, C |

## 4. Tentative / proposed scope items — not settled requirements

These should not be presented as firm commitments without qualification.

- Target a useful first release in approximately six weeks. This is a desired delivery target, not proof of feasibility. (A)
- Start with the ten most common change types. The wording is tentative: "should probably". It needs confirmation and a definition of those ten types. (A)
- Aim for validation completing within two minutes. Product Owner calls this the longest users will wait, but the Platform Engineer explicitly says feasibility is unproven. Treat as a candidate performance requirement / open question, not a committed NFR. (B)
- Future remediation/safe-fix capability is a later idea from Operations Lead and explicitly outside phase one. (B)

## 5. Contradictions / unresolved decisions

These are critical to the benchmark. A strong analyst must not silently resolve them.

### D-01 — Does a failed validation block implementation?

- Change Manager: initially advisory; do not automatically stop an approved change until reliability is proven.
- Operations Lead: at least some critical failures should block implementation.
- Current process notes: no consistent treatment and no agreed definition of "critical".

Expected treatment: flag as an unresolved governance/business-rule decision. Do **not** state either "failed checks block changes" or "failed checks never block changes" as settled fact.

### D-02 — Two-minute response target

- Product Owner: two minutes feels like the maximum acceptable wait.
- Platform Engineer: some queries may exceed this; needs testing.

Expected treatment: candidate NFR plus feasibility question.

## 6. Reasonable inferred requirements

These are acceptable only if clearly labelled as inferred and tied back to evidence.

- The system likely needs a mapping between change type and applicable pre-checks, because checklists differ by team/change type and the MVP may target common change types.
- Each individual check likely needs a status/result and enough detail for a reviewer to understand failures/warnings.
- Validation evidence likely needs to be tied to a particular execution/run so copied or stale evidence can be distinguished.
- The solution likely needs controlled read access to each source system it queries.

These are not explicit requirements. A response loses quality if it presents them as confirmed.

## 7. Key open questions

A strong response should raise questions covering most of these themes:

1. Which ten change types are in MVP scope, and who owns the decision?
2. Which pre-checks apply to each selected change type?
3. Which data source is authoritative for each automated check?
4. Which APIs/integration methods are actually available and supported?
5. What outcome should each check produce and what evidence/detail is required?
6. Which failures, if any, are "critical" and who defines/approves that classification?
7. In phase one, can any validation outcome block implementation, or are all outcomes advisory?
8. At exactly what point(s) in the change lifecycle can/should validation be run?
9. Does validation need to be rerun immediately before the implementation window because evidence becomes stale?
10. Is the two-minute target mandatory, aspirational or different by check type?
11. What permissions/service identities are approved for the source systems?
12. What audit retention requirements apply to validation results?
13. What reliability/availability is required before stakeholders would trust automated blocking in a later phase?
14. What constitutes success for the six-week MVP?

## 8. Out of scope / not established

A disciplined response should avoid inventing these:

- automatic remediation in phase one
- replacement of the current approval process
- automatic approval of changes
- automatic rollback
- AI/ML decision-making
- exact technology stack
- exact APIs or vendors not named in the input
- effort estimates or story points
- final user stories/epics in this analysis stage

## 9. Expected analysis quality

The ideal response:

- separates evidence from inference and recommendation;
- preserves disagreement instead of resolving it;
- makes requirements atomic enough to inspect;
- provides traceability to Sources A-D;
- calls out feasibility questions;
- does not prematurely produce user stories or estimates;
- explicitly says what cannot yet be known.
