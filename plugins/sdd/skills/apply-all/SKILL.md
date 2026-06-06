---
name: apply-all
description: >
  Run /apply sequentially on multiple changes. Use when the user has
  several prepared changes and wants to batch-implement them unattended.
user-invocable: true
---

Run `/apply` on multiple changes sequentially. The main Claude acts as orchestrator for the entire batch — dispatching worker agents in the background while remaining responsive to user messages.

Repo topology (single-repo vs multi-repo) is handled by each per-change `/apply` invocation — it runs its own Step 0 detection and binds task groups to their target repos. `/apply-all` adds nothing topology-specific; it just sequences the changes.

---

**Input**: Optionally specify change names in order (e.g., `/apply-all add-user-registration add-user-profile add-user-roles`). If omitted, auto-detect. An optional `dev-mode` token may appear anywhere in the arguments (e.g., `/apply-all add-user-registration dev-mode add-user-profile`) — see Step 1 for parsing rules.

**Steps**

1. **Discover active changes and parse mode flags**

   **Mode flag parsing**: split arguments on whitespace. If any token equals `dev-mode` (case-insensitive), set the internal `DEV_MODE = true` flag and remove the token from the argument list. Pass `dev-mode` through to each per-change `/apply` invocation in Step 3 so its retrospective is surfaced too. The remaining tokens go through normal name resolution. `DEV_MODE` defaults to `false` — the batch `事後檢討` block in Step 4 is suppressed unless the flag is set.

   List all directories under `feature-spec/changes/` (excluding `archive/`).
   Filter to only changes that have pending tasks (`- [ ]` in `tasks.md`).

   If no pending changes found:
   - Report: "No pending changes found. Run `/propose` first."
   - Stop.

2. **Determine execution order**

   **If names are provided as arguments:** use that exact order.

   **If no arguments — auto-resolve dependencies:**

   a. Read each change's `proposal.md` and look for the `## Dependencies` section.
   b. Build a dependency graph from all `Depends on` fields across all active changes.
   c. **Topological sort** — order changes so dependencies come first.
   d. If circular dependencies are detected, report the cycle and ask the user to resolve.
   e. **Decide whether to ask or auto-execute:**

   - **Order is deterministic** (all changes form a single dependency chain, or there is only one change): announce the order and **execute immediately without asking**.
   - **Order is ambiguous** (multiple independent changes exist at the same topological level — i.e., they have no dependency relationship and could run in any order): show the resolved order and **ask the user** which order to use:

     ```
     ## 批次套用

     發現 N 個待處理的變更（已依相依性排序）：

     1. add-user-registration（5 待處理 / 8 總計）
     2. add-user-profile（3 待處理 / 3 總計）← depends on: add-user-registration
     3. add-user-roles（4 待處理 / 4 總計）← depends on: add-user-registration

     ⚠️ 2 和 3 互相獨立，無法判斷先後順序。
     按此順序執行？或指定不同順序（例如 "3, 1, 2"）：
     ```

     Use **AskUserQuestion** to let the user confirm or reorder.
     This is the **only** question asked — after confirmation, execution begins automatically.

   **If no Dependencies sections found** — all changes are independent. List them in alphabetical order and ask the user to confirm or reorder (same format as the ambiguous branch above).

