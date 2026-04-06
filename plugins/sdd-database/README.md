# sdd-database

**SDD language pack — Database.** Extends the [`sdd`](../sdd) core plugin with the
`database-engineer` agent and Database skills. Part of the spec-driven multi-agent workflow.

## What it adds

- **Agent** `sdd-database:database-engineer` — schema design, migration strategy, query/index optimization, and data integrity across SQL Server, PostgreSQL, MongoDB, and analytics stores.
- **Skills** (6): database-schema-design, mongodb-query-optimizer, mongodb-schema-design, sql-expert, sql-optimization, sql-query-optimization.

## Install

```
/plugin install sdd-database@eli-marketplace
```

Declares `dependencies: ["sdd"]`, so installing this pack pulls in the `sdd` core
plugin automatically. The agent eager-loads core skills (agent-guidelines,
engineering-checklist, test-driven-development, …) cross-plugin by bare name.

## How it fits

The core orchestrator dispatches this pack's agent by its namespaced `subagent_type`
(`sdd-database:database-engineer`) per the routing table in `sdd/references/agent-routing.md`. If this
pack is not installed, core falls back to a general-purpose agent and suggests
installing it. See the [`sdd` README](../sdd/README.md) for the full workflow and the
maintenance guide for adding/maintaining packs.
