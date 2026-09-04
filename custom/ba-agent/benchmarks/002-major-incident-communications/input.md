# Benchmark 002 — Major Incident Communications Automation

**Status:** Synthetic benchmark input. The analyst should treat this as the complete available source pack.

---

## Source A — Stakeholder email

**From:** Head of Service Reliability  
**Subject:** Major incident updates

During major incidents we spend too much time chasing status and rewriting updates for different audiences. Internal leaders often hear about an outage late, and Service Desk agents sometimes work from an old update while the incident bridge has already moved on.

I want us to look at generating incident communications from the incident record so teams are not repeatedly copying the same facts into email and chat. Ideally we could publish one clear update that shows the affected service, customer impact, current status and when people should expect the next update.

I would like something useful before the peak trading period in about eight weeks. Maybe we start with Severity 1 incidents only rather than every incident and every communication channel.

Please do not redesign the incident management process or replace the incident bridge. This is about making communication faster and more consistent.

---

## Source B — Workshop extract

**Incident Manager:** I am happy for the system to generate a draft from incident data, but I do not want an external customer message going out automatically. Someone needs to review the wording first.

**Customer Communications Lead:** Agreed for external messages. Customer-facing wording must be approved by Communications and must use approved customer terminology. Technical hostnames, employee names and internal troubleshooting detail must not leak into customer updates.

**Service Desk Lead:** For internal Service Desk updates I would prefer automatic sending once impact is known. Agents need information quickly and waiting for another approval step could leave them behind the bridge.

**Incident Manager:** That worries me early in an incident. The impact field is often corrected as we learn more. I would rather an Incident Manager confirm the update before it is distributed internally as well.

**Product Owner:** The first version should show incident ID, affected service, impact summary, current status and the next update time if one is known. Five minutes after a material status change feels like a reasonable target for getting an internal update out.

**Incident Manager:** Be careful with "next update time". If the bridge has not committed to one, the tool must not invent a time just to fill the template.

**Platform Engineer:** We can get core incident data from the ITSM platform. We may also be able to use CMDB service relationships, the collaboration platform and the public status page, but I have not checked all of those APIs or their permissions yet. The quality of impacted-service data depends on the CI relationships being maintained properly.

**Security and Privacy Representative:** I need to know which channels receive data and what fields leave the company. Use approved authentication patterns and least privilege. Do not put personal information, internal hostnames or other restricted operational detail into external communications.

**Customer Communications Lead:** Longer term I would like reusable templates for different customer segments and possibly multilingual updates, but not if that makes the first release too large.

---

## Source C — Current process notes

Current major incident communications vary by incident and team, but the common pattern is:

1. A major incident record is opened and a bridge is established.
2. Technical teams provide updates verbally or in collaboration chat.
3. The Incident Manager or Service Desk manually rewrites information for internal audiences.
4. Customer Communications prepares any external customer-facing statement separately.
5. External wording is reviewed before publication.
6. Further updates are issued until service restoration and incident closure.

Known problems:

- Internal recipients sometimes receive different versions of the same incident status.
- Distribution lists and channel membership are not always current.
- Updates may be copied from an earlier incident and edited incompletely.
- There is no agreed definition of what counts as a "material status change" that should trigger a new communication.
- Incident severity can change during the lifecycle.
- Impact information is often incomplete or revised during the first part of an incident.
- The current process does not define one standard cadence for internal updates.

---

## Source D — Delivery note from Agile lead

Please give me a bounded first release that can be decomposed later, but do not create stories or estimates yet.

My preference would be to prove one internal communication path plus drafted external messaging before attempting every channel, but treat that as a delivery suggestion rather than an agreed requirement.

Do not assume recipients, distribution lists, templates or approval rules are already settled. Where the workshop contains different views, capture the decision needed rather than choosing whichever workflow seems more efficient.

We should estimate only after the communication flows, approval boundaries and source-data feasibility are understood well enough to identify meaningful slices.
