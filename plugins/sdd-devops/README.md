# sdd-devops

**SDD language pack — DevOps / infrastructure.** Extends the [`sdd`](../sdd) core plugin with the
`devops-engineer` agent and DevOps / infrastructure skills. Part of the spec-driven multi-agent workflow.

## What it adds

- **Agent** `sdd-devops:devops-engineer` — Docker containerization, Kubernetes deployment, CI/CD pipelines (GitLab CI / GitHub Actions), infrastructure config, and monitoring.
- **Skills** (7): ci-cd, devops-engineer, docker, gitlab-ci-patterns, gitlab-glab, kubernetes-architect, kubernetes-specialist.

## Install

```
/plugin install sdd-devops@eli-marketplace
```

Declares `dependencies: ["sdd"]`, so installing this pack pulls in the `sdd` core
plugin automatically. The agent eager-loads core skills (agent-guidelines,
engineering-checklist, test-driven-development, …) cross-plugin by bare name.

## How it fits

The core orchestrator dispatches this pack's agent by its namespaced `subagent_type`
(`sdd-devops:devops-engineer`) per the routing table in `sdd/references/agent-routing.md`. If this
pack is not installed, core falls back to a general-purpose agent and suggests
installing it. See the [`sdd` README](../sdd/README.md) for the full workflow and the
maintenance guide for adding/maintaining packs.
