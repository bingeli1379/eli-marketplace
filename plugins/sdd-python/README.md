# sdd-python

**SDD language pack — Python backend / ML.** Extends the [`sdd`](../sdd) core plugin with the
`python-engineer` agent and Python backend / ML skills. Part of the spec-driven multi-agent workflow.

## What it adds

- **Agent** `sdd-python:python-engineer` — FastAPI endpoints, data pipelines, ML model integration, database access, and testing.
- **Skills** (6): async-python-patterns, llm-evaluation, prompt-engineering-patterns, python-anti-patterns, python-performance-optimization, python-testing-patterns.

## Install

```
/plugin install sdd-python@eli-marketplace
```

Declares `dependencies: ["sdd"]`, so installing this pack pulls in the `sdd` core
plugin automatically. The agent eager-loads core skills (agent-guidelines,
engineering-checklist, test-driven-development, …) cross-plugin by bare name.

## How it fits

The core orchestrator dispatches this pack's agent by its namespaced `subagent_type`
(`sdd-python:python-engineer`) per the routing table in `sdd/references/agent-routing.md`. If this
pack is not installed, core falls back to a general-purpose agent and suggests
installing it. See the [`sdd` README](../sdd/README.md) for the full workflow and the
maintenance guide for adding/maintaining packs.
