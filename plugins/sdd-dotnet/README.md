# sdd-dotnet

**SDD language pack — ASP.NET / .NET backend.** Extends the [`sdd`](../sdd) core plugin with the
`dotnet-engineer` agent and ASP.NET / .NET backend skills. Part of the spec-driven multi-agent workflow.

## What it adds

- **Agent** `sdd-dotnet:dotnet-engineer` — ASP.NET across modern .NET Core and legacy .NET Framework: API endpoints, business logic, EF Core/Dapper, domain models, following Clean/Layered Architecture.
- **Skills** (8): analyzing-dotnet-performance, dotnet-best-practices, dotnet-grpc, dotnet-nunit, dotnet-upgrade, ef-core, legacy-aspnet, minimal-api.

## Install

```
/plugin install sdd-dotnet@eli-marketplace
```

Declares `dependencies: ["sdd"]`, so installing this pack pulls in the `sdd` core
plugin automatically. The agent eager-loads core skills (agent-guidelines,
engineering-checklist, test-driven-development, …) cross-plugin by bare name.

## How it fits

The core orchestrator dispatches this pack's agent by its namespaced `subagent_type`
(`sdd-dotnet:dotnet-engineer`) per the routing table in `sdd/references/agent-routing.md`. If this
pack is not installed, core falls back to a general-purpose agent and suggests
installing it. See the [`sdd` README](../sdd/README.md) for the full workflow and the
maintenance guide for adding/maintaining packs.
