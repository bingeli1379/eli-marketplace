---
name: usage-audit
description: Audit the INVENTORY of installed MCP servers, tools, and skills against actual usage — what is installed and whether it ever fires, NOT the text or logic of a prompt file.
disable-model-invocation: true
---

# Audit the toolset against what you actually use

**What an unused skill costs is its description, on every single request.** A model-selectable skill's `description` sits in context permanently while its body is lazy-loaded, so one that never fires is a fixed per-turn charge for nothing — while a command-only one is not in context at all and costs nothing however long it is (step 1 keeps that straight) — and that charge, not the number of skills, is what a prune is ranked by: thirty terse skills can cost less than six verbose ones. The second cost, a wider field of candidates making the right one harder to select, is real and is not measurable from here — say so rather than putting a number on it.

**Zero usage means two opposite things, and conflating them is the failure this skill exists to avoid.** An MCP server nobody called is surplus. A skill nobody called is often a skill that never got the chance, in a plugin that is doing its job by another route — deleting that is a loss, and keeping it is not free either.

## 1. Collect

Run `${CLAUDE_PLUGIN_ROOT}/skills/usage-audit/scripts/collect.py` with python3. It emits one JSON object and does the whole measurement, including the per-plugin arithmetic: its header documents every source it reads and why no single one is sufficient.

**Use the script rather than composing the scan or the totals inline.** The sources are several and each is incomplete in a different way, and the arithmetic on top of them is identical every run — both are what a per-run improvisation gets wrong.

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

**Two populations charge nothing and are already reported as zero — never re-add them as a cost.** A command-only skill (`disable-model-invocation: true`, flagged `command_only`) is absent from the model's skill listing, so its description is never in context however long it is; it still fires as `/plugin:skill`, so it belongs in the Keep table at 0. A disabled plugin is dropped from the inventory entirely. Both were once the largest rows of a real run, and both were phantom.

**A row carries two costs and they answer different questions — `description_chars` / `approx_tokens` cover its never-fired skills ONLY, `all_description_chars` / `all_approx_tokens` cover every skill it ships.** The never-fired pair accumulates in the same branch that increments `never_fired`, so a plugin whose every skill fires reads 0 there while its `all_` pair reads its real weight. Step 3's plugin table prints both, ranks on the `all_` pair, and decides on the never-fired one. Neither is the field for a *skill*: one skill's own cost is `skills_installed[<name>].description_chars`, and the totals over every plugin and personal skill are `description_cost.all_chars` / `all_approx_tokens` — a population that excludes the built-in skills, which step 3 (report) states rather than leaves implied.

**If python3 is not on the machine, stop and say so.** Every verdict rests on this collection, and there is no reduced version of the run worth reporting.

**Read `unavailable` before anything else.** Every entry is a source that could not be read, and each one silently removes a verdict the report would otherwise be entitled to make. Carry those entries to step 3 (report) verbatim.

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

**An empty `other_components` means nothing recognised is on disk, never that the plugin ships nothing.** The three `*-lsp` plugins on this machine hold a README and a LICENSE and not one component directory, their capability declared somewhere no source here reads — so a zero-skill plugin earns a verdict from the one thing that is measurable, an MCP server it declares, and is otherwise left unjudged with its contents printed. Reading an empty list as an empty plugin retires all three on evidence never taken, which is this skill's opening failure with a new population to happen to.

**Among the plugins that ship skills, the split is whether anything in the plugin is reached at all — not who owns it.** Two routes are visible from here: another of its skills fires (`never_fired` < `installed`), or its own MCP server does (`server_calls` > 0). A route this run cannot see is the third state, **無判定** per the paragraph above, and never a **該處理** arrived at by default. Which remedy a **該處理** row deserves — uninstall it, or rewrite the descriptions where the source is the user's — is theirs to pick and needs no column.

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

**A recorded name with nothing installed behind it is out of scope — it gets no verdict and is never merged into one.** It may be a rename, a merge of two skills, or something from a marketplace that no longer exists, and nothing in the data tells those apart; matching by name guesses wrong in both directions at once, folding two live siblings together while missing a rename that changed the name. Counts are therefore read exactly as recorded, and a run diagnosing the current setup has nothing to say about a name that is no longer part of it. The cost is that a renamed item's history stays under its old name and its current count reads low — low and true beats complete and guessed.

**Read `project_exists` before `project_sessions` — a declaration whose project directory is absent is decided, not unmeasured.** The entry stayed behind in `~/.claude.json` while the path went away, and the server cannot load while it is gone, so its zero needs no window at all: verdict **Remove**, reported as dead config rather than an unused capability. Quote the path and say only that it is absent — a directory check cannot tell a deleted project from one sitting on an unmounted volume, and the user can. Only when the directory still stands does the paragraph below apply. Getting the order wrong is this skill's opening failure one level down: an unmeasured zero and an impossible one read identically, and a single directory check separates them.

