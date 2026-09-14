---
name: review-skill
description: "Use when auditing or reviewing a skill or agent prompt file — its text quality (removed rules, broken references, bloat, hardcoded values, cross-file consistency, contradictory wording) and its procedural logic (resume/idempotency, step ordering, broken invariants, unhandled edge cases, dependency graphs, destructive-op safety), plus duplication and single-source-of-truth drift across the repo. Audits prompt files — SKILL.md, agent .md, output styles, bundled references — NOT application code. Triggers on review, audit, or check a skill, a prompt, an agent file, or a workflow's logic; --report-only to surface findings without fixing; or /review-skill. A bare \"review\" with no target named also means this inside a plugin or marketplace repo — one whose content is plugins, skills, and agents: there the changed skill and agent files ARE the target."
---

# Skill Audit

Audit prompt files — a skill, an agent, an output style, or the references and templates they bundle — on two levels: whether the prompt still **says** the right thing (the text pass) and whether the procedure it describes actually **behaves** correctly when executed, without duplicated or drifting content around it (the deep lenses). **Zero errors > correctness > speed > brevity.**

- **Text pass** — single-file text quality, audited against criteria a–z in `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/text-criteria.md` and the shared authoring catalogue in `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md` — the same file the write-time side follows, so both sides move together.
- **Lens A — procedural logic** — trace the steps as a state machine and find where the procedure breaks, corrupts state, loses data, or deadlocks.
- **Lens B — duplication & SSOT** — substantial content copied across files, and concepts with no canonical home. Both lenses live in `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/logic-lenses.md`.

**Every run does the text pass and both lenses; there is no cheaper mode.** A one-line wording change lands its blast radius in another file (Lens B class 12 fires on any rule edit), so no "this looks text-only" judgement skips a layer. Cost is controlled by method — one read per file serving both layers, Lens B swept grep-first, a report carrying findings rather than narration — never by coverage.

---

**Input**: target files as arguments, or auto-detect via git. One flag, **`--report-only`**: surface every finding, touch no file.

**Two finding vocabularies, deliberately not merged** — they carry different fix policies:
- Text-pass findings: **SAFE / RISKY / BROKEN / NOTE**. RISKY and BROKEN are fixed without asking, looping to ALL SAFE; NOTEs never.
- Lens findings: **CONFIRMED / PLAUSIBLE** with a severity. CONFIRMED ones are fixed — including those resting on a design choice: pick the option you would recommend, apply it, report the call in `### 我做的抉擇`. PLAUSIBLE ones are never fixed on a guess: verify them up to CONFIRMED, and only what verification genuinely cannot reach goes to `### 沒審到`, with what blocked it.

**Steps**

