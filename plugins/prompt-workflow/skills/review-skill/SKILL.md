---
name: review-skill
description: "Use when auditing or reviewing a skill or agent prompt file — its text quality (removed rules, broken references, bloat, hardcoded values, cross-file consistency, contradictory wording) and its procedural logic (resume/idempotency, step ordering, broken invariants, unhandled edge cases, dependency graphs, destructive-op safety), plus duplication and single-source-of-truth drift across the repo. Audits prompt files — SKILL.md, agent .md, output styles, bundled references — NOT application code. Triggers on review, audit, or check a skill, a prompt, an agent file, or a workflow's logic; --report-only to surface findings without fixing; or /review-skill. A bare \"review\" with no target named also means this inside a plugin or marketplace repo — one whose content is plugins, skills, and agents: there the changed skill and agent files ARE the target."
---

# Skill Audit

Audit prompt files — a skill, an agent, an output style, or the references and templates they bundle — on two levels: whether the prompt still **says** the right thing (the text pass) and whether the procedure it describes actually **behaves** correctly when executed, without duplicated or drifting content around it (the deep lenses). **Zero errors > correctness > speed > brevity.**

- **Text pass** — single-file text quality: removed rules, broken references, bloat, hardcoded values, cross-file consistency, wording contradictions, and steering effectiveness. It audits against two sources: criteria a–x in `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/text-criteria.md`, and the shared authoring catalogue in `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md` — the same file the write-time side follows, so both sides move together.
- **Lens A — procedural logic** — trace the steps as a state machine and find where the procedure breaks, corrupts state, loses data, or deadlocks.
- **Lens B — duplication & SSOT** — find substantial content copied across files and concepts with no canonical home. Lens A and B live in `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/logic-lenses.md`.

**There is one pass and it always runs both layers — there is no cheap mode, by design.** A change that looks like pure wording is exactly the shape whose blast radius lands in another file (Lens B class 12 fires on any rule edit, including a one-line description change), so any "this looks text-only" judgement — the user's or the auditor's — would skip the lenses precisely where they pay. Cost is controlled by **method, never by coverage**: one read per file serving both layers, Lens B swept grep-first instead of by reading siblings, and a report that carries findings rather than narration.

---

**Input**: Optionally specify target files via `$ARGUMENTS`. If omitted, auto-detect changed files via git. One flag: **`--report-only`** surfaces every finding without touching a file. There is no flag that drops a layer.

**Two finding vocabularies, deliberately not merged** — they carry different fix policies, so keep each finding in its own:
- Text-pass findings are rated **SAFE / RISKY / BROKEN / NOTE** and are **auto-fixed without asking** (RISKY and BROKEN, loop to ALL SAFE; NOTEs never).
- Lens findings are rated **CONFIRMED / PLAUSIBLE** with a severity. **CONFIRMED** ones are fixed — *including* the ones resting on a design choice: pick the option you would recommend, apply it, and report the call in `### 我做的抉擇`. Handing the user a menu of findings is not a review, it is the review's work left undone. **PLAUSIBLE** ones are never fixed on a guess — **the default is to go verify it**, and `### 沒審到` takes only the ones verification genuinely cannot reach: record what you could not confirm **and what blocked it** (it is a coverage gap, not a question for the user). "I did not get around to it" is not a blocker — that is unfinished work, and it belongs in the next batch (step 1, batching).

**Steps**

