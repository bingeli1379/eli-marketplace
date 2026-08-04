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

   **Multi-repo**: there is no umbrella `feature-spec/config.yaml` — read `lint_commands` from `<repo>/feature-spec/config.yaml` for **each child repo this task touches**, and run + commit that repo's lint inside it (`git -C <repo> ...`). A touched repo with no config gets no pre-lint.

   Otherwise, if `lint_commands` are configured (single-repo: `feature-spec/config.yaml`):
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

   **e. Present the plan (one message, then dispatch):**

   **Read `${CLAUDE_PLUGIN_ROOT}/skills/scope-contract/SKILL.md` in full before composing this message.** That skill is the single source for the 變更（現在 → 改成）block — its template, the depth rule (single-hop → one line; multi-execution-path → expanded behavior chain), the format-change tracing rule, and the terminal-state rule. Do NOT reconstruct it from memory.

   Wrap that contract in quick mode's own envelope:

   ```
   ## Quick Task: <summary>

   **Scope:** <affected layers>   **Complexity:** <Simple/Medium/Complex>

   <the 變更（現在 → 改成）+ 鎖定假設 blocks, per the scope-contract skill>

   ### Questions (need your input)      ← include ONLY when there are genuine ambiguities; omit the whole section otherwise
   1. <specific question about unclear behavior>
   2. <specific question about edge case or design choice>

   ### Acceptance Criteria              ← omit while questions are outstanding
   - WHEN <condition> THEN <expected result>

   ### Tasks
   ## 1. <Group Name>
   - [ ] 1.1 (Backend) <task description>
   - [ ] 1.2 (Frontend) <task description>

   ### Agents to Dispatch
   - <agent-1>: <task count> tasks

   Dispatching now.                     ← omit while questions are outstanding
   ```

   - **Ambiguities exist** → send it via **AskUserQuestion** with the Questions section, ALL questions in ONE message, tasks labelled as pending. After the user responds, incorporate their answers and dispatch.
   - **No ambiguities** → omit the Questions section, show it as a regular message with Acceptance Criteria + Tasks, and dispatch immediately without waiting.

   Three deltas from the scope-contract skill, all quick-mode specific:
   - The contract SHOULD stay under **20 lines** (smaller cap than `/propose`'s ~25) — if it exceeds that, the task is too big for quick and SHOULD be promoted to `/propose`.
   - That skill forbids AskUserQuestion because the `/propose` gate it was written for is a final sanity check. **The ambiguity path here overrides that** — it carries real open questions, so it uses AskUserQuestion. The no-ambiguity path is a plain message, as the skill says.
   - There is no correction-round loop here; a correction is folded in and dispatch proceeds.

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
   [full contents of the config.yaml governing THIS agent's repo, if it exists — single-repo: `feature-spec/config.yaml`; multi-repo: `<this agent's child repo>/feature-spec/config.yaml` (there is no umbrella config). Tech stack, architecture block (pattern, layers, entry_points), and hard_rules. hard_rules are non-negotiable. This is the only project context; omit the section if config.yaml is missing.]

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
   - **Implementation Protocol** — follow *Match Existing Code Before Writing* → *Decision order when modifying existing code* from `agent-guidelines` (Read → Look up → Decide → Implement → Verify). **It is already in your context — apply it; do NOT load it again.**
   - **CRITICAL — Committing is EXPLICITLY REQUIRED by the user as part of this workflow. You are authorized and expected to commit after every task. This is NOT optional.** (**No-git mode** — only when Step 0 detected no git repo: there is nothing to commit to, so implement directly and skip every per-task commit; the user commits later. **Still print the `DONE:` line per task** — with no git history to verify against, it is the orchestrator's only completion signal. The rest of this clause assumes a git repo is present.) After completing each task, you MUST:
     1. Stage all changed files with `git add` (specify files by name)
     2. Run all lint commands listed above (if any) — stage any changes they produce
     3. Commit following the `conventional-commits` skill (`skills/conventional-commits/SKILL.md`). Format: `<type>[optional scope]: <task-number> <description>` (e.g., `fix: 1.1 resolve login redirect loop`)
   - Do NOT batch multiple tasks into one commit — one commit per task
   - After the commit, report back: "DONE: <task-number> <task-description>"
   - **Completion contract** — binding, per *Completion Contract — do NOT end your turn early* in `agent-guidelines` (already in your context): not finished until every assigned task is committed with a `DONE:` line each; the only valid early stops are `NEEDS:` / `CONFLICT:` / `BLOCKED:`.
   - Only add code comments for business logic that is not obvious from the code
   - **Signaling a genuine stop (`NEEDS` / `CONFLICT` / `BLOCKED`)** — follow the **Signaling Unknowns** rules in `agent-guidelines`. In short: do NOT guess an external fact you can't obtain from the repo + this context — commit what is safely done, emit `NEEDS: <question + why blocked + options>`, stop that task; the orchestrator resolves it and resumes you with your context intact. Aside from those signals, do NOT ask questions — if merely ambiguous, make a reasonable decision and flag it.
   - **Language**: All output and reports MUST be in Traditional Chinese. Code and code comments MUST be in English.
   ```

   **Dispatch rules (same as apply):**
   - **Trivial / Simple tier implements inline — skip dispatch entirely.** Per the complexity judgment (Step 5c), when the work is one layer / one concern / mechanical, you (the orchestrator) write it yourself on the main thread — but FIRST load the mapped specialist's `skills:` via the Skill tool so inline work keeps the same skill context (see the Trivial/Simple block under *Phase execution*). The dispatch rules below apply only to Medium / Complex tier.
   - Use the **Agent** tool with `run_in_background: true` and `mode: "bypassPermissions"` for ALL worker agents (without `bypassPermissions`, background agents hang on invisible Write permission prompts)
   - Give each agent a descriptive `name`
   - **Writes single-threaded**: dispatch implementation/fix agents **one at a time** in dependency order, each committing before the next starts. Only read-only reviewers (Phase 2) are dispatched simultaneously. (Multi-repo exception: agents in *different* child repos may run concurrently.)
   - You will be **automatically notified** when each background agent completes — do NOT poll
   - **Handling a NEEDS return**: if an agent's report contains a `NEEDS:` line, treat it as *paused awaiting an external fact*, not done. Resolve it with whatever tools/knowledge you (the orchestrator) have, then **resume the SAME agent with `SendMessage`** (context intact — do NOT re-dispatch). Because agents run in the background you can service several concurrently. `CONFLICT:` → resolve with the user; `BLOCKED:` → re-scope or re-dispatch with corrected context. See `skills/agent-guidelines/SKILL.md` → *Signaling Unknowns* for the vocabulary.
   - **Enforce analytical depth for reviewer agents only**: read `${CLAUDE_PLUGIN_ROOT}/references/reviewer-depth.md` and include its block verbatim in every `review-engineer` / `security-engineer` / `qa-engineer` dispatch. Quick mode usually has no specs, so the `qa-engineer` line resolves to "every affected user-facing flow" — that conditional is in the file. It also names who must NOT receive it (implementation and fix agents, `performance-engineer`, technical-writer) and why; honor that exclusion.

   **Phase execution based on complexity:**

   **Trivial / Simple tasks (orchestrator implements inline — NO dispatch):**
   - **First, borrow the specialist's skills (MANDATORY — do NOT skip).** Implementing inline means you do NOT get the mapped agent's eagerly-loaded skills automatically, so load them yourself: resolve the agent file per `${CLAUDE_PLUGIN_ROOT}/references/agent-routing.md` (*Agent-file resolution* — core agents in `agents/`, pack agents via `find ~/.claude/plugins -path "*/<pack>/agents/<role>.md"`), take its `skills:` frontmatter list, and invoke each via the **Skill tool** before writing (e.g., a `(Frontend)` task → load `vue-best-practices`, `frontend-checklist`, `engineering-checklist`, `test-driven-development`; a `(Backend)` task → `dotnet-best-practices`, `clean-architecture`, `engineering-checklist`, `test-driven-development`). Then load any stack-/datastore-specific skill the task needs on demand, exactly as that agent would after its Stack Detection step. If the mapped pack is not installed, the file resolution finds nothing → load `agent-guidelines` first (it is on every agent's list and carries the Implementation Protocol you are about to apply), then the other core skills (`engineering-checklist`, `test-driven-development`, …), and note the degradation. This gives inline work the same skill context a dispatched agent would have had — without it, inline output silently loses the specialist's best-practices.
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
- `config.yaml` (when present) MUST be forwarded verbatim into every worker agent's prompt as `## Project Context` — the cwd repo's in single-repo mode, and in multi-repo the config of the child repo that agent is bound to (there is no umbrella config). `hard_rules` are binding. The project's own docs are never read or forwarded — config.yaml is the only project context. Skip the section silently if config.yaml is missing.
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
