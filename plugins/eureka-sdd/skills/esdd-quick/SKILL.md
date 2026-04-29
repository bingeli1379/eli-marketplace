---
name: esdd-quick
description: >
  Quick task execution with orchestrator analysis but no spec artifacts.
  Use when the user has small-to-medium tasks and wants agent team dispatch
  without the full propose → validate → apply ceremony.
user-invocable: true
---

Lightweight alternative to the full `/esdd-propose` → `/esdd-apply` pipeline. The orchestrator **analyzes the task inline** (similar to propose) and **dispatches agents directly** — no spec files are written to disk.

Best for: bug fixes, small features, refactors, chores — tasks where full spec ceremony is overkill but you still want the agent team's specialization and quality gates.

**Input**: A task description (e.g., `/esdd-quick fix the login redirect loop` or `/esdd-quick add dark mode toggle to settings page`).

**Steps**

1. **Get the task description**

   If no description is provided, use **AskUserQuestion** (open-ended) to ask:
   > "What do you want to do? Describe the task."

   Do NOT proceed without a clear task description.

2. **Read project context**

   - Read `feature-spec/config.yaml` for project context (tech stack, conventions, lint commands)
   - Read `feature-spec/context.md` if it exists — AI-readable project map (architecture layers, domain-to-code map, entry points, hard rules). Use it to ground the Step 5 codebase scan and forward it to every worker agent in Step 6.
   - Read `feature-spec/knowledge.md` if it exists — operational gotchas and dev tips. Forward to every worker agent in Step 6 so they avoid known landmines.
   - If `config.yaml` doesn't exist, proceed without it — use defaults from CLAUDE.md
   - `context.md` and `knowledge.md` are optional — skip silently if missing

3. **Confirm current branch**

   Use the current branch as-is. Do NOT create or switch branches.
   Announce: "Branch: **<current-branch>**"

4. **Pre-lint and commit (clean slate)**

   First, check `company-conventions.md` (in the plugin root) for pre-lint skip rules. If the current project matches a skip condition (e.g., .NET project), skip this entire step silently.

   Otherwise, if `lint_commands` are configured in `feature-spec/config.yaml`:
   1. Run all lint commands to fix pre-existing formatting issues
   2. If lint produced changes: stage and commit with `chore: pre-lint cleanup before esdd-quick`
   3. If no changes, skip silently

