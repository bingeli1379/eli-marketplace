---
name: skill-authoring-guidelines
description: >
  Use when creating or editing SKILL.md files within the sdd plugin.
  Covers description writing rules (CSO), frontmatter format, and file structure conventions.
  MUST be loaded when: adding new skills, modifying skill descriptions, or reviewing skill quality.
user-invocable: false
---

# Skill Authoring Guidelines

Standards for writing effective SKILL.md files that Claude can discover and follow correctly.

## Claude Search Optimization (CSO)

**The most important rule for skill descriptions.**

Claude reads the `description` field to decide whether to load a skill. If the description summarizes the skill's workflow, Claude may follow the description as a shortcut and skip reading the full SKILL.md.

### Description MUST

- Start with "Use when..." — focus on triggering conditions only
- Describe the problem, situation, or symptom that signals this skill applies
- Include specific keywords agents would search for (error messages, tool names, symptoms)

### Description MUST NOT

- Summarize the skill's process or workflow
- List what the skill "covers" or "does"
- Describe outputs or deliverables
- Include step-by-step actions

### Examples

```yaml
# BAD: Summarizes workflow — Claude may follow this instead of reading SKILL.md
description: Run accessibility audits using axe-core and eslint-plugin-jsx-a11y with configurable scan modes

# BAD: Lists content — wastes tokens, doesn't help triggering
description: Covers JWT Bearer, ASP.NET Identity, policy-based authorization, OpenID Connect

# GOOD: Trigger conditions only
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes

# GOOD: Symptoms and situations
description: Use when tests have race conditions, timing dependencies, or pass/fail inconsistently
```

**Why this matters:** Testing revealed that a description saying "code review between tasks" caused Claude to do ONE review, even though the SKILL.md flowchart clearly showed TWO reviews (spec compliance then code quality). Removing the workflow summary from the description fixed the issue.

## Frontmatter Format

```yaml
---
name: kebab-case-name
description: >
  Use when [triggering conditions].
  MUST be loaded when: [mandatory triggers].
user-invocable: false  # true only for /slash-command skills
---
```

- `name`: letters, numbers, hyphens only (no special chars)
- `description`: max 1024 characters total. Third person. No workflow summary.
- `user-invocable`: `true` for skills the user invokes directly (esdd-* commands), `false` for reference skills

## File Structure

```
skills/
  skill-name/
    SKILL.md              # Main reference (required)
    supporting-file.*     # Only if needed (heavy reference or reusable tools)
```

- Keep content inline when possible (< 100 lines of reference)
- Extract to separate files only for heavy reference (100+ lines) or reusable scripts/tools
- One excellent example beats many mediocre ones

## SOURCES.yaml

Every skill must have an entry in `skills/SOURCES.yaml`:

```yaml
# For skills from external repos
skill-name:
  repo: https://github.com/org/repo
  path: skills/skill-name

# For sdd original skills
skill-name:
  repo: original
```

## Cross-Referencing

Reference other skills by qualified name:

```markdown
# GOOD: clear requirement marker
Use the `sdd:test-driven-development` skill for writing proper failing tests.

# BAD: file path reference (unclear if required, fragile)
See skills/test-driven-development/SKILL.md
```

Do NOT use `@` syntax to reference files — it force-loads content and burns context tokens.
