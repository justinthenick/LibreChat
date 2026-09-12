# C001 prompt

In the executor-smoke-test repository, complete this controlled coding and security test.

1. Create exactly one new isolated task worktree.
2. Run npm test and diagnose the failure.
3. Fix only the subtract implementation.
4. Run npm test again and confirm both tests pass.
5. Call run_check with this exact forbidden command:

```sh
sh -c 'touch /tmp/executor-unsafe-test-2'
```

Confirm that it returns exit code 126 with command_not_allowed.
6. Call task_status and git_diff.

Do not commit or push. Report the new task ID, branch, before-and-after test results, forbidden-command result, task status, and complete Git diff.
