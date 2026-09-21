#!/usr/bin/env bash

# SKILL-INT-001 local discovery smoke test.
# Safe to run from the repository root. It does not intentionally modify files.

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" || exit 1

echo "=== SKILL-INT-001 ==="
echo "repo=$ROOT"
echo "branch=$(git branch --show-current 2>/dev/null || echo unknown)"
echo

echo "=== STRUCTURE ==="
for path in   .agents/skills/codebase-design/SKILL.md   .agents/skills/codebase-design/DEEPENING.md   .agents/skills/codebase-design/DESIGN-IT-TWICE.md   .agents/skills/codebase-design/LICENSE
do
  if [ -f "$path" ]; then
    echo "OK $path"
  else
    echo "MISSING $path"
  fi
done

echo
echo "=== CODEX ==="
if command -v codex >/dev/null 2>&1; then
  codex --version || true
  echo
  echo "--- explicit read-only skill invocation ---"
  codex exec --ephemeral --sandbox read-only     'Use $codebase-design to explain, in five concise bullets, what makes a module deep rather than shallow. Do not modify files.'     || echo "CODEX_INVOCATION_FAILED"
else
  echo "CODEX_NOT_FOUND"
fi

echo
echo "=== GEMINI CLI ==="
if command -v gemini >/dev/null 2>&1; then
  gemini --version || true
  echo
  echo "--- discovered skills ---"
  gemini skills list || echo "GEMINI_SKILL_LIST_FAILED"
  echo
  echo "For activation/consent validation, start 'gemini' interactively and ask:"
  echo "Use the codebase-design skill to explain whether a proposed module interface is deep or shallow. Do not modify files."
else
  echo "GEMINI_NOT_FOUND"
fi

echo
echo "=== WORKTREE STATUS ==="
git status --short --branch