1. **Identify the targets**

   **Scope**: this skill assumes Claude Code plugin structure — agent files matching `**/agents/*.md`, skill files matching `**/skills/*/SKILL.md`, output styles matching `**/output-styles/*.md`, and the prose a skill or plugin bundles alongside them (`**/references/*.md`, `**/templates/*.md`) at any depth. **An output style is prose the model is steered by, so it is audited exactly like a skill** — the same criteria and the same lenses; only Lens A usually reads N/A, because a persona describes no procedure. **A bundled reference is in scope, not an afterthought** — a skill that pushes its criteria or rules into `references/` keeps most of its auditable content there, so a filter that only matched `SKILL.md` would report "nothing to audit" on the very change that rewrote a rule. For non-plugin projects, specify target files explicitly via `$ARGUMENTS`.

   If files are specified, use them. Otherwise auto-detect:
   - Run `git diff --name-only` (uncommitted changes).
   - **If the working tree is clean** (common when this runs right after a commit), fall back to the most recent run of commits instead of stopping. Inspect `git log --oneline`, pick the run of related commits just made, and use `git diff --name-only <base>..HEAD` (default `HEAD~1..HEAD` if a single commit; widen to `HEAD~N..HEAD` to cover a multi-commit range). **Record that range — step 2 reuses it.**
   - Filter to paths matching `**/agents/*.md`, `**/skills/*/SKILL.md`, `**/output-styles/*.md`, `**/references/*.md`, or `**/templates/*.md` (match by path suffix; ignore leading directories like `plugins/<name>/`).
   - **The path globs above are where these files usually live, not the test. Every changed markdown file is in scope by default; what a directory decides is nothing, and what its ROLE decides is which criteria apply.** A plugin may keep authoritative prose anywhere — a `config/` directory, a convention file at the plugin root — and the always-loaded ones are not under `skills/` at all. Three roles:
     - **Prompt** — anything a model is steered by: `SKILL.md`, an agent, an output style, a bundled `references/` / `templates/` / `config/` markdown, and a `CLAUDE.md` (which no skill reads — the harness loads it, which makes it the most expensive prompt in the repo, not an exempt one). Full criteria plus both lenses.
     - **Documentation** — a `README`, a docs page: no agent loads it, so the steering criteria are N/A, but it **still gets the consistency pass** (criterion r, Lens B class 12). It is a copy of rules that live elsewhere, so it goes stale exactly like a summary table row does, and it is the copy a human reads.
     - **Historical record** — a `CHANGELOG`, an archived report: **excluded**, and say so in `### 沒審到`. A past entry describing behavior that has since changed is correct; "fixing" it destroys the record.
     Genuinely machine-readable data (`.json`, `.yaml`, a script) is not prose — the criteria do not apply, though a manifest is still a Lens B surface for a rule that has to land in it.
   - Only if neither uncommitted changes NOR that recent run of commits touch any in-scope file, report that and stop.

   **A changed bundled reference pulls in its owner — a reference and the steps that drive it are ONE unit.** A criterion, rule, or template edited inside `references/` is consumed by steps living in another file, so auditing the reference alone cannot see the break (a step citing a criterion the edit just renamed, a budget the longer list now blows past). So widen the set — **on both branches, explicitly specified paths and auto-detected ones alike** (an explicit reference path is the common case: it is how `/improve-skill` drives this audit):
   - `skills/<name>/references/*.md` or `skills/<name>/templates/*.md` → add `skills/<name>/SKILL.md`.
   - A **plugin-level** `references/*.md` / `templates/*.md` has no single owner — it is read by many skills. Do NOT add them all as targets; instead grep the repo for the file's name and treat the hits as Lens B blast radius (each reader must still state the rule correctly after the edit).
   - **One-way, and deduplicated.** Pulling in a `SKILL.md` does NOT then pull in that skill's other references — the widening stops after one hop, or a two-line edit snowballs into auditing a whole plugin. A file already in the set is audited once, not twice.
   - Name the pulled-in files in the report's `Targets` line, marked as pulled in rather than requested, so the user can see why they were read.

   **The two lenses scope over the file set differently** (this is the routing, and it is per file and per lens — not one switch for the run):
   - **Lens A (logic)** applies to files that describe a **multi-step procedure that mutates state** — sequential steps with ordering, git ops, file writes/deletes, dispatch/handoff, resume/retry, or a dependency graph. A pure knowledge / reference skill (a checklist or style guide, no executable procedure) has no logic to audit — skip it for Lens A only.
   - **Lens B (dedup/SSOT)** applies to **all** target files and the repo around them — a duplicated block or a drifting list lives in any file, procedure or not.

   **If the in-scope set is too big for one pass, batch it — never trim coverage to fit.** Every in-scope file gets the full text pass and both applicable lenses; `### 沒審到` does not buy that back. So when the set is larger than one pass can carry (a wide range of commits, plus the owners the widening above pulled in), order the files by blast radius — the ones other files read come first — and take them **3–5 at a time**. Each batch is a complete pass on its own — steps 2 through 7, the text pass through fix-and-sweep, exactly as an unbatched run does them (so with `--report-only` a batch still surfaces everything and still fixes nothing). Then **continue straight into the next batch in the same run** unless the user stops you; the run is done when no in-scope file is left pending. A batch boundary is a checkpoint, not an exit. Two reporting obligations while any file is still pending: the header carries `第 K 批` and how many in-scope files are untouched, and `### 沒審到` lists those files by path marked `待審（下一批）`. **That list is also the resume input** — a batched run stores its progress nowhere else, so a later run given those paths as targets picks up exactly where this one stopped.

   **A set larger than one run can carry is declared up front, never silently attempted.** "Continue into the next batch" assumes the run can reach the end; a target like an entire marketplace cannot, and pushing on until the context runs out ends the run mid-batch with no `待審` list at all — the one shape that reads as full coverage while covering least. So when the in-scope set is that large, state its size and that this run will not finish it **before the first batch**, work highest-blast-radius first, and stop at a batch boundary with every remaining file listed in `待審（下一批）`. A declared partial scope, finished cleanly, is a complete run; an undeclared one that stops when it runs out is not.

   **Deterministic backstop — run every one of these that is available, before any prose pass.** Mechanical defects are invisible to the criteria: a manifest is not prose, and a frontmatter block that fails to parse still *reads* correctly, so a prose-only review reports ALL SAFE on a skill the harness loads with no metadata at all. Name in the report whichever of the three did not run, and why — an unavailable check is a coverage gap, not a pass.
   - **`claude plugin validate <plugin-root>`** — when the target belongs to a plugin and the `claude` CLI is reachable. It is the only check here that catches a **frontmatter block that is not valid YAML** (usual cause: an unquoted `description:` whose value contains a colon followed by a space — YAML reads that as a new key, so `name` and `description` are silently dropped and the skill loads with empty metadata and never triggers). It reports one such failure per plugin, so re-run it after each fix rather than trusting the first count. Skip it for a non-plugin target, and record the skip.
   - **The repo's own fast validation/structure script** if it ships one (e.g. `scripts/check-*.sh`, or a `validate` / `lint` task) — it encodes that repo's invariants, which the validator knows nothing about. **Neither subsumes the other**: a line-based `name:` extractor passes happily on a frontmatter block that is not valid YAML, so a green repo script says nothing about the validator.
   - **Read the manifest yourself when the target's plugin ships hooks** — `plugin.json` re-declaring the conventional auto-loaded `hooks/hooks.json` is a duplicate that makes the hooks fail to load, and **neither tool above catches it** (verified against `claude plugin validate` on Claude Code 2.1.221); the only surface that reports it is the plugin's load-time error in `/plugin`. The manifest may name *additional* hook files only.

   Fold every failure into the report and fix them in the same cycle as the findings — this is the moment to sweep the mechanical regressions, not only the semantic ones.

