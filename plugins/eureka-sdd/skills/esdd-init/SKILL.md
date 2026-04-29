---
name: esdd-init
description: >
  Initialize feature-spec directory structure and auto-generate config.yaml +
  context.md with project context. Two-phase: SCAN (dry-run + confirm) then
  BUILD (write files). Use when setting up a new project for the eureka-sdd,
  or when the user wants to reconfigure project context.
user-invocable: true
---

Initialize the `feature-spec/` directory in the current project. Auto-generates up to three artifacts:

- `feature-spec/config.yaml` — tool-runnable config (lint/verification commands, rules)
- `feature-spec/context.md` — AI-readable project context (architecture layers, domain map, entry points, conditional subsystems, hard rules, anti-patterns, glossary, common commands) so AI knows **where to make changes**
- `feature-spec/knowledge.md` — annotated skeleton with per-section guidance comments (Domain / Dev Environment / Gotchas / External Dependencies, hinting at high-value subtypes such as upstream quirks, cache keys, fallback modes, mock-vs-real gaps), same canonical skeleton used by `/esdd-complete`. Created when missing. **When an existing file with real entries is detected, an inline audit pass re-verifies every entry's `path:line` citation against the current codebase (resolve / snippet match / counter-example grep) and surfaces stale / outdated / uncited entries for user decision in the SCAN report — existing entries are never auto-deleted.** Confirmed seed candidates (operational tribal knowledge harvested from `.env.example`, READMEs, package scripts, informational code comments, historical rules) are appended in place, deduped against surviving audited entries — only the entries the user explicitly selected from the SCAN-time batch question land in the file. Lives next to `context.md` so all spec-related files sit in one place.

Runs in two phases: **SCAN** (analyze + confirm) then **BUILD** (write files).

---

**Input**: No arguments required.

---

## Phase 0 — Pre-flight

1. **Check existing state**

   - If `feature-spec/` does not exist → proceed to SCAN, will create everything.
   - If `feature-spec/` exists, inventory each artifact:
     - `config.yaml` present? `context.md` present? `knowledge.md` present? subdirectories `specs/` and `changes/`?
   - For each existing artifact, use **AskUserQuestion** to choose:
     - "Regenerate (overwrite)" — re-detect and rewrite
     - "Keep existing" — skip in BUILD phase
   - **`knowledge.md` special case**: regardless of "keep" vs "regenerate", if the file exists with real entries (more than skeleton + HTML comments), Phase 1 step 4.5 runs an inline audit and surfaces findings in the SCAN report. "Regenerate" still wipes the file at BUILD time; "Keep existing" preserves the file but lets the user act on audit findings via the audit-decision batch question.
   - Always ensure missing subdirectories (`specs/`, `changes/`) get created.

   ```bash
   mkdir -p feature-spec/specs feature-spec/changes
   ```

2. **Migrate legacy `knowledge.md` from project root (silent, one-time)**

   Earlier versions of this plugin wrote `knowledge.md` to the project root. The current location is `feature-spec/knowledge.md`. Migrate without asking:

   - If `./knowledge.md` exists AND `feature-spec/knowledge.md` does NOT exist → run `git mv knowledge.md feature-spec/knowledge.md` (preserves history). Fall back to `mv` if the file is untracked. Announce in the conversation: `Moved knowledge.md → feature-spec/knowledge.md (legacy location migration)`.
   - If both `./knowledge.md` AND `feature-spec/knowledge.md` exist → leave both alone, do NOT auto-merge or auto-delete. Surface a one-line warning in the BUILD summary: `⚠️ ./knowledge.md and feature-spec/knowledge.md both exist — please reconcile manually.`
   - If only `feature-spec/knowledge.md` exists → no action.
   - If neither exists → no action; the BUILD phase may create `feature-spec/knowledge.md` if seeded.

   Migration is silent because the move is reversible and content is preserved — there is no decision worth interrupting the user for.

---

## Phase 1 — SCAN (dry-run, no files written)

Goal: gather everything that can be auto-detected, then ask the user to confirm or fill gaps. **Do not write any files in this phase.**

### 1. Auto-detect tech stack

Read these files if they exist:

- `package.json` → frontend framework, dependencies, node version, scripts
- `*.csproj` / `*.sln` / `global.json` → .NET version, target framework
- `tsconfig.json` → TypeScript config (strict mode, paths)
- `nuxt.config.ts` / `vite.config.ts` / `next.config.*` → build tool, framework
- `tailwind.config.*` / `unocss.config.*` → CSS framework
- `docker-compose.yml` / `Dockerfile` → containerization
- `go.mod` / `Cargo.toml` / `pyproject.toml` / `requirements.txt` → other languages
- Lock files → package manager (pnpm/npm/yarn)

### 2. Auto-detect lint and verification commands

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

