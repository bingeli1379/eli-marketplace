---
name: improve-skill
description: Use when ANY asset shipped by a plugin you maintain in a LOCAL marketplace/plugin repo — a skill, an output style or persona, an agent, a hook, a template — misbehaved, missed a case, or felt clunky while you used it during real work in ANOTHER project, and you want to feed that back into its source instead of working around it again. Triggers on improve, refine, patch, or fix a skill you just used, feed a problem back into a skill, or /improve-skill.
---

# Improve Skills from Real Usage

Feed real-usage problems back into your own skills: you used a skill you maintain in **another project**, it did something wrong, you handled it and finished — this skill turns that into a fix to the skill's **source** in whichever local repo owns it.

**How it differs from `/review-skill`:** that one statically audits skill *files*; this one is **usage-driven and cross-repo** — the signal is what happened in use, and the source lives in a *different* repo than the cwd. It composes that audit to validate its own edits.

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

   The target source is NOT under the current working directory, and different targets may live in different local repos. Resolve in two parts, in order:

   **0a. Which target → which plugin/marketplace.**
   - Take the target from `$ARGUMENTS`. If only a problem is described, infer the target from this session's usage.
   - Determine the owning plugin + marketplace. A skill lives at `plugins/<plugin>/skills/<name>/`. Find it in the installed layout — grep the install paths in `~/.claude/plugins/installed_plugins.json` (whose keys are `<plugin>@<marketplace>`), or the cache under `~/.claude/plugins/cache/<marketplace>/<plugin>/…`, for `skills/<name>/SKILL.md`. A `plugin:skill` reference already tells you the plugin. Agents (`agents/*.md`) and references (`references/*.md`) belong to the same plugin.
   - **The target need not be a skill.** Anything a plugin ships is fair game when that is what misbehaved: an **output style** (`output-styles/*.md` — named by its `<plugin>:<style>` id, and the thing to grep for when the user names a persona or voice rather than a skill), a hook (`hooks/`), an agent, a template, or `config/`. Resolve the owning plugin the same way — grep the installed cache for the file — then treat that file as the target everywhere below.

   **0b. Resolve the marketplace's LOCAL source working copy** — the git repo you version-control and push, **never** the installed cache under `~/.claude/plugins/cache/…` or the Claude-managed clone under `~/.claude/plugins/marketplaces/…` (both auto-overwritten on update). Candidates, most direct first: an absolute repo path in `$ARGUMENTS`; a pointer in the user's `~/.claude/CLAUDE.md` — match by which repo owns the skill, since the pointer may describe the repo by the skills it hosts and the marketplace's *registered* name can differ from the directory name; a working copy whose `origin` matches the remote URL in `~/.claude/plugins/known_marketplaces.json`, searched under the user's known project roots — **name in one line which root(s) you will check; never blind-scan the disk**. **A candidate is the source when** `git -C <candidate> rev-parse --is-inside-work-tree` succeeds AND the target file exists under it (`<candidate>/plugins/<plugin>/skills/<name>/SKILL.md`, or the `output-styles/` / `agents/` / `hooks/` / `templates/` path for a non-skill target); the file check is authoritative — remote URLs drift, the on-disk file does not. **None found → STOP and ask (AskUserQuestion)**: supply the absolute path, or skip that target; suggest recording the path in `~/.claude/CLAUDE.md`.

   Everything below targets the confirmed repo (call it `<repo>`) via absolute paths or `git -C <repo>`.

   **`<repo>` is per target, not per run.** One run's targets routinely resolve to different repos (a public marketplace and a private plugin repo), so resolve `0a` and `0b` for each target independently and carry every step below **per repo** — its conventions from `0c`, its edits, its validation, its handoff line — never a path, convention, or script from one repo applied to another.

   **0c. Load the maintenance conventions of EVERY `<repo>` you are about to edit, before editing anything in it.** A repo may keep its authoring rules *outside* the edited files so those stay free of authoring meta; the target file will not restate them.
   - Read `<repo>/CLAUDE.md` (and `<repo>/plugins/<plugin>/CLAUDE.md` if present) — repo structure, sync obligations, version-bump rules, language conventions.
   - Find that repo's maintenance skills and read the `SKILL.md` of any whose frontmatter `description` covers the file you are about to change (a maintenance skill for that plugin's persona, data, or prompt files). Follow it for the edit. **Look in both the live and the tracked location** — `<repo>/.claude/skills/`, and any committed `skills/` directory that is NOT the plugin's own shipped `plugins/<plugin>/skills/` (a maintainer kit parked under the plugin it serves). The live directory is routinely git-ignored and holds symlinks into that committed source, so an absent or empty `.claude/skills/` is not evidence the repo states no conventions.
   - **Read them as files, do not try to invoke them.** They are project-level skills of a *foreign* repo, so they are not registered in this session — `/<name>` will not resolve. Load the file with Read and comply with its content.
   - If such a skill covers the target and contradicts your instinct for the edit, **it wins**.

