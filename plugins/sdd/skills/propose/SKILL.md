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

   Load `${CLAUDE_PLUGIN_ROOT}/references/repo-topology.md` and run its Step 0 detection. Announce the mode.
   - **single-repo** — scan and plan against the one repo (the steps below, unchanged).
   - **multi-repo** — the change may span several child repos. The Step 5 codebase scan covers every repo the change plausibly touches; per-repo grounding is read per touched repo (Step 4); tasks are grouped so each group lands in exactly one repo (Step 7/design), ordered contract-first across repos. `feature-spec/` (the change artifacts) lives at the umbrella cwd.

1. **If no clear input provided, ask what they want to build**

   Use the **AskUserQuestion tool** (open-ended, no preset options) to ask:
   > "What change do you want to work on? Describe what you want to build or fix."

   From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.

2. **Ensure the feature-spec directory exists**

   Create `feature-spec/specs/` and `feature-spec/changes/` at cwd if missing. Do **not** auto-run `/setup` or generate `config.yaml` — config is optional. If it already exists it is read in Step 4; if not, Step 5's codebase scan is the grounding.

3. **Create the change directory**

   ```
   feature-spec/changes/<name>/
   ```

   If a change with that name already exists, use **AskUserQuestion** to ask if user wants to continue it or create a new one with a different name.

