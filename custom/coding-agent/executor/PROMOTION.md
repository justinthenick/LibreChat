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
EXPECTED_PATCH_SHA256=<approved-candidate-patch-sha256>
```

Then verify the boundaries in Bash under the same sanitized Git environment used for promotion rendering:

```bash
set -euo pipefail

PROMOTION_GIT=(
  env -i
  PATH=/usr/local/bin:/usr/bin:/bin
  HOME=/tmp/coding-agent-home
  XDG_CONFIG_HOME=/tmp/coding-agent-home/.config
  LANG=C.UTF-8
  GIT_CONFIG_NOSYSTEM=1
  GIT_CONFIG_GLOBAL=/dev/null
  GIT_OPTIONAL_LOCKS=0
  GIT_TERMINAL_PROMPT=0
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
[[ "$EXPECTED_PATCH_SHA256" =~ ^[0-9a-f]{64}$ ]]
test -z "$("${PROMOTION_GIT[@]}" -C "$REPO_PATH" status --porcelain --ignore-submodules=none)"
test "$("${PROMOTION_GIT[@]}" -C "$REPO_PATH" rev-parse HEAD)" = "$("${PROMOTION_GIT[@]}" -C "$TASK_PATH" rev-parse HEAD)"
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" diff --check --ignore-submodules=none
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" status --short --ignore-submodules=none
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" diff --stat --ignore-submodules=none
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" diff --ignore-submodules=none
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" ls-files --others --exclude-standard
while IFS= read -r -d '' RELATIVE_PATH; do
  test -f "$TASK_PATH/$RELATIVE_PATH"
  test ! -L "$TASK_PATH/$RELATIVE_PATH"
done < <("${PROMOTION_GIT[@]}" -C "$TASK_PATH" ls-files --others --exclude-standard -z --)
if "${PROMOTION_GIT[@]}" -C "$TASK_PATH" diff --raw --ignore-submodules=none HEAD -- | grep -Eq '(^| )160000( |$)'; then
  echo "submodule changes are not supported by this promotion procedure" >&2
  exit 1
fi
```

Stop if the source repository is dirty, the two HEAD commits differ, the task diff is malformed, an untracked path is not a regular non-symlink file, or the observed change differs from the agent's report.

Run the repository's required tests in the same controlled environment used by the executor. Do not promote solely because the agent claimed they passed.

## Apply after human approval

Create a temporary complete patch from the reviewed task. Tracked changes are exported first, followed by every untracked regular file:

```bash
PATCH_FILE="$(mktemp /tmp/coding-agent-promotion.XXXXXX.patch)"
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" diff --binary --no-ext-diff --no-textconv --ignore-submodules=none -- > "$PATCH_FILE"

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
read -r ACTUAL_PATCH_SHA256 _ < <(sha256sum "$PATCH_FILE")
printf 'patch_sha256=%s\n' "$ACTUAL_PATCH_SHA256"
test "$ACTUAL_PATCH_SHA256" = "$EXPECTED_PATCH_SHA256"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" apply --check "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" apply --stat "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" apply "$PATCH_FILE"
```

The `env -i` wrapper above runs every review/export/apply Git command under an allowlisted environment matching the executor's promotion renderer, so inherited Git environment variables and user/system configuration cannot change the reviewed paths or patch bytes. The block requires the approved candidate `patch_sha256` up front and aborts before any apply command if the regenerated patch digest differs.

The fail-closed exit-code check deliberately rejects empty untracked files because Git cannot represent them as an unstaged content diff. Add content or handle an intentionally empty file manually after review.

Review and test the source repository again:

```bash
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" diff --check --ignore-submodules=none
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" status --short --ignore-submodules=none
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" diff --stat --ignore-submodules=none
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" diff
```

Only a human may then create the source commit, push it, or open a pull request. Use the repository's normal branch, review and CI policy.

## Abort before commit

If source verification fails, reverse only the reviewed patch:

```bash
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" apply --reverse --check "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" apply --reverse "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" status --short --ignore-submodules=none
```

Do not use `git reset --hard` or discard unrelated changes.

## Retention and cleanup

Keep the task worktree and patch until the promoted change is committed, pushed and independently verified. Afterwards, either retain them as evidence or clean them up deliberately.

Before removing a task worktree, reverse its uncommitted patch and verify it is clean:

```bash
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" apply --reverse --check "$PATCH_FILE"
"${PROMOTION_GIT[@]}" -C "$TASK_PATH" apply --reverse "$PATCH_FILE"
test -z "$("${PROMOTION_GIT[@]}" -C "$TASK_PATH" status --porcelain --ignore-submodules=none)"
"${PROMOTION_GIT[@]}" -C "$REPO_PATH" worktree remove "$TASK_PATH"
```

Branch deletion is a separate destructive decision and is never automated by the executor.
