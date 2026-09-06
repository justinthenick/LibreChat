# Benchmark 038 Input — External Auditor Access Requirement Change

A production IAM onboarding baseline exists. Later evidence introduces one approved new outcome plus several unresolved details and unrelated suggestions. The user wants the delta reconciled, the new requirement analyzed for ambiguity, and change impact assessed before downstream refinement.

## Current baseline — version 7

| ID | Requirement | Status | Source |
|---|---|---|---|
| IAM-10 | Employees receive standard application access within one business day of an approved onboarding request. | Confirmed | IAM decision D-70 |
| IAM-11 | MFA is required for all interactive application access. | Confirmed | Security policy SP-14 |
| IAM-12 | External contractors are out of scope for the current onboarding workflow. | Confirmed | Scope decision D-71 |
| IAM-13 | Temporary privileged access expires after 90 days unless explicitly renewed. | Confirmed | Security decision D-72 |

The existing change-impact assessment predates any external-auditor access capability and does not cover that actor, request path or support burden.

## Later evidence

### Security decision SD-77 — 6 September

Status: Approved.

Decision: add support for **external auditors** who need time-limited application access during approved audit activity. The approved outcome says access must be "available within 15 minutes of an approved audit request" and must be time-limited.

The packet does **not** define:

- what event starts the 15-minute timer;
- the default or maximum access duration;
- who has authority to approve an audit request;
- whether auditors use an existing identity source or a separate guest identity path;
- renewal/extension rules;
- whether auditor access may ever include privileged roles.

SD-77 does not state that contractor scope changes.

### Operations meeting notes

- Service desk lead: "If auditors are temporary, maybe we should make all temporary access expire after 30 days."
- Security architect: "That needs a separate decision; leave IAM-13 alone for now."
- IAM-11 MFA is not discussed.

### Audit programme note

The programme manager will coordinate audit dates and supply the list of visiting auditors. The note does not establish that the programme manager is the authority who approves access.

## Request

1. Reconcile the baseline with the later evidence.
2. Analyze the approved auditor-access requirement enough to expose unresolved semantics and decisions without inventing them.
3. Assess the change impact of adding the auditor actor/capability because the existing impact assessment does not cover it.

Do **not** decompose the requirement or generate acceptance criteria/test cases yet; those should wait until the material semantic Unknowns are resolved. Preserve IAM-11, IAM-12 and IAM-13 unless explicit evidence changes them.
