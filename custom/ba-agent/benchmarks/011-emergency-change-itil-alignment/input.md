# Benchmark 011 — Emergency Payment Change ITIL Alignment

## Scenario

A delivery team is preparing an urgent production change for the **Payments API** before a forecast overnight transaction peak. The packet below mixes formal policy, change evidence and stakeholder opinions.

### Change record

- Change ID: `CHG-8472`
- Service: Payments API
- Release version: `6.4.2`
- Target environment: Production
- Proposed implementation window: 21:30–22:30 tonight
- Change classification: **Emergency proposed — not yet authorised**
- Business reason: recent timeout rates have increased and the team wants the fix in place before the overnight peak.

### Risk / impact evidence

A short risk review records:

- customer impact if the issue continues: High;
- implementation risk: High;
- known dependency: production database connectivity;
- known schedule conflict: a separate database maintenance activity is currently planned for 22:00;
- final handling of the schedule conflict: not decided.

No source in this packet shows that the implementation risk has been formally accepted or that the change has been authorised.

### Internal Change Policy excerpt

The organisation's current approved Change Policy states:

1. every production change must have a change record and recorded risk assessment;
2. a production change must be authorised by the appropriate Change Authority before implementation;
3. emergency changes are authorised by the designated **Emergency Change Authority**;
4. this packet does **not** identify who currently holds the Emergency Change Authority for the Payments API;
5. the normal CAB reviews high-risk normal changes, but CAB approval is **not required by this policy for emergency-change authorisation**;
6. emergency changes require a post-implementation review within two business days;
7. material schedule conflicts must be resolved before the implementation window is finalised.

### Stakeholder comments

**Operations Lead**

> ITIL says the CAB has to approve an emergency change, so we cannot proceed until CAB meets.

**Product Owner**

> If we are calling this emergency, I would skip the formal risk step and the rollback plan so we can move faster.

**Change Manager**

> The risk assessment is required by our policy even for emergency work. We also need the correct Emergency Change Authority and the schedule conflict resolved. I do not know from this packet who the authority holder is.

**Release Manager**

> The 6.4.2 release package and release notes are ready. Staging verification passed against the agreed release scope. Production availability still depends on the change decision.

**Deployment Lead**

> The existing approved deployment procedure for the Payments API is referenced by CHG-8472 and the production target is known. An engineer suggested reverting to 6.4.1 if needed, but no rollback approach has been agreed in this packet.

**Service Configuration Analyst**

> The Payments API service record currently identifies the API cluster and database connection as affected configuration items. We have not established from this packet who will update configuration information after the change or when that update should occur.

### Additional boundaries

- No new hardware/software asset acquisition, disposal or licence change is involved.
- No security-impacting change has been identified in the supplied evidence and no security approval requirement is stated.
- No source says that ITIL itself requires a CAB, rollback plan, post-implementation review, specific change template, specific change category, or particular CMDB tooling.
- No official ITIL maturity-model assessment criteria are included in this packet.
- The change is **not yet authorised**.
