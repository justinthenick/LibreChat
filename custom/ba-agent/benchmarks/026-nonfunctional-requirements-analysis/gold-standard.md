# Benchmark 026 Gold Standard — Evaluator Only

## Expected overall readiness

`Partially Ready` for solution design. Several important NFRs/constraints are established, but performance thresholds, recovery objectives, accessibility commitment and some security details remain unresolved or non-binding.

## Expected NFR classifications

### Confirmed

- **NFR-DATA-01 — Data residency:** customer personal data must be stored in Australia. Evidence Explicit; Status Confirmed; source Legal decision L-22.
- **NFR-SUP-01 — Support window:** support coverage 07:00-19:00 Australia/Sydney on business days. Evidence Explicit; Status Confirmed; source service-desk process note.
- **NFR-CONT-01 — Manual fallback:** existing email intake remains available when automated intake is unavailable. Evidence Explicit; Status Confirmed.
- **NFR-SUP-02 — Support identifiability outcome:** support must be able to identify the affected claim using the existing case reference when a customer reports a failed submission. Evidence Explicit; Status Confirmed. No logging/tracing/database/monitoring mechanism is established.

### Targets / qualitative goals

- **Performance:** pages should `feel fast`; no response-time threshold is established. This may be a qualitative Target/Candidate quality goal, not a measurable SLA.
- **Availability:** 99.9% during normal business hours is a Target / planning aim only; no SLA/SLO is approved.
- **Recovery:** `same-day recovery would probably be okay` is at most Proposed/Candidate or Target; RTO and RPO remain Unknown.

### Estimate / assumption, not committed requirement

- approximately 2,000 concurrent users at month-end is a planning estimate. It may inform capacity analysis, but must not be converted into a committed capacity minimum unless explicitly promoted later.

### Candidate / unconfirmed

- encryption at rest for export files is Proposed/Candidate pending policy confirmation. No algorithm, key-management mechanism or platform is established.
- WCAG 2.2 AA is Proposed/Candidate because the design lead recommends it but steering has not accepted it as committed scope.

### Unknown / unassessed

- exact response-time threshold;
- committed availability/SLA status;
- RTO;
- RPO;
- data retention;
- backup frequency;
- geographic redundancy;
- autoscaling approach/capacity commitment;
- browser matrix;
- mobile-app requirements;
- penetration-test cadence;
- certifications;
- encryption mechanism;
- monitoring technology.

These may be raised as questions or unassessed areas; they must not be turned into requirements.

## Expected solution-design handoff

Solution design may rely on:

- Australian data-residency constraint;
- support window;
- manual fallback outcome;
- support identifiability outcome.

It must preserve as non-binding:

- 99.9% availability Target;
- 2,000 concurrency planning estimate;
- WCAG 2.2 AA Candidate;
- encryption-at-rest Candidate;
- qualitative `feel fast` goal;
- same-day recovery discussion / Unknown RTO/RPO.

## Critical defects

- inventing a response-time number;
- turning 99.9% into an SLA/SLO/mandatory requirement;
- turning 2,000 concurrent users into a hard capacity minimum;
- making WCAG 2.2 AA mandatory;
- making encryption-at-rest mandatory or naming an encryption method;
- inventing RTO/RPO values;
- inventing active-active, autoscaling, backup, redundancy, monitoring/logging/observability technology;
- asserting regulatory/certification obligations not in the packet.