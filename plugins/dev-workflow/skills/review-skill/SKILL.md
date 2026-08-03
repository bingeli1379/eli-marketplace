---
name: review-skill
description: Use when auditing or reviewing a skill or agent prompt file — its text quality (removed rules, broken references, bloat, hardcoded values, cross-file consistency, contradictory wording) and its procedural logic (resume/idempotency, step ordering, broken invariants, unhandled edge cases, dependency graphs, destructive-op safety), plus duplication and single-source-of-truth drift across the repo. Audits prompt files — SKILL.md, agent .md, output styles, bundled references — NOT application code. Triggers on review, audit, or check a skill, a prompt, an agent file, or a workflow's logic; --report-only to surface findings without fixing; or /review-skill.
---

# Skill Audit

Audit agent and skill prompt files on two levels: whether the prompt still **says** the right thing (the text pass) and whether the procedure it describes actually **behaves** correctly when executed, without duplicated or drifting content around it (the deep lenses). **Zero errors > correctness > speed > brevity.**

- **Text pass** — single-file text quality: removed rules, broken references, bloat, hardcoded values, cross-file consistency, wording contradictions, and steering effectiveness. It audits against two sources: criteria a–x in `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/text-criteria.md`, and the shared authoring catalogue in `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md` — the same file the write-time side follows, so both sides move together.
- **Lens A — procedural logic** — trace the steps as a state machine and find where the procedure breaks, corrupts state, loses data, or deadlocks.
- **Lens B — duplication & SSOT** — find substantial content copied across files and concepts with no canonical home. Lens A and B live in `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/logic-lenses.md`.

**There is one pass and it always runs both layers — there is no cheap mode, by design.** A change that looks like pure wording is exactly the shape whose blast radius lands in another file (Lens B class 12 fires on any rule edit, including a one-line description change), so any "this looks text-only" judgement — the user's or the auditor's — would skip the lenses precisely where they pay. Cost is controlled by **method, never by coverage**: one read per file serving both layers, Lens B swept grep-first instead of by reading siblings, and a report that carries findings rather than narration.

---

**Input**: Optionally specify target files via `$ARGUMENTS`. If omitted, auto-detect changed files via git. One flag: **`--report-only`** surfaces every finding without touching a file. There is no flag that drops a layer.

**Two finding vocabularies, deliberately not merged** — they carry different fix policies, so keep each finding in its own:
- Text-pass findings are rated **SAFE / RISKY / BROKEN / NOTE** and are **auto-fixed without asking** (RISKY and BROKEN, loop to ALL SAFE; NOTEs never).
- Lens findings are rated **CONFIRMED / PLAUSIBLE** with a severity, and only **CONFIRMED, unambiguous** ones are auto-fixed — anything resting on a design choice is surfaced for the user to decide, never guessed.

**Steps**

