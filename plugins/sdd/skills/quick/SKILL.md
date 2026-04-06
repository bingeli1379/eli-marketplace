---
name: quick
description: >
  Quick task execution with orchestrator analysis but no spec artifacts.
  Use when the user has small-to-medium tasks and wants agent team dispatch
  without the full propose → validate → apply ceremony.
user-invocable: true
---

Lightweight alternative to the full `/propose` → `/apply` pipeline. The orchestrator **analyzes the task inline** (similar to propose) — no spec files are written to disk. For **trivial / simple** work it implements the change **itself on the main thread** (it is the single writer); for **medium / complex** work it dispatches implementation agents **sequentially** (single-writer). A read-only review pass (review + security, plus QA for bigger work) always follows.

Best for: bug fixes, small features, refactors, chores — tasks where full spec ceremony is overkill but you still want the agent team's specialization and quality gates.

**Input**: A task description (e.g., `/quick fix the login redirect loop` or `/quick add dark mode toggle to settings page`).

**Steps**

0. **Detect repo topology (MANDATORY first)**

   Load `${CLAUDE_PLUGIN_ROOT}/references/repo-topology.md` and run its Step 0 detection. Announce the mode. In **multi-repo** mode: the scan covers every child repo the task touches; per-repo grounding is read per touched repo (Step 2); each dispatched agent is bound to one child repo and does its work + commits inside that repo (`git -C <repo> ...`); cross-repo work is ordered contract-first.

1. **Get the task description**

   If no description is provided, use **AskUserQuestion** (open-ended) to ask:
   > "What do you want to do? Describe the task."

   Do NOT proceed without a clear task description.

2. **Read project context (grounding)**

   Follow `${CLAUDE_PLUGIN_ROOT}/references/grounding.md` — consult any project-knowledge skill for the working repo(s) first, then the curated `config.yaml` below, then resolve external facts with available lookup tools rather than guessing.

   - **single-repo**: read `feature-spec/config.yaml` — the grounding source (tech stack, lint commands, and the `architecture` block: pattern, layers, entry_points, hard_rules). Use it to ground the Step 5 scan and forward it to every worker agent in Step 6; `hard_rules` are non-negotiable.
   - **multi-repo**: for each child repo the task touches, read `<repo>/feature-spec/config.yaml` if it exists; else scan that repo's code. Forward each repo's grounding to the agents working in it.
   - Do not read the project's own prose docs — config.yaml is the only curated grounding this workflow trusts.
   - **Staleness check (cheap, non-blocking)**: for each config read, test that its `architecture.layers` / `entry_points` paths still resolve; if some do not, warn once (`⚠ config.yaml may be stale — N paths missing`) and proceed with what resolves. Never auto-edit or block.
   - `config.yaml` is optional — if a repo has none, skip silently and rely on the codebase scan

3. **Confirm current branch**

   Use the current branch as-is. Do NOT create or switch branches.
   Announce: "Branch: **<current-branch>**"
   **Multi-repo**: there is no single branch — announce the current branch of each child repo the task will touch (`git -C <repo> branch --show-current`). All commits for a repo's tasks land on that repo's current branch.

4. **Pre-lint and commit (clean slate)**

   In **no-git** mode (Step 0), skip this entire step — there is no repo to commit to.

   First, check `${CLAUDE_PLUGIN_ROOT}/company-conventions.md` for pre-lint skip rules. If the current project matches a skip condition (e.g., .NET project), skip this entire step silently.

   Otherwise, if `lint_commands` are configured in `feature-spec/config.yaml`:
   1. Run all lint commands to fix pre-existing formatting issues
   2. If lint produced changes: stage and commit with `chore: pre-lint cleanup before quick`
   3. If no changes, skip silently

