---
name: commit
description: Use when committing staged changes, or whenever the user asks to commit in ANY phrasing — "commit", "ai commit", "commit 一下", "幫我 commit", asks for a commit message to be written, or runs /commit. Applies even when the commit looks trivial enough to just run `git commit` directly — do not hand-roll the message, invoke this skill.
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git commit:*), Bash(git reset:*)
---

# Commit Message Generation

**Type**: Automated dev workflow
**Goal**: Group uncommitted changes into logical commits and create them, each following Conventional Commits.

## Context (gather first)

Run these and read the output:

- `git status --short` — what changed (untracked files show as `??`)
- `git diff --stat HEAD` — per-file change size
- `git log --oneline -10` — recent commits, for style reference

User instruction (optional): `$ARGUMENTS` (the text passed after the command; empty if none)

## Flow

1. **Honor the user instruction first.** If `$ARGUMENTS` says how to commit (e.g. "one commit", "split X and Y", named files, or a fixed message), follow it and skip any grouping decision it already resolves.
2. **Default = split by concern.** Group changes into the smallest set of cohesive commits: one concern per commit. Untracked files show as `??` in status — include them.
   - Work from the `--stat` output; open a diff only where the intent is not clear from path and stat. **Never open generated or vendored content** — lock files (`package-lock.json`, `pnpm-lock.yaml`, `*.sum`), `dist/`, `*.min.js`, snapshots — classify those as `chore` by filename alone.
   - **A lock file goes in the commit that changed its manifest**, not in a `chore` commit of its own. When the same changeset touches a dependency manifest (`package.json`, `*.csproj`, `pyproject.toml`, `go.mod`), the lock beside it is part of that change: splitting them leaves the manifest commit with a lock that does not match it, and a checkout there fails a frozen-lockfile install. A lock changed with no manifest change in the set is a `chore` commit as above.
3. **Match this repo's style** from the recent-commits log (scope usage, casing, prefixes) on top of the format rules below.
4. For each group, in dependency order: stage only that group's files (`git add <files>`), then `git commit`. Never `git add -A` when splitting.
5. After committing, report the result (`git log --oneline -<n>`).

## Rules

- Write in English
- Only describe technical content
- Generate the message from the actual diff, not the file names alone
- No promotional or attribution blocks

### Format

Conventional Commits: `<type>(<scope>)!: <title>`, blank line, body, footer. Types are the standard set (`feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `chore`, `ci`, `build`); a breaking change carries `!` after type/scope and a `BREAKING CHANGE: <description>` footer naming what breaks and the migration path.

- **Scope**: in a monorepo / multi-package repo, scope to the affected package or plugin (e.g. `feat(dev-workflow):`, `fix(sdd):`); omit when the change is repo-wide or spans many packages
- **Title**: imperative mood ("add" not "added"), lowercase first letter, no trailing period, under 50 characters
- **Body**: wrap at 72 characters; explain "what" and "why", not "how"; skip for self-explanatory changes
