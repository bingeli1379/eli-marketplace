# sdd-electron

**SDD language pack — Electron desktop / game.** Extends the [`sdd`](../sdd) core plugin with the
`electron-engineer` agent and Electron desktop / game skills. Part of the spec-driven multi-agent workflow.

## What it adds

- **Agent** `sdd-electron:electron-engineer` — Electron main/preload, IPC, native OS integration, window management, auto-update, packaging, plus web rendering (Three.js/TresJS, PixiJS) for desktop games; strict contextIsolation/sandbox.
- **Skills** (5): electron, electron-dev, pixi-js, threejs-geometry, threejs-tresjs.

## Install

```
/plugin install sdd-electron@titansoft-marketplace
```

Declares `dependencies: ["sdd"]`, so installing this pack pulls in the `sdd` core
plugin automatically. The agent eager-loads core skills (agent-guidelines,
engineering-checklist, test-driven-development, …) cross-plugin by bare name.

## How it fits

The core orchestrator dispatches this pack's agent by its namespaced `subagent_type`
(`sdd-electron:electron-engineer`) per the routing table in `sdd/references/agent-routing.md`. If this
pack is not installed, core falls back to a general-purpose agent and suggests
installing it. See the [`sdd` README](../sdd/README.md) for the full workflow and the
maintenance guide for adding/maintaining packs.
