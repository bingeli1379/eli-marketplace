# Eli Marketplace

A personal [Claude Code](https://claude.ai/code) plugin marketplace hosting custom skills and commands.

## Plugins

| Plugin | Description | Compatibility |
|--------|-------------|---------------|
| [dev-workflow](./plugins/dev-workflow) | Daily workflow commands — commit, release, prompt audit | Claude Code · Codex |
| [issue-tracing](./plugins/issue-tracing) | On-call triage — turn a Grafana or Kibana/ELK URL into a structured incident report | Claude Code · Codex |
| [sdd](./plugins/sdd) | Spec-driven multi-agent development workflow core — propose, validate, apply, complete | Claude Code (Codex: degraded) |
| [sdd-vue](./plugins/sdd-vue) | SDD language pack — Vue/Nuxt frontend engineer and frontend skills | Claude Code (Codex: degraded) |
| [sdd-dotnet](./plugins/sdd-dotnet) | SDD language pack — ASP.NET / .NET backend engineer and skills | Claude Code (Codex: degraded) |
| [sdd-python](./plugins/sdd-python) | SDD language pack — Python backend/ML engineer and skills | Claude Code (Codex: degraded) |
| [sdd-godot](./plugins/sdd-godot) | SDD language pack — Godot game engineer and skills | Claude Code (Codex: degraded) |
| [sdd-electron](./plugins/sdd-electron) | SDD language pack — Electron desktop/game engineer and skills | Claude Code (Codex: degraded) |
| [sdd-database](./plugins/sdd-database) | SDD language pack — database engineer and datastore skills | Claude Code (Codex: degraded) |
| [sdd-devops](./plugins/sdd-devops) | SDD language pack — DevOps engineer and infrastructure skills | Claude Code (Codex: degraded) |

The `sdd-*` language packs each declare `dependencies: ["sdd"]`, so installing a pack pulls in the `sdd` core automatically.

**Compatibility legend**

- **Claude Code · Codex** — fully portable. Claude-specific frontmatter (`allowed-tools`, `$ARGUMENTS`) is silently ignored or gracefully degraded on Codex; behavior is otherwise identical.
- **Claude Code (Codex: degraded)** — built around Claude Code subagent dispatch (`agents/*.md` + `subagent_type`), which Codex does not support. The skills still load on Codex but run inline in the main agent without the specialized parallel agent orchestration.

## Install

**Step 1** — open Claude Code:

```bash
claude
```

**Step 2** — add the marketplace (one-time):

```
/plugin marketplace add bingeli1379/eli-marketplace
```

**Step 3** — install a plugin by `<plugin>@<marketplace>` (the marketplace name is `eli-marketplace`):

```
/plugin install sdd@eli-marketplace
```

Repeat for any plugin listed above (e.g. `sdd-vue@eli-marketplace`, `dev-workflow@eli-marketplace`). Installing an `sdd-*` pack pulls in the `sdd` core automatically.

**Step 4** — restart Claude Code to load the plugin.

## Uninstall

```
/plugin uninstall sdd@eli-marketplace
```

## License

MIT
