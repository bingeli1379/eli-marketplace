# dev-workflow

Daily workflow skills for Claude Code.

## Skills

### `/commit` — Commit Message Generation

Inspects staged changes and generates a [Conventional Commits](https://www.conventionalcommits.org/) message, then executes the commit automatically.

- Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `chore`, `ci`, `build`
- Title: imperative mood, lowercase, under 50 chars, no period
- Body: explains "what" and "why", wraps at 72 chars, skipped for self-explanatory changes

### `/release` — Release Changelog & Version Bump

Detects the current version from project files (package.json, csproj, pyproject.toml, etc.), compares changes since the last release, generates a [Keep a Changelog](https://keepachangelog.com/) entry, bumps the version, and commits.

- Auto-determines bump level: major (breaking), minor (feat), patch (fix/refactor)
- Changelog written from end-user perspective
- Internal refactors, CI tweaks, dependency bumps are omitted unless user-facing

### `/review-prompt` — Prompt Audit

Audits agent and skill prompt files (`.md`) for quality risks. Rates each finding as **SAFE**, **RISKY**, or **BROKEN**, then auto-fixes issues until all files pass.

**Claude-first review architecture.** Claude Code is the authoritative, primary target — the audit optimizes for Claude effectiveness and treats Claude-specific features (`${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_SKILL_DIR}`, bang-backtick context injection, `Task` / subagent dispatch, `$ARGUMENTS`, `hooks`, `model:` / `effort:`) as correct and intended — **not** as portability liabilities to genericize away. The [Agent Skills open standard](https://agentskills.io) (`name` + `description` + plain markdown) is the portable baseline you get for free; cross-harness support (Codex, etc.) is the job of a downstream build/compile step that transforms this authoritative source, never of degrading the source itself.

- General audits: instruction completeness, code examples, templates, guardrails, cross-agent / cross-file consistency, context bloat, hardcoded values, reference path integrity
- Claude-correctness checks: bundled-file read instructions must use `${CLAUDE_PLUGIN_ROOT}/` (plugin-level) or `${CLAUDE_SKILL_DIR}/` (skill-own) — a bare relative path resolves against the user's working directory, not the skill dir; `name:` must equal the skill's parent directory; `model:` / `effort:` belong only on *dispatched* subagents, not on an agent the main session adopts as a persona (it inherits the session)
- Max 3 auto-fix rounds
- Report language: Traditional Chinese (technical terms in English)

### `/review-workflow` — Workflow Logic Audit

Companion to `/review-prompt`. Where `/review-prompt` judges prompt *text* quality, this audits a workflow / orchestration skill for *behavioral* correctness — it traces the described procedure as a state machine and finds where execution breaks: non-idempotent resume, step-ordering that destroys state a later step needs, cross-step contradictions, broken invariants, unhandled edge cases (crash mid-step, empty input, multi-repo, no-git), dependency-graph gaps, and destructive-op / data-loss paths.

- Each finding is rated **CONFIRMED** (a concrete failing scenario was traced) or **PLAUSIBLE**, ranked by severity, with the input → wrong-outcome scenario spelled out
- **Fix by default** — applies the CONFIRMED, unambiguous fixes; design-choice fixes are surfaced for you to decide. Pass `--report-only` to only surface findings without touching files
- Report language: Traditional Chinese (technical terms in English)

### `/improve-skill` — Improve Skills from Real Usage

Usage-driven and cross-repo. When a marketplace skill (`/sdd`, `/commit`, `/review`, `/issue-tracing`, …) misbehaves, misses a case, or feels clunky while you use it as a tool in *another* project, `/improve-skill` reads what went wrong in the session and patches that skill's source in your local marketplace repo — the git working copy, **not** the installed cache — then validates the edits via `/review-prompt`, `/review-workflow`, and the structure check.

- Resolves the marketplace repo path from your global `~/.claude/CLAUDE.md` (asks once and offers to record it if missing)
- Proposes a changeset for review before applying; routes durable preferences to memory / `CLAUDE.md` instead of editing a skill
- Evidence-driven — only fixes things that actually went wrong when the skill was used, not speculative polish
- Does **not** commit, push, or reinstall the plugin — you do those afterward so the fix goes live
- Report language: Traditional Chinese (technical terms in English)
