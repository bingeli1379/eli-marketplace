# Changelog

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
