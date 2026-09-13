# Synology NAS infrastructure read-only inspection

Status: Stage 2 implementation for **Sammy the Solution Architect**.

## Objective

Expose live, sanitized Synology/LibreChat runtime evidence without giving an architecture agent generic shell access, SSH, `docker exec`, container lifecycle controls, arbitrary file reads, environment-variable access, or the Docker socket.

## Architecture

The design deliberately separates the privileged host inspection boundary from the LibreChat Agent boundary:

`Sammy -> LibreChat MCP stdio bridge -> group-restricted Unix socket -> host read-only inspection worker -> fixed host/Docker queries`

### Host worker

`nas-infra-readonly-worker.py` runs as a root-owned systemd service because the Synology Docker CLI is host privileged. Its authority is constrained in code rather than passed through to the Agent:

- listens only on a Unix-domain socket;
- socket is group-restricted to the existing Docker/LibreChat group (`gid 100`);
- accepts only an explicit action allowlist;
- invokes fixed argv command lists with `shell=False`;
- exposes no generic command, shell, file-read, environment-read, Docker exec, or lifecycle action;
- sanitizes Docker inspection output before returning it;
- never returns container environment variables, labels, command/entrypoint data, or host-side mount source paths;
- restricts detailed container inspection to the reviewed LibreChat service allowlist.

### MCP bridge

`nas-infra-readonly-mcp.py` runs inside the LibreChat container and implements only MCP `tools/list` and `tools/call` for the reviewed read-only actions. It receives no Docker socket and has no host shell.

The bridge connects to:

`/run/nas-infra-readonly/worker.sock`

The host state directory is mounted into the LibreChat container read-only.

## Exposed tools

- `get_host_summary`
- `get_memory_status`
- `get_disk_status`
- `get_docker_version`
- `list_containers`
- `inspect_container`
- `list_docker_networks`
- `list_docker_volumes`
- `get_service_health`
- `get_dsm_version`
- `get_deployment_state`

`inspect_container` accepts only these logical services:

- `api`
- `mongodb`
- `rag_api`
- `vectordb`
- `cloudflared`
- `admin_settings`

## Explicitly not exposed

- generic shell or command execution;
- SSH;
- arbitrary file reads;
- `.env` or other secret reads;
- container environment variables;
- Docker labels or command/entrypoint strings;
- host mount source paths;
- `docker exec`;
- container start/stop/restart/remove/create;
- Docker image pull/build;
- network or volume mutation;
- unrestricted Docker API/socket access;
- deployment writes.

## Evidence classification

Results from this MCP are **live runtime/host evidence**. They are not repository evidence and should not be described as such.

Repository evidence remains sourced from `github_readonly`. Curated deployed configuration-file evidence remains sourced from `architecture_files`.

## Initial verification prompts

After deployment, initialize `nas_infra_readonly`, add it to Sammy, and test:

1. `Inspect the live Synology host and summarize DSM version, memory, /volume1 usage and Docker Engine version. Classify this as live runtime evidence.`
2. `List the reviewed LibreChat containers and their current health. Do not use repository files to infer runtime state.`
3. `Inspect the api container and report image, state, restarts, networks, published ports and mount destinations. Confirm that environment variables and host mount source paths are not available.`
4. `Compare get_deployment_state with repository branch server/synology and explain whether the recorded successful deployment matches the checked-out host revision.`

Then deliberately ask:

`Restart the LibreChat container and change an environment variable.`

Expected result: the Agent has no such tool and cannot perform either mutation.
