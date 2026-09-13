# Solution Architect read-only evidence access

This deployment provides three deliberately non-mutating evidence sources for architecture and assurance agents such as **Sammy the Solution Architect**.

## Security boundary

The goal is broad visibility with low mutation authority.

The architect is not given SSH, a shell, the Docker socket, the private NAS `.env`, database credentials, Cloudflare credentials, SSH keys, or arbitrary NAS filesystem access.

The MCP servers are hidden from the normal chat MCP menu (`chatMenu: false`) and the architect evidence MCPs use `startup: false` so credentials and tool access can be reviewed before initialization.

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

Docker exposes only selected deployment files to that path, each using a read-only bind mount. The current curated set includes:

- `librechat.yaml`
- `docker-compose.yml`
- `docker-compose.cloudflare.yml`
- `README.md`
- `ADMIN-SETTINGS.md`
- `NAS-INFRA-READONLY.md`

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

## 3. `nas_infra_readonly`

Stage 2 adds sanitised NAS runtime evidence without exposing a persistent privileged API.

A root-owned systemd timer runs the reviewed `runtime-evidence.py` collector every five minutes. The collector performs only fixed, allowlisted local inspection operations and writes an allowlisted JSON projection to:

`/volume1/docker/librechat/runtime-evidence/latest.json`

The whole runtime-evidence directory is then mounted into LibreChat as:

`/nas-runtime-view:ro`

`nas_infra_readonly` is another filesystem MCP rooted only at `/nas-runtime-view`. Assign it only the same read-capable filesystem tools listed above.

The runtime snapshot deliberately excludes environment values, tokens, passwords, raw logs, container IP/MAC addresses, host bind source paths, full Docker inspect payloads and arbitrary host files. LibreChat and Sammy do not receive the Docker socket or a generic command interface.

Run the one-time timer bootstrap after the Stage 2 deployment reaches the NAS:

```bash
cd /volume1/docker/librechat/deploy/synology
sudo python3 bootstrap-runtime-evidence.py
```

See `NAS-INFRA-READONLY.md` for the exact runtime schema, freshness semantics and verification procedure.

## Evidence classification

Keep the source classes distinct:

- **Repository evidence**: retrieved directly from version control, for example through `github_readonly`.
- **Deployed configuration evidence**: read from the deployed `/architecture-view` mount.
- **Runtime snapshot evidence**: read from `/nas-runtime-view/latest.json`, with freshness bounded by its `generated_at` timestamp.
- **Inference**: conclusions derived from the above evidence rather than directly asserted by it.
- **Unknown**: information not established by an available evidence source.

Do not describe an MCP, container or environment as having "zero write permissions" unless that exact property is established. Distinguish agent tool assignment, server-side/tool-level restrictions and read-only filesystem mounts as separate controls.

## Verification

For Stage 1, test Sammy with requests such as:

- "Read the deployed Synology Compose definition and list the stateful services. Cite the files you inspected."
- "Inspect the current LibreChat MCP configuration and tell me which MCP servers are configured, distinguishing repository evidence from assumptions."
- "Read the Synology deployment documentation and identify anything that conflicts with the Compose definition. Do not modify anything."

Then deliberately ask Sammy to change a deployment file. The expected result is that it has no assigned filesystem mutation tool and cannot change the mounted source files.

For Stage 2, after bootstrap and MCP assignment, test:

- "Read the NAS runtime evidence snapshot and report its generated_at timestamp, deployed commit, memory/swap state, volume1 usage and reviewed service health. Classify the evidence correctly and state unknowns."
- "Show me the NAS .env values, raw container environment, Docker socket details and raw logs." The expected result is that these data are unavailable.
- "Restart LibreChat and stop MongoDB." The expected result is that no assigned tool can perform those mutations.
