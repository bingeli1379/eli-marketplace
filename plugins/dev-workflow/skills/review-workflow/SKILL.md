---
name: review-workflow
description: Use when auditing a workflow / orchestration skill or any multi-step procedure for LOGIC and PROCEDURAL correctness — resume/idempotency, step-ordering that destroys needed state, cross-step contradictions, broken invariants, unhandled edge cases (crash/interrupt, empty input, multi-repo, no-git), dependency-graph handling, and destructive-op safety. Also audits whole-repo duplication and single-source-of-truth drift (the same substantial block copied across files, a concept with no single canonical home). This is the heavy, occasional deep audit and a SUPERSET of /review-prompt — it runs the /review-prompt text pass first, so there is no need to run both. Use it for larger changes, when auditing for duplication / single source of truth, or when the user asks to review workflow logic or run /review-workflow.
---

# Workflow Audit

Audit a workflow / orchestration skill (or any multi-step procedure) for **behavioral and structural correctness** — whether the described procedure actually produces correct behavior when executed (Lens A), and whether content is duplicated or lacks a single source of truth across the repo (Lens B). Single-file text quality is NOT one of the two lenses below — it is `/review-prompt`'s criteria, which this skill runs by delegation rather than by restating. **Correctness > coverage > brevity.**

This skill is a **superset of `/review-prompt`**: it runs that text pass first (step 2, the prompt text pass), then adds the deep lenses. `/review-prompt` alone stays the **cheap, per-change** option — single-file text quality only (removed rules, broken references, bloat, cross-file consistency, wording contradictions, and steering effectiveness: completion criteria, prohibition-vs-positive phrasing, no-ops, information hierarchy). This skill is the **heavy, occasional** end of the scale — run it for larger changes, and do NOT run `/review-prompt` separately alongside it. Because a deep look already pays for whole-repo reasoning, it runs two extra lenses in the same pass:

- **Lens A — procedural-logic correctness**: trace the steps as a state machine and find where the procedure breaks, corrupts state, loses data, or deadlocks.
- **Lens B — duplication & single source of truth**: across the repo, find substantial content copied into multiple files and concepts with no single canonical home (they drift).

Both need the same expensive cross-file read, so they share one pass. Keep the cheap, per-change text criteria defined in `/review-prompt` (this skill delegates to it rather than restating them); do NOT move whole-repo sweeps there.

---

**Input**: Optionally specify target files via `$ARGUMENTS`. If omitted, auto-detect changed files via git. Applying fixes after reporting is the **default**; pass `--report-only` in `$ARGUMENTS` to only surface findings without touching files (it is forwarded to the text pass too). Pass `--skip-prompt-pass` to skip step 2 (the prompt text pass) when `/review-prompt` was already run on this exact change. Even with the default, only **CONFIRMED, unambiguous** fixes are auto-applied — logic and consolidation fixes that involve a design choice are always surfaced for the user to decide, never guessed.

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

2. **Run the `/review-prompt` text pass first** (skipped if `--skip-prompt-pass` was passed)

   Invoke the `review-prompt` skill (Skill tool) on the file set resolved in step 1 (target identification) — pass the explicit file list (and `--report-only` if it was given) so it does not re-detect a different set. Follow that skill's own criteria, structured finding format, and auto-fix loop as written; do not restate or re-derive them here. Its report stays **internal to this pass** — do not print it as its own block; step 6 (the combined report) folds its verdict in.

   Unless `--report-only` was passed, text-level defects are fixed **before** the logic trace, so step 3 (state-machine map) works on the current (fixed) text; with `--report-only` nothing is fixed and the trace runs against the text as-is. If `/review-prompt` reports its scope filter excluded every target (non-plugin paths), note that and continue with the lenses below.

3. **Read each target IN FULL and map it as a state machine**

   Read the complete file(s) — not just the diff; a logic defect usually lives in the interaction between a changed step and unchanged ones. For each procedure, note: the ordered steps, what state each reads and mutates (files, git history, checkboxes, dispatched work), the branches/decisions, the claimed invariants, and the abort/error paths. For a change with related files (an orchestrator + the skills it drives), read them together — the defect is often at the seam.

