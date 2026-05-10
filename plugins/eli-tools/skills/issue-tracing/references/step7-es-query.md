# Step 7 — Run ES queries (per-project counts)

Required filters on every query:
- `range` on `@timestamp` — the parsed time range with ±5 min buffer
- `term` on `env.keyword` — usually `prod` (from URL filters)
- `term` on `project.keyword` — REQUIRED; one query per candidate project
- `terms` on `level.keyword` — default `["error", "fatal"]`; include `"warning"` only if the originating alert was warning-level or the dashboard panel includes warnings. Count warning separately from error/fatal.

**NEVER run a query without a project filter, time range, AND level filter.** A `*` or `match_all` query is forbidden — past incidents include heap exhaustion from unbounded queries.

**DO NOT include `aggs` / `aggregations` in your search body.** The `mcp__elasticsearch__search` wrapper strips aggregation results from responses; only `hits` are returned. Writing an `aggs` block wastes the round-trip — the wrapper accepts the body but drops the results, so you can't see what you asked for. Use per-bucket queries instead:
- Total counts: `size: 0` query — use the `Total results: N` line
- Top message patterns: `size: 5` sorted by `@timestamp desc`, read `message` field
- First / last occurrence: two queries with `sort` `asc` and `desc`, `size: 1`
- Distinct user counts: see step 8 (cannot use `cardinality` agg)

**Token-budget rules** (the wrapper truncates large responses to a file when responses exceed its limit, costing extra `jq` round-trips):
- **Always start with `size: 0`** to get the total. Only sample after that.
- **`size` cap when fetching `message`/stack traces: 5.** A single `size: 100` over `error` logs with stack traces typically blows the limit. If 5 is not enough, paginate (`from`+`size`) or refine the filter — do not raise `size`.
- **Always pass `_source`** with only the fields you need. For project distribution use `_source: ["project"]`; for time check use `_source: ["@timestamp"]`. Default `_source: "*"` only when you need to inspect schema once.
- **Dedupe stack traces.** When sampling errors, identify each unique error pattern by its leading message (first line / exception type). Once you have one full sample per pattern, do NOT pull additional documents that share the same pattern — re-reading the same stack trace 5 times costs tokens for zero new information. Use `must_not match_phrase` to exclude already-seen patterns when fetching the next sample.
