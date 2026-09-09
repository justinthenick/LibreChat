# Benchmark 043 input — Contractor Permit Routing

Use only the evidence below. Treat each source as authoritative only for what it actually states.

## SRC-DOC-01 — Contractor Permit Enhancement Note

The contractor permit request is initiated in the Field Access Portal. After submission, a Permit record is created in WorkHub and the Portal request number is linked to the WorkHub PER number.

The permit catalogue is filtered by the contractor's affiliated service region. A contractor may be affiliated with more than one service region.

Permit activities are selected through the following business hierarchy:
- Work Domain
- Job Family
- Job Type

Supporting evidence upload is mandatory for every permit request.

For permits requiring site attendance, a named crew must be supplied. Crew members selected for a permit must hold the competency required by the selected Job Type.

## SRC-XLS-01 — Permit Activity Matrix

The operational activity matrix contains these columns:

| Work Domain | Job Family | Job Type | `u_work_domain` | `u_job_family` | `u_job_type` | `assignment_queue` | Permit option available? | Remote Review available? | Evidence Required? | Risk Band |
|---|---|---|---|---|---|---|---|---|---|---|
| Radio | Antenna | Visual Inspection | RADIO | ANT | VIS | FIELD-ACCESS | Yes | Yes | No | Low |
| Radio | Antenna | Hardware Swap | RADIO | ANT | HSW | RADIO-OPS | Yes | No | Yes | Medium |
| Power | Battery | Capacity Test | POWER | BATT | CAP | POWER-OPS | Yes | Yes | No | Low |
| Power | Battery | Replacement | POWER | BATT | REP | POWER-OPS | Yes | No | Yes | High |
| Civil | Structure | Major Repair | CIVIL | STR | REPAIR | CIVIL-WORKS | No | No | Yes | High |

The workbook notes:
- `assignment_queue` is the default routing destination for the selected activity.
- `Permit option available?` controls whether that activity is available for permit creation.
- `Remote Review available?` controls whether remote review is available for that activity.
- `Evidence Required?` controls whether supporting evidence is required for that activity.
- `Risk Band` supplies the initial activity risk classification.
- Work Domain maps to `u_work_domain`; Job Family maps to `u_job_family`; Job Type maps to `u_job_type`.

## SRC-MAP-01 — Permit Lifecycle Draft

Confirmed draft flow:

`New -> Review -> Approved -> Scheduled`

Routing note:
- On creation, route the Permit to the selected activity's `assignment_queue`.

One unresolved annotation is present:

> For out-of-hours permits, can the duty supervisor self-approve instead of waiting for normal review? TBD.

No other unresolved annotations are shown.

## SRC-PPT-01 — Field Access Target-State Concept

Target concepts:
- When the first approved permit entry is recorded at the site gate, move the Permit to `In Progress`.
- When the final crew exit is recorded, create the completion-review task.

The presentation does not state how gate entry or crew exit events are technically detected, transported, reconciled, or implemented.

## User request

Prepare a full requirements lifecycle package: analysis, decomposition and acceptance criteria. Preserve source status, contradictions, unknowns and traceability. Do not make design recommendations or fill gaps with common practice.