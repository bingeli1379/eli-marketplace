---
name: commit
description: Use when committing staged changes or when the user asks to commit, write a commit message, or run /commit.
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git commit:*), Bash(git reset:*)
---

# Commit Message Generation

**Type**: Automated dev workflow
**Goal**: Group uncommitted changes into logical commits and create them, each following Conventional Commits.

## Context (gathered at invocation)

- Status: !`git status --short`
- Change stat: !`git diff --stat HEAD`
- Recent commits (style reference): !`git log --oneline -10`

User instruction (optional): $ARGUMENTS

## Flow

1. **Honor the user instruction first.** If `$ARGUMENTS` says how to commit (e.g. "one commit", "split X and Y", named files, or a fixed message), follow it and skip any grouping decision it already resolves.
2. **Default = split by concern.** Group changes into the smallest set of cohesive commits: one concern per commit. A feature, a bug fix, and a chore must NOT share a commit. Untracked files show as `??` in status — include them.
   - **Read frugally.** Work from the injected `--stat` first. Open the full diff (`git diff HEAD -- <file>`) ONLY for files whose intent isn't clear from path + stat. Skip pure renames, deletions, and obvious-from-path changes.
   - **Never read generated/vendored content.** Lock files (`package-lock.json`, `pnpm-lock.yaml`, `*.sum`), `dist/`, `*.min.js`, snapshots, etc. — classify as `chore` by filename alone, do not open them.
   - **One read, not N.** When the changeset is small, run a single `git diff HEAD` instead of one call per file; switch to targeted per-file reads only when the diff is large.
3. **Match this repo's style** from the recent-commits log (scope usage, casing, prefixes) on top of the format rules below.
4. For each group, in dependency order: stage only that group's files (`git add <files>`), then `git commit`. Never `git add -A` when splitting.
5. After committing, report the result (`git log --oneline -<n>`).

## Rules

- Write in English
- Only describe technical content
- Generate the message from the actual diff, not the file names alone

### Format
```
<type>(<scope>)!: <title>

<body>

<footer>
```
`(<scope>)` and the breaking-change `!` are both optional — see below.

### Scope
- Optional, lowercase noun in parens: `feat(parser): ...`
- In a monorepo / multi-package repo, scope to the affected package or plugin (e.g. `feat(dev-workflow):`, `fix(sdd):`)
- Omit when the change is repo-wide or spans many packages
- Splitting by concern usually leaves one package per commit — let that drive the scope

### Breaking changes
- Append `!` after type/scope, before the colon: `feat!:` or `feat(api)!:`
- Also add a `BREAKING CHANGE: <description>` footer explaining what breaks and the migration path

### Types
| Type | Purpose |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change (no feature/fix) |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `docs` | Documentation changes |
| `style` | Formatting, whitespace |
| `chore` | Maintenance, dependencies |
| `ci` | CI/CD changes |
| `build` | Build system changes |

### Description Rules
- Imperative mood: "add" not "added"
- Lowercase first letter
- No period at the end
- Keep under 50 characters

### Body
- Separate from title with blank line
- Wrap at 72 characters
- Explain "what" and "why", not "how"
- Skip for self-explanatory changes

### DO NOT
- Use past tense ("added", "fixed")
- Write vague descriptions ("bug", "changes", "stuff")
- Add promotional or attribution blocks
