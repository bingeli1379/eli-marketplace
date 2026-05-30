# Eli Claude Marketplace

A personal [Claude Code](https://claude.ai/code) plugin marketplace hosting custom skills and commands.

## Plugins

| Plugin | Description |
|--------|-------------|
| [dev-workflow](./plugins/dev-workflow) | Daily workflow commands — commit, release, prompt audit |
| [issue-tracing](./plugins/issue-tracing) | On-call triage — turn a Grafana or Kibana/ELK URL into a structured incident report |
| [eureka-sdd](./plugins/eureka-sdd) | Spec-driven multi-agent development workflow — propose, validate, apply, complete |

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
