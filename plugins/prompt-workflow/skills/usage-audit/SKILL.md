---
name: usage-audit
description: Audit the INVENTORY of installed MCP servers, tools, and skills against actual usage — what is installed and whether it ever fires, NOT the text or logic of a prompt file.
disable-model-invocation: true
---

# Audit the toolset against what you actually use

**What an unused skill costs is its description, on every single request.** A model-selectable skill's `description` sits in context permanently while its body is lazy-loaded; a command-only one is not in context at all and costs nothing however long it is (step 1 keeps that straight). That charge, not the number of skills, is what a prune is ranked by. The second cost — a wider field of candidates making the right one harder to select — is real and not measurable from here; say so rather than putting a number on it.

**Zero usage means two opposite things, and conflating them is the failure this skill exists to avoid.** An MCP server nobody called is surplus. A skill nobody called is often one that never got the chance, in a plugin doing its job by another route.

## 1. Collect

Run `${CLAUDE_PLUGIN_ROOT}/skills/usage-audit/scripts/collect.py` with python3. It emits one JSON object and does the whole measurement, including the per-plugin arithmetic: its header documents every source it reads and why no single one is sufficient.

**Use the script rather than composing the scan or the totals inline** — several incomplete sources plus fixed arithmetic is exactly what a per-run improvisation gets wrong.

The keys the steps below consume:

