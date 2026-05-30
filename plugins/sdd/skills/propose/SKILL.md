---
name: propose
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

0. **Detect repo topology (MANDATORY first)**

   Load `plugins/sdd/references/repo-topology.md` and run its Step 0 detection. Announce the mode.
   - **single-repo** — scan and plan against the one repo (the steps below, unchanged).
   - **multi-repo** — the change may span several child repos. The Step 5 codebase scan covers every repo the change plausibly touches; per-repo grounding is read per touched repo (Step 4); tasks are grouped so each group lands in exactly one repo (Step 7/design), ordered contract-first across repos. `feature-spec/` (the change artifacts) lives at the umbrella cwd.

1. **If no clear input provided, ask what they want to build**

   Use the **AskUserQuestion tool** (open-ended, no preset options) to ask:
   > "What change do you want to work on? Describe what you want to build or fix."

   From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.

2. **Ensure the feature-spec directory exists**

   Create `feature-spec/specs/` and `feature-spec/changes/` at cwd if missing. Do **not** auto-run `/init` or generate `config.yaml` — config is optional. If it already exists it is read in Step 4; if not, Step 5's codebase scan is the grounding.

3. **Create the change directory**

   ```
   feature-spec/changes/<name>/
   ```

   If a change with that name already exists, use **AskUserQuestion** to ask if user wants to continue it or create a new one with a different name.

4. **Read existing context**

   - **single-repo**: read `feature-spec/config.yaml` — the grounding source. Use its `architecture` block (pattern, layers, entry_points) to ground the Step 5 codebase scan (start from the paths it points at), and treat `hard_rules` as non-negotiable constraints for the Step 6 boundary definition and design.md. If it is missing, skip silently and work from the codebase scan alone.
   - **multi-repo**: for **each child repo the change touches**, read `<repo>/feature-spec/config.yaml` if it exists (its `architecture` + `hard_rules` ground work in that repo); if a repo has none, scan that repo's code. Per the topology rules, never generate config here.
   - Do not read the project's own prose docs (CLAUDE.md, README, etc.) — config.yaml is the only curated grounding this workflow trusts.
   - Read `feature-spec/specs/` for existing main specs (to understand what capabilities already exist)
   - These inform artifact generation but are NOT copied into artifact files