### 3. Auto-detect context.md content

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
  - **Historical** (version-pinned migration leftovers, "do not use the old X", upgrade recipes) → drop here; they get folded into "Knowledge seed candidates" (step 4) and, if the user approves them in the batch selection, end up in `knowledge.md`'s Gotchas section instead of `context.md`.
  - **Lint-enforceable** (anything an existing ESLint / dotnet-format / Ruff / Stylelint config already enforces — `consistent-type-imports`, `prefer-interface-over-type-for-object`, naming conventions, import order, etc.) → drop. Hard Rules is for invariants linters cannot express (layer boundaries, allowed call directions, cross-component contracts). Point to the lint config from Cross-cutting Concerns instead.
  - Smell test: if the rule could become wrong after a refactor or version bump, it is historical.
- **Anti-patterns** — do not auto-detect. Leave the section omitted unless the user explicitly contributes examples — empty Anti-patterns stubs add noise.
- **Glossary** — only draft if domain folders look complex (>3 distinct domains) AND a `docs/` or `README.md` defines terms; otherwise mark for omission. When drafting, split into:
  - **Code Terms**: identifiers visible in the codebase (folder names, recurring class/component prefixes). Auto-detectable from folder/file names.
  - **Business Terms**: domain abbreviations not visible in code. Must be asked from the user (or sourced from `docs/`).
  - **Disjoint rule (hard)**: a single term must appear in **exactly one** of the two subsections — never both. Domain abbreviations (`DLH`, `PPC`, `KYC`, `SLA`, `CMS`, etc.) always go to Business Terms even if they happen to appear in code (e.g., a folder named `dlh/`). Reserve Code Terms for codebase-only nouns whose meaning is mechanical (`Section`, `Island mode`, `B2CContext`, framework prefix names). Before writing, dedupe across the two lists and move duplicates to Business Terms.
- **Common Commands** — from `package.json` scripts, `Makefile` targets, project README.

**Confidence tagging** — for each section, classify confidence:
- ✅ **High** (>80%): confidently auto-detected, no question needed
- ⚠️  **Medium** (40-80%): show draft, ask "looks right?"
- ❌ **Low** (<40%): cannot infer, must ask user

### 4. Auto-detect knowledge.md seed candidates (file scan only — no git mining)

Goal: harvest the project's existing operational tribal knowledge that is already documented somewhere — env hints, "how to do X" tips, deps quirks, informational code comments — so a fresh project does not start with an empty `knowledge.md`. Surviving candidates are surfaced inline in the SCAN report (step 5) for **interactive batch confirmation** before any write to `knowledge.md`. AI never writes a candidate without explicit user approval — behavioral claims are easy to get wrong from naming alone.

**Sources to scan**:

| Source | What to extract | Target category |
|---|---|---|
| `.env.example` / `.env.sample` / `.env.template` | env vars whose names are non-obvious OR have inline comments explaining purpose / toggling behavior | Dev Environment |
| `README.md`, `CONTRIBUTING.md`, `docs/**.md` | "How to", "Tip", "Note", "Troubleshooting" subsections that describe operational shortcuts | Dev Environment |
| `package.json` scripts | non-standard script names (anything beyond dev/test/build/lint/typecheck) where the name implies an operational purpose | Dev Environment |
| Existing CLAUDE.md / AGENTS.md historical rules | rules classified as historical in step 3 (Hard Rules) — version-pinned, migration leftovers, "do not use old X" | Gotchas |
| Code comments matching informational patterns | `// triggered when …`, `// see also …`, `// note:`, `// because …`, `// only X when Y`. Skip `HACK` / `FIXME` / `XXX` — those are unresolved TODO markers, not stable knowledge. | Gotchas |
| Third-party deps with known internal replacements | a dep is in `package.json` BUT a project-internal helper covering the same need was detected during Cross-cutting Concerns (e.g., `axios` present alongside an internal `useApi` composable) | External Dependencies |

**Hard requirement — Cite-or-Skip**: every candidate MUST attach `path/file.ext:start-end` line range and a 3–5 line snippet of the cited content. Candidates that cannot be pinned to a specific line range are dropped silently — naming alone is not enough.

**Citations must point to code files, not markdown docs**: valid targets are `.ts` / `.tsx` / `.js` / `.vue` / `.cs` / `.csproj` / `.py` / `.go` / `.rs` / `.sql` / config files (`*.config.ts`, `nuxt.config.ts`, `package.json`, `appsettings.json`, etc.) — anything that represents the **actual behavior**. Citations pointing to other markdown documents (`CLAUDE.md`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `docs/**.md`) are **silently dropped** — they create circular references because `knowledge.md` is meant to capture facts not already living in those docs.