5. **Analyze the task (inline propose)**

   This is the core difference from `/esdd-apply`. Instead of reading spec files, you **perform the analysis yourself** — similar to what `/esdd-propose` does, but entirely in-memory without writing any files.

   **ZERO MISSES — exhaustive codebase scan (MANDATORY):**
   Scope specified → scan every file within it. No scope → scan entire project.
   Use Glob to list ALL files, read/inspect each that could be affected. Build affected-files inventory (file + WHY).

   **a. Scope analysis:**
   - What is the task trying to achieve?
   - Which layers are affected? (Frontend, Backend, Database, DevOps, etc.)
   - What are the key design decisions? (API shape, data model changes, UI approach)
   - What are the acceptance criteria? (When X happens, then Y should be the result)

   **b. Task breakdown:**
   - Break the task into discrete subtasks
   - Group by reviewable unit — each group = single agent type + single concern (same as tasks.md format)
   - Tag each subtask with an agent type: `(Backend)`, `(Python)`, `(Frontend)`, `(E2E)`, `(Electron)`, `(Database)`, `(DevOps)`, `(Performance)`, `(Security)`, `(Documentation)`
   - Add `<!-- depends: N -->` annotations if groups have dependencies
   - Follow TDD structure for Backend/Frontend tasks when appropriate (write test → implement)
   - Number tasks: `1.1`, `1.2`, etc.

   **c. Complexity judgment:**
   - **Simple** (single agent): one layer only → implementation agent → review
   - **Medium** (2-3 agents): cross-cutting → parallel implementation → review
   - **Complex** (full pipeline): new module/feature → full 4-phase pipeline

   **d. Identify ambiguities and unknowns:**
   - Are there vague requirements? ("improve" → improve what exactly?)
   - Missing edge case handling? (empty input, concurrent access, error states)
   - Unclear integration points with existing code?
   - Design decisions that could go multiple ways?

   **e. If ambiguities exist — ask the user ONCE:**

   Use **AskUserQuestion** with a structured summary. Ask ALL questions in ONE message:

   ```
   ## Quick Task: <summary>

   **Scope:** <affected layers>
   **Complexity:** <Simple/Medium/Complex>

   ### My Understanding
   - <what I plan to do>

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

   If the task description is clear and unambiguous, skip the question step. Show the plan and dispatch right away:

   ```
   ## Quick Task: <summary>

   **Scope:** <affected layers>
   **Complexity:** <Simple/Medium/Complex>

   ### Design Decisions
   - <key decision 1>
   - <key decision 2>

   ### Tasks
   ## 1. <Group Name>
   - [ ] 1.1 (Backend) <task description>
   - [ ] 1.2 (Frontend) <task description>
   ...

   ### Acceptance Criteria
   - WHEN <condition> THEN <expected result>
   - WHEN <condition> THEN <expected result>

   ### Agents to Dispatch
   - <agent-1>: <task count> tasks
   - <agent-2>: <task count> tasks

   Dispatching now.
   ```

   **Decision rule**: Only ask when there are genuine unknowns that would lead to wrong implementation. If you can make a reasonable decision, make it and note it — don't ask just to be safe.

6. **Become the orchestrator and dispatch**

   Read `agents/orchestrator.md` to load the orchestrator role. You are now the orchestrator.

   **Agent Prompt Template** — compose each worker agent's prompt with:

   ```
   You are working on a quick task: "<task summary>"

   ## Your Role
   [agent role definition from agents/<agent>.md]

   ## Mandatory Checklists
   [include content of skills/engineering-checklist/SKILL.md for ALL agents]
   [include content of skills/frontend-checklist/SKILL.md for Frontend/Electron/review agents]

   ## Project Context
   [from feature-spec/config.yaml, or CLAUDE.md defaults]

   ## Project Map
   [full contents of feature-spec/context.md if it exists — architecture layers, domain-to-code map, entry points, hard rules. Hard Rules are non-negotiable. Omit this entire section if the file is missing.]

   ## Operational Knowledge
   [full contents of feature-spec/knowledge.md if it exists — Domain rules, Dev Environment, Gotchas, External Dependencies. Treat Gotchas as binding constraints. Omit this entire section if the file is missing.]

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
     3. **Decide** — Choose approach based on priority: project convention > official recommendation > your own judgment. Never default to the simplest fix without checking
     4. **Implement** — Write the code
     5. **Verify** — After implementing, confirm: does the new code match surrounding style? Did you introduce any inconsistent patterns?
   - **CRITICAL — Committing is EXPLICITLY REQUIRED by the user as part of this workflow. You are authorized and expected to commit after every task. This is NOT optional.** After completing each task, you MUST:
     1. Stage all changed files with `git add` (specify files by name)
     2. Run all lint commands listed above (if any) — stage any changes they produce
     3. Commit following the `conventional-commits` skill (`skills/conventional-commits/SKILL.md`). Format: `<type>[optional scope]: <task-number> <description>` (e.g., `fix: 1.1 resolve login redirect loop`)
   - Do NOT batch multiple tasks into one commit — one commit per task
   - After the commit, report back: "DONE: <task-number> <task-description>"
   - Only add code comments for business logic that is not obvious from the code
   - Do NOT ask questions — if something is ambiguous, make a reasonable decision and flag it
   - **Language**: All output and reports MUST be in Traditional Chinese. Code and code comments MUST be in English.
   ```

   **Dispatch rules (same as esdd-apply):**
   - Use the **Agent** tool with `run_in_background: true` and `mode: "bypassPermissions"` for ALL worker agents (without `bypassPermissions`, background agents hang on invisible Write permission prompts)
   - Give each agent a descriptive `name`
   - Dispatch agents that can run in parallel **simultaneously**
   - You will be **automatically notified** when each background agent completes — do NOT poll
   - **Enforce analytical depth for reviewer agents only**: For `review-engineer`, `security-engineer`, and `qa-engineer` dispatches, the dispatched prompt MUST include an "Analytical depth requirement" section instructing the agent to:
     1. **Enumerate coverage BEFORE findings** — list the categories/dimensions examined:
        - `review-engineer` → architecture compliance, correctness, performance, readability, test quality
        - `security-engineer` → each applicable OWASP Top-10 category, authN/authZ, input validation, secrets/config, dependency risks
        - `qa-engineer` → every spec scenario (or every affected user-facing flow if no spec), happy path + edge cases + error paths + authorization cases (if applicable)
     2. **Confirm non-findings explicitly** — for every category examined, state the result. "No issues found in category X" is a valid outcome. Silence on a category is treated as "agent skipped it" and fails the review.
     3. **Severity-rank every finding** — `blocker` / `major` / `minor`, each with one-line rationale. Raw observations without severity are rejected.

     Do NOT apply this structure to implementation agents (Backend/Frontend/Python/Electron/Database/DevOps/Performance/Documentation) — they are executors; category enumeration produces over-engineered code. Rationale: structural enforcement of exhaustive scanning and auditable coverage is the primary safeguard.

   **Phase execution based on complexity:**

   **Simple tasks:**
   - Phase 1: Single implementation agent
   - Phase 2: review-engineer + security-engineer (parallel)
   - Done.

   **Medium tasks:**
   - Phase 1: Implementation agents in parallel
   - Phase 2: review-engineer + security-engineer + qa-engineer (all parallel)
   - Done.

   **Complex tasks (full pipeline):**
   - Phase 1: All implementation agents in parallel (including qa-engineer for E2E test writing)
   - Phase 2: review-engineer + security-engineer + qa-engineer (all parallel — code review, security review, and E2E tests run simultaneously)
   - Phase 3: technical-writer (if documentation changes needed)

   If review, security, or QA fails: collect all issues, group by responsible agent, dispatch **all fix agents in parallel** → run a **full fresh review** from scratch with all three reviewers simultaneously (not just verify original issues — fixes may introduce new bugs) → repeat until clean (max 3 rounds). Only pause and report to user if still failing after 3 rounds.

   **Commit consolidation after Phase 1:**

   Since `/esdd-quick` does NOT use worktree isolation, per-task commits (with task-number prefixes) land directly on the branch. After all Phase 1 agents complete, **squash per-task commits into one clean commit per group** — matching `/esdd-apply`'s final commit style:

   1. Identify the base commit (the commit before the first per-task commit): `git log --oneline`
   2. Count per-task commits since base: `git log --oneline <base-sha>..HEAD`
   3. If > 1 commit: `git reset --soft <base-sha>` then `git commit` with a clean conventional commit message following `conventional-commits` skill rules — **NO task numbers** (e.g., `refactor(enum): rename lowercase enum objects to PascalCase`)
   4. If only 1 commit: `git commit --amend -m "<clean message>"` to remove the task number prefix
   5. Safety: verify `git diff <base-sha>..HEAD` before and after squash produces identical tree

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
- `feature-spec/context.md` and `feature-spec/knowledge.md` (when present) MUST be forwarded verbatim into every worker agent's prompt as `## Project Map` and `## Operational Knowledge`. Hard Rules and Gotchas are binding. Skip the section silently if the source file is missing.
- **Execute first, report after** — show the plan and dispatch immediately, do NOT wait for user confirmation
- **Code review + security review are MANDATORY** for all complexity levels — never skip them
- If review/QA fails → auto-dispatch fix → **full fresh review** (not just verify original issues) → loop until clean (max 3 rounds) → only then pause
- **One commit per task during implementation** — atomic commits with task-number prefix. **Squashed into one clean group commit (no task numbers) after Phase 1 completes**, matching `/esdd-apply` final commit style.
- Work on the current branch — do NOT create or switch branches
- Keep the plan concise — this is quick mode, not a full spec
- **Language**: All output in Traditional Chinese. Code and comments in English.

## When to Suggest Full Spec Instead

If during analysis (step 5) you determine the task is:
- Touching 3+ independent capabilities
- Would produce 15+ tasks
- Requires significant architectural decisions
- Needs cross-team coordination

Then suggest: "This task looks complex enough for the full spec flow. Want me to run `/esdd-propose` instead?"

But still proceed if the user insists on quick mode.
