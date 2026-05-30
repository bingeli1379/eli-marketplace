---
name: apply
description: >
  Implement tasks from a spec change using Agent Team dispatch.
  Use when the user wants to start or continue implementing a change.
  Reads spec artifacts and dispatches tasks to specialized agents.
user-invocable: true
---

Implement tasks from a spec change. Reads all spec artifacts, prepares context, then **becomes the orchestrator** — the main Claude assumes the orchestrator role directly so the user can interact naturally via chat.

**IMPORTANT**: Specs are the single source of truth. If specs are incomplete, suggest running `/validate` first.

---

**Input**: Optionally specify a change name (e.g., `/apply add-user-search`). If omitted, auto-detect. An optional `dev-mode` token may appear anywhere in the arguments (e.g., `/apply add-user-search dev-mode`) — see Step 1 for parsing rules.

**Steps**

1. **Select the change and parse mode flags**

   **Mode flag parsing**: split arguments on whitespace. If any token equals `dev-mode` (case-insensitive), set the internal `DEV_MODE = true` flag and remove the token from the argument list. The remaining tokens go through normal name resolution. `DEV_MODE` defaults to `false` — the retrospective section in Step 9 is suppressed unless `DEV_MODE = true`. Plugin authors invoke with `dev-mode` to surface lessons-learned; end users get a clean report by default.

   If a name is provided (after stripping `dev-mode`), use it. Otherwise:
   - List directories under `feature-spec/changes/` (excluding `archive/`)
   - Auto-select if only one active change exists
   - If multiple, use **AskUserQuestion** to let the user choose
   - If none exist, report error: "No active changes found. Run `/propose` first."

   Always announce: "Implementing change: **<name>**" (and append "(dev-mode)" when the flag is set, so the user can confirm parsing).

2. **Confirm current branch and detect worktree-base mismatch (MANDATORY)**

   Use the current branch as-is. Do NOT create or switch branches — the user manages branches themselves.
   - Announce: "Branch: **<current-branch>**"

   **Worktree-base pre-flight check**: The Agent tool's `isolation: "worktree"` creates each worktree from the repo's **default branch** (typically `master` or `main`), NOT from the current HEAD. When HEAD is ahead of the default branch — the normal case when working on a feature branch — the worktree misses every commit already landed on the feature branch. Wave 1 commits become invisible inside Wave 2+ worktrees, producing merge-squash conflicts and stale-base implementations.

   Before Phase 1 dispatch, run:
   ```bash
   DEFAULT_BRANCH=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|origin/||' || echo master)
   HEAD_SHA=$(git rev-parse HEAD)
   DEFAULT_SHA=$(git rev-parse "$DEFAULT_BRANCH" 2>/dev/null || echo "")
   [ -n "$DEFAULT_SHA" ] && [ "$HEAD_SHA" = "$DEFAULT_SHA" ] && echo aligned || echo diverged
   ```

   - If **aligned**: set `worktree_mode = true`. Phase 1 agents dispatch with `isolation: "worktree"` normally.
   - If **diverged**: set `worktree_mode = false`. Announce to the user: "⚠ HEAD is ahead of `<default-branch>`. Worktree isolation would branch from the default tip and miss in-progress commits — falling back to **no-worktree mode** for Phase 1 (agents work on the current branch directly with per-task commits; orchestrator auto-squashes per group)." Do NOT ask the user to confirm — this is an automatic decision based on observed state.

   Pass `worktree_mode` to Phase 1 dispatch (see `orchestrator.md` Phase 1 for how it consumes the flag).

3. **Pre-lint and commit (clean slate — runs in background)**

   First, check `company-conventions.md` (in the plugin root) for pre-lint skip rules. If the current project matches a skip condition (e.g., .NET project), skip this entire step silently.

   Otherwise, if `lint_commands` are configured in `feature-spec/config.yaml`:
   1. Run all lint commands **in the background** (`run_in_background: true`) to fix any pre-existing formatting issues
   2. **Do NOT wait for lint to finish** — proceed to Step 4 (read context) and Step 5 (parse tasks) immediately
   3. **Before dispatching Phase 1 agents**, check if lint has completed:
      - If lint produced changes: stage all changed files and commit with message: `chore: pre-lint cleanup before apply`
      - If lint is still running: wait for it to finish, then commit if needed
      - If no changes, skip silently

   This ensures agents start from a clean state without blocking the orchestrator's preparation work.