| key | what it holds |
|---|---|
| `rollup_by_plugin` | an object keyed by `<plugin>@<marketplace>` (plus `(personal)` for the user's own skills), already ordered by descending TOTAL cost (`all_description_chars`) — iterate its `.items()`, it is not a list. **Every enabled plugin has a row, including one that ships no skill at all**, so the table is the whole plugin inventory rather than the skill-shipping part of it. Each row: `installed`, `fired`, `never_fired`, `never_fired_command_only`, `shadowed_by_personal`, `server_calls`, `declares_mcp`, `path_exists`, `other_components`, and two costs — `all_description_chars` / `all_approx_tokens` for the whole plugin, `description_chars` / `approx_tokens` for its never-fired share |
| `description_cost` | the totals, the never-fired share of them, and `chars_per_token` (the divisor every ≈tokens figure in the report converts with) |
| `mcp_servers` | per server: `count`, `scope`, `where`, and for a plugin server its `plugin`, `marketplace`, and the `manifest` filename its declaration was read from; for a project server, `project_exists` and `project_sessions` |
| `skills_used` / `skills_installed` | both keyed by skill name, and both holding an object rather than a bare number: a used name gives `count` and `last_used_ms`, an installed one gives `owner`, `description_chars`, and `command_only` |
| `disabled_plugins` | `<plugin>@<marketplace>` entries switched off in settings. Installed, loading nothing, costing nothing — excluded from every count above, so the report spends only a count on them, in the clause qualifying the fixed-cost figure |
| `coverage` | `transcript_files`, and the window as `window_start` / `window_end`, already `YYYY-MM-DD` — taken from the messages, not from file mtimes, and printed as given rather than reformatted. `files_without_timestamp` is how many transcripts contributed no date to it |
| `unavailable` | the sources that could not be read |

**Two populations charge nothing and are already reported as zero — never re-add them as a cost.** A command-only skill (`disable-model-invocation: true`, flagged `command_only`) is absent from the model's skill listing, so its description is never in context; it still fires as `/plugin:skill`, so it belongs in the Keep table at 0. A disabled plugin is dropped from the inventory entirely. Both were once the largest rows of a real run, and both were phantom.

**A row carries two costs — `description_chars` / `approx_tokens` cover its never-fired skills ONLY, `all_description_chars` / `all_approx_tokens` every skill it ships.** A plugin whose every skill fires reads 0 in the first pair and its real weight in the second. Step 3's plugin table prints both, ranks on the `all_` pair, decides on the never-fired one. One skill's own cost is `skills_installed[<name>].description_chars`; the totals over every plugin and personal skill are `description_cost.all_chars` / `all_approx_tokens`, a population that excludes the built-in skills — step 3 (report) states that.

**If python3 is not on the machine, stop and say so.** Every verdict rests on this collection, and there is no reduced version of the run worth reporting.

**Read `unavailable` before anything else** — each entry is a source that could not be read and a verdict the report is not entitled to make. Carry them to step 3 (report) verbatim.

**If `skills_installed` or `mcp_servers` came back empty, that population is reported usage-only** — ranked by what was used, with no claim about what is unused, and the report says so.

Records that JSON. Steps 2 (classify) and 3 (report) both read it.

## 2. Classify

| Verdict | Applies to | Condition |
|---|---|---|
| **Keep** | skill | It fired |
| **Remove** | MCP server | Zero calls — except a project-scoped server whose project is still there and whose window holds no session from it, which gets no verdict |
| **該處理** | plugin | Its skills never fired, and nothing else measurable in it is reached either |
| **保留** | plugin | Its skills never fired, but the plugin is reached another way |
| **無判定** | plugin | It ships no skill and no MCP server, so it holds nothing this run can count — or its install path is gone |

**An empty `other_components` means nothing recognised is on disk, never that the plugin ships nothing** — an `*-lsp` plugin holds a README and a LICENSE and declares its capability where no source here reads. A zero-skill plugin earns a verdict from the one measurable thing, an MCP server it declares, and is otherwise left unjudged with its contents printed.

**Among the plugins that ship skills, the split is whether anything in the plugin is reached at all.** Two routes are visible: another of its skills fires (`never_fired` < `installed`), or its own MCP server does (`server_calls` > 0). A route this run cannot see is **無判定**, never a **該處理** by default. Which remedy a **該處理** row deserves — uninstall, or rewrite the descriptions — is the user's and needs no column.

The signals, first match wins:

| What the data shows | Recommend |
|---|---|
| `path_exists` false | **無判定** — nothing loads from a directory that is absent, so no skill of its could ever have fired; the finding is the stale `installed_plugins.json` entry, quoted with its path, not an unused capability |
| `installed` == 0, `declares_mcp`, `server_calls` > 0 | **保留** — it ships no skill, and the one capability it does ship is in use |
| `installed` == 0, `declares_mcp`, `server_calls` == 0 | **該處理** — the only thing it ships is measurable and has never been called |
| `installed` == 0, not `declares_mcp` | **無判定** — it holds nothing this run can count; print what `other_components` lists (or that the directory holds only documentation) instead of ranking it |
| `never_fired` == 0 | **保留** — every skill in it fires; the row is the standing state, with nothing to prune |
| `never_fired_command_only` == `never_fired` | **保留** — every silent skill here is command-only, so the row already costs 0 and pruning it saves nothing; say that instead of ranking it |
| `shadowed_by_personal` > 0 and every skill silent | **該處理** — two copies of one skill are installed and only one can win |
| `never_fired` < `installed` | **保留** — the plugin is reached, so the silent ones are a matching problem, not an unwanted capability |
| No skill fires but `server_calls` > 0 | **保留** — the capability is in use through its tools; its skills are what fail to trigger |
| No skill fires and `server_calls` is 0 | **該處理** — nothing this run can see has ever been reached; where `other_components` is non-empty, name what it lists, so the reader weighs the route that went unmeasured rather than reading the row as an empty plugin |

State each recommendation with the signal that produced it. Acting on it is the user's — they read the same table and may know a capability is kept deliberately for work that has not come up yet.

**A recorded name with nothing installed behind it is out of scope — no verdict, never merged into one.** It may be a rename, a merge, or a vanished marketplace, and nothing in the data tells those apart. Counts are read exactly as recorded; a renamed item's history stays under its old name and its current count reads low — low and true beats complete and guessed.

**Read `project_exists` before `project_sessions` — a declaration whose project directory is absent is decided, not unmeasured.** The entry stayed in `~/.claude.json` while the path went away, so the server cannot load: verdict **Remove**, reported as dead config. Quote the path and say only that it is absent — a directory check cannot tell a deleted project from an unmounted volume, and the user can.

**A project-scoped server whose project still exists is only loaded inside it, so its zero is only evidence when the window contains sessions from there.** At `project_sessions` 0 **or `null`** it gets **no verdict**, and the two differ: 0 means no session from that project in the window, `null` means no transcript directory for it could be found — state which. A project-scoped server costs nothing in any other project, so removing it is worth less than a `user` or `plugin` one; rank it below them and say so.

**MCP verdicts are given at server level, never per tool.** Which tools a server exposes is knowable only by connecting, so a never-fired tool cannot be told from a nonexistent one; a never-fired server can, and is the actionable unit.

Records one verdict per item. Step 3 (report) prints them.

## 3. Report

**Written in Traditional Chinese; identifiers stay in English** — server and skill names, scopes, paths, and every command, which are copied and run rather than read.

**Emit exactly these five blocks, in this order, with these headings and these columns** — fixed so two runs can be compared and no count is printed without a header saying what it counts. A block with no rows still prints, with its count as 0. **Keep the column count as written**: a fact belonging to an existing column goes in that cell, not in a new one.

```
## 每輪成本
- 固定花費：plugin 與個人 skill 的 description ≈<`all_approx_tokens`> tokens／輪（已排除 <`disabled_plugins` 的個數> 個在設定裡停用的 plugin，它們不載入，所以不計成本）；另有 <n> 支 built-in skill 同樣每輪計費，這裡數不到，不含在內
- 沒觸發過的佔 ≈<`never_fired_approx_tokens`>（<`never_fired_pct`>%）
- 其中真的砍得掉的 ≈<步驟 2（classify）判為 **該處理** 的每個 plugin，其 `approx_tokens` 加總——表 3 那幾列就是它，兩邊要對得起來>；差額 ≈<沒觸發過的減去砍得掉的> 卡在要留下的 plugin 裡，只有重寫 description 救得回來
- <每一筆 unavailable，以及它讓哪個判定做不出來 | 沒有讀不到的來源>

## 1. MCP server（<n>）— 依呼叫次數排序
| server | 呼叫次數 | scope | plugin@marketplace | 宣告在哪 |
<`mcp_servers` 全部列出，不是只列零呼叫的；零呼叫那列整列加粗>
<表後一句：這些次數涵蓋的視窗是 <`coverage.window_start`> 到 <`coverage.window_end`>（<`transcript_files`> 個 transcript，照訊息時間戳；<`files_without_timestamp`> 個沒有時間戳、沒進區間時一併說）——零呼叫要能當證據，靠的就是這段視窗。接著寫零呼叫的是哪幾個（或「無」），以及拿不到判定的是哪幾個加上原因>
<再一段：這張表沒有 token 欄，但成本不是零。逐一寫出每個零呼叫、且這個 session 已經連上的 server，它常駐的 instructions 區塊實際多大（<chars> chars ≈<tokens> tokens／輪，用 `description_cost.chars_per_token` 換算）；有連上但本身沒有 instructions 區塊的，寫「沒有 instructions，這半是真的零」，沒連上的才寫「沒量到」並點出是哪幾個；tool schema 那半一律不估>

## 2. Local skill — 不屬於任何 marketplace（<n> 支，≈<tokens>／輪）
`~/.claude/skills/` 底下你自己放的。沒在用的 <k> 支佔 ≈<tokens>（<百分比>）。
| skill | 呼叫次數 | 每輪 ≈tokens |

## 3. Plugin@marketplace（<n> 個，≈<tokens>／輪）
| plugin@marketplace | skill（有用／共） | 每輪 ≈tokens | 沒在用的 ≈tokens | 建議 |

## 4. Keep — 有觸發過的 skill（<n>）
| skill | 呼叫次數（終生累計，照記錄的名字） | 每輪 ≈tokens |
```

### Why the cost block carries three numbers

**Spent, wasted, and recoverable are three different figures; printing fewer than three makes the report lie in a predictable direction** — the wasted figure alone reads as the saving, while the part inside plugins the reader keeps for another route comes back only by rewriting a description. The recoverable figure is the one number this report exists to produce.

### The built-in skills the collection cannot see

**They charge every turn and the totals exclude them, so the cost block's first line states how many there are and stops.** They ship inside the CLI binary, so the collection reports them under `unavailable`; the run itself sees them in this session's own skill listing, and counting those entries is a count, not an estimate. **Give the number and no token figure** — a length read off a listing by eye is the `≈` *The MCP table* forbids. Never rank them, never fold them into the prune arithmetic.

### The MCP table

**Every declared or observed server is a row, not only the silent ones** — a server sliding toward zero is the row worth seeing before it dies. Bold the zero rows.

**The bolded rows plus the sentence under the table ARE step 2's **Remove** verdict — the only place it appears.** Name the zero-call servers there (or 「無」), and separately every server that got **no verdict** with which case it was.

**`宣告在哪` names the config surface, never a path that repeats another column.** Derive the cell:

| scope | 宣告在哪 |
|---|---|
| `user` | `~/.claude.json` |
| `project` | the project path in `where` — the one scope where the path IS the fact, since it says which project loads it |
| `plugin` | plugin 自帶 `<the row's `manifest` value>` — quote what the collection recorded rather than picking between `.mcp.json` and `mcp.json` |
| `observed` | 只在 transcripts 看得到 — say the declaration cannot be read, and never invent a path for it |

**A zero-call row names how to remove it — a command or a named action, never a category**, one line per zero-call server in the sentence under the table. Derive it:

| scope | 怎麼移除 |
|---|---|
| `user` | `claude mcp remove <server> -s user` |
| `project`, directory still there | `cd <where> && claude mcp remove <server> -s project` |
| `project`, directory gone | drop that project's whole entry from `~/.claude.json`'s `projects` map — `claude mcp remove` needs a directory to run in. Name the key, say to back the file up first, and leave the edit to the user |
| `plugin` | uninstall `<plugin>@<marketplace>` via `/plugin` — a plugin-shipped server has no config entry to edit, and the same plugin name can exist in more than one marketplace |
| `observed` | seen only in transcripts and declared nowhere the run can read: say the removal path is unknown rather than guessing one |

**The table carries no token column, and the line under it states what a silent server actually charges rather than calling the whole cost unmeasurable.** A server's per-turn charge has two halves:

- **Its `instructions` block is a fixed per-turn charge of the same shape as a skill `description`**, and for a server this session is connected to, that text is in this session's own context — measurable by the run, converting with `description_cost.chars_per_token`; the collection never sees it (it arrives from the server at connect time, not from any file on disk). **The character count must come from an actual count of that text, never from reading its length off by eye** — a fabricated `≈` beside script-measured figures is what this audit exists not to print. **Three states, never collapsed**: measured (give the figure); **connected but shipping no `instructions` block** — a real zero, say it charges nothing for instructions; not connected this session — not measured, name which servers. **What separates the last two is whether that server's tools are present in this session at all** — loaded or listed as deferred: tools present with no instructions text is the real zero, no tools at all is not connected.
- **Its tool schemas are knowable only by connecting**, and under tool deferral are not a per-turn charge until something fetches them. Never estimate this half, and never fetch schemas just to size them.

### The two skill tables, and why they are two

**Table 3 excludes `rollup_by_plugin`'s `(personal)` row** — that population is table 2, expanded one row per `skills_installed` entry whose `owner` is `(personal)`, with its heading total from that same rollup row; leaving it in counts one population twice. It gets no **保留** / **該處理** verdict — those are per plugin — so table 3's heading total is the sum of the rows it shows.

**Local skills are expanded per skill; marketplace skills are rolled up per plugin** — a local skill is removed one at a time, a plugin arrives and leaves whole. Never merge the two tables, never expand a plugin's skills into rows.

**Table 2 sorts by call count, then by cost within a tie**; its header line carries the population's total and the never-fired share.

**A zero-skill plugin is a row like any other, and its `每輪 ≈tokens` of 0 is a real zero** — the 建議 cell is the whole content of that row, and 無判定 rows say there what could not be measured. Dropping them puts the inventory back to listing only skill-shipping plugins, which once left a 41-call server out of the table entirely.

**Table 3 carries two token columns and needs both.** `all_approx_tokens` is how heavy the plugin is and what it ranks on; `approx_tokens` is the never-fired share, what pruning would save. Label them `每輪 ≈tokens` and `沒在用的 ≈tokens`. Its **該處理** rows are the set the cost block's third number sums, so they have to add up to it.

**Table 4 repeats rows from tables 2 and 3, deliberately** — the only view that puts the most-called skill next to a once-called one. Its `每輪 ≈tokens` is that one skill's own cost, `skills_installed[<name>].description_chars` ÷ `chars_per_token`, because a skill called once or twice on a fat description is where a rewrite pays.

**One row per item, never two merged into one.**

**Counts from different sources are not comparable and never share a column.** Skill counts are lifetime totals from the harness's counter; MCP counts come from transcripts, which rotate, so they cover a recent window. State which is which wherever a number appears.

**The report recommends; it changes nothing.** Disabling a server or uninstalling a plugin edits the user's setup and is theirs to run.
