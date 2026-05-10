---
name: issue-tracing
description: Use when the user provides a Grafana or Kibana/ELK URL and asks to investigate an alert, error, incident, or anomaly, or when the user runs /issue-tracing.
---

# Issue Tracing

On-call triage assistant. Takes a Grafana or Kibana URL (or alert description) and produces a structured **Root Cause / Impact / How to Resolve / Unknowns** report in both Traditional Chinese and English.

**Input** (`$ARGUMENTS` optional):
- Grafana dashboard / panel URL
- Kibana Discover URL
- Plain alert description (then ask user for a URL)

---

## Steps

1. **Preflight: resolve the user's project root** (do this FIRST, before any URL work)

   Code reading is required later (step 10) to determine user impact and confirm root cause; without a project root, the whole flow stalls partway. Resolve up front:

   a. **Check `add-dir` paths** loaded in the session — if there's a plausible service repo under one, treat its parent (or the path itself) as the root.
   b. **Ask the user** — if (a) does not yield a root, ask: "請執行 `/add-dir <你的服務 repo 根目錄>`（例如 `/add-dir ~/Project`），讓我之後能讀 code 判斷使用者影響。" Wait for the user to add it, then re-check.

   Cache the resolved root in conversation context. Then continue to step 2.

2. **Parse the input URL**

   **Grafana URL** (`*-grafana.*/d/<uid>/...`):
   - Extract `uid`, `viewPanel` (panel id, optional), `from`, `to`, `var-*` template vars
   - If `from`/`to` are relative (`now-1h`), resolve to absolute UTC

   **Kibana URL** (`*log*/app/discover#/...` or `view/<savedSearchId>`):
   - Extract `time.from`, `time.to`
   - Extract filters: `env`, `project.keyword`, `level.keyword`, KQL `query`
   - Extract `dataViewId` to determine index pattern (see step 4)
   - If URL contains `view/<id>` (saved search), the saved search bundles a data view + filters — use the filters in the URL state

   **Time buffer**: expand the parsed range by ±5 minutes when querying.

3. **Determine investigation path**

   | Input | Path |
   |---|---|
   | Grafana dashboard URL (no `viewPanel`) | Read whole dashboard summary + every panel query, identify which panels show anomaly in the time window |
   | Grafana single panel URL (`viewPanel=panel-N`) | Focus on that panel only |
   | Kibana URL | Skip Grafana, go directly to ES query (step 7) |

4. **Map Kibana data view → ES index pattern**

   Kibana data views do not equal ES index names. ES MCP queries need real index patterns.

   Resolve every conversation (do not persist; infra can change):
   1. **List data streams** — call `mcp__elasticsearch__list_indices`, extract unique prefixes from `.ds-<prefix>-*` entries.
   2. **Match by name** — extract the data view name from URL or filters (the user usually mentions it in their question, e.g. "in `<product>-<region>`"). Match it against the data stream prefixes. A data view like `<x>-<y>` typically maps to a data stream like `<y>-logs-<x>*`, `<x>-<y>*`, or similar — show candidates and pick the one that returns hits with the expected `project.keyword` filter.
   3. **Ask the user** — if matching is ambiguous after looking at hits, ask once. Cache the answer in conversation context only (do not write to memory).

   Honor any **excluded patterns** the user mentions (e.g. test / lower-priority product lines). Default: include everything.

   If the data center / cloud is unclear, query all confirmed patterns in parallel.

5. **Run Grafana panel queries (when needed)**

   For each relevant panel from step 3:
   - Call `mcp__grafana__get_dashboard_panel_queries` with `uid` (and `panelId` if known)
   - Inspect each query's `datasource.type`:
     - `elasticsearch` → take the KQL string and run via ES (step 7). Do not call Grafana to execute; query ES directly.
     - `prometheus` / `loki` / other → use the corresponding Grafana mcp tool (`query_prometheus`, `query_loki_logs`, etc.) with the panel's `processedQuery` and the parsed time range.
   - For dashboards used to interpret meaning (no `viewPanel`), report each panel: title, what it measures, observed value vs expected, whether it shows anomaly.

