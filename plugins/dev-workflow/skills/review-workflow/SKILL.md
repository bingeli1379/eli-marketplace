---
name: review-workflow
description: Use when auditing a workflow / orchestration skill or any multi-step procedure for LOGIC and PROCEDURAL correctness — resume/idempotency, step-ordering that destroys needed state, cross-step contradictions, broken invariants, unhandled edge cases (crash/interrupt, empty input, multi-repo, no-git), dependency-graph handling, and destructive-op safety. Also audits whole-repo duplication and single-source-of-truth drift (the same substantial block copied across files, a concept with no single canonical home). This is the heavy, occasional deep audit — run it for larger changes. Use after /review-prompt for any skill that describes a procedure, when auditing for duplication / single source of truth, or when the user asks to review workflow logic or run /review-workflow.
---

# Workflow Audit

Audit a workflow / orchestration skill (or any multi-step procedure) for **behavioral and structural correctness** — whether the described procedure actually produces correct behavior when executed (Lens A), and whether content is duplicated or lacks a single source of truth across the repo (Lens B). This is *not* single-file text quality — that is `/review-prompt`. **Correctness > coverage > brevity.**

This is the companion to `/review-prompt`. `/review-prompt` judges prompt *text* quality (removed rules, broken references, bloat, cross-file consistency, wording contradictions) and stays **cheap and per-change**. This skill is the **heavy, occasional** end of the scale — run it for larger changes. Because a deep look already pays for whole-repo reasoning, it runs two lenses in one pass:

- **Lens A — procedural-logic correctness**: trace the steps as a state machine and find where the procedure breaks, corrupts state, loses data, or deadlocks.
- **Lens B — duplication & single source of truth**: across the repo, find substantial content copied into multiple files and concepts with no single canonical home (they drift).

Both need the same expensive cross-file read, so they share one pass. Keep the cheap, per-change checks in `/review-prompt`; do NOT move whole-repo sweeps there.

---

**Input**: Optionally specify target files via `$ARGUMENTS`. If omitted, auto-detect changed files via git. Pass `--fix` in `$ARGUMENTS` to apply fixes after reporting (default is **report-only** — logic and consolidation fixes are design decisions, so they are surfaced, not auto-applied).

**Steps**

1. **Identify the targets**

   Determine the file set (explicit `$ARGUMENTS`, else auto-detect below). The two lenses scope over it differently:
   - **Lens A (logic)** applies to files that describe a **multi-step procedure that mutates state** — sequential steps with ordering, git ops, file writes/deletes, dispatch/handoff, resume/retry, or a dependency graph. A pure knowledge / reference skill (a checklist or style guide, no executable procedure) has no logic to audit — skip it for Lens A only.
   - **Lens B (dedup/SSOT)** applies to **all** target files and their siblings across the repo — a duplicated block or a drifting list lives in any file, procedure or not.

   Auto-detect when no files are specified:
   - Run `git diff --name-only` (uncommitted changes).
   - **If the working tree is clean** (common when run right after `/commit`), fall back to the most recent commit batch: inspect `git log --oneline`, pick the run of related commits, and use `git diff --name-only <base>..HEAD` (default `HEAD~1..HEAD`, widen for a multi-commit batch). Record the range.
   - If there are no target files at all, report that and stop.

   **Deterministic backstop**: if the repo ships its own fast validation/structure script (e.g. `scripts/check-*.sh`, or a `validate` / `lint` task), run it up front and fold any failures into the report — a deep pass is the moment to sweep the mechanical regressions too, not only the semantic ones.

2. **Read each target IN FULL and map it as a state machine**

   Read the complete file(s) — not just the diff; a logic defect usually lives in the interaction between a changed step and unchanged ones. For each procedure, note: the ordered steps, what state each reads and mutates (files, git history, checkboxes, dispatched work), the branches/decisions, the claimed invariants, and the abort/error paths. For a change with related files (an orchestrator + the skills it drives), read them together — the defect is often at the seam.

