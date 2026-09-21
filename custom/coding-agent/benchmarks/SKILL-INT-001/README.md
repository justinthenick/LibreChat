# SKILL-INT-001 — Agent Skill interoperability

## Purpose

Prove that one repository skill under `.agents/skills` is discovered by multiple coding-agent runtimes before it is enabled in the LibreChat Software Engineering Pilot.

The fixture is `codebase-design`, reused from the repository's existing Claude-oriented skill rather than newly invented.

## Preconditions

- checkout branch: `feat/interoperable-agent-skills`;
- run from the repository root;
- workspace is trusted by the runtime where applicable;
- no changes are required to the executor.

## Codex

Discovery succeeds when Codex launched from the repository root can resolve `codebase-design` from `.agents/skills/codebase-design/SKILL.md`.

Positive trigger:

```text
Use $codebase-design to explain whether a proposed module interface is deep or shallow. Do not modify files.
```

Expected evidence:

- the skill is available without copying it into a user-global directory;
- the response uses the skill vocabulary such as module, interface, depth, seam, leverage and locality;
- no repository modification occurs.

## Gemini CLI

First verify discovery:

```bash
gemini skills list
```

Expected evidence includes an enabled workspace skill named `codebase-design`.

Positive trigger in an interactive session:

```text
Use the codebase-design skill to explain whether a proposed module interface is deep or shallow. Do not modify files.
```

If the skill was added after session start, run `/skills reload` first.

Expected evidence:

- Gemini requests/records skill activation according to its normal consent flow;
- the response uses the same skill vocabulary;
- no repository modification occurs.

## Nearby non-trigger

For each runtime, ask:

```text
What is the current Git branch name? Do not analyze architecture and do not modify files.
```

Expected: `codebase-design` is not activated merely because it exists in the catalog.

## LibreChat gate

Do not enable the Software Engineering Pilot for skills as part of this benchmark.

After Codex and Gemini discovery pass, merge the GitHub Skill Sync source and verify that LibreChat mirrors `codebase-design` from source id `coding-agent-skills`.

Pilot enablement and a narrow allowlist are a subsequent benchmark/change.