4. **Read all context files**

   Read these files from `feature-spec/changes/<name>/`:
   - `proposal.md` — scope and capabilities
   - `design.md` — technical decisions and approach
   - `tasks.md` — implementation checklist
   - `specs/*/spec.md` — all capability specs (acceptance criteria)

   Also read:
   - `feature-spec/config.yaml` — project context and `lint_commands` (if exists)
   - `feature-spec/context.md` — AI-readable project map (architecture layers, domain-to-code map, entry points, hard rules, common commands). Forwarded to every worker agent in Step 7 so they make changes in the right place and respect Hard Rules.
   - `feature-spec/knowledge.md` — operational gotchas and dev tips. Forwarded to every worker agent in Step 7 so they avoid known landmines.

   `context.md` and `knowledge.md` are optional — skip silently if missing (project may not have run `/init`).

   **If any required file is missing** (proposal, design, tasks, or specs):
   - Show which files are missing
   - Suggest: "Run `/validate <name>` to check completeness, or `/propose` to generate missing artifacts."
   - Stop.

5. **Parse tasks, detect interrupted state, and show progress**

   Parse `tasks.md`:
   - Identify task groups (## headings) and their agent mapping
   - Count total tasks, completed (`- [x]`), and pending (`- [ ]`)
   - If all tasks are complete: congratulate, suggest `/complete <name>` to extract knowledge and clean up

   **Detect and recover interrupted state** (runs every time, not just after crashes):

   a. **Orphaned worktrees**: Run `git worktree list`. If worktrees exist from a previous run:
      1. For each worktree, run the project's verification commands (type-check, test) **inside the worktree** to assess health
      2. If healthy (zero new errors): merge-squash back to main, same as normal Phase 1 merge
      3. If unhealthy (new errors from incomplete work): evaluate — if close to done, dispatch an agent to fix in the worktree first; if too broken, discard the worktree (`git worktree remove --force`) and re-dispatch the group from scratch
      4. Clean up worktree branches after merge

   b. **Un-squashed per-task commits on main**: Run `git log --oneline` and look for task-number prefixed commits (e.g., `1.1`, `2.3`) that weren't squashed into group commits. If found, squash adjacent same-group commits into one clean commit per group.

   c. **Reconcile tasks.md with git history**: For each pending task (`- [ ]`), search `git log --oneline` for its task number. If a matching commit exists (on main or in a worktree), mark the task as `- [x]` in tasks.md. Report: `"Recovered N tasks from previous interrupted run"`.

   d. **Verify main health**: Run type-check and/or test on main to establish the current baseline error count before dispatching new agents.

   Display:
   ```
   ## Implementing: <change-name>
   **Progress:** N/M tasks complete [recovered K from previous run]
   **Remaining groups:**
   - Backend - Search API (3 tasks)
   - Frontend - Search Page (5 tasks)
   ```

6. **Become the orchestrator**

   Read `agents/orchestrator.md` to load the orchestrator role definition. **You MUST actually read this file every time** — do NOT rely on memory from a previous change or earlier in the conversation, as context may have been compressed. **You are now the orchestrator.** Do NOT spawn a separate orchestrator agent — you act as the orchestrator directly in the main conversation.

   This means:
   - The user can talk to you naturally at any time
   - You dispatch worker agents in the **background** (`run_in_background: true`)
   - You track progress and report back as agents complete
   - The user can ask for status, reprioritize, or give you new instructions mid-flight

   Announce to the user:
   ```
   Orchestrator ready. Dispatching agents now.
   You can talk to me anytime — ask for progress, reprioritize tasks, or adjust the plan.
   ```

7. **Dispatch worker agents (following orchestrator.md rules)**

   Follow the dispatch rules from `agents/orchestrator.md` (Spec-Driven Mode), but with these adaptations:

   **Agent Prompt Template** — compose each worker agent's prompt with:

   ```
   You are working on change "<change-name>", group "<group-heading>".

   ## Your Role
   [agent role definition from agents/<agent>.md]

   ## Project Context
   [from feature-spec/config.yaml]

   ## Project Map
   [full contents of feature-spec/context.md if it exists — architecture layers, domain-to-code map, entry points, hard rules, common commands. Hard Rules are non-negotiable invariants; do not violate them even if a task description appears to ask for it. Omit this entire section if the file is missing.]

   ## Operational Knowledge
   [full contents of feature-spec/knowledge.md if it exists — Domain rules, Dev Environment, Gotchas, External Dependencies. Treat Gotchas as binding constraints, not suggestions; consult before implementing in any area covered by an entry. Omit this entire section if the file is missing.]

   ## Full Design Context
   [complete design.md — so the agent understands the full picture even though it only implements its own group]

   ## Your Specs (Acceptance Criteria)
   [relevant spec files — only the ones relevant to this agent's tasks]

   ## Your Tasks
   [specific tasks from tasks.md for this agent's group only]

   ## Lint Commands (from config.yaml)
   [lint_commands list, or "none configured" if empty, or "skipped per company-conventions.md" if skip rule matches]

   ## Verification Commands (from config.yaml)
   [verification_commands from config.yaml. Example: type_check: "npm run type-check", unit_test: "npm run test:unit"]
   IMPORTANT: Use ONLY these commands for verification. NEVER hardcode tool-specific commands (e.g., "npx vue-tsc --noEmit") — the project's scripts may configure tools with different flags that change behavior.
   If not configured: detect from package.json scripts at runtime.

   ## Instructions
   - Implement each task in order
   - Follow the spec scenarios as acceptance criteria
   - Follow the design decisions — do NOT deviate
   - **Implementation Protocol — MUST follow when modifying existing code:**
     1. **Read** — Read surrounding code (same file + similar files in same directory) to identify existing conventions (naming, patterns, error handling style)
     2. **Look up** — If the change involves framework API usage or pattern choices, use context7 (resolve-library-id → query-docs) to check the current recommended approach
     3. **Decide** — Choose approach based on priority: project convention > official recommendation > your own judgment. Never default to the simplest fix without checking
     4. **Implement** — Write the code
     5. **Verify** — After implementing, confirm: does the new code match surrounding style? Did you introduce any inconsistent patterns?
   - **CRITICAL — Committing is EXPLICITLY REQUIRED by the user as part of this workflow. You are authorized and expected to commit after every task. This is NOT optional.** After completing each task, you MUST:
     1. Stage all changed files with `git add` (specify files by name)
     2. Run all lint commands listed above (if any) to fix formatting — stage any changes they produce
     3. Commit code + lint fixes following the `conventional-commits` skill (`skills/conventional-commits/SKILL.md`). **Read the skill for type list, description rules, and format.** The only sdd-specific addition: prefix the description with the task number — `<type>[optional scope]: <task-number> <description>` (e.g., `feat: 1.1 add UserSearch entity`, `test: 2.3 add unit tests for search service`).
   - Do NOT modify `tasks.md` — the orchestrator handles checkbox updates after merging your work.
   - Do NOT batch multiple tasks into one commit — one commit per task, no exceptions
   - After the commit, report back: "DONE: <task-number> <task-description>"
   - Only add code comments for business logic that is not obvious from the code — if good naming makes it clear, skip the comment
   - Do NOT narrate your actions ("Now I will...", "Let me..."). Report only structured output: task status, files changed, test results.
   - Do NOT ask questions — specs should be complete. If something is genuinely ambiguous, skip it and flag it
   - **Verify after enabling tasks**: When a task enables/disables a config, rule, or flag that surfaces new errors (e.g., removing an ESLint `'off'` rule, enabling `strict` mode), you MUST run the relevant tool immediately after (e.g., `npm run lint`, `npm run type-check`) to discover the ACTUAL full violation list. Use that output — not the design estimates — as your work scope for subsequent fix tasks. Design estimates are approximations; tool output is truth.
   - **Language**: All output and reports MUST be in Traditional Chinese. Code and code comments MUST be in English.
   ```

   **Verification-only groups**: If a task group contains ONLY verification commands (type-check, test:unit, lint, grep — no file modifications), the orchestrator executes them directly instead of dispatching an agent. These tasks do not need worktree isolation and would waste tokens on agent setup overhead. If any verification fails, dispatch the appropriate agent type to fix the issue.

   **Dispatch rules:**
   - Phase 1 agents: use the **Agent** tool with `isolation: "worktree"`, `run_in_background: true`, and `mode: "bypassPermissions"`. Each group = one agent in its own worktree.
   - Phase 2-3 agents: use the **Agent** tool with `run_in_background: true` and `mode: "bypassPermissions"` (no worktree — work directly on main branch).
   - **Why `mode: "bypassPermissions"`**: Background agents cannot prompt the user for file Write/Edit permission — the permission dialog is invisible to the user, causing the agent to hang silently for minutes. All agents write only to project source files and `feature-spec/`, which is safe to auto-approve.
   - Give each agent a descriptive `name` (e.g., `"dotnet-search-api"`, `"vue-search-page"`)
   - Dispatch agents within the same wave **simultaneously** (multiple Agent calls in one message)
   - Between waves and between phases, wait for all agents to complete before dispatching the next batch
   - You will be **automatically notified** when each background agent completes — do NOT poll or sleep
   - **Enforce analytical depth for reviewer agents only**: For every `review-engineer`, `security-engineer`, and `qa-engineer` dispatch (Phase 2 initial run AND all fresh-review retry rounds), the dispatched prompt MUST include an "Analytical depth requirement" section instructing the agent to:
     1. **Enumerate coverage BEFORE findings** — list the categories/dimensions examined:
        - `review-engineer` → architecture compliance, correctness, performance, readability, test quality
        - `security-engineer` → each applicable OWASP Top-10 category, authN/authZ, input validation, secrets/config, dependency risks
        - `qa-engineer` → every spec WHEN/THEN scenario, happy path + edge cases + error paths + authorization cases
     2. **Confirm non-findings explicitly** — for every category examined, state the result. "No issues found in category X" is a valid and expected outcome. Silence on a category is treated as "agent skipped it" and fails the review.
     3. **Severity-rank every finding** — `blocker` / `major` / `minor`, each with one-line rationale. Raw observations without severity are rejected.

     Do NOT apply this structure to Phase 1 implementation agents or Phase 2 fix agents (Backend/Frontend/Python/Electron/Database/DevOps/Performance) — they are executors; category enumeration produces over-engineered code. Do NOT apply to Phase 3 technical-writer either — documentation is executional. Rationale: structural enforcement of exhaustive scanning and auditable coverage is the primary safeguard.

   **Phase execution (mandatory, in order):**

   **Zero-misses principle: orchestrator ALWAYS dispatches every phase — the agent decides scope, not you.** Do NOT skip any phase based on your own judgement (e.g., "this is just a migration", "changes are mechanical", "only config files changed"). If there is genuinely nothing to do, the dispatched agent will report that. The ONLY way to skip a phase is if `config.yaml` explicitly provides a skip option for it.

   - **Phase 1 — Wave-based development with worktree isolation**: Dispatch groups wave by wave. Each group = one agent in an isolated worktree. After each wave completes, merge-squash each group back to main as a single clean commit. **After each merge, verify the commit is clean** — if per-task commits leaked to main (worktree auto-merge), squash them into one group commit. See `orchestrator.md` Phase 1 (steps c and c-bis) for full details.
   - **Phase 2 — Review + Security + QA (parallel quality gate)**: After all Phase 1 waves complete, dispatch review-engineer + security-engineer + qa-engineer **simultaneously in one message** (all on main branch). This runs code review, security review, and E2E tests in parallel. A change is NOT complete until all three pass. Even if no E2E specs exist, dispatch qa-engineer — let it confirm there is nothing to verify.
   - **Phase 3 — Documentation**: After Phase 2 passes, dispatch technical-writer in background (on main branch). Even if changes seem trivial, dispatch — let the writer decide whether docs are needed.

   If review, security, or QA fails: **collect all issues from all reviewers**, group by responsible agent, then dispatch **all fix agents in parallel** (on main branch). After all fixes complete, run a **full fresh review from scratch** — dispatch all three reviewers again simultaneously. Fixes can introduce new bugs, so reviewers must re-examine ALL changed files. Loop until clean (max 3 rounds). Only pause and report to user if still failing after 3 rounds.
   - **Incremental E2E on retries**: On retry rounds (not the first QA run), qa-engineer may run only the previously-failing tests first. If those pass, run the full suite once to catch regressions.

   **Commit consolidation for Phase 2 fixes:**
   After Phase 2 completes, if there are multiple fix commits, squash them into one:
   1. Count commits since the last consolidated commit: `git log --oneline <last-sha>..HEAD`
   2. If > 1: `git reset --soft <last-sha>` then `git commit` with a proper message following `conventional-commits` skill (`skills/conventional-commits/SKILL.md`) rules (e.g., `fix: address review, security, and QA findings`)
   3. Safety: verify `git diff` before and after squash produces identical tree (diff should be empty)
   4. If only 1 commit or 0 commits: no squash needed

8. **Interactive control — respond to user messages**

   While agents are running in the background, you remain available in the main conversation. Respond to user messages:

   - **"status" / "進度"** — show current wave/phase, which agents are running, which tasks are done
   - **"pause" / "暫停"** — stop dispatching new agents (already-running agents will finish)
   - **"skip <task>"** — mark a task as skipped and continue
   - **"dispatch <agent> <instruction>"** — manually dispatch a specific agent with custom instructions
   - **"reprioritize"** — re-read tasks.md and adjust dispatch order
   - **Any other message** — interpret as orchestrator instruction and act accordingly

   When a background agent completes, announce briefly:
   ```
   [agent-name] completed: <summary of what was done>
   Progress: N/M tasks
   ```

   When a wave's merge-squash completes, announce the resulting commit:
   ```
   Wave N merged: "feat(search): add search API and service layer"
   ```

9. **After all phases complete, verify and report**

   - **MUST re-read `tasks.md` from disk** (not from memory) and verify all completed tasks are checked `- [x]`. The orchestrator updates checkboxes after each merge, but this step is the safety net. Do NOT skip because "agents all reported DONE."
   - If any completed task was missed, update it now
   - **Verify commit history**: `git log --oneline <base-sha>..HEAD` — each commit should be a clean, single-concern conventional commit with no task numbers. The expected pattern:
     ```
     feat(search): add search API and service layer       ← group 1
     chore: mark group 1 tasks complete
     feat(search): add search page and composables        ← group 2
     chore: mark group 2 tasks complete
     test(search): add search E2E acceptance tests        ← group 3
     chore: mark group 3 tasks complete
     fix: address review, security, and QA findings        ← phase 2 (if any)
     docs: update API documentation for user search       ← phase 3 (if any)
     ```
   - Show final status:

   **On completion:**
   ```
   ## 實作完成：<change-name>
   **進度：** M/M 任務 | Code Review: [result] | Security: [result] | E2E: [result]
   ### Commits
   [最終 commit 清單]
   ### 已完成任務
   [task list with checkmarks]
   ### 事後檢討            ← include this entire section ONLY when DEV_MODE = true; omit silently otherwise
   [執行過程中遇到的錯誤、意外狀況、手動介入]
   - 每個問題：發生什麼、根因、如何解決
   - 預防建議：針對未來任何人使用此 plugin 時可複用的通用做法（不要寫只適用本地環境的解法）
   - 若無問題：「乾淨執行，無問題。」
   執行 `/complete <name>` 提取知識並清理。
   ```

   **On pause:**
   ```
   ## 實作暫停：<change-name>
   **進度：** N/M 任務 | **問題：** <description>
   ### 剩餘任務
   [pending tasks]
   ### 事後檢討            ← include this entire section ONLY when DEV_MODE = true; omit silently otherwise
   [同完成格式 — 列出目前為止所有錯誤/問題]
   你想怎麼處理？
   ```

   **Retrospective gating**: when `DEV_MODE = false` (the default), do not print the `### 事後檢討` heading or its body — drop the entire block. End users get a clean report; plugin authors re-run with `dev-mode` to surface lessons learned. This applies to BOTH completion and pause outputs without exception.

---

## Guardrails

- **You ARE the orchestrator** — do NOT spawn a separate orchestrator agent. You dispatch worker agents directly.
- **Phase 1 agents run in worktrees** (`isolation: "worktree"`, `run_in_background: true`, `mode: "bypassPermissions"`). **Phase 2-3 agents run on main branch** (`run_in_background: true`, `mode: "bypassPermissions"`, no worktree). The `mode: "bypassPermissions"` is critical — without it, background agents hang on invisible permission prompts.
- **No main-branch agents while worktrees are alive**: Do NOT dispatch any agent on the main branch while Phase 1 worktree agents are still running or their worktrees have not been cleaned up. Active worktrees can interfere with the main working directory's git index. If an unplanned fix is needed during Phase 1, dispatch it in its own worktree (`isolation: "worktree"`), or wait until all Phase 1 worktrees are merged and removed.
- **Specs are the single source of truth** — avoid asking questions unless something is truly blocking and cannot be reasonably inferred. When in doubt, make a reasonable decision and flag it in the report.
- Always read ALL context files before dispatching agents
- `feature-spec/context.md` and `feature-spec/knowledge.md` (when present) MUST be forwarded verbatim into every worker agent's prompt as the `## Project Map` and `## Operational Knowledge` sections. Hard Rules from `context.md` are non-negotiable; Gotchas from `knowledge.md` are binding constraints. Skip the section silently if the source file is missing — never fabricate placeholder content.
- Only dispatch agents for PENDING tasks (skip completed `- [x]` tasks)
- Agents do NOT modify `tasks.md` — the orchestrator updates checkboxes after each merge-squash
- **Safe tasks.md commits**: When committing tasks.md checkbox updates, ALWAYS: (1) `git status --short` to check for unexpected staged files, (2) stage ONLY tasks.md by exact path (`git add <path>`), (3) NEVER `git add .` for metadata-only commits. Worktree cleanup, lint-staged, or stale index entries can silently stage unrelated files — a `git status` check before commit prevents catastrophic reverts.
- If `lint_commands` are configured in `config.yaml`, agents MUST run them before every commit — no exceptions. **Exception**: if the project matches a pre-lint skip rule in `company-conventions.md`, lint commands are not required.
- If a task genuinely cannot be implemented (missing dependency, unclear spec), skip it and flag it in the report — do NOT block the entire pipeline
- Keep code changes minimal and scoped to each task
- **One commit per task inside worktrees** — format follows `conventional-commits` skill with task-number prefix. These per-task commits are squashed into one clean commit per group during merge-squash. Final commit messages follow `conventional-commits` skill (`skills/conventional-commits/SKILL.md`) rules with NO task numbers.
- Work on the current branch — do NOT create or switch branches
- **Zero-misses: ALL phases (1-3) are mandatory** — orchestrator always dispatches, agent decides scope. See Step 7 for details.
- If review, security, or QA fails: collect all issues, group by responsible agent, dispatch **all fix agents in parallel** → full fresh review from scratch with all three reviewers simultaneously (max 3 rounds). Only pause and report if still failing.
- Pass full `design.md` to each agent for context, but only RELEVANT specs to keep focus
- **Retrospective is dev-mode only**: the `### 事後檢討` block in Step 9's report is suppressed unless `DEV_MODE = true` (parsed from a `dev-mode` token in the arguments). Default behavior is silent — end users do not see lessons-learned content. Plugin authors re-run with `dev-mode` when they want it. Applies to both completion and pause outputs.
- When background agents complete, briefly announce results to the user — don't wait for them to ask