**Special case — historical rules from CLAUDE.md / AGENTS.md**: when reclassifying a historical rule (per the row in the source table above), the candidate's citation must point to the **code location the rule actually constrains**, not the source markdown. Example: a rule "do not import the old `useAuth` composable" needs `composables/useAuth.ts:1` (or wherever the deprecated symbol now lives — even if it points at zero remaining usages, that is the invariant being asserted) — not `CLAUDE.md:42`. If no code anchor can be found (the rule is purely procedural / no longer maps to the codebase), drop the candidate.

**Self-skeptic pass** (run on every candidate before keeping it):

1. Re-read ONLY the cited snippet (do not re-explore).
2. Ask: does the candidate text match what the snippet actually does, not what its identifier suggests?
3. If they mismatch → either rewrite the entry to describe the actual behavior, or drop it. Mark surviving rewrites with `⚠️ Name-vs-impl mismatch:` so the user sees the warning during review.

**Counter-example pass** (cheap grep-based check):

1. Extract the entry's central claim (e.g., "X only triggers when country=MM").
2. Grep the codebase for tokens that could contradict the claim (`country !==`, `country === '`, etc.).
3. If a contradicting branch is found → either narrow the claim to the verified case, or drop it.

**Conservative default**: when in doubt, drop. False knowledge is worse than missing knowledge — `/esdd-complete` will pick up real operational facts as the project moves forward.

### 4.5. Audit existing `knowledge.md` entries (only when file already has real content)

Goal: re-verify each existing entry against the current codebase so the user can keep, rewrite, or drop drifted entries during the same SCAN pass — no separate `/knowledge-audit` round trip needed for the init flow.

**Skip this step entirely** when any of the following is true:
- `feature-spec/knowledge.md` does not exist.
- The file contains only the canonical skeleton (headings + HTML guidance comments + zero real entries).
- The user picked "Regenerate (overwrite)" for `knowledge.md` in Phase 0 (file will be wiped anyway).

**For each existing entry under any category heading**, run this pipeline:

1. **Parse citation** — extract `path/to/file:start-end`. If no citation present → mark `❓ Uncited`, skip remaining steps for this entry.
2. **Resolve file + lines** — check the file path exists and the line range is in bounds. If file missing OR line range out of bounds → mark `❌ Stale (citation broken)`.
3. **Re-read snippet** — read ONLY the cited line range. Do not re-explore.
4. **Self-skeptic check** — does the entry's central claim still match what the snippet actually does (not what an identifier suggests)? If snippet drifted (refactored, behavior moved, condition flipped, file shifted but lines now point at different code) → mark `⚠️ Needs rewrite` and draft a corrected one-line claim that describes the current behavior.
5. **Counter-example grep** — extract the entry's central claim, grep for tokens that could contradict it (`X !==`, `X === '`, alternative branches, feature flags). If a contradicting branch is found and the entry does not already narrow to it → mark `⚠️ Needs rewrite` and draft a narrower claim.
6. **Otherwise** → mark `✅ Still valid`.

**Conservative default**: when uncertain between "still valid" and "needs rewrite", pick `⚠️ Needs rewrite` so the user sees it. When uncertain between "needs rewrite" and "stale", pick `⚠️ Needs rewrite` — never `❌ Stale` unless the citation truly does not resolve. AI never auto-deletes; the user always makes the final call via the audit-decision batch question (step 5).

**Output of step 4.5**: a classified list of every existing entry, with original line, classification, citation status, and (for `⚠️`) the suggested rewrite. This list feeds the SCAN report's "既有 knowledge.md 審計" section in step 5.

**Dedup new candidates against audited entries** (run after step 4.5 finishes, before step 5 renders the report): take the `✅ Still valid` and `⚠️ Needs rewrite` entries from step 4.5 and use them to filter the raw candidate list collected by step 4. Drop any new candidate whose claim semantically overlaps an audited entry (same `path:line` neighborhood + same direction of claim). False duplicates pollute the SCAN report and make the user decide twice on the same fact.

**Phase 1 execution order is therefore**: 1 → 2 → 3 → 4 (collect raw candidates, defer dedup) → 4.5 → dedup pass (filter step 4 output using step 4.5 results) → 5 (render report). Step 4's candidate list is **not** finalized until after dedup runs.

### 5. Present scan report and ask up to 3 confirmation questions

Output the scan report to the conversation:

```
## SCAN Report

### Detected
- Mission: <one-line guess, Medium/Low>
- Tech stack & versions: <summary, High>
- Lint commands: <list, High>
- Verification commands: <list, High>
- Architecture layers: <summary, Medium>
- Domain-to-Code map: <table preview using pointer form, Medium>
- Entry points: <list with all conventional locations checked, High>
- Conditional subsystems: <list / "none detected", Low>
- Cross-cutting concerns: <list, Medium>
- Hard rules (structural): <count, Medium/Low>
- Glossary: <Code Terms count + Business Terms "needs user" / omitted, Low>
- Common commands: <list, High>

