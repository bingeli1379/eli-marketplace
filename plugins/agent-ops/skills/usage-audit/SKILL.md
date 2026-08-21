---
name: usage-audit
description: Audit installed MCP servers, tools, and skills against actual usage. Triggers on 盤點/檢查/清理 裝了哪些 MCP、tool 太多、哪些沒在用、哪些可以刪掉、skill 沒被觸發、skill 叫不出來、環境太肥, which MCP servers can I remove, is anything I installed unused, tool usage stats, prune my setup, audit my toolset, why does my skill never fire, or /usage-audit. Audits the INVENTORY — what is installed and whether it ever fires — NOT the text or logic of a prompt file.
---

# Audit the toolset against what you actually use

**What an unused item costs is its description, on every single request.** A skill's `description` sits in context permanently while its body is lazy-loaded, so one that never fires is a fixed per-turn charge for nothing — and that charge, not the number of skills, is what a prune is ranked by: thirty terse skills can cost less than six verbose ones. The second cost, a wider field of candidates making the right one harder to select, is real and is not measurable from here — say so rather than putting a number on it.

**Zero usage means two opposite things, and conflating them is the failure this skill exists to avoid.** An MCP server nobody called is surplus. A skill nobody called is often a skill that never got the chance, in a plugin that is doing its job by another route — deleting that is a loss, and keeping it is not free either.

## 1. Collect

Run `${CLAUDE_PLUGIN_ROOT}/skills/usage-audit/scripts/collect.py` with python3. It emits one JSON object and does the whole measurement, including the per-plugin arithmetic: its header documents every source it reads and why no single one is sufficient.

**Use the script rather than composing the scan or the totals inline.** The sources are several and each is incomplete in a different way, and the arithmetic on top of them is identical every run — both are what a per-run improvisation gets wrong.

The keys the steps below consume:

| key | what it holds |
|---|---|
| `rollup_by_plugin` | per plugin: `installed`, `never_fired`, `description_chars`, `approx_tokens`, `server_calls`, `shadowed_by_personal` — already sorted by cost |
| `description_cost` | the totals, the never-fired share of them, and `orphan_recorded_names` |
| `mcp_servers` | per server: `count`, `scope`, `where`, and for a plugin server its `plugin` and `marketplace`; for a project server, `project_sessions` |
| `skills_used` / `skills_installed` | per-name call counts, and each installed skill's owner and `description_chars` |
| `coverage`, `unavailable` | the window read, and the sources that could not be |

**If python3 is not on the machine, stop and say so.** Every verdict rests on this collection, and there is no reduced version of the run worth reporting.

**Read `unavailable` before anything else.** Every entry is a source that could not be read, and each one silently removes a verdict the report would otherwise be entitled to make. Carry those entries to step 3 (report) verbatim.

**If `skills_installed` or `mcp_servers` came back empty, that population is reported usage-only** — ranked by what was used, with no claim about what is unused, and the report says so.

Records that JSON. Steps 2 (classify) and 3 (report) both read it.

## 2. Classify

| Verdict | Applies to | Condition |
|---|---|---|
| **Keep** | skill | It fired |
| **Remove** | MCP server | Zero calls |
| **該處理** | plugin | Its skills never fired, and nothing else in it is reached either |
| **保留** | plugin | Its skills never fired, but the plugin is reached another way |

**The split is whether anything in the plugin is reached at all — not who owns it.** Two routes count as reached: another of its skills fires (`never_fired` < `installed`), or its own MCP server does (`server_calls` > 0). Which remedy a **該處理** row deserves — uninstall it, or rewrite the descriptions where the source is the user's — is theirs to pick and needs no column.

The signals, first match wins:

| What the data shows | Recommend |
|---|---|
| `shadowed_by_personal` > 0 and every skill silent | **該處理** — two copies of one skill are installed and only one can win |
| `never_fired` < `installed` | **保留** — the plugin is reached, so the silent ones are a matching problem, not an unwanted capability |
| No skill fires but `server_calls` > 0 | **保留** — the capability is in use through its tools; its skills are what fail to trigger |
| No skill fires and `server_calls` is 0 | **該處理** — nothing in it has ever been reached by any route |

State each recommendation with the signal that produced it. Acting on it is the user's — they read the same table and may know a capability is kept deliberately for work that has not come up yet.

