---
name: sql-query-optimization
description: >
  Use when tuning PostgreSQL/MySQL query performance — EXPLAIN ANALYZE, N+1 problems, missing/covering indexes,
  sequential scans, OFFSET pagination, temp-table spills, inefficient JOINs. For SQL Server / T-SQL / Oracle /
  stored-procedure tuning use sql-optimization; for authoring or debugging queries use sql-expert.
  Keywords: postgresql performance, mysql optimization, explain analyze, n+1 problem, covering index,
  sequential scan, work_mem, pg_stat_statements, keyset pagination, bitmap scan, index only scan.
user-invocable: false
license: MIT
---
# SQL Query Optimization

Tune a PostgreSQL or MySQL query from evidence: the plan (`EXPLAIN (ANALYZE, BUFFERS)`), the statement statistics (`pg_stat_statements` / `performance_schema`), and a before/after measurement on the same data. A change proposed without a plan to point at is a guess.

**Every threshold, ratio, or config value you are about to recommend is checked against the current official docs for the engine version in use, and cited** — memory-limit and planner defaults move between major versions, and the "x times faster" figures that circulate are from someone else's table.

## What to look for

| Finding | How it shows | What to do |
|---|---|---|
| Sequential scan on a large filtered table | `Seq Scan` with a high `Rows Removed by Filter` | Index the filter column(s); re-run EXPLAIN to confirm the plan switched |
| Foreign key without an index | Slow JOINs / cascades on the referencing table | Index every FK column (neither engine does it for you on the referencing side) |
| N+1 | One query per row of a parent result, usually ORM lazy loading | JOIN / eager load / batch by key |
| `SELECT *` on a wide table | Large row width in the plan, heavy network | Name the columns; a covering index (`INCLUDE`) is only possible once the column list is known |
| Unbounded result | No `LIMIT`; memory or timeout at the client | `LIMIT` + pagination |
| `OFFSET` pagination on deep pages | Cost grows with the offset; skipped rows are still scanned | Keyset (cursor) pagination on an indexed, unique ordering |
| Leading-wildcard `LIKE '%term%'` | B-tree index unusable | Trigram (`pg_trgm`) or full-text index, per engine |
| Sort / hash spilling to disk | `Sort Method: external merge`, temp blocks read/written | Fix the query or index first; `work_mem` is per operation per connection, so raising it globally is the last resort |
| Stale planner statistics | Good index exists, plan ignores it, estimates far from actuals | `ANALYZE` after bulk loads; check autovacuum/autoanalyze is reaching the table |
| Row-by-row INSERT in a loop | Many single-row statements | Multi-row `VALUES` / `COPY` / bulk load |
| Wrong composite index column order | Index exists but is not used, or used with a filter | Leading columns must match the equality predicates; range column last |
| String-built SQL | Concatenated literals | Parameterize — correctness and plan reuse, not only injection |

Never "fix" a query by adding an index without reading the plan first: an index that the planner cannot use costs every write and buys nothing.

## When to load references

Each at `${CLAUDE_SKILL_DIR}/references/`:

| Read | When |
|---|---|
| `explain-analysis.md` | Reading plan output, buffer statistics, PostgreSQL vs MySQL EXPLAIN differences |
| `index-strategies.md` | Choosing an index type (B-Tree, GIN, GiST, Hash), composite column order, covering and partial indexes, index-usage monitoring |
| `query-rewrites.md` | Subquery → JOIN, N+1 elimination, pagination, LIKE, batching — before/after shapes |
| `performance-monitoring.md` | `pg_stat_statements` / slow-query log setup, cache-hit ratio, bloat |
| `optimization-workflow.md` | The measure → hypothesis → change → re-measure loop, and long-term tracking |
| `error-catalog.md` | The full catalogue of the failure shapes above with worked fixes |

## Reporting

For each query: the plan node that hurts, the change, and the before/after measurement on the same data set — with the engine version and the doc you checked for any number you name.