### 既有 knowledge.md 審計（僅當步驟 4.5 有跑時顯示）
<Render in Traditional Chinese per the language guardrail. Skip the entire section when step 4.5 was skipped.>

Summary line: `總條目數 N | ✅ 仍有效 X | ⚠️ 建議改寫 Y | ❌ Citation 失效 Z | ❓ 無 citation W`

For every entry classified as ⚠️ / ❌ / ❓, list it with a stable index (the index used here is reused by the audit-decision batch question, so the user can refer to it):

```
A1. [⚠️ 建議改寫] <既有條目原文>
    Citation: `path:line` (resolves)
    Issue: <one-line drift description in Chinese>
    Suggested: <new one-line claim — file content stays in English>
A2. [❌ Citation 失效] <既有條目原文>
    Citation: `path:line` (file missing / lines out of bounds)
A3. [❓ 無 citation] <既有條目原文>
    無 path:line — 請手動審視
```

`✅ 仍有效` 的條目不逐條列出（純綠燈，不需用戶決策），只計入 summary。

### Knowledge seed candidates (numbered, awaiting user selection)
<Combined list of everything that survived Cite-or-Skip + Self-skeptic + Counter-example passes from step 4 (already deduped against ✅/⚠️ existing entries from step 4.5), plus historical rules reclassified from Hard Rules in step 3. Show each candidate as a numbered item with: index (use C-prefix to disambiguate from audit's A-prefix, e.g., `C1`, `C2`), category, one-line claim, `path:line` citation, 3-5 line snippet, and any ⚠️ Name-vs-impl warning. Empty list is fine — write "no seed candidates" and skip the candidate-selection question entirely.>

Format example:
```
C1. [Dev Environment] MSW handlers paginate; real API does not. `mocks/handlers.ts:14-18`
    ```ts
    <snippet>
    ```
C2. [Gotchas] ⚠️ Name-vs-impl mismatch: `validateUser` only null-checks. `src/auth.ts:12-18`
    ```ts
    <snippet>
    ```
```

### Files to be written in BUILD phase
- feature-spec/config.yaml  (new / overwrite / keep)
- feature-spec/context.md   (new / overwrite / keep)
- feature-spec/knowledge.md (new annotated skeleton if missing; existing-entry audit decisions applied in place if step 4.5 ran; confirmed candidates appended afterwards — sits next to context.md)

### Open questions
<2-3 prioritized confirmation questions for low-confidence sections, see below>
```

Use **AskUserQuestion** for at most **3 confirmation questions**, prioritized by impact:

**Priority order** (only ask if the section's confidence is Medium or Low):

1. **Mission** — if README missing or vague, ask:
   "What does this project do, in one sentence? (suggested: <best guess from package name + deps>)"
2. **Domain-to-Code Map** — if folder structure ambiguous, ask:
   "I see these top-level domains: [<list>]. Are any of these missing or wrong?"
3. **Hard Rules** — if no CLAUDE.md/AGENTS.md found, ask:
   "Any architectural rules AI must not break? (e.g., 'Endpoints don't access DbContext directly') — leave blank to skip"

Each question must include:
- A **default suggested answer** based on auto-detection
- An option "Skip / use my draft as-is" so the user can defer

**Cap**: never ask more than 3 confirmation questions. If more gap-filling is needed, write the file and let the user edit by hand later.

**Existing-entry audit decision (separate from the 3-cap, asked only when step 4.5 ran with at least one ⚠️ / ❌ / ❓ finding)**:

Use **AskUserQuestion** with this prompt (render in Traditional Chinese):

> "既有 knowledge.md 審計結果：⚠️ N 條建議改寫、❌ M 條 citation 失效、❓ K 條無 citation。請選擇處理方式：
> - `apply` — 套用所有建議（⚠️ 改寫成新版本、❌ 刪除、❓ 保留不動）
> - `keep-all` — 全部保留原樣，僅在檔案標註 `<!-- audit:YYYY-MM-DD ... -->` 註解供後續手動處理
> - `<indices>` — 用 A-prefix 索引單選需要套用的條目（例：`A1,A3` 或 `A1-A3`），其餘保留原樣
> - `none` — 完全忽略審計結果，檔案內容不動
>
> 預設（未回覆）= `keep-all`（保守，避免誤刪用戶手寫的有效知識）。"

This question is **not** counted against the 3-question cap. Skip the question entirely when step 4.5 was skipped or produced zero ⚠️ / ❌ / ❓ findings.

**Knowledge seed candidate selection (separate from the 3-cap)**: if step 4 produced one or more surviving candidates, ask **one additional batch question** after the audit-decision question:

> "Which knowledge candidates should I keep? Reply with C-prefix indices (e.g., `C1,C3,C5` or `C1-C3,C5`), `all`, or `none`. Default if you do not answer = `none` (false knowledge is worse than missing knowledge)."

This question is mandatory whenever candidates exist and is **not** counted against the 3-question cap — they are different decision categories (gap-filling vs candidate review). Skip the question entirely when zero candidates survived.

---

## Phase 2 — BUILD (write files based on confirmed answers)

### 1. Write `feature-spec/config.yaml`

Read the template at `skills/esdd-init/templates/config.yaml`. Fill in:

- `lint_commands:` — detected lint/format commands (fix mode)
- `verification_commands:` — detected type-check / unit-test / build commands
- `context:` — short pointer string: `See feature-spec/context.md for full project context.` plus a one-line summary (so downstream agents that only read config.yaml still get the gist)
- `rules:` — populate only if project-specific rules detected
- Add header comment: `# Auto-generated by /esdd-init on YYYY-MM-DD`

### 2. Write `feature-spec/context.md`

Read the template at `skills/esdd-init/templates/context.md`. Fill in each section using the SCAN results + confirmed answers:

- Replace placeholder text in each section
- **Drop these optional sections entirely** if not applicable (do not leave empty stubs):
  - **Conditional Subsystems** — drop if SCAN found no header/flag/route-based subsystems
  - **Anti-patterns** — drop unless the user provided concrete examples
  - **Glossary** — drop if SCAN marked it omittable AND the user did not request one
  - **Glossary > Code Terms / Business Terms** — keep only the subsection that has content
- Update header comment date

**Content guidelines**:
- Keep each section tight — bullets and tables, not prose
- **Pointer-over-enumeration is a global rule**: any section that would otherwise list named items (cache groups, server plugins, upstream adapters, route names, component lists, feature toggles) must collapse to `<count> <items> in <path>/` form. Enumerated lists rot the moment a file is added or renamed, and rotted docs are worse than thin docs. **Applies to every section**, not just Domain Map — Cross-cutting Concerns (do not list every cache key), Architecture Layers, Conditional Subsystems, Cross-cutting Concerns sub-bullets, Glossary Code Terms. If you find yourself writing more than ~3 named identifiers separated by commas / slashes, stop and rewrite as a pointer.
- **Domain map**: pointer form only (`Domain | path/ | aggregate root + N items under this path`). NEVER expand the file list.
- **Entry Points**: include every conventional location detected by the Phase 1 checklist, not just the obvious ones. Entry-point inventory is the **one exception** to the pointer rule — listing each entry point by location is the section's purpose. But within each entry-point row, do not enumerate the handlers under it — just point at the directory.
- **Hard Rules**: structural invariants only — one-line imperatives. Historical/migration rules go to the SCAN report's "Knowledge seed candidates" and, if the user approves them in the batch selection, are appended to `knowledge.md`.
- **Versions**: appear ONCE in Tech Stack & Versions. Strip version numbers from every other section before writing.
- **Common Commands**: copy exact script names from `package.json`, do not paraphrase
- **Keep the inline HTML guidance comments** (BAD/GOOD examples, structural-vs-historical hints, etc.) verbatim — they are load-bearing guidance for future AI re-runs and humans editing the file by hand. Only replace the angle-bracket placeholders (`<...>`) and example bullets.

**Self-audit pass before writing context.md** (mandatory — do not skip):

After drafting the full content but **before** writing the file, re-scan the draft for these enumeration smells and rewrite any hit as a pointer:

1. **Comma-list smell** — any line with ≥4 named identifiers separated by `,` / `/` / ` and ` (e.g., `dlh-v2, ppc-v2, seoInfo, ...` or `accessLogger / errorLogger / gzipResponse / applyHeaderFooter / shutdown`). → Replace with `N <items> in <path>/`.
2. **Bullet-explosion smell** — any sub-section with ≥4 bullets each naming one item under the same parent path. → Collapse into one bullet pointing at the parent path with cardinality.
3. **Identifier-suffix smell** — recurring suffix (`*-v2`, `*Logger`, `*Adapter`) listed individually. → Replace with `<N> *-v2 cache groups defined in <file>` or similar.
4. **Version drift smell** — any version-number pattern (`\d+\.\d+`, `v\d+`, `Vue 3.5.x`) outside the Tech Stack & Versions section. → Strip and replace with framework name or "current major".
5. **Cross-doc circularity smell** — any `Hard Rules` entry whose rationale points at `CLAUDE.md` or `AGENTS.md`. → Either it is a structural invariant (drop the cross-ref, the rule stands on its own) or it is historical (move it to the knowledge candidate batch instead).
6. **Half-rotten pointer smell** — any line that combines a pointer (`N <items> in <path>/`, `N subdirs in this path`) with a parenthetical or trailing enumeration (`(banners, games, icon, ...)`, `incl. X / Y / Z`). The count makes the enumeration redundant; the enumeration makes the count rot. Regex hint: `\b\d+\s+\w[\w\s]*\b.*[(—:]\s*\w+(?:\s*[,/]\s*\w+){2,}`. → Strip the parenthetical/trailing list. Pure pointer form only (`8 subdirs in this path.`).

The Editing rules embedded at the top of `context.md` are not just for human readers — AI must enforce them at write time. A draft that violates its own self-described rules is a self-contradicting doc and must be fixed before write.

### 3. Write `feature-spec/knowledge.md` (skeleton if missing, plus confirmed candidates)

**Step 3a — Skeleton**: if `feature-spec/knowledge.md` does not exist, create it by copying the canonical skeleton from `plugins/eureka-sdd/templates/knowledge.md` (single source of truth, shared with `/esdd-complete`). Write it verbatim — do not paraphrase or trim. The skeleton ships with per-section HTML comments that orient new contributors on what belongs where (Domain / Dev Environment / Gotchas / External Dependencies, including hints for high-value subtypes like upstream quirks, cache keys, fallback modes, mock-vs-real gaps). **Preserve these comments verbatim** when appending candidates afterwards.

If `feature-spec/knowledge.md` already exists, leave its existing content alone — only apply audit decisions (step 3a-bis) and append candidates (step 3b) below.

**Step 3a-bis — Apply existing-entry audit decisions** (only when Phase 1 step 4.5 ran AND the user's audit-decision reply is not `none`):

**Reply normalization**: no reply / empty reply → treat as `keep-all` (per the audit-decision question's stated default in Phase 1 step 5). Only the explicit string `none` skips this step entirely.

Translate the user's reply into per-entry actions:

| User reply | Action per ⚠️ / ❌ / ❓ entry |
|---|---|
| `apply` | ⚠️ → replace original line with the AI-suggested rewrite. ❌ → delete the line entirely. ❓ → leave the entry unchanged and insert an HTML comment `<!-- audit YYYY-MM-DD: no citation, please review -->` on the line directly above the entry. |
| `keep-all` (also: no reply / empty reply) | Leave every entry unchanged. Inject a single dated `<!-- audit YYYY-MM-DD: N entries flagged (Y rewrite / Z stale / W uncited), see /esdd-init SCAN report -->` comment at the top of `knowledge.md` so the user can find them later. |
| `<indices>` (e.g., `A1,A3`) | Apply the `apply` action only to the listed entries; the rest stay unchanged. |
| `none` (explicit only) | Skip step 3a-bis entirely. No edits, no audit comment. |

**Editing rules**:
- Operate **in place**: read `knowledge.md`, modify the targeted lines, write back. Never reorder unaffected entries.
- Preserve all category headings and the per-section HTML guidance comments verbatim.
- For ⚠️ rewrites, the new line must follow the same one-line format (`<claim>. <path:line>.`) — if the suggested rewrite spans multiple lines, collapse before writing or downgrade to ❓ behavior.
- For ❌ deletions, do not leave a blank line gap — close up the surrounding entries.
- All injected audit HTML comments are in **English** (per file-content language rule). The comment date must be the actual init run date in ISO format.
- **Audit summary comment is single-instance**: before injecting the `keep-all` summary comment at the top of the file, scan for any existing `<!-- audit YYYY-MM-DD: ... -->` summary comment at the file head and **replace** it (do not stack). Only the latest run's summary should remain. The per-entry `<!-- audit ... no citation -->` comments inserted by `apply` / `<indices>` are positional and accumulate normally — only the head-of-file summary is single-instance.

**Step 3b — Append confirmed candidates**: take the user's reply to the candidate-selection question (Phase 1 step 5) and append the chosen items directly under their respective category headings inside `feature-spec/knowledge.md`. Skip this step entirely if the user replied `none`, did not answer, or no candidates existed.

**Never write a candidate the user did not explicitly select** — false knowledge is worse than missing knowledge.

**Append rules**:
- Each entry: `- <one-line claim>. <path:line pointer>.`
- If a candidate carried a `⚠️ Name-vs-impl mismatch` flag, keep the flag inline so the user sees the warning in the final file.
- Drop the verification snippet when writing to `knowledge.md` — snippets exist only for the SCAN-time review, not for the final knowledge file.
- Place each entry under the category heading shown in the SCAN report (Domain / Dev Environment / Gotchas / External Dependencies). Create the heading inside the skeleton if it is somehow missing.
- Preserve the per-section HTML guidance comments unchanged — they sit between the heading and the first entry.

**Section-fit check (mandatory before placing any entry)**:

Before placing each entry under its target heading, re-read that heading's HTML guidance comment and confirm semantic fit. Common mismatches to catch:

| Misfit symptom | Wrong section | Correct destination |
|---|---|---|
| Hardcoded host / port / DSN / connection string | External Dependencies (header says "upstream service quirks") | Dev Environment (or new `## Infrastructure` section if 2+ such entries) |
| Build / bundler config oddity | Gotchas | Dev Environment |
| Domain rule sourced from upstream service docs | Domain | External Dependencies (the rule lives upstream, not in our domain model) |
| Test-only fixture quirk | Domain | Dev Environment |

**Rule**: if an entry's text does not match the target heading's HTML guidance comment, **do one of**:
1. Re-classify into a category that fits — re-read all four headings' guidance comments and pick the best match.
2. If no existing category fits, surface a warning in the BUILD summary: `⚠️ Entry "<one-line>" did not fit any existing category — appended to <best-guess section>; consider opening a new section.` and append under the best-guess section. Do not silently force-fit.
3. Never invent a category heading on the fly without flagging it.

**Reality-check note**: if the project has clear infrastructure-heavy concerns (Redis hosts, S3 buckets, CDN URLs, cron schedules, K8s namespace assumptions) but no `## Infrastructure` section exists, append the first such entry under Dev Environment but include a one-line note in the BUILD summary suggesting the user open a dedicated section.

**Length discipline (applies to every appended entry)**:
- One line per entry. Format: `<project-specific fact>. <path:line pointer>.`
- Two lines only when a single fact genuinely needs both halves.
- If "and" / "because" / multi-clause conditions appear, the entry is explaining logic — collapse to a pointer or split into separate entries before appending.
- No speculative or hypothetical entries — past pain only.

### 4. Show summary

```
## feature-spec Initialized

**Location:** feature-spec/

### Files written
- feature-spec/config.yaml  ← tool-runnable config (lint + verification commands)
- feature-spec/context.md   ← AI-readable project context (8 required sections + optional Conditional Subsystems / Anti-patterns / Glossary)
- feature-spec/knowledge.md ← annotated skeleton (only when missing) + audit decisions applied (R rewritten / D deleted / U flagged uncited — omit if step 4.5 skipped or user replied `none`) + N confirmed seed entries appended (omit "+N" half if user replied `none` or no candidates existed)

### Detected highlights
- Tech stack: <summary>
- Architecture: <layers summary>
- Domains mapped: <count>
- Hard rules: <count>
- Knowledge audit: <"X kept / Y rewritten / Z deleted / W flagged" — omit if step 4.5 skipped>
- Knowledge seeds: <count, or "none">

### Directory structure
feature-spec/
  config.yaml          ← tool-runnable config (lint + verification commands)
  context.md           ← AI-readable project context (auto-synced by /esdd-complete)
  specs/               ← accumulated main specs
  changes/             ← active changes
  knowledge.md         ← annotated skeleton + entries you approved during /esdd-init's batch confirmation

### Next steps
- Review feature-spec/context.md and refine Domain-to-Code Map / Hard Rules
- Open `feature-spec/knowledge.md` to confirm the appended entries look right (skip if you replied `none` or no candidates existed)
- Review audit decisions in `feature-spec/knowledge.md` — if you replied `keep-all`, look for the `<!-- audit ... -->` summary comment at the top of the file and resolve flagged entries manually; if you replied `apply` / `<indices>`, sanity-check the rewritten lines (skip if step 4.5 did not run)
- Run `/esdd-propose` to create your first change
```

---

## Guardrails

- **Language**: all conversation output (SCAN report, AskUserQuestion text, status announcements, BUILD summary, error messages) MUST be in **Traditional Chinese**. File contents (`config.yaml`, `context.md`, `knowledge.md`, all HTML comments, all examples) stay in **English** so they remain readable for AI agents and code reviewers downstream.
- **Two-phase is mandatory**: never skip SCAN — `context.md` has many sections and AI cannot reach >80% accuracy on all of them, so without confirmation half the file is wrong.
- **Cap questions at 3**: more than 3 turns the init into a survey. Trust the auto-detected draft for the rest.
- **Never overwrite without asking**: Phase 0 always asks per-artifact before BUILD writes.
- **Always create missing subdirectories** (`specs/`, `changes/`) even if `feature-spec/` partially exists.
- **`context.md` is markdown by design**: the format stays loose so humans edit it naturally and `/esdd-complete` can append without schema constraints.
- **Versions live in ONE place**: Tech Stack & Versions is the single source of truth. Before writing, scan the drafted `context.md` for version-number patterns (`\d+\.\d+`, `v\d+`, ISO years) outside that section and strip them — replace with the framework name or "current major".
- **Conditional sections are conditional**: omit Conditional Subsystems / Anti-patterns / Glossary entirely when not applicable; do not leave empty stubs or "TBD" placeholders.
- **Hard Rules vs knowledge.md/Gotchas**: Hard Rules are structural invariants only. Migration leftovers, version-pinned warnings, and "do not use the old X" notes feed into "Knowledge seed candidates" and, after user approval in the SCAN-time batch question, are appended to `knowledge.md`'s Gotchas section.
- **Domain map uses pointer form**: never enumerate component lists; rely on the path + cardinality so the doc does not rot.
- **Entry Points scan is exhaustive**: walk the full Phase 1 checklist (HTTP, pages, middleware, plugins, modules, jobs, event handlers, CLI). Missing one entry point silently breaks AI's ability to add features there.
- **Candidates require explicit user approval before writing**: `/esdd-init` shows surviving candidates inline in the SCAN report (numbered list with `path:line` + snippet, using `C`-prefix indices) and asks one batch question (`C1,C3,C5` / `all` / `none`). Only the entries the user explicitly selects are appended to `knowledge.md`. Default if the user does not answer = `none` (false knowledge worse than missing). No `.draft` file is produced.
- **Candidate-selection question is exempt from the 3-cap**: the gap-filling cap (max 3 questions for Mission / Domain map / Hard Rules) does not include the candidate-selection question; they are different decision categories.
- **Existing-entry audit (step 4.5) only runs when there is real content to audit**: skip when `knowledge.md` is missing, contains only the skeleton, or the user picked "Regenerate" for it in Phase 0. AI never auto-deletes existing entries — every drop / rewrite must be approved through the audit-decision batch question.
- **Audit decisions default to `keep-all`**: when the user does not answer the audit-decision question, leave existing entries untouched and inject a single dated audit-summary HTML comment at the top of the file. Never silently apply suggested rewrites or deletions.
- **Audit-decision question is exempt from the 3-cap**: same rationale as the candidate-selection question — different decision category, asked at most once per init run, only when step 4.5 produced ⚠️ / ❌ / ❓ findings.
- **Audit + candidate dedup**: candidate scanning (step 4) must filter out anything that semantically duplicates a `✅ Still valid` or `⚠️ Needs rewrite` audited entry, so the user does not decide on the same fact twice.
- **Audit indices use prefixes**: existing audited entries in the SCAN report use `A`-prefix indices (`A1`, `A2`); new candidates use `C`-prefix indices (`C1`, `C2`). The two question replies parse independently.
- **One line per knowledge entry**: every claim appended to `knowledge.md` is exactly one line; the verification snippet shown during SCAN is dropped on write. No speculative ("if future X, then Y") claims.
- **Cite-or-Skip is non-negotiable**: every knowledge candidate must carry a `path:line-line` citation and a 3–5 line snippet. No citation → silent drop, even if the candidate "looks right". Naming alone never qualifies.
- **Citations must be code, not markdown**: `knowledge.md` entries cite `.ts` / `.cs` / `.vue` / `.py` / config files — never other markdown docs (`CLAUDE.md`, `AGENTS.md`, `README.md`). Markdown citations create circular references and are silently dropped. Historical rules reclassified from `CLAUDE.md` must be re-anchored to the actual code location they constrain, otherwise the candidate is dropped.
- **Pointer-over-enumeration is a global context.md rule, not just Domain Map**: every section must use pointer form when listing ≥4 named items. Cross-cutting Concerns, Architecture Layers, Conditional Subsystems all fall under this rule. Entry Points is the one exception (its purpose IS to enumerate locations) — but each row inside it still points at a directory, not the handlers within.
- **context.md self-audit before write is mandatory**: AI must scan its own draft for enumeration smells (comma-lists, bullet explosions, identifier-suffix runs), version drift outside Tech Stack, and cross-doc rationale references — and rewrite hits as pointers — before persisting `context.md`. The Editing rules embedded at the top of `context.md` apply to AI at write time, not just to humans editing it later.
- **Section-fit check before knowledge.md append**: every entry's claim must match its target heading's HTML guidance comment. Common misfits (Redis host into External Dependencies, build config into Gotchas) must be re-classified or surfaced as a warning in the BUILD summary — never force-fit silently.
- **Self-skeptic + counter-example passes are mandatory**: every surviving candidate must be re-checked against the cited snippet AND grep-tested for contradicting cases before being shown in the SCAN report for user selection. Mark name-vs-impl mismatches with `⚠️` so the user can spot them at confirmation time.
- **Knowledge seed scope is current files only**: scan `.env.example`, READMEs, package.json scripts, informational code comments, and historical rules from CLAUDE.md/AGENTS.md. Do NOT mine git log or scan `HACK`/`FIXME`/`XXX` — those are unresolved TODOs, not stable knowledge. Ongoing knowledge accrues through `/esdd-complete` after each change.
- **Downstream compatibility**: `/esdd-propose` and `/esdd-apply` continue to read `config.yaml`. The `context:` string in `config.yaml` should at minimum point to `context.md` so agents can drill in when needed.
