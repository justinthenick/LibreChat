# Source Pack — Integrated Change Intake and Site Access

Treat the four source sections below as separate supplied project artifacts. They are the complete evidence pack for this benchmark.

## SRC-DOC-01 — Functional Enhancement Specification (Word)

### RFC intake
- The RFC form is initiated in Appian.
- A submitted RFC creates a ServiceNow Change Request and links the Appian request number to the ServiceNow CHG number.
- The Standard Change Catalogue is filtered by the Change Agent's affiliated company.
- Change Agents may be linked to more than one company for the same activity.
- Change Manager and MNP Service Desk roles can view all Standard Change Catalogue entries.
- Activity selection uses a four-tier hierarchy: Change Category, Activity Category, Activity Subcategory and Service L2.

### Date selection
The specification states the following lead-time rules:
- Standard: 3 business days processing + 1 day for Non-Service Affecting / 14 days for Service Affecting.
- Minor: 5 business days processing + 1 day for Non-Service Affecting.
- Significant: 10 business days after the next CAB + 1 day for Non-Service Affecting / 14 days for Service Affecting.
- Major: 10 business days after the next CAB + 14 days for Non-Service Affecting / 1 month for Service Affecting.

### Supporting documents
- MOP upload is mandatory on the RFC form.
- SWMS upload is mandatory on the RFC form.
- Vendor Release Notes are required for Software Update or Software Upgrade activities.

### Site access and keys
- If site access is required, at least one Work Type block is required.
- Visitors selected for a Work Type must be qualified for that Work Type.
- Some Work Types have minimum crew requirements.
- Field 67 asks whether a site key is required.
- Field 68 asks for key type: GRN09, CyberKey or Other.
- Field 69 is the CyberKey serial number. Its validation note reads: "Only appears when Yes is selected for Question 67 is No and CyberKey is selected for Question 68."

### Change lifecycle
- Standard Changes skip manual approval.
- For a change in Implement state, the Planned Start Date is locked; only Planned End Date may be amended, subject to conflict checking.
- If Current Time > Planned End Date and the CR is Scheduled, close as No Show and cancel the linked site access request.
- If Current Time > Planned End Date and the CR is Implement with no Actual End Time, set Actual End Time to Planned End Time, create a NOCC closure task, move the CR to Review, then close after the task is completed.

## SRC-XLS-01 — Service and Activity Catalogue (Excel)

The workbook contains the operational configuration matrix.

### Four-tier taxonomy and routing
Each activity row contains:
- Tier 1 `u_service_category`
- Tier 2 `u_service_subcategory`
- Tier 3 `u_service_l1`
- Tier 4 `u_service_l2`
- default `assignment_group`
- `Standard Change option available?` boolean
- `SAR option available?` boolean
- Change Type
- permitted PSN impact values: NSA / SA / RA
- initial risk level
- `MOP Required?` boolean
- `SWMS Required?` boolean
- `Release Notes Required?` boolean

Example rows:
- Maintenance / Air Conditioning / Inspection -> assignment group Facilities; Standard Change = true; SAR = true; Change Type = Minor; NSA lead time = 6 days; MOP Required = false; SWMS Required = true; Release Notes Required = false.
- Security / Software / Windows Patching -> assignment group ICT Software; Standard Change = true; SAR = false; Change Type = Standard; NSA lead time = 4 days; MOP Required = false; SWMS Required = false; Release Notes Required = true.
- Core / Motorola / Upgrade -> assignment group Core Support; Standard Change = false; SAR = false; Change Type = Significant; lead time = `25 + number of days to next CAB after submission`; MOP Required = true; SWMS Required = false; Release Notes Required = true.
- CCEP / New Site / Integration -> assignment group Construction; Standard Change = false; SAR = true; Change Type = Major; lead time = `54 + number of days to next CAB after submission`; MOP Required = true; SWMS Required = true; Release Notes Required = false.

### Change classification and approval matrix
- Minor -> Change Manager approval.
- Significant -> CAB approval.
- Major -> CAB + TAEC approval.

No rule in the workbook says which source takes precedence when its lead-time values or document flags differ from the Word specification.

## SRC-MAP-01 — Post-ServiceNow Review Process Map (PDF)

The process map is marked WIP / draft in several places.

### Standard Change path
- Process Map v1/v2 shows: New -> Assess -> Authorise -> Scheduled for Standard Changes, with automatic progression.
- An overall process-map annotation for "Site inspection only" shows a Standard Change going directly from New -> Scheduled.

### Assignment routing
- If an assignment group mapping exists, apply the mapped group.
- If no assignment group mapping exists, allocate through PSN Helpdesk.

### Unresolved annotations
The map includes these annotations exactly as unresolved design questions:
1. "For user/org that has been flagged for poor performance or bad change practice. Can they proceed with change creation."
2. "Post site visit tasks – Quota? 10% action – 90% Auto close? SLAs to be defined."
3. "Question – SNOW, Appian or other? Change task trigger a change approval."
4. "If minor change to change (such as date changes) move to Authorize (Or new state… such as 'Amend'.) TBD."

No answers to those four annotations are supplied elsewhere in this source pack.

## SRC-PPT-01 — Internal Change Transformation Presentation (PowerPoint)

The presentation describes the intended business outcomes and current pain points:
- Current Service Desk swivel-chair creation introduces additional handling and extensive processing time.
- Target state creates the change directly from Appian input.
- The target is to reduce processing time and double handling.
- Improved change-scope choices and structure are intended to improve classification and allocation of work.
- The current process uses a one-size-fits-all risk assessment; the target introduces improved base risk and more applicable risk-assessment tables.
- First site visit is intended to trigger the move to Implement for changes needing site attendance.
- Final site visit is intended to create a post-implementation task for NOCC and populate Actual End Date.

The presentation does not define security, performance, availability, retry, logging, audit, API, database or integration-error requirements.
