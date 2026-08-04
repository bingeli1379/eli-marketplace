# Detection Rules

Auto-detection logic for Phase 1 of `/setup`. Load this file when SCAN reaches the auto-detect stage. Everything here feeds `feature-spec/config.yaml` — nothing else is generated.

---

## 1. Auto-detect tech stack

Read these files if they exist and synthesize a **one-line** `tech_stack` string:

- `package.json` → frontend framework, dependencies, node version, scripts
- `*.csproj` / `*.sln` / `global.json` → .NET version, target framework
- `tsconfig.json` → TypeScript config (strict mode, paths)
- `nuxt.config.ts` / `vite.config.ts` / `next.config.*` → build tool, framework
- `tailwind.config.*` / `unocss.config.*` → CSS framework
- `docker-compose.yml` / `Dockerfile` → containerization
- `go.mod` / `Cargo.toml` / `pyproject.toml` / `requirements.txt` → other languages
- `project.godot` → Godot game project. Read `config/features` for the engine version (e.g. `"4.6"`) and renderer (`Forward Plus` / `Mobile` / `GL Compatibility`). Language track = GDScript by default; **C# (Mono/.NET) only if a `.csproj` / `.cs` files are present**. Note both when mixed.
- Lock files → package manager (pnpm/npm/yarn)

`tech_stack` is the **single source of truth** for versions. Do not repeat version numbers anywhere else in `config.yaml`.

---

## 2. Auto-detect lint and verification commands

**Lint commands** — build the list using **fix mode** (`--fix`, `--write`):
- Check `package.json` scripts for `lint`, `lint:fix`, `format`, `stylelint`
- Check config files: `eslint.config.*`, `.eslintrc*`, `.prettierrc*`, `.stylelintrc*`
- Check `.csproj` / `.sln` → `dotnet format`
- Godot (`project.godot` present): **gdtoolkit** if configured — `gdformat` (format), `gdlint` (lint). Look for `.pre-commit-config.yaml` referencing Scony/godot-gdscript-toolkit, a `.gdlintrc`, or `[tool.gdtoolkit]` in `pyproject.toml`. Leave empty if not configured (Godot ships no first-party formatter).
- Use the project's package manager based on lock file
- **Before generating**, check `${CLAUDE_PLUGIN_ROOT}/company-conventions.md` for pre-lint skip rules. Skip matching tooling.

**Verification commands** — use the **exact script name** from `package.json`:
- `type-check` / `typecheck` / `tsc`
- `test` / `test:unit` / `test:e2e`
- `build`
- For .NET: `dotnet build`, `dotnet test`
- For Godot (`project.godot` present): import/parse check `<godot-bin> --headless --import` (the universal baseline — catches parse and import errors); tests via the repo's runner — gdUnit4 (`addons/gdUnit4/runtest.sh` / `.cmd`), GUT (`<godot-bin> --headless -s addons/gut/gut_cmdln.gd`), or a custom `tools/*runner*`. C# track adds `<godot-bin> --headless --build-solutions` and/or `dotnet test`. The Godot binary path is machine-specific — record the command shape and let the project override the binary.
- **CRITICAL**: never hardcode tool flags (e.g., `vue-tsc --noEmit`) — different projects configure tools differently.

---

## 3. Auto-detect architecture baseline

Draft the four `architecture` fields that go into `config.yaml`. Keep everything **pointer-form** — `name → path`, never file lists.

- **pattern** — infer from top-level folder names:
  - `src/Domain/`, `src/Application/`, `src/Infrastructure/`, `src/Api/` → Clean Architecture
  - `pages/`, `composables/`, `components/`, `server/` → Nuxt / Vue
  - `controllers/`, `models/`, `views/` → MVC
  - `project.godot` present → "Godot scene/node composition". Note the layout variant: **feature-folder** (assets co-located with scenes, the official recommendation) vs **type-split** (`scenes/ scripts/ assets/ data/`). Flag autoload-centric global state if `project.godot` has an `[autoload]` block.
  - Combine front/back when both present (e.g. "Clean Architecture (backend) + Atomic Design (frontend)").
