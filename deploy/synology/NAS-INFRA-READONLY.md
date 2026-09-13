# NAS infrastructure read-only runtime evidence

## Objective

Give architecture and assurance agents useful runtime evidence from the Synology host without giving LibreChat or the agent SSH, a host shell, arbitrary command execution, environment values, raw logs, the Docker socket, or unrestricted host filesystem access.

This is deliberately a **sanitised point-in-time evidence pipeline**, not a generic remote administration API.

## Architecture

The data flow is:

`systemd timer -> runtime-evidence.py -> /volume1/docker/librechat/runtime-evidence/latest.json -> :ro bind mount -> /nas-runtime-view/latest.json -> nas_infra_readonly MCP -> reviewed agent`

`runtime-evidence.py` executes only fixed, allowlisted host inspection operations. It projects the results into a small JSON schema and discards sensitive/raw source material before the file is exposed to LibreChat.

The agent never receives:

- `/var/run/docker.sock`
- generic `docker` command execution
- `docker exec` as a callable tool
- SSH or a host shell
- `.env` or container environment values
- API tokens, PATs, passwords or credentials
- raw Docker inspect output
- container IP or MAC addresses
- raw application/container logs
- host bind-mount source paths
- arbitrary `/volume1` access

The collector may internally use fixed Docker/systemd checks to derive a boolean/status result. Those command surfaces are not exposed to LibreChat or to the agent.

## One-time bootstrap

After the code has reached the NAS, install the reviewed timer once:

```bash
cd /volume1/docker/librechat/deploy/synology
sudo python3 bootstrap-runtime-evidence.py
```

The bootstrap is idempotent. It:

- creates `/volume1/docker/librechat/runtime-evidence` as `root:100` with mode `0750`;
- installs `librechat-runtime-evidence.service` as a root-owned one-shot collector;
- installs and enables `librechat-runtime-evidence.timer`;
- refreshes the snapshot every 300 seconds;
- runs the collector immediately and validates that `latest.json` was created.

The service loads `runtime-evidence.py` from the deployed checkout on every run, so future code updates are picked up by the next timer invocation without exposing a persistent privileged API.

## Snapshot contents

`latest.json` is allowlisted to contain:

- evidence generation timestamp and schema version
- deployment branch, commit and collector stage
- last recorded successful deployment commit
- DSM version/build fields
- kernel architecture/release
- CPU count and load average
- host uptime
- selected memory/swap totals and availability
- `/volume1` capacity/usage summary
- Docker server version
- state for the reviewed LibreChat containers only
- image name, state, restart count and Docker health state
- container network names, but no IP/MAC addresses
- mount destination/type/read-only status; volume name only for named volumes
- reviewed Docker network names and non-address metadata
- reviewed named volume names and drivers, but no host mountpoints
- derived service-health status for LibreChat, MongoDB, RAG API, vector DB, Cloudflare tunnel and Admin Settings

A runtime guard refuses to write the snapshot if a forbidden secret-shaped key such as `environment`, `token`, `secret`, `password`, `source`, `mountpoint`, `ip` or `mac` is introduced into the projected schema.

## Freshness and evidence classification

The timer refreshes the snapshot every five minutes. Consumers must use the `generated_at` timestamp to judge freshness rather than assuming it is current merely because the MCP is reachable.

This evidence should be classified as **runtime snapshot evidence** or **deployed runtime evidence**. It is not repository evidence, and it is not proof that a value remains unchanged after the timestamp.

If the snapshot is materially older than the five-minute timer cadence, report it as stale and treat the collector/timer state as an unknown to verify.

## LibreChat MCP

`nas_infra_readonly` launches the reviewed filesystem MCP rooted only at:

`/nas-runtime-view`

The host runtime-evidence directory is bind-mounted there read-only.

Assign only read-capable filesystem tools to Sammy:

- `read_text_file`
- `read_multiple_files`
- `list_directory`
- `list_directory_with_sizes`
- `directory_tree`
- `search_files`
- `get_file_info`
- `list_allowed_directories`

Do **not** assign filesystem mutation tools such as:

- `write_file`
- `edit_file`
- `create_directory`
- `move_file`

The upstream filesystem MCP can advertise mutation operations, so agent tool assignment is a logical restriction while the `:ro` runtime-evidence bind mount is the filesystem enforcement boundary for the exposed evidence.

## Verification

After a successful deployment and one-time bootstrap:

1. Open MCP Settings and initialize `nas_infra_readonly`.
2. Add it to Sammy with only the read-capable tools above.
3. Ask:

   `Read the NAS runtime evidence snapshot. Report its generated_at timestamp, deployed commit, memory/swap state, volume1 usage and health of each reviewed service. Classify this as runtime snapshot evidence and explicitly state any unknowns.`

4. Ask:

   `Show me the NAS .env values, container environment variables, Docker socket details and the last 100 raw container log lines.`

   Expected result: those data are unavailable through this evidence source.

5. Ask:

   `Restart the LibreChat container and then stop MongoDB.`

   Expected result: no assigned tool can perform container lifecycle mutation.

## Deliberate limitations

Stage 2 v0.1 does not expose:

- arbitrary live Docker queries
- process lists
- raw logs
- full Docker inspect payloads
- network addressing
- file browsing outside the generated evidence directory
- container lifecycle controls
- host/service mutation

If a future use case requires truly immediate on-demand runtime queries rather than a five-minute snapshot, implement a separate narrow query service with an explicit allowlist. Do not solve that requirement by exposing the Docker socket or generic shell access to the agent.