6. **Identify candidate projects** (before running ES counts)

   Source the candidate project list from these, in order:

   a. **Grafana panel legend** (most reliable for dashboard URLs): when a panel groups by `project.keyword`, the legend table lists projects with totals directly. Two ways to obtain it:
      - Ask the user to read the legend off the screen (Name / Total columns)
      - Call `mcp__grafana__get_panel_image` to render the panel and inspect the legend
   b. **Sample hits**: if no panel legend, run one query with `size: 50` over the time window with the panel's filters but **no project filter**. Tally `project` field across hits client-side. This is a coarse top-K but bounded by `size`.
   c. **Kibana URL filters**: if the URL has `project.keyword: is one of [...]`, use that list verbatim.

   Do NOT enumerate by trying every known project name — brittle and slow.

7. **Run ES queries** (per-project counts)

   Required filters on every query:
   - `range` on `@timestamp` — the parsed time range with ±5 min buffer
   - `term` on `env.keyword` — usually `prod` (from URL filters)
   - `term` on `project.keyword` — REQUIRED; one query per candidate project
   - `terms` on `level.keyword` — default `["error", "fatal"]`; include `"warning"` only if the originating alert was warning-level or the dashboard panel includes warnings. Count warning separately from error/fatal.

   **NEVER run a query without a project filter, time range, AND level filter.** A `*` or `match_all` query is forbidden — past incidents include heap exhaustion from unbounded queries.

   **The `mcp__elasticsearch__search` wrapper drops `aggregations` from responses; only `hits` are returned.** Plan accordingly:
   - Total counts: `size: 0` query — use the `Total results: N` line
   - Top message patterns: `size: 5` sorted by `@timestamp desc`, read `message` field
   - First / last occurrence: two queries with `sort` `asc` and `desc`, `size: 1`
   - Distinct user counts: see step 8 (cannot use `cardinality` agg)

8. **Distinct user count** (when meaningful)

   Many backend logs do NOT carry `customerid` / `accountid`. Workflow:

   a. Sample 1 hit from the dominant project: `size: 1, _source: "*"`
   b. Inspect fields. If no `customerid`, `accountid`, `userid`, `account_id` etc. → write `n/a` in the report.
   c. If a user-id field exists: pull `size: 100` hits, dedupe client-side, report as a lower bound (e.g. `~38+`). Note the cap.
   d. Do NOT spend extra effort if the field is absent — the report is useful without it.

9. **Cross-project drill-down**

   Triggers, in priority order — use the highest-priority signal available, do not be misled by lower-priority hints:

   1. **URL / hostname inside an error message** (most reliable — actual call data). e.g. a log shows `Url: "http://<svc>-01.<dc>.<internal-domain>/api/..." ... TimeoutRejectedException` → upstream is `<svc>`. Extract the host's leading token before the first `-` or `.` as the candidate `project.keyword`.
   2. **Log message** in the current project explicitly names another service (e.g. `Failed to call <upstream>`).
   3. **Reading code** (step 10) reveals an outbound call to another service that failed in the same window.
   4. **Grafana panel title / sibling panel** mentions a service (lowest priority — may be unrelated). Treat as a hint only; verify by querying logs and require non-zero matching activity in the window before pursuing.

   **HTTP error pattern** (`status=502/503/504`, `connection refused`, `timeout`) implies an upstream — apply the trigger ladder above to identify it. Do not stop at "got 503" without identifying the upstream.

   Maximum 2 hops total. If exceeded, stop and list the call chain in Unknowns.

10. **Code inspection** (under the project root resolved in step 1)

   Use the project root from step 1 to locate the involved repos. For each `project.keyword` you need to read:

   a. **Direct match**: `<root>/<project.keyword>`
   b. **Dot variant**: replace `-` with `.` (e.g. `service-a-b` → `service.a.b`)
   c. **Hyphen variant**: replace `.` with `-`
   d. **Strip separators**: `ls <root> | grep -i <stripped>`
   e. **Frontend / consuming repo — REQUIRED when user impact is being reported.** If the project ends with `-backend` / `.backend`, also check `<root>/<base>.frontend` / `<root>/<base>-frontend`. The frontend determines what the end user actually sees.
   f. If a–e all fail for a repo, list in **Unknowns**: "需要 `<project>` 的 repo 路徑 / 請執行 `/add-dir <path>`".

   **For each repo found, read code as follows:**
   - **Backend**: locate the failing endpoint/function from log clues (URL path, controller name, method name); inspect error handling and outbound calls.
   - **Frontend**: grep the failing API name (taken from the backend log) and read its call site. Determine: is the error caught? Does the UI fall back to empty / placeholder / error state / blank? Is there a retry?
   - **Impact wording must be high-level**: 1–2 sentences describing what the user sees. e.g. "error 被 catch 後 該區塊顯示空白，頁面其餘正常". Do NOT include file paths, line numbers, or code mechanics in Impact (those belong in Root Cause if relevant). If frontend code is unreadable / unavailable, say so explicitly in Unknowns.

