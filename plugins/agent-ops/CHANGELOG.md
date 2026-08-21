# Changelog

## [0.1.0] - 2026-08-21

### Added
- `/usage-audit` — measures which installed MCP servers and skills actually fire, and gives each one a verdict: keep, remove, fix its description, drop it, or already gone.
- Collection runs as a bundled script rather than a scan composed per run. No single source is sufficient: the harness's own `skillUsage` counter holds lifetime totals but no zero-count entry, so it can never name an unused skill; `pluginUsage` has zero-count entries but stops at the plugin; `toolUsage` covers built-ins only and was observed stale; transcripts are the only per-MCP-tool record but rotate, so they cover a recent window. The installed side comes off disk, counting only the newest cached version of each plugin — the cache keeps every previous version, and counting the tree as-is multiplies each skill by its version history.
- Zero usage is split into two opposite verdicts. An MCP server nobody called is surplus and gets disabled; a skill nobody called usually never got the chance, so it gets its trigger surface rewritten instead of deleted. Which one applies is the single question the run asks, grouped by plugin.
- MCP verdicts are given per server, never per tool. Which tools a server exposes is knowable only by connecting to it, so an unused tool cannot be told apart from one that does not exist — while an unused server can.
- A plugin-shipped MCP server appears in transcripts as `plugin_<plugin>_<server>` and in the manifest as `<server>`. Both names are resolved to one, without which every plugin MCP server reads as undeclared and unused at the same time.
- Usage history with nothing installed behind it is reported separately as **Gone** and resolved first, so a renamed item is not counted twice — once as history nobody can act on, once as an installed item that looks new.
