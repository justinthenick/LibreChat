# BA Agent Lab

This folder contains version-controlled Business Analyst skills and benchmark cases for LibreChat.

## Goal

Build a reliable BA agent for an ITIL / Agile delivery environment. The first capability is deliberately narrow: **requirements analysis from messy source material**.

Current `analyze-requirements` version: **0.4.0**.

This capability does **not** create epics, user stories, use cases, estimates, solution designs, or implementation plans. Those will be separate skills so each capability can be benchmarked independently.

## Skill under test

- `skills/analyze-requirements/SKILL.md`

The skill is tested for evidence discipline, requirement-status discipline, traceability, ambiguity handling, unknown decision ownership, separation of analyst proposals from sourced requirements, and readiness for later decomposition.

## Benchmark 001 — Change Validation Automation

Purpose: establish and iteratively improve core requirements-analysis discipline using a change-enablement problem with tentative scope, technical uncertainty and a blocking-vs-advisory stakeholder dispute.

Files:

- `benchmarks/001-change-validation-automation/input.md` — model-visible benchmark input.
- `benchmarks/001-change-validation-automation/gold-standard.md` — evaluator-only expected analysis.
- `benchmarks/001-change-validation-automation/scoring-rubric.md` — evaluator-only scoring method.
- `benchmarks/001-change-validation-automation/results/` — versioned benchmark run notes and scores.

Latest validated Gemini 3.6 Flash results:

- no skill: **57/100**
- v0.2: **84/100**, **86/100** — average **85**
- v0.3: **93/100**, **97/100** — average **95**

Benchmark 001 drove the distinction between:

- **Evidence class** — how the source supports the statement;
- **Requirement status** — how agreed/committed the item is;
- **Confidence** — confidence that the extraction/classification accurately reflects the evidence.

## Benchmark 002 — Major Incident Communications Automation

Purpose: test **generalization** on a materially different IT service-management problem rather than continue optimizing against one benchmark.

It tests:

- different internal vs external communication rules;
- a human-approval boundary for customer messages;
- a disputed internal auto-send rule;
- tentative Severity 1 scope and eight-week delivery target;
- a tentative five-minute communication target;
- undefined `material status change` semantics;
- data quality, recipient and channel uncertainty;
- candidate integrations with incomplete API/permission evidence;
- activity/responsibility versus true decision authority;
- required outcomes versus analyst-suggested discovery/solution mechanisms.

Files:

- `benchmarks/002-major-incident-communications/input.md` — model-visible benchmark input.
- `benchmarks/002-major-incident-communications/gold-standard.md` — evaluator-only expected analysis.
- `benchmarks/002-major-incident-communications/scoring-rubric.md` — evaluator-only scoring method.

## Standard A/B test procedure

Use the same model and generation settings for both runs.

### Run A — baseline

Start a clean chat with Skills disabled. Supply only the selected benchmark `input.md` and this instruction:

> Act as a business analyst. Analyze the supplied source material and produce a requirements analysis suitable for stakeholder review. Identify the business objective, stakeholders, requirements, constraints, assumptions, ambiguities or contradictions, and important open questions. Do not invent facts or silently resolve disagreements. Do not create user stories, epics, estimates, solution designs or implementation plans at this stage.

Save the complete response.

### Run B — skill

Start another clean chat with the same model and settings. Manually invoke `$analyze-requirements`, supply the same benchmark `input.md`, and use the exact same instruction.

Save the complete response.

### Score

Score both responses independently using that benchmark's `scoring-rubric.md`. Record:

- model and exact model version/name;
- reasoning/temperature settings if exposed;
- date/time;
- skill version;
- baseline score;
- skill score;
- hallucinations;
- missed requirements;
- disputed rules incorrectly converted into facts;
- invented decision authority;
- analyst proposals incorrectly promoted into required outcomes;
- useful questions raised;
- recurring failure modes across repeated runs.

Do not allow the model being tested to read the gold standard or scoring rubric. For a clean benchmark, disable unrelated browsing/tools and do not expose this repository through Filesystem MCP during the run.

## Versioning and generalization rule

Change one material thing at a time. If the skill changes, increment its version in the changelog and rerun an appropriate benchmark.

Do not optimize indefinitely against one benchmark. Once a behavior is repeatably strong, add a materially different benchmark to test generalization. Keep a skill change only when it improves or preserves quality across the benchmark set without introducing a serious hallucination, authority, contradiction or evidence-discipline regression.
