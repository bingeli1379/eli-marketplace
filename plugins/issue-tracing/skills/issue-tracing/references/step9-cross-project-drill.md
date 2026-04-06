# Step 9 — Cross-project drill-down

Triggers, in priority order — use the highest-priority signal available, do not be misled by lower-priority hints:

1. **URL / hostname inside an error message** (most reliable — actual call data). e.g. a log shows `Url: "http://<svc>-01.<dc>.<internal-domain>/api/..." ... TimeoutRejectedException` → upstream is `<svc>`. Extract the host's leading token before the first `-` or `.` as the candidate `project.keyword`.
2. **Log message** in the current project explicitly names another service (e.g. `Failed to call <upstream>`).
3. **Reading code** (step 10) reveals an outbound call to another service that failed in the same window.
4. **Grafana panel title / sibling panel** mentions a service (lowest priority — may be unrelated). Treat as a hint only; verify by querying logs, then apply the correlation check below before pursuing.

**HTTP error pattern** (`status=502/503/504`, `connection refused`, `timeout`) implies an upstream — apply the trigger ladder above to identify it. Do not stop at "got 503" without identifying the upstream.

Maximum 2 hops total. If exceeded, stop and list the call chain in Unknowns.

## Caller-direction drill — trigger source (who sent the request)

The ladder above drills toward the **callee** (which dependency failed). When the question is **who / what triggered** the error — bot? human? surge? new data? — i.e. axis **C** in step12 HARD RULE #4 (code unchanged, no one released, but the incoming request changed), drill the OPPOSITE way: toward the **caller / ingress**.

- **Hop one level toward the edge** to a service that logs IP / User-Agent (gateway / proxy / auth). The originating service often lacks these fields; the caller-side one has them.
- **Reuse two signals you already have — both queryable, neither fabricated**:
  - distinct customerId concentration (step 8): one customer = targeted / single-account bug; many spread = broad.
  - incident vs pre-incident baseline ratio (the correlation check below): a sharp spike = event-driven surge (deploy, campaign, bot run); ratio ≈ 1 = chronic background (axis D).
- **Do NOT infer "it's a bot" from a request-rate shape alone** — that is a fabrication risk. If IP / UA / concentration are unreachable, write "觸發源未判定 + 缺 IP/UA 來源" per HARD RULE #4. Never guess the trigger from a waveform.

**Correlation check before claiming "related"**: Before treating a sibling error pattern as part of this incident, run the same query over an **equally-long pre-incident window** (e.g. previous hour or previous day same time) and compare counts. If the pre-incident baseline is similar to the incident window, the pattern is **chronic, not caused by this incident** — list it as "out of scope / unrelated background error" instead of folding into Root Cause. Only fold in when incident-window count is materially higher than baseline.
