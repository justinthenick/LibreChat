# Evaluation — B015 cross-domain verification

- Job: `b015-g36-procurement-verify-v02-ab-001`
- Model: `gemini-3.6-flash`
- Baseline: **82/100**, 6,142 tokens
- `verify-procurement-options` v0.2.0: **95/100**, 8,116 tokens
- Decision: **Retain v0.2.0 as cross-domain verified and move to B016.**

## Baseline

The baseline correctly recommends Candidate B, holds Candidate A and rejects Candidate C. Its reusable defect is Candidate D: approximate seller dimensions and the statement that the legs come off are treated as enough to infer a rigid access failure and Reject the table. The benchmark gold standard requires `Hold for verification` because the maximum rigid component width remains unevidenced. This is scored as an unsupported critical access inference and attracts the rubric's -10 critical-fact penalty.

## Skill v0.2.0

The Skill fixes that distinction cleanly. Candidate B is Recommend; Candidate A and D are Hold; Candidate C is Reject. It preserves exact-variant discipline for Candidate A and independently evaluates seating, room dimensions and access rather than letting family/approximate evidence leak across hard gates.

The only notable precision issue is preference-level wording that treats Candidate A's “Natural Oak” title as evidence of timber/veneer material. That is unsupported by the packet, so the no-invention section is not awarded. It does not influence hard-gate viability or the ranking, so no explicit penalty applies.

The 13-point quality improvement comes with about 32% more total tokens than baseline. Given that the improvement is specifically in avoiding a false Reject/unsupported access inference in a materially different domain, the added cost is acceptable for this stage.

B015 therefore provides the cross-domain evidence needed to treat `verify-procurement-options` v0.2.0 as reusable beyond IT hardware. The next isolated question is market-expansion behavior, not more verification tuning.
