---
name: write-pr
description: Use when writing the title and description for a pull request or merge request, or opening one from a finished branch — write the PR description, open a PR, open an MR, 寫 MR 描述, 幫我開 MR, 開 PR, 整理成 MR 說明. NOT for commit messages or changelog entries.
allowed-tools: Bash(git log:*), Bash(git diff:*), Bash(git status:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(git remote:*)
---

# Pull / Merge Request Description

**Goal**: a title and description a reviewer can read in a minute, written from what the branch contains and what was actually run.

## Context (gather first)

- **Base branch**: the one the user names, else the repo's default branch.
- `git log --oneline <base>..HEAD` and `git diff --stat <base>...HEAD`. Open a diff only where the intent is not clear from path and stat.
- `git log --oneline -10` on the base, for the repo's title style (scope usage, casing).
- **Verification evidence**: the commands run in this session and their outcomes (tests, lint, type-check, a manual run). This is the only source for the Verification section.

## Flow

1. **Write the title** in the `commit` skill's format (`type(scope): subject`), with the scope of the package or plugin the whole branch affects.
2. **Write the body** for a reviewer who has the diff. `##` headings in this order; drop a section with nothing to say, except Scope:
   - `## Why`: the problem and the approach, 1–3 short sentences.
   - `## What changed`: 1–3 bullets. Name a symbol or path only where it carries the change.
   - `## Scope`: always. What it covers, and what it deliberately leaves out (a follow-up, a known gap).
   - `## Tradeoffs`: only a rejected alternative a reviewer would otherwise ask about.
   - `## Blast radius`: who or what this touches, and why that is safe or risky. 1–2 sentences.
   - `## Verification`: one bullet per run, each with its outcome. A check that was not run is written `not run`, never implied.
3. **Show the title and body.** Stop there unless the request says to open the PR or MR. When it does, create it with the tool that matches the `origin` remote's host (`gh` for GitHub, `glab` for GitLab, or a connected MCP for that forge). With no such tool, print the text for pasting and say nothing was created. A branch that is not pushed is the user's call: report it, do not push.

## Guardrails

- Every claim comes from the diff, the log, or a recorded run. Nothing is invented, Verification above all.
- Keep the body under about 40 lines. Long evidence (logs, full SHAs, file-by-file lists) goes in a linked artifact.
- No attribution, tool mentions, or promotional text.
- Write in the language of the repo's recent commits; English when there is no signal.