**A recorded name with nothing installed behind it is out of scope — it gets no verdict and is never merged into one.** It may be a rename, a merge of two skills, or something from a marketplace that no longer exists, and nothing in the data tells those apart; matching by name guesses wrong in both directions at once, folding two live siblings together while missing a rename that changed the name. Counts are therefore read exactly as recorded, and a run diagnosing the current setup has nothing to say about a name that is no longer part of it. The cost is that a renamed item's history stays under its old name and its current count reads low — low and true beats complete and guessed.

**A project-scoped server is only loaded inside its own project, so its zero is only evidence when the window contains sessions from there.** At `project_sessions` 0 **or `null`** the server gets **no verdict**, and the two say different things: 0 means the window holds no session from that project, `null` means no transcript directory for it could be found at all, so nothing was measured either way. State which of the two it was. Even with sessions behind it, a project-scoped server costs nothing in any other project, which makes removing it worth less than removing a `user` or `plugin` one; rank it below them and say so.

**MCP verdicts are given at server level, never per tool.** Which tools a server exposes is knowable only by connecting to it, so a tool that never fired cannot be distinguished from a tool that does not exist. A server that never fired can be, and that is the actionable unit anyway.

Records one verdict per item. Step 3 (report) prints them.

## 3. Report

**Written in Traditional Chinese; identifiers stay in English** — server and skill names, scopes, paths, and every command, which are copied and run rather than read.

**Emit exactly these four sections, in this order, with these headings and these columns.** The shape is fixed so two runs can be compared, and so no count is printed without a header saying what it counts — a bare number beside a plugin name is unreadable, and the reader cannot tell a total from a remainder. A section with no rows still prints, with its count as 0. **Keep the column count as written**: every added column narrows the rest until cells wrap, and a wrapped table is harder to read than the prose it replaced — a fact belonging to an existing column goes in that cell, not in a new one.

```
## Coverage
- transcripts：<n> 個檔，<YYYY-MM-DD> 到 <YYYY-MM-DD>
- 讀不到的來源：<每一筆 unavailable，以及它讓哪個判定做不出來 | 無>
- 只在歷史裡、沒有安裝對應的名字：<`description_cost.orphan_recorded_names`> 個（不判定）
- 每輪固定成本：全部 skill description ≈<總 tokens>，其中從沒觸發的佔 ≈<tokens>（<百分比>）

## Remove — 零呼叫的 MCP server（<n>）
| server | scope | 宣告在哪 | 影響範圍 | 怎麼移除 |
<一個拿不到判定的 server 仍然列在這張表上，`怎麼移除` 寫「不判定」加上原因；把它漏掉會讓讀者以為它有在用>

## 從沒觸發過的 skill（<n> / 共 <m> 個已安裝）— 依每輪成本排序
| plugin@marketplace | 從沒觸發的 skill 數 | 每輪 ≈tokens | 建議 | 依據 |

## Keep — 有觸發過的 skill（<n>）
| skill | 呼叫次數（終生累計，照記錄的名字） |
```

**The never-fired section lists only plugins with `never_fired` > 0**, in `rollup_by_plugin` order, and closes with the total ≈tokens of its **該處理** rows — that sum is what the reader would save, and it is the one number the whole report exists to produce.

**Every `怎麼移除` cell is a command or a named action, never a category.** The scope alone leaves the reader to find out which project or which plugin. Derive it:

| scope | 怎麼移除 |
|---|---|
| `user` | `claude mcp remove <server> -s user` |
| `project` | `cd <where> && claude mcp remove <server> -s project` |
| `plugin` | uninstall `<plugin>@<marketplace>` via `/plugin` — a plugin-shipped server has no config entry to edit, and the marketplace is half the address: the same plugin name can exist in more than one |
| `observed` | seen only in transcripts and declared nowhere the run can read: say the removal path is unknown rather than guessing one |

The `影響範圍` cell says where the server is actually loaded — everywhere for `user` and `plugin`, only inside `<where>` for `project` — because that, not the zero, decides whether removing it is worth doing.

**One row per item, never two merged into one.** Rows sharing a count are still separate rows: merging costs the reader one-line-per-thing scanning and hides which name the number belongs to.

**Counts from different sources are not comparable and never share a column.** Skill counts are lifetime totals from the harness's own counter; MCP counts come from transcripts, which rotate, so they cover a recent window. State which is which wherever a number appears.

**The report recommends; it changes nothing.** Disabling a server or uninstalling a plugin edits the user's setup and is theirs to run.