5. **Exhaustive codebase scan — identify ALL affected files**

   **ZERO MISSES. Thoroughness over speed. This step is MANDATORY.**

   Scan the actual project codebase before clarifying requirements:
   - User specified scope → scan every file within it. No scope → scan entire project.
   - Use `Glob` to list ALL files, then read/inspect each that could be affected.
   - Do NOT rely on filename guessing alone — open files to confirm relevance.
   - Build an **affected-files inventory**: every file to create/modify/delete, with WHY (imports, routes, types, indirect dependencies).
   - Include this inventory as "Affected Files" section in `design.md`. Every affected file must map to at least one task.
   - **Find the precedent for every NEW thing (MANDATORY).** For each new artifact the change introduces (endpoint, service, component, store, migration, etc.), locate the nearest existing analog — a sibling that does the same kind of job — and record its path as the **Reference implementation** for that work. You have the full codebase in view right now; this is the cheapest place to find it. Note the approach the analog uses (data access via SP/repository, query conventions, structure, naming, error handling) so the implementing agent mirrors it instead of inventing a new style. If genuinely no analog exists, say so explicitly.

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

   **e. Ask the user** via **AskUserQuestion** — use a **chain-form** message that the user can scan in one screen. Goal: surface only what the user needs to decide on; hide what's already obvious.

   ```
   你說：<one-line restatement of the request>

   理解的鏈：
     <Layer/Module A> → <Layer/Module B> → <Layer/Module C> → ...
     （e.g. User input → AuthService.login → JWT issuer → /api/auth/login → useAuth composable）

   影響：<Backend(新/改)> · <Frontend(新/改)> · <DB(table)> · <其他>

   預設（不對就講哪一條）：
     - <assumption 1>
     - <assumption 2>
     - <assumption 3>
   未定（影響面）：
     - <unknown 1> — 若 X→Y，則 design 的 Z 會變
   NFR/Data/Reversibility： <one line; "無" 可省略>

   做法：<recommended one-liner — 只列推薦那條；替代方案只在真有 trade-off 時才列 #2 #3>

   問題：<只列必須使用者回答的；無→空>
   ```

   **Format guardrails for the chain message**:
   - The chain is the centerpiece — express the change as a flow of named symbols/modules so the user reads it like a diff (`A → B → C`), not a tree of bullets.
   - **Hide noise**: in-scope/out-of-scope only when split is suggested or scope is non-obvious. Otherwise the chain itself implies scope.
   - **Three defaults max**, one line each. Defaults are interpretations the user might disagree with; do NOT list trivially-true facts ("使用 TypeScript") — those are not assumptions, they're context.
   - **Approaches collapse to one line** when only one is viable. Multi-option list only when there's a real trade-off the user must arbitrate.
   - **Questions section is the ONLY place open clarifications go** — keep it short. If empty, omit the line.
   - If the input is detailed and the chain + defaults already cover everything, the message can be ~10 lines total. Long chain messages are a smell — the user can't read them.

   **f. If splitting — plan the sub-change chain (artifacts are written later in Step 7)**

   Decide the order in which sub-changes will be generated (earlier informs later) and what each sub-change's `proposal.md` will declare in its **Dependencies** section. Do NOT write any artifact files in this step — actual generation happens in Step 7 after the Scope Contract (Step 6g) is confirmed.

   Dependencies section format (to be included in each sub-change's `proposal.md` during Step 7):

   ```
   ## Dependencies
   - **Depends on:** [list of change names this change requires to be applied first, or "none"]
   - **Depended by:** [list of change names that require this change, or "none"]
   - **Execution order:** N of M
   ```

   This makes the dependency chain visible to users and to `/apply-all`. A combined summary with the full dependency graph is shown after Step 7 completes for all sub-changes.

   **g. Confirm scope contract before generating artifacts**

   After the user answers 6e (or immediately, if 6e had no Questions), synthesize everything into a **Scope Contract** organized as two sections — **變更清單** (what gets added / replaced / removed, grouped by concept category) and **流程鏈** (how a request / data flows through the system, or how a change cascades downstream). Show it back as a regular chat message (NOT AskUserQuestion — this is a final sanity check, not an open clarification round). Then wait for the user's reply.

   The two sections work together regardless of change type:
   - **新功能**：變更清單 = 列出新增的元件 / API / DB / service / 設定，分類擺好；流程鏈 = 走一遍使用者操作從觸發到結果會經過哪些環節
   - **重構 / migration**：變更清單 = 列出被取代 / 移除的東西，分類擺好；流程鏈 = 一個變動沿著哪些下游擴散（值格式變了 → CSS class → 圖檔名 → API body → 字面比較 …）
   - **混合**：變更清單三類混列（新增 / 取代 / 移除）；流程鏈兩種都有（使用者流程 + 衝擊流程），分標題

   The contract MUST let the user scan top-to-bottom and verify intent without reading code. The single most common cause of Phase 2 review blockers is **a downstream consumer being missed** — either a callsite that wasn't updated (refactor), or a step in the user flow that wasn't accounted for (new feature). 流程鏈 exists specifically to surface these multi-hop ripples.

   ```
   ## 確認一下（變更清單 + 流程鏈，不對就講哪條，OK 就 go）

   <change-name>

   ### 變更清單（依類別 + 動作）

   **【類別 A — e.g. UI 元件 / API endpoint / Cookie 讀寫 / 中間對照表 / DB schema / 拆檔搬家】**
   - 新增 / 取代 / 移除 — <概念名稱描述，不用 symbol 名稱>
   - <下一條>

   **【類別 B】**
   - ...

   ### 流程鏈（一條流程走完會經過哪些環節 / 一個變動會擴散到哪些下游）

   **【1. <一句話描述場景>】**
   <若是新功能：寫使用者操作觸發；若是重構/格式變：寫情境前提，例如「store 存的值格式從 'EN' 變 'en-US'」>
   - <環節 / 下游 1 — 用行為動詞描述，不講 symbol>
   - <環節 / 下游 2>
   - ...

   **【2. <下一個場景或變動>】**
   ...

   ### 鎖定假設
   - <假設 1>
   - <假設 2>

   ### 不做：<one line; 省略 if 無>
   ### 影響範圍 / Reversibility：<one line; 省略 if "無">
   ```

   **Format rules for the two sections**:

   - **Categorize 變更清單 by concept, not by directory / file path** — group similar items under `【類別】` brackets. Pick categories that match the change shape:
     - 新功能常見類別：【UI 元件】、【API endpoint】、【後端 service】、【DB schema】、【設定 / env】、【權限】
     - 重構常見類別：【某概念定義】、【Cookie 讀寫】、【中間對照表】、【拆檔搬家】、【UI 元件改造】、【測試 fixture】
     - 每條前綴標 `新增 / 取代 / 移除` 三選一，讓動作清楚
   - **Use concept names, not symbol names** — say "「語言 → 後端數字編號」橋接表" not "`LANGUAGE_TO_LANGUAGE_TYPE` map"; say "忘記密碼觸發點" not "`ForgotPasswordButton.vue`". The contract is for the user to verify intent, not to enumerate code.
   - **流程鏈 entries need ≥ 3 hops** — if a flow only touches 1-2 places, fold it into 變更清單 instead. 流程鏈 exists specifically to surface multi-hop ripple (user flow with multiple system handoffs, or refactor cascade with multiple downstream consumers).
   - **Use action verbs in 流程鏈, not technical jargon** — say "元件拼 CSS class 名" not "`:class` binding"; say "後端產生 token 寫 DB" not "`TokenService.generate()` + `INSERT INTO password_reset_tokens`". Stay readable for a non-engineer reviewer.
   - **No file:line, no import paths, no precise symbol references** in either section. If the user needs to see file-level detail they can read design.md after approval. The Scope Contract is the conceptual sanity check that precedes design.md.
   - **Format / shape changes are the most error-prone** — when a refactor modifies the FORMAT or SHAPE of data flowing through the system (enum value renamed, cookie format change, type signature widened, etc.), it MUST appear as a 流程鏈 item with all downstream consumers traced (CSS classes / asset filenames / API body / URL / string-literal comparisons / string-split operations / SCSS selectors / etc.). Reviewers historically miss these because they read the Scope Contract for "what changes" not "what downstream assumes about the old shape".
   - **User flows in new features need terminal state** — every 流程鏈 entry for a new feature MUST end at a user-visible result (success page / email sent / data persisted / error message), not at an internal handoff. If the flow stops mid-system, the design will leave a feature half-built.
   - **Length cap**: 變更清單 + 流程鏈 combined SHOULD stay under 30 lines. If exceeded, the change is too large and SHOULD be split into sub-changes (return to 6c/6f).
   - **Split changes**: show ONE combined Scope Contract covering all sub-changes, with the two sections repeated under each sub-change name. Sub-change ordering must reflect the dependency chain from Step 6f.

   **Purpose**: catches interpretation mismatches BEFORE the architect agent writes design.md. A wrong design.md costs 5–10 minutes to regenerate; a wrong Scope Contract costs 10 seconds to correct here. Per-category 變更清單 catches "you forgot to replace X". Multi-hop 流程鏈 catches "you didn't trace this change all the way to its terminal consumers" — the format-mismatch class of bug that typically only surfaces at Phase 2 review round 2 or later.

   **One correction round only**: if the user pushes back, incorporate the corrections and proceed directly to Step 7 — do NOT loop on this checkpoint. More than one round of correction is a signal that Step 6e was under-specified; treat that as self-feedback for future runs, not a reason to keep asking.

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
   - `subagent_type`: `"sdd:architect"`
   - **CRITICAL — enforce structured trade-off analysis**: The architect's dispatched prompt MUST include an "Analytical depth requirement" section instructing the agent, BEFORE writing design.md, to:
     1. Enumerate **2-3 candidate designs** for each major decision (domain model shape, storage / aggregate boundaries, API style, integration pattern).
     2. For each candidate, list **concrete trade-offs** (complexity, performance, reversibility, blast radius, coupling).
     3. **Explicitly justify rejections** — rejected alternatives must be named, with the reason they were ruled out (cost, mismatch with constraints, unnecessary flexibility, etc.).
     4. Do NOT skip straight to "the answer". The comparison IS the design work — a single-option design.md is treated as incomplete.

     Rationale: structural enforcement of exhaustive reasoning, with an auditable trail of rejected alternatives, is the primary safeguard against a single-option design.md.
   - **CRITICAL — feed pre-collected context**: The prompt MUST include the **complete affected-files inventory from Step 5** (including the **Reference implementation pointers** found there), the proposal.md content, **all completed spec files from Step 7b**, the **full contents of `feature-spec/config.yaml`** (the `architecture` block and `hard_rules` are constraints the design MUST honor — surface `hard_rules` to the architect as non-negotiable), existing specs from `feature-spec/specs/`, and the design.md template from `templates/`. Include any file contents you already read during the codebase scan (store definitions, key interfaces, usage patterns, etc.). Do not forward the project's own docs — config.yaml is the only project context. If `config.yaml` does not exist, omit that section entirely — do not fabricate placeholder content.
   - **CRITICAL — record patterns to mirror**: Instruct the architect: "For each new component, name the existing **Reference implementation** it must mirror (from the affected-files inventory) and state the local approach to follow — data access mechanism (stored procedure / repository / query helper, never inline SQL or direct DbContext when siblings avoid it), read-query conventions, structure, naming, error handling. Design decisions must conform to how the project already does the same kind of thing; do not introduce a new pattern when a sibling pattern exists."
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

   **Why `mode: "bypassPermissions"`**: The architect agent writes ONLY to `feature-spec/changes/<name>/design.md`. Without this mode, the agent blocks on Write permission approval — the user cannot see or approve the permission prompt from a background subprocess, causing the agent to hang for minutes (often 5-10 min per Write). This is the #1 cause of slow `/propose` execution.

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

   - **Each group names its Reference implementation.** Carry the nearest-analog pointers found in Step 5 into the group: add a `Reference: <path>[, <path>]` line under the group heading (e.g. `Reference: src/Api/Orders/OrderEndpoints.cs — mirror its SP-based data access and Result error handling`). The implementing agent opens it first and mirrors its approach. Write `Reference: none (no existing analog)` when there genuinely is none.

   - **Each group MUST contain a single agent type.** This ensures each commit is a single-concern, single-layer change.
     - GOOD: `## 1. Search API and service layer` (all Backend tasks)
     - GOOD: `## 2. Search page and composables` (all Frontend tasks)
     - BAD: `## 1. User Search` (mixes Backend + Frontend + E2E → produces a mixed-concern commit)
   - **Multi-repo: each group MUST also stay within a single child repo.** A group's tasks all target files under one repo, so its commit lands atomically in that repo. A change spanning repos splits into one group per repo, wired with dependency annotations contract-first (the repo defining a shared API/type/schema runs first; consumer repos depend on it). Annotate each group's owning repo on the heading, e.g. `## 1. Search API and service layer <!-- repo: services/search-api -->`.
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

   Ready for implementation. Run `/apply <name>` to start.
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
- `config.yaml` is the first-class input for design.md generation: forward the full `config.yaml` verbatim to the architect agent in Step 7c. `hard_rules` are non-negotiable. Do not read or forward the project's own docs — config.yaml is the only project context. If `config.yaml` is missing, skip silently — the project may not have run `/init`.
- Use Traditional Chinese for artifact content (matching user's communication language)
- Code examples and technical terms remain in English