1. **Identify the targets**

   **Scope**: this skill assumes Claude Code plugin structure — agent files matching `**/agents/*.md`, skill files matching `**/skills/*/SKILL.md`, and the prose a skill or plugin bundles alongside them (`**/references/*.md`, `**/templates/*.md`) at any depth. **A bundled reference is in scope, not an afterthought** — a skill that pushes its criteria or rules into `references/` keeps most of its auditable content there, so a filter that only matched `SKILL.md` would report "nothing to audit" on the very change that rewrote a rule. For non-plugin projects, specify target files explicitly via `$ARGUMENTS`.

   If files are specified, use them. Otherwise auto-detect:
   - Run `git diff --name-only` (uncommitted changes).
   - **If the working tree is clean** (common when this runs right after `/commit`), fall back to the most recent commit batch instead of stopping. Inspect `git log --oneline`, pick the run of related commits just made, and use `git diff --name-only <base>..HEAD` (default `HEAD~1..HEAD` if a single commit; widen to `HEAD~N..HEAD` to cover a multi-commit batch). **Record that range — step 2 reuses it.**
   - Filter to paths matching `**/agents/*.md`, `**/skills/*/SKILL.md`, `**/references/*.md`, or `**/templates/*.md` (match by path suffix; ignore leading directories like `plugins/<name>/`).
   - Only if neither uncommitted changes NOR the recent commit batch touch any in-scope file, report that and stop.

   **A changed bundled reference pulls in its owner — a reference and the steps that drive it are ONE unit.** A criterion, rule, or template edited inside `references/` is consumed by steps living in another file, so auditing the reference alone cannot see the break (a step citing a criterion the edit just renamed, a budget the longer list now blows past). So widen the set — **on both branches, explicitly specified paths and auto-detected ones alike** (an explicit reference path is the common case: it is how `/improve-skill` drives this audit):
   - `skills/<name>/references/*.md` or `skills/<name>/templates/*.md` → add `skills/<name>/SKILL.md`.
   - A **plugin-level** `references/*.md` / `templates/*.md` has no single owner — it is read by many skills. Do NOT add them all as targets; instead grep the repo for the file's name and treat the hits as Lens B blast radius (each reader must still state the rule correctly after the edit).
   - **One-way, and deduplicated.** Pulling in a `SKILL.md` does NOT then pull in that skill's other references — the widening stops after one hop, or a two-line edit snowballs into auditing a whole plugin. A file already in the set is audited once, not twice.
   - Name the pulled-in files in the report's `Targets` line, marked as pulled in rather than requested, so the user can see why they were read.

   **The two lenses scope over the file set differently** (this is the routing, and it is per file and per lens — not one switch for the run):
   - **Lens A (logic)** applies to files that describe a **multi-step procedure that mutates state** — sequential steps with ordering, git ops, file writes/deletes, dispatch/handoff, resume/retry, or a dependency graph. A pure knowledge / reference skill (a checklist or style guide, no executable procedure) has no logic to audit — skip it for Lens A only.
   - **Lens B (dedup/SSOT)** applies to **all** target files and the repo around them — a duplicated block or a drifting list lives in any file, procedure or not.

   **Deterministic backstop**: if the repo ships its own fast validation/structure script (e.g. `scripts/check-*.sh`, or a `validate` / `lint` task), run it up front and fold any failures into the report — this is the moment to sweep the mechanical regressions too, not only the semantic ones.

2. **Text pass — read each target IN FULL, diff it, and apply the criteria and the shared authoring rules**

   Read **both** of these now, and audit from them rather than from memory — every criterion and every rule applied to every target, with N/A stated explicitly where one does not apply:
   - `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/text-criteria.md` — the rating scale and criteria a–x.
   - `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md` — the shared authoring catalogue, which is what the write-time side follows. **Each entry is a criterion here**: its `→ check:` clause tells you how the violation is visible, and an entry marked `→ process` governs what the author did rather than what the file says, so skip it — skipping those is correct, not a coverage gap. This is the one file that keeps the two sides in step: a rule added there is audited here without editing this skill.

   For each target file:
   - Read the complete file — not just the diff; context determines whether a change is safe.
   - Run `git diff HEAD -- <file>` for uncommitted changes, or `git diff <base>..HEAD -- <file>` using the range recorded in step 1 when the changes are already committed (do NOT use bare `HEAD~1` for a multi-commit batch — it misses all but the last commit).
   - Rate each finding SAFE / RISKY / BROKEN / NOTE.

   Then, unless `--report-only` was passed, **fix the RISKY and BROKEN findings immediately — do NOT ask.** After fixing, re-run this step on the fixed files; repeat until every file is SAFE, max 3 rounds. If files remain unSAFE after 3 rounds, carry the remainder into the step 6 report and stop looping. **NOTES are never auto-fixed** — they ride along for the user to act on or ignore, never affect a rating, and never trigger the loop; acting on one unasked would delete battle-tested content on an unobservable hunch, which criteria k and w forbid.

   Fixing here (rather than after the lenses) is deliberate: step 3's state-machine map then works on the current, fixed text. With `--report-only` nothing is fixed and the trace runs against the text as-is.

3. **Map each target as a state machine**

   For each procedure, note: the ordered steps, what state each reads and mutates (files, git history, checkboxes, dispatched work), the branches/decisions, the claimed invariants, and the abort/error paths. For a change with related files (an orchestrator + the skills it drives), read them together — the defect is often at the seam. Step 2 already read the files in full; do not re-read what is already in context.

