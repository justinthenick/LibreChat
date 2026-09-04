---
name: derive-test-cases
description: Use after acceptance criteria are sufficiently ready to derive traceable test cases and assurance coverage without inventing UI actions, test data, environments, automation, interfaces, error messages or unresolved business behaviour.
always-apply: false
user-invocable: true
disable-model-invocation: false
---

# Derive Test Cases

Version: **0.3.0**

## Purpose

Turn sufficiently ready acceptance criteria into a compact, traceable set of test cases or assurance checks while preserving upstream readiness, uncertainty and scope boundaries.

This skill does **not** design test automation, test environments, architecture, detailed test data, UI procedures or implementation-specific diagnostics.

## Core principle

A test case verifies an established condition; it must not create new product behaviour or future execution prerequisites merely to make testing convenient.

## Non-negotiable rules

1. **Preserve upstream readiness and status.**
   - Ready criteria may be turned into test cases.
   - Partially Ready criteria may be tested only for the confirmed portion.
   - Blocked / Disputed / Unknown behaviour remains untestable until resolved.
   - Candidate / Conditional scope remains non-committed.
   - Deferred work receives no current delivery test cases.
   - Targets remain planning/quality objectives unless upstream explicitly makes them binding acceptance commitments.

2. **Trace every test case.**
   Every material test case must reference:
   - acceptance-criterion ID;
   - delivery-item ID;
   - upstream requirement ID(s).

3. **Do not invent execution mechanics.**
   Unless explicitly sourced, do not invent:
   - screens, buttons, menus, forms or click paths;
   - API endpoints, protocols, payloads, queues, databases or storage;
   - test environments, deployment stages or accounts;
   - login/authentication steps;
   - notification channels;
   - error messages or validation text;
   - retries, timeouts or polling;
   - test automation frameworks, scripts or tooling;
   - mock/stub architecture;
   - exact test data values, formats or boundary numbers.

4. **Do not manufacture future execution prerequisites.**
   The same no-invention rule applies to gaps, next steps, execution planning and recommendations.
   - Absent UI/API/environment/account/data-format/protocol/tooling detail is **not** itself a gap to list.
   - Do not say such mechanics `must be defined`, `must be established`, `are required before execution`, or equivalent unless upstream explicitly establishes that prerequisite.
   - Do not introduce owners, sign-off roles, compliance owners, approval authorities or governance steps that are not sourced.
   - If a supplied unresolved Decision Item, Unknown requirement, Candidate dependency or other explicit upstream item prevents test derivation, carry that specific item forward with its existing status and owner value unchanged.

5. **No synthetic business rules.**
   Do not resolve disputed decisions, infer approval rights, invent duplicate/error handling, add field validation rules or assume behavior for Unknown areas.

6. **Logical complements are allowed only when necessary.**
   If an acceptance criterion explicitly establishes an `only when`, `must not`, `cannot`, `remains available when`, or equivalent boundary, a positive and/or negative test may be derived from that boundary.
   Label such cases `Derived boundary` when the expected result is the logical complement rather than separately explicit wording.

7. **Do not harden Targets.**
   A Target may be listed as a non-binding performance/quality observation opportunity, but do not turn it into a pass/fail release gate or mandatory test unless upstream has done so.

8. **Constraint assurance states WHAT, never HOW, unless sourced.**
   For security/process/read-only/data-integrity constraints, state only the required condition or state to be assured.
   - Do not prescribe inspection, observation, code review, account inspection, IAM review, log review, database inspection, API tracing, configuration review or any other verification mechanism unless upstream explicitly establishes it.
   - A good assurance check is `The integration uses an approved service identity`, not `Inspect the identity configuration and verify...`.

9. **Avoid over-splitting.**
   Create enough cases to cover materially distinct acceptance conditions and supported negative boundaries, but do not multiply cases by invented data combinations, browsers, channels, roles, states, environments or permutations.

10. **Coverage integrity check is mandatory.**
   Before returning the answer, verify:
   - each Ready criterion is covered by at least one test case or assurance check;
   - no test case points to a non-existent AC/work-item/REQ ID;
   - Blocked/Candidate/Deferred/Unknown behavior has not leaked into committed tests;
   - every expected outcome is grounded in the supplied acceptance criteria;
   - any listed unresolved gap is itself an explicit upstream item that blocks test derivation;
   - no absent execution mechanic has been promoted into a required future prerequisite.

## Test-case wording

Prefer concise declarative test cases with:

- **Condition / setup:** only sourced preconditions necessary to exercise the criterion;
- **Action / stimulus:** only the sourced business action or state transition;
- **Expected outcome:** the established acceptance condition;
- **Evidence basis:** `Explicit` or `Derived boundary`.

Do not use Given/When/Then unless every clause is source-backed.

## Default output

1. Test-design readiness
2. Acceptance-criterion readiness map
3. Test cases for Ready / confirmed portions
4. Constraint / assurance checks
5. Blocked and unresolved coverage
6. Candidate / conditional coverage notes
7. Target / deferred coverage notes
8. Traceability and coverage summary

Add a ninth section, **Sourced blockers to further test derivation**, only when the supplied upstream material contains explicit unresolved items that actually prevent additional test cases from being derived. Do not use that section for absent execution mechanics.

Recommended table:

`Test ID | AC ID | Delivery item | Test condition | Expected outcome | Evidence basis | Upstream REQ(s)`

## Final quality bar

A strong answer is traceable and executable at a behavioural level without pretending that unresolved requirements, implementation details, future execution mechanisms, governance or test mechanics are known.

## Changelog

### 0.3.0

- Removed the default execution-planning gaps section.
- Restricted optional gaps to explicit upstream blockers that prevent test derivation.
- Prohibited treating absent UI/API/environment/test-data/tooling mechanics as future prerequisites.
- Tightened assurance checks to state only the required condition/state, never an inspection mechanism unless sourced.

### 0.2.0

- Added controls against manufacturing future execution prerequisites and decision ownership.

### 0.1.0

- Initial test/assurance derivation skill.
