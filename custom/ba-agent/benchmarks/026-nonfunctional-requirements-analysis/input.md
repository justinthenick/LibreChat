# Benchmark 026 Input — Customer Claims Portal NFR Packet

The team is replacing an email-based claims intake process with a customer web portal. Functional requirements are being handled elsewhere. Analyze only the non-functional/quality evidence below.

## Source notes

- Product Owner: "Pages should feel fast. I don't want customers waiting around, but we haven't agreed a response-time number."
- Sponsor: "Let's aim for 99.9% availability during our normal business hours if that's practical." No SLA has been approved.
- Operations analyst: month-end launch load is estimated at around **2,000 concurrent users**. The number is a planning estimate, not a committed capacity requirement.
- Legal decision L-22: customer personal data for this service **must be stored in Australia**.
- Security engineer: "Export files should probably be encrypted at rest, but I need to confirm whether that is actually required by policy." No encryption algorithm or platform mechanism is specified.
- Design lead: "We should meet WCAG 2.2 AA." The steering group has not accepted this as committed scope yet.
- Service desk process note: support coverage for the portal is **07:00-19:00 Australia/Sydney on business days**.
- Claims Operations: if automated intake is unavailable, the existing email intake remains the confirmed manual fallback.
- Business continuity discussion: "Same-day recovery would probably be okay, but nobody has set an RTO or RPO." 
- Support manager: when a customer reports a failed claim submission, support must be able to identify the affected claim using the existing case reference. No logging, tracing, database, or monitoring implementation is specified.
- No source material establishes data-retention duration, backup frequency, geographic redundancy, active-active architecture, autoscaling, browser support matrix, mobile-app requirements, penetration-test cadence, certification, encryption algorithm, or monitoring technology.

## Request

Produce a non-functional requirements analysis suitable as an input to solution design. Preserve targets, estimates, candidates and unknowns exactly rather than filling in standard architecture expectations.