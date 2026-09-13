# Human promotion procedure

Executor tasks deliberately stop at an uncommitted worktree. Promotion is a separate, human-authorised operation performed from WSL after reviewing the complete task evidence.

The executor never runs these steps.

## Preconditions

Set explicit paths for the approved source repository and task:

```bash
CODING_ROOT=/home/<wsl-user>/coding-agent
REPOSITORY_NAME=<approved-repository>
TASK_ID=<executor-task-id>
REPO_PATH="$CODING_ROOT/repos/$REPOSITORY_NAME"
TASK_PATH="$CODING_ROOT/tasks/$TASK_ID"
```

Then verify the boundaries in Bash:

```bash
set -euo pipefail
test -d "$REPO_PATH/.git"
test -e "$TASK_PATH/.git"
test -z "$(git -C "$REPO_PATH" status --porcelain)"
test "$(git -C "$REPO_PATH" rev-parse HEAD)" = "$(git -C "$TASK_PATH" rev-parse HEAD)"
git -C "$TASK_PATH" diff --check
git -C "$TASK_PATH" status --short
git -C "$TASK_PATH" diff --stat
git -C "$TASK_PATH" diff
git -C "$TASK_PATH" ls-files --others --exclude-standard
while IFS= read -r -d '' RELATIVE_PATH; do
  test -f "$TASK_PATH/$RELATIVE_PATH"
  test ! -L "$TASK_PATH/$RELATIVE_PATH"
done < <(git -C "$TASK_PATH" ls-files --others --exclude-standard -z --)
```

Stop if the source repository is dirty, the two HEAD commits differ, the task diff is malformed, an untracked path is not a regular non-symlink file, or the observed change differs from the agent's report.

Run the repository's required tests in the same controlled environment used by the executor. Do not promote solely because the agent claimed they passed.

## Apply after human approval

Create a temporary complete patch from the reviewed task. Tracked changes are exported first, followed by every untracked regular file:

```bash
PATCH_FILE="$(mktemp /tmp/coding-agent-promotion.XXXXXX.patch)"
git -C "$TASK_PATH" diff --binary --no-ext-diff -- > "$PATCH_FILE"

while IFS= read -r -d '' RELATIVE_PATH; do
  test -f "$TASK_PATH/$RELATIVE_PATH"
  test ! -L "$TASK_PATH/$RELATIVE_PATH"
  set +e
  git -C "$TASK_PATH" diff --no-index --binary --no-ext-diff -- /dev/null "$RELATIVE_PATH" >> "$PATCH_FILE"
  DIFF_EXIT=$?
  set -e
  test "$DIFF_EXIT" -eq 1
done < <(git -C "$TASK_PATH" ls-files --others --exclude-standard -z --)

test -s "$PATCH_FILE"
git -C "$REPO_PATH" apply --check "$PATCH_FILE"
git -C "$REPO_PATH" apply --stat "$PATCH_FILE"
git -C "$REPO_PATH" apply "$PATCH_FILE"
```

The fail-closed exit-code check deliberately rejects empty untracked files because Git cannot represent them as an unstaged content diff. Add content or handle an intentionally empty file manually after review.

Review and test the source repository again:

```bash
git -C "$REPO_PATH" diff --check
git -C "$REPO_PATH" status --short
git -C "$REPO_PATH" diff --stat
git -C "$REPO_PATH" diff
```

Only a human may then create the source commit, push it, or open a pull request. Use the repository's normal branch, review and CI policy.

## Abort before commit

If source verification fails, reverse only the reviewed patch:

```bash
git -C "$REPO_PATH" apply --reverse --check "$PATCH_FILE"
git -C "$REPO_PATH" apply --reverse "$PATCH_FILE"
git -C "$REPO_PATH" status --short
```

Do not use `git reset --hard` or discard unrelated changes.

## Retention and cleanup

Keep the task worktree and patch until the promoted change is committed, pushed and independently verified. Afterwards, either retain them as evidence or clean them up deliberately.

Before removing a task worktree, reverse its uncommitted patch and verify it is clean:

```bash
git -C "$TASK_PATH" apply --reverse --check "$PATCH_FILE"
git -C "$TASK_PATH" apply --reverse "$PATCH_FILE"
test -z "$(git -C "$TASK_PATH" status --porcelain)"
git -C "$REPO_PATH" worktree remove "$TASK_PATH"
```

Branch deletion is a separate destructive decision and is never automated by the executor.