1. **Identify the targets**

   **Scope is anything a model is steered by, wherever it lives** — `**/skills/*/SKILL.md`, `**/agents/*.md`, `**/output-styles/*.md`, bundled `references/`, `templates/`, `config/` markdown at any depth, and a `CLAUDE.md` (harness-loaded, so the most expensive prompt in the repo). An output style is audited exactly like a skill; Lens A usually reads N/A for it. The directory decides nothing; the file's role decides which criteria apply:
   - **Prompt** — full criteria plus both lenses.
   - **Documentation** (a README, a docs page) — the consistency pass only (criterion r, Lens B class 12): it is the human-read copy of rules that live elsewhere, and it goes stale like any copy.
   - **Historical record** (a CHANGELOG, an archived report) — excluded, and said so in `### 沒審到`; a past entry describing behavior that has since changed is correct.
   Machine-readable data (`.json`, `.yaml`, a script) is not prose; a manifest is still a Lens B surface for a rule that has to land in it.

   Explicit paths are the targets. Otherwise `git diff --name-only`; on a clean tree, the most recent run of related commits from `git log --oneline` as `git diff --name-only <base>..HEAD` — **record that range; step 2, the text pass, reuses it.** If neither touches an in-scope file, report that and stop.

   **A changed bundled reference pulls in its owner — the two are one unit.** `skills/<name>/references/*.md` or `templates/*.md` → add `skills/<name>/SKILL.md`, on explicit and auto-detected paths alike. A plugin-level `references/*.md` has many readers: grep the repo for its filename and treat the hits as Lens B blast radius, not as targets. **The second hop takes coupled siblings, never the directory.** A sibling is *coupled* when either file cites the other by filename or by a unit inside it (a criterion letter, a lens class number, a section name), or when the owner's steps apply the two together in one pass — one grep of the changed file's name and the owner's own steps settle it, in both directions. A coupled sibling becomes a **consulted** file: read in step 4, hunt the defect classes, and compared against the changed file for their coupling only — not text-passed, pulling in nothing further, taking no batch slot; its own standing defects are not this run's business. Mark them in `### 各檔` — `（帶入）` for a pulled-in owner, `（僅比對）` for a consulted file.

   **Per-lens scoping**: Lens A applies to files describing a multi-step procedure that mutates state — ordering, git ops, file writes, dispatch, resume, a dependency graph; a pure knowledge skill skips Lens A only. Lens B applies to every target and the repo around it.

   **Batching**: when the set is larger than one pass carries, order by blast radius — files other files read come first — and take a batch at a time; each batch runs steps 2 through 7 in full (with `--report-only` it still fixes nothing), then continue into the next unless stopped. While files are pending, the header carries `第 K 批` and how many are untouched, and `### 沒審到` lists them as `待審（下一批）` — that list is the resume input, since the run stores progress nowhere else. **A set one run cannot finish is declared before the first batch**, worked highest-blast-radius first, and stopped at a batch boundary with every remaining file listed; a run that pushes on until context runs out leaves no `待審` list and reads as full coverage.

   **Deterministic backstop — run each available check before any prose pass**, and name in the report whichever did not run and why:
   - **`claude plugin validate <plugin-root>`** when the target is in a plugin and the `claude` CLI is reachable. The only check that catches a **frontmatter block that is not valid YAML** (usual cause: an unquoted `description:` containing a colon followed by a space — YAML reads it as a new key, `name` and `description` are silently dropped, and the skill never triggers). It reports one such failure per plugin; re-run after each fix. Skip for a non-plugin target and record the skip.
   - **The repo's own structure script** (`scripts/check-*.sh`, a `validate` / `lint` task) — it encodes that repo's invariants. **Neither subsumes the other**: a line-based `name:` extractor passes a frontmatter block that is not valid YAML.
   - **The manifest, read yourself, when the plugin ships hooks** — `plugin.json` re-declaring the conventional `hooks/hooks.json` makes the hooks fail to load, and neither tool above catches it (verified against `claude plugin validate` on Claude Code 2.1.221); the manifest may name *additional* hook files only.
   Fold every failure into the same fix cycle as the findings.

2. **Text pass — read each target IN FULL, diff it, and apply the criteria and the shared authoring rules**

   Read both files now and audit from them rather than from memory — every criterion and every rule applied to every target, N/A stated explicitly where one does not apply:
   - `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/text-criteria.md` — the rating scale and criteria a–z.
   - `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md` — **each entry is a criterion here**: its `→ check:` clause says how the violation is visible; an entry marked `→ process` governs the author rather than the file, and skipping it is correct.

   For each target: read the complete file, not just the diff. Diff it — `git diff HEAD -- <file>` for uncommitted changes; `git diff <base>..HEAD -- <file>` with the range recorded in step 1 for committed ones (a bare `HEAD~1` misses all but the last commit of a range); `git -C <that target's repo>` for a target outside the cwd's repo, where `git diff HEAD -- <foreign-path>` errors or returns empty and reads exactly like "nothing changed". **If no diff is obtainable** (an untracked file, no git, an unreachable repo), say so in `### 沒審到` and audit the full text; every criterion that judges the *change* — a, b, h, i, q, t among them — is **N/A, not passed**, and is named. Carve-out: criterion q's rot-prone half still runs — verify every command and path the file names. Rate each finding SAFE / RISKY / BROKEN / NOTE.

   Then, unless `--report-only` was passed, **fix the RISKY and BROKEN findings immediately — do NOT ask** — and re-run this step on the fixed files until every file is SAFE, max 3 rounds; carry any remainder into the step 6 report. **NOTEs are never auto-fixed** — they ride along for the user, never affect a rating, never trigger the loop; acting on one unasked would decide something the file cannot show you, which is exactly what criterion k reserves the NOTE for. Fixing here, before the lenses, is deliberate: step 3 then maps the fixed text.

3. **Map each target as a state machine**

   For each procedure: the ordered steps, what state each reads and mutates (files, git history, checkboxes, dispatched work), the branches, the claimed invariants, the abort and error paths. Read related files together — an orchestrator with the skills it drives — since the defect is usually at the seam. Do not re-read what step 2 already has in context.

4. **Hunt the defect classes**

   Read `${CLAUDE_PLUGIN_ROOT}/skills/review-skill/references/logic-lenses.md` now — Lens A classes 1–9 and 13–14, Lens B classes 10–12, and Lens B's grep-first sweep with its token budget. Work through **every** class for every in-scope target, per step 1's per-lens scoping. Sweep Lens B grep-first — distinctive tokens from what the change touched, grepped repo-wide, only the hits read — never every sibling. The consulted files from step 1 are the one exception: read each against the changed file for their coupling only, because a split whose two halves share no token is what the grep cannot see.

