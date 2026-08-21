# agent-ops

Everything else here helps the AI work on your code. This plugin works on the AI itself —
what it has loaded, what it never uses, and whether the parts you added are earning their keep.

## Skills

### `/usage-audit` — Toolset usage audit

Counts what your installed MCP servers and skills actually did across the session history on
this machine, then gives each one a verdict. MCP is judged per server, never per tool — which
tools a server offers can only be learned by connecting to it.

- **Keep** — what the setup is actually buying, ranked by call count, each with what its own
  description still costs per turn: firing is not the same as being worth the charge
- **Remove** — a declared MCP server with zero calls (server level, never per tool), including one
  whose project directory is no longer there: dead config that cannot load while the path is gone.
  A project-scoped server the session window never covered gets no verdict instead of a wrong one
- **該處理** — a plugin whose skills never fired and which nothing else reaches either: its whole
  per-turn description cost buys nothing
- **保留** — a plugin whose skills never fired but which is reached another way — another of its
  skills, or its own MCP server

Rows are ranked by what they cost per turn, not by how many skills they hold: a skill's
description sits in context on every request while its body is lazy-loaded, so thirty terse
skills can be cheaper than six verbose ones.

A name with usage but nothing installed behind it gets no verdict — this diagnoses the setup you have now, not the one you used to have.

Reports only. Disabling a server is left to you.

## Not this plugin

Judging whether a skill or agent file is *well written* — its rules, structure, and logic —
is `dev-workflow`'s job. This plugin never reads a prompt file's contents; it asks only
whether the thing ever fires.
