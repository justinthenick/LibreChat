# Coding-agent self-development harness

This harness lets the **development** coding executor build and test a candidate version of itself without giving the executor Docker access.

## Trust boundary

Production remains unchanged:

- production executor keeps the original nine MCP tools;
- production has no self-development socket;
- production never receives the Docker socket;
- production does not build or start candidate images.

Self-development is opt-in and is intended only for the loopback-only development executor.

The development executor talks to a host worker through one Unix socket. The host worker owns Docker access and accepts only six fixed actions:

1. `build_candidate(task_id)`
2. `test_candidate(task_id)`
3. `start_candidate(task_id)`
4. `run_candidate_gate(task_id)`
5. `candidate_status()`
6. `destroy_candidate()`

The worker does not accept shell commands, Docker arguments, image names, paths, environment variables, ports, or arbitrary command lines from the agent.

## Expected local layout

```text
~/coding-agent/
  control/                 # stable executor source
  dev/
    repos/LibreChat/       # repository available to the dev executor
    tasks/                 # dev executor worktrees
    candidate/
      repos/               # fixture repositories for candidate runtime
      tasks/               # candidate runtime worktrees
      state.json           # private candidate state, including runtime token
    selfdev/
      worker.sock          # Unix socket, mode 0600
```

Recommended ports:

- production executor: `8765`
- development executor: `8766`, loopback only
- candidate executor: `8767`, loopback only

## Start the host worker

For one-off testing, run the worker from the same source revision used to build the development executor:

```bash
python3 ~/coding-agent/dev/repos/LibreChat/custom/coding-agent/executor/src/coding_executor/selfdev_host.py \
  --task-root ~/coding-agent/dev/tasks \
  --candidate-root ~/coding-agent/dev/candidate \
  --socket ~/coding-agent/dev/selfdev/worker.sock \
  --candidate-port 8767
```

For normal WSL operation, install the included user service instead:

```bash
bash ~/coding-agent/dev/repos/LibreChat/custom/coding-agent/executor/systemd/install-user-service.sh
```

The user service uses `systemctl --user`, restarts on failure, runs with `NoNewPrivileges=true`, and does not require root. The socket directory and socket remain private to the WSL user. The worker serializes requests so two candidate lifecycle operations cannot race each other.

## Connect only the dev executor

The worker must be running before Docker bind-mounts the socket.

Add these settings to the **development executor only**:

```yaml
environment:
  CODING_SELF_DEV_SOCKET: /run/selfdev/worker.sock

volumes:
  - "/home/<user>/coding-agent/dev/selfdev:/run/selfdev:ro"
```

Do not add either setting to production.

Mount the private socket **directory**, not the socket inode itself. The worker replaces the Unix socket when it restarts; a directory bind mount makes the replacement visible without recreating the dev container.

After recreating the development executor, its MCP tool list should contain the original nine tools plus the six self-development tools. Production should still expose only the original nine.

## Candidate lifecycle

The intended agent-controlled flow is:

```text
create_task
  -> inspect/edit executor source in the task worktree
  -> run_check for lightweight checks
  -> git_diff for reviewable evidence
  -> run_candidate_gate
  -> human review of diff + gate evidence
```

The individual `build_candidate`, `test_candidate`, `start_candidate`, `candidate_status` and `destroy_candidate` actions remain available for diagnosis and controlled manual testing. The normal self-improvement path should use `run_candidate_gate` because it performs the fixed lifecycle and always attempts cleanup.

`build_candidate` always builds from:

```text
<configured dev task root>/<task_id>/custom/coding-agent/executor
```

The image name is derived by the worker. The agent cannot choose another Docker build context or image.

`test_candidate` runs a fixed, network-disabled validation set:

- `python3 -m compileall -q /app/src`
- the complete executor unittest suite mounted read-only from the candidate task

`start_candidate` uses:

- one fixed candidate container name;
- loopback-only port `8767`;
- a worker-generated bearer token that is never returned by MCP status calls;
- a dedicated fixture repository root and task root;
- read-only container root;
- no extra Linux capabilities;
- `no-new-privileges`;
- bounded CPU, RAM and PID limits.

The candidate does not receive the Docker socket or production repositories.

### Atomic candidate gate

`run_candidate_gate(task_id)` is the preferred validation path. The agent supplies only the existing task ID. The worker performs, in order:

1. fixed candidate image build;
2. read-only compile validation with Python bytecode redirected to the `/tmp` tmpfs;
3. the complete executor unit-test suite with networking disabled;
4. candidate startup on loopback-only port `8767`;
5. authenticated MCP `server/discover` using the worker-held candidate token and the `2026-07-28` request metadata/header contract;
6. authenticated MCP `tools/list` and verification that the original nine coding tools are present while self-development tools are absent from the candidate runtime;
7. candidate status validation;
8. candidate container/image cleanup in a `finally` path.

The gate refuses to start if another candidate state/container already exists. Validation failures are returned as structured gate evidence and cleanup is still attempted.

## Human promotion gate

Self-development stops before source control promotion.

The agent still cannot:

- commit;
- push;
- merge;
- modify the production executor;
- deploy the candidate to production.

After candidate validation, use the existing [PROMOTION.md](./PROMOTION.md) process to review the complete diff. A human decides whether to commit, push, open/merge a PR, and later deploy.

## Rollback

`destroy_candidate()` removes the fixed candidate container and the image recorded in private candidate state. It does not modify the task worktree, the stable dev executor, or production.

If the candidate cannot start, the stable dev executor on `8766` remains available to repair the task.