- **layers** — the architectural folders that define the pattern, as `name → path` pointers (e.g. `domain → src/Domain/`). Do not enumerate files inside them.
- **entry_points** — scan **all** conventional locations and list each that exists as `kind → path`. Missing one silently breaks AI's ability to add features there:
  - HTTP API: `src/**/Endpoints/`, `src/**/Controllers/`, `server/api/`, `server/routes/`
  - Frontend pages: `pages/**/*.vue`, `app/pages/`, `app/routes/`, `src/views/`
  - Middleware: `middleware/`, `server/middleware/`
  - Plugins / modules: `plugins/`, `modules/`, `src/Modules/`
  - Background jobs: `src/**/Jobs/`, `src/**/Workers/`, `worker/`
  - Event handlers: `src/**/EventHandlers/`, `src/**/Handlers/`
  - CLI / scripts: `bin/`, `scripts/`, `src/Cli/`
  - Godot: main scene (`project.godot` `run/main_scene`), autoloads (`project.godot` `[autoload]` → each global script — the cross-scene entry points), scenes (`scenes/` or feature folders' `*.tscn`), input actions (`project.godot` `[input]`)
- **hard_rules** — read existing `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`, `.github/copilot-instructions.md`, `eslint.config.*` / `.eslintrc*`, `.editorconfig`; extract imperative rules and **classify each** (below). Also infer **data-access / query conventions** from the code when the evidence is consistent across the codebase — these are exactly the invariants engineers must not break and that a code scan alone may not make obvious. Capture them as hard_rules when a quick grep confirms the pattern is followed everywhere, e.g.:
  - data access always goes through stored procedures / a repository layer, never inline SQL or a direct `DbContext` in endpoints
  - read queries use a specific convention (a locking hint like `NOLOCK`, a shared query helper, a standard pagination shape)
  - a specific result/error type is always returned instead of throwing

  Only record one when the codebase actually follows it consistently (grep shows ~no counter-examples). A convention with mixed adherence is not a hard_rule — leave it for per-task precedent-mirroring instead.

  **A rule asserting an absence ("never X", "no X anywhere") MUST be established from the positive side.** Enumerate the actual data-access call sites and read what each one does; never conclude an absence from a negative grep of framework-specific markers. Micro-ORMs and in-house DAL wrappers call stored procedures by **bare name string** — `QueryAsync("[dbo].[Foo_25.01.02]", …)` — with no `CommandType.StoredProcedure`, no `EXEC`, no `sp_` prefix, so a grep for those comes back clean on a codebase built entirely on stored procedures. The same trap applies to raw SQL behind a query-builder and to context access behind a helper. A wrong `hard_rule` is worse than a missing one: `/propose` forwards it to the architect as non-negotiable, so it actively steers the design wrong and the error is only caught (if at all) after a design already depends on it.

  Where two mechanisms coexist — e.g. EF Core for one database, Dapper + stored procedures for another — record the **split and the axis it divides on**, not one blanket rule.

  Classification of every candidate:
  - **Structural** (true a year from now, layer/dependency invariants) → keep in `hard_rules`.
  - **Historical** (version-pinned migration leftovers, "do not use the old X", upgrade recipes) → **drop**. These age out; the project's own docs can carry them if it cares.
  - **Lint-enforceable** (anything an existing ESLint / dotnet-format / Ruff / Stylelint config already enforces — naming conventions, import order, `consistent-type-imports`, etc.) → **drop**. `hard_rules` is for invariants linters cannot express (layer boundaries, allowed call directions, cross-component contracts).
  - Smell test: if the rule could become wrong after a refactor or version bump, it is historical — drop it.

Everything else the old context.md used to capture (mission, domain map, glossary, cross-cutting concerns, common commands) is **out of scope**. `config.yaml` is a stable architecture floor, not a full project map — it is the only project context downstream agents get, so keep it accurate but do not try to make it exhaustive.

---

## Confidence tagging

For each architecture field, classify confidence. The classification is deterministic — pick the row whose condition matches first.

| Tag | Meaning | User experience |
|---|---|---|
| ✅ **High** | Direct evidence in the codebase / manifest / config (no inference) | Show in SCAN report. **Never ask**. |
| ⚠️ **Medium** | Inferred from indirect signals; reasonably confident but not certain | Show in SCAN report. **Do not ask** — user edits config.yaml by hand if off. |
| ○ **N/A** | The field's signal class is **inapplicable to this repo type** (e.g. layers on a docs-only repo) | Show as `○`. **Never ask**. Field is left empty in config.yaml. |
| ❌ **Low** | The signal class applies but AI cannot infer at all (should exist but missing) | Show in SCAN report **and** trigger a gap-filling question (capped at 3 total). |

Key principle: the only thing that triggers a question is a **signal that should exist but is missing**. A wrong guess is fixed by editing config.yaml, not by interrupting the user. A signal class that genuinely does not apply is a confident `○`, not a gap.

### Repo-type pre-classification (run BEFORE per-field rules)

| Repo type | Signal | Effect |
|---|---|---|
| **Code-bearing repo** | At least one tracked file whose extension is NOT in the doc-or-config allowlist (`.md` / `.adoc` / `.rst` / `.txt` / `.yaml` / `.yml` / `.json` / `.toml` / `.ini` / `.lock` / `.gitignore` / `.editorconfig`). | Tech stack / Lint / Verification / Entry points use the per-field rules unchanged. |
| **Config-only repo** | All tracked files match the allowlist AND at least one is `.json` / `.yaml` / `.yml` / `.toml`. | Tech stack / Lint / Verification → force ○. Entry points → run the "non-standard entry kinds" check below before falling through. |
| **Docs-only repo** | All tracked files match the allowlist AND no machine-readable config is present. | Tech stack / Lint / Verification / Entry points → force ○. |

**Non-standard entry kinds** (Entry points): when the conventional locations all miss but the repo has its own entry convention, list those instead and mark ✅ High. Examples:

- Claude Code plugin / marketplace repo: `commands/` / `skills/` / `agents/` / `hooks/` under each plugin
- VS Code extension: `package.json` `contributes.*` (commands / views / menus)
- GitHub Actions repo: `action.yml` files

### Per-field confidence rules (deterministic — first match wins)

| Field | ✅ High when | ⚠️ Medium when | ❌ Low when |
|---|---|---|---|
| Tech stack | Manifest files parse cleanly | Manifest exists but non-standard / sparse | No manifest but repo is **code-bearing** → ❌ Low. Config-only / docs-only → force ○. |
| Lint commands | `package.json` has `lint`/`lint:fix` OR `dotnet format` applicable OR config files present | One config file exists but no script wired up | Code-bearing repo with no lint setup → ❌ Low. Config-only / docs-only → force ○. |
| Verification commands | Standard `type-check` / `test` / `build` scripts OR `*.csproj` present | Non-standard script names implying verification ("ci", "check") | Code-bearing repo with no buildable/testable manifest → ❌ Low. Config-only / docs-only → force ○. |
| Pattern | Top-level folders match a known pattern (Clean / Nuxt / MVC) | Folder structure exists but matches no known pattern — describe literally | Single dir or no `src/` / `app/` |
| Layers | ≥2 architectural folders matching the detected pattern | folders exist but ambiguous mapping | No `src/` / `app/`, or single dir |
| Entry points | ≥1 conventional location resolves, OR a non-standard entry kind matches | Some locations resolve but unconventional naming | Code-bearing repo with no resolvable entry locations and no non-standard kind → ❌ Low. Docs-only → force ○. |
| Hard rules | `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/` exists with extractable structural rules | `eslint.config.*` has team rules but no human-written project rules | None of those files exist → render as empty (not a question unless the user wants to add one) |

**Special cases**:
- A field can be ✅ High even when empty if the empty result is confidently observed (e.g. `hard_rules: []` after finding no rules files — that is a certain negative, not ❌ Low).
- **Inapplicable signal class → ○ not ❌**: tech stack / lint / verification / entry points on a config-only or docs-only repo are confidently inapplicable. Force ○ via the pre-classification; leave the field empty in config.yaml.