5. **Rate and verify each lens finding**

   **CONFIRMED** — a concrete failing scenario traced (specific inputs/state → specific wrong outcome). **PLAUSIBLE** — looks risky, not fully confirmed; say what you could not verify. **Severity**, most severe first: data loss / state corruption > silent wrong result that ships > recoverable stall / degraded behavior > cosmetic. A workflow deliberately leaves judgment to the executing agent — a finding is a genuine logic defect with a concrete failure scenario; without one it is not a finding.

6. **Produce the audit report**

   **Traditional Chinese prose, English only for identifiers** — file paths, section names as they appear in the audited file, rating labels, severity literals, criteria letters, lens class numbers; section headings Chinese too. **One format whatever the file count** — a single target makes the per-file overview one line. **Order by what the reader must do** — what needs them, what is handled, what was not covered; the text-pass / lens split does not appear as structure. **Cite by name** — `<file> › <section or rule name>`; a line number only on a finding the reader still has to act on, and re-read after step 7's fixes, since a fixed finding's number points at moved text. **Severity is one of exactly four literals**, most severe first: `data-loss` › `silent-wrong` › `stall` › `cosmetic`.

````
   ## 審查報告
   <N> 檔（in-scope <M>）· <總數> 個問題，修掉 <X>（其中 <D> 個是抉擇）· **<Y> 個要你回答** · <第 K 批、還有 R 檔待審 — 只有分批時才寫> · <本輪改動造成 | 既有缺陷被翻出來 | 前一輪的修改帶出來的>

   ### 各檔
   | 檔 | 問題 | 已修 | 待回答 |
   |---|---|---|---|
   | ⚠️ `<path>` | <n> | <x> | <y> |
   | ✅ `<path>` | <n> | <x> | — |

   其餘 <k> 檔無 finding。<僅比對過、沒有 finding 的檔，逐一列出 — 沒有就整句省略>

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

   Four sections are **mandatory on every run** — a missing section is indistinguishable from a clean one:
   - `### 要你回答` — `無` when empty, **and it usually is**. The first finding section because it is the only one that costs the reader work. Admissible only for a fact that lives outside every file you can read — whether the user wants the capability at all, a business or product constraint they hold. "Two valid designs" is `### 我做的抉擇`, decided and applied; a finding parked here that one more file would have resolved is the failure this section exists to prevent.
   - `### 我做的抉擇` — `無` when empty. Every judgement call you resolved: what you picked, what you rejected, one line of why. Above `### 已修` because a call they might overrule outranks a fix they will accept. Each is listed here and nowhere else, and still counts inside `已修 <X>` — `<D>` is a subset of `<X>`.
   - `### 各檔` — a table of the files with findings, `⚠️` rows (still need the reader) first, then `✅` (everything fixed); the glyph prefixes the path inside the file cell, **two glyphs only**, an em dash for a zero count. Close with one sentence counting the clean files and naming the consulted files that produced none.
   - `### 沒審到` — admissible only as a limit of the method, never of effort: Lens B's grep blind spot (two untouched files duplicating each other), a criterion the missing diff makes N/A, a body the repo does not own (an upstream-synced skill), an unavailable deterministic check, an excluded role (a CHANGELOG, an archived report), and a PLAUSIBLE finding with what blocked its verification. **An in-scope file you did not audit is not admissible** — its only line here is `待審（下一批）`.

   **The header's last clause is the convergence signal**, and it decides whether the user runs again. Do not default to 本輪改動造成 — a later pass usually runs in a fresh session, so judge by the findings' shape: fix-shaped commits on top of the change, or findings landing on text the diff just added. Say which of the three it is: the change's own doing; pre-existing defects uncovered (coverage still growing); or defects an earlier pass's fixes introduced (rounds converging).

