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

4. **Only edit skills the repo authors; never rewrite an upstream-synced skill's body.** Before editing any skill body, check `plugins/sdd/skills/SOURCES.yaml`: only `repo: original` skills are ours to edit. A skill marked `repo: <url>` is an upstream mirror — `scripts/update-skills.sh` replaces its body on the next sync, so a body edit is lost. Its frontmatter `description` IS safe to change (sync preserves local frontmatter) for a trigger-wording tweak. To change behavior around a synced skill, edit what the repo owns (an agent, a workflow-core skill, an original skill) or its description. Agent `.md` files are always ours to edit.

5. **Keep each plugin self-contained — no cross-plugin / cross-marketplace references.** A `${CLAUDE_PLUGIN_ROOT}` path must stay within the plugin's own directory; refer to another skill only by name (Skill tool) and only within the same plugin. A reference that crosses plugin boundaries breaks whenever the other plugin isn't installed and couples release cycles. (E.g. sdd's own `conventional-commits` stays independent of dev-workflow's `/commit`.)

## Structure Validation

`scripts/check-structure.sh` validates the marketplace's deterministic invariants: JSON manifests parse, `marketplace.json` ↔ on-disk plugins, every skill/agent `name:` equals its directory/filename (a mismatch is a silent load failure), sdd-family `SOURCES.yaml` coverage, and wrong-base bundled-file reads. It is fast and token-free.

**Run it at the START of a review pass — before `/review-prompt` or `/review-workflow` — whenever a change touches plugin/skill/agent structure or a manifest** (adding/renaming/moving a plugin, skill, or agent; editing any `plugin.json`, `marketplace.json`, or `SOURCES.yaml`). Fold any failures into the same fix cycle as the review findings, so structural and prompt/logic issues are fixed together before committing. If the diff has no structural change, skip it. Not tied to `/commit` — that skill is generic across repos and must not carry a marketplace-specific check.