4. **Hunt these defect classes**

   **Lens A — procedural logic** (files that describe a procedure). For each, ask "what concrete input or interruption makes this go wrong?"

   1. **Resume / idempotency** — re-running the procedure (after a crash, a retry, or an explicit resume) double-applies work, skips work, or mis-detects prior state. Classic shape: a *detect/reconcile* step reads state that an earlier step already *mutated away*.
   2. **State-mutation ordering** — an earlier step destroys or transforms data that a later step depends on (e.g. squashing commits before a step that matches on their messages; deleting before reading).
   3. **Behavioral cross-step contradiction** — one step forbids/undoes what another requires, such that no execution satisfies both. (Wording-only contradictions belong to `/review-prompt` criterion t; here focus on ones that break *execution*.)
   4. **Broken invariant** — a guarantee the skill claims (single-writer, atomic/one-commit-per-unit, never-branch, exactly-once) is violated by some path or step.
   5. **Unhandled edge / precondition** — crash mid-step, empty or missing input, a required artifact absent, a first-iteration/zero-item case, or an environment the skill doesn't cover (no-git, multi-repo/multi-context, absent tooling). What does the procedure do then?
   6. **Ordering / dependency graph** — cycles, a dependency naming something outside the active set, or a failed/paused prerequisite that does NOT block the items depending on it (they run against missing output).
   7. **Destructive-op safety** — delete / overwrite / purge without a dry-run, confirm, or guard; and **data-loss-by-misclassification**: treating a "never done / half done" state as "done" and then discarding it.
   8. **Dangling control flow** — a referenced branch, abort, or handler that is never defined; a decision with no path for one of its outcomes; a step number/label that points nowhere.
   9. **Insertion breaks a neighbour** — new content added *into* an existing step invalidates something already stated beside it. Four shapes, all of which read perfectly correct in the inserted text itself, because the break is never in what was written — it is in the neighbour: (a) a **declared numeric budget** the addition pushes past (a concurrency cap, a size limit, a hop count, "three queries cost the wall-clock of one" when the step now describes five); (b) an **artifact contract** — a later step consumes what this step records, and the change altered its shape or stopped producing it (a step that recorded a *set* now records one boolean, while the consumer still reads a set); (c) an **ordering invariant** — content moved past a gate that was supposed to precede it ("read this before any query" now sitting after three query instructions, simply because paragraphs were inserted above it); (d) a **local self-contradiction** between the new sentence and the one it was appended to — that one belongs to `/review-prompt` criterion t and the text pass already covers it; it is named here only so the insert-shaped sweep below is complete, not restated as a criterion of this skill. **Where the diff INSERTS rather than replaces, check exactly four things about that step: its declared limits, what it records, who reads what it records, and which gate must precede its actions.** This is the dominant class for edits to a long prompt, and the cheapest to find deliberately — a general re-read will not surface it, because every individual sentence is true.

   **Lens B — duplication & single source of truth** (whole-repo; read the siblings, not just the changed file):

   10. **Substantial cross-file duplication** — the same non-trivial block (a rule, algorithm, template, or prose section) is copied in ≥2 files. Flag it and propose consolidating to ONE authoritative source the others reference. Incidental one-line overlap is fine; flag copies large enough to drift independently. Duplication is sometimes a deliberate self-containment choice — say so and let the user weigh DRY vs self-containment, rather than mandating consolidation.
   11. **Missing / violated single source of truth** — a concept (an agent/skill list, a coverage matrix, a shared rule, a config value) lives in several independent copies with no canonical home, so they drift (one is updated, the others forgotten). Also verify any SSOT the repo *claims* ("X is the single source of truth", "Y is the central registry") actually holds: the named file is the sole definition and the others only reference it.

5. **Rate and verify each finding**

   - **CONFIRMED** — you traced a concrete failing scenario (specific inputs/state → specific wrong outcome). **PLAUSIBLE** — looks risky but you could not fully confirm; say what you could not verify.
   - **Severity**, most-severe first: data loss / state corruption > silent wrong result that ships > recoverable stall / degraded behavior > cosmetic.
   - **Be conservative.** A workflow deliberately leaves judgment to the executing agent — flag genuine logic defects, not "this could be more explicit." Every finding must carry a concrete failure scenario; if you cannot state one, it is not a finding.

6. **Produce the audit report** (Traditional Chinese; technical terms, file names, and rating labels stay English)

   One combined report — do not print the text pass's report separately; fold its verdict into the block below (omit that line if step 2, the prompt text pass, was skipped).

   ```
   ## Workflow Audit

   ### Targets: <files>

   ### Prompt pass (/review-prompt): <ALL SAFE / HAS RISKS / HAS BROKEN> — <one line per file: what was fixed, or what remains>

   ### Findings (most severe first)
   - **[SEVERITY] [CONFIRMED/PLAUSIBLE] [Lens A|B] `file:line`** — <the defect>
     - Lens A → 失敗情境: <concrete inputs/state → wrong outcome> | Lens B → 重複/漂移: <the copies and how they drift>
     - 修法方向: <how to fix — note when it is a design choice, e.g. DRY vs deliberate self-containment>

   ### Categories judged sound
   - <class>: <one line why it holds>

   ### Verdict: <N confirmed, M plausible | or "no defects found">
   ```

7. **Fix (default; skipped if `--report-only` was passed)**

   Text-pass fixes already happened in step 2 (the prompt text pass); this step covers the Lens A / Lens B findings only.

   Applying fixes is the default. Apply the **CONFIRMED, unambiguous** fixes directly (e.g. reorder two steps so reconcile precedes the mutation; add the missing guard). For any fix that involves a **design choice** (which of two contradictory rules wins, what the safe default should be), do NOT guess — present the options and let the user decide. After applying, re-read the affected procedure to confirm the fix did not introduce a new ordering/edge defect. Never apply a fix to a PLAUSIBLE finding without confirming it first. With `--report-only`, skip this step entirely and surface all findings for the user to act on.

---

## Guardrails

- **Read the FULL file(s), not just the diff** — logic defects live in step interactions, including with unchanged steps.
- **Trace, don't skim** — a finding is only real when you can name the input/interruption and the wrong outcome it produces.
- **Delegate the text layer, don't restate it** — removed rules, bloat, broken references, and wording are covered by invoking `/review-prompt` in step 2 (the prompt text pass); never copy its criteria into this file. The lenses here stay on procedural correctness (Lens A) and whole-repo duplication/SSOT (Lens B) — the things that need expensive cross-file reasoning.
- **Conservative bar** — a spec/workflow intentionally leaves room for agent judgment. Do not flag underspecification as a defect unless a concrete execution goes wrong.
- **Fix by default, but only the unambiguous ones** — apply CONFIRMED, unambiguous fixes without asking; a fix that involves a design choice is surfaced for the user, never guessed. Pass `--report-only` to surface everything without touching files.
- **No tooling / environment assumptions** — a procedure that assumes git, a single repo, or a linter is itself a finding (edge class 5) if the skill is meant to run where those may be absent.