**A project-scoped server whose project still exists is only loaded inside it, so its zero is only evidence when the window contains sessions from there.** At `project_sessions` 0 **or `null`** the server gets **no verdict**, and the two say different things: 0 means the window holds no session from that project, `null` here means the project is still there but no transcript directory for it could be found, so nothing was measured either way — a `null` with `project_exists` false is the paragraph above, not this one. State which of the two it was. Even with sessions behind it, a project-scoped server costs nothing in any other project, which makes removing it worth less than removing a `user` or `plugin` one; rank it below them and say so.

**MCP verdicts are given at server level, never per tool.** Which tools a server exposes is knowable only by connecting to it, so a tool that never fired cannot be distinguished from a tool that does not exist. A server that never fired can be, and that is the actionable unit anyway.

Records one verdict per item. Step 3 (report) prints them.

## 3. Report

**Written in Traditional Chinese; identifiers stay in English** — server and skill names, scopes, paths, and every command, which are copied and run rather than read.

**Emit exactly these five blocks, in this order, with these headings and these columns.** The shape is fixed so two runs can be compared, and so no count is printed without a header saying what it counts — a bare number beside a name is unreadable, and the reader cannot tell a total from a remainder. A block with no rows still prints, with its count as 0. **Keep the column count as written**: every added column narrows the rest until cells wrap, and a wrapped table is harder to read than the prose it replaced, so a fact belonging to an existing column goes in that cell, not in a new one.

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

**Spent, wasted, and recoverable are three different figures, and printing fewer than three makes the report lie in a predictable direction.** The never-fired total counts every silent skill, including the ones inside plugins the reader is keeping for another route — those are unreachable by uninstalling anything and come back only by rewriting a description that fails to trigger. Printing the wasted figure alone reads as the saving, so the reader budgets for it, acts, and recovers a fraction; the difference between the two is the part that needs different work, which is why it is stated as its own clause rather than left to subtraction. Whether the recoverable figure is worth acting on is theirs to judge, and it is the one number this whole report exists to produce.

### The built-in skills the collection cannot see

**They charge every turn and the totals exclude them, so the cost block's first line states how many there are and stops.** They ship inside the CLI binary rather than on disk, which is why the collection reports them under `unavailable` instead of counting them — but the run itself is looking at them: they are in this session's own skill listing, the same way a connected server's `instructions` block is, and counting the entries in that listing is a count, not an estimate. **Give the number and no token figure.** A description's length read off a listing is the eyeballed `≈` that *The MCP table*'s instructions rule forbids, and it would land beside figures the script measured with nothing marking which is which. The user cannot uninstall a built-in anyway, so the number is there to keep the total honest, not to be acted on — never rank them, and never fold them into the prune arithmetic.

### The MCP table

**Every declared or observed server is a row, not only the silent ones** — a report of zeros cannot show a server sliding toward zero, and that one (a handful of calls where its neighbours have hundreds) is the row worth seeing before it dies. The zero rows are what the reader acts on, so bold them; the rest is the standing state they are read against.

**The bolded rows plus the sentence under the table ARE step 2's **Remove** verdict — this table is where it lands, and it is the only place it appears.** Name the zero-call servers there (or 「無」), and name separately every server that got **no verdict** with which case it was, since a bolded row and an unbolded one look identical for a server nobody could measure. Without that sentence the verdict step 2 recorded is never printed, and a table sorted by call count reads as a ranking with nothing decided.

**`宣告在哪` names the config surface, never a path that repeats another column.** A plugin's `installPath` is where its body is installed, which `plugin@marketplace` already says in the form the reader can act on — printing it again spends the widest cell in the table on a duplicate. Derive the cell:

| scope | 宣告在哪 |
|---|---|
| `user` | `~/.claude.json` |
| `project` | the project path in `where` — this is the one scope where the path IS the fact, since it says which project loads it |
| `plugin` | plugin 自帶 `<the row's `manifest` value>` — quote what the collection recorded rather than picking between `.mcp.json` and `mcp.json`, which is a coin flip printed as a fact |
| `observed` | 只在 transcripts 看得到 — say the declaration cannot be read, and never invent a path for it |

**A zero-call row names how to remove it — a command or a named action, never a category.** The scope alone leaves the reader to find out which project or which plugin, and the sentence under the table is where it lands, one line per zero-call server. Derive it:

| scope | 怎麼移除 |
|---|---|
| `user` | `claude mcp remove <server> -s user` |
| `project`, directory still there | `cd <where> && claude mcp remove <server> -s project` |
| `project`, directory gone | drop that project's whole entry from `~/.claude.json`'s `projects` map — `claude mcp remove` needs a directory to run in, so the command above cannot execute at all here. Name the key, say to back the file up first, and leave the edit to the user |
| `plugin` | uninstall `<plugin>@<marketplace>` via `/plugin` — a plugin-shipped server has no config entry to edit, and the marketplace is half the address: the same plugin name can exist in more than one |
| `observed` | seen only in transcripts and declared nowhere the run can read: say the removal path is unknown rather than guessing one |

