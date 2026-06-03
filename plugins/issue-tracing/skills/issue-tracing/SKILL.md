---
name: issue-tracing
description: Use when the user provides a Grafana or Kibana/ELK URL and asks to investigate an alert, error, incident, or anomaly, or when the user runs /issue-tracing.
---

# Issue Tracing

On-call triage assistant. Takes a Grafana or Kibana URL (or alert description) and produces a structured **Root Cause / Impact / How to Resolve / Unknowns** report in both Traditional Chinese and English.

> **This skill is a step-by-step SOP, not a reference document.** First read the operating principle below — it sets the mode (Look vs Report). **In Report mode**, each step has rules and gates you MUST execute and acknowledge in chat before moving to the next; reading the rules without writing the required outputs (scope table, query plan, etc.) violates the skill, and "I'll just write the report now" before completing every step is skipping work. **In Look mode** you intentionally stop after surfacing the filtered logs — that is not skipping, it is the principle. Do not run the Report-mode pipeline unasked.

**Input** (`$ARGUMENTS` optional):
- Grafana dashboard / panel URL
- Kibana Discover URL
- Plain alert description (then ask user for a URL)

---

## Operating principle: execute the user's filter first, expand only on demand

The URL's filters ARE the user's scope and intent — not a loose starting point to broaden. Your **first action** is always: run the URL's filters **exactly as given** (resolved per step 4) and surface the matching logs. Then **read what came back and let it drive the next move** — only fetch more if interpreting the first pass shows you genuinely need it.

- A URL already filtered to `level=error` means "show me these errors" → return them, read the dominant pattern, answer. A URL with a broader filter means "show me what matches that" → same discipline. Either way, honor the filter the user sent; do not substitute your own.
- **Do NOT pre-emptively fan out.** Baseline windows, distinct-user counts (step 8), cross-project drill (step 9), infra metrics (step 11), extra projects, or a wider time range are **not reflexive**. Run them only when ONE of these holds:
  - the user explicitly wants a full **Root Cause / Impact report**, OR
  - interpreting the first-pass results shows you genuinely need more (e.g. the logs alone don't explain the failure, or you can't distinguish a spike from background).
