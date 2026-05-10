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

   **Token-budget rules** (the wrapper truncates large responses to a file when responses exceed its limit, costing extra `jq` round-trips):
   - **Always start with `size: 0`** to get the total. Only sample after that.
   - **`size` cap when fetching `message`/stack traces: 5.** A single `size: 100` over `error` logs with stack traces typically blows the limit. If 5 is not enough, paginate (`from`+`size`) or refine the filter — do not raise `size`.
   - **Always pass `_source`** with only the fields you need. For project distribution use `_source: ["project"]`; for time check use `_source: ["@timestamp"]`. Default `_source: "*"` only when you need to inspect schema once.

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
   4. **Grafana panel title / sibling panel** mentions a service (lowest priority — may be unrelated). Treat as a hint only; verify by querying logs, then apply the correlation check below before pursuing.

   **HTTP error pattern** (`status=502/503/504`, `connection refused`, `timeout`) implies an upstream — apply the trigger ladder above to identify it. Do not stop at "got 503" without identifying the upstream.

   Maximum 2 hops total. If exceeded, stop and list the call chain in Unknowns.

   **Correlation check before claiming "related"**: Before treating a sibling error pattern as part of this incident, run the same query over an **equally-long pre-incident window** (e.g. previous hour or previous day same time) and compare counts. If the pre-incident baseline is similar to the incident window, the pattern is **chronic, not caused by this incident** — list it as "out of scope / unrelated background error" instead of folding into Root Cause. Only fold in when incident-window count is materially higher than baseline.

