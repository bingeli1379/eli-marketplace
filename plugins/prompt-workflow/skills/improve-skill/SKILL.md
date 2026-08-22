---
name: improve-skill
description: Use when ANY asset shipped by a plugin you maintain in a LOCAL marketplace/plugin repo — a skill, an output style or persona, an agent, a hook, a template — misbehaved, missed a case, or felt clunky while you used it during real work in ANOTHER project, and you want to feed that back into its source instead of working around it again. Triggers on improve, refine, patch, or fix a skill you just used, feed a problem back into a skill, or /improve-skill.
---

# Improve Skills from Real Usage

Feed real-usage problems back into your own skills. You were working in **another project** and used a skill you maintain — shipped by a plugin from one of your local marketplace/plugin repos — as a tool; it did something wrong, missed a case, or was clunky. You already handled it and finished your task — this skill turns that experience into a concrete fix to the skill's **source** in whichever local repo owns it.

**How it differs from `/review-skill`:** that one statically audits skill *files* when you are deliberately editing a skill. This one is **usage-driven and cross-repo** — the signal is what happened when you *used* the skill in a different project, and the target source lives in a *different* repo than your current working directory. It composes that audit to validate its own edits.

**Scope — this skill does exactly ONE thing: patch the target's source in the local working copy of whichever repo owns it.** It does NOT commit, push, or reinstall the plugin. Those are your follow-up steps.

## The loop this fits into

1. In another project, you use a skill and hit a problem.
2. You handle it manually and finish your task — do NOT block on the skill defect.
3. **← You run `/improve-skill <skill>` here.** It patches the skill's source in the owning repo's local working copy.
4. You commit yourself.
5. You `git push` yourself.
6. You reinstall / update the plugin yourself so the fix takes effect.

Steps 4–6 are deliberately yours; this skill stops after step 3.

---

**Input**: Name the target(s) via `$ARGUMENTS` (a `plugin:skill` reference, a bare skill name, a `<plugin>:<style>` output-style id, a persona / voice name, or a plugin name) and/or describe the problem. There is no confirm gate: the run decides, edits, and reports what it decided (step 4, rank the changeset).

**Steps**