- **Two modes:**
  - **Look mode (default):** step 1 (preflight) → step 4 (resolve data view) → step 7 first query (run the URL's filters verbatim), surface the matching logs + a short read of the dominant pattern → **stop**, and offer the deeper report. Don't run it unasked. (Skip steps 5–6 for a Kibana URL.)
  - **Report mode (only when asked / clearly warranted):** continue through steps 5–12 (the full Root Cause / Impact pipeline). The GATEs in those steps apply only once you're in this mode.

If unsure which mode, default to Look mode and ask.

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
   - Extract filters: `env`, `project`, `level`, KQL `query` — copy each filter's exact clause (field path + `match_phrase`, e.g. `match_phrase:(project:...)` or `match_phrase:(project.keyword:...)`), to replicate verbatim later (see step 4b-bis)
   - Extract `dataViewId` — this is an opaque id, NOT an index name; resolve it to the real index pattern via `.kibana` in step 4a
   - If URL contains `view/<id>` (saved search), note the saved-search id; resolve its bundled query + filters + referenced data view from `.kibana` in step 4a. The URL state filters override/extend the saved-search filters.

   **Time buffer**: expand the parsed range by ±5 minutes when querying.

3. **Determine investigation path**

   | Input | Path |
   |---|---|
   | Grafana dashboard URL (no `viewPanel`) | Read whole dashboard summary + every panel query, identify which panels show anomaly in the time window |
   | Grafana single panel URL (`viewPanel=panel-N`) | Focus on that panel only |
   | Kibana URL | Skip Grafana → resolve data view (step 4) → run the URL filter (step 7 first query). Stop there unless in Report mode. |

4. **Resolve the Kibana data view → real ES index pattern** (do this BEFORE any ES query)

   A Kibana URL gives you a `dataViewId` (and, for `view/<id>`, a saved-search id) — **not** an index name. Resolve it to the real ES index pattern *deterministically*. Do not guess from the data view's display name, and do not lean on `_all`.

   ### 4a. Resolve the dataViewId from `.kibana` (authoritative — do this first)

   Kibana stores every data view as a saved object in the `.kibana*` indices. Read it directly:

   ```
   index: ".kibana*"
   queryBody: { "size": 5, "query": { "ids": { "values": ["index-pattern:<dataViewId>"] } },
               "_source": ["index-pattern.title", "index-pattern.name"] }
   ```

   - `index-pattern.title` is the **real ES index pattern** you query against — often a data-stream name or a comma-separated list of patterns.
   - `index-pattern.name` is only the **display label** in the Kibana UI and frequently differs from `title` (e.g. display `foo-bar` → title `bar-logs-foo`). **Never query the display name.**

   For a saved search (`view/<id>` in the URL), read `search:<savedSearchId>` the same way: `search.kibanaSavedObjectMeta.searchSourceJSON` holds the bundled query + filters, and `references[]` maps each filter / the main query to an `index-pattern` id — resolve those ids the same way. The saved search's `title` / `description` also tell you what the view is *for* (useful sanity check on which service you're actually looking at).

   Then query the resolved `title` **verbatim** — a data-stream title auto-expands its backing indices.

   **Do NOT append `*` to the resolved title.** A data-stream name `<stream>` and a name-prefix wildcard `<stream>*` are NOT the same: a data stream's backing indices are named `.ds-<stream>-<date>-<n>` and start with `.ds-`, so a `<stream>*` wildcard does NOT match them — it only matches plain indices literally named `<stream>...`. Querying the exact name resolves the data stream; appending `*` silently drops every data-stream doc. Pass the title exactly as stored (only honor a `*` that is already part of the stored title).

   ### 4b. Why not `_all` / bare wildcards — the silent data-stream trap

   `_all`, bare `*`, and `<name>*` name-prefix wildcards **do NOT match hidden indices, and data-stream backing indices (`.ds-*`) are hidden.** So any of them + a perfect `project` / `env` / `level` filter can return **0 hits while the data exists** in a data stream. **A `0` from `_all` or a `<name>*` wildcard is never authoritative** — it is not "no such error" and it is not grounds for a wrong-cluster conclusion. Always query the resolved index-pattern `title` from 4a verbatim, which expands data streams correctly. (`_all` is fine only for a quick cross-check once you already know the data lives in a plain, non-hidden index.)

   ### 4b-bis. Match your filter type to the field mapping — `.keyword` may not exist

   Don't blindly default to `term` on `<field>.keyword`. The authoritative move: **copy the URL's filter clause verbatim — same field path, same query type.** Kibana URL filters carry the exact query, e.g. `query:(match_phrase:(project:<p>))` OR `query:(match_phrase:(project.keyword:<p>))` — the field path differs per data view and the type is `match_phrase`, never `term`. Replicate that clause as-is; do NOT "upgrade" it to `term <field>.keyword`.

   Why it matters: data streams often map `project` / `env` / `level` as plain `text` (or `match_only_text`) with **no `.keyword` sub-field**, so a `term project.keyword` on a missing field matches **nothing** — a false `0` with no error. `match_phrase` on whichever field the URL names sidesteps this (and also catches value-casing like `"Error"` vs `"error"`). If you must build a filter the URL didn't give you, sanity-check first: sample one doc (`size: 1, _source: "*"`) or `get_mappings` to see whether `<field>.keyword` exists. A `match <field>` that returns hits while `term <field>.keyword` returns 0 is the tell that the keyword sub-field is missing.

   ### 4c. "0 hits" diagnostic ladder (walk in order before concluding "not found")

   When the fully-filtered query returns 0, do NOT jump to "wrong cluster / no data". Step down:
   1. **Are you querying the resolved `title`, not `_all` / the display name?** If not, re-run against the 4a title.
   2. **Are you on the exact title, or did you append `*`?** `<name>*` skips data-stream backing indices (see 4a). Re-run on the verbatim title.
   3. **Drop filters one at a time**, keeping the time range — remove `level`, then `project`, then `env`. The first removal that yields hits is the culprit. Two common traps, both producing a false 0:
      - **`.keyword` sub-field doesn't exist** — `term project.keyword: "<p>"` matches nothing if the field is plain `text` (see 4b-bis). If `match project: "<p>"` returns hits but `term project.keyword` returns 0, switch to `match_phrase` on the field path the URL actually names (bare or `.keyword`).
      - **Value casing** — `level.keyword: "error"` (exact) misses a value stored as `"Error"` / `"ERROR"`, while `match_phrase` on the analyzed `level` field lowercases and matches it.
   4. **Confirm the index pattern has *any* data in the window** (time-only query). Data present but your filters yield 0 ⇒ field/value/mapping mismatch (steps 2–3), not a missing cluster.
   5. **Only after 1–4**, consider cross-cluster: `mcp__elasticsearch__search` connects to ONE ES endpoint, but the URL's Kibana may federate via cross-cluster search (CCS) to a remote ES your single-endpoint connection doesn't include. Say so explicitly and ask the user which ELK / datasource matches the URL. If browser tools + the user's logged-in session are available, offer to open the Kibana URL and read the results directly instead of concluding the error doesn't exist.

   ### 4d. Discovery flow (fallback only — when 4a can't resolve, e.g. no `.kibana` read access)

   1. **List data streams** — call `mcp__elasticsearch__list_indices`, extract unique prefixes from `.ds-<prefix>-*` entries.
   2. **When a data-stream name / wildcard returns 0 hits** even though backing indices exist: pull the concrete backing index names out of the (often 80KB-truncated) `list_indices` output with `jq`, filter to the days in your time window, and pass them as an explicit comma-separated `index` list. An exact single-day index is also the fastest query path (least shard fan-out).
   3. **Match by name** — a data view like `<x>-<y>` typically maps to a data stream like `<y>-logs-<x>`, `<x>-<y>`, or similar — show candidates and pick the one that returns hits with the expected `project` filter (query each candidate by its exact name, no trailing `*`).
   4. **Ask the user** — if matching is ambiguous after looking at hits, ask once. Cache the answer in conversation context only (do not write to memory).

   Honor any **excluded patterns** the user mentions (e.g. test / lower-priority product lines). Default: include everything. If the data center / cloud is unclear, query all confirmed patterns in parallel.

