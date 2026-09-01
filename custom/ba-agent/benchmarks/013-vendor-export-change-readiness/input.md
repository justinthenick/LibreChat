# Source packet — Vendor Invoice Exception Export

The Finance Operations team wants a controlled export of monthly invoice-exception data for analysis by an external analytics vendor. BA analysis, decomposition, acceptance criteria and test designs are complete for the confirmed internal export capability, but downstream solution and Change evidence is incomplete.

## Confirmed scope and constraints

- REQ-01 — An authorised Finance Operations user can generate an invoice-exception export containing account ID, invoice ID, exception code and exception amount. Status: Confirmed.
- REQ-02 — The export must use the organisation's existing Finance access-control model; this initiative must not create a new privilege model. Status: Confirmed.
- REQ-03 — The export event must record requester identity, outcome and associated date/time. Status: Confirmed.
- REQ-04 — The current manual report process must remain available when the new export capability is unavailable. Status: Confirmed.
- CON-01 — Existing Finance access-control policy is not to be redesigned by this initiative. Status: Confirmed.
- CON-02 — External handling of customer-related data must follow existing security and data-handling standards. Status: Confirmed.

## Unresolved / non-committed material

- REQ-05 — Product Owner proposes SFTP delivery to the external analytics vendor as the first external-transfer mechanism. Status: Candidate. No transfer mechanism has been approved.
- REQ-06 — Whether account IDs must be tokenised before external transfer is disputed. Security Engineering says tokenisation is required; Finance Operations says the vendor needs the original account ID. Decision owner: Unknown. Status: Disputed.
- REQ-07 — Product Owner target: produce the export within 15 minutes for a normal monthly run. Status: Target / non-binding.
- REQ-08 — Scheduled recurring exports are Deferred.
- REQ-09 — Retention period for generated export files is Unknown.
- REQ-10 — A draft field mapping has been reviewed by Finance and contains the four confirmed data elements. Status: Confirmed evidence, but it is not an approved interface design.

## Delivery / acceptance evidence

- US-01 Ready — generate the invoice-exception export with the four confirmed data elements. Traces REQ-01.
- US-02 Ready — apply existing Finance access controls. Traces REQ-02, CON-01.
- US-03 Ready — record export requester/outcome/date-time. Traces REQ-03.
- US-04 Ready — preserve the manual-report fallback. Traces REQ-04.
- CAN-01 Candidate — external vendor transfer using SFTP. Traces REQ-05.
- DEC-01 Blocked — account-ID tokenisation rule for external transfer. Traces REQ-06. Decision owner Unknown.
- TGT-01 Target — 15-minute normal-run objective. Traces REQ-07.
- DEF-01 Deferred — scheduled recurring exports. Traces REQ-08.
- DEC-02 Open — export-file retention period. Traces REQ-09.

Acceptance criteria:

- AC-01 — The export contains account ID, invoice ID, exception code and exception amount. Traces US-01 / REQ-01.
- AC-02 — Only users permitted by the existing Finance access-control model can generate the export. Traces US-02 / REQ-02 / CON-01.
- AC-03 — Export requester identity, outcome and associated date/time are recorded. Traces US-03 / REQ-03.
- AC-04 — The existing manual report remains available when the new export capability is unavailable. Traces US-04 / REQ-04.
- AC-CON-01 — No new Finance privilege model is introduced. Traces CON-01.
- AC-CON-02 — Any external handling of customer-related data conforms to existing security/data-handling standards. Traces CON-02.

Test/assurance designs exist for AC-01 through AC-04 and both constraints. They have not been executed.

## Downstream evidence and comments

- A draft field mapping exists for the four confirmed export elements. It has been reviewed by Finance but is not an approved interface specification.
- The Integration Lead says: "We already have a Managed File Transfer gateway used by another team. We might be able to reuse it, but I haven't checked vendor onboarding, endpoint support, authentication or whether it is approved for this data."
- The Vendor Manager says the analytics vendor can receive SFTP files, but no internal transfer mechanism or vendor-onboarding decision has been approved.
- The Change Coordinator says a Change package should be prepared after the external-transfer approach, data-handling decision and implementation/backout approach are established. No Change approver, CAB decision, risk rating, implementation date or maintenance window is supplied.
- No approved solution/interface design, production deployment plan, rollback/backout plan, production validation method, test-execution evidence, support transition plan or communications plan is supplied.