2. **Text pass — read each target IN FULL, diff it, and apply the criteria and the shared authoring rules**

   Read **both** of these now, and audit from them rather than from memory — every criterion and every rule applied to every target, with N/A stated explicitly where one does not apply:
   - `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/text-criteria.md` — the rating scale and criteria a–x.
   - `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md` — the shared authoring catalogue, which is what the write-time side follows. **Each entry is a criterion here**: its `→ check:` clause tells you how the violation is visible, and an entry marked `→ process` governs what the author did rather than what the file says, so skip it — skipping those is correct, not a coverage gap. This is the one file that keeps the two sides in step: a rule added there is audited here without editing this skill.

   For each target file:
   - Read the complete file — not just the diff; context determines whether a change is safe.
   - Run `git diff HEAD -- <file>` for uncommitted changes, or `git diff <base>..HEAD -- <file>` using the range recorded in step 1 when the changes are already committed (do NOT use bare `HEAD~1` for a multi-commit range — it misses all but the last commit).
   - **When a target lives outside the current working directory's repo** — explicit paths into another project, which is the normal case when this audit is driven from elsewhere — take the diff with `git -C <that target's repo>` instead. The cwd's git state says nothing about a foreign path, and `git diff HEAD -- <foreign-path>` errors or returns empty, which reads exactly like "nothing changed".
   - **If no diff is obtainable at all** (an untracked new file, no git, a repo you cannot reach), say so in the report's `### 沒審到` and audit the full file text on its own. Every criterion that judges the **change** rather than the standing text — what was removed, softened, silently dropped from a list, or newly asserted (a, b, h, i, q, t among them) — is **N/A without a diff, not passed**; name them, so the gap is not mistaken for coverage. **One carve-out: criterion q's rot-prone half survives a missing diff** — a file whose content goes stale because the codebase moved has nothing in the diff to scope to, which is the normal state of the very target that half exists for, so verify the commands and paths it names regardless.
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

6. **Produce the audit report**

   **Language: Traditional Chinese prose, English ONLY for identifiers** — file paths, section names as they appear in the audited file, rating labels (`RISKY` / `BROKEN` / `NOTE` / `CONFIRMED` / `PLAUSIBLE`), severity literals, criteria letters, lens class numbers. **Section headings are Chinese too**; a half-English heading set reads as an inconsistency rather than a convention.

   **One format, whatever the file count.** The shape below is multi-file native and is the only shape — with a single target the per-file overview is one line and nothing else changes.

   **Order by what the reader must do**, never by how the audit works: what needs them, what is already handled, what was not covered. The text-pass / lens split is internal machinery and must not appear as report structure.

   **Cite by name, not by number** — `<file> › <section or rule name>`. A line number appears in parentheses **only** on a finding the reader still has to act on, and it is the number **re-read after the fixes land** (step 7, fix and sweep). A fixed finding carries no line number at all: the edit already moved it, so the number captured during the trace points at the wrong text.

   **Severity is one of exactly four literals**, most severe first: `data-loss` › `silent-wrong` › `stall` › `cosmetic`. Nothing else — a free-text severity cannot be compared between runs.

