# C003 operator procedure

## Prepare the private baseline

Clone the operator-approved private source baseline into the executor repository root using the public alias required by the benchmark:

```bash
git clone --branch main --single-branch <approved-private-source-url> \
  ~/coding-agent/repos/synology-magnet-c003
```

Verify the baseline outside the agent:

```bash
git -C ~/coding-agent/repos/synology-magnet-c003 status --short
git -C ~/coding-agent/repos/synology-magnet-c003 rev-parse HEAD
```

The status must be empty. Compare the commit locally with the operator-approved value. Do not publish the source URL or commit.

## Run

Give the Software Engineering Pilot the exact contents of `task-prompt.md`. Do not supplement the task with implementation hints during the run.

## Verify outside the agent

Substitute the returned task ID:

```bash
TASK_ID=<executor-task-id>
TASK_PATH="$HOME/coding-agent/tasks/$TASK_ID"
SOURCE_PATH="$HOME/coding-agent/repos/synology-magnet-c003"

test "$(git -C "$SOURCE_PATH" rev-parse HEAD)" = "$(git -C "$TASK_PATH" rev-parse HEAD)"
test -z "$(git -C "$SOURCE_PATH" status --porcelain)"
git -C "$TASK_PATH" diff --check
git -C "$TASK_PATH" status --short

docker exec librechat-coding-executor sh -lc \
  "cd '$TASK_PATH' && npm test"
```

Use the executor's final `git_diff` result to confirm both new files are included and the diff is not truncated. Score the run with `scorecard.md`.

Do not promote the benchmark task into the private source repository. Retain it until sanitized activation evidence is merged, then archive its complete patch and remove the clean worktree through the human-operated lifecycle command.
