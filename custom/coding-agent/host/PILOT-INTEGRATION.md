# Software Engineering Pilot maintenance integration

The Pilot has thirteen explicitly named MCP tools: the existing nine coding tools
and four read-only `coding_maintenance` tools. The maintenance additions are
`executor_health`, `repository_status`, `task_inventory` and `executor_logs`.
Persisted IDs use `<operation>_mcp_coding_maintenance`. No wildcard, refresh,
cleanup or restart tool is assigned to the Pilot. Existing skill and ownership
permissions remain unchanged.

The previous Pilot instructions required a worktree for every task, including
status checks. Version 0.1.10 routes maintenance inspections directly to these
four tools and explicitly stops if maintenance is unavailable. Coding tasks keep
their existing worktree workflow.

## Deployment gates

1. Install and validate executor 0.1.7 and host package 0.1.2 with a pinned image.
   These add missing read-only response fields: installed executor version,
   cached upstream ahead/behind/divergence and stale worktree registrations.
   `freshness: not_fetched` explicitly means no live remote fetch was performed.
2. Configure a private maintenance connection restricted to the NAS. Keep the
   separate maintenance token in protected environment files. Do not expose the
   endpoint publicly or reuse the coding token.
3. Set `CODING_MAINTENANCE_HOST`, `CODING_MAINTENANCE_PORT` (8767), and
   `CODING_MAINTENANCE_TOKEN` in the protected Synology environment. The renderer
   materializes host/port in both the URL and private-address exemption; it never
   writes the token into runtime YAML. Match the broker's explicit allowed host.
4. Deploy the updated YAML, renderer, Compose configuration, Pilot manifest and
   seeder together. Recreate the LibreChat API service so its environment and
   configuration reload. Startup reconciliation assigns and validates all thirteen
   tool IDs and both MCP server names. Preserve existing agent ownership.
5. In the running LibreChat instance, confirm MCP discovery returns the four
   maintenance names and the persisted Pilot includes their exact IDs. Confirm
   the logged-in Pilot user can invoke them. Registration alone is not acceptance.

## Required live acceptance

Start a fresh conversation with **Software Engineering Pilot** and send:

> Perform a read-only maintenance inspection. Report executor health and version;
> the LibreChat source branch, HEAD, dirty state, cached ahead/behind/divergence and
> freshness limitation; and coding worktree clean/dirty/stale inventory. Use the
> constrained maintenance tools directly. Do not create a task or use coding
> executor tools. If maintenance tools are unavailable, report that failure and stop.

Capture the actual conversation tool-call trace, not only the answer or a direct
broker probe. Require successful calls to `executor_health_mcp_coding_maintenance`,
`repository_status_mcp_coding_maintenance` and
`task_inventory_mcp_coding_maintenance`, and **zero `create_task` calls**. Preserve
the conversation ID and trace as acceptance evidence. A failed/missing call, a
fallback coding call, or missing trace is not a pass.

## Accidental inspection worktree

`maintenance-inspection-3c5e6683` was inspected after the failed run. It is dirty
(the policy includes ignored and untracked files), cleanup is disabled, and it has
no retirement record. It must remain intact. Do not discard its contents or bypass
the 24-hour retirement gate to make an acceptance test pass.
