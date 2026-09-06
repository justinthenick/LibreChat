# Incident / Problem Engineering Lab

## Objective

Extend the existing evidence/authority discipline into operational incident and problem analysis without confusing chronology, correlation, hypothesis, cause, ownership or corrective action.

This track is **planned, not yet active**. Do not queue model runs until the current workflow-strengthening standalone benchmarks establish their first results and available provider capacity is known.

## Proposed Skill sequence

### I001 — `reconstruct-incident-timeline`

Purpose: merge logs, chat, tickets, monitoring events and human statements into a single timestamped chronology while distinguishing observed timestamps, reported timestamps, approximate times and ordering uncertainty.

Critical controls:

- do not invent event times;
- do not reorder ambiguous events as certain;
- distinguish event occurrence from when it was noticed/reported;
- preserve source references and clock/timezone uncertainty.

### I002 — `analyze-causal-evidence`

Purpose: analyze candidate causal relationships from the reconstructed timeline and technical evidence.

Critical controls:

- correlation is not causation;
- temporal precedence alone does not prove cause;
- distinguish `Observed contributor`, `Supported causal factor`, `Hypothesis`, `Disputed`, and `Unknown`;
- do not infer root cause from the team/person that made the last change;
- do not invent mechanisms that are not evidenced by logs/tests/configuration.

### I003 — `prepare-problem-record`

Purpose: convert established incident/causal evidence into a Problem Management handoff with known errors, hypotheses, workarounds, unresolved evidence and problem scope.

Critical controls:

- problem record does not claim a root cause stronger than causal evidence;
- workaround is not a permanent fix;
- incident resolver is not automatically Problem Owner;
- missing evidence becomes an investigation question, not invented root cause.

### I004 — `assess-corrective-actions`

Purpose: assess proposed corrective/preventive actions against supported causal factors and verify coverage without claiming an action prevents recurrence when the causal chain is uncertain.

Critical controls:

- action must trace to a supported factor/risk;
- distinguish containment, workaround, corrective action, preventive action and observation;
- do not invent owners/dates/implementation designs;
- avoid generic action lists unrelated to the incident evidence.

## Planned Agent

### A005 — Incident / Problem Orchestrator

Only after I001-I004 have standalone evidence.

Expected route:

incident evidence -> timeline reconstruction -> causal-evidence analysis -> problem record -> corrective-action assessment.

The Agent must stop when evidence is insufficient rather than force a `root cause` conclusion.

## Benchmark sequence

Use at least three materially different domains before Agent composition:

1. application release / configuration incident;
2. network/connectivity incident;
3. third-party/vendor/dependency incident.

Each synthetic packet should contain deliberate timestamp ambiguity, misleading correlation, uncertain ownership and at least one plausible but unsupported causal story so hallucination penalties are meaningful.