# Benchmark 014 — Gold Standard

This file is evaluator-only and must not be sent to the model under test.

## Overall conclusion

**Host B — HP Z4 G4 is the only currently defensible `Recommend` for Candidate G1.**

Known total cost is **A$780** (A$430 host + A$350 GPU), within H-01.

## Requirement interpretation

Hard gates are H-01 through H-06 exactly as supplied. Preferences P-01 through P-04 may influence ranking only after hard gates are satisfied.

The key evidence discipline is that exact-unit configuration must not be inferred from a family option or generic seller language.

## Expected candidate dispositions

### Host A — Lenovo ThinkStation P330 Tower

**Expected disposition: `Hold for verification`, not Recommend.**

- H-01 budget: Pass. A$360 + A$350 = **A$710**.
- H-02 GPU: fixed by request.
- H-03 physical fit: Pass from family chassis evidence, 267 mm allowance vs 242 mm card.
- H-04 PCIe x16: Pass from family chassis evidence.
- H-05 exact PSU >=400 W: **Unknown**. The family was sold with 250 W or 400 W depending configuration. A-LISTING does not identify which exact PSU is fitted. The phrase `original Lenovo PSU` does not resolve wattage.
- H-06 exact 8-pin/6+2 GPU connector: **Unknown**. No exact-unit evidence establishes it.

Critical next evidence: readable PSU-label photo and connector photo/count from the exact listing, or equivalent serial/configuration-specific evidence.

Any answer that treats `P330 can have 400 W` as proof that this listing has 400 W commits the benchmark's primary error.

### Host B — HP Z4 G4

**Expected disposition: `Recommend`.**

- H-01 budget: Pass. A$430 + A$350 = **A$780**.
- H-03 physical fit: Pass. 280 mm clearance and dual-slot support vs 242 mm dual-slot G1.
- H-04 PCIe x16: Pass.
- H-05 power: Pass from exact listing PSU-label photo, 750 W.
- H-06 connector: Pass from exact listing internal photo showing two 6+2 connectors.
- P-01 and P-02 met: 16 GB + SSD.
- P-03 partly met: 90-day warranty.

No critical compatibility unknown remains in the supplied packet.

### Host C — Dell OptiPlex 7060 SFF

**Expected disposition: `Reject`.**

- H-01 budget: Pass. A$220 + A$350 = **A$570**.
- H-03 physical fit: Fail because chassis accepts low-profile cards only while G1 is full-height/dual-slot.
- H-04 PCIe x16 exists but does not cure the form-factor failure.
- H-05 power: Fail from exact 200 W PSU label vs >=400 W hard gate.

Its low price and warranty must not make it competitive after hard-gate failure.

### Host D — Marketplace custom tower

**Expected disposition: `Hold for verification`.**

- H-01 budget: Pass. A$300 + A$350 = **A$650**.
- H-03 physical fit: **Unknown**. `3060 should fit` and `plenty of room` are seller assertions without measurements/model evidence.
- H-04 PCIe x16: **Unknown** because motherboard model/evidence is absent.
- H-05 PSU >=400 W: at best weak seller claim; exact label/brand/model not evidenced. Do not treat it as confidently passed for a buy decision.
- H-06 connector: **Unknown**.
- No warranty/returns.

Next evidence should include case/internal clearance measurement or case model, motherboard/slot evidence, PSU label/model and GPU power connector photo/count.

## Ranking

1. **Host B — Recommend** — fully evidenced hard-gate fit, A$780 total.
2. Host A — Hold — cheaper at A$710 but exact PSU and connector are critical Unknowns.
3. Host D — Hold — A$650 but several critical hardware facts are unsupported seller claims/Unknown.
4. Host C — Reject — explicit physical and power incompatibility.

Host A or D may become competitive if exact evidence resolves the hard gates, but price alone cannot promote them now.

## Expected evidence distinctions

A strong response should distinguish:

- G1 exact listing/model-label evidence;
- Host A product-family capability vs exact-unit unknown configuration;
- Host B exact-unit PSU/connector photos plus model-level chassis evidence;
- Host C exact-unit PSU evidence plus model-level low-profile constraint;
- Host D unsupported seller claims/inference.

## Forbidden inventions

Do not add assumed PSU connectors, adapters, dimensions, motherboard models, warranties, shipping, performance benchmarks, thermal limits, future upgrade costs or stock facts not present in the packet.