5. **Run Grafana panel queries** *(Report mode / dashboard URLs only)*

   For each relevant panel from step 3:
   - Call `mcp__grafana__get_dashboard_panel_queries` with `uid` (and `panelId` if known)
   - Inspect each query's `datasource.type`:
     - `elasticsearch` → take the KQL string and run via ES (step 7). Do not call Grafana to execute; query ES directly.
     - `prometheus` / `loki` / other → use the corresponding Grafana mcp tool (`query_prometheus`, `query_loki_logs`, etc.) with the panel's `processedQuery` and the parsed time range.
   - For dashboards used to interpret meaning (no `viewPanel`), report each panel: title, what it measures, observed value vs expected, whether it shows anomaly.

6. **Identify candidate projects** *(Report mode; skip when the URL already pins the project)*

   Source the candidate project list from these, in order:

   a. **Grafana panel legend** (most reliable for dashboard URLs): when a panel groups by `project.keyword`, the legend table lists projects with totals directly. Two ways to obtain it:
      - Ask the user to read the legend off the screen (Name / Total columns)
      - Call `mcp__grafana__get_panel_image` to render the panel and inspect the legend
   b. **Sample hits**: if no panel legend, run one query with `size: 50` over the time window with the panel's filters but **no project filter**. Tally `project` field across hits client-side. This is a coarse top-K but bounded by `size`.
   c. **Kibana URL filters**: if the URL has `project.keyword: is one of [...]`, use that list verbatim.

   Do NOT enumerate by trying every known project name — brittle and slow.

7. **Run ES queries**

   **First query = the URL's filters, verbatim (Look mode — always do this).** Run exactly the filters the URL carries (resolved per step 4: same index, same field paths, `match_phrase`), `sort @timestamp desc`, a small `size` (e.g. 5–10) to surface the matching logs, plus one `size: 0` + `track_total_hits` for the total. Read the dominant message pattern. **This is the primary deliverable** — for a tightly-scoped URL (e.g. already filtered to `level=error`) this is often the whole answer: report the hits + pattern and stop, per the operating principle.

   **Per-project counts, baselines, dominant-pattern weighting (Report mode only):** the rest of this step — per-candidate-project counts, pre-incident baseline ratios, pattern verification — runs only when you're producing a full Root Cause / Impact report, or when the first-pass logs don't explain the failure. Don't fan out by reflex.

   **GATE — Read `references/step7-es-query.md` NOW** (before any ES query) for filter requirements, aggs ban, token budget, and stack-trace dedupe — these apply to both the first query and any report-mode counts. Do not write any ES query before reading it; this content does not survive context dilution if you only read it once at the start of the conversation.