3. **Hunt these defect classes**

   **Lens A — procedural logic** (files that describe a procedure). For each, ask "what concrete input or interruption makes this go wrong?"

   1. **Resume / idempotency** — re-running the procedure (after a crash, a retry, or an explicit resume) double-applies work, skips work, or mis-detects prior state. Classic shape: a *detect/reconcile* step reads state that an earlier step already *mutated away*.
   2. **State-mutation ordering** — an earlier step destroys or transforms data that a later step depends on (e.g. squashing commits before a step that matches on their messages; deleting before reading).
   3. **Behavioral cross-step contradiction** — one step forbids/undoes what another requires, such that no execution satisfies both. (Wording-only contradictions belong to `/review-prompt` criterion t; here focus on ones that break *execution*.)
   4. **Broken invariant** — a guarantee the skill claims (single-writer, atomic/one-commit-per-unit, never-branch, exactly-once) is violated by some path or step.
   5. **Unhandled edge / precondition** — crash mid-step, empty or missing input, a required artifact absent, a first-iteration/zero-item case, or an environment the skill doesn't cover (no-git, multi-repo/multi-context, absent tooling). What does the procedure do then?
   6. **Ordering / dependency graph** — cycles, a dependency naming something outside the active set, or a failed/paused prerequisite that does NOT block the items depending on it (they run against missing output).
   7. **Destructive-op safety** — delete / overwrite / purge without a dry-run, confirm, or guard; and **data-loss-by-misclassification**: treating a "never done / half done" state as "done" and then discarding it.
   8. **Dangling control flow** — a referenced branch, abort, or handler that is never defined; a decision with no path for one of its outcomes; a step number/label that points nowhere.

   **Lens B — duplication & single source of truth** (whole-repo; read the siblings, not just the changed file):

   9. **Substantial cross-file duplication** — the same non-trivial block (a rule, algorithm, template, or prose section) is copied in ≥2 files. Flag it and propose consolidating to ONE authoritative source the others reference. Incidental one-line overlap is fine; flag copies large enough to drift independently. Duplication is sometimes a deliberate self-containment choice — say so and let the user weigh DRY vs self-containment, rather than mandating consolidation.
   10. **Missing / violated single source of truth** — a concept (an agent/skill list, a coverage matrix, a shared rule, a config value) lives in several independent copies with no canonical home, so they drift (one is updated, the others forgotten). Also verify any SSOT the repo *claims* ("X is the single source of truth", "Y is the central registry") actually holds: the named file is the sole definition and the others only reference it.

4. **Rate and verify each finding**

   - **CONFIRMED** — you traced a concrete failing scenario (specific inputs/state → specific wrong outcome). **PLAUSIBLE** — looks risky but you could not fully confirm; say what you could not verify.
   - **Severity**, most-severe first: data loss / state corruption > silent wrong result that ships > recoverable stall / degraded behavior > cosmetic.
   - **Be conservative.** A workflow deliberately leaves judgment to the executing agent — flag genuine logic defects, not "this could be more explicit." Every finding must carry a concrete failure scenario; if you cannot state one, it is not a finding.

5. **Produce the audit report** (Traditional Chinese; technical terms, file names, and rating labels stay English)

   ```
   ## Workflow Audit

   ### Targets: <files>

   ### Findings (most severe first)
   - **[SEVERITY] [CONFIRMED/PLAUSIBLE] [Lens A|B] `file:line`** — <the defect>
     - Lens A → 失敗情境: <concrete inputs/state → wrong outcome> | Lens B → 重複/漂移: <the copies and how they drift>
     - 修法方向: <how to fix — note when it is a design choice, e.g. DRY vs deliberate self-containment>

   ### Categories judged sound
   - <class>: <one line why it holds>

   ### Verdict: <N confirmed, M plausible | or "no defects found">
   ```

6. **Fix (only if `--fix` was passed)**

   Default is report-only. With `--fix`: apply the **CONFIRMED, unambiguous** fixes directly (e.g. reorder two steps so reconcile precedes the mutation; add the missing guard). For any fix that involves a **design choice** (which of two contradictory rules wins, what the safe default should be), do NOT guess — present the options and let the user decide. After applying, re-read the affected procedure to confirm the fix did not introduce a new ordering/edge defect. Never apply a fix to a PLAUSIBLE finding without confirming it first.

---

## Guardrails

- **Read the FULL file(s), not just the diff** — logic defects live in step interactions, including with unchanged steps.
- **Trace, don't skim** — a finding is only real when you can name the input/interruption and the wrong outcome it produces.
- **Behavior and structure, not single-file text** — removed rules, bloat, broken references, and wording are `/review-prompt`'s job (cheap, per-change). Stay on procedural correctness (Lens A) and whole-repo duplication/SSOT (Lens B) — the things that need expensive cross-file reasoning.
- **Conservative bar** — a spec/workflow intentionally leaves room for agent judgment. Do not flag underspecification as a defect unless a concrete execution goes wrong.
- **Report-only by default** — logic changes to a workflow are design decisions; surface them and fix only under `--fix`, and only the unambiguous ones without asking.
- **No tooling / environment assumptions** — a procedure that assumes git, a single repo, or a linter is itself a finding (edge class 5) if the skill is meant to run where those may be absent.
