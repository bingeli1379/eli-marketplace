# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A Claude Code plugin marketplace. It hosts custom plugins (skills) distributed via the `.claude-plugin` system.

## Structure

- `.claude-plugin/marketplace.json` — marketplace manifest, lists all plugins with name/source/description
- `plugins/<plugin-name>/` — each plugin directory
  - `.claude-plugin/plugin.json` — plugin metadata (name, version, description)
  - `skills/<skill-name>/SKILL.md` — skill definitions with YAML frontmatter (name, description) and prompt body

Contains:

- **dev-workflow** — daily workflow skills: commit, release, review-prompt
- **issue-tracing** — on-call triage assistant that turns a Grafana or Kibana/ELK URL into a structured incident report
- **sdd** — spec-driven AI development workflow core (proposal, design, tasks → implement, validate, archive): workflow commands, orchestrator, architect, cross-cutting reviewers, universal skills
- **sdd-\<lang\> packs** — optional language packs that extend sdd with one stack's engineer agent + skills: `sdd-vue`, `sdd-dotnet`, `sdd-python`, `sdd-godot`, `sdd-electron`, `sdd-database`, `sdd-devops`. Each declares `dependencies: ["sdd"]`. See `plugins/sdd/CLAUDE.md` → *Plugin Topology* and `plugins/sdd/references/agent-routing.md`.

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

## Skill Development Rules (apply to ALL skills in this repo)

1. **No company-specific information.** Skills are public; do not write internal service names, hostnames, FQDNs, internal domains, dashboard UIDs, or any identifying values. Use placeholders like `<svc>`, `<host>`, `<dc>`, `<internal-domain>`. Examples and templates must be generic.

2. **Times in user-facing output use GMT+8 (Asia/Taipei).** Convert any UTC values from URLs, logs, or APIs before producing reports. Show the timezone explicitly (`GMT+8` / `+08:00`).

3. **Preflight inputs that need the user.** Anything that requires the user to do something (e.g. `/add-dir`, supply credentials, confirm a path) must be the FIRST step of the skill flow, not buried mid-flow. Resolve it before doing the bulk of the work so a missing input does not waste prior tool calls.
