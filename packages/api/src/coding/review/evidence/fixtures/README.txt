Unmodified public verification data from C2SP/wycheproof.
Revision: d17cc89fa5c8f4f4d378b5385ebf75da5d0926c9
Source: https://github.com/C2SP/wycheproof/blob/d17cc89fa5c8f4f4d378b5385ebf75da5d0926c9/testvectors_v1/ed25519_test.json
Local name: ed25519.json (bytes unchanged).
Git blob: 3f991dd56496129e3a99b6b486408ef8f3df6945
SHA256: ea80ffebac085e21cb9d3e903e7fa2b448d96702da5b31f061d0b83b430b74b3
172,628 bytes; 210 cases in 111 groups: 117 valid, 64 invalid, 29 acceptable.
The accompanying upstream LICENSE is Apache-2.0, copied unchanged from the same revision. Preserve upstream source/group attributions, notes, case IDs, comments, flags and result classifications in the JSON. No test data, keys or signatures were generated for this import.
The spec runs raw pure Ed25519 message verification on Node 24.16.0 / OpenSSL 3.5.6 and compares the current verifyPublicFixture API. No S4 frame prefix or prehash is added. Every case is exercised; the expected result, never the flag, determines valid/invalid assertions. Acceptable outcomes are observations only and are reported separately. Unsupported lengths are explicitly classified as length rejection; unexpected import/verification exceptions fail rather than count as a rejection. Metadata, hash and full-case coverage checks prevent unnoticed filtering. No policy adjustment is made to match outcomes.
This public primitive corpus does not contain signed S4-OFFLINE-1 profile envelopes and cannot close positive authenticated-profile acceptance. It installs no trust and provides no runtime authority.
