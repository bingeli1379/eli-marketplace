# Changelog

## [0.2.0] - 2026-08-22

### Changed
- The plugin is renamed from `agent-ops` to `prompt-workflow`. The old install name no longer resolves, so reinstall as `prompt-workflow@eli-marketplace` to keep getting updates. The new name pairs it with `dev-workflow`: that one works on your code, this one on the prompt files that steer the model.
- `/usage-audit` only runs when you type it. A passing remark about your setup no longer reaches it, because the run reads your whole session history and starting that is your call.

### Added
- Writing, auditing, and improving prompt files now happen here. `skill-authoring` (the write-time rules), `/review-skill` (the audit), and `/improve-skill` (feed a real-usage problem back into a skill's source) moved in from `dev-workflow`, alongside the shared authoring catalogue they both read.
- The authoring rules now cover who may invoke a skill: decide it before writing the description and say it with the frontmatter flags, because a "never auto-trigger" sentence written into a description binds nothing and is charged on every request.

### Fixed
- The plugin now appears in the Codex marketplace. It had never been registered there, so Codex users could not install it at all while everything looked fine on the Claude side.

## [0.1.1] - 2026-08-21

### Added
- A project's MCP server whose folder is no longer on your machine is now called out as leftover config rather than skipped as unmeasurable — it can never load again, and the report names the `~/.claude.json` entry to delete. It says only that the folder is missing, never why: a check like this cannot tell a deleted project from one on a drive you have not plugged in.
- The list of skills that DID fire now shows what each one's description costs you per turn. A skill you called once that carries a long description is the one worth rewriting, and a table of call counts alone made it look no different from a cheap one.

### Fixed
- A project's MCP server the history never covered could be recommended for removal off the summary table alone, retiring something on evidence that was never collected. The summary now carries the same exception the detailed rules already had.
- Removing a project server whose folder is gone used to hand you a command that cannot run, because it has to change into that folder first. You now get the config entry to edit instead.
- Every zero-call server is shown with where it actually loads, which now includes "nowhere" for one whose folder is missing.

## [0.1.0] - 2026-08-21

### Added
- `/usage-audit` — tells you which of your installed MCP servers and skills have actually been used, and what to do about each: keep it, disable the server, or deal with a plugin whose skills never fire.
- Rows are ranked by what they cost you per turn, not by how many skills a plugin holds. A skill's description sits in context on every request while its body is only loaded when it fires, so a skill that never fires is a fixed charge for nothing — and thirty terse skills can cost less than six verbose ones. The report opens with that total and how much of it is going to waste.
- An unused skill is not treated like an unused server. A server nobody called is surplus. A plugin whose skills never fired is only dead weight if nothing else in it is reached either — another of its skills, or its own MCP server — and the run decides that from the data instead of asking you.
- Every server is reported with where it was declared and the command that removes it: your own config, a named project's config, or the plugin that ships it. A plugin-shipped server names both the plugin and its marketplace, because the same plugin name can exist in more than one.
- MCP results are per server, never per tool. Which tools a server offers can only be learned by connecting to it, so a tool that never fired cannot be told apart from one that does not exist — a server that never fired can be, and that is what you would switch off anyway.
- A fixed report shape — four sections, named columns, one row per item — so two runs can be put side by side.

### Notes
- Requires `python3`. Without it the run stops and says so; every verdict rests on the collection step, so there is no partial result worth showing you.
- Anything the run could not measure is named rather than counted as zero: a server whose project has no session history gets no verdict at all, and a name in your history with nothing installed behind it is left alone instead of being guessed into a rename.
