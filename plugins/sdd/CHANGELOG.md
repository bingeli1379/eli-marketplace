# Changelog

## [3.0.0-beta.1] - 2026-06-19

### Changed
- Language specialists now ship as optional packs. The Vue, .NET, Python, Godot, Electron, database, and DevOps engineers — and their stack-specific skills — moved out of this core plugin into separate `sdd-<lang>` packs. Install only the stacks you work in; the core keeps the workflow commands, orchestrator, architect, reviewers, and shared skills. Installing any pack pulls in core automatically.
- When a task needs a language pack you have not installed, sdd now runs the work with a general-purpose agent and tells you which pack to install for full specialist quality, instead of failing.

## [2.7.0] - 2026-06-19

### Added
- Godot game development support — you can now build Godot 4.x games (GDScript-first, and C# where the project uses it) through the full spec-driven pipeline. Adds a dedicated game engineer that follows Godot's scene/node composition model, plus a library of Godot skills covering architecture, testing, the C# track, and 2D game systems. Code review and acceptance testing adapt to Godot on their own (headless scene tests instead of a browser, Godot-specific anti-pattern checks), and `/setup` recognizes a Godot project automatically.

### Changed
- Simplified how agents flag missing information: the separate "UNKNOWN" signal is folded into "NEEDS", so there is one clear way an agent pauses for a fact it cannot obtain.

### Fixed
- The orchestrator now finds its role definition reliably across different install locations, so `/apply` starts correctly in setups where it previously could not.

## [2.6.0] - 2026-06-18

### Added
- `/propose` now suggests the lighter `/quick` path when a change is too small to justify full spec ceremony, so you don't over-plan a trivial task.

### Changed
- Implementing a change (`/apply`) now runs as one continuous line of work on a single branch instead of parallel copies — eliminating merge conflicts and divergent working trees, making larger implementations more predictable.
- `/quick` now handles small tasks directly with the right specialist knowledge loaded, instead of spinning up a separate agent first — faster turnaround on trivial and simple changes.
- Design planning now scales its depth to the stakes of the change: lighter for low-risk work, more thorough where the risk is higher.

### Fixed
- `/apply` no longer stalls or wrongly gives up when a background worker goes quiet — it confirms real progress against git history and continues reliably.

## [2.5.2] - 2026-06-17

### Changed
- When a proposed change involves an irreversible or destructive action (bulk deletion, mass external updates, data purges), the design now defaults to the safe path — dry-run / preview / explicit confirmation — with the destructive behavior as a conscious opt-in, encoded in the API contract from the start instead of left to a later review pass.

## [2.5.1] - 2026-06-16

### Changed
- Agents now favor the simplest solution that fits your codebase — reaching for the standard library, a native platform feature, or a dependency you already have before writing new custom code, and not pulling in a new dependency for something a few lines can do. This always stays subordinate to your project's existing conventions: a leaner-but-unfamiliar pattern never replaces how your code already does the same thing, and correctness, security, and accessibility are never traded for brevity
- Code review (and the `/review` quality lens) now also flags over-engineering — reinvented standard-library code, dead abstractions, needless dependencies — and tells you what to delete, while leaving alone the layers your architecture actually requires

## [2.5.0] - 2026-06-11

### Changed
- **Breaking:** `/sdd:init` renamed to `/sdd:setup` to stop colliding with the native `/init` command in the slash-command picker. Update any saved command references or notes — the behavior is unchanged (it still generates `feature-spec/config.yaml`)

### Fixed
- Shared plugin-root references (`repo-topology.md`, `company-conventions.md`) are now addressed via `${CLAUDE_PLUGIN_ROOT}/...` so they resolve in the installed location. They previously used a wrong/relative path (`plugins/sdd/...` or bare `(in the plugin root)`) that did not resolve at runtime, which could break multi-repo topology detection and the pre-lint skip rules

## [2.4.0] - 2026-06-06

### Added
- Agents now stop and ask instead of guessing. When implementing or reviewing a change depends on a fact that isn't in your code or the brief — a live production setting, a value owned by another service, the current state of your infrastructure — the agent flags exactly what it needs instead of inventing a plausible-looking answer, and the workflow looks it up and resumes the agent right where it paused. Planning gathers these facts up front; implementation catches anything that slips through. Works with whatever lookup tools your setup already has, and needs no configuration.

## [2.3.0] - 2026-06-06

### Added
- `/review` — review existing code, a diff, an API, or a stored procedure on its own, by lens (quality / security / performance / end-to-end); the right reviewer is chosen from what you point it at, and it only reports findings — it never edits or commits
- `/role` — turn the conversation into any specialist persona (architect, an engineer, a reviewer, …) and work with it interactively, running on your session's model instead of the agent's lighter dispatch tier
- Performance review now spans the whole stack — backend APIs, SQL / stored procedures, and Python data pipelines, not just the frontend — and adds a data-scale capacity check ("will this pull of N rows hold up, and how much can it pull?") that runs automatically when a change touches an API or database

### Changed
- Specialist agents now load only the skills a task actually needs (the rest load on demand), so each dispatch runs leaner and cheaper

## [2.2.0] - 2026-06-05

### Added
- Agents now ship with knowledge for more stacks out of the box — Kafka consumers (delivery semantics, offset commits, idempotent processing, dead-letter handling), legacy ASP.NET (.NET Framework / WebForms / MVC5), and MongoDB schema design & query optimization — so they produce sound work on these without extra guidance

### Changed
- Every engineer agent now detects your project's actual stack (framework, data store, CI) and follows it, using its built-in defaults only as a fallback — so it fits a Vite SPA, a Vue 2 app, a legacy .NET Framework service, or a MongoDB repo instead of forcing one template
- The Python agent is no longer tied to one codebase's helpers and layout — it now adapts to any FastAPI / data / ML project's own conventions
- The DevOps agent picks the CI system from your repo (GitLab CI or GitHub Actions) instead of always assuming GitHub Actions
- Code review and security review now cover Python projects, not just Vue/Nuxt and .NET

## [2.1.1] - 2026-06-04

### Changed
- During `/apply`, the workflow now always hands each task group to the right specialist agent and runs the full review and security checks — it will no longer take shortcuts and do the work itself, even for small or hard-to-test changes, so every change gets the same quality pipeline

## [2.1.0] - 2026-06-04

### Added
- On a project that ships its own repo-knowledge skill, the implementation agents now pull in that repo's context — its responsibility, dependencies, and conventions — before writing code, so generated work fits the target repo instead of a generic template, with no extra setup from you

## [2.0.0] - 2026-05-30

### Changed
- **Breaking:** workflow commands dropped the `esdd-` prefix — use `/sdd:init`, `/sdd:propose`, `/sdd:validate`, `/sdd:apply`, `/sdd:complete`, and `/sdd:quick` (previously `/esdd-init`, etc.). Update any saved command references or notes
- The scope confirmation shown before implementation now presents each change as a "before → after" view: simple swaps stay on one line, and only changes that ripple through several steps expand into a full flow. Easier to scan and approve at a glance than the previous two-section layout
- `config.yaml` is now the single source of project context. `/init` produces only `config.yaml` (tool commands plus an architecture baseline) and the workflow no longer reads your project's own README or docs, so what the agents rely on is explicit and in one place

### Added
- Multi-repo support: run the workflow from a folder containing several independent repos. Planning lives at the top level, each task group is tied to one repo, cross-repo changes are ordered contract-first, and QA checks the seams between repos
- Generated changes now mirror your existing code — the planner finds the nearest similar file and follows its data-access, query, structure, and naming conventions instead of inventing a new style
- The planner now serializes any two task groups that touch the same file, preventing the parallel edits that previously collided during implementation

### Removed
- **Breaking:** `/init` no longer generates `context.md` or `knowledge.md`, `/complete` no longer extracts knowledge, and the separate knowledge-audit step is gone. Project context is now fully captured by `config.yaml` — delete the old files if you have them

## [1.16.8] - 2026-05-16

### Changed
- `/esdd-propose` and `/esdd-quick` scope confirmation now splits the contract into two sections — **變更清單** (what gets added / replaced / removed, grouped by concept) and **流程鏈** (how a user flow or refactor cascade traces through downstream consumers). Format / shape changes must trace every downstream consumer (CSS classes, asset filenames, string comparisons, etc.) and new-feature flows must end at a user-visible terminal state. Catches the "missed downstream consumer" class of bug that previously only surfaced at Phase 2 review

## [1.16.7] - 2026-05-10

### Changed
- `/esdd-init` SCAN report now collapses high-confidence detections into a single summary line and only lists items that need your eyes (medium / low confidence). Reports stay under one screen instead of sprawling across a 13-row table
- `/esdd-propose` scope confirmation replaces the seven-section block (In-Scope / Out-of-Scope / Assumptions / Unknowns / NFR / Approaches / Recommendation) with a chain-form view (`A → B → C`) that shows the change as a flow you can read like a diff. Approaches collapse to one line when there is no real trade-off, and the follow-up Scope Contract uses the same compact form
- `engineering-checklist` replaces the vague "respect the existing codebase" principle with a concrete directive: open a sibling file and mirror its style before writing new code

## [1.16.6] - 2026-05-02

### Added
- `frontend-checklist` adds a public API boundary rule for JS/TS library/plugin authoring: frontend agents now declare narrow TS types on the public surface so TS callers get compile-time constraints, and add runtime guards that emit `console.warn` with a documented fallback when JS callers (or `as`-casted code) pass wrong types. Keeps host apps alive instead of throwing when input slips through the type contract

## [1.16.5] - 2026-05-01

### Changed
- `/esdd-init` confirmation prompts (Phase 0 keep/regenerate, gap-filling questions, knowledge candidate selection) now render in Traditional Chinese to match the rest of the conversation. The previous refactor accidentally left these strings as the literal English from the skill template
- `/esdd-init` knowledge candidate review now shows a short Traditional Chinese summary alongside the original English claim, making it faster to skim before deciding what to keep. `knowledge.md` content itself still gets written in English so downstream agents read it consistently

## [1.16.4] - 2026-05-01

### Changed
- `/esdd-init` asks fewer questions — only when AI truly cannot infer a section (no README, single source dir, no CLAUDE.md). Medium-confidence guesses now write the draft directly; edit the file if anything is off
- `/esdd-init` batch decisions (knowledge candidate selection, audit findings) use clickable checkboxes instead of typing index lists like `C1,C3,C5` or `A1-A3`. Falls back to mode-based options when there are 5+ items
- `/esdd-init` recognises config-only and docs-only repos (plugin marketplaces, doc sites, etc.) and stops asking about tech stack / lint / verification commands that do not apply
- `/esdd-init` knowledge candidate sources pruned to high-signal only — `.env.example`, informational code comments, and named-symbol historical rules from `CLAUDE.md` / `AGENTS.md` (kept only when the named symbol still resolves in code). README, package.json scripts, and vague historical rules are dropped to reduce noise

### Fixed
- `/esdd-init` batch question no longer fails when only one knowledge candidate or audit finding survives — single-select Apply/Skip fallback added so the question UI satisfies its 2-option minimum

## [1.16.3] - 2026-04-27

### Fixed
- The project context that `/esdd-init` generates (`context.md` and `knowledge.md`) is now actually used by `/esdd-propose`, `/esdd-apply`, and `/esdd-quick`. The architect agent receives the full project map and operational gotchas when designing changes; every implementation agent receives them when writing code. Hard Rules from `context.md` are treated as non-negotiable invariants and Gotchas from `knowledge.md` as binding constraints — previously these files were generated but never read downstream, so the time spent curating them was wasted

## [1.16.2] - 2026-04-26

### Fixed
- `/esdd-init` no longer references the non-existent `/esdd-knowledge-bootstrap` command in its skill prompt or in the generated `knowledge.md` footer — following those instructions previously produced "Unknown command". Skip rules for `HACK` / `FIXME` / `XXX` markers are reframed as "unresolved TODOs, not stable knowledge"; ongoing knowledge accrues through `/esdd-complete` after each change
- `qa-engineer` now preloads `engineering-checklist` via frontmatter, restoring the verify-before-commit gate that was inadvertently dropped during the recent agent frontmatter refactor

### Changed
- `/esdd-init` self-audit now catches half-rotten pointer patterns like `8 subdirs in this path (banners, games, ...)` before writing `context.md` — the count and the inline list both rot, so the audit strips the parenthetical and keeps just the pointer. The `context.md` template's editing rule #3 also calls out parenthetical enumeration variants explicitly, not just `incl. X / Y`

## [1.16.1] - 2026-04-26

### Added
- `/esdd-init` now audits existing `knowledge.md` entries when re-run — verifies every `path:line` citation still resolves, re-reads the snippet to confirm the claim still matches the code, and grep-tests for contradicting branches. Drifted entries surface in the SCAN report with suggested rewrites; one batch reply (`apply` / `keep-all` / pick A-prefix indices / `none`) decides per entry. Saves the `/knowledge-audit` round trip during re-init.

### Changed
- `/esdd-init` produces more durable `context.md` — pointer-over-enumeration is now enforced in every section (not just Domain Map), so cache groups, server plugins, and upstream adapters collapse to `<count> in <path>/` instead of listing identifiers that rot the moment a file moves. A self-audit pass before writing catches enumeration smells, version drift outside Tech Stack, and cross-doc circular Hard Rules references
- `knowledge.md` citations must point to actual code (`.ts`, `.cs`, `.vue`, config files) — citations to other markdown docs like `CLAUDE.md` are silently dropped to avoid circular references. Historical rules reclassified from `CLAUDE.md` are re-anchored to the code location they constrain, otherwise dropped
- `knowledge.md` entries are section-fit checked before append — infrastructure constants (Redis hosts, CDN URLs) no longer get force-fit under "External Dependencies" (which is reserved for upstream service quirks). Misfits are re-classified or flagged in the BUILD summary

## [1.16.0] - 2026-04-26

### Changed
- `/esdd-init` now talks to you in Traditional Chinese for all questions, status updates, and SCAN/BUILD reports; file contents (`config.yaml`, `context.md`, `knowledge.md`) stay in English so downstream agents and code reviewers can read them
- Knowledge candidates are now confirmed inline in the SCAN report — numbered list with `path:line` citation and snippet, then one batch reply (`1,3,5` / `all` / `none`) appends only your selections directly into `knowledge.md`. The intermediate `knowledge.md.draft` file is gone, removing the manual review-and-copy loop.
- `knowledge.md` now lives at `feature-spec/knowledge.md` instead of the project root, sitting next to `context.md` and `config.yaml` so all spec artifacts are in one place. `/esdd-init`, `/esdd-complete`, and `/knowledge-audit` silently move a legacy `./knowledge.md` into the new location with `git mv` (history preserved); both-exist conflicts surface a one-line warning instead of being auto-merged.
- `/esdd-init` generated `context.md` is more durable: Tech Stack uses major-only versions (e.g. `Nuxt 3`, not `Nuxt 3.17.6`) so it does not rot on patch bumps; half-pointer "incl. X / Y" enumerations are banned; lint-enforceable rules are excluded from Hard Rules to keep the list focused on structural invariants
- `/esdd-init` detection picks up more cross-cutting concerns previously slipping through — responsive composables (`useRwdIsMobile`, `useBreakpoint`, `useMedia`) and i18n config — and enforces a hard Glossary split so domain abbreviations (DLH, PPC, KYC, ...) always land in Business Terms instead of being duplicated in Code Terms
- `knowledge.md` skeleton ships with BAD examples (vague / speculative / generic / logic-walkthrough) and a footer pointing at `/knowledge-audit` for periodic rot checks, so contributors see what NOT to write and remember to prune stale entries

## [1.15.1] - 2026-04-26

### Added
- `/esdd-init` now seeds `knowledge.md.draft` at the project root with operational tips harvested from `.env.example`, READMEs, package scripts, and informational code comments — review and merge keepers into `knowledge.md`
- `/esdd-init` now creates an annotated `knowledge.md` skeleton when missing, with per-section guidance comments hinting at high-value categories (upstream service quirks, cache keys, fallback modes, mock-vs-real gaps) so contributors know what kind of facts belong where
- `dev-mode` keyword for `/esdd-apply` and `/esdd-apply-all` — pass it anywhere in the arguments to surface the post-run retrospective; default reports stay clean for end users

### Changed
- `/esdd-init` produces a more durable `context.md`: domain map uses pointer form so it does not rot when files are added or renamed; hard rules separate structural invariants from migration debt; glossary splits into Code Terms (auto-syncable) vs Business Terms (human-curated); conditional subsystems require an explicit trigger condition (header / flag / route / env)
- `/esdd-init` Entry Points scan now walks the full conventional set (HTTP, pages, server middleware, plugins, modules, jobs, handlers, CLI) so areas are no longer silently missed
- Version numbers in `context.md` are kept to a single source — `Tech Stack & Versions` only; other sections refer to the framework by name to prevent stale duplicates
- `knowledge.md` entries are now hard-capped to one line per fact, with speculative "if future X, then Y" entries explicitly rejected to keep the file high-signal

## [1.15.0] - 2026-04-26

### Added
- `/esdd-init` now produces `feature-spec/context.md` alongside `config.yaml` — an AI-readable project map (Mission, Tech Stack, Architecture Layers, Domain-to-Code Map, Entry Points, Cross-cutting Concerns, Hard Rules, optional Glossary, Common Commands) so AI knows *where* to make changes, not just *what* the project uses
- `/esdd-init` now runs two-phase: SCAN (dry-run + at most 3 confirmation questions with default suggestions) then BUILD (writes files) — caps mis-detection by letting the user correct medium-confidence inferences before any file is written

### Changed
- `/esdd-complete` now auto-syncs `feature-spec/context.md` after each completed change — appends new domain folders, entry points, cross-cutting helpers, hard rules, and dev commands derived from the change diff and `design.md`; never touches Mission or Glossary; skipped silently if `context.md` does not exist
- `/esdd-init` re-run UX: per-artifact prompt (regenerate vs keep) instead of a single all-or-nothing overwrite confirmation

## [1.14.0] - 2026-04-25

### Added
- `frontend-checklist` now flags Vite projects whose app-level `tsconfig.json` lacks `noEmit: true` (or `emitDeclarationOnly: true` for publishable packages) — prevents `tsc -b` from silently regenerating phantom `.js` files next to sources

### Changed
- `/esdd-propose` now requires spec THEN clauses and architect design assertions to be verifiable — every behavior claim must cite a command, SHA, or necessary-condition phrasing, cutting hallucinated facts that QA used to catch late
- `/esdd-propose` task authoring bundles `git mv` / path renames with all dependent config edits (tsconfig, eslint, vite, vitest, package exports, CI paths) into a single task, so structural refactors no longer produce intermediate broken states between commits

### Fixed
- `/esdd-apply` now detects when you're on a feature branch ahead of the default branch and commits directly on the branch instead of spawning worktrees — previously lost every in-progress commit because worktrees were created from the default branch, breaking wave-1 merges

## [1.13.0] - 2026-04-18

### Added
- `/esdd-propose` now confirms a "Scope Contract" before generating design.md — catches interpretation mismatches in 10 seconds before the architect spends 5–10 minutes writing the wrong design
- `/esdd-propose` scope clarification now enumerates assumptions, unknowns, and maps boundaries across five axes (feature / integration / data / NFR budget / reversibility) — surfaces silent misinterpretations that used to slip into design.md
- User-facing Tip in `/esdd-propose` and `/esdd-quick` explaining how prefixing `ultrathink` on invocation boosts orchestrator-layer reasoning

### Changed
- Architect and reviewer sub-agents (code review / security / QA) now receive an "Analytical depth requirement" section that forces coverage enumeration, explicit non-findings, severity-ranked findings, and for the architect: 2–3 candidate designs with trade-offs — previously relied on a single keyword that may not reach sub-agents reliably
- `qa-engineer` coverage in `/esdd-quick` now includes authorization cases, matching `/esdd-apply`

## [1.12.1] - 2026-04-15

### Changed
- `/esdd-complete` now writes knowledge entries straight to `knowledge.md` — no more item-by-item confirmation prompts during completion
- Knowledge entries are enforced as one-line pointers (project-specific fact + file path) instead of paragraph walkthroughs, and are always written in English regardless of conversation language

## [1.12.0] - 2026-04-14

### Added
- `/esdd-complete` command replaces `/esdd-archive` — extracts valuable knowledge to `knowledge.md`, updates project docs, and cleans up change directories instead of just archiving them
- `/knowledge-audit` command audits `knowledge.md` entries against the current codebase, flagging stale or outdated knowledge

### Removed
- `/esdd-archive` — superseded by `/esdd-complete` which provides a more useful post-change workflow

## [1.11.3] - 2026-04-10

### Fixed
- esdd-quick now squashes per-task commits into clean group commits after each phase, matching esdd-apply's final commit style (420d743)

## [1.11.2] - 2026-04-08

### Fixed
- Pattern-removal changes (e.g., remove `: any`, `@ts-nocheck`) now require grep-based inventory with full task coverage — dry-run alone can't catch removals of valid-but-unwanted code (f0cd254)

## [1.11.1] - 2026-04-07

### Fixed
- Dry-run now runs both verification and lint commands — type-aware ESLint rules (e.g., `@typescript-eslint/no-unnecessary-type-assertion`) can surface errors that type-check alone misses (1332304)

## [1.11.0] - 2026-04-07

### Added
- `verification_commands` support in config.yaml — agents now use project-defined scripts (e.g., `npm run type-check`) instead of hardcoding tool-specific commands, preventing flag mismatches across projects (ecf2084)

### Changed
- Dry-run type-tightening now requires zero out-of-scope errors: either expand scope or reduce aggressiveness, never defer breakage to future changes (ecf2084)
- Type-tightening discovery checks both backend source and frontend usage to produce the full field union (ecf2084)

## [1.10.0] - 2026-04-06

### Added
- 6 new skills: kubernetes-architect, gitlab-ci-patterns, electron, dataverse-python-production-code, dataverse-python-advanced-patterns, dataverse-python-usecase-builder (d58eed7)

## [1.9.0] - 2026-04-06

### Added
- 7 new skills: dotnet-best-practices, dotnet-upgrade, typescript-advanced-types, playwright-best-practices, frontend-testing-best-practices, tailwind-best-practices, vue-debug-guides (new source) (7f6cff2)

### Changed
- Migrate 15 frozen skills from defunct anthropics/skills to active upstream repos (vuejs-ai/skills, antfu/skills, vueuse/skills, vercel-labs/agent-skills) (7f6cff2)

### Removed
- vue-development-guides skill (upstream removed, no replacement available) (7f6cff2)

## [1.8.0] - 2026-04-06

### Added
- Interrupted state recovery in esdd-apply: detects orphaned worktrees, un-squashed commits, and tasks completed in git but unmarked in tasks.md — enables seamless resume after token limit interruptions (1078565)

### Fixed
- Propose now generates specs before design, letting architect receive specs as constraints with a CONFLICT marker mechanism for disagreements (141bb73)
- Dry-run scope expanded to type-level changes (index signature removal, type defaults, `Partial<T>`) with bounded tasks instead of catch-all "fix all" (141bb73)
- Group complexity estimation prevents token exhaustion on large analytical groups (141bb73)
- Post-merge auto-squash fallback for worktree commits that leak to main without squash (141bb73)

## [1.7.0] - 2026-04-05

### Added
- Implementation protocol for worker agents: 5-step pipeline (read conventions → look up best practices via context7 → decide approach → implement → verify consistency) enforced when modifying existing code (b554e3c)

## [1.6.0] - 2026-04-04

### Added
- Auto-commit step in esdd-propose to persist spec artifacts immediately after generation (b53a3cf)
- Token efficiency guards: anti-narration rule for worker agents, hallucination guard for architect, stop-when-tests-pass checklist item (6e08f74)
- Report templates localized to Traditional Chinese (orchestrator, apply, apply-all) (a4b019a)

### Fixed
- Branch cleanup after merge-by-SHA fallback in orchestrator — stale worktree branches no longer left behind (b9da3b7)

## [1.5.1] - 2026-04-03

### Fixed
- Background agents no longer hang on invisible Write permission prompts — all background agents now use `bypassPermissions` mode
- Architect agent in esdd-propose receives pre-collected codebase context instead of re-scanning, avoiding redundant file reads

## 1.5.0

### Added
- Post-mortem section in apply/apply-all reports for tracking errors and interventions
- Safe tasks.md commit workflow to prevent staging unrelated files during worktree merges
- Worktree isolation guardrail: block main-branch agents while worktrees are alive
- Verify-after-enabling rule for config/flag tasks in esdd-apply

### Changed
- Merge Phase 2 (review+security) and Phase 3 (QA) into a single parallel Phase 2 for faster execution
- Fix agents now dispatch in parallel grouped by responsible agent type
- Pre-lint runs in background during orchestrator preparation instead of blocking
- Config files cached once per batch in apply-all instead of re-reading per change
- Design and specs generate in parallel during esdd-propose with cross-validation after
- Incremental E2E reruns on retry rounds to save time on large test suites

### Removed
- prompt-audit skill (moved to local user commands)

## 1.4.0

### Added
- `systematic-debugging` skill — 4-phase root cause investigation with tracing, defense-in-depth, and condition-based waiting techniques (from obra/superpowers)
- `test-driven-development` skill — TDD iron law with rationalization countermeasures and testing anti-patterns reference (from obra/superpowers)
- `verification-before-completion` skill — evidence-before-claims gate for all completion assertions (from obra/superpowers)
- `owasp-security` skill — OWASP Top 10:2025, ASVS 5.0, Agentic AI security risks 2026, and language-specific patterns for 20+ languages (from agamm/claude-code-owasp)
- `skill-authoring-guidelines` skill — CSO (Claude Search Optimization) rules for writing effective skill descriptions
- `check-cso.sh` script to detect description quality issues after upstream sync

### Changed
- `esdd-propose` now proposes 2-3 implementation approaches with trade-offs before design generation
- `esdd-propose` validation adds semantic self-review: placeholder scan (13 patterns), type/name consistency, scope creep detection
- Orchestrator handles agent result statuses (DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED)
- Orchestrator provides git SHA diff range to reviewers for precise scope
- Orchestrator fix agents verify suggestions before implementing, can push back with technical reasoning
- `security-engineer` references `owasp-security` as mandatory review baseline
- Fix 6 skill descriptions for CSO compliance (accessibility, create-adaptable-composable, devops-engineer, differential-review, electron-dev, playwright)

## 1.3.0

- Add `python-engineer` agent for FastAPI, data pipelines, ML models, LLM integration, and monitoring
- Register `(Python)` tag in orchestrator, esdd-propose, and esdd-quick dispatch mappings

## 1.2.2

- Prompt audit now checks reference files are properly split and all reference paths are valid

## 1.2.1

- Trim `conventional-commits` skill to essential rules (520 → 66 lines)
- Replace all `git-commit-helper` references with `conventional-commits` skill path
- Plugin no longer depends on external `plugins/git/` for commit formatting

## 1.2.0

- Each task group now produces a single, clean reviewable commit instead of mixed-concern squashes
- Groups support dependency declarations for safe parallel execution
- Commit consolidation no longer relies on rebase, preventing change loss
- Streamlined agent checklists
