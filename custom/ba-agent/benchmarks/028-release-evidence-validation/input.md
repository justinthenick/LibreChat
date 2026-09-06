# Benchmark 028 Input — Billing Portal Release Evidence Packet

Assess only what this packet demonstrates about release CHG-442 / build 2.4.1.

## Planned scope

- Fix customer login timeout defect DEF-61.
- Add invoice CSV export required by AC-17.
- No database schema change is planned.

## Change / deployment evidence

- Change record CHG-442 shows `Authorized` by named local Change Authority: Sam Lee at 2026-09-04 21:40.
- Deployment plan says build 2.4.1 should be deployed between 22:00 and 22:30 and includes a documented rollback procedure.
- Deployment log excerpt:
  - 22:05 deployment started;
  - 22:07 application container replaced with build 2.4.1;
  - 22:08 application health endpoint returned HTTP 200;
  - 22:09 deployment script completed with exit code 0.
- No evidence says the rollback procedure was executed.

## Test evidence

- T-101 / AC-12 customer login after idle timeout: `PASS`, executed 22:12, result record includes expected vs actual behavior.
- T-102 / AC-17 invoice CSV export: `FAIL`, executed 22:14. Actual result: HTTP 500 when exporting invoices containing an adjustment line.
- DEF-77 was raised from T-102 and is still `Open`. Severity is recorded as Medium. No accepted-risk decision is supplied.
- T-103 basic invoice view: `PASS`, executed 22:13.

## Monitoring / service evidence

- Infrastructure dashboard screenshot at 22:15 shows CPU 28%, memory 54%, container running and no restart since 22:07.
- No packet evidence shows customer transaction success rate, export transaction health, error-rate trend, synthetic tests, user validation, or business KPI checks after deployment.

## Communications

At 22:20 the release coordinator sent: "Release fully successful. Build 2.4.1 is live with no issues."

## Request

Validate the release evidence. State what is Verified, Partially evidenced, Not evidenced or Failed, and give the strongest overall release-success conclusion the packet supports. Do not infer missing checks or rewrite the release history.