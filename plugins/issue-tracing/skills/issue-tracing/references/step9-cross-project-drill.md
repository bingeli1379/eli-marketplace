# Step 9 — Cross-project drill-down

Triggers, in priority order — use the highest-priority signal available, do not be misled by lower-priority hints:

1. **URL / hostname inside an error message** (most reliable — actual call data). e.g. a log shows `Url: "http://<svc>-01.<dc>.<internal-domain>/api/..." ... TimeoutRejectedException` → upstream is `<svc>`. Extract the host's leading token before the first `-` or `.` as the candidate `project.keyword`.
2. **Log message** in the current project explicitly names another service (e.g. `Failed to call <upstream>`).
3. **Reading code** (step 10) reveals an outbound call to another service that failed in the same window.
4. **Grafana panel title / sibling panel** mentions a service (lowest priority — may be unrelated). Treat as a hint only; verify by querying logs, then apply the correlation check below before pursuing.

**HTTP error pattern** (`status=502/503/504`, `connection refused`, `timeout`) implies an upstream — apply the trigger ladder above to identify it. Do not stop at "got 503" without identifying the upstream.

Maximum 2 hops total. If exceeded, stop and list the call chain in Unknowns.

**Correlation check before claiming "related"**: Before treating a sibling error pattern as part of this incident, run the same query over an **equally-long pre-incident window** (e.g. previous hour or previous day same time) and compare counts. If the pre-incident baseline is similar to the incident window, the pattern is **chronic, not caused by this incident** — list it as "out of scope / unrelated background error" instead of folding into Root Cause. Only fold in when incident-window count is materially higher than baseline.
