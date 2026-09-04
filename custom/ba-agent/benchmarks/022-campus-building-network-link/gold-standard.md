# Benchmark 022 — Gold Standard

This file is evaluator-only and must not be sent to the model under test.

## Overall conclusion

The campus-connectivity outcome is feasible, but one direct 900 metre 1000BASE-T Cat6 channel is infeasible because the supplied maximum channel length is 100 metres and there is no supported powered midpoint design.

The preferred architecture is a passive optical inter-building link through the existing conduit between the two communications rooms, terminated through equipment compatible with the existing switches or through separately justified media equipment if compatibility cannot be established. Exact optical medium, strand/core count, connector/termination, transceiver coding, wavelength, speed mode and make/model remain survey/candidate verification decisions.

## Expected reasoning

A strong answer should:

1. preserve the reliable campus-network outcome while rejecting only the direct copper mechanism;
2. cite the supplied 100 metre limit and 900 metre pathway as the sufficient blocker without inventing extra hazards;
3. treat electrical isolation preference, existing conduit, endpoint power/rack space and unused SFP+ cages as relevant evidence;
4. avoid treating the cages as proof of any exact optical compatibility;
5. keep 1 Gbit/s as a target until BA/service ownership confirms demand and service requirements;
6. compare a passive optical path with at least one bounded alternative, such as a surveyed wireless bridge, while leaving line-of-sight/spectrum/weather/security facts Unknown;
7. avoid product shopping inside architecture.

## Preferred topology

`Building A switch boundary -> verified optical interface/termination -> passive inter-building optical path in existing conduit -> verified optical interface/termination -> Building B switch boundary`

The answer may prefer an optical family subject to survey and compatibility evidence, but must not claim exact switch-module/cable interoperability without the missing switch and candidate facts.

## Handoff boundaries

### BA / service ownership

- whether 1 Gbit/s is sufficient or mandatory;
- current/forecast traffic and application criticality;
- single-link versus resilient service requirement;
- acceptable restoration time and planned outage;
- Layer-2 extension versus routed/security boundary;
- monitoring/operational ownership and migration acceptance.

### Procurement / implementation verification

- exact switch model, firmware, supported speed modes and approved module matrix;
- optical budget and distance/path survey evidence;
- medium, strand/core count, connector/termination and installation suitability;
- candidate transceiver compatibility at both ends;
- conduit condition/pull feasibility and required installation evidence;
- warranty/supportability and candidate-specific acceptance tests.

No make/model should be recommended from the supplied evidence.
