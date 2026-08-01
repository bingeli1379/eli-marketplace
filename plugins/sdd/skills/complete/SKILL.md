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

   Load `${CLAUDE_PLUGIN_ROOT}/references/repo-topology.md` and run its Step 0 detection. It only affects Step 4 (the cleanup commit): in **single-repo** mode the `feature-spec/` deletion is committed in the cwd repo; in **multi-repo** mode the code commits already landed per child repo during `/apply`, so `/complete` just deletes `feature-spec/` and commits that deletion only if cwd is itself a git repo (otherwise plain `rm`).

1. **Select change(s) to complete**

   **If a name is provided:** Use that single change. Go to step 2.

   **If no name is provided (batch mode):**
   - List all directories under `feature-spec/changes/` (excluding `archive/` if it exists)
   - If none exist, report error: "No active changes found."
   - For each change, read its `tasks.md` and count `- [ ]` vs `- [x]`
   - Collect changes where **all tasks are complete**: `tasks.md` exists, has at least one task, and zero `- [ ]` remain. A change with **no `tasks.md`, or an empty `tasks.md` (zero tasks)**, does **NOT** qualify — it was never implemented (e.g. `/propose` crashed before writing tasks.md), and auto-deleting it would silently discard its proposal/design. Treat it as incomplete and never auto-delete it in batch mode.
   - If no changes qualify, report: "No fully completed changes found." and list each change with its status (e.g., `add-user-search: 3/5 tasks complete`, `draft-x: no tasks.md — not implemented`)
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

   **Walking-skeleton residue gate (MANDATORY — blocks completion):** search for residual `SKELETON:` markers in **tracked source only**. Use `git grep`, not plain `grep -r` — a recursive filesystem grep also hits `node_modules/`, build output, and vendored code, producing false blocks:

   The marker is a **code comment** by convention, so the scan excludes documentation (`*.md`) — otherwise a project that merely *documents* the `SKELETON:` convention in its own docs would be blocked forever, including this workflow's own docs:

   ```bash
   # single-repo (cwd is the repo)
   git grep -n "SKELETON:" -- . ':(exclude)feature-spec' ':(exclude)*.md'

   # multi-repo: run per child repo THIS change touched (from tasks.md `<!-- repo: … -->`
   # annotations) — never scan untouched sibling repos, their markers are not yours
   git -C <repo> grep -n "SKELETON:" -- . ':(exclude)*.md'
   ```

   **no-git mode** (Step 0 detected no repo): fall back to `grep -rnI "SKELETON:" . --exclude="*.md" --exclude-dir=feature-spec --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=build` (`-I` skips binaries), and say in the report that the scan is best-effort because there is no index to scope it.

   **Attribute each hit to a change before blocking on it.** The working tree is shared, so a raw hit may belong to a *different* in-flight change — blocking `<name>` for someone else's placeholder is wrong. Ownership is decided from two sources: the files in this change's `design.md` `## Affected Files` (always available), plus the files touched by its own commits — which requires a commit range, derived as follows:

   ```bash
   # single-repo: /propose Step 11 committed exactly "docs: propose <name>" — that is the change's start
   CHANGE_BASE=$(git log --format=%H --grep="^docs: propose <name>$" -1)
   # contamination check: any OTHER change proposed after this one shares the range
   OTHERS=$(git log --format=%s "$CHANGE_BASE"..HEAD --grep="^docs: propose ")
   [ -n "$CHANGE_BASE" ] && [ -z "$OTHERS" ] \
     && git log --name-only --pretty=format: "$CHANGE_BASE"..HEAD | sort -u
   ```

   - **Anchor found AND range uncontaminated** → union those paths with `## Affected Files` and attribute against the union.
   - **Range contaminated** (`OTHERS` non-empty — another change was proposed after this one, so `CHANGE_BASE..HEAD` also contains ITS commits) → the range cannot be attributed to `<name>` alone. Fall back to `## Affected Files` alone, exactly as below. Using the contaminated range would pull a sibling change's placeholder into this change's scope and block a change that is actually finished — the precise failure this attribution exists to prevent.
   - **Anchor NOT found** — the propose commit was amended/rebased away, `/propose` ran in **no-git**, or this is **multi-repo** (the `docs: propose` commit lives at the umbrella, and child repos carry no change-named marker, so no honest per-repo range exists) → attribute on `## Affected Files` **alone**.

   Whenever you fall back (not found OR contaminated), say so in the report: `ℹ SKELETON 歸屬僅依 design.md Affected Files（<找不到 commit 錨點 | 範圍含其他 change>）`. Never widen instead — no timestamps, no whole-branch history. An over-wide range attributes other changes' placeholders to this one and blocks completion wrongly.

   Then:

   - **Hit inside this change's scope** → this change is **unfinished regardless of checkbox state**. Report every residual location (`file:line`) and **stop**: do not delete artifacts, do not commit. Tell the user which harden tasks are effectively incomplete and to finish them (`/apply <name>`) before re-running `/complete`. This is not overridable by confirmation — a checked-off `tasks.md` with live `SKELETON:` markers is exactly the failure mode the gate exists to catch.
   - **Hit outside this change's scope** → do NOT block. Report it as an informational note naming the file and, if identifiable, the other change that owns it.

   In **batch mode**, apply the same attribution per change: a change with in-scope residue is skipped and listed with its residual count; the others still complete.

   **If no tasks.md exists (or it has zero tasks):** the change was never implemented — deleting it discards its proposal/design work. Use **AskUserQuestion** to confirm: "No tasks.md — delete un-implemented change `<name>`?" / "Cancel". Proceed only if the user confirms. (In batch mode this path is unreachable — such changes were already filtered out in Step 1.)

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
- **Residual `SKELETON:` markers block completion unconditionally** (Step 2 gate) — in single-repo and in every touched child repo. Not overridable by user confirmation, and checked even when all tasks are `- [x]`; a shipped skeleton placeholder is a bug, not a completed change.
- When a name is explicitly provided, allow completing incomplete changes with user confirmation.
- **No knowledge extraction, no doc maintenance**: `/complete` does not write `knowledge.md`, sync `context.md`, or edit CLAUDE.md / README. Those artifacts are not part of this workflow anymore — the project owns its own docs.
- Always keep `feature-spec/config.yaml` — never delete it.
- Show a clear summary of what happened.
- Never push to remote — only commit locally.