4. **Read existing context (grounding)**

   Follow `${CLAUDE_PLUGIN_ROOT}/references/grounding.md` — the canonical grounding step. In short: consult any project-knowledge skill for the working repo(s) first, then `config.yaml`, then plan to front-load external facts (done concretely in Step 7c before dispatching the architect). The rest of this step is the `config.yaml` specifics.

   - **single-repo**: read `feature-spec/config.yaml` — the grounding source. Use its `architecture` block (pattern, layers, entry_points) to ground the Step 5 codebase scan (start from the paths it points at), and treat `hard_rules` as non-negotiable constraints for the Step 6 boundary definition and design.md. If it is missing, skip silently and work from the codebase scan alone.
   - **multi-repo**: for **each child repo the change touches**, read `<repo>/feature-spec/config.yaml` if it exists (its `architecture` + `hard_rules` ground work in that repo); if a repo has none, scan that repo's code. Per the topology rules, never generate config here.
   - Do not read the project's own prose docs (CLAUDE.md, README, etc.) — config.yaml is the only curated grounding this workflow trusts.
   - **Staleness check (cheap, non-blocking)**: for each config read, test that the `architecture.layers` and `entry_points` paths still resolve on disk. If one or more do not, warn once — `⚠ config.yaml references N paths that no longer exist (<list>); it may be stale — consider re-running /setup or editing it` — then proceed using what still resolves. Never auto-edit config or block on this.
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
   - **Find the precedent for every NEW thing, per operation (MANDATORY).** For each new artifact the change introduces (endpoint, service, component, store, migration, etc.), do NOT settle for one feature-sibling. Decompose it into the technical operations it performs (DB access, DI/wiring, class/type shape, layering & file placement, error handling, logging) and record a **Reference implementation per operation** — the existing code that already does *that operation*, even if it lives in an unrelated feature. You have the full codebase in view right now; this is the cheapest place to find it. A change that restructures architecture usually has no same-job sibling, but the repo still performs each underlying operation somewhere — point to those. Only write "no precedent" for a specific operation that genuinely has none anywhere; never collapse the whole artifact to "no analog".

   **Dry-run for config-flip AND type-level changes:** When a change enables/disables rules, flags, or config that will surface new errors (e.g., enabling ESLint rules, turning on `strict` mode, enabling a feature toggle that changes validation), OR when a change modifies type signatures that affect downstream consumers (e.g., removing index signatures, changing type defaults like `any` → `unknown`, narrowing union types, making properties optional via `Partial<T>`), do NOT estimate the violation count by grepping patterns. Instead:
   1. Temporarily apply the config/type change **in the working tree** — do NOT create or switch branches (the user manages branches; every other step honors this). If the tree has uncommitted work, `git stash` it first.
   2. Run **ALL** the project's verification and lint commands — both `verification_commands` AND `lint_commands` from `config.yaml` (or detect from `package.json` scripts). **NEVER hardcode tool-specific commands** like `npx vue-tsc --noEmit`. Type-aware ESLint rules (e.g., `@typescript-eslint/no-unnecessary-type-assertion`) can surface errors that type-check alone misses.
   3. Use that output as the authoritative affected-files inventory and violation counts
   4. Categorize errors: **in-scope** (files this change will modify) vs **out-of-scope** (downstream files for future changes)
   5. If out-of-scope errors > 0: this change has **cascade impact**. You MUST either:
      - (a) Expand scope to include all affected files (and add tasks for them), OR
      - (b) Reduce the change's aggressiveness to maintain backward compatibility (e.g., keep `any` default, keep index signature) and defer the stricter version to a later change that handles the callers
      - **Never leave out-of-scope errors for "a future change" to handle** — the current change must compile cleanly on its own.
   6. Use the exact error list to create **bounded tasks** — never write catch-all tasks like "fix all type errors". Instead, create one task per error category or per file group (e.g., "Add optional chaining for 5 nullable properties in stores/main.ts", "Add type parameters to 3 Form.post calls")
   7. Revert the temporary changes: `git restore .` / `git checkout -- .` (and `git stash pop` if you stashed in step 1). Never leave the change committed or a branch created — if interrupted mid-dry-run, the change is uncommitted working-tree edits and is fully revertible with the same commands.

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

   **Representation-change egress trace (MANDATORY when a value's format changes).** When the change alters the *representation* of any value — enum rename, string/format change, type change, unit change, serialization shape — that value almost always leaves the module. Trace every **egress site** where it crosses a boundary you do not fully control: outbound API request bodies / query params / route params / headers, cookies, persisted storage, URL and asset paths, and third-party / CDN calls. Grep the value/symbol across the codebase and follow it to the wire — do NOT assume "internal rename, no external effect". For EACH egress site record: does the external contract change in lockstep, or must the value be **converted back at the boundary** (anti-corruption layer)? A change that renames an internal enum/format but keeps the old wire format at the backend is the single most common false-"no API impact": the correct fix is a boundary converter at each egress, NOT propagating the new format outward. Record the egress inventory and each conversion point in `design.md` (Affected Files + `## External Boundary Contracts`) and in `proposal.md` Impact. **You may NOT write "API: 無/none" or "Backend: 無/none" in Impact until this trace is done and shows zero egress.**

6. **Clarify requirements and define feature boundaries**

   Before generating any artifact, analyze the user's description and proactively clarify:

   **a. Identify ambiguities and surface assumptions** — vague scope, undefined behavior, missing edge cases. **Enumerate every implicit assumption you are making** as you interpret the request (e.g., "assuming admin role is required", "assuming pagination reuses the existing pattern", "assuming no backfill is needed for existing data"). Hidden assumptions in your reasoning become silent bugs in design.md — externalize them so the user can correct them.

   **b. Define boundaries (multi-dimensional)** — draw scope on five axes, not just features:
   - **Feature**: in-scope capabilities vs out-of-scope (separate changes)
   - **Integration (boundary contracts — bidirectional)**: identify every boundary this change touches and, for each, list **both sides + all consumers**, then decide per boundary: change in lockstep / add a conversion layer / version with a compatibility transition. Do this before designing — the boundary is drawn first, then both sides are designed across it. Two directions, same discipline:
     - **You own the boundary and change its contract** (an API you expose, an event/message schema, a shared type, a DB column): enumerate **every consumer** and verify each still works. If a consumer cannot change in lockstep (other repo, external client, in-flight data/messages), you MUST version or keep a backward-compatible transition — never break a consumer silently. The Step 5 codebase scan (single-repo) or per-repo scan (multi-repo) is where you find the consumers; a **semantic** change types don't catch (field meaning, status code, runtime nullability, default value) still needs this — do not lean on the type dry-run alone.
     - **You cross a boundary you do not own** (send a value to a backend/third-party, write a URL/asset path, set a cookie): this is the **representation-change egress trace** from Step 5 — convert at the boundary to the format the other side expects (anti-corruption layer).

     Record the per-boundary decisions in `design.md` `## External Boundary Contracts`.
   - **Data**: tables/collections in scope, migration/backfill expectations. **When a schema / persisted-data shape changes** (new/renamed/dropped column, table, index, or a type/format change to stored data), the design MUST state a **backfill plan** for existing rows and a **rollback plan** — record them in `design.md` `## Data Migration & Rollback`. Also decide **idempotency** for any operation that can be retried or redelivered (client retry, at-least-once queue/webhook) — the reviewers flag non-idempotent mutation paths.
   - **NFR budget**: performance targets, security requirements, UX constraints that apply to THIS change
   - **Reversibility**: how hard is this decision to change later (easy / hard / irreversible) — drives how careful the upfront clarification needs to be. **Safe-by-default rule (irreversible / destructive operations):** when the change performs an action with no undo — bulk deletion, mass external mutation (e.g. patching/removing remote resources), data purges — the *proposed default* MUST be the safe one: dry-run / preview / explicit-confirm, with the destructive behavior as an opt-in the caller consciously requests (e.g. `dryRun` defaults to `true`). This is the design you propose in the Scope Contract from the start — NOT a hardening to be added later by review. Do not let caller convenience ("they'll just call it directly") set a destructive default; identifying the risk is not enough, the default must encode the safe choice.

   **c. Assess size** — two directions:

   - **Too large** — if 3+ independent capabilities or 15+ tasks, suggest splitting. Each split should be reviewable in one sitting, self-contained, and focused on one concern. Example: "Add user management" → `add-user-registration`, `add-user-profile`, `add-user-roles`.
   - **Too small for full spec (downgrade suggestion)** — if the change is a single capability, single layer, and roughly ≤5 tasks with no cross-cutting integration, the full `/propose` → `/apply` spec ceremony (4 artifacts, architect dispatch, validation) is likely overkill. Say so in one line and offer the lighter path: **`/quick <description>`** (inline analysis + review, no spec files), or just a direct edit if the user is at the keyboard. Spec artifacts earn their cost mainly when the work is large, spans sessions/people, or must be handed off — so still proceed with full `/propose` if the user wants that durable record; this is a suggestion, not a gate. Ask once via the Step 6e message (or proceed with full spec if they already signalled they want it).

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

   This gate is also packaged as the standalone `scope-contract` skill (`skills/scope-contract/SKILL.md`) — the canonical definition of the format, depth rule, and rationale. The inline copy below is kept so `/propose` is self-contained; when editing the rules, keep both in sync (or trim this to a reference).

   After the user answers 6e (or immediately, if 6e had no Questions), synthesize everything into a **Scope Contract** — a single **現在 → 改成 (Before → After)** list where every modified area is shown as how it works now versus how it works after. Show it back as a regular chat message (NOT AskUserQuestion — this is a final sanity check, not an open clarification round). Then wait for the user's reply.

   **Depth scales with the item — this is the core rule:**
   - **Single-hop swap or bulk replacement** (swap function A for B, batch import changes, replace one helper with a library) → **ONE line**: `<area>：現在 X → 改成 Y`. Do NOT inflate these into multi-step chains; padding a one-liner is the #1 way the report loses focus.
   - **A change that alters several execution-path steps** (a login/locale-decision flow, a value-format change that cascades downstream) → **trace it as a full behavior chain**: write the 現在 chain and the 改成 chain step-by-step and mark the diff. These are the only items that earn the expanded form.

   The contract MUST let the user scan top-to-bottom and verify intent without reading code. **Concise first — highlight the key/high-risk items, keep everything else to one line.** The single most common cause of Phase 2 review blockers is **a downstream consumer being missed** — a callsite not updated (refactor) or a flow step unaccounted for (new feature). The expanded behavior chains exist specifically to surface those multi-hop ripples; the one-liners keep the bulk readable.

   ```
   ## 確認一下（每處 現在 → 改成，不對就講哪條，OK 就 go）

   <change-name>

   ### 變更（現在 → 改成）

   - <區域 / 行為 1>：現在 <how it works now> → 改成 <how it works after>      ← 單跳 / 大量取代：一行
   - <區域 / 行為 2>：現在 ... → 改成 ...

   <只有「真正改到幾條執行路徑」的變動才展開成完整行為鏈：>

   **【<關鍵流程名>】**
   - 現在：A → B → C
   - 改成：A → B′ → C′（標出差異）

   ### 鎖定假設
   - <假設 1>
   - <假設 2>

   ### 不做：<one line; 省略 if 無>
   ### 影響範圍 / Reversibility：<one line; 省略 if "無">
   ```

   **Format rules:**

   - **Concise first, key points stand out.** Whole contract SHOULD stay under 25 lines. Most items are one line; only the genuinely multi-step flows expand. Writing too much buries the items the user actually needs to check.
   - **Concrete names are fine when the name IS the change** — a function-for-function swap, or a value-format migration (`ZH_CN` → `zh-CN`), reads clearest with the actual names/values. Use a concept name instead when a raw symbol would be noise (say "「語言 → 後端數字編號」橋接表" not the constant's identifier). **Never** write `file:line` or import paths — that detail lives in design.md after approval.
   - **Format / shape changes MUST get the expanded chain (most error-prone)** — when a change alters the FORMAT or SHAPE of data flowing through the system (enum value renamed, cookie format change, type widened), it MUST be an expanded behavior chain with every downstream consumer traced (cookie / i18n / asset filenames / API body / string-literal comparisons / backend mapping keys / …). Reviewers miss these because they read for "what changes" not "what downstream assumes about the old shape".
   - **New-feature user flows need a terminal state** — an expanded user-flow chain MUST end at a user-visible result (success page / email sent / data persisted / error message), not an internal handoff. A flow that stops mid-system leaves a feature half-built.
   - **Use action verbs in expanded chains, readable for a non-engineer** — "元件拼 CSS class 名" not "`:class` binding"; "後端產生 token 寫 DB" not "`TokenService.generate()`".
   - **Length signal**: if the contract can't fit under ~25 lines even after collapsing one-liners, the change is too large — split into sub-changes (return to 6c/6f).
   - **Split changes**: one combined Scope Contract, each sub-change under its own heading, ordered by the dependency chain from Step 6f.

   **Purpose**: catches interpretation mismatches BEFORE the architect agent writes design.md. A wrong design.md costs 5–10 minutes to regenerate; a wrong Scope Contract costs 10 seconds to correct here. The one-line 現在 → 改成 entries catch "you forgot to replace X" or "you changed it to the wrong thing"; the expanded behavior chains catch "you didn't trace this change to its terminal consumers" — the format-mismatch class of bug that otherwise surfaces only at Phase 2 review round 2+.

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

   **Front-load external facts first (orchestrator).** Before dispatching, identify every fact the design will hinge on that is NOT obtainable from the repo or specs — a runtime/production config value (feature flags, rollout rates, limits), a cross-repo/service contract, live infrastructure state. For each one, **before you assume a value or let a plausible default stand, check whether your available tools can look it up** — a connected MCP server, a query/lookup tool, a project-knowledge skill — and **if such a tool exists you MUST use it rather than guess** (lookup tools often have no auto-trigger, so you must reach for them deliberately). Resolve what you can NOW, feed the values into the architect's context below, and record them in `design.md` with how/when they were obtained. sdd names no specific tool — use whatever the environment exposes; this front-loading is the primary thing that keeps the architect from designing on a guessed value. Anything you genuinely cannot resolve, leave for the architect to raise as a `NEEDS:` (handled in step d).

   Dispatch the **architect agent** — use the **Agent** tool with `run_in_background: true` and `mode: "bypassPermissions"`:
   - `subagent_type`: `"sdd:architect"`
   - **CRITICAL — trade-off analysis scaled to stakes (progressive depth)**: The architect's dispatched prompt MUST include an "Analytical depth requirement" section. The depth of analysis is **conditional on each decision's stakes — do NOT apply the full multi-candidate treatment to every decision**, that is the design-level equivalent of gold-plating (wasted tokens + a bloated design.md). Instruct the agent, BEFORE writing design.md, to first classify each major decision (domain model shape, storage / aggregate boundaries, API style, integration pattern) as **high-stakes** or **routine**:
     - **High-stakes** = irreversible or hard-to-reverse, high blast-radius, or the constraints genuinely admit materially different approaches with real trade-offs. For these, do the full treatment:
       1. Enumerate **2-3 candidate designs**.
       2. For each, list **concrete trade-offs** (complexity, performance, reversibility, blast radius, coupling).
       3. **Explicitly justify rejections** — name each rejected alternative and why (cost, mismatch with constraints, unnecessary flexibility, etc.).
     - **Routine** = reversible, low blast-radius, or effectively determined by an existing project convention / the named Reference implementation. For these, **one line stating the choice and why is enough** — do NOT manufacture 2-3 candidates to compare. Naming the convention/Reference it follows IS the justification.

     The bar: a high-stakes decision presented as a single option with no alternatives considered is incomplete; a routine decision padded into a 3-candidate comparison is over-engineered. Match the analysis to the decision. (Reversibility was already assessed per area in the Step 6b Scope Contract — reuse that classification here.)
   - **CRITICAL — feed pre-collected context**: The prompt MUST include the **complete affected-files inventory from Step 5** (including the **Reference implementation pointers** found there), the proposal.md content, **all completed spec files from Step 7b**, the **full contents of `feature-spec/config.yaml`** (the `architecture` block and `hard_rules` are constraints the design MUST honor — surface `hard_rules` to the architect as non-negotiable), existing specs from `feature-spec/specs/`, and the design.md template from `templates/`. Include any file contents you already read during the codebase scan (store definitions, key interfaces, usage patterns, etc.). Do not forward the project's own docs — config.yaml is the only project context. If `config.yaml` does not exist, omit that section entirely — do not fabricate placeholder content.
   - **CRITICAL — record patterns to mirror, per operation**: Instruct the architect: "For each new component, list the technical operations it performs (data access, DI/wiring, class/type shape, layering & file placement, error handling, logging) and, for each, name the existing **Reference implementation** it must mirror (from the affected-files inventory) plus the local approach to follow — data access mechanism (stored procedure / repository / query helper, never inline SQL or direct DbContext when the project avoids them), read-query conventions, DI wiring, class shape, file placement, naming, error handling. Anchor each operation to how the project already performs *that operation*, not to the nearest similar feature. A restructuring change often has no same-job sibling — that is not a reason to invent a new style; point each operation at existing code that performs it. Do not introduce a new pattern when an existing one covers the operation."
   - **CRITICAL — specs are constraints**: Explicitly instruct the architect: "The spec THEN clauses are acceptance criteria that your design MUST satisfy. If you believe a spec THEN clause should be different, do NOT silently override it. Instead, mark it as `CONFLICT:` in your design.md with your reasoning, so the orchestrator can resolve it with the user."
   - **CRITICAL — external facts → NEEDS, never guess**: Per `skills/agent-guidelines/SKILL.md` (*Signaling Unknowns*), instruct the architect: "If a design decision depends on a fact not present in the context provided to you — a runtime/production value, a contract owned by another repo/service, live infrastructure state — do NOT guess or quietly pick a default. Emit a `NEEDS:` line and stop that decision; the orchestrator will resolve it and resume you." (`NEEDS` = external fact or unverifiable in-repo name; `CONFLICT` = spec disagreement; `BLOCKED` = non-external blocker — the three signals defined in agent-guidelines.)
   - **Do NOT tell the architect to re-scan the codebase.** Explicitly instruct: "All context is provided below. Do NOT re-read files or re-scan the codebase. Go straight to writing design.md."
   - Instruct the architect to write `design.md` directly to `feature-spec/changes/<name>/design.md`

   The architect agent will produce:
   - Context, Goals/Non-Goals, Decisions (alternatives considered for high-stakes decisions; one-line choice for routine ones), Risks/Trade-offs
   - **Domain Model (DDD)**: Bounded contexts, aggregates (root + children + invariants), value objects, domain events
   - **API Contract**: Every endpoint (METHOD, path, request/response schema, status codes, auth)
   - **Shared Types**: TypeScript interfaces and C# DTOs as integration contract
   - Each high-stakes decision with justification and rejected alternatives; routine decisions with a one-line rationale (naming the convention/Reference followed)
   - Risks with mitigation strategies
   - **CONFLICT markers** (if any) — where the architect disagrees with a spec THEN clause
   - **NEEDS markers** (if any) — where the architect is blocked on an external fact it could not obtain from the provided context

   **Why `mode: "bypassPermissions"`**: The architect agent writes ONLY to `feature-spec/changes/<name>/design.md`. Without this mode, the agent blocks on Write permission approval — the user cannot see or approve the permission prompt from a background subprocess, causing the agent to hang for minutes (often 5-10 min per Write). This is the #1 cause of slow `/propose` execution.

   **d. Resolve conflicts and cross-validate**

   **WAIT for the architect agent to complete before proceeding.** Do NOT write design.md yourself — the architect agent has a specialized system prompt with design checklists, trade-off frameworks, and structured analysis that you do not have access to. Its output will be more thorough than what you can produce. If the agent is taking long, check its progress — do NOT override it by writing the file yourself.

   Once the architect agent completes, read the generated `design.md`:

   **d0. Resolve NEEDS markers (resume the architect)**: If the architect emitted any `NEEDS:` lines (or wrote `NEEDS` markers into design.md), it is paused on an external fact, not finished. Resolve each using whatever tools the environment provides (connected MCP servers, lookup tools, project-knowledge skills, or the user), then **resume the SAME architect with `SendMessage`** — its context is intact, so do NOT re-dispatch a fresh architect. Wait for it to finish design.md with the facts incorporated. If a resolved fact invalidates a spec assumption, note it for d2. Only proceed once no NEEDS remain. (If a NEEDS is genuinely unresolvable, surface it to the user before continuing.)

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

   - **Each group names its Reference implementations, per operation.** Carry the per-operation precedent pointers found in Step 5 into the group: add a `Reference:` line under the group heading mapping each operation to the code that already does it (e.g. `Reference: DB access → src/Api/Orders/OrderRepository.cs (SP-based); DI → src/Api/Startup.cs; error handling → Result pattern in OrderService.cs`). The implementing agent opens these first and mirrors each operation's approach. Only mark a specific operation `none` when it genuinely has no precedent anywhere — never write `Reference: none` for the whole group just because no same-job sibling exists.

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
   - **Dependency annotations**: if a group depends on another group's output (e.g., frontend needs backend API types), annotate with `<!-- depends: N[, M...] -->` on the group heading line. The orchestrator topologically sorts these into a **linear execution order** (writes are single-threaded — groups run one at a time, in dependency order; contract-defining groups first).
     - Annotate dependencies wherever one group consumes another's output, so the order is correct (e.g., backend contract before frontend that calls it).
     - In multi-repo mode, groups bound to *different* child repos may run in parallel; annotate cross-repo dependencies contract-first.
   - **Tag each task with an agent type** in parentheses:
     - `(Backend)` → dotnet-engineer (includes unit tests, TDD style)
     - `(Python)` → python-engineer (FastAPI, data pipelines, ML, LLM, monitoring)
     - `(Frontend)` → vue-engineer (includes unit tests, TDD style)
     - `(Electron)` → electron-engineer (main process, IPC, preload, packaging)
     - `(Godot)` → godot-engineer (GDScript/C#, scenes, nodes, autoloads, signals, game systems; includes unit tests, TDD style)
     - `(Database)` → database-engineer (schema, migration, indexing)
     - `(DevOps)` → devops-engineer (Docker, CI/CD, K8s)
     - `(Performance)` → performance-engineer
     - `(Security)` → security-engineer (security audit, hardening)
     - `(Documentation)` → technical-writer (API docs, changelog, ADR)
     - `(E2E)` → qa-engineer (Playwright E2E tests for AC verification)
   - The orchestrator dispatches **one agent per group**, sequentially in dependency order on the current branch (single-writer). Each group's agent reads the prior groups' committed code.
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
   - **Cross-group file collision (MANDATORY for refactors / multi-consumer changes):** Using the Step 5 affected-files inventory, derive the set of files each group actually edits — including the expansion of catch-all task wording like "rewrite all N consumers" (grep the real paths, do NOT trust the prose count). Intersect every pair of group file-sets. **Any file edited by 2+ groups MUST have those groups on a dependency chain** (`<!-- depends: ... -->`) so their edits to that shared file land in a deterministic order, with the contract-owning group first. Single-repo writes are fully serialized so there is no concurrent clobbering, but a missing dependency can still let the groups run in the wrong order (a consumer edited before the contract it depends on). In multi-repo mode the same file cannot be shared across repos, so collisions only arise within a repo — where serialization already applies; the dependency just fixes the order.

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

   In **no-git** mode (Step 0 detected no repo), skip this commit entirely — leave the artifacts on disk under `feature-spec/changes/<name>/` and tell the user they are un-committed. Otherwise, stage and commit all generated artifacts following the `conventional-commits` skill (`skills/conventional-commits/SKILL.md`):

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
- If two groups modify the same file, add a `<!-- depends: N -->` annotation so their edits land in a deterministic order (writes are serialized single-writer; the dependency fixes which group goes first)
- Every spec requirement MUST have SHALL/MUST and at least 2 WHEN/THEN scenarios (happy path + edge case)
- Proactively clarify ambiguities and define feature boundaries BEFORE generating artifacts — do NOT guess when scope is unclear
- Ask all clarification questions in one structured message, not one at a time
- Verify each artifact file exists after writing before proceeding to next
- `config.yaml` context and rules are constraints for YOU, not content for artifact files
- `config.yaml` is the first-class input for design.md generation: forward the full `config.yaml` verbatim to the architect agent in Step 7c. `hard_rules` are non-negotiable. Do not read or forward the project's own docs — config.yaml is the only project context. If `config.yaml` is missing, skip silently — the project may not have run `/setup`.
- Use Traditional Chinese for artifact content (matching user's communication language)
- Code examples and technical terms remain in English
