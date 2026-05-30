---
name: complete
description: >
  Complete a change: confirm its tasks are done, then clean up the change
  artifacts and commit. If a name is given, complete that specific change.
  If omitted, auto-scan and batch-complete all fully finished changes.
user-invocable: true
---

Complete a change by confirming its tasks are done, deleting the change artifacts, and committing the cleanup.

This skill does **not** extract knowledge or maintain docs. Capturing what was learned and keeping project docs current is the project's own responsibility — use your own docs (CLAUDE.md, README, `docs/`) and whatever skills you prefer for that. `/complete` only finalizes and cleans up.

---

**Input**: Optionally specify a change name (e.g., `/complete add-user-search`). If omitted, auto-scan for all completed changes.

**Steps**

0. **Detect repo topology (MANDATORY first)**

   Load `plugins/sdd/references/repo-topology.md` and run its Step 0 detection. It only affects Step 4 (the cleanup commit): in **single-repo** mode the `feature-spec/` deletion is committed in the cwd repo; in **multi-repo** mode the code commits already landed per child repo during `/apply`, so `/complete` just deletes `feature-spec/` and commits that deletion only if cwd is itself a git repo (otherwise plain `rm`).

1. **Select change(s) to complete**

   **If a name is provided:** Use that single change. Go to step 2.

   **If no name is provided (batch mode):**
   - List all directories under `feature-spec/changes/` (excluding `archive/` if it exists)
   - If none exist, report error: "No active changes found."
   - For each change, read its `tasks.md` and count `- [ ]` vs `- [x]`
   - Collect changes where **all tasks are complete** (zero `- [ ]` remaining), or where `tasks.md` does not exist
   - If no changes qualify, report: "No fully completed changes found." and list each change with its completion status (e.g., `add-user-search: 3/5 tasks complete`)
   - If one or more qualify, display them and proceed to complete **all** of them sequentially (steps 2–4 for each)

   **IMPORTANT**: Batch mode does NOT ask for confirmation — it completes all fully finished changes automatically.

2. **Check task completion status**

   Read `feature-spec/changes/<name>/tasks.md`:
   - Count tasks marked `- [ ]` (incomplete) vs `- [x]` (complete)
   - Display: "Tasks: N/M complete"

   **If incomplete tasks found (only possible when name is explicitly provided):**
   - Display warning showing count and list of incomplete tasks
   - Use **AskUserQuestion** to confirm: "Complete with N incomplete tasks?" / "Cancel"
   - Proceed only if user confirms

   **If no tasks.md exists:** Proceed without task-related warning.

3. **Delete change artifacts**

   ```bash
   rm -rf feature-spec/changes/<name>
   ```

   After deletion, check remaining state:
   - If `feature-spec/changes/` is now empty (no more active changes):
     - Also delete `feature-spec/specs/` (main specs are no longer needed)
     - Also delete `feature-spec/changes/` directory itself
     - Delete `feature-spec/archive/` if it exists (legacy)
   - **Always keep** `feature-spec/config.yaml` — it is reused by future `/propose` and `/quick`.

4. **Commit the cleanup**

   Stage the cleanup (deleted change files) and commit:
   - Single change: `chore: complete <change-name>`
   - Batch mode: `chore: complete <name1>, <name2>, ...`
   - Do NOT push to remote — only commit locally.
   - **Multi-repo**: the change's code was already committed per child repo during `/apply` — do not re-commit code here. This commit only records the `feature-spec/` deletion, and only if cwd is itself a git repo. If cwd is not a repo (plain umbrella folder), skip the commit — the `rm` in Step 3 is enough.

5. **Display summary**

   **Single change:**
   ```
   ## Change Complete: <change-name>

   **Tasks:** M/M complete ✓
   **Cleaned up:** feature-spec/changes/<name>/ deleted
   ```

   **Batch mode:**
   ```
   ## Batch Complete

   Completed N change(s):

   | Change | Tasks | Cleaned Up |
   |--------|-------|------------|
   | add-user-search | 5/5 ✓ | ✓ |
   | fix-login-bug | 3/3 ✓ | ✓ |

   Skipped M change(s) with incomplete tasks:
   - refactor-auth: 2/4 tasks complete
   ```

---

## Guardrails

- Batch mode (no name provided) only completes fully finished changes — never completes incomplete ones without explicit naming.
- When a name is explicitly provided, allow completing incomplete changes with user confirmation.
- **No knowledge extraction, no doc maintenance**: `/complete` does not write `knowledge.md`, sync `context.md`, or edit CLAUDE.md / README. Those artifacts are not part of this workflow anymore — the project owns its own docs.
- Always keep `feature-spec/config.yaml` — never delete it.
- Show a clear summary of what happened.
- Never push to remote — only commit locally.
