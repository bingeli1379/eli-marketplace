# Step 11 — Verify infra metrics

Once an upstream service is suspected (from the drill, `step9-cross-project-drill.md`), use its ownership classification (your team's readable service = in-scope; a service owned by another team = out-of-scope) AND the shape of the error:

- **In-scope upstream + infra-shape signal in log** → REQUIRED. Infra-shape signals: HTTP `502/503/504`, `connection refused`, `timeout`, `TaskCanceledException`, `Polly TimeoutRejectedException`, `OOMKilled`, throttling, redis timeout, "No server is available", DB connection pool exhaustion, etc. These error shapes only get explained by infra metrics, so checking is required before writing Root Cause.
- **In-scope upstream + app-level root cause clearly visible in log** → OPTIONAL. App-level signals: validation errors, auth misconfig, deserialization / parse errors, explicit business-logic exceptions, code bugs with stack traces pointing at app code only. Infra numbers do not explain these, so a CPU/Memory check is noise. The evidence dump in the report step (`step12-report.md`) should mark infra as `n/a (app-level root cause)` for that service.
- **Out-of-scope upstream** → OPTIONAL. The default report can stop at "upstream `<svc>` returned 503/timeout"; deeper Root Cause (why `<svc>` failed) belongs to the owning team and may stay in Unknowns. Run 11 only if the user asks for a deeper dive or the log payload is too thin to confirm the upstream is the bottleneck.

When in doubt about which category the error falls into, default to REQUIRED — it is cheaper to verify infra and find nothing than to ship a report that missed an infra-side root cause.

**Approach: query the datasource directly. Do NOT start from dashboards.** Dashboards are visualization for humans; for an agent, they are stale, full of unresolved scopedVars, and may not exist for the right tier. The metrics live in the datasource — go there first.

**GATE — Plan-then-batch execution. The Plan block is required.** Before issuing any infra query, you MUST write a Plan block in chat with this shape:

```
Infra query plan:
- Datasources: <list with type + uid>
- Hosts/instances: <list>
- Metrics per host: <CPU, Memory, ...>
- Time range: <from> ~ <to>
- Total queries: <N>
```

Then dispatch the queries in **bounded-concurrency batches — at most 2–3 calls per tool-use block** — and wait for each batch to return before sending the next. **Do NOT fire all N in one block.** The ELK / Grafana MCP backends sit behind a connection / rate ceiling; a large parallel fan-out exhausts it and the whole investigation hangs (observed repeatedly — the symptom is calls that never return). If any query comes back with a connection / timeout / rate error, **drop to sequential (one call at a time)** for the remainder. The Plan block still enumerates all N up front so nothing is missed — it controls *pacing*, not a single mega-batch. No Plan block → no queries; skipping it is how the agent ends up missing entire datasources or instances.

## 11.0 Anchor on prod config FIRST

Before searching any datasource, read the calling service's source to find the upstream config key (e.g. `BaseAddress = config.GetValue("UpstreamApi")`, `_httpClient.BaseAddress = ...`, helm values, ConfigMap, `appsettings.Production.json`, env vars). Resolve to the **actual prod hostname / DNS / IP** the caller will hit at runtime.

Use that hostname as the **primary seed** for datasource lookup. Do NOT start from the service name alone. Service names collide across clusters (RKE / GKE / VM / multi-region); the prod config is the only authoritative pointer to which deployment serves real traffic.

When the upstream candidate came from log host extraction (the drill's trigger #1, `step9-cross-project-drill.md`) you already have the hostname — still cross-check against prod config to make sure it matches.

If the calling service is not in scope (no source code available), record this in the evidence dump as "anchor: log host only, prod config not verified" and proceed with extra caution at 11f.

## 11a. Identify the service token (not the literal hostname)

After anchoring on prod config (11.0), extract the service token from the resolved hostname for use as a regex / wildcard filter:

- `<qualifier>-<svc>-01.<dc>.<internal-domain>` → token `<svc>` (strip leading qualifier prefixes, trailing instance suffixes `-01`/`-a01`/`-b02`)
- **Why**: config / log hostnames are often DNS aliases or LB VIPs (e.g. `<qualifier>-<svc>-01.<dc>.<internal-domain>`), while monitoring uses a different naming (e.g. `<svc>-a01..<svc>-b03`). Querying with the literal config name will fail. Always use the **token** as a wildcard / regex filter — but keep the literal hostname / IP for the wrong-instance check at 11f.

## 11b. Query the datasource directly

1. **List datasources** — `mcp__grafana__list_datasources`. Note Prometheus and InfluxDB UIDs + databases. **If the response includes `hasMore: true` or fills the default page size, paginate with `offset`/`page` until you have all entries**, or use the `type` filter (`type: "influxdb"`, `type: "prometheus"`) to narrow. Skipping pagination is how you miss the InfluxDB datasource that holds VM metrics.
2. **For each Prometheus datasource**: `mcp__grafana__query_prometheus` to find which label carries the service token. **Try these labels in order, do NOT stop after a few empties**: `pod`, `container`, `hostname`, `instance`, `app`, `service`, `kubernetes_pod_name`, `exported_instance`. For each: `expr: label_values(up{<label>=~".*<token>.*"}, <label>)`. Empty on one label ≠ "no metrics here" — only after all 8 are empty may you mark this datasource as "no data for this service". Once a label hits, build queries:
   - CPU: `100 - rate(node_cpu_seconds_total{mode="idle",<label>=~"<svc>.*"}[1m]) * 100` (or whatever the export pattern is — discover via `list_prometheus_metric_names`)
   - Memory: `node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes`
   - Use `query_prometheus` with `query_type: "range"` and `step: 60` for 1-min bins.
3. **For each InfluxDB datasource**: query via `mcp__grafana__grafana_api_request` proxy:
   - **Don't stop at `SHOW DATABASES`.** If it returns names like `icinga2`, `telegraf`, `metrics`, `nagios`, `collectd`, `sensu` (any non-`_internal` database), each is a likely VM-tier monitoring db. You MUST run the hostname-tag-values query inside EVERY non-`_internal` database before concluding "no VM metrics". Seeing a database name listed but never querying it is the most common miss in this skill.
   - Discover hostnames: `SHOW TAG VALUES FROM /.+/ WITH KEY = "hostname"` then grep for the service token, OR run `SHOW SERIES WHERE hostname =~ /<svc>/` (lighter).
   - Discover measurements for those hosts: `SHOW MEASUREMENTS WHERE hostname = '<svc>-a01'` (or browse `SHOW MEASUREMENTS` and identify CPU / memory / disk by name).
   - Discover tag keys for chosen measurement: `SHOW TAG KEYS FROM "<measurement>"`; then `SHOW TAG VALUES FROM "<measurement>" WITH KEY = "metric"` to find the right metric tag value (e.g. `CPU-AVG`, `physical %`).
   - Build query: `SELECT mean("value"), max("value") FROM "<measurement>" WHERE hostname =~ /<svc>/ AND "metric" = '<tag>' AND time >= '<from>' AND time <= '<to>' GROUP BY time(1m), hostname fill(null)`.

## 11c. Dashboard as last-resort hint (NOT primary entry)

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

## 11d. Mandatory metric scan

Once you have a working datasource path, query ALL of these for the suspected service (one query per metric per instance, all instances):

1. **CPU** (mean + max, 1-min bins) — every instance
2. **Memory** (mean + max, 1-min bins) — every instance
3. **Restart / replica count** (k8s tiers only) — every replica
4. For VM tier: also check **disk I/O / network** if the data exists

Do NOT report on memory while skipping CPU (or vice versa). If you only have data for one, the report is incomplete — go back and query the other before writing Root Cause. Report the **worst instance's max** value across all metrics.

**Beyond the mandatory list above, drill into other panels (latency, GC, queue depth, thread pool, connection pool, etc.) only when one of the mandatory metrics shows an anomaly that needs further explanation.** Do not pre-emptively scan every panel.

Other signals to look for during the mandatory scan: pod restart, replica drop, CPU/memory saturation, throttle, network drop, redis timeout.

## 11e. Aggregation rule

**Aggregate with both `mean` AND `max`, and keep bins ≤ 1 min.** A 5-min `mean` smooths away spikes — a chart visually showing 86% peak can read 50% under 5-min mean. Cite the **max** for spike detection, not the mean.

- Brief findings into Root Cause **only when the data is verified**. Acceptable verification: Prometheus query that returned numbers, InfluxDB proxy query that returned numbers, panel image that actually rendered a chart, or a user-supplied screenshot. **A "No data" image, an empty Prometheus result that you didn't double-check, or "current metrics look normal" are NOT verification of incident-time state.**

## 11f. Reverse-signal sanity check (GATE before writing Root Cause)

A real upstream-shape outage always leaves SOME footprint somewhere. If your queried metrics are completely flat across CPU + Memory + restart + replica during a documented incident burst, do the following before concluding "infra is healthy":

**Trigger**: incident has a clear upstream-shape outage (503 burst / timeout flood / >100x error ratio over baseline) AND the metrics you pulled are dead-flat in the incident window.

**Three possible diagnoses** — distinguish by checking traffic / request-rate alongside resource metrics:

1. **Wrong instance / wrong datasource** — flat metrics + traffic on this instance is normal (no drop): you're looking at a different deployment than the one that's actually serving prod. Most common when the same service name exists in multiple clusters / regions.
2. **Network / LB / DNS failure between caller and service** — flat metrics + traffic on this instance dropped to zero (or near zero) during the burst: the service itself is fine, requests just couldn't reach it. Look at LB / ingress / DNS / network logs, not service infra.
3. **Genuinely healthy and the incident root cause is elsewhere** — flat metrics + traffic normal + the upstream-shape signal is wrong (e.g. it was actually app-level after all, or noise).

**Required action**:
1. Re-verify hostname / DNS / IP from prod config (11.0) matches the instance you queried — if you queried `<svc>-a01` but prod points at `<svc>-b01`, you're in case (1).
2. Pull request rate / traffic on the queried instance for the same window. If it dropped, you're in case (2). If it stayed normal, you're in case (1) or (3).
3. If multiple deployments with the same service name exist, list them all in the evidence dump and explicitly note which one prod traffic actually hits.
4. If you cannot rule out wrong-instance / network-side failure after the above, mark Root Cause as "infra: indeterminate" and put the question in Unknowns. Do NOT default to "infra healthy".