0. **Preflight — identify the target and resolve ITS local source working copy (do this FIRST)**

   You are almost certainly running from a *different* project, and different skills may live in *different* local repos, so the target source is NOT under the current working directory. Resolve it in two parts, in order:

   **0a. Which target → which plugin/marketplace.**
   - Take the target from `$ARGUMENTS`. If only a problem is described, infer the target from this session's usage.
   - Determine the owning plugin + marketplace. A skill lives at `plugins/<plugin>/skills/<name>/`. Find it in the installed layout — grep the install paths in `~/.claude/plugins/installed_plugins.json` (whose keys are `<plugin>@<marketplace>`), or the cache under `~/.claude/plugins/cache/<marketplace>/<plugin>/…`, for `skills/<name>/SKILL.md`. A `plugin:skill` reference already tells you the plugin. Agents (`agents/*.md`) and references (`references/*.md`) belong to the same plugin.
   - **The target need not be a skill.** Anything a plugin ships is fair game when that is what misbehaved: an **output style** (`output-styles/*.md` — named by its `<plugin>:<style>` id, and the thing to grep for when the user names a persona or voice rather than a skill), a hook (`hooks/`), an agent, a template, or `config/`. Resolve the owning plugin the same way — grep the installed cache for the file — then treat that file as the target everywhere below.

   **0b. Resolve the marketplace's LOCAL source working copy** — the git repo you version-control and push, **NOT** the installed cache under `~/.claude/plugins/cache/…` and **NOT** the Claude-managed marketplace clone under `~/.claude/plugins/marketplaces/…` (both are ephemeral and auto-overwritten on update). In priority order:
   1. If `$ARGUMENTS` gives an absolute repo path, prefer it.
   2. A recorded pointer in the user's `~/.claude/CLAUDE.md` — it lists local repo paths for the marketplaces/plugin repos they maintain. Match by which repo owns the skill (the pointer may describe the repo by the slash-commands / skills it hosts rather than by the marketplace's *registered* name — the registered name can differ from the working-copy directory name), not by a strict marketplace-name string match. Any pointer whose path passes the 0b④ file check is a valid hit.
   3. Otherwise derive the marketplace's remote URL from `~/.claude/plugins/known_marketplaces.json`, then look for a local git working copy whose `origin` remote matches, within the user's known project roots — **name in one line which root(s) you will check; do not blind-scan the whole disk.**
   4. **Confirm the candidate really is the source**: `git -C <candidate> rev-parse --is-inside-work-tree` succeeds AND the target file exists under it — `<candidate>/plugins/<plugin>/skills/<name>/SKILL.md` for a skill, or the corresponding `output-styles/` / `agents/` / `hooks/` / `templates/` path for a non-skill target. The file-exists check is authoritative — remote URLs drift (a repo gets renamed or mirrored), the on-disk skill file does not.
   5. **If no local source is found, STOP and ask (AskUserQuestion):** how to proceed — supply the absolute path, or skip that target. Suggest recording the resolved path in `~/.claude/CLAUDE.md` so future runs skip discovery. Never fall back to editing the cache or the marketplace clone.

   Everything below targets the confirmed repo (call it `<repo>`) via absolute paths or `git -C <repo>`.

   **`<repo>` is per target, not per run.** When you maintain more than one marketplace/plugin repo, a single run's targets routinely resolve to *different* ones (e.g. a public marketplace and a private plugin repo) — so never assume one run means one repo, even if the first target you resolved happens to be the only one. Resolve `0a`–`0b` for each target independently, then carry every step below **per repo**: its own conventions (`0c`), its own edits, its own validation, its own handoff line. Never let a path, a convention, or a validation script from one repo apply to another, and never collapse the run onto whichever repo you resolved first. Where a step says `<repo>` below, read it as "that target's repo".

   **0c. Load the maintenance conventions of EVERY `<repo>` you are about to edit, before editing anything in it.** A repo you maintain may keep its authoring rules *outside* the files being edited — precisely so the edited files stay free of authoring meta. Those rules are not optional context; they are the house style for the edit you are about to make, and the target file will not restate them. So:
   - Read `<repo>/CLAUDE.md` (and `<repo>/plugins/<plugin>/CLAUDE.md` if present) — repo structure, sync obligations, version-bump rules, language conventions.
   - List `<repo>/.claude/skills/` and read the `SKILL.md` of any whose frontmatter `description` covers the file you are about to change (a maintenance skill for that plugin's persona, data, or prompt files). Follow it for the edit.
   - **Read them as files, do not try to invoke them.** They are project-level skills of a *foreign* repo, so they are not registered in this session — `/<name>` will not resolve. Load the file with Read and comply with its content.
   - If such a skill covers the target and contradicts your instinct for the edit, **it wins**.

1. **Capture the usage problem(s)**

   Gather concrete evidence of what went wrong when the target was *used* — primarily from THIS session (the output you had to correct, a case it didn't handle, a manual workaround you did, a rerun/retry), plus anything the user describes for a problem from an earlier session. For each, record: which target (skill / output style / hook / agent — per 0a), the exact symptom / moment, and what the correct behavior would have been. If there is no concrete evidence, there is nothing to refine — say so and stop (do not invent improvements).

2. **Classify each problem**

   - **Target deficiency** — the target's own instructions led to the bad result → fixable here. This covers every asset type 0a admits: a skill's steps, an **output style's / persona's** wording, a hook's behavior, an agent's prompt. A persona that talked wrong is a target deficiency, not a preference.
   - **Durable personal preference** — not a defect, just how you like things done → belongs in memory or a `CLAUDE.md`, NOT an edit to the target. Note it and route it there. **Test it before routing it here**: does it describe how *you* like to work, or how *the skill* should behave for every future run? The second is a target deficiency, not a preference — see the guardrail below.
   - **One-off / user error / environment quirk** — skip.

   Keep only target deficiencies backed by concrete evidence.

3. **Locate the source + ownership guardrails**

   Map each target to its file in `<repo>`: `<repo>/plugins/<plugin>/skills/<name>/SKILL.md` (or `agents/*.md`, `references/*.md`, `output-styles/*.md`, `hooks/*`, `templates/*`, `config/*`). Then:
   - Edit the **working copy** at `<repo>`, never the installed cache or the marketplace clone.
   - **Apply whatever `0c` turned up.** A maintenance skill's authoring rules govern this edit — where a new rule belongs, whether to merge into an existing one instead of appending, what must not change, which mirror files have to move together. Do not fall back to your own instinct because the target file itself says nothing.
   - **Only edit skills the repo authors itself.** If the owning repo tracks upstream-synced skills (e.g. a `SOURCES.yaml` that marks a skill `repo: <url>`), do NOT rewrite its body — a sync would clobber it. Its frontmatter `description` IS safe to edit (sync preserves local frontmatter) if the fix is a trigger-wording tweak. Prefer changing what the repo owns (an agent, a workflow-core skill, an original skill).
   - Keep each edit **within its own plugin** — never add a reference that crosses plugin / marketplace boundaries.

4. **Rank the changeset, then act on it**

   Rank the changeset; each item:
   `<repo> · <repo-relative file> · what went wrong in usage (the evidence) · the edit · why it fixes it`

   **Then apply it — the same policy `/review-skill` follows, for the same reason** (its step 7, fix and sweep): a directly-fixable item you just fix, and a judgement call is *yours* — apply what you would recommend and record the call, rather than handing back a menu at the moment the user has least context. Stop only for what they alone can answer. **A constraint you proposed earlier in this conversation is not their requirement**; if the fix needs it dropped, drop it and report that as one of the calls.

   Show the ranked list as part of step 7's report, alongside the calls you made — not as a gate before step 5.

5. **Apply to the working copy**

   **Before writing any prose edit, read `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md`.** It is the same catalogue step 6's audit measures the edit against, so reaching it only there means fixing your own edit instead of writing it right — and the rules that bite hardest are the ones invisible from the file you are editing (which frontmatter flag a behavior change actually needs, what a description may hold). Where `0c`'s repo conventions conflict with it, they win.

   Make the edits at `<repo>`. For any item classified as a preference in step 2, write the memory / suggest the `CLAUDE.md` line instead of editing the target.

6. **Validate the edits — compose the existing audits, do not re-implement them**

   Validate the changed files at `<repo>`, **one invocation per repo** — never a single audit call mixing paths from two repos, since each audit reads the cwd's git state and each repo has its own conventions and its own verdict. **Caveat: `/review-skill` assumes the current working directory IS the repo under audit and uses its `git diff` to find "what changed" — but you are in another project, so its auto-detect points at the wrong repo (and `git diff HEAD -- <foreign-path>` may error).** Since you just made the edits and know exactly what changed, drive it explicitly:
   - `/review-skill` — pass the changed `SKILL.md` / agent `.md` files as explicit path arguments, and tell it what you changed rather than relying on its `git diff` auto-detect; if it needs a diff, have it use `git -C <repo>`. Pass `--report-only`: it applies fixes by default, but this run needs them to land in **one** changeset — yours — because only this skill sees every repo the run touched and owns the step 7 report. So it surfaces, you apply. That handoff is the whole point of the flag — findings it reports are your work items, not the user's, so carry every one back into step 5 and fix it. Its `### 我做的抉擇` entries are calls it made on your behalf; fold them into your own step 7 report.
   - If `<repo>` has a structure/lint validation script (e.g. `scripts/check-structure.sh`), run it directly — such scripts derive their own repo root from the script's location, so the current working directory does not matter. Skip if absent. **Run each touched repo's own script**, and only over that repo: one repo's validator knows nothing about another's layout, so a pass there says nothing about the edits here.
   - Also run `claude plugin validate <plugin-root>` for every plugin you edited — it catches what a repo script's line-based frontmatter reads cannot: a frontmatter block that is not valid YAML, which loads the skill with empty metadata instead of failing loudly. Same check `/review-skill` step 1's deterministic backstop runs; run it here too, because a `--report-only` audit surfaces findings but you are the one applying them.

   **Route by what the target actually is** — the two audits above audit *prompt prose*:
   - **Prose targets** — anything a model is steered by, whatever directory it sits in: `SKILL.md`, `agents/*.md`, `output-styles/*.md`, `references/*.md`, `templates/*.md`, a bundled `config/*.md` where the plugin keeps its authoritative prose there, and a plugin-level `CLAUDE.md`. Pass them to `/review-skill` as explicit paths, as above. An output style is prose and gets the same audit as a skill.
   - **Non-prose targets** (`hooks/*` scripts, machine-readable `config/*.json` / `*.yaml`, generated data) → do NOT feed them to the prompt audits; that produces noise, not findings. Validate them by their own nature instead: the repo's structure/lint script, a syntax check for the language (e.g. `bash -n` for a shell hook, a JSON/YAML parse for data), and the conventions `0c` turned up. State in the step-7 report which validation you ran and which you skipped, with the reason.

   Fix anything the applicable checks flag until they pass.

7. **Hand off (do NOT commit, push, or reinstall)**

   Report **the ranked changeset from step 4** (each item with the usage evidence behind it), **the calls you made** — every judgement call you resolved rather than asked about, what you picked and what you rejected — and the `<repo>` path(s). Then state the remaining steps are the user's. **Group the handoff by repo — one block per touched repo, each listing its own files and its own three steps.** Separate repos mean separate git histories and separate plugin installs; a merged handoff loses which commit belongs where:
   - commit from that repo (or `git -C <repo> …`), plus a version bump and changelog entry if the target's behavior changed — never one commit spanning two repos, that is not even possible;
   - `git push` in that repo;
   - reinstall / update that repo's plugin so the fix goes live — reinstalling one marketplace does nothing for the other's edits.
   Flag explicitly: **the fix is NOT active in the current environment until that reinstall** — the running copy (skill, output style, hook) still comes from the old installed cache.

## Guardrails

- **Evidence over speculation** — every edit must trace to something that actually happened when the target was used this session (or a problem the user concretely describes). Generic "this could read better" improvements are `/review-skill`'s job, not this.
- **One run can span several repos** — treat multi-repo as the normal case, not an edge case: resolve, edit, validate, and hand off per repo (step 0b, "`<repo>` is per target, not per run"). Anything reported or run against the wrong `<repo>` is a wrong answer, not a near miss.
- **Working copy, never the cache or the marketplace clone** — edits under `~/.claude/plugins/cache/…` or `~/.claude/plugins/marketplaces/…` are auto-overwritten on update and never version-controlled. Always target the resolved git working copy `<repo>`.
- **Confirm the source by the file, not the URL** — a local repo is the right source only when the target's file actually exists in it; remote URLs can drift. When no local source is found, ask — do not guess or fall back to a cache path.
- **Never commit, push, or reinstall** — this skill stops at editing the working copy; the user does the rest (they asked for it that way).
- **Respect ownership** — do not rewrite upstream-synced skill bodies; do not add cross-plugin / cross-marketplace references. Mirror the owning repo's own conventions.
- **The owning repo's maintenance skills outrank your instinct** — when `<repo>/.claude/skills/` holds one covering the target, it is the house style for the edit (step 0c). A target file that carries no authoring meta is usually a deliberate choice, not an omission: do not "restore" a pointer, a sync note, or a rule reminder into it, and do not infer the conventions from the file's contents when a skill states them.
- **Preferences are not skill fixes** — route durable preferences to memory / `CLAUDE.md`, not into skill edits. **But how the user wants a skill of theirs to behave IS a skill fix**: "I want the review to just fix things" changes that skill's contract for every future run, so it belongs in the skill body — routing it to `CLAUDE.md` buries a behavior change in personal config.
- **Report language: Traditional Chinese** (technical terms, file names, and labels stay English).
