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

### `skill-authoring` — Write-Time Rules for Skills

**Not a command** (`user-invocable: false`) — it has nothing to run. It loads itself before you write or edit a skill, an agent file, or the prose they bundle, and carries the authoring rules in **positive** form — how to write so the defect never lands. Derived from what audits and real use kept catching: descriptions that summarize instead of trigger, an example list quietly becoming the agent's whole permitted set, position-shaped names (`step1`, `notes.md`) that die on the first reorder, bare relative paths that resolve against the user's cwd, `name:` drifting from its directory, step handoffs nobody wrote down, an edit that never reached the rule's other five homes, and synonym drift that makes one concept read as three.

- **Cost has an order** — restructure the flow so the words are unnecessary, then merge near-duplicate wording, then extract what is not always needed, then cut the lecture; never shorten a rule into ambiguity. Trimming prose is the last and smallest lever, not the first
- **Structure over prose** — a sequence gets numbered steps, repeated items get fixed fields, so a missing field shows up as an empty cell instead of hiding inside a paragraph
- **State and dependencies** — a skill that writes files or runs git says what a second run does and guards destructive ops; anything it leans on from outside (an argument, a tool or MCP server, a sibling skill, a file) needs a stated absence plan, announced rather than silently skipped
- **Behavior-preserving vs behavior-changing** — a restructure keeps every decision identical; if a behavior changes, the edit has to say which and why, because the diff will not
- Deliberately short — it loads on every skill edit, so every line has to earn its place
- Pairs with `/review-skill` through one shared file: the rules live in the plugin's `references/authoring-rules.md`, which this skill follows while writing and `/review-skill` audits against — each entry carries the rule, what breaks without it, and how the violation is visible (or a `process` mark when it governs the author rather than the file). A rule added there is enforced on both sides with no second copy
- Ends where the work ends: run the repo's structure script, then `/review-skill` on what changed

### `/review-skill` — Skill Audit

Audits prompt files (`.md`) — a skill, an agent, an output style, or the references and templates they bundle — on two levels: whether the prompt still **says** the right thing (the text pass) and whether the procedure it describes actually **behaves** correctly, without duplicated or drifting content around it (the deep lenses).

**One pass, both layers, always — there is no cheap mode.** A change that looks like pure wording is exactly the shape whose blast radius lands in another file, so a pre-judged "text-only" run would skip the lenses precisely where they pay. Cost is controlled by method instead: one read per file serving both layers, Lens B swept grep-first rather than by reading every sibling, and a report that carries findings rather than narration. **Coverage itself is never traded** — a file set too big for one pass is taken 3–5 files at a time, each batch a complete pass, running until nothing is pending; what the run has not reached yet is reported as `待審`, never as a skip. `--report-only` surfaces findings without applying fixes.

**Claude-first review architecture.** Claude Code is the authoritative, primary target — the audit optimizes for Claude effectiveness and treats Claude-specific features (`${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_SKILL_DIR}`, bang-backtick context injection, `Task` / subagent dispatch, `$ARGUMENTS`, `hooks`, `model:` / `effort:`) as correct and intended — **not** as portability liabilities to genericize away. The [Agent Skills open standard](https://agentskills.io) (`name` + `description` + plain markdown) is the portable baseline you get for free; cross-harness support (Codex, etc.) is the job of a downstream build/compile step that transforms this authoritative source, never of degrading the source itself.

- **Text pass** (criteria a–x): instruction completeness, code examples, templates, guardrails, cross-agent / cross-file consistency, context bloat, hardcoded values, reference path integrity, wording contradictions, steering effectiveness. Findings rated **SAFE** / **RISKY** / **BROKEN** / **NOTE**, auto-fixed until every file passes, max 3 rounds
- **Lens A — procedural logic**: traces the described procedure as a state machine and finds where execution breaks — non-idempotent resume, step-ordering that destroys state a later step needs, cross-step contradictions, broken invariants, unhandled edge cases (crash mid-step, empty input, multi-repo, no-git), dependency-graph gaps, destructive-op / data-loss paths, and an insertion that invalidates its own neighbour
- **Lens B — duplication & SSOT**: substantial blocks copied across files, concepts with no canonical home, and a changed rule left half-applied. Swept grep-first from distinctive tokens in the change — cheaper and more accurate than reading every sibling
- Lens findings are rated **CONFIRMED** (a concrete failing scenario was traced) or **PLAUSIBLE**, ranked by severity, with the input → wrong-outcome scenario spelled out
- **Fix by default** — text findings are fixed without asking, and a lens fix resting on a design choice is decided and applied too, then reported under `我做的抉擇` for you to overrule; only a fact living outside every readable file is escalated as a question. Pass `--report-only` to only surface findings without touching files
- Claude-correctness checks: bundled-file read instructions must use `${CLAUDE_PLUGIN_ROOT}/` (plugin-level) or `${CLAUDE_SKILL_DIR}/` (skill-own) — a bare relative path resolves against the user's working directory, not the skill dir; `name:` must equal the skill's parent directory; `model:` / `effort:` belong only on *dispatched* subagents, not on an agent the main session adopts as a persona (it inherits the session)
- Report language: Traditional Chinese (technical terms in English)

### `/improve-skill` — Improve Skills from Real Usage

Usage-driven and cross-repo. When anything a plugin ships — a skill, an output style or persona, an agent, a hook — misbehaves, misses a case, or feels clunky while you use it as a tool in *another* project, `/improve-skill` reads what went wrong in the session and patches that target's source in the local marketplace repo that owns it — the git working copy, **not** the installed cache — then validates the edits via `/review-skill` and the structure check.

- Resolves each target's owning marketplace repo path from your global `~/.claude/CLAUDE.md` (asks once and offers to record it if missing); one run may span several repos, and each is edited, validated, and handed off separately
- Ranks the changeset and applies it — no confirm gate; the report says what it decided. Routes durable preferences to memory / `CLAUDE.md` instead of editing a skill
- Evidence-driven — only fixes things that actually went wrong when the skill was used, not speculative polish
- Does **not** commit, push, or reinstall the plugin — you do those afterward so the fix goes live
- Report language: Traditional Chinese (technical terms in English)
