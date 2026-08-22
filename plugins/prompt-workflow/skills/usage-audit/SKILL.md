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
| `rollup_by_plugin` | an object keyed by `<plugin>@<marketplace>` (plus `(personal)` for the user's own skills), already ordered by descending TOTAL cost (`all_description_chars`) — iterate its `.items()`, it is not a list. Each row: `installed`, `fired`, `never_fired`, `never_fired_command_only`, `shadowed_by_personal`, `server_calls`, and two costs — `all_description_chars` / `all_approx_tokens` for the whole plugin, `description_chars` / `approx_tokens` for its never-fired share |
| `description_cost` | the totals, the never-fired share of them, `chars_per_token` (the divisor every ≈tokens figure in the report converts with), and `orphan_recorded_names` |
| `mcp_servers` | per server: `count`, `scope`, `where`, and for a plugin server its `plugin`, `marketplace`, and the `manifest` filename its declaration was read from; for a project server, `project_exists` and `project_sessions` |
| `skills_used` / `skills_installed` | both keyed by skill name, and both holding an object rather than a bare number: a used name gives `count` and `last_used_ms`, an installed one gives `owner`, `description_chars`, and `command_only` |
| `disabled_plugins` | `<plugin>@<marketplace>` entries switched off in settings. Installed, loading nothing, costing nothing — excluded from every count above, so they appear in the report only as the Coverage line that says they were excluded |
| `coverage`, `unavailable` | the window read, and the sources that could not be |

**Two populations charge nothing and are already reported as zero — never re-add them as a cost.** A command-only skill (`disable-model-invocation: true`, flagged `command_only`) is absent from the model's skill listing, so its description is never in context however long it is; it still fires as `/plugin:skill`, so it belongs in the Keep table at 0. A disabled plugin is dropped from the inventory entirely. Both were once the largest rows of a real run, and both were phantom.

**A row carries two costs and they answer different questions — `description_chars` / `approx_tokens` cover its never-fired skills ONLY, `all_description_chars` / `all_approx_tokens` cover every skill it ships.** The never-fired pair accumulates in the same branch that increments `never_fired`, so a plugin whose every skill fires reads 0 there while its `all_` pair reads its real weight. Step 3's plugin table prints both, ranks on the `all_` pair, and decides on the never-fired one. Neither is the field for a *skill*: one skill's own cost is `skills_installed[<name>].description_chars`, and the inventory-wide totals are `description_cost.all_chars` / `all_approx_tokens`.

**If python3 is not on the machine, stop and say so.** Every verdict rests on this collection, and there is no reduced version of the run worth reporting.

**Read `unavailable` before anything else.** Every entry is a source that could not be read, and each one silently removes a verdict the report would otherwise be entitled to make. Carry those entries to step 3 (report) verbatim.

**If `skills_installed` or `mcp_servers` came back empty, that population is reported usage-only** — ranked by what was used, with no claim about what is unused, and the report says so.

Records that JSON. Steps 2 (classify) and 3 (report) both read it.

## 2. Classify

| Verdict | Applies to | Condition |
|---|---|---|
| **Keep** | skill | It fired |
| **Remove** | MCP server | Zero calls — except a project-scoped server whose project is still there and whose window holds no session from it, which gets no verdict |
| **該處理** | plugin | Its skills never fired, and nothing else in it is reached either |
| **保留** | plugin | Its skills never fired, but the plugin is reached another way |

**The split is whether anything in the plugin is reached at all — not who owns it.** Two routes count as reached: another of its skills fires (`never_fired` < `installed`), or its own MCP server does (`server_calls` > 0). Which remedy a **該處理** row deserves — uninstall it, or rewrite the descriptions where the source is the user's — is theirs to pick and needs no column.

The signals, first match wins:

| What the data shows | Recommend |
|---|---|
| `never_fired` == 0 | **保留** — every skill in it fires; the row is the standing state, with nothing to prune |
| `never_fired_command_only` == `never_fired` | **保留** — every silent skill here is command-only, so the row already costs 0 and pruning it saves nothing; say that instead of ranking it |
| `shadowed_by_personal` > 0 and every skill silent | **該處理** — two copies of one skill are installed and only one can win |
| `never_fired` < `installed` | **保留** — the plugin is reached, so the silent ones are a matching problem, not an unwanted capability |
| No skill fires but `server_calls` > 0 | **保留** — the capability is in use through its tools; its skills are what fail to trigger |
| No skill fires and `server_calls` is 0 | **該處理** — nothing in it has ever been reached by any route |

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
## Coverage
- transcripts：<n> 個檔，<YYYY-MM-DD> 到 <YYYY-MM-DD>
- 讀不到的來源：<每一筆 unavailable，以及它讓哪個判定做不出來 | 無>
- 只在歷史裡、沒有安裝對應的名字：<`description_cost.orphan_recorded_names`> 個（不判定）
- 已停用、不計成本的 plugin：<`disabled_plugins` 逐一列出 | 無>
- 每輪固定成本：全部 skill description ≈<總 tokens>，其中沒在用的佔 ≈<tokens>（<百分比>）

## 1. MCP server（<n>）— 依呼叫次數排序
| server | 呼叫次數 | scope | plugin@marketplace | 宣告在哪 |
<`mcp_servers` 全部列出，不是只列零呼叫的；零呼叫那列整列加粗>
<表後一句：零呼叫的是哪幾個（或「無」），以及拿不到判定的是哪幾個加上原因>
<再一段：這張表沒有 token 欄，但成本不是零。逐一寫出每個零呼叫、且這個 session 已經連上的 server，它常駐的 instructions 區塊實際多大（<chars> chars ≈<tokens> tokens／輪，用 `description_cost.chars_per_token` 換算）；有連上但本身沒有 instructions 區塊的，寫「沒有 instructions，這半是真的零」，沒連上的才寫「沒量到」並點出是哪幾個；tool schema 那半一律不估>

## 2. Local skill — 不屬於任何 marketplace（<n> 支，≈<tokens>／輪）
`~/.claude/skills/` 底下你自己放的。沒在用的 <k> 支佔 ≈<tokens>（<百分比>）。
| skill | 呼叫次數 | 每輪 ≈tokens |

## 3. Plugin@marketplace（<n> 個，≈<tokens>／輪）
| plugin@marketplace | skill（有用／共） | 每輪 ≈tokens | 沒在用的 ≈tokens | 建議 |

## 4. Keep — 有觸發過的 skill（<n>）
| skill | 呼叫次數（終生累計，照記錄的名字） | 每輪 ≈tokens |
```

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

**Table 3 carries two token columns and needs both.** `all_approx_tokens` is how heavy the plugin is — that is what it ranks on. `approx_tokens` is the never-fired share, which is what pruning would actually save. One alone answers neither question: a large total tells you nothing about whether to act, and a large wasted share tells you nothing about the plugin's weight. Label them `每輪 ≈tokens` and `沒在用的 ≈tokens`, and close the table with the total `沒在用的` of its **該處理** rows — that sum is what the reader would save, and it is the one number the whole report exists to produce.

**Table 4 repeats rows from tables 2 and 3, deliberately.** Those two are ranked by cost within their own population; this one ranks the whole inventory by use, which is the only view that puts the most-called skill next to a once-called one. Its `每輪 ≈tokens` is that one skill's own cost — `skills_installed[<name>].description_chars` ÷ `chars_per_token` — because firing is not the same as being worth its charge: a skill called once or twice on a fat description is the one place a rewrite pays.

**One row per item, never two merged into one.** Rows sharing a count are still separate rows: merging costs the reader one-line-per-thing scanning and hides which name the number belongs to.

**Counts from different sources are not comparable and never share a column.** Skill counts are lifetime totals from the harness's own counter; MCP counts come from transcripts, which rotate, so they cover a recent window. State which is which wherever a number appears.

**The report recommends; it changes nothing.** Disabling a server or uninstalling a plugin edits the user's setup and is theirs to run.