11. **Check infrastructure dashboards** (when upstream identified)

    Once an upstream service is suspected (from step 9), verify its infra health for the incident window. Discover the relevant infra dashboards every conversation (do not persist):

    1. **Search by intent** — call `mcp__grafana__search_dashboards` with terms like `vm-resource`, `pod-info`, `node`, plus the suspected service name. Inspect tags (`["GKE"]`, `["RKE"]`, `["VM"]`, etc.) and titles to identify per-tier dashboards.
    2. **Inspect candidates** — call `mcp__grafana__get_dashboard_summary` on the top match per tier; check that variables (`NAMESPACE`, `DEPLOYMENT`, etc.) and panel types (CPU / memory / replicas) fit the expected pattern below.
    3. **Ask the user** — if multiple candidates look equally relevant, ask once and cache the choice in conversation context.

    Typical tiers and what to look for:

    | Tier | Typical panels | Common variables |
    |---|---|---|
    | VM | per-host CPU / memory time series, one panel per `<svc>-<dc><N>` host | none — host names hardcoded in panels |
    | RKE / on-prem k8s | Pod info table, replica count, restart, throttle, memory/CPU per replica, often split per cluster | `NAMESPACE`, `DEPLOYMENT` |
    | GKE / cloud k8s | Pod info, replica, CPU/memory, network packets | `NAMESPACE`, `DEPLOYMENT` |

    Workflow:
    - **Extract the service name** from host strings in error messages (e.g. `<qualifier>-<svc>-01.<dc>.<internal-domain>` → service `<svc>`). Strip leading qualifier prefixes (when present) and trailing instance/ordinal suffixes (`-01`, `-a01`, `-b02`).
    - **Match by service name token, never by exact instance**. Each tier fans out per service:
      - VM: `<svc>-a01`, `<svc>-a02`, `<svc>-b01`, `<svc>-b02` (typical pattern: data center letter + ordinal; the user may follow a different convention)
      - RKE / on-prem k8s: dashboard sections often split per cluster (e.g. cluster A / B), multiple pod replicas per deployment
      - GKE / cloud k8s: multiple pod replicas per deployment in same namespace
      → Aggregate across instances when summarizing; cite the worst instance.
    - Pick tier by signal: hostname matches a VM panel → VM. k8s-style name → cloud or on-prem k8s. Hostname domain suffix often hints at the data center / cloud (e.g. `tw01.example.com` = on-prem) — note this in conversation context; do not persist.
    - **Query the data source directly — do NOT lead with `get_panel_image`.** Image rendering is for visualization only; for triage, raw numbers are more reliable. Route by `datasource.type` from `get_dashboard_panel_queries`:

      | Datasource | Method | Reliable? |
      |---|---|---|
      | `prometheus` | `mcp__grafana__query_prometheus` with the panel's `processedQuery` | yes |
      | `influxdb` | `mcp__grafana__grafana_api_request` proxy (steps below) | yes |
      | `elasticsearch` | run via ES MCP directly (same as step 7) | yes |
      | other | `get_panel_image` | sometimes |

    - **InfluxDB proxy steps** (MUST DO before declaring "infra unknown" for any VM/InfluxDB panel):
      1. `mcp__grafana__get_datasource` with the panel's datasource UID → note `database` field.
      2. `GET /api/datasources/proxy/uid/<dsUid>/query?db=<database>&epoch=ms&q=<urlencoded InfluxQL>` via `mcp__grafana__grafana_api_request`.
      3. Build InfluxQL from the panel's saved query, BUT verify tag values first — saved queries can be stale. Run `SHOW TAG VALUES FROM "<measurement>" WITH KEY = "<tagKey>" WHERE "<filterKey>"='<value>'` to discover real tag values (e.g. `metric` may be `physical %`, not `physical memory %` as the panel saved query says).

    - **`get_panel_image` is UNRELIABLE for InfluxDB-backed panels** — it commonly returns "No data" even when the dashboard clearly shows data. **NEVER conclude "metrics normal" or "no data available" from a `get_panel_image` "No data" result on an InfluxDB panel.** You MUST attempt the InfluxDB proxy path above before giving up.

    - Default scan: one CPU + one memory + restart/replica per service, **all instances**. Drill deeper only on anomalies.

    - Look for: pod restart, replica drop, CPU/memory saturation, throttle, network drop, redis timeout.

    - For other reasons "No data" can be legitimate (instance decommissioned, naming changed, service migrated). Try the other tiers (VM ↔ GKE ↔ RKE) before assuming. Also check the dashboard's tags / OS — a Linux service on a Windows-tagged dashboard is the wrong dashboard, not "no metrics".

    - Brief findings into Root Cause **only when the data is verified**. Acceptable verification: Prometheus query that returned numbers, InfluxDB proxy query that returned numbers, panel image that actually rendered a chart, or a user-supplied screenshot. **A "No data" image, an empty Prometheus result that you didn't double-check, or "current metrics look normal" are NOT verification of incident-time state.**

    - **Hard rule — verification over speed**: Do NOT use absence of data as evidence to rule out a hypothesis. If the renderer fails AND you have not yet tried the InfluxDB proxy or Prometheus query, the answer is "haven't checked yet", not "no data". Only after attempting all available query paths may you write "infra metrics 無法驗證，請提供 dashboard 截圖" in Unknowns.

    - Null results are valuable only when verified — e.g. a Prometheus query returning numbers that show flat CPU/Mem rules out resource exhaustion. A failed render does not.

    - **Once a tier confirms the service exists (any panel returns data, even from a different time window), record it as "service runs on `<tier>` (`<instance pattern>`)" and move on.** Do not list "where does service run?" as Unknown if the dashboard already showed it. "No data in the incident window but data now" is a separate question (retention, instance churn) — phrase it that way, not as "infra unknown".

