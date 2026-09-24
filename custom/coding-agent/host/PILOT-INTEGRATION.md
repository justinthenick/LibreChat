# Software Engineering Pilot maintenance integration

The Pilot has sixteen explicitly named MCP tools: the existing nine coding tools
and seven explicit `coding_maintenance` tools. The maintenance additions are
`executor_health`, `repository_status`, `task_inventory`, `executor_logs`,
`fresh_repository_status`, `preview_cleanup` and `cleanup_task`.
Persisted IDs use `<operation>_mcp_coding_maintenance`. No wildcard, source working-tree refresh or restart tool is assigned. Cleanup
is the only assigned mutation and requires operator retirement, eligibility and
a confirmed single-use ticket. Existing skill and ownership
permissions remain unchanged.

The previous Pilot instructions required a worktree for every task, including
status checks. Version 0.1.11 routes maintenance inspections directly to these
maintenance tools and explicitly stops if maintenance is unavailable. Coding tasks keep
their existing worktree workflow.

## Deployment gates

1. Install and validate executor 0.1.8 and host package 0.1.3 with a pinned image.
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
   configuration reload. Startup reconciliation assigns and validates all sixteen
   tool IDs and both MCP server names. Preserve existing agent ownership.
5. In the running LibreChat instance, confirm MCP discovery returns the seven
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

`maintenance-inspection-3c5e6683` was removed separately with explicit user approval
after a verified full backup on 24 September 2026. Its Git branch and state record
were retained. That operator action is not a cleanup acceptance fixture; never
recreate or target that identity during later acceptance tests.