5. **Analyze the task (inline propose)**

   This is the core difference from `/apply`. Instead of reading spec files, you **perform the analysis yourself** — similar to what `/propose` does, but entirely in-memory without writing any files.

   **ZERO MISSES — exhaustive codebase scan (MANDATORY):**
   Scope specified → scan every file within it. No scope → scan entire project.
   Use Glob to list ALL files, read/inspect each that could be affected. Build affected-files inventory (file + WHY).

   **a. Scope analysis:**
   - What is the task trying to achieve?
   - Which layers are affected? (Frontend, Backend, Database, DevOps, etc.)
   - What are the key design decisions? (API shape, data model changes, UI approach)
   - What are the acceptance criteria? (When X happens, then Y should be the result)
   - **External facts → look up, don't guess:** if a decision hinges on a runtime/production value (feature flag, rollout rate, limit), a cross-repo/service contract, or live infra state not in the repo, check whether your available tools can resolve it (a connected MCP server, a query/lookup tool, a project-knowledge skill) and **use it before assuming a value** — lookup tools have no auto-trigger, so reach for them deliberately. What you genuinely can't resolve becomes a `NEEDS` a dispatched agent raises later.

   **b. Task breakdown:**
   - Break the task into discrete subtasks
   - Group by reviewable unit — each group = single agent type + single concern (same as tasks.md format)
   - Tag each subtask with an agent type: `(Backend)`, `(Python)`, `(Frontend)`, `(Godot)`, `(E2E)`, `(Electron)`, `(Database)`, `(DevOps)`, `(Performance)`, `(Security)`, `(Documentation)`
   - Add `<!-- depends: N -->` annotations if groups have dependencies
   - **Writes are single-threaded** — implementation groups run **sequentially**, one agent at a time on the current branch, each reading the prior groups' committed work. Use `<!-- depends: N -->` to fix the order wherever one group consumes another's output (contract-defining group first). To order shared-file edits correctly, derive the set of files each group actually edits from the Step 5 scan — **including the expansion of catch-all wording like "rewrite all N consumers": grep the real paths, do NOT trust the prose count** — and add a dependency between any two groups touching the same file.
   - Follow TDD structure for Backend/Frontend tasks when appropriate (write test → implement)
   - Number tasks: `1.1`, `1.2`, etc.

   **c. Complexity judgment:**
   - **Trivial / Simple** (one layer, one concern, ~≤5 files, mechanical or near-mechanical, no cross-layer dependency) → **orchestrator implements INLINE on the main thread** (you are already the single writer), then review. Do NOT dispatch a background specialist for this — it is pure overkill and the dominant failure mode is a background worker going idle mid-task without committing. If the task is trivial enough that the user could just have written it directly, say so in one line and proceed inline.
   - **Medium** (2-3 groups, cross-cutting) → sequential single-writer dispatch → review
   - **Complex** (full pipeline): new module/feature → full 4-phase pipeline (sequential implementation)

   **d. Identify ambiguities and unknowns:**
   - Are there vague requirements? ("improve" → improve what exactly?)
   - Missing edge case handling? (empty input, concurrent access, error states)
   - Unclear integration points with existing code?
   - Design decisions that could go multiple ways?

   **e. If ambiguities exist — ask the user ONCE:**

   Use **AskUserQuestion** with a structured summary that follows the Scope Contract shape (canonical definition: the `scope-contract` skill, `skills/scope-contract/SKILL.md`), plus an explicit Questions block. Ask ALL questions in ONE message:

   ```
   ## Quick Task: <summary>

   **Scope:** <affected layers>   **Complexity:** <Simple/Medium/Complex>

   ### 變更（現在 → 改成）

   - <區域 / 行為 1>：現在 <how it works now> → 改成 <how it works after>   ← 單跳 / 大量取代：一行
   - <區域 / 行為 2>：現在 ... → 改成 ...

   <只有真正改到幾條執行路徑的變動才展開成完整行為鏈：>
   **【<關鍵流程名>】**
   - 現在：A → B → C
   - 改成：A → B′ → C′（標出差異）

   ### 鎖定假設
   - <假設 1>

   ### Questions (need your input)
   1. <specific question about unclear behavior>
   2. <specific question about edge case or design choice>

   ### Planned Tasks (pending your answers)
   - 1.1 (Backend) <task description>
   - 1.2 (Frontend) <task description>
   ...
   ```

   After the user responds, incorporate their answers into the plan.

   **f. If NO ambiguities — present the plan and dispatch immediately:**

   If the task description is clear and unambiguous, skip the question step. Show the same Scope Contract shape (without the Questions block) plus tasks + agents, then dispatch:

   ```
   ## Quick Task: <summary>

   **Scope:** <affected layers>   **Complexity:** <Simple/Medium/Complex>

   ### 變更（現在 → 改成）

   - <區域 / 行為 1>：現在 <how it works now> → 改成 <how it works after>   ← 單跳 / 大量取代：一行
   - <區域 / 行為 2>：現在 ... → 改成 ...

   <只有真正改到幾條執行路徑的變動才展開成完整行為鏈：>
   **【<關鍵流程名>】**
   - 現在：A → B → C
   - 改成：A → B′ → C′（標出差異）

   ### 鎖定假設
   - <假設 1>

   ### Acceptance Criteria
   - WHEN <condition> THEN <expected result>
   - WHEN <condition> THEN <expected result>

   ### Tasks
   ## 1. <Group Name>
   - [ ] 1.1 (Backend) <task description>
   - [ ] 1.2 (Frontend) <task description>
   ...

   ### Agents to Dispatch
   - <agent-1>: <task count> tasks
   - <agent-2>: <task count> tasks

   Dispatching now.
   ```

   **Format rules (same as `/propose` Step 6g)**:
   - **Depth scales with the item**: single-hop swap / bulk replacement → ONE `現在 X → 改成 Y` line (do NOT inflate); only a change that alters several execution-path steps gets an expanded 現在/改成 behavior chain.
   - **Concise first, key points stand out** — most items are one line; only genuinely multi-step flows expand.
   - Concrete names are fine when the name IS the change (function swap, value-format `ZH_CN`→`zh-CN`); use a concept name when a raw symbol is noise; never `file:line` or import paths.
   - **Format / shape changes MUST get the expanded chain** with all downstream consumers traced (cookie / i18n / filenames / API body / string comparisons / backend mapping keys / …).
   - User-flow entries (new feature) MUST end at a user-visible terminal state.
   - Whole contract SHOULD stay under 20 lines for quick mode (smaller cap than full propose — if exceeded, the task is too big for quick and SHOULD be promoted to `/propose`).

   **Decision rule**: Only ask when there are genuine unknowns that would lead to wrong implementation. If you can make a reasonable decision, make it and note it — don't ask just to be safe.