````
   ## 審查報告
   <N> 檔（in-scope <M>）· <總數> 個問題，修掉 <X>（其中 <D> 個是抉擇）· **<Y> 個要你回答** · <第 K 批、還有 R 檔待審 — 只有分批時才寫> · <本輪改動造成 | 既有缺陷被翻出來 | 前一輪的修改帶出來的>

   ### 各檔
   | 檔 | 問題 | 已修 | 待回答 |
   |---|---|---|---|
   | ⚠️ `<path>` | <n> | <x> | <y> |
   | ✅ `<path>` | <n> | <x> | — |

   其餘 <k> 檔無 finding。

   ### 要你回答（<Y>｜無）
   - **<file>** › <section name>（`:<current line>`）
     <what is wrong, one or two sentences> → 只有你答得出來：<the fact that lives outside every file you can read> → 我會選 <the option you would take>

   ### 我做的抉擇（<D>｜無）
   - **<file>** › <section name> — <the call> → 選 <what you applied>、不選 <the option you rejected>：<why, one sentence>

   ### 已修（<X>）
   - **<file>** › <section name> — <what was wrong> → <what changed>　`<severity>`

   ### 看似違規但正確（optional — only when it would mislead the next pass into "fixing" it）
   - **<file>** › <section name> — <why it holds>

   ### 沒審到
   - <what the sweep structurally cannot see — e.g. duplication between two files neither of which changed>
   - <anything skipped, and why: an upstream-synced body, an absent tool, a target outside scope>