**The table carries no token column, and the line under it states what a silent server actually charges rather than calling the whole cost unmeasurable.** "This collection cannot see it" reads as zero, and zero is wrong — a server's per-turn charge has two halves, and only one of them is out of reach:

- **Its `instructions` block is a fixed per-turn charge of exactly the same shape as a skill `description`**, and for a server the running session is connected to, that text is sitting in this session's own context — so it is not unmeasured, it is measurable by the run itself, converting with `description_cost.chars_per_token`. The collection never sees this block (it reaches the session from the server at connect time, not from any config file on disk), which is a limit of the script, not of the report. **The character count must come from an actual count of that text, never from reading its length off by eye** — an eyeballed number lands in the report beside figures the script measured, with nothing marking which is which, and a fabricated `≈` is what this whole audit exists not to print.
  **Three states, and collapsing any two is this skill's own opening failure in miniature:** measured (give the figure); **connected but shipping no `instructions` block at all** — a real zero, so say it charges nothing for instructions rather than that it was not measured; and not connected this session — not measured, and name which servers that covers. **What separates those last two is whether that server's tools are present in this session at all** — loaded, or listed as deferred: tools present with no instructions text is the real zero, no tools at all is not connected. The absence of instructions text is never the answer on its own, because that is the one reading under which the two states are indistinguishable.
- **Its tool schemas are knowable only by connecting**, which is the same limit that keeps verdicts at server level, and under tool deferral they are not even a per-turn charge until something fetches them. Never estimate this half, and never fetch schemas just to size them — that charges the context for the measurement and reports a number the server does not normally cost.

### The two skill tables, and why they are two

**Table 3 excludes `rollup_by_plugin`'s `(personal)` row** — that population is table 2, expanded one row per `skills_installed` entry whose `owner` is `(personal)`, with its heading total taken from that same rollup row. Leaving it in prints that whole population's tokens twice under two different headings, and the reader has no way to tell it is one population counted once. It gets no **保留** / **該處理** verdict either — those are per plugin, and table 2 has no 建議 column — so table 3's heading total is the sum of the rows it actually shows.

**Local skills are expanded per skill; marketplace skills are rolled up per plugin.** They are pruned differently, and that is the whole reason for the split: a local skill is a directory the user owns and removes one at a time, so the actionable unit is the skill; a plugin arrives and leaves whole, so listing its skills individually offers a cut nobody can make. Never merge the two tables, and never expand a plugin's skills into rows.

**Table 2 sorts by call count, then by cost within a tie** — it is read as "what am I actually using", so the used ones lead and the silent tail sorts by what it charges. Its header line carries the population's total and the never-fired share of it, since a per-skill table alone never adds up to the number the reader wants.

**A zero-skill plugin is a row like any other, and its `每輪 ≈tokens` of 0 is a real zero.** It ships no description, so it charges nothing per turn while still being installed — the 建議 cell is the whole content of that row, and 無判定 rows say there what could not be measured. Dropping them because they cost nothing puts the plugin inventory back to listing only the plugins that happen to ship skills, which is what left a 41-call server out of the table entirely.

**Table 3 carries two token columns and needs both.** `all_approx_tokens` is how heavy the plugin is — that is what it ranks on. `approx_tokens` is the never-fired share, which is what pruning would actually save. One alone answers neither question: a large total tells you nothing about whether to act, and a large wasted share tells you nothing about the plugin's weight. Label them `每輪 ≈tokens` and `沒在用的 ≈tokens`. Its **該處理** rows are the same set the cost block's third number sums, so that number is printed there and never restated here — and these rows have to add up to it, since a headline the table below contradicts is worse than either number alone.

**Table 4 repeats rows from tables 2 and 3, deliberately.** Those two are ranked by cost within their own population; this one ranks the whole inventory by use, which is the only view that puts the most-called skill next to a once-called one. Its `每輪 ≈tokens` is that one skill's own cost — `skills_installed[<name>].description_chars` ÷ `chars_per_token` — because firing is not the same as being worth its charge: a skill called once or twice on a fat description is the one place a rewrite pays.

**One row per item, never two merged into one.** Rows sharing a count are still separate rows: merging costs the reader one-line-per-thing scanning and hides which name the number belongs to.

**Counts from different sources are not comparable and never share a column.** Skill counts are lifetime totals from the harness's own counter; MCP counts come from transcripts, which rotate, so they cover a recent window. State which is which wherever a number appears.

**The report recommends; it changes nothing.** Disabling a server or uninstalling a plugin edits the user's setup and is theirs to run.
