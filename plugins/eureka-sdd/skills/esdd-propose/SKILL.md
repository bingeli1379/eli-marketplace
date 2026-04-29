---
name: esdd-propose
description: >
  Generate spec artifacts (proposal, design, tasks, specs) for a new change.
  Use when the user wants to describe what they want to build and get a complete
  proposal with design, specs, and tasks ready for implementation.
user-invocable: true
---

Generate a complete set of spec artifacts for a new change — proposal, design, specs, and tasks — all in one step. Follows **SDD (Spec-Driven Development)** with **DDD (Domain-Driven Design)** domain modeling.

Artifacts created:
- `proposal.md` — what & why
- `design.md` — how (technical decisions, **domain model**, **API contract**, **shared types**)
- `specs/<capability>/spec.md` — acceptance criteria (WHEN/THEN)
- `tasks.md` — implementation checklist grouped by agent type (**TDD-style**: test first → implement → refactor)

After all artifacts are created, **automatically runs validation** (`validate` skill logic) and fixes any issues until all checks pass.

**Input**: The argument is a description of what the user wants to build, OR a kebab-case change name.

**Steps**

1. **If no clear input provided, ask what they want to build**

   Use the **AskUserQuestion tool** (open-ended, no preset options) to ask:
   > "What change do you want to work on? Describe what you want to build or fix."

   From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.

2. **Ensure feature-spec is initialized**

   Check if `feature-spec/config.yaml` exists. If not, execute the `init` skill logic to initialize the directory structure and auto-detect project context.

   If already initialized, read `feature-spec/config.yaml` for project context.

3. **Create the change directory**

   ```
   feature-spec/changes/<name>/
   ```

   If a change with that name already exists, use **AskUserQuestion** to ask if user wants to continue it or create a new one with a different name.

4. **Read existing context**

   - Read `feature-spec/config.yaml` for project context (tech stack, conventions, rules)
   - Read `feature-spec/context.md` if it exists — AI-readable project map (architecture layers, domain-to-code map, entry points, hard rules, common commands). Use it to ground the Step 5 codebase scan (start from the domain folders it points at) and the Step 6 boundary definition (Hard Rules become non-negotiable constraints for design.md).
   - Read `feature-spec/knowledge.md` if it exists — operational tribal knowledge (Domain rules, Dev Environment, Gotchas, External Dependencies). Treat Gotchas as binding constraints when shaping design and tasks; ignoring a documented landmine is a propose-time bug.
   - Read `feature-spec/specs/` for existing main specs (to understand what capabilities already exist)
   - `context.md` and `knowledge.md` are optional — skip silently if missing (the project may not have run `/esdd-init` yet, or the user may have removed them deliberately).
   - These inform artifact generation but are NOT copied into artifact files

