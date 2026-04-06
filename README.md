# Eli Claude Marketplace

A personal [Claude Code](https://claude.ai/code) plugin marketplace hosting custom skills and commands.

## Plugins

| Plugin | Description | Compatibility |
|--------|-------------|---------------|
| [dev-workflow](./plugins/dev-workflow) | Daily workflow commands — commit, release, prompt audit | Claude Code · Codex |
| [issue-tracing](./plugins/issue-tracing) | On-call triage — turn a Grafana or Kibana/ELK URL into a structured incident report | Claude Code · Codex |
| [sdd](./plugins/sdd) | Spec-driven multi-agent development workflow — propose, validate, apply, complete | Claude Code (Codex: degraded) |

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

**Step 3** — install the plugin:

```
/plugin install bingeli1379/eli-marketplace --scope local
```

**Step 4** — restart Claude Code to load the plugin.

## Uninstall

```
/plugin uninstall bingeli1379/eli-marketplace --scope local
```

## License

MIT
