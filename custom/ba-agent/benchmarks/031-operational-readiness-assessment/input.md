# Benchmark 031 Input — Vendor Export Operational Readiness Packet

Assess whether the automated vendor-export service is operationally ready for production based only on this packet.

## Service / support evidence

- Named service owner: Billing Operations.
- Support coverage: 08:00-18:00 Australia/Sydney on business days.
- Vendor support contact and escalation number are recorded in the service file.
- The service desk has a draft support article describing how to identify the export job and where to route incidents. The article is marked `Draft`; no evidence shows it has been published.

## Operating procedure / fallback

- Runbook RB-12 documents daily-job start/check/failure-response steps and is marked `Approved` by Billing Operations.
- If automated export is unavailable, Billing Operations can produce and send the existing manual export. This fallback is explicitly confirmed.
- No RTO or RPO is established for the export service.

## Monitoring evidence

- A monitoring dashboard definition has been created for job status and file-transfer result.
- Deployment checklist says the dashboard/alert configuration is `Planned for production deployment`.
- No evidence demonstrates that the production dashboard or alerts are currently active.
- No source specifies alert thresholds, paging/on-call integration, SIEM, or monitoring vendor requirements.

## Access / configuration evidence

- Production service account `svc-billing-export` has been created.
- Pre-release production-connectivity test at 16:20 shows authentication succeeded but the account received `Permission denied` when attempting to write to the vendor's target folder.
- Ticket ACC-91 to correct the vendor-folder write permission is Open. No later successful write test is supplied.
- Application version/configuration record for release 1.2 is complete.

## Known defect / residual risk

- DEF-42: on a vendor timeout the first retry may require an operator to use the documented `Retry export` action in RB-12.
- Service owner Billing Operations explicitly accepted DEF-42 as residual risk for release 1.2 until the automated retry enhancement is delivered later.
- The future retry enhancement is Deferred and is not part of this release.

## Other evidence

- A CMDB/service-catalog update is planned after production release; no local policy in this packet says that update is a pre-release gate.
- No packet evidence shows a 24x7 on-call roster, disaster-recovery exercise, formal knowledge-transfer meeting, backup job, capacity test, or security sign-off requirement.

## Request

Assess operational readiness. Distinguish Ready, Partially ready, Not evidenced and Not ready conditions; identify genuine blockers separately from ordinary missing evidence; preserve accepted residual risk and Deferred scope; and prepare a handoff for Change Readiness / ITIL assessment.