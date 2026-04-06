# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A Claude Code plugin marketplace. It hosts custom plugins (skills) distributed via the `.claude-plugin` system.

## Structure

- `.claude-plugin/marketplace.json` — marketplace manifest, lists all plugins with name/source/description
- `plugins/<plugin-name>/` — each plugin directory
  - `.claude-plugin/plugin.json` — plugin metadata (name, version, description)
  - `skills/<skill-name>/SKILL.md` — skill definitions with YAML frontmatter (name, description) and prompt body

Currently contains one plugin: **eli-tools** (daily workflow skills: commit, release, review-prompt).

## Adding a New Plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with name, description, version
2. Add skill directories under `plugins/<name>/skills/`
3. Register the plugin in `.claude-plugin/marketplace.json` under the `plugins` array

## Adding a New Skill to an Existing Plugin

Create `plugins/<plugin-name>/skills/<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description` starting with "Use when...") and the prompt body.

## Skill File Conventions

- YAML frontmatter: `name` and `description` (description starts with "Use when...")
- Instructions are structured with numbered steps and tables
- Rules/guardrails go at the bottom
- Audit report language: Traditional Chinese (technical terms stay English)
- All commit messages and code comments: English, imperative mood
- Follows Conventional Commits format for commit-related tooling
