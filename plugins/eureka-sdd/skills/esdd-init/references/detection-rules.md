# Detection Rules

Detailed auto-detection logic for Phase 1 steps 1–3 of `/esdd-init`. Load this file when SCAN reaches the auto-detect stage.

---

## 1. Auto-detect tech stack

Read these files if they exist:

- `package.json` → frontend framework, dependencies, node version, scripts
- `*.csproj` / `*.sln` / `global.json` → .NET version, target framework
- `tsconfig.json` → TypeScript config (strict mode, paths)
- `nuxt.config.ts` / `vite.config.ts` / `next.config.*` → build tool, framework
- `tailwind.config.*` / `unocss.config.*` → CSS framework
- `docker-compose.yml` / `Dockerfile` → containerization
- `go.mod` / `Cargo.toml` / `pyproject.toml` / `requirements.txt` → other languages
- Lock files → package manager (pnpm/npm/yarn)

---

## 2. Auto-detect lint and verification commands

**Lint commands** — build the list using **fix mode** (`--fix`, `--write`):
- Check `package.json` scripts for `lint`, `lint:fix`, `format`, `stylelint`
- Check config files: `eslint.config.*`, `.eslintrc*`, `.prettierrc*`, `.stylelintrc*`
- Check `.csproj` / `.sln` → `dotnet format`
- Use the project's package manager based on lock file
- **Before generating**, check `company-conventions.md` (in the plugin root) for pre-lint skip rules. Skip matching tooling.

**Verification commands** — use the **exact script name** from `package.json`:
- `type-check` / `typecheck` / `tsc`
- `test` / `test:unit` / `test:e2e`
- `build`
- For .NET: `dotnet build`, `dotnet test`
- **CRITICAL**: never hardcode tool flags (e.g., `vue-tsc --noEmit`) — different projects configure tools differently.

---

## 3. Auto-detect context.md content

For each section in `templates/context.md`, draft the best AI inference:

- **Mission** — read `README.md` first paragraph(s); fall back to project name + dependencies. Strip any version numbers — versions only live in Tech Stack.
- **Tech Stack & Versions** — from manifest files (above). This is the **single source of truth** for versions; downstream sections must not duplicate them.
- **Architecture Layers** — infer from top-level folder names (`src/Domain/`, `src/Application/` → Clean Architecture; `pages/`, `composables/`, `components/` → Nuxt; `controllers/`, `models/`, `views/` → MVC).
- **Domain-to-Code Map** — list direct subfolders of `src/`, `app/`, or domain roots. **Use pointer form**, not enumeration: `Domain | path/ | aggregate root + N items under this path`. Never expand the full file list — it rots whenever a file is added or renamed.
- **Entry Points** — scan **all** of these conventional locations and list each one that exists. Missing one silently breaks AI's ability to add features in that area:
  - HTTP API: `src/**/Endpoints/`, `src/**/Controllers/`, `server/api/`, `server/routes/`
  - Frontend pages: `pages/**/*.vue`, `app/pages/`, `app/routes/`, `src/views/`
  - Middleware: `middleware/`, `server/middleware/`
  - Plugins / modules: `plugins/`, `modules/`, `src/Modules/`
  - Background jobs: `src/**/Jobs/`, `src/**/Workers/`, `worker/`
  - Event handlers: `src/**/EventHandlers/`, `src/**/Handlers/`
  - CLI / scripts: `bin/`, `scripts/`, `src/Cli/`
- **Conditional Subsystems** — only draft if the codebase contains clear conditional activation patterns (request-header branching like `request.headers['x-render-props']`, feature-flag checks, route-prefix routing). Each entry must state the **trigger condition** (header / flag / path / env), not just the behavior. Omit the section entirely if no such subsystems exist.
- **Cross-cutting Concerns** — detect known patterns: `Middlewares/`, `Filters/`, `composables/useApi*`, `composables/useRwd*` / `composables/useBreakpoint*` / `composables/useMedia*` (responsive design / mobile detection — easy to miss but always cross-cutting in a Nuxt or Vue app), `composables/useI18n*` / `i18n.config.*`, `Serilog`, `HybridCache`, `[Authorize]`. If you find more than ~5 high-frequency concerns, split the heavy ones (e.g., Caching, i18n, Datetime, Responsive) into their own H2 sections and leave only the long tail under Cross-cutting Concerns.
- **Hard Rules** — read existing `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`, `.github/copilot-instructions.md`, `eslint.config.*` / `.eslintrc*` (custom rules that encode team conventions), `.editorconfig` if present; extract imperative rules. **Classify each candidate**:
  - **Structural** (true a year from now, layer/dependency invariants) → keep in Hard Rules.
  - **Historical** (version-pinned migration leftovers, "do not use the old X", upgrade recipes) → not in Hard Rules. Forwarded to `knowledge-seed.md` for the **named-symbol gate** (only kept as a knowledge candidate when the rule names a code symbol that still resolves in the codebase; otherwise silently dropped as aged-out).
  - **Lint-enforceable** (anything an existing ESLint / dotnet-format / Ruff / Stylelint config already enforces — `consistent-type-imports`, `prefer-interface-over-type-for-object`, naming conventions, import order, etc.) → drop. Hard Rules is for invariants linters cannot express (layer boundaries, allowed call directions, cross-component contracts). Point to the lint config from Cross-cutting Concerns instead.
  - Smell test: if the rule could become wrong after a refactor or version bump, it is historical.
