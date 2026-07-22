---
name: issue-tracing
description: Use when the user provides a Grafana or Kibana/ELK URL and asks to investigate an alert, error, incident, or anomaly, or when the user runs /issue-tracing.
---

# Issue Tracing

On-call triage assistant. Takes a Grafana or Kibana/ELK URL, **autonomously traces from the filtered logs down the call chain to the root cause**, and produces a structured **Root Cause / Impact / How to Resolve / Unknowns** report in both Traditional Chinese (full) and English (short).

> **This skill is a step-by-step SOP, not a reference document.** Read the operating principle below first — it sets the working contract: the URL's filter is your scope, and you drive the investigation to a root cause on your own, checking in with the user only when a decision genuinely needs a human. Several steps ask you to write a short artifact in chat (scope/chain note, query plan, evidence dump) — that is **internal discipline for auditability, not a request for the user's approval**: write it, then keep going. Do not skip it, and do not stop to wait for acknowledgment.

**Input** (`$ARGUMENTS` optional):
- Kibana / ELK Discover URL (carries the filter directly)
- Grafana dashboard / panel / alert URL (carries the filter or alert condition)
- Plain alert description (then ask user for a URL)

---

## Operating principle: filter-driven, autonomous to root cause, minimal check-ins

The URL's filter (or alert condition) **is the user's scope and intent** — you do not re-decide what to investigate. From there you run the investigation to completion yourself and produce the report. Do not stop after the first look to ask "want the full report?" — finding the root cause and reporting it IS the task.

1. **Recover the filter from the input** (step 2).
   - **ELK URL** → the embedded filter (time / env / project / level / KQL) already says exactly what the user is looking at. Replicate it verbatim; do not substitute your own scope.
   - **Grafana URL** → read what the panel filters on, or what the alert's firing condition is, and translate that into the equivalent ELK filter. The point of the Grafana input is to recover the *condition*, then investigate in the logs — not to tour the dashboard.

