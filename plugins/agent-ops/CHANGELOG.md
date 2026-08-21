# Changelog

## [0.1.0] - 2026-08-21

### Added
- `/usage-audit` — tells you which of your installed MCP servers and skills have actually been used, and what to do about each one: keep it, remove it, rewrite its description, drop it, or ignore it because it is already gone.
- An unused skill is not treated like an unused server. A server nobody called is surplus and gets disabled; a skill nobody called usually never got the chance, so the suggestion is to fix how it is described rather than delete it. Which one applies is the single question the run asks you, grouped by plugin so you answer once per plugin instead of once per skill.
- MCP results are per server, never per tool. Which tools a server offers can only be learned by connecting to it, so a tool that never fired cannot be told apart from one that does not exist — a server that never fired can be, and that is what you would switch off anyway.
- Every server is reported with where it was declared, because that decides how you remove it: your own config, a project's config, a plugin that ships it, or — for one that appears only in your history and is declared nowhere — a plain statement that the removal path is unknown, instead of a guess.
- Counts from different places are never mixed into one column. Skill counts are lifetime totals kept by Claude Code itself; MCP counts come from your session transcripts, which get rotated away, so they describe a recent window. The report says which is which next to every number.

### Notes
- Requires `python3`. Without it the run stops and says so — every verdict rests on the collection step, so there is no partial result worth showing you.
