# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A Claude Code plugin marketplace. It hosts custom plugins (skills/commands) distributed via the `.claude-plugin` system.

## Structure

- `.claude-plugin/marketplace.json` — marketplace manifest, lists all plugins with name/source/description
- `plugins/<plugin-name>/` — each plugin directory
  - `.claude-plugin/plugin.json` — plugin metadata (name, version, description)
  - `commands/<command-name>.md` — skill definitions in Markdown (the prompt files that Claude Code executes)

Currently contains one plugin: **eli-tools** (daily workflow commands: commit, release, review-prompt).

## Adding a New Plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with name, description, version
2. Add command files under `plugins/<name>/commands/`
3. Register the plugin in `.claude-plugin/marketplace.json` under the `plugins` array

## Adding a New Command to an Existing Plugin

Create a Markdown file at `plugins/<plugin-name>/commands/<command-name>.md`. The filename becomes the slash command name.

## Command File Conventions

- Each command `.md` starts with a title, type, and goal
- Instructions are structured with numbered steps and tables
- Rules/guardrails go at the bottom
- Audit report language: Traditional Chinese (technical terms stay English)
- All commit messages and code comments: English, imperative mood
- Follows Conventional Commits format for commit-related tooling
