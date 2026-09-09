# Benchmark 043 gold standard — evaluator only

This file is evaluator-only and must never be included in the generation prompt.

## Purpose

Held-out generalisation gate for Requirements Lifecycle Skill v0.2.4. The benchmark tests whether the skill's B042 fixes transfer to a different business domain and evidence shape.

## Required source use

A passing answer must materially use all four sources.

### G1 — Structured operational controls must become requirements/rules
From SRC-XLS-01, the answer must operationalise rather than merely mention:
- three-tier taxonomy and explicit mappings to `u_work_domain`, `u_job_family`, `u_job_type`;
- default routing through `assignment_queue`;
- `Permit option available?` activity availability;
- `Remote Review available?` activity availability;
- `Evidence Required?` activity-specific evidence rule;
- `Risk Band` initial risk classification.

### G2 — Multi-region affiliation must remain an unknown handling outcome
SRC-DOC-01 establishes:
- catalogue filtered by affiliated service region;
- a contractor may have more than one service region.

It does NOT establish union, intersection, primary region, prompt-to-select, display-all, precedence, fallback or any other multi-region handling policy.

Correct treatment: preserve the multi-region condition and state that the required handling outcome is Unknown / not established. Do not enumerate candidate solutions as requirements or acceptance criteria.

### G3 — Business labels and technical field names are mappings, not conflicts
SRC-XLS-01 explicitly maps:
- Work Domain -> `u_work_domain`
- Job Family -> `u_job_family`
- Job Type -> `u_job_type`

A passing answer must not create a contradiction, ambiguity, source-precedence item or naming Decision Item from these paired names.

### G4 — Target events remain at target abstraction
SRC-PPT-01 establishes two target outcomes:
- first approved permit entry recorded at gate -> Permit moves to `In Progress`;
- final crew exit recorded -> completion-review task created.

A passing answer may preserve these as Target/Candidate requirements. It must NOT create questions, Decision Items, requirements or blockers about how gate/exit events are detected, transported, integrated, reconciled, polled, scanned, exposed through APIs or otherwise implemented. The source explicitly says those technical mechanisms are not stated; that absence does not itself create scope.

### G5 — Explicit document-rule contradiction must remain disputed
SRC-DOC-01 says supporting evidence upload is mandatory for every permit request.
SRC-XLS-01 says `Evidence Required?` varies by activity and is No for some rows.
A passing answer must preserve this as one disputed rule/decision dimension and must not execute either side as confirmed acceptance criteria until resolved.

### G6 — Exact unresolved-cardinality discipline
SRC-MAP-01 contains exactly one explicit unresolved annotation:
- out-of-hours permits: can duty supervisor self-approve instead of normal review?

Apart from the independently sourced multi-region ambiguity and document-rule contradiction, no extra engineering Decision Items/open questions should be invented.

## Confirmed source-backed behaviours

Expected confirmed/usable source atoms include:
- Portal initiation;
- submitted request creates WorkHub Permit and links request/PER numbers;
- single-region catalogue filtering rule at the abstraction stated;
- Change? no: permit activity three-tier taxonomy and mappings;
- mapped assignment queue routing;
- Permit availability flag;
- Remote Review availability flag;
- Risk Band initial classification;
- site-attendance crew required;
- crew competency must match selected Job Type;
- draft lifecycle New -> Review -> Approved -> Scheduled;
- two PPT target outcomes preserved as Target/Candidate, not implementation-ready mechanisms.

## Prohibited negative-space additions

Automatic source-closure defects include unsourced requirements/questions about:
- APIs, webhooks, scanners, polling, integration transport, event reconciliation;
- permission models or role matrices beyond the explicit duty-supervisor annotation;
- invalid/missing/duplicate records;
- retries, errors, audit/logging, performance, availability;
- generic governance or decision owners;
- invented benefits;
- technical data-model design beyond explicit field mappings.

## Readiness

A passing answer should distinguish:
- confirmed implementation-ready behaviours;
- the multi-region handling unknown;
- the disputed universal-vs-matrix evidence rule;
- the one out-of-hours self-approval WIP question;
- target-state gate/exit outcomes retained as Target/Candidate without invented implementation blockers.