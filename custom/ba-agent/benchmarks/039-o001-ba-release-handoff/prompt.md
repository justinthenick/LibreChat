# Benchmark 039 prompt

Apply the candidate `BA Supervisor → Release / Change Assurance` workflow policy to **each case independently**.

For each case, return these headings exactly:

## CASE <A|B> ROUTE
One line only: `RETAIN_BA` or `HANDOFF_RELEASE_ASSURANCE`.

## CASE <A|B> REASON
A concise explanation grounded only in the supplied request/evidence.

## CASE <A|B> HANDOFF_PACKET
- If `RETAIN_BA`, state `NOT_APPLICABLE` and do not manufacture release-assurance work.
- If `HANDOFF_RELEASE_ASSURANCE`, pass only the evidence and states needed by Release / Change Assurance, including the exact assurance question. Preserve Candidate, Unknown, Draft, OPEN, NOT RUN and pilot-only states exactly.

## CASE <A|B> PROHIBITED_UPGRADES_CHECK
State whether any approval, owner, date, production result, rollback demonstration, monitoring control or evidence state was invented or strengthened. Expected value: `NONE`.

Do not solve unrelated Solution Architecture, Procurement or Manuscript work. Do not route Case A merely because a target date exists. Do not keep Case B in BA merely because its requirements are already linked.
