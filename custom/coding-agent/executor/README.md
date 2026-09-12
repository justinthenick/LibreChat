# LibreChat coding executor v0.1

This service gives a LibreChat Agent a deliberately narrow coding surface without granting access to the NAS Docker socket or the host filesystem.

## Security boundary

- Every task is created as a separate Git worktree and `agent/<task-id>` branch.
- All paths are resolved beneath that task worktree.
- Edits are unified diffs checked by `git apply --check` before application.
- Shell strings are never evaluated. Only test, lint, build and `git diff --check` command prefixes are accepted.
- Child commands receive a minimal environment that excludes the MCP bearer token.
- The MCP server has no commit, push, delete-task, package-install or Docker tools.
- The container runs non-root, drops Linux capabilities, has no Docker socket and has CPU, memory and process limits.

Repository code is still untrusted code. Running its tests can execute repository-controlled scripts inside this container. Keep secrets out of mounted repositories and review the final diff before committing or pushing.

## Host layout

Use the Linux filesystem inside WSL, not `/mnt/c`, for the repositories and worktrees:

```text
~/coding-agent/
  repos/     # manually cloned repositories that the Agent may access
  tasks/     # executor-created worktrees
  executor/  # this directory
```

## Initial setup

1. Copy `.env.example` to `.env`.
2. Generate the token with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.
3. Replace the example address with the Windows host LAN address that the Synology NAS can reach.
4. Create `repos` and `tasks`, clone only approved repositories under `repos`, and run `docker compose -f compose.example.yaml up -d --build`.
5. Confirm `curl http://127.0.0.1:8765/health` returns `{"status":"ok","version":"0.1.0"}`.

Do not expose port 8765 to the public internet. Permit it only from the NAS address in Windows Firewall.

## LibreChat configuration (after host validation)

The Synology config should use a Streamable HTTP server with a static bearer header and a single private-address exemption:

```yaml
mcpSettings:
  allowedAddresses:
    - '${CODING_EXECUTOR_HOST}:${CODING_EXECUTOR_PORT}'

mcpServers:
  coding_executor:
    type: streamable-http
    url: 'http://${CODING_EXECUTOR_HOST}:${CODING_EXECUTOR_PORT}/mcp'
    headers:
      Authorization: 'Bearer ${CODING_EXECUTOR_TOKEN}'
    requiresOAuth: false
    chatMenu: false
    serverInstructions: true
    timeout: 300000
```

Keep this server out of ordinary chat. Attach it only to the reviewed Software Engineering Agent after the executor and connectivity checks pass.
