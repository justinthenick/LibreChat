# Solution Architect read-only evidence access

This change adds two deliberately non-mutating evidence sources for architecture and assurance agents such as **Sammy the Solution Architect**.

## Security boundary

The goal is broad visibility with low mutation authority.

The architect is not given SSH, a shell, the Docker socket, the private NAS `.env`, database credentials, Cloudflare credentials, SSH keys, or arbitrary NAS filesystem access.

The two MCP servers are hidden from the normal chat MCP menu (`chatMenu: false`) and are configured with `startup: false` so credentials and tool access can be reviewed before initialization.

## 1. `github_readonly`

This uses GitHub's official remote MCP endpoint:

- endpoint: `https://api.githubcopilot.com/mcp/`
- toolset: `repos`
- server-side `X-MCP-Readonly: true`
- PAT supplied as a LibreChat custom user variable, not through the NAS `.env`

### Create the token

Create a **fine-grained GitHub personal access token** for the architect.

Recommended initial scope:

- Repository access: **Only select repositories**
- Repository: `justinthenick/LibreChat`
- Permissions: grant only read access required for repository inspection; do not grant write or administration permissions

The MCP server additionally enforces read-only mode, so a mistakenly exposed write-capable GitHub tool is filtered server-side.

### Initialize in LibreChat

After deployment/restart:

1. Open LibreChat's MCP Settings panel.
2. Open `github_readonly`.
3. Enter the fine-grained PAT in **GitHub read-only PAT**.
4. Save it and initialize/reinitialize the MCP server.
5. Confirm the available tools are read-only repository inspection tools.

When editing Sammy, add `github_readonly` only if repository evidence is needed.

## 2. `architecture_files`

This launches the official Model Context Protocol filesystem server with its allowed root fixed to:

`/architecture-view`

Docker exposes only these selected files to that path, each using a read-only bind mount:

- `librechat.yaml`
- `docker-compose.yml`
- `docker-compose.cloudflare.yml`
- `README.md`
- `ADMIN-SETTINGS.md`

The following are intentionally **not** exposed:

- `.env`
- API tokens or PATs
- Cloudflare tunnel tokens
- database credentials
- SSH keys
- `/var/run/docker.sock`
- arbitrary `/volume1` paths
- LibreChat user data, uploads, MongoDB data, or pgvector data

The upstream filesystem MCP advertises both read and write operations. The bind-mounted source files are read-only at the container boundary, but the architect should still be assigned **only the read-capable filesystem tools**.

Recommended tools for Sammy:

- `read_text_file`
- `read_multiple_files`
- `list_directory`
- `list_directory_with_sizes`
- `directory_tree`
- `search_files`
- `get_file_info`
- `list_allowed_directories`

Do **not** assign:

- `write_file`
- `edit_file`
- `create_directory`
- `move_file`

After deployment/restart, initialize `architecture_files` in MCP Settings and then add only the read tools above to Sammy.

## Verification

Before considering this stage complete, test Sammy with requests such as:

- "Read the deployed Synology Compose definition and list the stateful services. Cite the files you inspected."
- "Inspect the current LibreChat MCP configuration and tell me which MCP servers are configured, distinguishing repository evidence from assumptions."
- "Read the Synology deployment documentation and identify anything that conflicts with the Compose definition. Do not modify anything."

Then deliberately ask Sammy to change a deployment file. The expected result is that it has no assigned filesystem mutation tool and cannot change the mounted source files.

## Next stage: `nas-infra-readonly`

Do not give the architect generic SSH or shell access merely to inspect runtime state.

The preferred next stage is a dedicated read-only NAS infrastructure MCP exposing narrow queries such as:

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

It must not expose generic command execution, `docker exec`, container lifecycle mutations, file writes, or an unrestricted Docker socket.
