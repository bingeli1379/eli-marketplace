---
name: usage-audit
description: Audit installed MCP servers, tools, and skills against actual usage. Triggers on 盤點/檢查/清理 裝了哪些 MCP、tool 太多、哪些沒在用、哪些可以刪掉、skill 沒被觸發、skill 叫不出來、環境太肥, which MCP servers can I remove, is anything I installed unused, tool usage stats, prune my setup, audit my toolset, why does my skill never fire, or /usage-audit. Audits the INVENTORY — what is installed and whether it ever fires — NOT the text or logic of a prompt file.
---

# Audit the toolset against what you actually use

An installed MCP server or skill costs something on every request and returns nothing unless it fires. This skill measures what fires, compares it against what is installed, and gives each item one verdict.

**Zero usage means two opposite things, and conflating them is the failure this skill exists to avoid.** An MCP server nobody called is surplus. A skill nobody called is usually a skill that never got the chance — its description does not match how the user actually asks. One gets removed, the other gets fixed.

## 1. Collect the inventory and the usage

Run `${CLAUDE_PLUGIN_ROOT}/skills/usage-audit/scripts/collect.py` with python3. It emits one JSON object; its header documents every source it reads and why each one alone is insufficient. The keys the steps below consume are `skills_installed`, `skills_used`, `mcp_servers` (each server's call count and where it was declared), `coverage`, and `unavailable`.

**If python3 is not on the machine, stop and say so.** Every verdict rests on this collection, and there is no reduced version of the run worth reporting.

Use the script rather than composing the scan inline. The sources are several, each incomplete in a different way, and the combination is exactly what a per-run improvisation gets wrong.

Records that JSON. Steps 2 (resolve Gone), 3 (classify), and 4 (report) all read it.

**Read `unavailable` before anything else.** Every entry there is a source that could not be read, and each one silently removes a verdict the report would otherwise be entitled to make. Carry those entries to step 4 (report) verbatim.

**If `skills_installed` or `mcp_servers` came back empty, that population is reported usage-only** — ranked by what was used, with no claim about what is unused, and the report says so.

## 2. Resolve what is already gone

An entry in `skills_used` with no counterpart in `skills_installed` is history for something no longer installed — renamed, or removed. Where an old and a current name are plainly the same thing, combine their counts under the current name.

**Do this before step 3 (classify).** Left unresolved, a renamed item is counted twice: once as history nobody can act on, once as an installed item that looks brand new.

Records the resolved pairs and the leftover orphans. Step 3 excludes both from its zero-usage sets.

## 3. Classify

| Verdict | Condition | Action |
|---|---|---|
| **Keep** | Installed, used | none |
| **Remove** | MCP server in `mcp_servers`, zero calls | disable it |
| **Fix** | Installed skill, never invoked, and the user still wants what it does | its description is not matching — rewrite the trigger surface |
| **Drop** | Installed skill, never invoked, and the need is gone | uninstall it |
| **Gone** | Usage history with nothing installed behind it | already removed or renamed — excluded from the above |

**MCP verdicts are given at server level, never per tool.** Which tools a server exposes is knowable only by connecting to it, so a tool that never fired cannot be distinguished from a tool that does not exist. A server that never fired can be, and that is the actionable unit anyway.

Separating **Fix** from **Drop** needs the one thing no source supplies: whether the user still wants what an unused skill does. Ask once, with the never-invoked skills grouped by plugin — a plugin whose every skill is unused is one question, not twenty.

Records one verdict per item. Step 4 (report) prints them.

## 4. Report

Print, in this order:

1. **Coverage** — transcript file count, the date range from `coverage`, and every `unavailable` entry with the verdict it cost.
2. **Remove** — each zero-call server with the `source` the script gave it, because how it is removed follows from that: `user` and `project` are config edits at their own scope, `plugin` means uninstalling the plugin that ships it, and `observed` is a server seen only in transcripts and declared in none of those places — name it and say the removal path is unknown rather than guessing one.
3. **Fix / Drop** — grouped by plugin, with each skill's install path.
4. **Gone** — history names with nothing behind them, and what each is now.
5. **Keep** — used items by call count, so the reader sees what the setup is buying.

**Counts from different sources are not comparable, and the report never puts them in one column.** Skill counts are lifetime totals from the harness's own counter; MCP counts come from transcripts, which rotate, so they cover a recent window only. State which is which wherever a number appears.

**The report recommends; it changes nothing.** Disabling a server or uninstalling a plugin edits the user's setup and is theirs to run.
