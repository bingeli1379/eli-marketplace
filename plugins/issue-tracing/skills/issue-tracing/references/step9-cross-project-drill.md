# Step 9 — Cross-project drill-down

Triggers, in priority order — use the highest-priority signal available, do not be misled by lower-priority hints:

1. **URL / hostname inside an error message** (most reliable — actual call data). e.g. a log shows `Url: "http://<svc>-01.<dc>.<internal-domain>/api/..." ... TimeoutRejectedException` → upstream is `<svc>`. Extract the host's leading token before the first `-` or `.` as the candidate `project.keyword`.
2. **Log message** in the current project explicitly names another service (e.g. `Failed to call <upstream>`).
3. **Reading code** (the code-reading step of the trace loop) reveals an outbound call to another service that failed in the same window.
4. **Grafana panel title / sibling panel** mentions a service (lowest priority — may be unrelated). Treat as a hint only; verify by querying logs, then apply the correlation check below before pursuing.

**HTTP error pattern** (`status=502/503/504`, `connection refused`, `timeout`) implies an upstream — apply the trigger ladder above to identify it. Do not stop at "got 503" without identifying the upstream.

**Boundary-driven, not hop-capped.** Keep drilling through your team's own services (per the environment knowledge's ownership info) until you reach the service where the fault actually originates, OR the next hop is a service owned by another team (stop there — state what it returned, leave its internals to the owner). There is no fixed hop limit. Every hop must be backed by real call data (a host in an error, a log naming the service, an outbound call in code, or a documented dependency) — never invent a hop. Runaway guard: if the chain exceeds ~5 hops, stop, lay out the full chain, and hand the decision to the user. List the chain in Unknowns whenever you stop before a confirmed root cause.

## Slowed-but-not-broken hop is itself an upstream pointer

The ladder above fires on a hop that **errors** (URL in the error, a `Failed to call <upstream>` log, a 502/timeout). A hop can also be the cause while returning **200-but-slow**: healthy infra (0 restart, normal CPU / mem), no error naming a downstream, only high latency / saturation. **That is not a root cause — a service that is slow but not erroring is blocked on something else.** Do not stop there, and do not wait for the user to hand you the chain; keep drilling.

**Two things a 200-but-slow hop can be blocked on — check both, do not assume the first:**
1. **Its own downstream service** — an outbound call to the next hop is slow. Follow the topology to that hop (below).
2. **Its own shared infra** — its own Redis / DB / cache is slow, so *its* work (even cache reads, session lookups) drags, with no downstream service to blame. This is the trap: do not conclude "it is just a passthrough waiting on the next service" without ruling out its own datastore. If the slow hop's dependency is a **shared** datastore, run the **breadth classifier from SKILL.md step 5d** (same infra exception, window, `project` filter dropped) — if the same slowness/timeout hits several unrelated services at once, the root is the shared infra layer and you should stop chaining services (see step 5d's fleet-wide branch), not keep hopping.

When the hop didn't error, triggers 1–3 give you nothing to grep — so discover its downstream from **static topology, not logs**:

- the **environment knowledge base's per-project dependency docs** (the knowledge source loaded in step 1c) — a project's upstreams / call topology are documented there;
- the **service's own repo config** (`appsettings*`, outbound-host / base-URL keys) under the project root (read in the code-reading step) — grep which hosts it calls.

Topology is knowable even when that hop's prod logs / metrics are unreachable (e.g. its logs don't land in the default index) — **an observability gap blocks seeing a hop's _state_, never its _topology_.** Continue until you reach a hop that actually broke (5xx / resource-exhausted) or one that crosses an ownership / observability boundary (another product's stack) — stop there and note the boundary in Unknowns. A slowed-but-not-broken hop still counts toward the ~5-hop runaway guard above.

## Caller-direction drill — trigger source (who sent the request)

The ladder above drills toward the **callee** (which dependency failed). When the question is **who / what triggered** the error — bot? human? surge? new data? — i.e. axis **C** in step12 HARD RULE #4 (code unchanged, no one released, but the incoming request changed), drill the OPPOSITE way: toward the **caller / ingress**.

- **Hop one level toward the edge** to a service that logs IP / User-Agent (gateway / proxy / auth). The originating service often lacks these fields; the caller-side one has them.
- **Reuse two signals you already have — both queryable, neither fabricated**:
  - distinct customerId concentration (from the log-analysis step): one customer = targeted / single-account bug; many spread = broad.
  - incident vs pre-incident baseline ratio (the correlation check below): a sharp spike = event-driven surge (deploy, campaign, bot run); ratio ≈ 1 = chronic background (axis D).
- **Do NOT infer "it's a bot" from a request-rate shape alone** — that is a fabrication risk. If IP / UA / concentration are unreachable, write "觸發源未判定 + 缺 IP/UA 來源" per HARD RULE #4. Never guess the trigger from a waveform.

**Correlation check before claiming "related"**: Before treating a sibling error pattern as part of this incident, run the same query over an **equally-long pre-incident window** (e.g. previous hour or previous day same time) and compare counts. If the pre-incident baseline is similar to the incident window, the pattern is **chronic, not caused by this incident** — list it as "out of scope / unrelated background error" instead of folding into Root Cause. Only fold in when incident-window count is materially higher than baseline.
