# Benchmark 001 — Change Validation Automation

**Status:** Synthetic benchmark input. The analyst should treat this as the complete available source pack.

---

## Source A — Stakeholder email

**From:** Head of Service Operations  
**Subject:** Pre-change validation idea

We have had several production changes delayed or backed out because basic pre-checks were either missed or were based on stale evidence. I want us to look at automating the checks we already expect teams to do before implementation.

Ideally, someone could run one validation from the change record and get a simple result showing what passed, what failed and what could not be checked automatically. The result should be kept with the change so we have evidence later.

I would like a useful first release in about six weeks. We should probably start with the ten most common change types rather than trying to solve every change on day one.

Please do not turn this into another huge workflow replacement project. The current approval process should remain in place for now.

---

## Source B — Meeting extract

**Change Manager:** I am comfortable with automation giving the implementer a warning, but I do not want a failed automated check automatically stopping an approved change until we have proved the checks are reliable.

**Operations Lead:** I disagree. If a critical pre-check is red, allowing the implementation to continue defeats the purpose. At least some failures should block implementation.

**Platform Engineer:** We can probably query the ITSM/CMDB data, monitoring platform and deployment system. I have not checked every API yet. Some checks will still need manual evidence, especially where there is no authoritative data source.

**Product Owner:** The output needs to be understandable at a glance: pass, fail, warning, and not checked. I also want the result attached to the change record with the date and time. Two minutes feels like the longest people will wait for it.

**Platform Engineer:** Two minutes might be fine for most checks, but some monitoring queries are slow. We need to test that before promising it.

**Security Representative:** Do not create a new highly privileged shared account just for this. Reuse approved authentication patterns and keep access least-privilege. I need to understand what systems it will read before I can sign off the approach.

**Change Manager:** One other point: I do not want the tool making configuration changes in production. This is validation, not remediation.

**Operations Lead:** Fine for phase one, but eventually I would like it to offer safe fixes for obvious issues.

**Product Owner:** That sounds later. Six weeks is already tight.

---

## Source C — Current process notes

Current pre-change activity varies by team, but the common pattern is:

1. A change record is raised.
2. The implementer performs a checklist of pre-change checks.
3. Evidence is added to the change record, usually as text, screenshots or attachments.
4. A peer or change reviewer checks the evidence.
5. The normal approval process continues.
6. The implementer performs the change in the approved window.

Known problems:

- Checklists differ between teams and change types.
- Screenshots may be several hours old by the time implementation starts.
- Reviewers cannot always tell when a check was actually performed.
- Some evidence is copied from previous changes.
- A failed pre-check does not have one consistent treatment across teams.
- There is no agreed definition yet of which pre-checks are "critical".

---

## Source D — Delivery note from Agile lead

If this proceeds, please give me a bounded MVP that can be split into backlog items. Do not assume every business rule is settled before discovery starts. Where stakeholders disagree, capture the decision needed rather than silently choosing one side.

We will estimate only after the initial requirements are understood well enough to identify meaningful slices.
