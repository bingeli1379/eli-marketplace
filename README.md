# Eli Claude Marketplace

A personal [Claude Code](https://claude.ai/code) plugin marketplace hosting custom skills and commands.

## Plugins

| Plugin | Description |
|--------|-------------|
| [eli-tools](./plugins/eli-tools) | Daily workflow commands — commit, release, prompt audit |
| [eureka-sdd](./plugins/eureka-sdd) | Spec-driven multi-agent development workflow — propose, validate, apply, complete |

## Install

**Step 1** — open Claude Code:

```bash
claude
```

**Step 2** — add the marketplace (one-time):

```
/plugin marketplace add bingeli1379/eli-claude-marketplace
```

**Step 3** — install the plugin:

```
/plugin install bingeli1379/eli-claude-marketplace --scope local
```

**Step 4** — restart Claude Code to load the plugin.

## Uninstall

```
/plugin uninstall bingeli1379/eli-claude-marketplace --scope local
```

## License

MIT
