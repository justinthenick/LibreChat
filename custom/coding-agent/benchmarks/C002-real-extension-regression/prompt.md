# C002 prompt

In the `synology-magnet-c002` repository, diagnose and repair the existing validation failures.

1. Create exactly one isolated task worktree.
2. Read the repository's `AGENTS.md` and the files implicated by the validation output.
3. Run `npm test` before editing and explain every failure.
4. Apply the smallest coherent repair. Do not add dependencies, broaden extension permissions, change credential handling or redesign the UI.
5. Run `npm test` after editing.
6. Call `task_status` and `git_diff`.

Do not commit, push or modify the source repository. Report the task ID, branch, diagnosis, changed files, before-and-after checks, remaining risks and complete diff.