6. **Become the orchestrator and dispatch**

   Read `${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md` to load the orchestrator role. You are now the orchestrator.

   **Agent Prompt Template** — compose each worker agent's prompt with:

   ```
   You are working on a quick task: "<task summary>"

   ## Your Role
   [auto-loaded by dispatching `subagent_type` (see `${CLAUDE_PLUGIN_ROOT}/references/agent-routing.md`) — do NOT read/embed the agent file. Only the absent-pack fallback embeds the routing-table brief into a `general-purpose` dispatch.]

   ## Mandatory Checklists
   [include content of skills/engineering-checklist/SKILL.md for ALL agents]
   [include content of skills/frontend-checklist/SKILL.md for Frontend/Electron/review agents]

   ## Project Context
   [full contents of feature-spec/config.yaml if it exists — tech stack, architecture block (pattern, layers, entry_points), and hard_rules. hard_rules are non-negotiable. This is the only project context; omit the section if config.yaml is missing.]

   ## Design Decisions
   [from your inline analysis in step 5]

   ## Acceptance Criteria
   [from your inline analysis in step 5]

   ## Your Tasks
   [specific tasks for this agent from step 5]

   ## Lint Commands (from config.yaml)
   [lint_commands list, or "none configured", or "skipped per company-conventions.md" if skip rule matches]

   ## Instructions
   - Implement each task in order
   - Follow the design decisions — do NOT deviate
   - **Implementation Protocol — MUST follow when modifying existing code:**
     1. **Read** — Read surrounding code (same file + similar files in same directory) to identify existing conventions (naming, patterns, error handling style)
     2. **Look up** — If the change involves framework API usage or pattern choices, use context7 (resolve-library-id → query-docs) to check the current recommended approach
     3. **Decide** — Choose approach by priority: project convention > official recommendation > your own judgment. Check convention first, *then* prefer the simplest option that matches it (standard library / native platform feature / an already-installed dependency over new custom code or a new dependency). Never reach for a leaner-but-foreign pattern over an established local one, and never trade away correctness, trust-boundary validation, security, or accessibility for brevity.
     4. **Implement** — Write the code
     5. **Verify** — After implementing, confirm: does the new code match surrounding style? Did you introduce any inconsistent patterns?
   - **CRITICAL — Committing is EXPLICITLY REQUIRED by the user as part of this workflow. You are authorized and expected to commit after every task. This is NOT optional.** (**No-git mode** — only when Step 0 detected no git repo: there is nothing to commit to, so implement directly and skip every per-task commit; the user commits later. The rest of this clause assumes a git repo is present.) After completing each task, you MUST:
     1. Stage all changed files with `git add` (specify files by name)
     2. Run all lint commands listed above (if any) — stage any changes they produce
     3. Commit following the `conventional-commits` skill (`skills/conventional-commits/SKILL.md`). Format: `<type>[optional scope]: <task-number> <description>` (e.g., `fix: 1.1 resolve login redirect loop`)
   - Do NOT batch multiple tasks into one commit — one commit per task
   - After the commit, report back: "DONE: <task-number> <task-description>"
   - **Completion contract — do NOT end your turn early.** You are NOT finished until **every** assigned task is committed and you have printed a `DONE:` line for each. Do NOT stop to "report progress" and wait — complete all your tasks within this turn. The ONLY valid early stops are `NEEDS:` / `CONFLICT:` / `BLOCKED:`. Going idle or yielding without one of {all tasks DONE, NEEDS, CONFLICT, BLOCKED} is a protocol violation, not a pause — the orchestrator treats it as a failed dispatch and re-dispatches.
   - Only add code comments for business logic that is not obvious from the code
   - **Signaling a genuine stop (`NEEDS` / `CONFLICT` / `BLOCKED`)** — follow the **Signaling Unknowns** rules in `skills/agent-guidelines/SKILL.md`. In short: do NOT guess an external fact you can't obtain from the repo + this context — commit what is safely done, emit `NEEDS: <question + why blocked + options>`, stop that task; the orchestrator resolves it and resumes you with your context intact. Aside from those signals, do NOT ask questions — if merely ambiguous, make a reasonable decision and flag it.
   - **Language**: All output and reports MUST be in Traditional Chinese. Code and code comments MUST be in English.
   ```

   **Dispatch rules (same as apply):**
   - **Trivial / Simple tier implements inline — skip dispatch entirely.** Per the complexity judgment (Step 5c), when the work is one layer / one concern / mechanical, you (the orchestrator) write it yourself on the main thread — but FIRST load the mapped specialist's `skills:` via the Skill tool so inline work keeps the same skill context (see the Trivial/Simple block under *Phase execution*). The dispatch rules below apply only to Medium / Complex tier.
   - Use the **Agent** tool with `run_in_background: true` and `mode: "bypassPermissions"` for ALL worker agents (without `bypassPermissions`, background agents hang on invisible Write permission prompts)
   - Give each agent a descriptive `name`
   - **Writes single-threaded**: dispatch implementation/fix agents **one at a time** in dependency order, each committing before the next starts. Only read-only reviewers (Phase 2) are dispatched simultaneously. (Multi-repo exception: agents in *different* child repos may run concurrently.)
   - You will be **automatically notified** when each background agent completes — do NOT poll
   - **Handling a NEEDS return**: if an agent's report contains a `NEEDS:` line, treat it as *paused awaiting an external fact*, not done. Resolve it with whatever tools/knowledge you (the orchestrator) have, then **resume the SAME agent with `SendMessage`** (context intact — do NOT re-dispatch). Because agents run in the background you can service several concurrently. `CONFLICT:` → resolve with the user; `BLOCKED:` → re-scope or re-dispatch with corrected context. See `skills/agent-guidelines/SKILL.md` → *Signaling Unknowns* for the vocabulary.
   - **Enforce analytical depth for reviewer agents only**: For `review-engineer`, `security-engineer`, and `qa-engineer` dispatches, the dispatched prompt MUST include an "Analytical depth requirement" section instructing the agent to:
     1. **Enumerate coverage BEFORE findings** — list the categories/dimensions examined:
        - `review-engineer` → architecture compliance, correctness, performance, readability, test quality
        - `security-engineer` → each applicable OWASP Top-10 category, authN/authZ, input validation, secrets/config, dependency risks
        - `qa-engineer` → every spec scenario (or every affected user-facing flow if no spec), happy path + edge cases + error paths + authorization cases (if applicable)
     2. **Confirm non-findings explicitly** — for every category examined, state the result. "No issues found in category X" is a valid outcome. Silence on a category is treated as "agent skipped it" and fails the review.
     3. **Severity-rank every finding** — `blocker` / `major` / `minor`, each with one-line rationale. Raw observations without severity are rejected.

     Do NOT apply this structure to implementation agents (Backend/Frontend/Python/Godot/Electron/Database/DevOps/Performance/Documentation) — they are executors; category enumeration produces over-engineered code. Rationale: structural enforcement of exhaustive scanning and auditable coverage is the primary safeguard.

   **Phase execution based on complexity:**

   **Trivial / Simple tasks (orchestrator implements inline — NO dispatch):**
   - **First, borrow the specialist's skills (MANDATORY — do NOT skip).** Implementing inline means you do NOT get the mapped agent's eagerly-loaded skills automatically, so load them yourself: resolve the agent file per `${CLAUDE_PLUGIN_ROOT}/references/agent-routing.md` (*Agent-file resolution* — core agents in `agents/`, pack agents via `find ~/.claude/plugins -path "*/<pack>/agents/<role>.md"`), take its `skills:` frontmatter list, and invoke each via the **Skill tool** before writing (e.g., a `(Frontend)` task → load `vue-best-practices`, `frontend-checklist`, `engineering-checklist`, `test-driven-development`; a `(Backend)` task → `dotnet-best-practices`, `clean-architecture`, `engineering-checklist`, `test-driven-development`). Then load any stack-/datastore-specific skill the task needs on demand, exactly as that agent would after its Stack Detection step. If the mapped pack is not installed, the file resolution finds nothing → load only core skills (`engineering-checklist`, `test-driven-development`, …) and note the degradation. This gives inline work the same skill context a dispatched agent would have had — without it, inline output silently loses the specialist's best-practices.
   - Phase 1: **you (the orchestrator / main thread) implement it directly** — read the reference/sibling code, write the change, run the project's verification + lint, and commit it yourself following the same per-task → squash discipline. Do NOT spawn a background implementation agent; you are the single writer. (A background specialist here is overkill and its dominant failure mode is going idle mid-task without committing.)
   - Phase 2: review-engineer + security-engineer (parallel, read-only) — still mandatory; you wrote the code, so an independent review is the safeguard.
   - Done.
   - **Note:** if the task is so small the user could have written it in a couple of edits, say so — `/quick` exists for tasks worth a review pass, not as a wrapper around a two-line change.

   **Medium tasks:**
   - Phase 1: Implementation agents **sequentially** in dependency order (contract-first)
   - Phase 2: review-engineer + security-engineer + qa-engineer (all parallel, read-only)
   - Done.

   **Complex tasks (full pipeline):**
   - Phase 1: Implementation agents **sequentially** in dependency order (then qa-engineer for E2E test writing)
   - Phase 2: review-engineer + security-engineer + qa-engineer (all parallel, read-only — code review, security review, and E2E tests run simultaneously)
   - Phase 3: technical-writer (if documentation changes needed)

   **Conditional Phase 2 reviewer — performance-engineer (all complexity levels):** if the diff touches a **performance-sensitive surface** (new/changed API endpoint, stored-procedure / SQL / Dapper / EF query, data-access/repository path, batch or data-pipeline job, list/report endpoint), add **performance-engineer** to the Phase 2 parallel dispatch. It does **static data-scale capacity analysis only** (no load tests/profilers; no code edits) and reports a per-path verdict (SAFE / RISKY / WILL NOT SCALE); findings are advisory recommendations routed to the owning agent. Skip for purely frontend-presentational, config, docs, or test-only diffs.

   If review, security, or QA fails: collect all issues, group by responsible agent, dispatch **fix agents sequentially** (one write agent at a time) → run a **full fresh review** from scratch with all three reviewers simultaneously (read-only; not just verify original issues — fixes may introduce new bugs) → repeat until clean (max 3 rounds). Only pause and report to user if still failing after 3 rounds.

   **Commit consolidation (per group, single-writer):**

   Per-task commits (with task-number prefixes) land directly on the branch. Squash **each group as it completes** (before dispatching the next group), so the next group's agent reads a clean history — matching `/apply`'s final commit style. **Multi-repo**: run this inside each child repo that received commits (`git -C <repo> ...`).

   1. Before dispatching the group's agent, capture the base: `GROUP_BASE=$(git rev-parse HEAD)`
   2. After the agent completes, count its per-task commits: `git log --oneline $GROUP_BASE..HEAD`
   3. If > 1 commit: `git reset --soft $GROUP_BASE` then `git commit` with a clean conventional commit message following `conventional-commits` skill rules — **NO task numbers** (e.g., `refactor(enum): rename lowercase enum objects to PascalCase`)
   4. If only 1 commit: `git commit --amend -m "<clean message>"` to remove the task number prefix
   5. Safety: verify `git diff $GROUP_BASE..HEAD` before and after squash produces identical tree

   **Commit consolidation after Phase 2 fixes:**
   Same as above — if Phase 2 fix agents produce multiple commits, squash them into one clean commit (e.g., `fix: address review and security findings`).

