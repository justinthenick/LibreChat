# Benchmark 022 — Scoring Rubric

This file is evaluator-only and must not be sent to the model under test.

Score out of 100 before penalties.

## 1. Outcome vs mechanism separation — 15 points

- Preserves reliable inter-building campus connectivity while separating it from long copper: 8
- Does not reject the objective because the proposed medium fails: 4
- Keeps the 1 Gbit/s statement at Target strength: 3

## 2. Feasibility and evidence accuracy — 20 points

- Classifies one 900 metre 1000BASE-T Cat6 channel as infeasible: 7
- Uses the supplied 100 metre limit as the sufficient blocker: 5
- Does not invent additional copper hazards or midpoint facilities: 4
- Uses conduit, endpoint facilities, electrical-isolation preference and SFP+ cages at their supported strength: 4

## 3. Alternative topology quality — 25 points

- Proposes a passive optical inter-building path through the existing conduit: 8
- Shows clear endpoint/interface/path boundaries: 5
- Keeps exact medium/termination/module decisions conditional on survey and compatibility: 5
- Compares at least one bounded alternative with honest Unknowns: 3
- Selects the preferred design with defensible maintainability/isolation reasoning: 4

## 4. Compatibility and requirement-strength discipline — 15 points

- Does not infer exact transceiver/module compatibility from an SFP+ cage: 5
- Does not invent fibre, connector, wavelength, coding, speed-mode or optical-budget facts: 4
- Distinguishes hard requirements, targets, preferences and Unknowns: 3
- Does not invent VLAN/routing/security/redundancy design: 3

## 5. Unknowns and validation discipline — 15 points

- Exposes traffic, availability/restoration and Layer-2/routed-boundary questions: 5
- Exposes switch/firmware/module/path/installation compatibility checks: 5
- Includes migration, monitoring/ownership and acceptance considerations without inventing answers: 3
- Converts Unknowns into concrete validation actions: 2

## 6. Handoff discipline — 10 points

- Routes service scope/availability decisions to BA or service ownership: 4
- Gives Procurement a capability-and-evidence specification rather than products: 4
- Keeps product selection and exact implementation downstream: 2

# Penalties

- **-30** if the direct 900 metre Cat6 channel is recommended as standards-compliant.
- **-20** if a specific transceiver/fibre/cable combination is declared compatible without switch and candidate evidence.
- **-15** if unsupported active repeaters, powered midpoint cabinets or extenders are made part of the preferred design.
- **-10 each** for invented critical VLAN, routing, firewall, redundancy, civil-work or optical-budget facts used to select the design.
- **-10** if 1 Gbit/s is promoted from Target to hard minimum without justification.
- **-10** if make/model procurement recommendations are supplied.
- **-5** if a wireless alternative is declared feasible without route/line-of-sight/spectrum validation.

# Interpretation

- 90–100: excellent third-domain architecture discipline; candidate is ready for a standalone retain/reject decision.
- 80–89: useful, but a reusable compatibility or handoff defect remains.
- 70–79: mixed; material invention or boundary risk remains.
- below 70: unreliable network-topology architecture discipline.

For A/B comparison, prefer the Skill only if it materially improves feasibility accuracy, compatibility caution, requirement strength and BA/Procurement handoff discipline without inventing a network design.
