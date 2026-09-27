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

Then verify the boundaries in Bash under the same sanitized Git environment used for promotion rendering:

```bash
set -euo pipefail
export HOME=/tmp/coding-agent-home
export XDG_CONFIG_HOME="$HOME/.config"
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_OPTIONAL_LOCKS=0
export GIT_TERMINAL_PROMPT=0
export LANG=C.UTF-8
unset GIT_DIFF_OPTS GIT_EXTERNAL_DIFF

PROMOTION_GIT=(
  git --no-optional-locks
  -c core.hooksPath=/dev/null
  -c core.fsmonitor=false
  -c credential.helper=
  -c core.excludesFile=/dev/null
  -c core.attributesFile=/dev/null
  -c protocol.allow=never
  -c protocol.https.allow=always
  -c submodule.recurse=false
)

test -d "$REPO_PATH/.git"
test -e "$TASK_PATH/.git"
test -z "$("${PROMOTION_GIT[@]}" -C "$REPO_PATH" status --porcelain)"
test "$("${PROMOTION_GIT[@]}" -C "$REPO_PATH" rev-parse HEAD)" = "$("${PROMOTION_GIT[@]}" -C "$TASK_PATH" rev-parse HEAD)"
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" diff --check
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" status --short
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" diff --stat
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" diff
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" ls-files --others --exclude-standard
while IFS= read -r -d '' RELATIVE_PATH; do
  test -f "$TASK_PATH/$RELATIVE_PATH"
  test ! -L "$TASK_PATH/$RELATIVE_PATH"
done < <("${PROMOTION_GIT[@]}" -C "$TASK_PATH" ls-files --others --exclude-standard -z --)
```

Stop if the source repository is dirty, the two HEAD commits differ, the task diff is malformed, an untracked path is not a regular non-symlink file, or the observed change differs from the agent's report.

Run the repository's required tests in the same controlled environment used by the executor. Do not promote solely because the agent claimed they passed.

## Apply after human approval

Create a temporary complete patch from the reviewed task. Tracked changes are exported first, followed by every untracked regular file:

```bash
PATCH_FILE="$(mktemp /tmp/coding-agent-promotion.XXXXXX.patch)"
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" diff --binary --no-ext-diff --no-textconv -- > "$PATCH_FILE"

while IFS= read -r -d '' RELATIVE_PATH; do
  test -f "$TASK_PATH/$RELATIVE_PATH"
  test ! -L "$TASK_PATH/$RELATIVE_PATH"
  set +e
  "${PROMOTION_GIT[@]}" -C "$TASK_PATH" diff --no-index --binary --no-ext-diff --no-textconv -- /dev/null "$RELATIVE_PATH" >> "$PATCH_FILE"
  DIFF_EXIT=$?
  set -e
  test "$DIFF_EXIT" -eq 1
done < <("${PROMOTION_GIT[@]}" -C "$TASK_PATH" ls-files --others --exclude-standard -z --)

test -s "$PATCH_FILE"
sha256sum "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" apply --check "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" apply --stat "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" apply "$PATCH_FILE"
```

The sanitized Git environment above intentionally matches the executor's promotion-candidate renderer so global or system Git configuration cannot change the patch bytes. Compare the printed SHA-256 with the candidate's reported `patch_sha256` before applying.

The fail-closed exit-code check deliberately rejects empty untracked files because Git cannot represent them as an unstaged content diff. Add content or handle an intentionally empty file manually after review.

Review and test the source repository again:

```bash
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" diff --check
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" status --short
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" diff --stat
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" diff
```

Only a human may then create the source commit, push it, or open a pull request. Use the repository's normal branch, review and CI policy.

## Abort before commit

If source verification fails, reverse only the reviewed patch:

```bash
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" apply --reverse --check "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" apply --reverse "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" status --short
```

Do not use `git reset --hard` or discard unrelated changes.

## Retention and cleanup

Keep the task worktree and patch until the promoted change is committed, pushed and independently verified. Afterwards, either retain them as evidence or clean them up deliberately.

Before removing a task worktree, reverse its uncommitted patch and verify it is clean:

```bash
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" apply --reverse --check "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" apply --reverse "$PATCH_FILE"
test -z "$("${PROMOTION_GIT[@]}" -C "$TASK_PATH" status --porcelain)"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" worktree remove "$TASK_PATH"
```

Branch deletion is a separate destructive decision and is never automated by the executor.
