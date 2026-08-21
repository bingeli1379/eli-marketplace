# agent-ops

Everything else here helps the AI work on your code. This plugin works on the AI itself —
what it has loaded, what it never uses, and whether the parts you added are earning their keep.

## Skills

### `/usage-audit` — Toolset usage audit

Counts what your installed MCP servers, tools, and skills actually did across the session
history on this machine, then gives each one a verdict.

- **Keep** — what the setup is actually buying, ranked by call count
- **Remove** — declared MCP server with zero calls (server level, never per tool)
- **Fix** — installed skill that never fired, where the need exists and the description is not matching
- **Drop** — installed skill that never fired and whose need is gone
- **Gone** — history under a name that no longer exists (renamed or already removed)

Reports only. Disabling a server is left to you.

## Not this plugin

Judging whether a skill or agent file is *well written* — its rules, structure, and logic —
is `dev-workflow`'s job. This plugin never reads a prompt file's contents; it asks only
whether the thing ever fires.