5. **Exhaustive codebase scan — identify ALL affected files**

   **ZERO MISSES. Thoroughness over speed. This step is MANDATORY.**

   Scan the actual project codebase before clarifying requirements:
   - User specified scope → scan every file within it. No scope → scan entire project.
   - Use `Glob` to list ALL files, then read/inspect each that could be affected.
   - Do NOT rely on filename guessing alone — open files to confirm relevance.
   - Build an **affected-files inventory**: every file to create/modify/delete, with WHY (imports, routes, types, indirect dependencies).
   - Include this inventory as "Affected Files" section in `design.md`. Every affected file must map to at least one task.

   **Dry-run for config-flip AND type-level changes:** When a change enables/disables rules, flags, or config that will surface new errors (e.g., enabling ESLint rules, turning on `strict` mode, enabling a feature toggle that changes validation), OR when a change modifies type signatures that affect downstream consumers (e.g., removing index signatures, changing type defaults like `any` → `unknown`, narrowing union types, making properties optional via `Partial<T>`), do NOT estimate the violation count by grepping patterns. Instead:
   1. Temporarily apply the config/type change in a temporary branch
   2. Run **ALL** the project's verification and lint commands — both `verification_commands` AND `lint_commands` from `config.yaml` (or detect from `package.json` scripts). **NEVER hardcode tool-specific commands** like `npx vue-tsc --noEmit`. Type-aware ESLint rules (e.g., `@typescript-eslint/no-unnecessary-type-assertion`) can surface errors that type-check alone misses.
   3. Use that output as the authoritative affected-files inventory and violation counts
   4. Categorize errors: **in-scope** (files this change will modify) vs **out-of-scope** (downstream files for future changes)
   5. If out-of-scope errors > 0: this change has **cascade impact**. You MUST either:
      - (a) Expand scope to include all affected files (and add tasks for them), OR
      - (b) Reduce the change's aggressiveness to maintain backward compatibility (e.g., keep `any` default, keep index signature) and defer the stricter version to a later change that handles the callers
      - **Never leave out-of-scope errors for "a future change" to handle** — the current change must compile cleanly on its own.
   6. Use the exact error list to create **bounded tasks** — never write catch-all tasks like "fix all type errors". Instead, create one task per error category or per file group (e.g., "Add optional chaining for 5 nullable properties in stores/main.ts", "Add type parameters to 3 Form.post calls")
   7. Revert the temporary changes

   This prevents design estimates from diverging from reality. Grep-based estimates miss indirect violations, cascading type errors, and tool-specific edge cases.

   **Pattern-removal changes** (e.g., "remove all `: any`", "remove all `@ts-nocheck`", "replace all `var` with `const`/`let`"): The target pattern is valid code that won't produce compiler/linter errors, so the dry-run above won't catch them. Instead:
   1. Grep the ENTIRE scope for the target pattern — this output IS the authoritative inventory
   2. Every match must map to at least one task in `tasks.md`
   3. Cross-verify in `design.md` Affected Files: total grep count must equal sum of per-file counts listed
   4. If the grep finds instances in files not covered by any task group, add them or explicitly mark as out-of-scope with justification

   **When tightening types by removing index signatures or widening/narrowing types**, check BOTH directions to discover all fields that must be in the interface:
   - **Backend source** → fields the API actually returns
   - **Frontend usage** → `grep 'variable.'` across all files to find every property access (includes runtime-injected fields not in backend source)
   Take the **union** of both sets. Mark backend-only fields as required, frontend-only fields as optional (`?`) with a comment explaining the source.

