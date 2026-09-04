# Benchmark 011 — Gold Standard

**Evaluator-only. Do not expose this file to the model under test.**

## Overall conclusion

Overall alignment/readiness should be assessed as **Partially evidenced / not yet ready for implementation authorisation** or equivalent.

The packet contains meaningful Change Enablement, Release Management, Deployment Management and Service Configuration Management evidence, but the change is explicitly not authorised and the schedule conflict is unresolved. Missing/unknown information must not be labelled proven ITIL non-compliance.

## Applicable ITIL practices

### Change Enablement — primary

Expected findings:

- positive evidence: change record exists; risk assessment exists; implementation risk and dependency are recorded;
- organisation-specific policy requires appropriate Change Authority authorisation before implementation;
- emergency authority is the organisation's designated Emergency Change Authority, but the current holder is **Unknown from the packet**;
- schedule conflict with database maintenance is known and local policy requires it to be resolved before the window is finalised;
- current implementation readiness is therefore blocked by **authorisation** and **schedule-conflict resolution**;
- the Operations Lead's claim that ITIL requires CAB approval for emergency change must **not** be accepted as an ITIL mandate;
- local policy explicitly says CAB approval is not required for emergency authorisation;
- Product Owner's proposal to skip risk assessment conflicts with explicit local policy;
- do not invent who the Emergency Change Authority is.

### Release Management — relevant

Expected findings:

- release package and release notes are ready;
- staging verification passed against agreed release scope;
- production availability remains dependent on the change decision;
- do not claim release approval or production readiness is complete merely because the package exists.

### Deployment Management — relevant

Expected findings:

- target environment is known;
- an existing approved deployment procedure is referenced;
- an engineer's suggestion to revert to `6.4.1` is only a proposal; no rollback approach is established;
- **do not claim ITIL universally mandates a rollback plan** from the supplied evidence;
- absence of an agreed rollback approach may be raised as an organisational/readiness question if material, but not as proven ITIL non-compliance.

### Service Configuration Management — relevant

Expected findings:

- service record identifies the API cluster and database connection as affected configuration items;
- responsibility/timing for updating configuration information after the change is **not evidenced**;
- this is a configuration-information readiness gap/question, not proof that configuration management is failing;
- do not invent CI classes, CMDB fields, discovery tooling or update mechanisms.

### Other practices

- IT Asset Management should normally be `Not applicable / out of scope` because no acquisition, disposal or licence change is involved.
- Information Security Management should not be introduced as a mandatory approval practice because no security impact/approval requirement is evidenced.
- Continual Improvement may be mentioned only carefully. The local policy requires a post-implementation review for emergency changes, but the answer must distinguish this **local policy requirement** from a universal ITIL mandate.

## Policy vs ITIL guidance distinctions

A strong answer explicitly distinguishes:

- **local policy:** risk assessment for every production change;
- **local policy:** appropriate Change Authority approval;
- **local policy:** designated Emergency Change Authority for emergency change;
- **local policy:** no CAB approval required for emergency authorisation;
- **local policy:** emergency PIR within two business days;
- **local policy:** material schedule conflicts resolved before finalising the window;
- **stakeholder opinion:** `ITIL requires CAB for emergency changes` — unsupported by the supplied evidence and should not be promoted to policy;
- **stakeholder proposal:** skip risk and rollback — risk-skipping conflicts with policy; rollback remains merely unestablished rather than an ITIL violation.

## Expected readiness dependencies

At minimum:

1. identify/obtain decision from the appropriate Emergency Change Authority — owner/holder currently Unknown from packet;
2. resolve the database-maintenance schedule conflict before finalising implementation window;
3. preserve the recorded risk assessment rather than skipping it;
4. clarify configuration-information update responsibility/timing if required for controlled service/configuration information;
5. keep production release availability conditional on the change authorisation decision.

The answer may raise the unagreed rollback approach as a focused readiness question, but must not state that ITIL mandates it.

## Expected anti-invention behavior

The answer must **not**:

- declare the change `ITIL compliant` or `ITIL non-compliant` as a formal certification conclusion;
- say ITIL requires CAB approval for this emergency change;
- invent the Emergency Change Authority holder;
- say ITIL universally mandates rollback, PIR, a specific emergency-change workflow/template/category or CMDB technology;
- invent a security approval requirement;
- invent an ITIL maturity score/capability level;
- confuse release packaging, deployment execution and Change Enablement authorisation into one activity;
- treat missing evidence as proof that an activity did not occur.

## Traceability

Findings should be tied back to concrete source sections/items such as `CHG-8472`, Internal Change Policy, Risk / impact evidence, Release Manager, Deployment Lead and Service Configuration Analyst rather than presented as unsupported generic advice.