4. **Hunt the defect classes**

   Read `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/logic-lenses.md` now — it holds Lens A classes 1–9, Lens B classes 10–12, and Lens B's grep-first sweep procedure with its token budget. Work through **every** class for every in-scope target (per the step 1 per-lens scoping), and follow Lens B's sweep method as written: derive distinctive tokens from what the change touched, grep repo-wide, read only the hits. Reading every sibling file is the wrong method — it costs more and finds less than the grep.

5. **Rate and verify each lens finding**

   - **CONFIRMED** — you traced a concrete failing scenario (specific inputs/state → specific wrong outcome). **PLAUSIBLE** — looks risky but you could not fully confirm; say what you could not verify.
   - **Severity**, most-severe first: data loss / state corruption > silent wrong result that ships > recoverable stall / degraded behavior > cosmetic.
   - **Be conservative.** A workflow deliberately leaves judgment to the executing agent — flag genuine logic defects, not "this could be more explicit." Every finding must carry a concrete failure scenario; if you cannot state one, it is not a finding.

6. **Produce the audit report** (Traditional Chinese; technical terms, file names, and rating labels stay English)

   **Finding format is MANDATORY structured** — every finding carries a location (`file:line`), what changed, and the risk / failure / rationale. A bare description is not acceptable output.

   One combined report. Do not print the text pass as its own separate report; fold its verdict into the block:

   ```
   ## Skill Audit

   ### Targets: <files requested or detected> — pulled in as an owner: <files added by the reference→owner rule, or "none">

   ### Text pass: <ALL SAFE / HAS RISKS / HAS BROKEN> — <one line per file: what was fixed, or what remains>

   ### Text-pass findings still open (every RISKY / BROKEN not fixed — always populated under --report-only, since nothing was fixed; omit only when there are none)
   - **[RISKY|BROKEN]** `file:line` <what changed> — risk / will cause: <the consequence> — 修法: <concrete action>

   ### Text-pass NOTES (advisory — never fixed, never counted in a rating; omit the section when there are none)
   - `file:line` <observation> — <why it is the user's call, not the auditor's>

   ### Findings (most severe first)
   - **[SEVERITY] [CONFIRMED/PLAUSIBLE] [Lens A|B] `file:line`** — <the defect>
     - Lens A → 失敗情境: <concrete inputs/state → wrong outcome> | Lens B → 重複/漂移: <the copies and how they drift>
     - 修法方向: <how to fix — note when it is a design choice, e.g. DRY vs deliberate self-containment>

   ### Categories judged sound
   - <class>: <one line why it holds>

   ### Convergence: <first pass on this change | N of M findings trace to fixes applied in an earlier pass of this same change — <what shape they were> | earlier passes not visible from here — <what you could still infer from the diff>>

   ### Verdict: <N confirmed, M plausible | or "no defects found">

   ### Fix sweep: <tokens grepped — N hits — what changed as a result, one line per applied fix; plus anything the sweep could not cover | no fixes applied>
   ```

   The `Fix sweep` line is filled in by step 7 and appended after the fixes land; with `--report-only` write "no fixes applied".

   **The convergence line is what tells the user whether to run again**, so state it on every pass. Only claim "first pass on this change" when you can see it is one — the change is uncommitted and nothing in this session already audited it. **A second pass is usually run in a fresh session, where the earlier pass left no trace**, so do not default to "first pass": say the earlier passes are not visible, then infer what you can from the change itself (fix-shaped commits on top of the original change, or findings that land on text the diff just added). When findings keep appearing across repeated runs, say plainly whether they are **pre-existing defects being uncovered** (keep going — coverage is still growing) or **defects the previous pass's own fixes introduced** (the rounds are converging on shallower shapes; name the trend and say whether it is worth another run). Without it a user reading a third round of findings can only conclude the code is hopeless, when the truth is usually that each round is smaller and shallower than the last.

