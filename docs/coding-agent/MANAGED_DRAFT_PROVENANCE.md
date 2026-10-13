# Managed draft publication base checks

Publish requires the draft's original source identity, positive base version, commit SHA
and SKILL.md blob SHA. Missing or invalid provenance returns HTTP 409 with instructions
to retain edits by renaming the old draft to an unused name, sync, create a fresh draft and
review/copy changes. Create Draft otherwise returns the existing deterministic-name draft,
so sync/Create Draft alone cannot refresh stale provenance. No credential lookup
or remote request occurs for invalid local provenance. Nothing silently adopts today's
source as the draft base; no edits are discarded or credentials changed. Draft editing
and Trial routes are unchanged, including for older drafts.

Before creating any GitHub blobs, trees, commits, refs or PRs, publication compares the
skill subtree at the recorded base commit, the synced publication commit and the selected
upstream commit. Exact repository/source/ref/path identity must agree. Git tree identity
binds all nested file names, modes and contents, so unchanged SKILL.md alone is insufficient.
Unrelated commits and sync version advancement can pass when the affected subtree is
unchanged. Missing history, truncated/ambiguous trees, path type changes or drift fail closed.
The existing successful response and publication workflow remain intact.

This checks stale bases; it does not make draft creation/copying atomic, pin Trial to a
whole-bundle snapshot, or authenticate a faulty storage adapter. The existing independent
Skill/SkillFile reads and mutable draft reads remain non-atomic. GitHub comparisons use
immutable commit/tree IDs captured for this attempt. The upstream branch may move after
validation, including while a PR is being created. No atomic compare-and-publish or merge
guarantee is claimed; review and sync remain required. Live provider calls are not part of
offline acceptance, which uses synthetic responses and verifies no writes on rejection.

Legacy policy is deliberately explicit: older drafts remain editable and trialable, but
Publish requires complete provenance. The error does not auto-refresh, overwrite, delete
or silently migrate them. Owners retain their edits for manual reconciliation into a fresh
draft. This behavior changes only publication of drafts whose original base cannot be
verified; it does not change permissions or token formats.
