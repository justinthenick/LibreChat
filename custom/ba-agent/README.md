# BA Agent Lab

This folder contains version-controlled Business Analyst skills and benchmark cases for LibreChat.

## Goal

Build a reliable BA agent for an ITIL Change Enablement / Agile delivery environment. The first capability is deliberately narrow: **requirements analysis from messy source material**.

Version 0.1 does **not** create epics, user stories, use cases, estimates, solution designs, or implementation plans. Those will be separate skills so each capability can be benchmarked independently.

## Benchmark 001 — Change Validation Automation

Files:

- `benchmarks/001-change-validation-automation/input.md` — the only benchmark material the model should see.
- `benchmarks/001-change-validation-automation/gold-standard.md` — evaluator-only expected analysis.
- `benchmarks/001-change-validation-automation/scoring-rubric.md` — evaluator-only scoring method.
- `skills/analyze-requirements/SKILL.md` — skill under test.

## Test procedure

Use the same model and generation settings for both runs.

### Run A — baseline

Start a clean chat with Skills disabled for the test agent. Supply `input.md` and this prompt:

> Analyze this material as a business analyst. Identify the business objective, stakeholders, requirements, constraints, assumptions, contradictions and open questions. Do not invent facts and do not create user stories yet.

Save the complete response.

### Run B — skill

Start another clean chat with the same model and settings. Enable Skills, manually invoke `$analyze-requirements`, supply the same `input.md`, and use the same prompt.

Save the complete response.

### Score

Score both responses independently using `scoring-rubric.md`. Record:

- model and exact model version/name
- reasoning/temperature settings if exposed
- date/time
- baseline score
- skill score
- hallucinations
- missed requirements
- unresolved contradictions that were incorrectly converted into facts
- useful questions raised

Do not allow the model being tested to read the gold standard or scoring rubric. For a clean benchmark, disable unrelated browsing/tools and do not expose this repository through Filesystem MCP during the run.

## Versioning rule

Change one material thing at a time. If the skill changes, increment its version in the changelog and rerun the same benchmark. Keep a change only if it improves the benchmark without introducing a serious regression.