````

   Four sections are **mandatory on every run**, because a missing section is indistinguishable from a clean one:
   - `### 要你回答` — write `無` when there is nothing, **and it usually is `無`**. It is the **first finding section**, ahead of `已修` and everything after it, because it is the only part that costs the reader work — which is exactly why the bar for putting something here is so high. **The only admissible reason is a fact that lives outside every file you can read**: whether the user wants the capability at all, a business or product requirement, a constraint they hold and you do not. **"Two valid designs" is NOT that** — that is `### 我做的抉擇`, decided and applied. A finding parked here that you could have resolved by reading one more file is the failure this section exists to prevent.
   - `### 我做的抉擇` — write `無` when there is nothing. Every judgement call you resolved: what you picked, what you rejected, one line of why. This is what keeps the user in the loop **after** the work instead of blocking on them before it; a run that decides things and does not list them here is worse than one that asked. It sits **above `### 已修`** for that reason — a call they might overrule outranks a mechanical fix they will just accept. **Each one is listed here and nowhere else**, and it still counts inside `已修 <X>`: `<D>` is a subset of `<X>`, not a total beside it, so the same fix is never printed twice.
   - `### 各檔` — a table, only files that have findings, `⚠️` rows first; close with one sentence counting the clean files instead of listing them. **The status glyph prefixes the path inside the file cell** — `⚠️` when the file still needs the reader, `✅` when everything in it is fixed — which keeps the glyphs in one scannable column without spending a column on them. Terminal output renders markdown, not ANSI colour, so the glyph is what carries the at-a-glance grouping: **two glyphs only, never a third**, and an em dash for a zero count so the eye does not read `0` as a finding.
   - `### 沒審到` — **its admission bar is as high as `### 要你回答`'s, and for the same reason**: it is the section that declares what never got looked at, so what gets in is only ever a limit of the method, never a limit of your effort. Admissible: the blast-radius sweep's own blind spot (Lens B's token grep sees only what the change touched); a criterion the missing diff makes N/A (step 2, the text pass); a body the repo does not own, e.g. an upstream-synced skill; a deterministic check that was unavailable; a role step 1 excludes, e.g. a `CHANGELOG` or an archived report; and a PLAUSIBLE finding you could not raise to CONFIRMED, with what blocked the verification named. **An in-scope file you simply did not audit is NOT admissible** — it goes into the next batch, and the only line it may occupy here is a `待審（下一批）` entry. Silence here reads as full coverage; a long list of genuine skips reads as an unfinished run, because it is one.

   **The header's last clause is the convergence signal, and it decides whether the user runs again.** Do not default to "本輪改動造成": a second pass usually runs in a fresh session where the earlier one left no trace, so when the history is not visible, judge by the findings' shape instead — fix-shaped commits sitting on top of the change, or findings landing on text the diff just added. Say plainly which of the three it is: the change's own doing, pre-existing defects being uncovered (keep going, coverage is still growing), or defects an earlier pass's fixes introduced (the rounds are converging on shallower shapes). Without it, a reader on the third round can only conclude the code is hopeless, when the truth is usually that each round is smaller than the last.

7. **Fix and sweep the blast radius** (skipped entirely if `--report-only` was passed)

   Text-pass fixes already happened in step 2; the *finding* work here covers the Lens A / Lens B findings. Apply the **CONFIRMED** ones directly (e.g. reorder two steps so reconcile precedes the mutation; add the missing guard).

   **A fix resting on a design choice — which of two contradictory rules wins, what the safe default should be — is still yours to make.** Pick the option you would recommend, apply it, and record the call for `### 我做的抉擇`. Do not park it for the user: a list of findings handed back is the review's own work left undone, and it arrives at the moment they have least context to judge it. Two traps that make a decision *look* like theirs when it is not:
   - **A constraint you proposed earlier in the conversation is not their requirement.** If the correct fix needs it dropped, drop it and say so in the 抉擇 list. Defending your own earlier framing is the most common reason a run stalls on a question nobody asked.
   - **Blast radius is not a veto.** "This changes another file / another skill" is a reason to sweep further, not to stop — the sweep below is exactly that step.

   Escalate to `### 要你回答` **only** when the answer lives outside every file you can read (does the user want this capability at all; a product or business constraint they hold and you do not). **Never apply a fix to a PLAUSIBLE finding** — go verify it up to CONFIRMED, and record it in `### 沒審到` only when the verification is genuinely blocked, naming what blocked it. It does **not** go to `### 要你回答`: "I am not sure" is your gap to close or declare, not a decision the user can make for you. After applying, re-read the affected procedure to confirm the fix did not introduce a new ordering/edge defect.

   **Then sweep each fix's blast radius before calling the pass done — this is what stops the next run from re-finding your own work.** This sweep covers **every fix applied in this pass, the step 2 text fixes included**, because a text fix leaves the same stale copies behind as a logic fix and step 2's own loop does not sweep for them. A fix to a rule almost never lives alone: the same rule is usually also stated in a summary table, a checklist line, a template comment, a pointer, or a per-role contract. So run Lens B's token grep against **what you just wrote** instead of against the diff — same mechanic — and every hit must now state the new version, state the *other* branch of the rule correctly, or be unrelated. A fix that landed in one of six places is class 12, and finding it here costs one grep; finding it on the next pass costs a whole audit round. The sweep's own **blind spot** goes in the report's `### 沒審到` section: the token grep sees only what the change touched, so duplication between two untouched files does not surface.

   **Last, re-read the line numbers for every finding left in `### 要你回答`.** The fixes just applied moved everything below them, so a number captured during the trace now points at the wrong text — resolve each open finding's current line from the file as it stands, and cite the section name alongside it so the reference survives the next edit too.

---

## Guardrails

- **Read the FULL file, not just the diff** — context determines whether a change is safe, and logic defects live in step interactions, including with unchanged steps.
- **Trace, don't skim** — a lens finding is only real when you can name the input/interruption and the wrong outcome it produces.
- **Be strict on text, conservative on logic** — flag anything even slightly questionable as RISKY in the text pass; but a spec/workflow intentionally leaves room for agent judgment, so do not flag underspecification as a logic defect unless a concrete execution goes wrong.
- **Save tokens by method, never by coverage** — every run does the text pass and both lenses. Spend less by reading each file once for both layers, sweeping Lens B grep-first, and reporting findings instead of narrating the work — never by dropping a criterion or a lens. **When method alone cannot make the set fit, batch it and keep going (step 1) — do not settle it in `### 沒審到`**: that section reports what the method cannot see, never what the run did not get to. If something genuinely was not audited, say so in the report rather than letting silence read as coverage.
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
- **Fix it, don't hand over a menu** — RISKY/BROKEN text findings are fixed immediately and re-audited until clean, and a logic or consolidation fix that picks between two valid designs is **yours to decide**: apply what you would recommend and list it in `### 我做的抉擇`. Escalate only what the user alone can answer (see step 7, fix and sweep). The report keeps them in the loop after the work; a confirmation gate before it just moves the work onto them. Pass `--report-only` to surface everything without touching files.