8. **Distinct user count** *(Report mode; when meaningful)*

   Many backend logs do NOT carry `customerid` / `accountid`. Workflow:

   a. Sample 1 hit from the dominant project: `size: 1, _source: "*"`
   b. Inspect fields. If no `customerid`, `accountid`, `userid`, `account_id` etc. → write `n/a` in the report.
   c. If a user-id field exists: pull `size: 100` hits, dedupe client-side, report as a lower bound (e.g. `~38+`). Note the cap.
   d. Do NOT spend extra effort if the field is absent — the report is useful without it.

9. **Cross-project drill-down** *(Report mode; only if the failure points outside the filtered project)*

   **GATE — Read `references/step9-cross-project-drill.md` NOW** for the trigger priority ladder, hop limit, and the mandatory pre-incident baseline correlation check. Do not pull a sibling error pattern into Root Cause without the procedure in that file.

10. **Code inspection & scope check** *(Report mode)*

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

   **Scope follows where the abnormal response is produced, NOT what triggered it.** A bot / scheduled / upstream trigger does NOT exempt an in-scope service that produced the error (e.g. threw the 500) from reading code. "The trigger was a bot" is never a reason to skip 10b for an in-scope service — the trigger source goes in the Root Cause fact layer (step12 HARD RULE #4), it does not shrink the code-reading obligation.

   **GATE — write the scope table out in chat before continuing**, even if it has only one row. Without an explicit scope table, you have no basis to decide whether step 11 is mandatory or optional.

   ### 10b. Read code (in-scope only; required when impact involves them)

   - **Backend**: locate the failing endpoint/function from log clues (URL path, controller name, method name); inspect error handling and outbound calls.
   - **Intent vs defect**: when you can't tell whether an error is a real bug or intended behavior, `git blame` the failing line and read the introducing commit's message to determine intent. Intent being correct (e.g. deliberately rejecting a bad token) does NOT mean the implementation is correct — returning an unhandled 500 instead of a 403 is still a defect. Feed both findings into the step12 Root Cause judgment layer.
   - **Frontend**: grep the failing API name (taken from the backend log) and read its call site. Determine: is the error caught? Does the UI fall back to empty / placeholder / error state / blank? Is there a retry?
   - **Impact wording**: derive from frontend code what the user actually sees, then write the Impact field per the rules in step 12 (HARD RULES). Do NOT include file paths, line numbers, or code mechanics here.

   **Hard rule for frontend lookup**: if the originating service is `-backend` / `.backend` and the report's Impact will describe user-visible behavior, locating the frontend repo via 10a.e is REQUIRED — backend code alone cannot tell you how the error surfaces to the user. If the frontend repo is not found under the project root, Impact must say so explicitly in Unknowns instead of guessing.

   If a–e all failed for a repo you needed (e.g. originating project's frontend not under root), list in **Unknowns**: "需要 `<project>` 的 repo 路徑 / 請執行 `/add-dir <path>`".

11. **Verify infra metrics** *(Report mode)*

    **GATE — Read `references/step11-infra-metrics.md` NOW** for the full procedure (in-scope vs out-of-scope branch, service-token extraction, datasource-first query flow with Prometheus + InfluxDB recipes, dashboard fallback, mandatory CPU + Memory + restart scan, mean+max + 1-min-bin aggregation, Plan block requirement).

    The reference is the source of truth for this step; this skill body is intentionally thin so the rules arrive fresh in context when you actually run the step, not stale at conversation start.

12. **Produce the report**

   **GATE — Read `references/step12-report.md` NOW** for the full procedure (pre-report final check, HARD RULES on Impact wording, GMT+8 rule, Chinese full template, English short template). Do not start writing the report before reading; the formatting rules and Impact constraints will not survive context dilution from the preceding tool calls.

---

## Guardrails

- **No unbounded ES queries.** Every search MUST include `@timestamp` range + a project filter + a level filter + `size` cap.
- **Copy the URL's filter clause verbatim — do NOT default to `term .keyword`.** Replicate the URL's exact query: same field path (`project` or `project.keyword`, differs per data view) and `match_phrase` (never `term`). `term <field>.keyword` matches nothing when the field has no `.keyword` sub-field (common on data streams mapping `project`/`env`/`level` as `text`) → a false `0` with no error. Build your own `term <field>.keyword` only after confirming the sub-field exists (sample a doc / `get_mappings`). See step 4b-bis / step7 reference.
- **Resolve the data view before trusting any count.** A Kibana `dataViewId` and a data view's display `name` are NOT index names. Read `.kibana*` (`index-pattern:<dataViewId>` → `index-pattern.title`) and query the `title` **verbatim — never append `*`** (a `<name>*` wildcard skips a data stream's hidden `.ds-` backing indices). The display `name` often differs from `title` (`foo-bar` → `bar-logs-foo`). Skipping this — or appending `*`, or assuming `.keyword` — is the #1 cause of false "not found" / false "wrong cluster" conclusions.
- **Where `*` is dangerous vs fine** — the heap-killer is an unbounded full scan, not the character `*`:
  - `query` / `match_all` with no filter → **forbidden** (this is what exhausts ES heap).
  - Index-level wildcard (`.ds-...-prod-*`) or `_all` → allowed ONLY with a strong filter (project + time + level), but prefer an exact single-day backing index — it is far faster and avoids multi-shard fan-out timeouts. **`_all`, bare `*`, and `<name>*` name-prefix wildcards skip hidden indices, and data-stream backing indices (`.ds-*`) are hidden — so they silently miss all data-stream logs and return 0 with no error.** A 0 from any of them is never proof the data is absent; resolve the data view's real index pattern first (step 4a) and query the exact title — see step 4.
  - `_source: "*"` → fine, but use it once to inspect schema, then list only the fields you need.
- **Counting rows: `size: 0` + `track_total_hits: true`, NEVER aggs.** The `mcp__elasticsearch__search` wrapper STRIPS aggregation results, so a `date_histogram` / `terms` agg pays the full aggregation cost AND returns nothing — the #1 source of slow queries and timeouts. And without `track_total_hits: true` the total caps at 10000 (a real 72k reads as "10000"), which silently breaks every baseline ratio and impact number. One filtered `size: 0` query per bucket instead.
- **No fabricated numbers.** Distinct user counts, request counts, customer ids — only report what the aggregation actually returned. If a field is missing, write `n/a`, never estimate.
- **No fabricated root causes.** If code is needed and unavailable, the report's Root Cause must say "需要看 code 才能確認" and the Unknowns must request the repo path. Do not pattern-match a guess.
- **No fabricated unknowns.** Unknowns may only contain: (a) facts about out-of-scope services (per step 10a scope table), (b) data that the available tools / permissions cannot reach, or (c) decisions that need a human (business / ownership). "Need to check Grafana for CPU", "should confirm pod restart" or any item the agent can answer with an MCP query is NOT a valid Unknown — go and check it.
- **Cross-project drill is bounded** — max 2 hops. List the chain if you stop early.
- **Same-name service across clusters is the default, not the exception.** When the candidate upstream is a service that could plausibly run in multiple tiers (RKE / GKE / VM / multi-region), assume there's a chance the same name exists in more than one of them simultaneously. Always anchor on prod config (hostname / DNS / IP from the calling service's source) before touching metrics — see step 11.0.
- **Project → repo mapping is per-user.** Get it from `add-dir` paths or ask the user to `/add-dir`. Never hardcode paths and never persist to memory (per-project memory doesn't help cross-project triage).
- **Honor user-mentioned excluded indices.** If the user mentions patterns to skip (e.g. lower-priority product lines, test indices) during the conversation, exclude them from queries. Only include excluded patterns if the user explicitly asks.
- **Output language order is fixed**: Traditional Chinese first (full), English second (super-short two lines). No language headings ("中文版" / "English") in the output. Order: Root Cause → Impact → How to Resolve → Unknowns.
- **Warning level handling**: include only when the originating signal is warning-level or the user asks. Always count warning separately from error/fatal in stats.