3. **Run each change sequentially**

   For each change in order:

   a. Announce: `[N/M] Applying: <change-name>` and record start time.

   b. Execute the full `/apply` logic (Steps 3-9 from `apply/SKILL.md`):
      - **Cache invariant files once at batch start**: Read `orchestrator.md` and `feature-spec/config.yaml` once before the first change. These are invariant across the batch — reuse them for all changes instead of re-reading each time.
      - **Re-read change-specific files fresh for each change** (proposal.md, design.md, tasks.md, specs/). Each change has different specs — do NOT reuse these from the previous change. Prior context may also have been compressed.
      - Read context → parse tasks → act as orchestrator → wave-based dispatch with worktree merge-squash → all phases (implementation → review+QA parallel → docs) → verify checkboxes and commit history
      - **Do NOT ask implementation questions** — make reasonable choices, flag ambiguities in report

   c. **Mandatory completion checkpoint — Do NOT proceed to next change until ALL are satisfied:**
      - [ ] Phase 1-3 ALL dispatched (orchestrator never pre-judges whether a phase is "needed" — always dispatch, let the agent decide scope)
      - [ ] Phase 2 all three verdicts pass: code review APPROVED (or APPROVED WITH COMMENTS), security SECURE, QA PASSED — a change is NOT complete until all three pass
      - [ ] Step 9 tasks.md re-read from disk and checkboxes verified
      - [ ] All worktrees cleaned up (no leftover worktree branches)
      - [ ] Final commits are clean conventional-commit messages with no task numbers

   d. Record end time, duration, and result (COMPLETE or PAUSED with reason).

   e. Announce: `[N/M] <change-name>: COMPLETE (8/8 tasks, 25m)` and **automatically proceed to next change**.

   f. **If a change pauses** (review/QA failure after retries): record reason, **continue to next change** — do NOT stop the batch. User can fix later with `/apply <name>`.

   g. **Unresolvable NEEDS in unattended mode**: when a worker emits a `NEEDS:` (see `skills/agent-guidelines/SKILL.md` → *Signaling Unknowns*), resolve it with the tools available and resume the agent as in `/apply`. But because the batch runs unattended, if a NEEDS can only be answered by the user and no resolving tool is available, do NOT hang waiting — **park that change as PAUSED** (reason: `unresolved NEEDS: <question>`) and continue to the next. The user resolves it later with `/apply <name>`.

4. **Show final batch report**

   ```
   ## 批次實作完成

   **總耗時：** Xh Ym

   **結果：**
   - [x] add-user-registration — 完成 (8/8 任務, 25m)
   - [ ] add-user-profile — 暫停 (code review failed after 2 retries, 18m)
   - [x] add-user-roles — 完成 (4/4 任務, 12m)

   **摘要：** 2/3 changes 完成, 1 暫停

   **暫停的 changes：**
   - `add-user-profile`: [原因]. 執行 `/apply add-user-profile` 重跑

   **事後檢討：**            ← include this entire block ONLY when DEV_MODE = true; omit silently otherwise
   [彙整所有 changes 中遇到的錯誤、意外狀況、手動介入]
   - 每個問題：哪個 change、發生什麼、根因、如何解決
   - 預防建議：針對未來任何人使用此 plugin 時可複用的通用做法
   - 若無問題：「乾淨執行，所有 changes 無問題。」
   ```

   **Retrospective gating**: when `DEV_MODE = false` (the default), drop the `**事後檢討：**` line and its body entirely from the batch report. End users get a clean batch summary; plugin authors re-run with `dev-mode` to surface aggregated lessons learned.

---

## Interactive Control

While the batch is running, the user can send messages at any time. Respond to them:

- **"status" / "進度"** — show batch progress: which change is active, current phase, running agents, overall N/M changes
- **"skip" / "跳過"** — skip the current change, move to next
- **"stop" / "停止"** — stop dispatching new agents/changes after current agents finish, show partial report
- **"skip <change-name>"** — remove a specific upcoming change from the queue
- **Any other message** — interpret as orchestrator instruction for the current change

After responding to the user, **resume batch execution automatically** — do NOT wait for further input.

---

## Guardrails

- **You ARE the orchestrator** for the entire batch — do NOT spawn a separate orchestrator agent
- **All worker agents run in background** (`run_in_background: true`)
- **Only ask execution order when ambiguous** (independent changes at same level) — if order is deterministic, execute directly
- **Do NOT ask implementation questions** — make reasonable decisions and flag ambiguities in the report
- **Do NOT stop the batch if one change fails** — skip it and continue to next
- **After responding to user messages, resume automatically** — never wait for follow-up input unless the user explicitly says "stop"
- **Zero-misses: ALL phases (1-3) are mandatory** — see Step 3c checkpoint for the complete checklist
- **Worktree cleanup**: ensure all worktrees are removed after each change completes
- Each change runs on the current branch — do NOT create or switch branches
- If a change has no pending tasks (all `- [x]`), skip it and note in the report
- Track and report duration for each change and total batch time
- **Retrospective is dev-mode only**: the `**事後檢討：**` block in Step 4 is suppressed unless `DEV_MODE = true` (parsed from a `dev-mode` token in the arguments). The flag is also forwarded to each per-change `/apply` so per-change retrospectives surface consistently. Default behavior is silent — end users see only progress, results, and pause reasons.
