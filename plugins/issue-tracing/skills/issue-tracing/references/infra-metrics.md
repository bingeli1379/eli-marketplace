# Infra-metric verification (loaded at step 5d's GATE)

Once an upstream service is suspected (from the drill, `next-hop-drill.md`), use its ownership classification (your team's readable service = in-scope; a service owned by another team = out-of-scope) AND the shape of the error:

- **In-scope upstream + infra-shape signal in log** → REQUIRED. Infra-shape signals: HTTP `502/503/504`, `connection refused`, `timeout`, `TaskCanceledException`, `Polly TimeoutRejectedException`, `OOMKilled`, throttling, redis timeout, "No server is available", DB connection pool exhaustion, etc. These error shapes only get explained by infra metrics, so checking is required before writing Root Cause.
- **In-scope upstream + app-level root cause clearly visible in log** → OPTIONAL. App-level signals: validation errors, auth misconfig, deserialization / parse errors, explicit business-logic exceptions, code bugs with stack traces pointing at app code only. Infra numbers do not explain these, so a CPU/Memory check is noise. The evidence dump in the report step (`report.md`) should mark infra as `n/a (app-level root cause)` for that service.
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

When the upstream candidate came from log host extraction (the drill's trigger #1, `next-hop-drill.md`) you already have the hostname — still cross-check against prod config to make sure it matches.

If the calling service is not in scope (no source code available), record this in the evidence dump as "anchor: log host only, prod config not verified" and proceed with extra caution at 11f.

## 11a. Identify the service token (not the literal hostname)

After anchoring on prod config (11.0), extract the service token from the resolved hostname for use as a regex / wildcard filter:

- `<qualifier>-<svc>-01.<dc>.<internal-domain>` → token `<svc>` (strip leading qualifier prefixes, trailing instance suffixes `-01`/`-a01`/`-b02`)
- **Why**: config / log hostnames are often DNS aliases or LB VIPs (e.g. `<qualifier>-<svc>-01.<dc>.<internal-domain>`), while monitoring uses a different naming (e.g. `<svc>-a01..<svc>-b03`). Querying with the literal config name will fail. Always use the **token** as a wildcard / regex filter — but keep the literal hostname / IP for the wrong-instance check at 11f.

## 11b. Query the datasource directly

1. **List datasources** — `mcp__grafana__list_datasources`. Note Prometheus and InfluxDB UIDs + databases. **If the response includes `hasMore: true` or fills the default page size, paginate with `offset`/`page` until you have all entries**, or use the `type` filter (`type: "influxdb"`, `type: "prometheus"`) to narrow. Skipping pagination is how you miss the InfluxDB datasource that holds VM metrics.
2. **Pick the right cluster's datasource FIRST — don't probe every one.** A large multi-cluster env commonly runs many Prometheus datasources, one per cluster / tier (e.g. RKE-a/-b, GKE, VM, VictoriaMetrics…); probing a cluster the service does NOT run on is pure waste. Resolve the serving cluster from what you ALREADY have, in order: the **cluster tag on `current`'s OTEL / structured access logs** (the same logs you pulled for the callee latency check: strongest, free, it names the exact cluster); else the **env-knowledge per-project cluster (step 1c)** + the **datacenter token in the prod hostname** (11.0).

   **That cluster name is a POINTER to the datasource, not a label value to filter on.** The metrics backend routinely stores a *different* string for the same cluster than the logs do (log-side `<a>-<b>-<c>` vs metric-side `<b>-<c>-<a>`, long form vs short form), so pasting the log's cluster value into a PromQL label matcher silently returns nothing and reads as "no metrics for this service". Map cluster → datasource through 1c's datasource table (which datasource serves which cluster), and note that **one datasource can serve more than one spelling of its cluster label** — so filtering on one spelling drops the series carrying the other. Prefer **no cluster-label filter at all** once you have picked the right datasource (it already scopes the cluster); if you must filter, enumerate the label's real values first (`list_prometheus_label_values`) rather than assuming.

   Query THAT cluster's datasource first; widen to a sibling cluster's datasource only if the in-scope one is genuinely empty AND the env knowledge says the service is multi-cluster. Then, **on the chosen datasource**, `mcp__grafana__query_prometheus` to find which label carries the service token. **Try these labels in order, do NOT stop after a few empties**: `pod`, `container`, `hostname`, `instance`, `app`, `service`, `kubernetes_pod_name`, `exported_instance`. For each: `expr: label_values(up{<label>=~".*<token>.*"}, <label>)`. Empty on one label ≠ "no metrics here" — only after all 8 are empty may you mark this datasource as "no data for this service". Once a label hits, build queries:
   - CPU: `100 - rate(node_cpu_seconds_total{mode="idle",<label>=~"<svc>.*"}[1m]) * 100` (or whatever the export pattern is — discover via `list_prometheus_metric_names`)
   - Memory: `node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes`
   - Use `query_prometheus` with `queryType: "range"` and `stepSeconds: 60` for 1-min bins — **but for a many-instance scan (11d requires every instance), a `range` query over many series routinely truncates; use the instant `max_over_time` / `avg_over_time` form from 11e instead, and keep `range` for a few instances or when you need the time-shape.**
   - **`query_prometheus` param names + required fields**: `queryType` (`"range"` / `"instant"`), `startTime`, `endTime`, `stepSeconds`. **`endTime` is required on EVERY call — including `queryType: "instant"`**, where `startTime` / `stepSeconds` are ignored (pass the same timestamp for `startTime` if you like; harmless). `range` needs all four. Omitting `endTime` fails with `parsing end time: syntax error`, which does not name the field it wants, so it reads as a malformed-expression error and sends you rewriting the query instead of adding the missing param.
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
- When you find a panel with the right measurement, read the raw panel JSON (NOT `get_dashboard_panel_queries` — its `processedQuery` keeps unresolved `/^$var$/` for panel-level scopedVars). Use `mcp__grafana__get_dashboard_property` with `jsonPath: "$.panels[?(@.id==<panelId>)].targets"` (the param is `jsonPath`; `property` is rejected) and extract:
  - `measurement` — literal name, use verbatim
  - `select` — field + aggregation (when `rawQuery=false`, UI uses this, not `query`)
  - `tags` — literal tag filters
- **Do NOT guess measurement names.** **Do NOT loop through candidate names.** Hard limit: at most 1 alternate measurement attempt; then stop and list in Unknowns.
- `get_panel_image` rules:
  - For `prometheus`, `loki`, `elasticsearch`, `influxdb` panels: **do NOT call `get_panel_image` for data verification or as a sanity check.** Always use the direct query path (11b). Image rendering on these is at best redundant, at worst (InfluxDB) silently broken. Image is acceptable only when the user explicitly asks for a chart / screenshot — never for deciding numbers.
  - For other datasources (CloudWatch, Splunk, SQL, Tempo, etc.) where no direct MCP query exists: `get_panel_image` is the legitimate fallback.

## 11d. Mandatory metric scan

Once you have a working datasource path, query ALL of these for the suspected service, **every instance covered** — preferring 11e's instant form, which returns one value per instance from a SINGLE query; fall back to one-query-per-instance only when the instant form cannot express the metric:

1. **CPU** (mean + max, 1-min bins) — every instance
2. **Memory** (mean + max, 1-min bins) — every instance
3. **Restart / replica count** (k8s tiers only) — every replica
4. **CPU throttle ratio** (k8s tiers only) — every instance, ONE instant query, not per-instance loops:
   `max_over_time((rate(container_cpu_cfs_throttled_periods_total{<label>=~"<svc>.*"}[<rate-win>]) / rate(container_cpu_cfs_periods_total{<label>=~"<svc>.*"}[<rate-win>]))[<window>:60s])` as `queryType: "instant"` — returns one peak ratio per instance (11e's instant rule). Set `<rate-win>` to the burst length, capped at 5m and floored at 1m — a `[5m]` rate over a 2-min burst dilutes the ratio the same way a 5-min mean hides a spike (11e). Anything non-trivial on a single instance while the others sit near zero is the isolated-throttle case below — average CPU will NOT show it.
   **Empty result ≠ no throttling — it is usually the wrong label.** The label you resolved from `up` in 11b (often `instance` / `hostname`, node-exporter's naming) frequently does NOT exist on cAdvisor container metrics, which carry `pod` / `container` / `namespace` instead. On an empty return, re-resolve against the container family (`label_values(container_cpu_cfs_periods_total{<label>=~".*<token>.*"}, <label>)` over `pod`, `container`, `kubernetes_pod_name`) before anything else; then, if the metric names themselves are absent, discover the tier's throttle metric via `list_prometheus_metric_names` (grep `throttl`). Only after BOTH come up empty may you record throttle as unavailable.
5. For VM tier: also check **disk I/O / network** if the data exists

Do NOT report on memory while skipping CPU (or vice versa), and on a k8s tier do NOT skip throttle. Every applicable item above must come back either with numbers or with an explicit "unavailable, here is what I tried"; a partial set is an incomplete report — go back and query the rest before writing Root Cause. Report the **worst instance's max** value across all metrics.

**Beyond the mandatory list above, drill into other panels (latency, GC, queue depth, thread pool, connection pool, etc.) only when one of the mandatory metrics shows an anomaly that needs further explanation.** Do not pre-emptively scan every panel.

Other signals to look for during the mandatory scan (throttle is item 4, not an optional watch-item): pod restart, replica drop, CPU/memory saturation, network drop, redis timeout.

**Throttling isolated to ONE instance while every instance's average CPU looks alike → compare the NODE, not the pod.** A CPU limit is a CFS quota — a time budget per ~100ms period, drained by all runnable threads together — so the *same* quota on a higher-core node is spent in less wall-clock time, and the cgroup sits frozen for a larger share of every period. Two instances can therefore show near-identical average CPU while only one is throttled. Pull each affected pod's node from the label set already on its container metrics, then compare `kube_node_status_capacity{resource="cpu"}` across those nodes; heterogeneous node fleets (a newer, higher-core batch alongside older machines) are the usual cause. Note the second-order effect when writing Root Cause: a frozen cgroup also stalls the client library's socket-read thread, so the payload arrives but goes unread — which surfaces as an apparent "slow datastore / upstream timeout" rather than as high CPU, and will mislead the drill toward a healthy downstream.

**A one-instance throttle is also invisible to average-based autoscaling.** An HPA / KEDA CPU-utilization trigger averages across replicas, so one saturated instance stays hidden behind idle siblings and no scale-up fires. When throttling is isolated, check the observed replica count over the incident window and state plainly that autoscaling did not react and why — do not report "autoscaling was healthy" from a flat replica line alone.

## 11e. Aggregation rule

**Aggregate with both `mean` AND `max`, and keep bins ≤ 1 min.** A 5-min `mean` smooths away spikes — a chart visually showing 86% peak can read 50% under 5-min mean. Cite the **max** for spike detection, not the mean.

- **Across many instances, get the peak with an INSTANT `max_over_time` query, not a `range` query.** `max_over_time(<expr>[<window>:<step>])` evaluated as `queryType: instant` returns one value per instance (its peak in the window, with `<step>` ≤ 1 min preserving the bin rule); a `range` query over many series × dozens of 1-min points routinely blows the response / token budget and truncates to a file, costing an extra round-trip. Use `range` only for a few instances or when you actually need the time-shape; get the window mean the same way with `avg_over_time(<expr>[<window>:<step>])` instant.
- Brief findings into Root Cause **only when the data is verified**. Acceptable verification: Prometheus query that returned numbers, InfluxDB proxy query that returned numbers, panel image that actually rendered a chart, or a user-supplied screenshot. **A "No data" image, an empty Prometheus result that you didn't double-check, or "current metrics look normal" are NOT verification of incident-time state.**

## 11f. Reverse-signal sanity check (GATE before writing Root Cause)

A real upstream-shape outage always leaves SOME footprint somewhere. If your queried metrics come back clean across the whole 11d list (CPU + Memory + restart / replica + throttle) during a documented incident burst, do the following before concluding "infra is healthy":

**Trigger**: incident has a clear upstream-shape outage (503 burst / timeout flood / >100x error ratio over baseline) AND the metrics you pulled show nothing in the incident window — dead-flat, *or* merely unremarkable while the numbers you looked at were aggregated across instances.

**Four possible diagnoses** — distinguish by checking traffic / request-rate alongside resource metrics:

1. **Wrong instance / wrong datasource** — flat metrics + traffic on this instance is normal (no drop): you're looking at a different deployment than the one that's actually serving prod. Most common when the same service name exists in multiple clusters / regions.
2. **Network / LB / DNS failure between caller and service** — flat metrics + traffic on this instance dropped to zero (or near zero) during the burst: the service itself is fine, requests just couldn't reach it. Look at LB / ingress / DNS / network logs, not service infra.
3. **Genuinely healthy and the incident root cause is elsewhere** — flat metrics + traffic normal + the upstream-shape signal is wrong (e.g. it was actually app-level after all, or noise).
4. **Per-instance saturation hidden by an average** — CPU/memory read normal *because you looked at the mean across instances*, while one instance is throttled or pegged. Before accepting case (3), re-check per instance (not aggregated) and apply the isolated-throttle rules in 11d (node-capacity comparison + the average-based-autoscaling blind spot).

**Required action**:
1. Re-verify hostname / DNS / IP from prod config (11.0) matches the instance you queried — if you queried `<svc>-a01` but prod points at `<svc>-b01`, you're in case (1).
2. Pull request rate / traffic on the queried instance for the same window. If it dropped, you're in case (2). If it stayed normal, you're in case (1), (4) or (3) — rule out (4) before (3).
3. If multiple deployments with the same service name exist, list them all in the evidence dump and explicitly note which one prod traffic actually hits.
4. Confirm the numbers you are calling flat are **per instance**, not an average across instances — an aggregated series hides case (4).
5. If you cannot rule out wrong-instance / network-side / hidden-per-instance failure after the above, mark Root Cause as "infra: indeterminate" and put the question in Unknowns. Do NOT default to "infra healthy".

## 11g. Shared-datastore root cause — datastore-itself vs the path to it, and WHO owns each

When the root bottoms out at a **shared datastore / cache / message layer** (a Redis or DB cluster, a broker, DNS) — typically after the SKILL.md step 5d breadth classifier showed the failure is **fleet-wide** — there is a **second ownership axis** beyond step 5a's service ownership. Step 5a asks "which *team* owns this service"; here ask "who owns this *infra layer*": a shared datastore and the network path to it are usually owned by a separate **infra / network (IT)** and/or **database (DBA) / datastore** function, NOT the app team whose service happened to log the error. Resolve the actual owner from the environment knowledge (step 1c).

**Deciding datastore-itself vs the path to it is YOUR job, not the user's** — do not hand off "go ask IT" without first narrowing which. Narrow with what the tools already give you:

- **Inner-exception type on the failing calls.** A connection-level error (`RedisConnectionException`, `connection refused`, DNS resolution failure, TLS/handshake, connection-pool exhausted) points at the **path** (network / LB / DNS / transport) → **IT / network** owner. A server-side error (`RedisTimeoutException` where the command reached the server, `server is busy`, high server load, `OOM`, auth/`NOAUTH`) points at the **datastore itself** → **DBA / datastore** owner. Pull the inner exception from `_source` — do not stop at the top-of-stack `TaskCanceledException`.
- **Breadth + simultaneity** (from the 5d classifier). Many *unrelated* clients timing out on the **same datastore node(s) at the same instant**, while those nodes' own host metrics (CPU / IO / memory / blocked-clients) look normal, is a strong **path/transport** signal (the clients can't reach a healthy datastore) → IT / network. The same clients failing while the datastore host metrics are saturated is a **datastore-itself** signal → DBA.
- **Datastore host metrics if reachable.** If the datastore cluster exposes metrics you can query (11b), check the specific nodes the errors name: CPU / memory / blocked-clients / network retransmit-drop. Query them the same bounded way as any other instance.
- **GATE before escalating either way — rule out the CLIENT first.** A timeout that reached the server is only a datastore signal if the *caller* was healthy. An isolated CPU-throttled instance (11d) produces exactly this shape: the response arrives but the frozen cgroup never runs the socket-read thread, so the client library raises a server-side-looking timeout against a datastore that is fine. Tell-tales that it is the client, not the datastore: the failures cluster on **one caller instance / pod** rather than across unrelated clients, and that instance's throttle ratio is non-trivial while its siblings' is ~0. Step 11 usually scans the *upstream*, so this number often does not exist yet — run 11d item 4 once more against the **calling** service's instances before judging the gate; skipping it is not the same as clearing it. If both hold, the owner is **your own team**, not DBA or IT — do NOT escalate. Only after this gate is clear may you name a datastore or path owner.

**Output**: name the specific instance(s) (node IPs / host), state the datastore-vs-path verdict with its evidence, and name the matching owner for the report to escalate to (`report.md`). If the tools genuinely cannot disambiguate, say so and list **both** candidates (datastore + network path) with **both** owners as confirm-with items in Unknowns — but only after actually trying every narrowing signal above and clearing the client-side gate.