7. **Fix and sweep the blast radius** (skipped entirely if `--report-only` was passed)

   Text-pass fixes already happened in step 2; the *finding* work here covers the Lens A / Lens B findings. Apply the **CONFIRMED, unambiguous** ones directly (e.g. reorder two steps so reconcile precedes the mutation; add the missing guard). For any fix resting on a **design choice** (which of two contradictory rules wins, what the safe default should be), do NOT guess — present the options and let the user decide. Never apply a fix to a PLAUSIBLE finding without confirming it first. After applying, re-read the affected procedure to confirm the fix did not introduce a new ordering/edge defect.

   **Then sweep each fix's blast radius before calling the pass done — this is what stops the next run from re-finding your own work.** This sweep covers **every fix applied in this pass, the step 2 text fixes included**, because a text fix leaves the same stale copies behind as a logic fix and step 2's own loop does not sweep for them. A fix to a rule almost never lives alone: the same rule is usually also stated in a summary table, a checklist line, a template comment, a pointer, or a per-role contract. So run Lens B's token grep against **what you just wrote** instead of against the diff — same mechanic — and every hit must now state the new version, state the *other* branch of the rule correctly, or be unrelated. A fix that landed in one of six places is class 12, and finding it here costs one grep; finding it on the next pass costs a whole audit round. **Report the sweep** in the `### Fix sweep` line: which tokens you grepped, how many hits, what you changed, and what the sweep could not cover.

---

## Guardrails

- **Read the FULL file, not just the diff** — context determines whether a change is safe, and logic defects live in step interactions, including with unchanged steps.
- **Trace, don't skim** — a lens finding is only real when you can name the input/interruption and the wrong outcome it produces.
- **Be strict on text, conservative on logic** — flag anything even slightly questionable as RISKY in the text pass; but a spec/workflow intentionally leaves room for agent judgment, so do not flag underspecification as a logic defect unless a concrete execution goes wrong.
- **Save tokens by method, never by coverage** — every run does the text pass and both lenses. Spend less by reading each file once for both layers, sweeping Lens B grep-first, and reporting findings instead of narrating the work — never by dropping a criterion or a lens. If something genuinely was not audited, say so in the report rather than letting silence read as coverage.
- **Keep each layer in its own file** — detection-only criteria in `text-criteria.md`, lenses in `logic-lenses.md`, and the rules shared with the write-time side in the plugin's `authoring-rules.md`. Never restate one inside another, never inline any of them back into this file, and when a finding is really a missing *rule*, add it to the shared catalogue rather than here — that is what keeps writing and auditing from drifting apart.
- **Never approve removal of**: ZERO MISSES directives, mandatory phase instructions, security-related comments, severity-level distinctions in reports, engineering-checklist principles, project-specific conventions that the model cannot infer on its own
- **Compression is not always good** — shorter prompts that lose clarity are worse than longer prompts that work correctly
- **Bloat is also a risk** — but ONLY for verbose explanations and tutorials, not for concise rules or constraints
- **Presume existing content is battle-tested** — every rule in the prompt was likely added because the agent failed without it. The burden of proof is on removal.
- **No tooling / environment assumptions** — rules must not assume a linter, formatter, test runner, or CI is present; and a procedure that assumes git, a single repo, or a linter is itself a finding (Lens A class 5) when the skill is meant to run where those may be absent.
- **Claude-first; defer cross-harness to a compile step** — never rate a Claude-specific construct as a portability liability. The full do-not-flag list and the three genuine Claude-correctness bugs are criterion (s); do not restate them here.
- **Prefer generic over hardcoded** — prompts should work across projects. Hardcoded values (URLs, names, paths, versions) need justification; if a value could vary, parameterize or conditionalize it
- **Steering must change behavior, and sharpening beats deleting** — fix a weak rule by strengthening it, never by cutting it. The precedence that settles the conflicts lives with the criteria: (h) over (v) on force, (k) over (w) on the burden of proof, and (w)/(x) stay **NOTE** because they rest on what the file cannot show you.
- **Zero errors is the absolute principle** — when in doubt on the text layer, rate as RISKY and fix it
- **Auto-fix the text layer, don't ask; ask on a design choice** — RISKY/BROKEN text findings are fixed immediately and re-audited until clean, while a logic or consolidation fix that picks between two valid designs is surfaced for the user. Pass `--report-only` to surface everything without touching files.
