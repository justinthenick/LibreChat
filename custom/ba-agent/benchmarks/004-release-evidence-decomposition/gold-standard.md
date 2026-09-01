# Benchmark 004 — Gold Standard

**Evaluator-only. Do not expose this file to the model under test.**

This benchmark evaluates whether `decompose-requirements` generalizes beyond access-request workflow decomposition into software-release evidence and Change Enablement boundaries.

## Expected readiness

Overall: **Partially Ready**.

Proceed with decomposition of the confirmed evidence/manual path while keeping the following visibly unresolved or conditional:

- REQ-004 failed-validation response — Disputed;
- REQ-006 automated evidence import — Candidate and technically unverified;
- REQ-008 pilot services — Candidate, not approved;
- REQ-010 evidence retention period — Unknown.

## Status preservation

### Confirmed
- REQ-001 evidence record with change ID, service/application, release version, target environment;
- REQ-002 pre/deployment/post validation outcomes and associated date/time;
- REQ-003 approved change reference before production is treated ready to execute;
- REQ-005 manual evidence entry/attachment fallback;
- REQ-011 approved service identities / least privilege / no shared admin account;
- REQ-012 do not redesign CAB/change approval or alter approval authorities;
- REQ-013 imported evidence retains source reference and imported outcome.

### Disputed
- REQ-004 failed post-deployment validation response.

### Candidate
- REQ-006 automated import from existing deployment platform;
- REQ-008 Billing API / Customer Portal pilot scope.

### Target
- REQ-007 evidence pack complete within 15 minutes.

### Deferred
- REQ-009 predictive deployment-risk scoring.

### Unknown
- REQ-010 retention period.

## Expected decomposition pattern

Acceptable capabilities include variants of:

- Deployment Evidence Capture & Validation;
- Manual Evidence & Audit Traceability;
- Evidence Import Enablement.

Do not require these exact names.

Likely current work:

- user-visible work for creating a deployment-evidence record with the supported fields (REQ-001);
- evidence capture for pre/deployment/post outcomes and timestamps (REQ-002), either story or technical/audit work depending wording;
- production readiness linkage to an approved change record (REQ-003) without inventing CAB screens, API gates or notifications;
- manual evidence entry/attachment fallback (REQ-005);
- security integration constraint as an Enabler/Technical Task (REQ-011);
- Change Enablement process boundary as Constraint/Dependency rather than a story (REQ-012);
- source-reference/imported-outcome preservation as audit/traceability work (REQ-013).

## Critical Decision Item — REQ-004

Expected:

- Type: Decision Item or clearly equivalent;
- preserve both positions:
  - Service Reliability Lead: automatic rollback;
  - Application Owner: pause and human decides rollback/continue;
- Decision owner: **Unknown**;
- failed-validation implementation remains Blocked/Conditional.

Incorrect:

- select either side;
- invent a compromise such as automatic rollback only in production;
- invent an approval board or escalation authority;
- create a ready rollback workflow/story.

## Critical Spike — REQ-006

Expected:

- Spike/Discovery Item;
- question: what integration capability/authentication/support exists in the current deployment platform and for which services;
- downstream evidence-import work remains Candidate/Conditional;
- no vendor, REST/webhook protocol, queue, agent, database or pipeline technology is invented.

## Candidate scope — REQ-008

Billing API and Customer Portal remain Candidate only.

They may be referenced by discovery, but must not become committed service-specific implementation stories.

## Target — REQ-007

The fifteen-minute objective remains a planning/quality target, not a hard SLA or acceptance commitment.

## Deferred — REQ-009

Predictive deployment-risk scoring remains future/deferred and outside the current backlog.

## Unknown — REQ-010

Retention period remains Unknown/open. No duration, regulation or owner is guessed.

## Process-boundary discipline — REQ-012

Do not turn the initiative into CAB/change-process redesign. No new approval authority, board, governance role or approval workflow should be invented.

## Upstream analyst proposal

The staged/proven-feasible-services mechanism is Proposed only. It may be noted as a proposal, but not presented as mandatory sequence or settled product design.

## Traceability

Every material item should trace to REQ IDs. A strong traceability summary accounts for all 13 requirements and distinguishes current, blocked, candidate, target, deferred and unknown items.

## Acceptance-criteria discipline

Short source-backed anchors are acceptable. Do not invent detailed UI, notifications, validation messages, pipeline states, rollback triggers, storage mechanisms or error behavior.

Expected acceptance-criteria readiness: **Partially Ready**. Confirmed evidence/manual items may progress; failed-validation behavior and automated import remain blocked/conditional.

## Estimates and sequencing

Do not create points, sizes, durations, sprint assignments, dates or mandatory sequence not established upstream.
