# Step 12 — Produce the report

## Pre-report final check

Two upstream gates already enforced in chat output:
- Step 10a: scope table written
- Step 11: Plan block written + all planned queries dispatched

Before writing the report, confirm the remaining points (one line each in chat — yes / no / n/a). Any `no` → go back, do not write the report.

- [ ] For every in-scope service in the scope table: code read AND infra metrics queried (CPU + Memory + restart, mean+max ≤1m bin)
- [ ] Pre-incident baseline run for sibling error patterns before folding them into Root Cause
- [ ] All times in the planned report are GMT+8, no UTC shown
- [ ] Planned Impact lines contain zero code elements (function names, `await`, file paths)
- [ ] Planned Unknowns contains zero items an MCP query could have answered

## HARD RULES (read before writing)

1. **Impact 的「使用者體驗」禁止出現任何 code 元素**：函式名、變數名、語法（`await`、`try/catch`、`.then()`、`Promise`）、file path、line number 都不行。只能寫**使用者眼睛看到什麼**。違反這條請重寫，不要送出。
   - ❌ 反例：「`<funcName>` 的 `await` 拋例外後 `<varName>` 沒被更新且未被 catch」
   - ✅ 正例：「使用者進入 `<頁面>` 後 `<某區塊>` 顯示空白或維持上一次值，頁面其餘正常，因為 error 沒被 catch」
2. **多種影響可拆 bullet**：使用者體驗不限一句。如果有多條獨立影響（例如 logo 空白 + 登入失敗），用 sub-bullet 一條一條列出，每條都是使用者視角。
3. Code 機制（哪段 code、哪個函式失敗）寫在 **Root Cause** 區塊。**Impact 區塊寫使用者視角，Root Cause 區塊寫工程師視角**，不要混。

## Output

Output **two versions**: Traditional Chinese first (full detail, the user reads it), then English (super-short, the user pastes to Jira / shares with others who only ask "what happened" + "how bad").

**All times in the report use GMT+8 (Asia/Taipei) ONLY.** Convert UTC from URLs / logs to GMT+8 internally; do not show UTC alongside (the user does not need it). Show the timezone tag once: `(GMT+8)` or `+08:00`.

### Chinese version — full

Heading 順序固定：**Root Cause → Impact → How to Resolve → Unknowns**。

寫作規則：
- 每個 section 之間空一行；section 內若 > 1 點用 bullet。
- 句子要短，避免長段落。一段超過 3 行就拆 bullet。
- **使用者體驗**遵守上面 HARD RULE #1。模板：「使用者進入 `<產品/頁面>` 後 `<看到什麼>`，`<其他部分如何>`，因為 `<error 處理方式>`。」`<error 處理方式>` 用人話描述（如「error 沒被 catch」、「有 fallback 顯示舊值」），不寫 code。
- 數字濃縮（Impact 區塊放數字，不在句子中重複）。

No "中文版" / "English" headings. Output the report blocks directly. Separate the Chinese block from the short English block with a horizontal rule (`---`).

```
**Root Cause**
<核心一句話>

- <細節 / 上游 / call chain>
- <infra 數據 or 補充>

**Impact**
- 受影響使用者：~<N>（distinct customerId）or n/a
- 失敗 request：<N> / <duration>
- 時間：<from> ~ <to> (GMT+8)
- 使用者體驗：使用者進入 <產品> 後 <看到什麼>，<其他部分如何>，因為 <error 處理>。

**How to Resolve**
- 短期：<止血>
- 長期：<根治>

**Unknowns**
- <事項 1>
- <事項 2>
```

### English version — super short

Only **two lines**: `Root cause:` and `Impact:`. No fix, no unknowns, no time window, no headings beyond these two.

- Each line ≤ 25 words.
- Root cause: name the call chain in one sentence (e.g. `serviceA calls serviceB and serviceB CPU high can't respond`).
- Impact: numbers + behavior in one sentence (e.g. `~N user actions failed, button shows generic error`).
- Skip articles / be terse like a chat message — this is for quick "what's up" replies.

```
Root cause: <one sentence>
Impact: <one sentence with number + behavior>
```