- **Anti-patterns** — do not auto-detect. Leave the section omitted unless the user explicitly contributes examples — empty Anti-patterns stubs add noise.
- **Glossary** — only draft if domain folders look complex (>3 distinct domains) AND a `docs/` or `README.md` defines terms; otherwise mark for omission. When drafting, split into:
  - **Code Terms**: identifiers visible in the codebase (folder names, recurring class/component prefixes). Auto-detectable from folder/file names.
  - **Business Terms**: domain abbreviations not visible in code. Must be asked from the user (or sourced from `docs/`).
  - **Disjoint rule (hard)**: a single term must appear in **exactly one** of the two subsections — never both. Domain abbreviations (`DLH`, `PPC`, `KYC`, `SLA`, `CMS`, etc.) always go to Business Terms even if they happen to appear in code (e.g., a folder named `dlh/`). Reserve Code Terms for codebase-only nouns whose meaning is mechanical (`Section`, `Island mode`, `B2CContext`, framework prefix names). Before writing, dedupe across the two lists and move duplicates to Business Terms.
- **Common Commands** — from `package.json` scripts, `Makefile` targets, project README.

---

## Confidence tagging

For each section, classify confidence using the per-section table below. The classification is deterministic — pick the row whose condition matches first.

| Tag | Meaning | User experience |
|---|---|---|
| ✅ **High** | Direct evidence in the codebase / manifest / config (no inference) | Show in SCAN report. **Never ask** the user. |
| ⚠️ **Medium** | Inferred from indirect signals; AI is reasonably confident but not certain | Show in SCAN report. **Do not ask** — user can edit the file by hand if the draft is off. |
| ○ **N/A** | The section's signal class is **inapplicable to this repo type** (e.g. tech stack on a markdown-only config repo) | Show as `○` in SCAN report. **Never ask**. The section is dropped from `context.md`. |
| ❌ **Low** | The signal class is applicable but AI cannot infer at all (signal *should* exist but is missing) | Show in SCAN report **and** trigger a gap-filling question (capped at 3 total per init). |

Key principle: the only thing that triggers a question is a **signal that should exist but is missing**. If AI took a guess that turned out to be wrong, the user fixes it by editing — not by being interrupted. If a signal class genuinely does not apply to this repo, that is a confident negative answer (`○`), not a knowledge gap.

### Repo-type pre-classification (run BEFORE per-section rules)

Some signal classes are inapplicable to entire repo categories. Detect the repo type up front so per-section classification can downgrade ❌ Low → ○ where appropriate.

| Repo type | Signal | Effect |
|---|---|---|
| **Code-bearing repo** | The repo contains **at least one tracked file whose extension is NOT in the doc-or-config allowlist** (`.md` / `.adoc` / `.rst` / `.txt` / `.yaml` / `.yml` / `.json` / `.toml` / `.ini` / `.lock` / `.gitignore` / `.editorconfig`). The negative-space test is intentional — it stays correct as new languages appear. | Tech stack / Lint / Verification / Entry points use the per-section rules unchanged. |
| **Config-only repo** | All tracked files match the doc-or-config allowlist AND at least one is `.json` / `.yaml` / `.yml` / `.toml` (i.e. there is something machine-readable beyond docs). | Tech stack / Lint / Verification → force ○. Entry points → run the special "non-standard entry kinds" check (see below) before falling through. |
| **Docs-only repo** | All tracked files match the doc-or-config allowlist AND no machine-readable config is present (only `.md` / `.adoc` / `.rst` / `.txt`). | Tech stack / Lint / Verification / Entry points → force ○. |

**Non-standard entry kinds** (Entry points): when the conventional locations (HTTP/pages/middleware/etc.) all miss but the repo has its own entry convention, list those instead and mark ✅ High. Examples:

- Claude Code plugin / marketplace repo: `commands/` / `skills/` / `agents/` / `hooks/` under each plugin
- VS Code extension: `package.json` `contributes.*` (commands / views / menus)
- GitHub Actions repo: `action.yml` files