7. **Interactive control**

   While agents run in background, respond to user messages:
   - **"status" / "進度"** — show current phase and progress
   - **"pause" / "暫停"** — stop dispatching new agents
   - **"skip <task>"** — skip a specific task
   - **Any other message** — interpret as orchestrator instruction

   When a background agent completes, announce briefly:
   ```
   [agent-name] completed: <summary>
   Progress: N/M tasks
   ```

8. **Final report**

   After all phases complete:

   ```
   ## Quick Task Complete

   **Task:** <summary>
   **Complexity:** <Simple/Medium/Complex>
   **Progress:** M/M tasks complete

   ### Completed
   - [x] 1.1 <task description>
   - [x] 1.2 <task description>
   ...

   ### Code Review
   [APPROVED / APPROVED WITH COMMENTS]

   ### Security Review
   [SECURE / ISSUES FOUND]

   ### E2E (if applicable)
   [PASSED / FAILED / SKIPPED]

   ### Notes
   [issues encountered, decisions made, follow-up suggestions]
   ```

---

## Guardrails

- **You ARE the orchestrator** — do NOT spawn a separate orchestrator agent
- **All worker agents run in background** (`run_in_background: true`, `mode: "bypassPermissions"`)
- **No spec files are written** — analysis stays in-memory and is passed to agents via prompts
- `feature-spec/config.yaml` (when present) MUST be forwarded verbatim into every worker agent's prompt as `## Project Context`. `hard_rules` are binding. The project's own docs are never read or forwarded — config.yaml is the only project context. Skip the section silently if config.yaml is missing.
- **Execute first, report after** — show the plan and dispatch immediately, do NOT wait for user confirmation
- **Code review + security review are MANDATORY** for all complexity levels — never skip them
- If review/QA fails → auto-dispatch fix → **full fresh review** (not just verify original issues) → loop until clean (max 3 rounds) → only then pause
- **One commit per task during implementation** — atomic commits with task-number prefix. **Squashed into one clean group commit (no task numbers) after Phase 1 completes**, matching `/apply` final commit style.
- Work on the current branch — do NOT create or switch branches
- Keep the plan concise — this is quick mode, not a full spec
- **Language**: All output in Traditional Chinese. Code and comments in English.

## When to Suggest Full Spec Instead

If during analysis (step 5) you determine the task is:
- Touching 3+ independent capabilities
- Would produce 15+ tasks
- Requires significant architectural decisions
- Needs cross-team coordination

Then suggest: "This task looks complex enough for the full spec flow. Want me to run `/propose` instead?"

But still proceed if the user insists on quick mode.
