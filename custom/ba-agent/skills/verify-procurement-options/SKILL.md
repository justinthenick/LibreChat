---
name: verify-procurement-options
description: Verify procurement candidates against evidence-backed requirements, compatibility gates, exact-unit configuration, condition and landed cost without turning unknowns into assumptions.
---

# Verify Procurement Options

Version: **0.2.0**

## Purpose

Turn a procurement request plus supplied product/listing evidence into a defensible shortlist or rejection set. This Skill is intentionally domain-general: IT/electronics, furniture, appliances/kitchen, tools/industrial and other purchasable categories should use the same evidence discipline while applying different compatibility dimensions.

## Core principle

**A product family being capable of a specification does not prove that the exact item being sold has that specification. A critical unknown is not a pass. Each hard gate must also be evidenced independently: failure of one gate does not prove that another gate failed.**

## Required flow

1. **Classify the procurement domain and objective.** State what is being bought, the intended use, geography/currency if supplied, and whether the task is a component, bundle/system, replacement, fit-out or general purchase.
2. **Normalize requirements.** Separate Hard gates, Preferences, Targets and Unknowns. Do not silently promote a preference or target into a mandatory gate.
3. **Build the compatibility/evidence graph.** For every candidate or candidate combination, map each hard gate to the evidence that supports, contradicts or fails to establish it. Evaluate each gate independently. A candidate may already be rejected because one gate failed, but every other unevidenced gate must remain `Unknown` / `not evidenced`, not be converted to `Fail` by association.
4. **Distinguish evidence level.** At minimum distinguish:
   - exact-item / exact-listing evidence;
   - exact model/configuration evidence;
   - product-family evidence;
   - seller/retailer claim;
   - inference;
   - Unknown / not evidenced.
5. **Evaluate category-specific risk dimensions.** Use only dimensions relevant to the domain. Examples include:
   - IT/electronics: interfaces, form factor, slots, power capacity/connectors, thermals, firmware/OS support, dimensions/clearance;
   - furniture/home: physical dimensions, access path, load rating, materials/finish, assembly, ergonomics, room fit;
   - appliances/kitchen: dimensions, electrical/gas/water requirements, ventilation, installation, capacity, consumables, regulatory/safety requirements;
   - tools/industrial: power source, tooling/accessory interface, duty/load rating, safety/compliance, consumables, environmental limits.
   These are prompts for analysis, not permission to invent unsupplied requirements.
6. **Evaluate commercial evidence separately from technical fit.** Price, condition, warranty/returns, seller confidence, freight, required adapters/upgrades and total landed cost do not cure an unresolved hard compatibility gate.
7. **Assign a disposition.** Use one of:
   - `Recommend` — all material hard gates evidenced and no material contradiction;
   - `Shortlist` — appears viable, with only non-critical or commercial questions remaining;
   - `Hold for verification` — one or more critical gates remain Unknown or only family-level/inferential;
   - `Reject` — a hard gate is contradicted;
   - `Watch` — potentially useful later but not currently competitive/available/ready.
8. **State the next verification action for every Hold.** Ask for the smallest evidence that would resolve the gate, such as a PSU-label photo, exact dimensions, connector photo, model suffix, load rating, installation manual page or seller confirmation. Do not invent the answer.
9. **Rank only after gating.** A cheaper option must not outrank a technically unresolved or incompatible option merely on price.

## Non-negotiable controls

- Never substitute family-level capability for exact-unit configuration.
- Never convert seller language such as `supports`, `up to`, `compatible with`, `standard`, `should fit` or `ready for` into exact-item proof without corroborating evidence.
- Never assume included accessories, cables, brackets, adapters, installation parts, warranty, licences or consumables unless evidenced.
- Never assume used/refurbished condition implies a particular warranty, remaining life or defect state.
- Never invent dimensions, connectors, ratings, standards, model suffixes, prices, shipping, stock or compatibility.
- Never treat an Unknown hard gate as Passed because the candidate is cheap, common or from a reputable brand.
- **Never use one failed or passed gate as evidence for a different gate.** For example, an undersized PSU does not itself prove that a GPU power connector is absent; a width failure does not prove an access-path failure; a voltage mismatch does not prove a plug type. Unless the second fact is independently evidenced, leave it `Unknown` / `not evidenced`.
- A candidate can be `Reject` overall while some individual gates remain `Unknown`. Overall disposition and per-gate evidence status are separate concepts.
- Preserve contradictory evidence rather than choosing the convenient source silently.
- If two sources conflict, mark the gate `Conflicted` and identify what exact evidence would resolve it.
- Keep `Target` performance/cost goals distinct from hard minimums unless the request explicitly makes them mandatory.
- For bundles/systems, validate the interfaces **between** items, not just each item independently.

## Recommended output

### 1. Procurement objective and domain

### 2. Requirement register

`Requirement ID | Requirement | Class (Hard/Preference/Target/Unknown) | Evidence basis`

### 3. Candidate evidence register

`Candidate | Evidence item | Evidence level | What it establishes | What it does not establish`

### 4. Compatibility matrix

`Candidate or bundle | Hard gate | Status (Pass/Fail/Unknown/Conflicted) | Evidence | Consequence`

### 5. Commercial/value comparison

Include total known cost and explicitly identified unknown/additional costs. Do not manufacture missing totals.

### 6. Disposition and ranking

`Candidate | Disposition | Why | Critical unknowns | Next verification action`

### 7. Recommendation

Give the best currently defensible option, plus a value/balanced/stretch framing only where the evidence supports those tiers. If no option is safe to recommend, say so.

## Final audit

Before answering, check:

- Did I accidentally use a family spec as exact-item proof?
- Did I pass any critical Unknown?
- Did I mark a gate Pass or Fail only because a different gate passed or failed?
- For every per-gate status, can I point to evidence for that exact gate?
- Did I confuse price/value with compatibility?
- Did I invent a missing accessory, connector, dimension, rating, condition or warranty?
- Did I preserve conflicting evidence?
- Can every recommendation be traced to evidence supplied in the task?
