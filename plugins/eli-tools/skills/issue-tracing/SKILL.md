---
name: issue-tracing
description: Use when the user provides a Grafana or Kibana/ELK URL and asks to investigate an alert, error, incident, or anomaly, or when the user runs /issue-tracing.
---

# Issue Tracing

On-call triage assistant. Takes a Grafana or Kibana URL (or alert description) and produces a structured **Root Cause / Impact / How to Resolve / Unknowns** report in both Traditional Chinese and English.

> **This skill is a step-by-step SOP, not a reference document.** Each step has rules and gates you MUST execute and acknowledge in chat before moving to the next. Reading the rules without writing the required outputs (scope table, query plan, etc.) violates the skill. If you find yourself thinking "I'll just write the report now" before completing every step, you are skipping work.

**Input** (`$ARGUMENTS` optional):
- Grafana dashboard / panel URL
- Kibana Discover URL
- Plain alert description (then ask user for a URL)

---

## Steps

1. **Preflight: resolve project root + preload tools** (do this FIRST, before any URL work)

   ### 1a. Preload core deferred tools

   Pre-load only the always-used entry-point tools so the very first ES / Grafana calls don't break narrative. Single `ToolSearch` with:

   - `mcp__elasticsearch__search`
   - `mcp__elasticsearch__list_indices`
   - `mcp__grafana__list_datasources`

   All other tools (panel queries, dashboard JSON, Prometheus / Loki query, panel image, etc.) are loaded on demand when actually needed — `ToolSearch` is cheap and saves context vs. preloading schemas you may not use.

   ### 1b. Resolve the user's project root

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

4. **Map Kibana data view → ES index pattern** (skip when possible)

   **Fast path — prefer this**: if the input already gives you a `project.keyword` filter (or any other strong field filter that pins the data), query with `index: "_all"` and the filter directly. The right index can be inferred afterwards from the `_index` field on hits if you really need it. This skips the entire discovery flow below and avoids the 80KB+ `list_indices` truncation.

   Use the discovery flow below ONLY when:
   - You have no strong filter and need to narrow search to a specific data stream, OR
   - The user explicitly asks "only logs from <data view>"

   Discovery flow (when needed):
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

   **GATE — Read `references/step7-es-query.md` NOW** for the full procedure (filter requirements, aggs ban, token budget, stack-trace dedupe). Do not write any ES query before reading it; this content does not survive context dilution if you only read it once at the start of the conversation.

8. **Distinct user count** (when meaningful)

   Many backend logs do NOT carry `customerid` / `accountid`. Workflow:

   a. Sample 1 hit from the dominant project: `size: 1, _source: "*"`
   b. Inspect fields. If no `customerid`, `accountid`, `userid`, `account_id` etc. → write `n/a` in the report.
   c. If a user-id field exists: pull `size: 100` hits, dedupe client-side, report as a lower bound (e.g. `~38+`). Note the cap.
   d. Do NOT spend extra effort if the field is absent — the report is useful without it.

9. **Cross-project drill-down**

   **GATE — Read `references/step9-cross-project-drill.md` NOW** for the trigger priority ladder, hop limit, and the mandatory pre-incident baseline correlation check. Do not pull a sibling error pattern into Root Cause without the procedure in that file.

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

   **GATE — write the scope table out in chat before continuing**, even if it has only one row. Without an explicit scope table, you have no basis to decide whether step 11 is mandatory or optional.

   ### 10b. Read code (in-scope only; required when impact involves them)

   - **Backend**: locate the failing endpoint/function from log clues (URL path, controller name, method name); inspect error handling and outbound calls.
   - **Frontend**: grep the failing API name (taken from the backend log) and read its call site. Determine: is the error caught? Does the UI fall back to empty / placeholder / error state / blank? Is there a retry?
   - **Impact wording**: derive from frontend code what the user actually sees, then write the Impact field per the rules in step 12 (HARD RULES). Do NOT include file paths, line numbers, or code mechanics here.

   **Hard rule for frontend lookup**: if the originating service is `-backend` / `.backend` and the report's Impact will describe user-visible behavior, locating the frontend repo via 10a.e is REQUIRED — backend code alone cannot tell you how the error surfaces to the user. If the frontend repo is not found under the project root, Impact must say so explicitly in Unknowns instead of guessing.

   If a–e all failed for a repo you needed (e.g. originating project's frontend not under root), list in **Unknowns**: "需要 `<project>` 的 repo 路徑 / 請執行 `/add-dir <path>`".

11. **Verify infra metrics**

    **GATE — Read `references/step11-infra-metrics.md` NOW** for the full procedure (in-scope vs out-of-scope branch, service-token extraction, datasource-first query flow with Prometheus + InfluxDB recipes, dashboard fallback, mandatory CPU + Memory + restart scan, mean+max + 1-min-bin aggregation, Plan block requirement).

    The reference is the source of truth for this step; this skill body is intentionally thin so the rules arrive fresh in context when you actually run the step, not stale at conversation start.

12. **Produce the report**

   **GATE — Read `references/step12-report.md` NOW** for the full procedure (pre-report final check, HARD RULES on Impact wording, GMT+8 rule, Chinese full template, English short template). Do not start writing the report before reading; the formatting rules and Impact constraints will not survive context dilution from the preceding tool calls.

---

## Guardrails

- **No unbounded ES queries.** Every search MUST include `@timestamp` range + `project.keyword` + `level.keyword` + `size` cap. No `*` / `match_all` queries.
- **No fabricated numbers.** Distinct user counts, request counts, customer ids — only report what the aggregation actually returned. If a field is missing, write `n/a`, never estimate.
- **No fabricated root causes.** If code is needed and unavailable, the report's Root Cause must say "需要看 code 才能確認" and the Unknowns must request the repo path. Do not pattern-match a guess.
- **No fabricated unknowns.** Unknowns may only contain: (a) facts about out-of-scope services (per step 10a scope table), (b) data that the available tools / permissions cannot reach, or (c) decisions that need a human (business / ownership). "Need to check Grafana for CPU", "should confirm pod restart" or any item the agent can answer with an MCP query is NOT a valid Unknown — go and check it.
- **Cross-project drill is bounded** — max 2 hops. List the chain if you stop early.
- **Same-name service across clusters is the default, not the exception.** When the candidate upstream is a service that could plausibly run in multiple tiers (RKE / GKE / VM / multi-region), assume there's a chance the same name exists in more than one of them simultaneously. Always anchor on prod config (hostname / DNS / IP from the calling service's source) before touching metrics — see step 11.0.
- **Project → repo mapping is per-user.** Get it from `add-dir` paths or ask the user to `/add-dir`. Never hardcode paths and never persist to memory (per-project memory doesn't help cross-project triage).
- **Honor user-mentioned excluded indices.** If the user mentions patterns to skip (e.g. lower-priority product lines, test indices) during the conversation, exclude them from queries. Only include excluded patterns if the user explicitly asks.
- **Output language order is fixed**: Traditional Chinese first (full), English second (super-short two lines). No language headings ("中文版" / "English") in the output. Order: Root Cause → Impact → How to Resolve → Unknowns.
- **Warning level handling**: include only when the originating signal is warning-level or the user asks. Always count warning separately from error/fatal in stats.
