# Report production (loaded at step 6's GATE)

## Pre-report evidence dump (NOT a checkbox list)

Two notes already written in chat during the trace loop:
- the running scope/chain note (each hop's role: erroring / slow-but-healthy / root cause / boundary)
- the infra Plan block + all planned queries dispatched (whenever the infra check fired)

Before writing the report, paste the evidence below in chat verbatim. **No ticking boxes — paste real numbers, queries, and excerpts.** Empty fields are visible; faking data is harder than checking a box.

```
=== Pre-report evidence ===

Time window (GMT+8): <from> ~ <to>
Burst window (if narrower than the URL range): <from> ~ <to>

Chain visibility (one line per hop, in call order):
# How each hop became visible, and — for the LAST hop — which of 5f's three visibility-end
# forms you excluded. A hop marked "trace" is one you SAW; a hop marked "navigated" is one you
# INFERRED from a host / log / code / dependency doc. If the last hop reads "chain simply ended",
# the root cause is not established — go back to 5f before writing Root Cause.
- <svc-1>: trace | navigated (<how>)   role: entry / pass-through / root cause / boundary
- <svc-2>: ...
- Not trace-covered on this chain: <svc, svc>  (or "none")
  # A factual note, not a recommendation. Accumulated across investigations it is the
  # evidence for which services are worth instrumenting next.

Request outcome (HARD RULE 6 — error count is not failure count). Impact needs a number for
EACH of the three outcomes, so each has a line here; "n/a" is allowed, silence is not:
- Status of the traced request(s): <200 / 5xx / not obtained>
- Structured access fields available? <yes → count of status>=500 in window | no → how outcome was established>
- Failed: <N> (<statuses>, <paths>)
- Succeeded but degraded: <N>  | latency spread: median <x>s, max <y>s, bands <…>  | n/a + why
  # Pulled and bucketed client-side; the cut is chosen FROM the distribution, not guessed
  # in advance — a guessed threshold sweeps in whatever slowness the service always has.
- Unaffected in the same window: <N> or "rest of the window normal"
- If 200: the errors were logged before an upper layer caught them — say so here, and Impact is not
  a failure count. If not obtained: it goes in Unknowns; do NOT substitute the error count.

Co-affected callers (fill whenever the breadth classifier returned fleet-wide — SKILL.md 5d):
- <svc>: <N> failed / <N> degraded / <N> distinct users     (same signature, same window)
- Peeled until the breadth query returned 0? <yes → all callers accounted for | no → who is missing>
- Any caller NOT quantified ⇒ Impact is a LOWER BOUND and must say so, naming who is missing.
# A shared-layer root cause with one named victim contradicts itself; this block is what stops
# the report scoping Impact to the anchor by default.

Lines-per-request ratio (REQUIRED before any count reaches Impact):
- Traced request emitted <N> lines matching the anchor filter → ratio 1:<N>
- Raw line count <M> ÷ <N> ≈ <M/N> requests
# One failure routinely emits several lines — an access log, a connection error, the unhandled
# exception, a fatal. Reporting lines as requests inflates Impact by exactly that factor (an
# observed run: 2 lines per request, so the honest number was half the count). This costs
# nothing: the trace you already pulled in 5.0 IS the sample — count its lines for this filter.
# If no trace was available, sample one failing request's lines by correlation id instead.

Per-project error counts (size:0 + track_total_hits:true — raw log-line count):
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

0. **憑證絕對不可原文引用——這條在寫任何一段之前先套用。** auth / token / session 失敗的 log，**訊息本體常常就是憑證本身**（完整 bearer / JWT、api key、簽章 cookie、帶密碼的連線字串）。而報告會逐字引用 dominant pattern 的原文，所以 auth 類事故是**預設會外洩**，不是失手才外洩。做法：用 **exception type + 角色**描述（「access token 驗證失敗」），值本身截斷或遮蔽。適用範圍包含報告、pre-report evidence dump、chain note、以及任何貼到 ticket / 對話的內容。看起來已過期也不例外——從 log 行判斷不出來，而報告的壽命比 token 長。

1. **Impact 的「使用者體驗」禁止出現任何 code 元素**：函式名、變數名、語法（`await`、`try/catch`、`.then()`、`Promise`）、file path、line number 都不行。只能寫**使用者眼睛看到什麼**。違反這條請重寫，不要送出。
   - ❌ 反例：「`<funcName>` 的 `await` 拋例外後 `<varName>` 沒被更新且未被 catch」
   - ✅ 正例：「使用者進入 `<頁面>` 後 `<某區塊>` 顯示空白或維持上一次值，頁面其餘正常，因為 error 沒被 catch」
2. **多種影響可拆 bullet**：使用者體驗不限一句。如果有多條獨立影響（例如 logo 空白 + 登入失敗），用 sub-bullet 一條一條列出，每條都是使用者視角。
3. Code 機制（哪段 code、哪個函式失敗）寫在 **Root Cause** 區塊。**Impact 區塊寫使用者視角，Root Cause 區塊寫工程師視角**，不要混。
4. **Root Cause 必須分兩層，「觸發源」永遠先寫**：
   - **觸發源（事實層，必填）= 先回答「什麼變了？」四選一**：
     - **A. code 變了** → 誰 release？（`git blame` 出事那行 + deploy timeline）→ 引入的 bug。
     - **B. dependency 變了** → 第三方 / 別人的服務掛（往 callee 鑽，`next-hop-drill.md` callee ladder）。
     - **C. input / load 變了** → 同一段 code、沒人 release，但進來的 request 變了：bot / 暴量 / 新客戶資料 / 一直潛伏今天才被打中的 edge case（往 caller 鑽，`next-hop-drill.md` caller-direction drill）。
     - **D. 啥都沒變** → 本來就這個錯誤率 = chronic 背景 / by-design（`next-hop-drill.md` baseline ratio ≈ 1 即屬此類）。
     - ⚠️ 最常見的漏判：沒人 release 就直接跳 B/D，漏掉 **C**（code 沒變但觸發變了）。
     佐證用可查、不可捏造的數字：git blame 意圖、IP 集中度、distinct customerId 集中度（log 分析步驟）、incident/baseline 暴增倍率（`next-hop-drill.md` correlation check）。這層是使用者做後續決策（封 bot / 改 code / 接受）的依據，**必須優先查實**。查不到就明寫「觸發源未判定 + 還缺什麼資料」，**絕不能因為「還沒確定是不是 bug」就把觸發源丟進 Unknowns** — 事實層與判斷層獨立。
   - **機制 / 判斷（看法層）**：agent 認為這是 bug / 預期行為 / 設計缺陷，**標明這是判斷**並給依據（stack trace、code、git blame）。注意 throw 的那行不一定是真因，可能是下游症狀（頂層 NullRef 源自上游 bad state）——先判這行是因還是果。
   - 兩層獨立：觸發是 bot 不代表沒有 code 問題；是設計意圖也要分清「意圖」與「實作後果」是否一致（例：刻意拒絕 token 是對的，但用 unhandled exception 回 500 仍是缺陷）。

5. **根因觸底到共享基礎設施 → 明列「請使用者去找 infra owner 確認」，但判斷在先。** 當 Root Cause 是共享資料層 / 網路（Redis / DB / cache 叢集、DNS、LB）而非單一服務自身資源時（通常經 step 5d 廣度分類器判為 fleet-wide、`infra-metrics.md` §11g 判定）：
   - **先由你判定**「資料層本身 vs 到資料層的網路路徑」（依 §11g 的判別訊號）——**這是你的活，不可把判斷丟給使用者**。
   - 判定為**網路/連線層** → How to Resolve / Unknowns 明列「需與 **網路 / IT** 確認 `<RKE→datastore 網段 / 交換器 / DNS>`」；判定為**資料層本身** → 明列「需與 **DBA / 資料層 owner** 確認 `<node、負載、blocked clients>`」。owner 名稱從環境知識（step 1c）取，保持通用。
   - **判不出來**才並列兩個 owner + 兩個確認項，並寫明還缺什麼資料——不可因「還沒確定」就整包丟 Unknowns 讓使用者自己查。

6. **Error level ≠ 請求失敗。把任何 error log 寫進 Impact 之前，先拿到那個請求的 HTTP status。**
   Library 常在例外被上層 handler 接住**之前**就先用 Error 記一筆——ORM、HTTP client、gRPC interceptor 都會。所以「N 筆 error」跟「N 個請求失敗」之間**沒有必然關係**，而報告的嚴重度整個掛在這個差別上。
   - 判法是機械的，而且成本為零：**拿一筆 hit 的 trace-correlation id 撈整條鏈（5.0 已經做過），看最後那筆 access log 的 status code。** 200 就是被接住了、使用者沒事；5xx 才是真的失敗。
   - 若該 stream 有結構化 access 欄位（status / path / 耗時），**直接查 `status_code >= 500` 的清單**——那是「誰真的失敗、失敗在哪個 endpoint、等了幾秒」的唯一直接來源，不是補充色彩。
   - 兩個方向都要防：**全 200 卻報成事故**（假警報，把良性噪音寫成「N 筆錯誤影響某流程」），以及**有 5xx 卻因為「大多數看起來還好」而漏報**。
   - **沒有結構化 access 欄位不等於拿不到 status**：該 stream 若有 access-severity 的 log 行，那行通常是固定欄位順序，撈原始 log 文字下來 client-side 解析即可得 status／耗時／client address（SKILL.md step 4 的 access-line 段落）。走完那條才算「拿不到」。
   - 拿不到 status 就明寫「未取得請求結果」並列進 Unknowns——**不可用 error 筆數代替失敗數**。

7. **止血建議要對得起你自己量到的數字，而且「擋得住這件事的開關是關的」永遠是一條 How to Resolve。** 這兩件事在調查途中就已經拿到，卻最容易在寫報告時掉——因為此刻眼前只有這份模板：告警／SOP 附的第一時間處置（step 2b「Alert URL / alert context」已要求驗證而非照抄），以及能擋住這類事件的設定現值（step 1c 的 config / settings lookup）。收尾前檢查兩項：**你的 infra 數字有沒有否證掉告警指定的動作**（有 → 明說哪一項無效與依據，不可把它原文寫成建議），以及**那顆旋鈕現在是什麼值**（關著／設錯 → 指名設定與現值，那通常就是真正的長期解）。查不到值就進 Unknowns，**不可寫「建議調整相關設定」這種沒有受詞的句子**——它讀起來像有結論，實際沒有。

## Output

Output **two versions**: Traditional Chinese first (full detail, the user reads it), then English (super-short, the user pastes to Jira / shares with others who only ask "what happened" + "how bad").

**All times in the report use GMT+8 (Asia/Taipei) ONLY.** Convert UTC from URLs / logs to GMT+8 internally; do not show UTC alongside (the user does not need it). Show the timezone tag once: `(GMT+8)` or `+08:00`.

**Normalize the timestamp to an absolute instant BEFORE converting — do not assume the log's timestamp is an ISO date string.** A stream's timestamp storage format comes from 1c's per-stream mapping (step 1c / step 3's family classification): one family stores ISO 8601, another can store an **epoch-millis value carrying sub-millisecond digits, as a string** (e.g. `"1785595083661.277400"`). Range-filtering and sorting work on both, so the format never surfaces as an error during the investigation — it surfaces **in the report**, as a burst window that is off by decades or renders as a raw number. Parse to an instant, then shift to GMT+8. If you cannot determine a timestamp's format with confidence, say so in Unknowns rather than printing a time you have not verified — a wrong incident window is worse than a missing one, because everyone downstream correlates against it.

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
- 請求結果（三類都要有數字，缺的寫 n/a + 原因）：
  - 失敗：<N> 筆（<主要 status>），端點：<path…>
  - 成功但顯著變慢：<N> 筆，<延遲分佈，見下>
  - 未受影響：<N> 筆 or「同窗其餘請求正常」
- 延遲（只在有「慢但成功」時）：中位數 <x>s、最大 <y>s；區間：<<5s: N>、<5–10s: N>、<10–20s: N>、<>20s: N>
- 其他同樣中招的 caller：<service: N 筆 / N 人> or「已確認僅此服務」
- 時間：<from> ~ <to> (GMT+8)
- 使用者體驗：使用者進入 <產品> 後 <看到什麼>，<其他部分如何>，因為 <error 處理>。

**How to Resolve**
- 短期：<止血>
- 長期：<根治>
- <只在成立時：告警／SOP 指定的處置與你的數據矛盾 → 明說哪一項無效、依據是什麼>
- <只在成立時：能擋住這件事的開關目前是關的／值設錯 → 指名該設定與現值>

**Unknowns**
- <事項 1>
- <事項 2>
```

### 變體：查完發現沒有事故（benign noise）

**當 HARD RULE 6 的結果是「請求全部成功」時，用這個形狀，不要硬填上面的模板。** 硬填會逼你在「受影響使用者」寫 0、在「使用者體驗」寫「沒有異常」——讀起來像在閃避，而且把真正該講的事擠掉了。這種結論**不是失敗的調查**，它回答的是一個不同但同樣有價值的問題，所以主題要換掉：**為什麼這條 alert 在吵，以及怎麼讓它不要再吵。**

Heading 順序：**Root Cause → 為什麼無影響 → 噪音組成 → How to Resolve → Unknowns**。

```
**Root Cause**
- 觸發源：<多半是 D 啥都沒變 —— 附 incident/baseline 倍率與背景率>
- 機制（判斷）：<這些 error 是什麼、誰記的、為什麼是良性>

**為什麼無影響**
- 請求結果：<N> 筆請求全部 <200 / 3xx>，證據：<trace 末端的 access log / status>=500 查詢回 0>
- error 是在例外被上層接住**之前**由 <哪一層 library> 記的 → level 反映不了實際結果

**噪音組成**（這條 filter 到底在吵什麼）
- 總計 <N> 筆 → <pattern A> <n1> 筆（<x1>%）、<pattern B> <n2> 筆（<x2>%）…
- 良性佔比：<~X>%

**How to Resolve**
- 讓它不再吵：<具體的排除條件 / alert 門檻調整 —— 寫成可以直接照做的形式>
- 若要根治噪音源：<可選，通常優先度低>

**Unknowns**
- <沒有量測就排除的 pattern，以及還缺什麼數字>
```

英文版兩行照舊，但 `Impact:` 要明說沒有影響，例如 `Impact: none, all N requests succeeded; ~X% of this filter is benign noise`。**不要省略 Impact 行** —— 讀的人需要看到「有人查過而且確認沒事」，那跟沒查過完全是兩回事。

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