1. **Capture the usage problem(s)**

   Gather concrete evidence of what went wrong in use — from THIS session (the output you had to correct, a case it didn't handle, a workaround, a retry) plus anything the user describes from an earlier one. Per problem: which target (per 0a), the exact symptom, and the correct behavior. No concrete evidence → nothing to refine; say so and stop.

2. **Classify each problem**

   - **Target deficiency** — the target's own instructions led to the bad result → fixable here, for every asset type 0a admits (a persona that talked wrong is this, not a preference).
   - **Durable personal preference** — how *you* like to work → memory or a `CLAUDE.md`, not an edit to the target. **Test it before routing it here**: how *the skill* should behave for every future run is a target deficiency.
   - **One-off / user error / environment quirk** — skip.

   Keep only target deficiencies backed by concrete evidence.

3. **Locate the source + ownership guardrails**

   Map each target to its file in `<repo>`: `<repo>/plugins/<plugin>/skills/<name>/SKILL.md` (or `agents/*.md`, `references/*.md`, `output-styles/*.md`, `hooks/*`, `templates/*`, `config/*`). Then:
   - Edit the **working copy** at `<repo>`, never the installed cache or the marketplace clone.
   - **Apply whatever `0c`, load the maintenance conventions, turned up.** A maintenance skill's authoring rules govern this edit — where a new rule belongs, whether to merge into an existing one instead of appending, what must not change, which mirror files have to move together. Do not fall back to your own instinct because the target file itself says nothing.
   - **Only edit skills the repo authors itself.** If the owning repo tracks upstream-synced skills (e.g. a `SOURCES.yaml` that marks a skill `repo: <url>`), do NOT rewrite its body — a sync would clobber it. Its frontmatter `description` IS safe to edit (sync preserves local frontmatter) if the fix is a trigger-wording tweak. Prefer changing what the repo owns (an agent, a workflow-core skill, an original skill).
   - **Never add a hard cross-plugin / cross-marketplace dependency** — a path into another plugin, or a step that cannot finish when it is absent. A named Skill-tool load guarded by an absence plan is not that, and is allowed; the owning repo's own convention file settles which it wants.

4. **Rank the changeset, then act on it**

   Rank the changeset; each item:
   `<repo> · <repo-relative file> · what went wrong in usage (the evidence) · the edit · why it fixes it`

   **Then apply it — the same policy `/review-skill` follows** (its step 7, fix and sweep): a directly-fixable item you fix, a judgement call is *yours* — apply what you would recommend and record the call. Stop only for what the user alone can answer. **A constraint you proposed earlier in this conversation is not their requirement**; if the fix needs it dropped, drop it and report that as one of the calls.

   Show the ranked list as part of step 7's report, alongside the calls you made — not as a gate before step 5.

5. **Apply to the working copy**

   **Before writing any prose edit, read `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md`** — the same catalogue step 6's audit measures the edit against, and the rules that bite hardest are invisible from the file being edited (which frontmatter flag a behavior change needs, what a description may hold). Where the conventions loaded in `0c` conflict with it, they win.

   Make the edits at `<repo>`. For any item classified as a preference in step 2, write the memory / suggest the `CLAUDE.md` line instead of editing the target.

6. **Validate the edits — compose the existing audits, do not re-implement them**

   Validate the changed files at `<repo>`, **one invocation per repo** — each audit reads the cwd's git state and each repo has its own conventions and verdict. **Caveat: `/review-skill` assumes the cwd IS the repo under audit and uses its `git diff` to find what changed; from another project its auto-detect points at the wrong repo and `git diff HEAD -- <foreign-path>` may error.** Drive it explicitly:
   - `/review-skill` — pass the changed files as explicit paths and tell it what you changed; if it needs a diff, have it use `git -C <repo>`. Pass `--report-only`: its fixes have to land in **one** changeset — yours — since only this skill sees every repo the run touched and owns the step 7 report. Its findings are your work items: carry every one back into step 5 and fix it; fold its `### 我做的抉擇` entries into your own report.
   - The repo's structure/lint script (e.g. `scripts/check-structure.sh`), run directly — it derives its repo root from its own location, so the cwd does not matter. **Each touched repo's own script, over that repo only.** Skip if absent.
   - `claude plugin validate <plugin-root>` for every plugin you edited — it catches a frontmatter block that is not valid YAML, which a line-based script passes and which loads the skill with empty metadata. Run it here because a `--report-only` audit surfaces findings and you are the one applying them.

   **Route by what the target actually is** — the two audits above audit *prompt prose*:
   - **Prose targets** — anything a model is steered by, whatever directory it sits in: `SKILL.md`, `agents/*.md`, `output-styles/*.md`, `references/*.md`, `templates/*.md`, a bundled `config/*.md`, a plugin-level `CLAUDE.md` → `/review-skill` as explicit paths.
   - **Non-prose targets** (`hooks/*` scripts, machine-readable `config/*.json` / `*.yaml`, generated data) → never the prompt audits; validate by their own nature — the repo's structure/lint script, a syntax check (`bash -n` for a shell hook, a JSON/YAML parse for data), and the conventions from `0c`. State in the step-7 report which validation ran and which was skipped, with the reason.

   Fix anything the applicable checks flag until they pass.

7. **Hand off (do NOT commit, push, or reinstall)**

   Report **the ranked changeset from step 4** (each item with its usage evidence), **the calls you made** (what you picked, what you rejected), and the `<repo>` path(s). **Group the handoff by repo — one block per touched repo, its own files and its own three steps**, since each repo has its own git history and plugin install:
   - commit from that repo (or `git -C <repo> …`), plus a version bump and changelog entry if the target's behavior changed;
   - `git push` in that repo;
   - reinstall / update that repo's plugin so the fix goes live.
   Flag explicitly: **the fix is NOT active in the current environment until that reinstall** — the running copy still comes from the old installed cache.

## Guardrails

- **Evidence over speculation** — every edit must trace to something that actually happened when the target was used this session (or a problem the user concretely describes). Generic "this could read better" improvements are `/review-skill`'s job, not this.
- **One run can span several repos** — resolve, edit, validate, and hand off per repo (step 0b, "`<repo>` is per target, not per run").
- **Working copy, never the cache or the marketplace clone** — edits under `~/.claude/plugins/cache/…` or `~/.claude/plugins/marketplaces/…` are auto-overwritten on update and never version-controlled. Always target the resolved git working copy `<repo>`.
- **Confirm the source by the file, not the URL** — a local repo is the right source only when the target's file actually exists in it; remote URLs can drift. When no local source is found, ask — do not guess or fall back to a cache path.
- **Never commit, push, or reinstall** — this skill stops at editing the working copy; the user does the rest (they asked for it that way).
- **Respect ownership** — do not rewrite upstream-synced skill bodies; do not add a **hard** cross-plugin / cross-marketplace dependency (a lazy named load with an absence plan is fine); mirror the owning repo's own conventions.
- **The owning repo's maintenance skills outrank your instinct** (step `0c`, load the maintenance conventions). A target file carrying no authoring meta is a deliberate choice: do not "restore" a pointer, a sync note, or a rule reminder into it.
- **Preferences are not skill fixes** — durable preferences go to memory / `CLAUDE.md`. **But how the user wants a skill of theirs to behave IS a skill fix** ("I want the review to just fix things" changes that skill's contract for every future run) and belongs in the skill body.
- **Report language: Traditional Chinese** (technical terms, file names, and labels stay English).