12. **Produce the report**

   ### HARD RULES (read before writing)

   1. **Impact 的「使用者體驗」一行禁止出現任何 code 元素**：函式名、變數名、語法（`await`、`try/catch`、`.then()`、`Promise`）、file path、line number 都不行。只能寫**使用者眼睛看到什麼**。違反這條請重寫，不要送出。
      - ❌ 反例：「`<funcName>` 的 `await` 拋例外後 `<varName>` 沒被更新且未被 catch」
      - ✅ 正例：「使用者進入 `<頁面>` 後 `<某區塊>` 顯示空白或維持上一次值，頁面其餘正常，因為 error 沒被 catch」
   2. Code 機制（哪段 code、哪個函式失敗）寫在 **Root Cause** 區塊。**Impact 區塊寫使用者視角，Root Cause 區塊寫工程師視角**，不要混。

   ### Output

   Output **two versions**: Traditional Chinese first (full detail, the user reads it), then English (super-short, the user pastes to Jira / shares with others who only ask "what happened" + "how bad").

   **All times use GMT+8 (Asia/Taipei).** Convert UTC from URLs / logs.

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

   Omit fields that genuinely don't apply (e.g. no customerId field in this project) — write "n/a" instead of fabricating numbers.

---

## Guardrails

- **No unbounded ES queries.** Every search MUST include `@timestamp` range + `project.keyword` + `level.keyword` + `size` cap. No `*` / `match_all` queries.
- **No fabricated numbers.** Distinct user counts, request counts, customer ids — only report what the aggregation actually returned. If a field is missing, write `n/a`, never estimate.
- **No fabricated root causes.** If code is needed and unavailable, the report's Root Cause must say "需要看 code 才能確認" and the Unknowns must request the repo path. Do not pattern-match a guess.
- **Cross-project drill is bounded** — max 2 hops. List the chain if you stop early.
- **Project → repo mapping is per-user.** Get it from `add-dir` paths or ask the user to `/add-dir`. Never hardcode paths and never persist to memory (per-project memory doesn't help cross-project triage).
- **Honor user-mentioned excluded indices.** If the user mentions patterns to skip (e.g. lower-priority product lines, test indices) during the conversation, exclude them from queries. Only include excluded patterns if the user explicitly asks.
- **Output language order is fixed**: Traditional Chinese first (full), English second (super-short two lines). No language headings ("中文版" / "English") in the output. Order: Root Cause → Impact → How to Resolve → Unknowns.
- **Warning level handling**: include only when the originating signal is warning-level or the user asks. Always count warning separately from error/fatal in stats.
