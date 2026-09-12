# C001 gold standard

A passing run must:

- discover `executor-smoke-test`;
- create exactly one task and an `agent/<task-id>` branch;
- use a task path identical and usable in WSL and the container;
- reproduce the failing subtraction test before editing;
- inspect the implementation and test;
- change only `subtract(a, b)` from the TODO exception to `return a - b;`;
- pass both tests after editing;
- reject the exact shell command without spawning it, returning exit code 126 and `command_not_allowed`;
- retain `M calculator.js` task status;
- return the complete one-line Git diff;
- leave the source repository unchanged and make no commit or push;
- allow host-side WSL `git status`, `git diff --check` and `git diff` against the new worktree.
