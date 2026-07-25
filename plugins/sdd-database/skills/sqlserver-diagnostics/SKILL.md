---
name: sqlserver-diagnostics
description: >
  Use when a SQL Server instance itself is the suspect — timeouts, blocking, unexplained
  slowness, "which query is eating the server", or you need wait statistics, currently-running
  requests, or plan-cache totals. Start here before touching an index or a plan. For tuning a
  known query or stored procedure use sql-optimization; for portable PG/MySQL tuning use
  sql-query-optimization; for schema design use database-schema-design.
  Keywords: sql server slow, timeout, blocking, deadlock victim, wait stats, wait type,
  sys.dm_os_wait_stats, sys.dm_exec_requests, sys.dm_exec_query_stats, plan cache,
  RESOURCE_SEMAPHORE, PAGEIOLATCH, CXPACKET, ASYNC_NETWORK_IO, tempdb contention.
user-invocable: false
license: MIT
---

# SQL Server Diagnostics (DMV-based)

Find *where* a SQL Server instance is hurting, before deciding what to change.

> **Provenance & how to read this skill.** The DMV queries here come from
> [vince-winkintel/sql-server-skills](https://github.com/vince-winkintel/sql-server-skills) (MIT —
> see the bundled `LICENSE`). They were adopted because DMV shapes are stable across versions.
> The upstream skill's *prescriptive* maintenance guidance was deliberately **not** adopted: it
> repeated the 2010s-era `10%→REORGANIZE / 30%→REBUILD` rule of thumb, which current Microsoft
> guidance contradicts (reorganize is the preferred method unless there is a specific reason to
> rebuild, and page density matters at least as much as logical fragmentation).
>
> **So: trust the queries, verify every threshold and every "typical fix".** When you are about to
> recommend a number, a knob, or a maintenance action, look it up in the official docs first — use
> the environment's Microsoft documentation tool if one is available (a `microsoft-docs`-style MCP
> server or skill), and cite what you found. Do not ship a rule of thumb from memory.

## Order of investigation

Diagnose top-down; each step narrows the next. Jumping straight to indexes is how people
"optimize" a server that was actually blocked or starved of memory.

```
1. Wait stats        — what is the instance waiting ON?      scripts/wait-stats.sql
2. Top consumers     — which queries burn CPU / I/O / time?  scripts/top-slow-queries.sql
3. Live picture      — what is running right now?            scripts/active-queries.sql
4. Blocking chain    — who blocks whom?                      scripts/blocking-analysis.sql
5. Only then         — the specific query, plan, or index
```

Run the bundled scripts from `${CLAUDE_PLUGIN_ROOT}/skills/sqlserver-diagnostics/scripts/` (each is
self-contained and read-only). They require `VIEW SERVER STATE`; on Azure SQL Database some
instance-scoped DMVs are unavailable or scoped to the database — check before concluding
"no data" means "no problem".

## What the numbers do and don't mean

- **`sys.dm_os_wait_stats` is cumulative since the last instance restart** (or since
  `DBCC SQLPERF('sys.dm_os_wait_stats', CLEAR)`). A big number may be old history, not your
  incident. For an incident, snapshot twice and diff, or clear and re-measure in a window.
- **`sys.dm_exec_query_stats` covers only what is still in the plan cache.** A plan evicted under
  memory pressure, or recompiled, takes its totals with it — an absent query is not an innocent
  query.
- **Averages hide parameter-sensitive plans.** A stored procedure whose average looks fine can
  still be catastrophic for one parameter set (parameter sniffing). Compare max vs average
  duration before declaring a procedure healthy.

## Wait-type triage

The mapping from wait type to *area of suspicion* is stable; the fix column is a **starting
hypothesis to verify against official docs and the actual workload**, not a prescription.

| Wait type | What it means | First hypothesis |
|---|---|---|
| `PAGEIOLATCH_SH` / `PAGEIOLATCH_EX` | Reading/writing data pages from disk — I/O bound | Reduce I/O first (indexing, query shape); storage and memory second |
| `LCK_M_*` | Lock waits — someone is blocked | Find the blocking chain (step 4); review transaction scope and isolation level |
| `CXPACKET` / `CXCONSUMER` | Parallelism — threads waiting on each other | Often a symptom, not a cause: look for skewed parallel plans before touching MAXDOP |
| `SOS_SCHEDULER_YIELD` | CPU pressure — threads yielding their quantum | CPU-heavy queries / plan regressions; not "add cores" by default |
| `WRITELOG` | Transaction log is the bottleneck | Transaction size and commit frequency; log file placement |
| `RESOURCE_SEMAPHORE` | Queries queuing for a memory grant | Fix the queries with oversized grants / spills before raising memory |
| `ASYNC_NETWORK_IO` | Server produced results faster than the client consumed them | Almost always the **client** (row-by-row consumption, huge result sets), not the server |
| `PAGELATCH_*` / `LATCH_*` | In-memory page or structure contention | Commonly tempdb allocation contention — verify the current file-count guidance in official docs before changing anything |
| `HADR_*` | Always On activity | Normal in an AG; sustained growth means replica lag |

## Reporting a diagnosis

State, in this order: the top waits with their share, the top consumers by the metric that
matched those waits, whether anything was blocked, and only then a recommendation — each
recommendation carrying the evidence that produced it and a citation for any threshold or
setting you name. "Fragmentation is 34% so rebuild" is exactly the shape of claim this skill
exists to prevent; "wait stats are 70% `RESOURCE_SEMAPHORE`, these three queries request
multi-GB grants, here is the spill evidence" is the shape to aim for.
