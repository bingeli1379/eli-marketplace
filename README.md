# Eli Claude Marketplace

A personal [Claude Code](https://claude.ai/code) plugin marketplace hosting custom skills and commands.

## Plugins

| Plugin | Description |
|--------|-------------|
| [eli-tools](./plugins/eli-tools) | Daily workflow commands — commit, release, prompt audit |

## Usage

Install this marketplace as a Claude Code plugin source, then use the commands via slash commands in Claude Code.

## Structure

```
.claude-plugin/
  marketplace.json        # Marketplace manifest
plugins/
  <plugin-name>/
    .claude-plugin/
      plugin.json         # Plugin metadata (name, version)
    commands/
      <command-name>.md   # Skill definition (filename = slash command)
```

## Adding a Plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json`:
   ```json
   {
     "name": "<name>",
     "description": "<description>",
     "version": "1.0.0"
   }
   ```
2. Add command files under `plugins/<name>/commands/`
3. Register in `.claude-plugin/marketplace.json`

## License

Private use.