2. **Surface the filtered logs and read the dominant pattern** (steps 3–4). These logs are the anchor; everything downstream explains them. (The one exception — a pure-infra alert with no error-log correlate — is handled by step 4's infra-first pivot, which anchors on metrics instead.)

3. **Trace to the root cause on your own** (step 5). Follow the failure from the logs into the code and down the call chain — reading each service's code and confirming against its logs — until you reach the service where the fault actually originates, **or** you hit an ownership boundary (a service owned by another team). Keep going through your own team's services; do not stop at the first hop just because the first-pass logs were tidy.

4. **Produce the report** (step 6).

**Minimal check-ins (do NOT make the user drive):** anything the tools can answer, answer yourself — do not defer it to Unknowns and do not ask the user to run it for you. Pause for the user only when the decision truly needs a human:
- an ownership / business call (who owns this, is this acceptable, should we block this caller);
- code or logs you genuinely cannot reach after trying (e.g. a repo not present locally, a datasource behind cross-cluster search) — say precisely what you tried and what you need.

Everything in between — resolving data views, running counts, reading code, following the next hop, checking infra metrics — you do without asking.

---

## Steps

1. **Preflight: preload tools + resolve project root + load environment knowledge** (do this FIRST)

   ### 1a. Preload core deferred tools

   One `ToolSearch` for the always-used entry points so the first queries don't break narrative:

   - `mcp__elasticsearch__search`
   - `mcp__elasticsearch__list_indices`
   - `mcp__grafana__list_datasources`

   Load everything else on demand (Grafana panel/alert queries, Prometheus/Loki/InfluxDB queries, code-host / decode / id-lookup MCP tools, panel image). `ToolSearch` is cheap; preloading unused schemas is not.

   ### 1b. Resolve the project root (reading code is part of the normal flow)

   You will read service code in step 5 to confirm root cause and user impact, so resolve where the repos live up front:

   a. **Use the root that is already known** — the session's working directory, an `add-dir` path, or the local-repo convention recorded in the environment knowledge (see 1c). If the root is already granted/known, just use it; do not ask.
   b. **Only if no root can be resolved**, ask the user once to `/add-dir <their service repo root>`.

   Cache the resolved root. When a *specific* repo you need turns out not to be present under the root, that is not a reason to stop the whole investigation — read what you can, and tell the user which repo is missing (see step 5). Continue to 1c.

   ### 1c. Load environment knowledge (this is what fills the skill's placeholders)

   This skill is deliberately generic — it names no real hosts, indices, projects, clusters, or domains (see the open-source guardrail). When the URL points at an internal system and the session exposes a knowledge skill / doc describing **this organization's conventions**, load it now and pull the concrete values from it:

   - **Kibana / Grafana host + real index / data-stream names** → steps 3–4 (query the right source; know when one service's logs are split across multiple streams / clusters).
   - **Log field conventions** (which fields exist, `.keyword` or not, env value casing) → step 3 / step 4 (skips the trial-and-error that yields false `0` hits).
   - **Logging exceptions** (services whose logs are NOT in the default index — routed to APM / a separate stack) → step 3's 0-hits ladder, so you don't misread "different backend" as "no data".
   - **Project ownership + dependency / topology docs** → step 5 (which services are your team's vs another team's = the drill boundary; and a service's upstreams when its logs don't name them).
   - **Local-repo convention** (where each project is cloned, how a project name maps to a directory) → step 1b / step 5.
   - **Dashboard UIDs + metrics mental model** (shared vs per-project boards, template vars) → step 5's infra check.
   - **Decode / lookup tools** for opaque log values (encoded payloads, status bitflags, id↔id mapping) → step 4.

   If no such knowledge source exists, discover live as the steps describe. Continue to step 2.

2. **Recover the filter from the input**

   The output of this step is a concrete ELK filter set — index (to resolve in step 3), time range, and field filters (`env` / `project` / `level` / KQL) — **regardless of whether the input was ELK or Grafana**.

   ### 2a. ELK / Kibana URL (`*/app/discover#/...` or `.../view/<savedSearchId>`)

   - Extract `time.from` / `time.to`.
   - Extract each filter's **exact clause** — field path + query type, e.g. `match_phrase:(project:<p>)` OR `match_phrase:(project.keyword:<p>)` — to replicate verbatim later (see step 3's filter-mapping note). The field path differs per data view; the type is `match_phrase`, never `term`.
   - Extract `dataViewId` — an opaque id, NOT an index name; resolve it in step 3.
   - For `view/<id>` (saved search), note the id; its bundled query + filters + referenced data view resolve from `.kibana` in step 3. URL-state filters override/extend the saved-search filters.

   This embedded filter **is** the scope — do not broaden or narrow it.

   ### 2b. Grafana URL (`*-grafana.*/d/<uid>/...`, panel, or alert)

   Goal: recover the *condition*, translate to an ELK filter, then investigate in the logs.

   - **Dashboard / panel URL**: extract `uid`, `viewPanel` (panel id, optional), `from` / `to`, `var-*` template vars. For the anomalous panel(s), read the query and grouping with `mcp__grafana__get_dashboard_panel_queries` (or `get_dashboard_property` for raw targets). Pull the filter dimensions (service / project / level / env) and any log query behind the panel.
     - If a panel's datasource is `elasticsearch`, take its query/filters straight across into your ELK filter.
     - If it's `prometheus` / `loki` / `influxdb`, the panel tells you *which service and what condition* is anomalous → map that service + severity to the equivalent `project` / `level` ELK filter.
   - **Alert URL / alert context**: get the alert rule's firing condition (metric + threshold + labels) via the alerting MCP (`mcp__grafana__list_alert_groups` / alerting rule tools). Map its labels (service / project / severity) to the ELK filter.
   - Resolve relative time (`now-1h`) to absolute UTC.

   **Time buffer**: expand the parsed range by ±5 minutes when querying.

3. **Resolve the target index** (BEFORE any ES query)

   You need the real ES index pattern for the filter from step 2. **Pick it by input type first — do not guess the index name:**
   - **ELK URL** → you have a `dataViewId` (and maybe a saved-search id), **not** an index name → resolve it via 3a. Do not guess from the display name; do not lean on `_all`.
   - **Grafana URL** → you have **no** `dataViewId`. Get the index from, in order: (a) an `elasticsearch` panel's own datasource — it references a Kibana index-pattern by uid; resolve that uid via 3a exactly like a `dataViewId`; (b) the env-knowledge index / data-stream names (step 1c) for the service the panel / alert pointed at; (c) the 3e discovery flow. Then apply 3b–3d the same way.

   ### 3a. Resolve from `.kibana` (authoritative — do this first)

   Every data view is a saved object in `.kibana*`:

   ```
   index: ".kibana*"
   queryBody: { "size": 5, "query": { "ids": { "values": ["index-pattern:<dataViewId>"] } },
               "_source": ["index-pattern.title", "index-pattern.name"] }
   ```

   - `index-pattern.title` = the **real ES index pattern** to query — often a data-stream name or comma-separated list.
   - `index-pattern.name` = display label only, frequently differs from `title` (display `foo-bar` → title `bar-logs-foo`). **Never query the display name.**

   For a saved search (`view/<id>`), read `search:<savedSearchId>` the same way: `search.kibanaSavedObjectMeta.searchSourceJSON` holds the bundled query + filters, `references[]` maps each to an `index-pattern` id — resolve those the same way. The `title` / `description` also confirm which service the view is for.

   Query the resolved `title` **verbatim** — a data-stream title auto-expands its backing indices.

   **Do NOT append `*` to the resolved title.** A data stream's backing indices are named `.ds-<stream>-<date>-<n>` (they start with `.ds-` and are hidden), so a `<stream>*` name-prefix wildcard does NOT match them — it silently drops every data-stream doc. Pass the title exactly as stored (honor only a `*` already part of the stored title).

   ### 3b. Why not `_all` / bare wildcards — the silent data-stream trap

   `_all`, bare `*`, and `<name>*` wildcards **do NOT match hidden indices, and data-stream backing indices (`.ds-*`) are hidden.** So any of them + a perfect filter can return **0 hits while the data exists**. **A `0` from `_all` or a `<name>*` wildcard is never authoritative** — not "no such error", not grounds for a wrong-cluster conclusion. Always query the resolved `title` from 3a verbatim. (`_all` is fine only for a quick cross-check once you know the data lives in a plain, non-hidden index.)

   ### 3c. Match your filter type to the field mapping — `.keyword` may not exist

   **Copy the URL's filter clause verbatim — same field path, same query type.** URL filters carry the exact query, e.g. `match_phrase:(project:<p>)` OR `match_phrase:(project.keyword:<p>)` — replicate as-is; do NOT "upgrade" to `term <field>.keyword`. Data streams often map `project` / `env` / `level` as plain `text` with **no `.keyword` sub-field**, so `term project.keyword` matches **nothing** — a false `0` with no error. `match_phrase` on whichever field the URL names sidesteps this (and catches value-casing like `"Error"` vs `"error"`). If you must build a filter the URL didn't give you, first sample one doc (`size: 1, _source: "*"`) or `get_mappings` to check whether `<field>.keyword` exists.

   ### 3d. "0 hits" diagnostic ladder (walk in order before concluding "not found")

   1. **Querying the resolved `title`, not `_all` / the display name?** If not, re-run against the 3a title.
   2. **Exact title, or did you append `*`?** `<name>*` skips data-stream backing indices. Re-run on the verbatim title.
   3. **Drop filters one at a time** (keep the time range) — remove `level`, then `project`, then `env`. First removal that yields hits is the culprit. Two traps: `.keyword` sub-field missing (3c), and value casing (`level.keyword:"error"` misses `"Error"`; `match_phrase` lowercases and matches).
   4. **Confirm the index has *any* data in the window** (time-only query). Data present but filters yield 0 ⇒ field/value/mapping mismatch, not a missing cluster.
   5. **Service logs via an OTEL sink? Check the OTEL logs stream.** Many services (especially .NET) ship server logs through an OTEL log sink into a **separate OTEL logs data stream** (name per env, e.g. an `…otel-<env>` stream), keyed by `resource.attributes.service.name` — NOT the project stream, and NOT keyed by `project`. So a prod service can read `0` in the project streams while logging fine to OTEL. If the project streams return 0 for a service you know is running, resolve the concrete OTEL logs-stream name + service-name field from the environment knowledge (step 1c) and query there before concluding cross-cluster / absent. (A service's uat may still land in the project stream while its prod goes to OTEL — a prod `0` is not absence. The OTEL stream also carries access-log fields like response time / status code, handy for a latency check on the callee.)
   6. **Only after 1–5**, consider cross-cluster: `mcp__elasticsearch__search` hits ONE ES endpoint, but the Kibana may federate via cross-cluster search to a remote ES you don't include. Say so and ask the user which ELK / datasource matches the URL. If browser tools + the user's session are available, offer to open the URL and read it directly.

   ### 3e. Discovery flow (fallback only — when 3a can't resolve, e.g. no `.kibana` read access)

   1. **List data streams** — `mcp__elasticsearch__list_indices`, extract unique prefixes from `.ds-<prefix>-*`.
   2. **Data-stream name / wildcard returns 0 despite backing indices existing**: pull concrete backing index names from the (often truncated) `list_indices` output with `jq`, filter to the days in your window, pass them as an explicit comma-separated `index` list. An exact single-day index is also the fastest path (least shard fan-out).
   3. **Match by name** — a display like `<x>-<y>` typically maps to `<y>-logs-<x>` / `<x>-<y>` / similar. Query each candidate by exact name (no trailing `*`), pick the one that returns hits with the expected `project` filter.
   4. **Ask once** if still ambiguous after looking at hits. Cache in conversation context only.

   Honor any **excluded patterns** the user mentions (test / lower-priority lines). Default: include everything. If the cluster is unclear, query all confirmed patterns (respecting the concurrency ceiling).

4. **Run the filter, surface the logs, read the dominant pattern**

   **Run the recovered filter verbatim** (from step 2, resolved per step 3: same index, same field paths, `match_phrase`): `sort @timestamp desc`, small `size` (5–10) to surface the matching logs, plus one `size: 0` + `track_total_hits: true` for the total. This is the anchor — everything downstream explains these logs.

   **GATE — Read `${CLAUDE_PLUGIN_ROOT}/skills/issue-tracing/references/step7-es-query.md` NOW** (before any ES query) for filter requirements, the aggs ban, `track_total_hits`, `size`/token budget, stack-trace dedupe, and the dominant-pattern weighting method. This content does not survive context dilution if you only read it once at conversation start.

   Then, still in this step:
   - **Read the dominant pattern** — do NOT trust the first sample (recent ≠ most frequent). Weight patterns by pulling `_source` and bucketing the leading lines **client-side** — the `message` field is usually NOT filterable on server-log streams, so a `match_phrase` on it silently returns a false `0`; only weight via `match_phrase` once you have proven the field is searchable (see the reference for the full method).
   - **Decode opaque values before interpreting.** If a hit carries an unreadable value (encoded payload, status bitflag, an id needing mapping) and the environment (step 1c) exposed a decode / lookup MCP tool, use it — do not guess or report the raw blob.
   - **Distinct users** — sample 1 hit (`size: 1, _source: "*"`) and check for a user-id field (`customerid` / `accountid` / `userid` / …). If absent → `n/a`. If present → pull `size: 100`, dedupe client-side, report as a lower bound (note the cap). Do not spend more if the field is absent.
   - **Spike vs chronic** — when it matters for Root Cause, run the same filter over an **equal-length pre-incident window** and compare. Ratio ≈ 1 ⇒ chronic background / by-design, not caused by this incident (exclude from Root Cause). Sharp spike ⇒ event-driven.

   Output of this step: the originating project, the error shape, the weighted dominant pattern, scale, and (if available) affected users. Now enter the trace loop.

   **Infra-first pivot (no log correlate).** If the filtered logs are genuinely empty but the signal is real — typically a pure-infra Grafana alert (CPU / memory / saturation / restart) with no error-log correlate — and you have confirmed via the 0-hits ladder (3d) that the query is correct and the index has data, do NOT stall waiting for a failing code path. Set `current` = the service the alert/panel pointed at, still run **5a** to classify ownership (an infra check on another team's service stops at the boundary too), then jump to the **infra check (5d)** — skipping 5b/5c, which need a log-derived code path you don't have — and continue the loop normally (5e onward) from whatever the infra numbers reveal.

5. **Trace to the root cause — the autonomous loop**

   Set `current` = the originating project and start at 5a (on the infra-first pivot from step 4, still run 5a, then jump to 5d). Then loop:

   ### 5a. Classify `current` (the drill boundary)

   Using the environment knowledge (step 1c):
   - **Another team's service / not in your knowledge base → BOUNDARY. STOP the drill.** Record the hop and the boundary in Unknowns. The report may state what this upstream returned (e.g. 503 / timeout); *why it failed inside* belongs to its owner.
   - **Your team's service, resolvable locally under the project root** → read its code (5b).
   - **Your team's service but the repo is not present locally** → the root should let you read it (per step 1b / the environment's local-repo convention). If you still cannot read it, say so precisely (which repo, where you looked) and list it in Unknowns; continue only with what you can confirm. Do not silently guess its internals.

   ### 5b. Read the failing code path in `current`

   - **Locate the failure** from log clues (URL path, controller / method / function name). Inspect its error handling and outbound calls.
   - **Is the error produced here, or a downstream symptom?**
     - *Produced here* = a real defect or intended behavior in this service. Use `git blame` on the failing line + the introducing commit message to tell intent from defect. Intent being correct (e.g. deliberately rejecting a bad token) does NOT make the implementation correct — returning an unhandled 500 instead of a 403 is still a defect.
     - *Downstream symptom* = an outbound call failed / timed out / returned 5xx; the top-of-stack exception here is the *effect*, the cause is the next hop.
   - **User-visible surface**: if `current` is a `-backend` / `.backend` and the report's Impact will describe what the user sees, locate its frontend repo under the root (`<base>.frontend` / `<base>-frontend`) and read the call site — is the error caught? fallback / placeholder / blank? retry? Backend code alone cannot tell you how it surfaces. If the frontend repo isn't present, Impact must say so in Unknowns, not guess.

   ### 5c. Confirm against ELK

   Do not assert from code alone. Query `current`'s own logs to confirm the hypothesis — the outbound call that failed, its timing, the error host, the burst window. Apply the baseline/correlation check before folding any sibling pattern into Root Cause.

   ### 5d. Verify infra when the error shape is infra-shaped

   If the signal at `current` or its dependency is infra-shaped (timeout / 5xx / connection refused / OOM / pool exhaustion / redis timeout / throttling), verify infra metrics before writing Root Cause.

   **GATE — Read `${CLAUDE_PLUGIN_ROOT}/skills/issue-tracing/references/step11-infra-metrics.md` NOW** for the full procedure (anchor on prod config first, service-token extraction, datasource-first query flow with Prometheus + InfluxDB recipes, mandatory CPU + Memory + restart scan, mean+max at ≤1-min bins, the reverse-signal sanity check, and the required Plan block). Write the Plan block in chat, then dispatch in bounded-concurrency batches (≤2–3, see guardrails).

   ### 5e. Decide the next move

   - **Root cause confirmed at `current`** → exit the loop.
   - **Points to a downstream hop** → identify the next hop and set `current` to it, then repeat from 5a. Read `${CLAUDE_PLUGIN_ROOT}/skills/issue-tracing/references/step9-cross-project-drill.md` for how to identify the next hop (URL/host in the error → log naming another service → outbound config in code → the environment's dependency docs), the **slow-but-healthy pointer** (a 200-but-slow hop is blocked on *its* downstream — keep going, don't blame it), the **caller-direction drill** (when the question is *who triggered* it — bot / surge / new data), and the correlation check.
   - **Stuck — cannot confirm a root cause at `current` AND cannot identify a next hop** (e.g. `current`'s repo or logs are unreachable per 5a) → exit the loop and report what you have, recording the gap in Unknowns. Do not spin waiting for a signal that isn't reachable.

   ### 5f. Loop discipline

   - **Every hop must be backed by real call data** — a host in an error, a log naming the service, an outbound call in code, or a documented dependency. Never invent a hop.
   - **Boundary-driven, not count-capped**: keep drilling through your team's services until you reach the root cause or an ownership boundary (5a). There is no fixed hop limit — but if the chain runs unusually long (**runaway guard: ~5 hops**), stop, lay out the full chain, and hand the decision to the user.
   - **Write the running chain in chat as a short note** (`originating → hop A → hop B …`, with each hop's role: erroring / slow-but-healthy / root cause / boundary), and the infra Plan block when 5d fires. This is internal auditability — write it and keep going; do not wait for the user.

6. **Produce the report**

   **GATE — Read `${CLAUDE_PLUGIN_ROOT}/skills/issue-tracing/references/step12-report.md` NOW** for the full procedure (pre-report evidence dump, HARD RULES on Impact wording, the GMT+8 rule, the two-layer Root Cause with trigger-source-first, and the Chinese-full + English-short templates). Do not start writing before reading; these rules will not survive context dilution from the preceding tool calls.

   Write the report once the loop exits with a confirmed root cause, or with a clearly-recorded ownership boundary (state what the boundary upstream returned and that the internal cause is the owner's).

---

## Guardrails

- **Open-source skill — keep the source generic; never bake in company info.** These skill files are published. NEVER write real host names, index / data-stream names, cluster names, internal domains, project or department names, repo roots, dashboard UIDs, or any customer / business data into this SKILL.md or its references. Use placeholders (`<svc>`, `<dc>`, `<internal-domain>`, `<project>`, `<root>`) and pull the real values only from the environment knowledge loaded at runtime (step 1c). The report the skill produces is for the user (internal); do not publish it or send investigation data (logs, service names, customer ids) to any external / third-party service.
- **Drive to the root cause; check in only for human decisions.** Do not stop after the first look to ask whether to continue, and do not defer to Unknowns anything a tool can answer. Ask the user only for an ownership / business decision, or when code / logs are genuinely unreachable (say what you tried). Steps that ask for a scope/chain note, query plan, or evidence dump want them written in chat for auditability — write and continue, do not wait for approval.
- **No unbounded ES queries.** Every search MUST include an `@timestamp` range + a project filter + a level filter + a `size` cap.
- **Cap concurrent ELK / Grafana MCP calls.** These backends sit behind a connection / rate ceiling; firing many `mcp__elasticsearch__search` / `mcp__grafana__*` calls in one block exhausts it and the investigation hangs. Send **at most 2–3 in parallel per block, wait, then send the next**; on any connection / timeout / rate error, drop to **sequential**.
- **Copy the URL's filter clause verbatim — do NOT default to `term .keyword`.** Same field path (`project` or `project.keyword`, differs per data view) and `match_phrase` (never `term`). `term <field>.keyword` matches nothing when the field has no `.keyword` sub-field (common on data streams) → a false `0`. Build your own `term <field>.keyword` only after confirming the sub-field exists (sample a doc / `get_mappings`). See step 3c / `references/step7-es-query.md`.
- **Resolve the data view before trusting any count.** A `dataViewId` and a display `name` are NOT index names. Read `.kibana*` (`index-pattern:<dataViewId>` → `index-pattern.title`) and query the `title` **verbatim — never append `*`** (a `<name>*` wildcard skips a data stream's hidden `.ds-` backing indices). Skipping this — or appending `*`, or assuming `.keyword` — is the #1 cause of false "not found" / "wrong cluster" conclusions.
- **Where `*` is dangerous vs fine** — the heap-killer is an unbounded full scan, not the character `*`:
  - `query` / `match_all` with no filter → **forbidden** (exhausts ES heap).
  - Index-level wildcard (`.ds-...-prod-*`) or `_all` → allowed ONLY with a strong filter (project + time + level), but prefer an exact single-day backing index (faster, avoids multi-shard fan-out). `_all`, bare `*`, and `<name>*` skip hidden indices — a 0 from any of them is never proof of absence.
  - `_source: "*"` → fine, but use it once to inspect schema, then list only the fields you need.
- **Counting rows: `size: 0` + `track_total_hits: true`, NEVER aggs.** The `mcp__elasticsearch__search` wrapper STRIPS aggregation results, so a `date_histogram` / `terms` / `cardinality` agg pays full cost AND returns nothing. Without `track_total_hits: true` the total caps at 10000 (a real 72k reads as "10000"), silently breaking every ratio. One filtered `size: 0` query per bucket instead.
- **No fabricated numbers.** Distinct users, request counts, customer ids — only what the query actually returned. Missing field → `n/a`, never estimate.
- **No fabricated root causes.** If code is needed and unavailable, Root Cause says "需要看 code 才能確認" and Unknowns requests the repo path. Do not pattern-match a guess.
- **No fabricated unknowns.** Unknowns may contain only: (a) facts about a service owned by another team (the boundary at 5a), (b) data the tools / permissions cannot reach, (c) a decision that needs a human. Anything an MCP query can answer is NOT a valid Unknown — go check it.
- **Drill boundary is ownership, not a hop count.** Keep drilling through your team's services until root cause or a service owned by another team; runaway guard ~5 hops. Every hop must be backed by real call data; list the chain when you stop.
- **Same-name service across clusters is the default, not the exception.** A service may run in multiple tiers (RKE / GKE / VM / multi-region) at once. Anchor on prod config (hostname / DNS / IP from the caller's source) before touching metrics — see `references/step11-infra-metrics.md`.
- **Project → repo mapping is per-user.** Resolve from the known root (working dir / add-dir / the environment's local-repo convention). Never hardcode paths in this skill and never persist them to memory.
- **Honor user-mentioned excluded indices.** Exclude patterns the user says to skip; include them only if explicitly asked.
- **Output language order is fixed**: Traditional Chinese first (full), English second (super-short two lines). No language headings. Order: Root Cause → Impact → How to Resolve → Unknowns.
- **Warning level**: include only when the originating signal is warning-level or the user asks. Always count warning separately from error/fatal.