7. **Fix and sweep the blast radius** (skipped entirely if `--report-only` was passed)

   Text fixes already landed in step 2; apply the **CONFIRMED** lens findings directly (reorder two steps so reconcile precedes the mutation; add the missing guard). **A fix resting on a design choice — which of two contradictory rules wins, what the safe default is — is yours to make**: pick the option you would recommend, apply it, record it for `### 我做的抉擇`. Two traps: **a constraint you proposed earlier in the conversation is not the user's requirement** — if the fix needs it dropped, drop it and say so; and **blast radius is not a veto** — another file changing is a reason to sweep further. Escalate to `### 要你回答` only what lives outside every file you can read. **Never apply a fix to a PLAUSIBLE finding** — verify it to CONFIRMED, or record it in `### 沒審到` with what blocked it; it does not go to `### 要你回答`. After applying, re-read the affected procedure for a new ordering or edge defect.

   **Then sweep each fix's blast radius — every fix in this pass, step 2's text fixes included.** A rule also lives in a summary table, a checklist line, a template comment, a pointer, a per-role contract: run Lens B's token grep against **what you just wrote**, and every hit must state the new version, state the other branch correctly, or be unrelated. Re-run classes 13 and 14 against the text you wrote — a fix routinely adds a slot or a rule, and those two catch a slot with no defined vocabulary and a rule colliding under precedence. The grep's blind spot — two untouched files — goes in `### 沒審到`.

   **Last, re-read the line numbers for every finding left in `### 要你回答`** — the fixes moved everything below them; resolve each from the file as it stands and cite the section name alongside.

---

## Guardrails

- **Read the FULL file, not just the diff** — context determines whether a change is safe, and logic defects live in step interactions, including with unchanged steps.
- **Trace, don't skim** — a lens finding is only real when you can name the input/interruption and the wrong outcome it produces.
- **Be strict on text, conservative on logic** — flag anything even slightly questionable as RISKY in the text pass; but a spec/workflow intentionally leaves room for agent judgment, so do not flag underspecification as a logic defect unless a concrete execution goes wrong.
- **Save tokens by method, never by coverage** — one read per file for both layers, Lens B grep-first, findings instead of narration; never a dropped criterion or lens. When the set does not fit, batch it (step 1, identify the targets) — `### 沒審到` reports what the method cannot see, never what the run did not get to.
- **Keep each layer in its own file** — detection-only criteria in `text-criteria.md`, lenses in `logic-lenses.md`, and the rules shared with the write-time side in the plugin's `authoring-rules.md`. Never restate one inside another, never inline any of them back into this file, and when a finding is really a missing *rule*, add it to the shared catalogue rather than here — that is what keeps writing and auditing from drifting apart.
- **Never approve removal of** a rule with a recorded failure or a project convention behind it, a coverage or severity distinction a report carries, a security constraint, or a phase another step depends on — the catalogue's *Delete a rule only for a named reason* is the test. Emphasis around a rule that survives is none of these.
- **Compression is not always good** — shorter prompts that lose clarity are worse than longer prompts that work correctly
- **Bloat is also a risk** — verbose explanations, tutorials, scripts for the model's reasoning or route, and emphasis with no recorded failure behind it; never a concise rule carrying a fact, a contract, or a recorded failure
- **A rule with a recorded failure is battle-tested; one without is a claim.** The catalogue's *A rule earns its line* says what a rule is for and *Delete a rule only for a named reason* names the three reasons a deletion may carry; criterion k applies both. Neither "the model should know this" nor "the model might skip this" settles anything on its own — the record does.
- **No tooling / environment assumptions** — rules must not assume a linter, formatter, test runner, or CI is present; and a procedure that assumes git, a single repo, or a linter is itself a finding (Lens A class 5) when the skill is meant to run where those may be absent.
- **Claude-first; defer cross-harness to a compile step** — never rate a Claude-specific construct as a portability liability. The full do-not-flag list and the three genuine Claude-correctness bugs are criterion (s); do not restate them here.
- **Prefer generic over hardcoded** — prompts should work across projects. Hardcoded values (URLs, names, paths, versions) need justification; if a value could vary, parameterize or conditionalize it
- **Steering must change behavior, and sharpening beats deleting** — a weak rule with a recorded failure or a convention behind it is fixed by strengthening it, never by cutting it; one with neither is criterion k's call. The precedence that settles the conflicts lives with the criteria: (h) over (v) on force, (w) rated under (k) on the burden of proof, and (w)'s residual and (x) stay **NOTE** because they rest on what the file cannot show you — except the frontmatter `description` that (x) carves out, whose budget is stated, making it **RISKY** and fixed in the pass.
- **Zero errors is the absolute principle** — when in doubt on the text layer, rate as RISKY and fix it
- **Fix it, don't hand over a menu** — RISKY/BROKEN text findings are fixed and re-audited until clean; a logic or consolidation fix that picks between two valid designs is **yours to decide** — apply what you would recommend and list it in `### 我做的抉擇`. Escalate only what the user alone can answer (step 7, fix and sweep); the report keeps them in the loop after the work. `--report-only` surfaces everything and touches nothing.