10. **Code inspection & scope check**

   ### 10a. Scope check — for EVERY project named in this incident

   For the originating project AND every upstream identified in step 9, look it up under the project root from step 1 using these rules:

   a. **Direct match**: `<root>/<project.keyword>`
   b. **Dot variant**: replace `-` with `.` (e.g. `service-a-b` → `service.a.b`)
   c. **Hyphen variant**: replace `.` with `-`
   d. **Strip separators**: `ls <root> | grep -i <stripped>`
   e. **Frontend / consuming repo**: if the project ends with `-backend` / `.backend`, also check `<root>/<base>.frontend` / `<root>/<base>-frontend`.

   Record the result in conversation context as a scope table:

   ```
   Investigation scope:
   - <project>: in-scope (path: <path>)
   - <upstream-A>: in-scope (path: <path>)
   - <upstream-B>: out-of-scope
   ```

   **In-scope** = repo found under project root.
   **Out-of-scope** = no match after a–e (likely owned by another team / not on this machine).

   The scope table drives the depth of step 10b and step 11:
   - in-scope service → REQUIRED to read code (10b) and verify infra (step 11)
   - out-of-scope service → both are optional; root cause inside the service may stay in Unknowns

   ### 10b. Read code (in-scope only; required when impact involves them)

   - **Backend**: locate the failing endpoint/function from log clues (URL path, controller name, method name); inspect error handling and outbound calls.
   - **Frontend**: grep the failing API name (taken from the backend log) and read its call site. Determine: is the error caught? Does the UI fall back to empty / placeholder / error state / blank? Is there a retry?
   - **Impact wording**: derive from frontend code what the user actually sees, then write the Impact field per the rules in step 12 (HARD RULES). Do NOT include file paths, line numbers, or code mechanics here.

   **Hard rule for frontend lookup**: if the originating service is `-backend` / `.backend` and the report's Impact will describe user-visible behavior, locating the frontend repo via 10a.e is REQUIRED — backend code alone cannot tell you how the error surfaces to the user. If the frontend repo is not found under the project root, Impact must say so explicitly in Unknowns instead of guessing.

   If a–e all failed for a repo you needed (e.g. originating project's frontend not under root), list in **Unknowns**: "需要 `<project>` 的 repo 路徑 / 請執行 `/add-dir <path>`".

11. **Verify infra metrics**

    Once an upstream service is suspected (from step 9), use the scope table from step 10a:
    - **In-scope upstream**: REQUIRED to verify infra health for the incident window before writing Root Cause.
    - **Out-of-scope upstream**: optional. The default report can stop at "upstream `<svc>` returned 503/timeout"; deeper Root Cause (why `<svc>` failed) belongs to the owning team and may stay in Unknowns. Run 11 only if the user asks for a deeper dive or the log payload is too thin to confirm the upstream is the bottleneck.

    **Approach: query the datasource directly. Do NOT start from dashboards.** Dashboards are visualization for humans; for an agent, they are stale, full of unresolved scopedVars, and may not exist for the right tier. The metrics live in the datasource — go there first.

    **Parallelize independent reconnaissance.** When you need multiple unrelated lookups before any decision (e.g. `list_datasources`, `list_indices`, `SHOW TAG VALUES` on different InfluxDB datasources, `label_values` on different Prometheus datasources), fire them in a single batch of parallel tool calls — do not serialize. Same applies to per-instance metric queries once you know the host list (CPU + Memory queries for all `<svc>` instances should be one parallel batch, not N sequential calls).

    ### 11a. Identify the service token (not the literal hostname)

    Extract the service token from the host string in error messages, NOT the literal config hostname:

    - `<qualifier>-<svc>-01.<dc>.<internal-domain>` → token `<svc>` (strip leading qualifier prefixes, trailing instance suffixes `-01`/`-a01`/`-b02`)
    - **Why**: config / log hostnames are often DNS aliases or LB VIPs (e.g. `<qualifier>-<svc>-01.<dc>.<internal-domain>`), while monitoring uses a different naming (e.g. `<svc>-a01..<svc>-b03`). Querying with the literal config name will fail. Always use the **token** as a wildcard / regex filter.

    ### 11b. Query the datasource directly

    1. **List datasources** — `mcp__grafana__list_datasources`. Note Prometheus and InfluxDB UIDs + databases.
    2. **For each Prometheus datasource**: `mcp__grafana__query_prometheus` with `expr: label_values(up, instance)` (or a known service-label query) and grep for the service token. If hits, build queries:
       - CPU: `100 - rate(node_cpu_seconds_total{mode="idle",instance=~"<svc>.*"}[1m]) * 100` (or whatever the export pattern is — discover via `list_prometheus_metric_names`)
       - Memory: `node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes`
       - Use `query_prometheus` with `query_type: "range"` and `step: 60` for 1-min bins.
    3. **For each InfluxDB datasource**: query via `mcp__grafana__grafana_api_request` proxy:
       - Discover hostnames: `SHOW TAG VALUES FROM /.+/ WITH KEY = "hostname"` then grep for the service token, OR run `SHOW SERIES WHERE hostname =~ /<svc>/` (lighter).
       - Discover measurements for those hosts: `SHOW MEASUREMENTS WHERE hostname = '<svc>-a01'` (or browse `SHOW MEASUREMENTS` and identify CPU / memory / disk by name).
       - Discover tag keys for chosen measurement: `SHOW TAG KEYS FROM "<measurement>"`; then `SHOW TAG VALUES FROM "<measurement>" WITH KEY = "metric"` to find the right metric tag value (e.g. `CPU-AVG`, `physical %`).
       - Build query: `SELECT mean("value"), max("value") FROM "<measurement>" WHERE hostname =~ /<svc>/ AND "metric" = '<tag>' AND time >= '<from>' AND time <= '<to>' GROUP BY time(1m), hostname fill(null)`.

    ### 11c. Dashboard as last-resort hint (NOT primary entry)

    Only when 11b returns no metrics across all datasources should you turn to dashboards, and only to find which measurement / metric tag / aggregation the saved panel uses. Even then:

    - `mcp__grafana__search_dashboards` — try generic terms (`vm`, `host`, `node`, `pod-info`, `resource`, plus the service token). **0 hits ≠ "no dashboard"** — broaden terms once before giving up.
    - **Tags / titles are unreliable filters.** A `["windows"]`-tagged dashboard may still hold the Linux host you need (templating regex inside the dashboard is what matters, not the tag). If `search_dashboards` returns ≤ 5 candidates, you MUST run `get_dashboard_summary` (or `get_dashboard_property` for templating) on **every** candidate before discarding.
    - When you find a panel with the right measurement, read the raw panel JSON (NOT `get_dashboard_panel_queries` — its `processedQuery` keeps unresolved `/^$var$/` for panel-level scopedVars). Use `mcp__grafana__get_dashboard_property` with `property: "$.panels[?(@.id==<panelId>)].targets"` and extract:
      - `measurement` — literal name, use verbatim
      - `select` — field + aggregation (when `rawQuery=false`, UI uses this, not `query`)
      - `tags` — literal tag filters
    - **Do NOT guess measurement names.** **Do NOT loop through candidate names.** Hard limit: at most 1 alternate measurement attempt; then stop and list in Unknowns.
    - `get_panel_image` rules:
      - For `prometheus`, `loki`, `elasticsearch`, `influxdb` panels: **do NOT call `get_panel_image` for data verification or as a sanity check.** Always use the direct query path (11b). Image rendering on these is at best redundant, at worst (InfluxDB) silently broken. Image is acceptable only when the user explicitly asks for a chart / screenshot — never for deciding numbers.
      - For other datasources (CloudWatch, Splunk, SQL, Tempo, etc.) where no direct MCP query exists: `get_panel_image` is the legitimate fallback.

    ### 11d. Mandatory metric scan

    Once you have a working datasource path, query ALL of these for the suspected service (one query per metric per instance, all instances):

    1. **CPU** (mean + max, 1-min bins) — every instance
    2. **Memory** (mean + max, 1-min bins) — every instance
    3. **Restart / replica count** (k8s tiers only) — every replica
    4. For VM tier: also check **disk I/O / network** if the data exists

    Do NOT report on memory while skipping CPU (or vice versa). If you only have data for one, the report is incomplete — go back and query the other before writing Root Cause. Report the **worst instance's max** value across all metrics.

    **Beyond the mandatory list above, drill into other panels (latency, GC, queue depth, thread pool, connection pool, etc.) only when one of the mandatory metrics shows an anomaly that needs further explanation.** Do not pre-emptively scan every panel.

    Other signals to look for during the mandatory scan: pod restart, replica drop, CPU/memory saturation, throttle, network drop, redis timeout.

    ### 11e. Aggregation rule

    **Aggregate with both `mean` AND `max`, and keep bins ≤ 1 min.** A 5-min `mean` smooths away spikes — a chart visually showing 86% peak can read 50% under 5-min mean. Cite the **max** for spike detection, not the mean.

    - Brief findings into Root Cause **only when the data is verified**. Acceptable verification: Prometheus query that returned numbers, InfluxDB proxy query that returned numbers, panel image that actually rendered a chart, or a user-supplied screenshot. **A "No data" image, an empty Prometheus result that you didn't double-check, or "current metrics look normal" are NOT verification of incident-time state.**

12. **Produce the report**

   ### HARD RULES (read before writing)

   1. **Impact 的「使用者體驗」禁止出現任何 code 元素**：函式名、變數名、語法（`await`、`try/catch`、`.then()`、`Promise`）、file path、line number 都不行。只能寫**使用者眼睛看到什麼**。違反這條請重寫，不要送出。
      - ❌ 反例：「`<funcName>` 的 `await` 拋例外後 `<varName>` 沒被更新且未被 catch」
      - ✅ 正例：「使用者進入 `<頁面>` 後 `<某區塊>` 顯示空白或維持上一次值，頁面其餘正常，因為 error 沒被 catch」
   2. **多種影響可拆 bullet**：使用者體驗不限一句。如果有多條獨立影響（例如 logo 空白 + 登入失敗），用 sub-bullet 一條一條列出，每條都是使用者視角。
   3. Code 機制（哪段 code、哪個函式失敗）寫在 **Root Cause** 區塊。**Impact 區塊寫使用者視角，Root Cause 區塊寫工程師視角**，不要混。

   ### Output

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

   Omit fields that genuinely don't apply (e.g. no customerId field in this project) — write "n/a" instead of fabricating numbers.

---

## Guardrails

- **No unbounded ES queries.** Every search MUST include `@timestamp` range + `project.keyword` + `level.keyword` + `size` cap. No `*` / `match_all` queries.
- **No fabricated numbers.** Distinct user counts, request counts, customer ids — only report what the aggregation actually returned. If a field is missing, write `n/a`, never estimate.
- **No fabricated root causes.** If code is needed and unavailable, the report's Root Cause must say "需要看 code 才能確認" and the Unknowns must request the repo path. Do not pattern-match a guess.
- **No fabricated unknowns.** Unknowns may only contain: (a) facts about out-of-scope services (per step 10a scope table), (b) data that the available tools / permissions cannot reach, or (c) decisions that need a human (business / ownership). "Need to check Grafana for CPU", "should confirm pod restart" or any item the agent can answer with an MCP query is NOT a valid Unknown — go and check it.
- **Cross-project drill is bounded** — max 2 hops. List the chain if you stop early.
- **Project → repo mapping is per-user.** Get it from `add-dir` paths or ask the user to `/add-dir`. Never hardcode paths and never persist to memory (per-project memory doesn't help cross-project triage).
- **Honor user-mentioned excluded indices.** If the user mentions patterns to skip (e.g. lower-priority product lines, test indices) during the conversation, exclude them from queries. Only include excluded patterns if the user explicitly asks.
- **Output language order is fixed**: Traditional Chinese first (full), English second (super-short two lines). No language headings ("中文版" / "English") in the output. Order: Root Cause → Impact → How to Resolve → Unknowns.
- **Warning level handling**: include only when the originating signal is warning-level or the user asks. Always count warning separately from error/fatal in stats.
