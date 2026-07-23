# Step 12 — Produce the report

## Pre-report evidence dump (NOT a checkbox list)

Two notes already written in chat during the trace loop:
- the running scope/chain note (each hop's role: erroring / slow-but-healthy / root cause / boundary)
- the infra Plan block + all planned queries dispatched (whenever the infra check fired)

Before writing the report, paste the evidence below in chat verbatim. **No ticking boxes — paste real numbers, queries, and excerpts.** Empty fields are visible; faking data is harder than checking a box.

```
=== Pre-report evidence ===

Time window (GMT+8): <from> ~ <to>
Burst window (if narrower than the URL range): <from> ~ <to>

Per-project error counts (size:0 + track_total_hits:true — raw log-line count):
# NOTE: one failed request can emit multiple log lines (e.g. AccessLog + Connection + Unhandled + fatal = 4 lines per failure). Sample one failure, count its lines, and state both raw lines AND estimated request count so the Impact number isn't inflated.
- <project-A>: <N> errors  | top message: "<first line of dominant pattern>"
- <project-B>: <N> errors  | top message: "..."

Pre-incident baseline (same-length window before incident, same filter, track_total_hits:true):
- <project>: <N> errors  → ratio incident/baseline: <X>x
- (run for every project that may go into Root Cause; if ratio ≈ 1, treat as background and exclude)

Infra metrics (one block per upstream named in the incident):

<svc-A>:
  Status: <REQUIRED / n/a (app-level root cause) / n/a (out-of-scope)>
  # If REQUIRED, fill the rest. Otherwise leave a one-line reason.
  Source: <prom expr | influxql>
  Per instance, mean / max in incident window (1-min bins):
    <inst-1>  CPU __ / __%   Mem __ / __%   Restarts __
    <inst-2>  CPU __ / __%   Mem __ / __%   Restarts __
    ...

<svc-B>:
  ... (same shape)

Frontend behavior (when impact will describe user-visible behavior — MANDATORY to fill if the frontend repo is present, per SKILL.md step 5b):
- Repo: <path or "genuinely absent — listed in Unknowns">
- Call site: <file:line of API call>   # if an endpoint-name grep missed, you MUST have widened to route-path / client-method / component / i18n key / shared header-footer repo before writing "not found" — a single name-grep miss is NOT grounds to punt
- Error handling: <caught? fallback? retry?>
- User sees: <one-line plain-language description — read from the call site, not guessed>

=== End evidence ===
```

If any block is empty or says "skipped", the work is incomplete — go back and fill it. Producing the report with empty evidence blocks violates the skill.

## HARD RULES (read before writing)

1. **Impact 的「使用者體驗」禁止出現任何 code 元素**：函式名、變數名、語法（`await`、`try/catch`、`.then()`、`Promise`）、file path、line number 都不行。只能寫**使用者眼睛看到什麼**。違反這條請重寫，不要送出。
   - ❌ 反例：「`<funcName>` 的 `await` 拋例外後 `<varName>` 沒被更新且未被 catch」
   - ✅ 正例：「使用者進入 `<頁面>` 後 `<某區塊>` 顯示空白或維持上一次值，頁面其餘正常，因為 error 沒被 catch」
2. **多種影響可拆 bullet**：使用者體驗不限一句。如果有多條獨立影響（例如 logo 空白 + 登入失敗），用 sub-bullet 一條一條列出，每條都是使用者視角。
3. Code 機制（哪段 code、哪個函式失敗）寫在 **Root Cause** 區塊。**Impact 區塊寫使用者視角，Root Cause 區塊寫工程師視角**，不要混。
4. **Root Cause 必須分兩層，「觸發源」永遠先寫**：
   - **觸發源（事實層，必填）= 先回答「什麼變了？」四選一**：
     - **A. code 變了** → 誰 release？（`git blame` 出事那行 + deploy timeline）→ 引入的 bug。
     - **B. dependency 變了** → 第三方 / 別人的服務掛（往 callee 鑽，step9 callee ladder）。
     - **C. input / load 變了** → 同一段 code、沒人 release，但進來的 request 變了：bot / 暴量 / 新客戶資料 / 一直潛伏今天才被打中的 edge case（往 caller 鑽，step9 caller-direction drill）。
     - **D. 啥都沒變** → 本來就這個錯誤率 = chronic 背景 / by-design（step9 baseline ratio ≈ 1 即屬此類）。
     - ⚠️ 最常見的漏判：沒人 release 就直接跳 B/D，漏掉 **C**（code 沒變但觸發變了）。
     佐證用可查、不可捏造的數字：git blame 意圖、IP 集中度、distinct customerId 集中度（log 分析步驟）、incident/baseline 暴增倍率（`step9-cross-project-drill.md` correlation check）。這層是使用者做後續決策（封 bot / 改 code / 接受）的依據，**必須優先查實**。查不到就明寫「觸發源未判定 + 還缺什麼資料」，**絕不能因為「還沒確定是不是 bug」就把觸發源丟進 Unknowns** — 事實層與判斷層獨立。
   - **機制 / 判斷（看法層）**：agent 認為這是 bug / 預期行為 / 設計缺陷，**標明這是判斷**並給依據（stack trace、code、git blame）。注意 throw 的那行不一定是真因，可能是下游症狀（頂層 NullRef 源自上游 bad state）——先判這行是因還是果。
   - 兩層獨立：觸發是 bot 不代表沒有 code 問題；是設計意圖也要分清「意圖」與「實作後果」是否一致（例：刻意拒絕 token 是對的，但用 unhandled exception 回 500 仍是缺陷）。

5. **根因觸底到共享基礎設施 → 明列「請使用者去找 infra owner 確認」，但判斷在先。** 當 Root Cause 是共享資料層 / 網路（Redis / DB / cache 叢集、DNS、LB）而非單一服務自身資源時（通常經 step 5d 廣度分類器判為 fleet-wide、step11 §11g 判定）：
   - **先由你判定**「資料層本身 vs 到資料層的網路路徑」（依 §11g 的判別訊號）——**這是你的活，不可把判斷丟給使用者**。
   - 判定為**網路/連線層** → How to Resolve / Unknowns 明列「需與 **網路 / IT** 確認 `<RKE→datastore 網段 / 交換器 / DNS>`」；判定為**資料層本身** → 明列「需與 **DBA / 資料層 owner** 確認 `<node、負載、blocked clients>`」。owner 名稱從環境知識（step 1c）取，保持通用。
   - **判不出來**才並列兩個 owner + 兩個確認項，並寫明還缺什麼資料——不可因「還沒確定」就整包丟 Unknowns 讓使用者自己查。

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
- 觸發源（事實，什麼變了）：<A code 變 / B dependency 變 / C input·load 變 / D 啥都沒變>，佐證：<git blame? IP·customerId 集中? incident/baseline 倍率?>
- 機制（判斷，標明看法）：<我認為這是 bug / 預期行為 / 設計缺陷，因為…（stack trace / code / git blame）>
- <call chain / infra 數據 補充>

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
