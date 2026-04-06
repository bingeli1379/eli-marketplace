# sdd-godot

**SDD language pack — Godot game development.** Extends the [`sdd`](../sdd) core plugin with the
`godot-engineer` agent and Godot game development skills. Part of the spec-driven multi-agent workflow.

## What it adds

- **Agent** `sdd-godot:godot-engineer` — GDScript-first (C# capable) Godot 4.x: scenes, nodes, autoloads, signals, resources, and game systems (player controller, inventory, dialogue, save/load, HUD).
- **Skills** (31): csharp-godot, csharp-signals, gdscript-advanced, gdscript-patterns, godot-2d-essentials, godot-animation-system, godot-audio-system, godot-camera-system, godot-code-review, godot-component-system, godot-debugging, godot-dependency-injection, godot-dialogue-system, godot-event-bus, godot-export-pipeline, godot-hud-system, godot-input-handling, godot-inventory-system, godot-localization, godot-math-essentials, godot-optimization, godot-physics-system, godot-player-controller, godot-project-setup, godot-resource-pattern, godot-save-load, godot-scene-organization, godot-state-machine, godot-testing, godot-tween-animation, godot-ui.

## Install

```
/plugin install sdd-godot@eli-marketplace
```

Declares `dependencies: ["sdd"]`, so installing this pack pulls in the `sdd` core
plugin automatically. The agent eager-loads core skills (agent-guidelines,
engineering-checklist, test-driven-development, …) cross-plugin by bare name.

## How it fits

The core orchestrator dispatches this pack's agent by its namespaced `subagent_type`
(`sdd-godot:godot-engineer`) per the routing table in `sdd/references/agent-routing.md`. If this
pack is not installed, core falls back to a general-purpose agent and suggests
installing it. See the [`sdd` README](../sdd/README.md) for the full workflow and the
maintenance guide for adding/maintaining packs.