Detect by scanning for these patterns; if found, the section is **not** Low — it is High with a custom-shape entry list. Document the kind in `context.md` Entry Points so downstream agents understand the convention.

### Per-section confidence rules (deterministic — first match wins)

| Section | ✅ High when | ⚠️ Medium when | ❌ Low when |
|---|---|---|---|
| Mission | `README.md` first paragraph clearly describes the project (subject + verb + what for whom) | `README.md` exists but is meta-only / list-of-features / minimal — AI synthesizes from `package.json` name + deps | No `README.md`, or README has zero descriptive text |
| Tech stack | Manifest files (`package.json` / `*.csproj` / `pyproject.toml` / `go.mod` / `Cargo.toml`) parse cleanly | Manifest exists but is non-standard or sparse (e.g. only a `package.json` with no deps yet) | No manifest files but repo is **code-bearing** per the pre-classification (signal should exist but missing) → ❌ Low. **Config-only / docs-only repo** → force ○. |
| Lint commands | `package.json` has `lint` / `lint:fix` script(s) OR `dotnet format` is applicable (`*.csproj` exists) OR config files (`eslint.config.*`, `.prettierrc*`) present | One config file exists but no script wired up — AI guesses the invocation | Code-bearing repo with no lint setup → ❌ Low. **Config-only / docs-only repo** → force ○. |
| Verification commands | `package.json` has standard `type-check` / `test` / `build` scripts OR `*.csproj` exists (use `dotnet build`/`test`) | Non-standard script names that imply verification ("ci", "check") — AI maps them | Code-bearing repo with no buildable / testable manifest → ❌ Low. **Config-only / docs-only repo** → force ○. |
| Architecture layers | Top-level folder names match a known pattern (Clean Architecture: `Domain/Application/Infrastructure/Api`; Nuxt: `pages/composables/components/server`; MVC: `controllers/models/views`) | Folder structure exists but does not match a known pattern — AI describes literally | Single dir or no `src/` / `app/` |
| Domain map | ≥2 named subdirs under `src/` / `app/` / `server/` that look like domain boundaries (not framework folders) | 1 subdir, or all subdirs are framework-named (`controllers/services/` only) — AI labels what it sees | No `src/` / `app/`, or only single dir |
| Entry points | At least one of the conventional locations (HTTP / pages / middleware / etc.) resolves on disk, **OR** a non-standard entry kind matches (per the pre-classification table — plugin marketplace / VS Code extension / GitHub Action) | Some locations resolve but unconventional naming — AI lists what it found | Code-bearing repo with no resolvable entry locations and no non-standard kind matched → ❌ Low. **Docs-only repo** → force ○. |
| Conditional subsystems | grep finds clear branching pattern (`request.headers['x-render-props']`, feature flag check, route prefix) | Hints of branching but trigger condition unclear | No branching pattern found → render as `none detected` (this is ✅ ○-equivalent — `none` is a valid certain answer, no question needed) |
| Cross-cutting concerns | ≥1 known pattern detected (Middlewares/Filters, `useApi*`, `Serilog`, `[Authorize]`) | Concerns exist but unconventional locations | None detected |
| Hard rules | `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/` exists with extractable structural rules | `eslint.config.*` has team-specific rules but no human-written project rules | None of the above files exist at all |
| Glossary | `docs/` defines terms OR ≥3 distinct domain folders with non-mechanical names (need user-supplied business terms) | Project has domain folders but no `docs/` — Code Terms detectable; Business Terms unknown | No domain complexity → render as `omitted (no docs/, no obvious domain abbrevs)` |
| Common commands | `package.json` scripts / `Makefile` targets / README has a "## Commands" section | Some scripts exist but standard-only (dev/test/build) — list them | No scripts file exists |
| Anti-patterns | (always omitted unless the user explicitly contributes; no auto-detection) | — | — (do not classify; just omit) |

**Special cases**:

- **Conditional Subsystems / Glossary "omitted" outcomes are NOT ❌ Low** — they are certain *negative* answers (we know there are none). Render in the SCAN report as `○` (not applicable) and never ask. ❌ Low is reserved for "AI does not know whether there are any".
- A section can be marked ✅ High even when its content is empty, if the empty result is itself confidently observed (e.g. `Conditional subsystems: none detected` after a clean grep pass).
- **Inapplicable signal class → ○ not ❌**: tech stack / lint / verification / entry points on a config-only or docs-only repo are confidently inapplicable, not unknown. Always force ○ via the repo-type pre-classification. The section is dropped from `context.md` (`templates/context.md` already supports omitting any section).