6. **Clarify requirements and define feature boundaries**

   Before generating any artifact, analyze the user's description and proactively clarify:

   **a. Identify ambiguities and surface assumptions** — vague scope, undefined behavior, missing edge cases. **Enumerate every implicit assumption you are making** as you interpret the request (e.g., "assuming admin role is required", "assuming pagination reuses the existing pattern", "assuming no backfill is needed for existing data"). Hidden assumptions in your reasoning become silent bugs in design.md — externalize them so the user can correct them.

   **b. Define boundaries (multi-dimensional)** — draw scope on five axes, not just features:
   - **Feature**: in-scope capabilities vs out-of-scope (separate changes)
   - **Integration**: which systems this calls, which systems call this
   - **Data**: tables/collections in scope, migration/backfill expectations
   - **NFR budget**: performance targets, security requirements, UX constraints that apply to THIS change
   - **Reversibility**: how hard is this decision to change later (easy / hard / irreversible) — drives how careful the upfront clarification needs to be

   **c. Assess size** — if 3+ independent capabilities or 15+ tasks, suggest splitting. Each split should be reviewable in one sitting, self-contained, and focused on one concern. Example: "Add user management" → `add-user-registration`, `add-user-profile`, `add-user-roles`.

   **d. Propose approaches** — Based on the codebase scan and requirement analysis, propose 2-3 implementation approaches with trade-offs and a clear recommendation. This step prevents the architect agent from committing to a direction the user didn't intend.

   - Each approach: one sentence describing the strategy + key trade-off (e.g., "simpler but less extensible")
   - Lead with the recommended approach and state why
   - If only one viable approach exists, state it and explain why alternatives were ruled out

   **e. Ask the user** via **AskUserQuestion** — ONE message with:
   ```
   **In-Scope:** [features]
   **Out-of-Scope:** [separate changes]
   **Scope Assessment:** [OK / Too Large — split suggestion if needed]
   **Assumptions I'm making:**
     - [assumption 1] — correct if wrong
     - [assumption 2] — correct if wrong
   **Unknowns (impact if wrong):**
     - [unknown 1] — if X turns out to be Y, then Z in the design changes
     - [unknown 2] — ...
   **NFR / Data / Reversibility:**
     - NFR budgets: [perf / security / UX constraints that apply, or "none specified"]
     - Data: [tables/collections touched, migration/backfill expectations, or "none"]
     - Reversibility: [easy / hard / irreversible] — [one-sentence implication]
   **Approaches:**
     1. [recommended] — description + trade-off
     2. — description + trade-off
     3. — description + trade-off (if applicable)
   **Recommendation:** [which approach and why]
   **Questions:** [all clarification questions, if any]
   ```
   If the input is detailed and unambiguous with only one viable approach, the **Questions** section may be empty — but **Assumptions**, **Unknowns**, and **NFR / Data / Reversibility** MUST always be filled in so the user can catch silent misinterpretations.

   **f. If splitting — plan the sub-change chain (artifacts are written later in Step 7)**

   Decide the order in which sub-changes will be generated (earlier informs later) and what each sub-change's `proposal.md` will declare in its **Dependencies** section. Do NOT write any artifact files in this step — actual generation happens in Step 7 after the Scope Contract (Step 6g) is confirmed.

   Dependencies section format (to be included in each sub-change's `proposal.md` during Step 7):

   ```
   ## Dependencies
   - **Depends on:** [list of change names this change requires to be applied first, or "none"]
   - **Depended by:** [list of change names that require this change, or "none"]
   - **Execution order:** N of M
   ```

   This makes the dependency chain visible to users and to `/esdd-apply-all`. A combined summary with the full dependency graph is shown after Step 7 completes for all sub-changes.

   **g. Confirm scope contract before generating artifacts**

   After the user answers 6e (or immediately, if 6e had no Questions), synthesize everything into a concise **Scope Contract** and show it back as a regular chat message (NOT AskUserQuestion — this is a final sanity check, not an open clarification round). Then wait for the user's reply.

   ```
   ## Scope Contract — confirm or correct

   **Change:** <name>
   **Doing:** [concise in-scope bullets, reflecting the user's answers]
   **NOT doing:** [concise out-of-scope bullets]
   **Assumptions (locked in — design.md will depend on these):**
     - [assumption 1]
     - [assumption 2]
   **NFR / Data / Reversibility:** [one line each, from 6e]

   Reply with corrections, or "go" / "ok" / "proceed" to generate artifacts.
   ```

   - **Purpose**: catches interpretation mismatches BEFORE the architect agent writes design.md. A wrong design.md costs 5-10 minutes to regenerate; a wrong Scope Contract costs 10 seconds to correct here.
   - **One correction round only**: if the user pushes back, incorporate the corrections and proceed directly to Step 7 — do NOT loop on this checkpoint. More than one round of correction is a signal that Step 6e was under-specified; treat that as self-feedback for future runs, not a reason to keep asking.
   - **Split changes**: show ONE combined Scope Contract covering all sub-changes (with per-change Doing/NOT doing bullets), not one checkpoint per sub-change.

7. **Generate artifacts in dependency order**

   Generate each artifact following the templates in this skill's `templates/` directory. The dependency order is:

   ```
   proposal (standalone)
       ↓
   specs (depends on proposal — defines acceptance criteria FIRST)
       ↓
   design (depends on proposal + specs — specs are constraints the architect must satisfy)
       ↓
   tasks (depends on: proposal, design, specs)
   ```

   For each artifact:
   - Read the corresponding template from `templates/` for structure guidance
   - Read completed dependency artifacts for context
   - Apply project context from `config.yaml` as constraints (do NOT copy into the file)
   - Write the artifact file
   - Show brief progress: "Created `<artifact>`"

   **a. proposal.md**
   - Fill in Why (motivation, min 50 chars), What Changes, Capabilities (new/modified), Impact
   - Capabilities must use kebab-case names (these become `specs/<name>/` directories)
   - Impact should clearly indicate which layers are affected (Backend, Frontend, API, Database, etc.)

   **b. specs/<capability>/spec.md** (FIRST — defines acceptance criteria before design)
   - Read proposal.md
   - For EACH capability listed in proposal's "New Capabilities" and "Modified Capabilities":
     - Create `feature-spec/changes/<name>/specs/<capability-name>/spec.md`
   - Each requirement MUST use `SHALL` or `MUST` keyword
   - Each requirement MUST have at least 2 Scenarios with WHEN/THEN (happy path + edge case minimum)
   - Scenarios should also cover: error cases, authorization (if applicable)
   - Spec THEN clauses define the **acceptance criteria** — these become constraints for the architect
   - **Grounding requirements for THEN clauses** (prevents the three common hallucination patterns):
     1. **Tool-behavior assertions** ("pnpm does X", "vitest emits Y", "npm includes Z by default") MUST be verifiable via a concrete command (`pnpm … --dry-run`, `npm pack --dry-run`, `node -e …`). Prefer "the THEN output is whatever `<command>` produces at BASE_SHA" over asserting a specific string from memory. When uncertain about a tool's semantics, run the command against the current repo during propose and quote the actual output.
     2. **Historical / temporal references** ("retained from the previous fix", "preserved from v1.1.0", "as introduced in commit X") MUST cite a specific SHA plus the exact line the claim refers to, or be removed. Phrases like "前次修復保留" / "previously fixed" without a SHA are hallucination bait — the model fabricates plausible-sounding history that never happened.
     3. **Exact-string invariants** (`files: ["dist"]`, `types: ["vitest/globals"]`) MUST be rewritten as **necessary-condition invariants** (`files MUST at least include "dist"`, `types MUST include "vitest/globals" and "node"`) unless the exact-match is genuinely load-bearing. Ecosystem conventions (Changesets adding `CHANGELOG.md`, tool defaults injecting metadata) will routinely extend these arrays in valid ways; over-tight specs force agents to fight the ecosystem.

   **c. design.md** (AFTER specs — architect receives specs as constraints)

   Dispatch the **architect agent** — use the **Agent** tool with `run_in_background: true` and `mode: "bypassPermissions"`:
   - `subagent_type`: `"eureka-sdd:architect"`
   - **CRITICAL — enforce structured trade-off analysis**: The architect's dispatched prompt MUST include an "Analytical depth requirement" section instructing the agent, BEFORE writing design.md, to:
     1. Enumerate **2-3 candidate designs** for each major decision (domain model shape, storage / aggregate boundaries, API style, integration pattern).
     2. For each candidate, list **concrete trade-offs** (complexity, performance, reversibility, blast radius, coupling).
     3. **Explicitly justify rejections** — rejected alternatives must be named, with the reason they were ruled out (cost, mismatch with constraints, unnecessary flexibility, etc.).
     4. Do NOT skip straight to "the answer". The comparison IS the design work — a single-option design.md is treated as incomplete.

     Rationale: structural enforcement of exhaustive reasoning, with an auditable trail of rejected alternatives, is the primary safeguard against a single-option design.md.
   - **CRITICAL — feed pre-collected context**: The prompt MUST include the **complete affected-files inventory from Step 5**, the proposal.md content, **all completed spec files from Step 7b**, project context from config.yaml, **the full contents of `feature-spec/context.md` if it exists** (project map: architecture layers, domain-to-code map, entry points, hard rules — these are constraints the design MUST honor; surface Hard Rules to the architect as non-negotiable), **the full contents of `feature-spec/knowledge.md` if it exists** (operational gotchas and dev tips that must inform design decisions to avoid known landmines — explicitly instruct the architect to consult Gotchas when choosing patterns, especially for areas the change touches), existing specs from `feature-spec/specs/`, and the design.md template from `templates/`. Include any file contents you already read during the codebase scan (store definitions, key interfaces, usage patterns, etc.). If `context.md` / `knowledge.md` do not exist, omit those sections entirely from the prompt — do not fabricate placeholder content.
   - **CRITICAL — specs are constraints**: Explicitly instruct the architect: "The spec THEN clauses are acceptance criteria that your design MUST satisfy. If you believe a spec THEN clause should be different, do NOT silently override it. Instead, mark it as `CONFLICT:` in your design.md with your reasoning, so the orchestrator can resolve it with the user."
   - **Do NOT tell the architect to re-scan the codebase.** Explicitly instruct: "All context is provided below. Do NOT re-read files or re-scan the codebase. Go straight to writing design.md."
   - Instruct the architect to write `design.md` directly to `feature-spec/changes/<name>/design.md`

   The architect agent will produce:
   - Context, Goals/Non-Goals, Decisions (with alternatives considered), Risks/Trade-offs
   - **Domain Model (DDD)**: Bounded contexts, aggregates (root + children + invariants), value objects, domain events
   - **API Contract**: Every endpoint (METHOD, path, request/response schema, status codes, auth)
   - **Shared Types**: TypeScript interfaces and C# DTOs as integration contract
   - Each decision with justification and rejected alternatives
   - Risks with mitigation strategies
   - **CONFLICT markers** (if any) — where the architect disagrees with a spec THEN clause

   **Why `mode: "bypassPermissions"`**: The architect agent writes ONLY to `feature-spec/changes/<name>/design.md`. Without this mode, the agent blocks on Write permission approval — the user cannot see or approve the permission prompt from a background subprocess, causing the agent to hang for minutes (often 5-10 min per Write). This is the #1 cause of slow `/esdd-propose` execution.

   **d. Resolve conflicts and cross-validate**

   **WAIT for the architect agent to complete before proceeding.** Do NOT write design.md yourself — the architect agent has a specialized system prompt with design checklists, trade-off frameworks, and structured analysis that you do not have access to. Its output will be more thorough than what you can produce. If the agent is taking long, check its progress — do NOT override it by writing the file yourself.

   Once the architect agent completes, read the generated `design.md`:

   **d1. Resolve CONFLICT markers**: If the architect marked any `CONFLICT:` items:
   - Collect ALL conflicts into one structured **AskUserQuestion** message:
     ```
     Spec 與 Design 有以下衝突：
     1. Spec says [THEN clause]. Architect recommends [alternative] because [reason].
     2. ...
     For each: keep spec / adopt architect's approach?
     ```
   - Based on user's decision, update the losing side (spec OR design) to align
   - If no CONFLICT markers, skip this step

   **d2. Cross-validate** (even if no conflicts):
   - Do spec scenarios reference types, endpoints, or domain concepts that match `design.md`?
   - If the architect found additional affected files not in your Step 5 inventory, update your understanding accordingly — these must be reflected in tasks.md.
   - This step is quick — only check names, paths, and types, not rewrite specs.
   - **Both artifacts must agree** — if any remaining inconsistency is found, fix whichever side is less specific (usually update spec names/paths to match design's concrete choices).

   **e. tasks.md** (follows **TDD** — Red/Green/Refactor cycle)
   - Read proposal.md, **the architect-generated design.md**, and all specs first
   - Use design.md as the authoritative source for affected files, decisions, and migration patterns — do NOT contradict it

   **Grouping principle: each group = one reviewable unit = one final commit.**
   The orchestrator squashes each group into a single commit after implementation. Design groups so a reviewer can understand each commit in isolation.

   - **Each group MUST contain a single agent type.** This ensures each commit is a single-concern, single-layer change.
     - GOOD: `## 1. Search API and service layer` (all Backend tasks)
     - GOOD: `## 2. Search page and composables` (all Frontend tasks)
     - BAD: `## 1. User Search` (mixes Backend + Frontend + E2E → produces a mixed-concern commit)
   - **Group heading describes the concern**, NOT the agent type.
     - GOOD: `## 1. Search API and service layer`
     - BAD: `## 1. Backend tasks`
   - **For feature changes**: split by layer/concern. Each layer of a feature becomes its own group.
     - Example: "User Search" feature → group 1 (Backend API), group 2 (Frontend page), group 3 (E2E tests)
     - If shared types/contracts are needed by multiple groups, make them their own group and add dependencies.
   - **For refactoring / migration / style changes**: group by **type of change**, NOT by directory or module. Each group = one kind of mechanical operation across all affected files.
     - GOOD: `## 1. Remove empty script setup blocks` (all files, one commit)
     - GOOD: `## 2. Reorder SFC blocks to script-template-style` (all directories, one commit)
     - BAD: `## 2. Reorder SFC in core` + `## 3. Reorder SFC in productPlatform` + `## 4. Reorder SFC in games` (same operation split by directory — produces redundant commits)
     - Rule of thumb: if a reviewer would say "this is the same change, just different files", it belongs in one group
   - **Structural moves MUST bundle their dependent config updates into a single task**: whenever a task involves `git mv`, directory restructuring, or path renames, ALL downstream config edits that reference the old paths (tsconfig `include` / `paths`, ESLint `parserOptions.project`, Vite `lib.entry`, Vitest `setupFiles`, package.json `main` / `exports` / `files` entries, CI path references, etc.) MUST live in the **same task = same commit** as the move itself. Per-file decomposition breaks here because the post-move and pre-config-update state is mutually inconsistent: pre-commit lint cannot pass, `tsc` cannot type-check, and agents end up bypassing hooks with `--no-verify` to make per-task commits at all.
     - GOOD: `- [ ] 2.1 (DevOps) git mv src/ → packages/toolkit/src/ AND update vite.config lib.entry paths, tsconfig include paths, and eslint.config parserOptions.project in the same commit`
     - BAD: `- [ ] 2.1 git mv src/` then `- [ ] 2.2 update vite.config path` then `- [ ] 2.3 update eslint config` (three intermediate broken commits; every one fails pre-commit lint)
     - If the full structural edit is genuinely too large for a single commit (e.g., > 40 files), split by **independent move units** (e.g., move library source as one task, move docs as another) — NOT by operation type within a single move unit.
   - **Dependency annotations**: if a group depends on another group's output (e.g., frontend needs backend API types), annotate with `<!-- depends: N[, M...] -->` on the group heading line. The orchestrator uses these to determine execution waves.
     - Groups without dependencies run in parallel (Wave 1)
     - Groups depending on Wave 1 groups run after Wave 1 completes (Wave 2), etc.
     - If two independent groups (no dependency) modify the same file, add a dependency between them to prevent merge conflicts.
   - **Tag each task with an agent type** in parentheses:
     - `(Backend)` → dotnet-engineer (includes unit tests, TDD style)
     - `(Python)` → python-engineer (FastAPI, data pipelines, ML, LLM, monitoring)
     - `(Frontend)` → vue-engineer (includes unit tests, TDD style)
     - `(Electron)` → electron-engineer (main process, IPC, preload, packaging)
     - `(Database)` → database-engineer (schema, migration, indexing)
     - `(DevOps)` → devops-engineer (Docker, CI/CD, K8s)
     - `(Performance)` → performance-engineer
     - `(Security)` → security-engineer (security audit, hardening)
     - `(Documentation)` → technical-writer (API docs, changelog, ADR)
     - `(E2E)` → qa-engineer (Playwright E2E tests for AC verification)
   - The orchestrator dispatches **one agent per group** in an isolated worktree. Groups in the same wave run in parallel.
   - **AI decides group granularity automatically** based on the change type. Do NOT ask the user to choose a commit strategy.
   - **Group complexity estimation**: For each group, assess whether tasks are **mechanical** (find-and-replace, type annotation changes, import updates) or **analytical** (requires reading context, making judgment calls, fixing cascading errors). If a group has analytical tasks AND > 6 total tasks, split into sub-groups by concern. Mechanical-only groups can be larger. Never create groups with unbounded scope — every task must have a predictable, finite scope determined by the dry-run in Step 5.
   - **TDD task structure for Backend/Frontend tasks**: Each feature should follow RED → GREEN → REFACTOR:
     1. Write failing unit test first (RED)
     2. Implement minimum code to pass (GREEN)
     3. Refactor if needed (REFACTOR)
   - **E2E tasks**: Each spec WHEN/THEN scenario becomes a Playwright E2E test case
   - Each task: starts with a verb, actionable, scoped to one logical unit
   - Use numbered groups and sub-items: `## 1. Search API and service layer` → `- [ ] 1.1 (Backend) Write unit test for ...`
   - Tasks must cover ALL requirements from specs — every spec scenario should be traceable to at least one task
   - **Do NOT create `Test` groups** — unit tests belong inside Backend/Frontend tasks; E2E tests are tagged `(E2E)` in their own group

8. **If an artifact requires user input** (unclear context, ambiguous requirements):
   - Use **AskUserQuestion tool** to clarify
   - Then continue with creation

9. **Auto-validate and fix**

   After all artifacts are created, run two layers of validation:

   **a. Semantic self-review** — before structural validation, check for quality issues:
   - **Placeholder scan:** Search ALL artifacts for these plan failure patterns and fix every instance:
     - "TBD", "TODO", "[fill in]", "implement later", "fill in details"
     - "Add appropriate error handling" / "add validation" / "handle edge cases" (vague directives without specifics)
     - "Similar to Task N" or "same as above" (repeat the actual content — agents read tasks independently)
     - "Write tests for the above" without actual test scenarios
     - Steps that describe what to do without showing how (missing acceptance criteria)
     - References to types, functions, or API endpoints not defined in any artifact
   - **Type/name consistency:** Do types, method signatures, endpoint paths, and component names used in `tasks.md` match what's defined in `design.md`? A function called `searchUsers()` in design but `findUsers()` in tasks is a bug. Cross-check all shared names across artifacts.
   - **Internal consistency:** Do any sections across artifacts contradict each other? Does the design match the proposal's capabilities? Do tasks cover all spec scenarios?
   - **Scope check:** Has scope crept beyond what user approved? Are there tasks not traceable to a spec requirement?
   - **Ambiguity check:** Could any requirement be interpreted two ways? If so, pick one and make it explicit.

   Fix any issues found inline immediately.

   **b. Structural validation** — run the validation logic from `validate` skill:
   - Read all artifacts and check against all validation rules
   - If any errors found: **fix them immediately** (edit the artifact files to resolve issues)
   - Re-validate until **all checks pass** (max 3 rounds to avoid infinite loops)
   - If issues persist after 3 rounds, report remaining issues and ask user for input

10. **Show final summary**

   ```
   ## Spec Created: <change-name>

   **Location:** feature-spec/changes/<name>/

   ### Artifacts
   - proposal.md — [one-line summary]
   - design.md — [one-line summary, includes domain model + API contract]
   - specs/<cap-1>/spec.md — [one-line summary]
   - specs/<cap-2>/spec.md — [one-line summary]
   - tasks.md — [N tasks in M groups, TDD structure]

   ### Validation
   ✓ PASS — all checks passed

   Ready for implementation. Run `/esdd-apply <name>` to start.
   ```

11. **Commit spec artifacts**

   Stage and commit all generated artifacts following the `conventional-commits` skill (`skills/conventional-commits/SKILL.md`):

   ```bash
   git add feature-spec/changes/<name>/
   git commit -m "docs: propose <change-name>"
   ```

   - Do NOT push to remote
   - If `feature-spec/config.yaml` was newly created (Step 2), include it in the commit:
     ```bash
     git add feature-spec/config.yaml feature-spec/changes/<name>/
     git commit -m "docs: propose <change-name>"
     ```

**Guardrails**

- Create ALL 4 artifact types (proposal, design, specs, tasks). Do NOT skip any.
- Read dependency artifacts before creating dependent ones. Specs MUST complete before dispatching the architect agent — specs are constraints for design, not the other way around.
- **Exhaustive codebase scan is MANDATORY** — do NOT skip Step 5. Every file in scope must be inspected. Zero misses is the absolute principle.
- **Do NOT override specialized agent output.** The architect agent has a dedicated system prompt with domain-specific checklists you don't have. WAIT for it to complete, then use its output as the baseline for tasks.md and cross-validation. If the architect found more affected files or made different design decisions than you expected, defer to the agent's analysis — it likely has reasons you can't see. **However**, if the architect's design contradicts spec THEN clauses without a `CONFLICT:` marker, that is a bug — escalate to user via AskUserQuestion.
- **Feed pre-collected context to agents.** When dispatching the architect, include ALL file contents and scan results you already gathered in Step 5. Agents re-scanning the same files wastes time. Explicitly instruct agents NOT to re-read files you already provided.
- **Use `mode: "bypassPermissions"` for background agents.** Background agents that write to `feature-spec/` cannot prompt the user for Write permission — they will hang silently. Always set `mode: "bypassPermissions"` when dispatching agents with `run_in_background: true`.
- **Every affected file in `design.md` must be covered by at least one task in `tasks.md`** — cross-check before finalizing
- Capability names in proposal MUST match `specs/<name>/` directory names exactly
- Each task group MUST contain a single agent type and describe a reviewable concern. Each task tagged by agent type in parentheses: `(Backend)`, `(Frontend)`, `(E2E)`, etc.
- If two independent groups modify the same file, add a `<!-- depends: N -->` annotation to prevent merge conflicts during worktree consolidation
- Every spec requirement MUST have SHALL/MUST and at least 2 WHEN/THEN scenarios (happy path + edge case)
- Proactively clarify ambiguities and define feature boundaries BEFORE generating artifacts — do NOT guess when scope is unclear
- Ask all clarification questions in one structured message, not one at a time
- Verify each artifact file exists after writing before proceeding to next
- `config.yaml` context and rules are constraints for YOU, not content for artifact files
- `context.md` and `knowledge.md` are first-class inputs for design.md generation: forward them verbatim to the architect agent in Step 7c. Hard Rules from `context.md` are non-negotiable; Gotchas from `knowledge.md` are binding constraints, not suggestions. If either file is missing, skip silently — the project may not have run `/esdd-init`.
- Use Traditional Chinese for artifact content (matching user's communication language)
- Code examples and technical terms remain in English
