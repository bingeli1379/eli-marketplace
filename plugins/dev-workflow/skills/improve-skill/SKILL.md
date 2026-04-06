---
name: improve-skill
description: Use when a skill from this marketplace (/sdd, /commit, /release, /review, /issue-tracing, etc.) misbehaved, missed a case, or felt clunky while you were using it as a tool during real work in ANOTHER project, and you want to feed that back into the skill's source. It reads what went wrong in the current session and patches the skill's files in your local marketplace repo (the git working copy), then validates. Report-and-confirm before applying. You commit, push, and reinstall the plugin yourself afterward. Use when the user asks to improve, refine, patch, or fix a skill they just used, or run /improve-skill.
---

# Improve Skills from Real Usage

Feed real-usage problems back into your own skills. You were working in **another project** and used a marketplace skill (`/sdd`, `/commit`, `/review`, `/issue-tracing`, …) as a tool; it did something wrong, missed a case, or was clunky. You already handled it and finished your task — this skill turns that experience into a concrete fix to the skill's **source** in your local marketplace repo.

**How it differs from `/review-prompt` and `/review-workflow`:** those statically audit skill *files* when you are deliberately editing a skill. This one is **usage-driven and cross-repo** — the signal is what happened when you *used* the skill in a different project, and the target source lives in a *different* repo than your current working directory. It composes those audits to validate its own edits.

**Scope — this skill does exactly ONE thing: patch the skill source in your local marketplace repo working copy.** It does NOT commit, push, or reinstall the plugin. Those are your follow-up steps.

## The loop this fits into

1. In another project, you use a marketplace skill and hit a problem.
2. You handle it manually and finish your task — do NOT block on the skill defect.
3. **← You run `/improve-skill` here.** It patches the skill's source in your local marketplace repo.
4. You run `/commit` (etc.) yourself.
5. You `git push` yourself.
6. You reinstall / update the plugin yourself so the fix takes effect.

Steps 4–6 are deliberately yours; this skill stops after step 3.

---

**Input**: Optionally name the skill(s) or describe the problem via `$ARGUMENTS`. Pass `--apply` to skip the confirm gate in step 4.

**Steps**

0. **Preflight — resolve the marketplace repo path (do this FIRST)**

   You are almost certainly running from a *different* project, so the skill sources are NOT under the current working directory. Resolve the **local marketplace repo working-copy path** — the git-tracked source you version-control, **NOT** the installed cache under `~/.claude/plugins/cache/…` (that is ephemeral and overwritten on reinstall):
   - Read it from the user's global `~/.claude/CLAUDE.md` — there is a recorded "marketplace repo" path pointer there.
   - If `$ARGUMENTS` gives a path, prefer that.
   - If neither is available, ask the user once (AskUserQuestion) for the absolute path, and suggest recording it in `~/.claude/CLAUDE.md` so future runs skip this.
   - Verify it exists and is a git repo (`git -C <path> rev-parse --is-inside-work-tree`). Every edit and check below targets this `<repo>` path via absolute paths or `git -C <repo>`.

1. **Capture the usage problem(s)**

   Gather concrete evidence of what went wrong when the skill was *used* — primarily from THIS session (the output you had to correct, a case it didn't handle, a manual workaround you did, a rerun/retry), plus anything the user describes for a problem from an earlier session. For each, record: which skill, the exact symptom / moment, and what the correct behavior would have been. If there is no concrete evidence, there is nothing to refine — say so and stop (do not invent improvements).

2. **Classify each problem**

   - **Skill deficiency** — the skill's instructions led to the bad result → fixable here.
   - **Durable personal preference** — not a defect, just how you like things done → belongs in memory or a `CLAUDE.md`, NOT a skill edit. Note it and route it there.
   - **One-off / user error / environment quirk** — skip.

   Keep only skill deficiencies backed by concrete evidence.

3. **Locate the source + ownership guardrails**

   Map each skill to its file in the working copy: `<repo>/plugins/<plugin>/skills/<name>/SKILL.md` (or `agents/*.md`, `references/*.md`). Then:
   - Edit the **working copy** at `<repo>`, never the installed cache.
   - **Only edit skills the repo authors itself.** If the repo tracks upstream-synced skills (e.g. `plugins/sdd/skills/SOURCES.yaml` marks a skill `repo: <url>`), do NOT rewrite its body — a sync would clobber it. Its frontmatter `description` IS safe to edit (sync preserves local frontmatter) if the fix is a trigger-wording tweak. Prefer changing what the repo owns (an agent, a workflow-core skill, an original skill).
   - Keep each edit **within its own plugin** — never add a reference that crosses plugin / marketplace boundaries.

4. **Propose the changeset — the review gate ("檢視")**

   Present a ranked list; each item:
   `<repo-relative file> · what went wrong in usage (the evidence) · proposed edit · why it fixes it`
   This is where the user reviews before anything changes. Wait for confirmation. (Skip the wait only if `--apply` was passed.)

5. **Apply to the working copy** (after confirmation)

   Make the edits at `<repo>`. For any item classified as a preference in step 2, write the memory / suggest the `CLAUDE.md` line instead of editing a skill.

6. **Validate the edits — compose the existing audits, do not re-implement them**

   Validate the changed files at `<repo>`. **Caveat: `/review-prompt` and `/review-workflow` assume the current working directory IS the repo under audit and use its `git diff` to find "what changed" — but you are in another project, so their auto-detect points at the wrong repo (and `git diff HEAD -- <foreign-path>` may error).** Since you just made the edits and know exactly what changed, drive them explicitly:
   - `/review-prompt` — pass the changed `SKILL.md` / agent `.md` files as explicit path arguments, and tell it what you changed rather than relying on its `git diff` auto-detect; if it needs a diff, have it use `git -C <repo>`. (Prompt-text quality + intra-file contradiction.)
   - `/review-workflow` — same handling, if a changed skill's procedure/logic (Lens A) or cross-file duplication / SSOT (Lens B) was affected.
   - `<repo>/scripts/check-structure.sh` — run it directly if present; it derives its own repo root from the script's location, so the current working directory does not matter. Skip if absent.
   Fix anything they flag until they pass.

7. **Hand off (do NOT commit, push, or reinstall)**

   Report the applied changeset and the `<repo>` path, then state the remaining steps are the user's:
   - commit (run `/commit` from that repo, or `git -C <repo> …`), and `/release` if a skill's behavior changed;
   - `git push`;
   - reinstall / update the plugin so the fix goes live.
   Flag explicitly: **the fix is NOT active in the current environment until that reinstall** — the running skill still comes from the old installed cache.

## Guardrails

- **Evidence over speculation** — every edit must trace to something that actually happened when the skill was used this session (or a problem the user concretely describes). Generic "this could read better" improvements are `/review-prompt`'s job, not this.
- **Working copy, never the cache** — edits under `~/.claude/plugins/cache/…` are overwritten on reinstall and never version-controlled. Always target the resolved git working copy.
- **Never commit, push, or reinstall** — this skill stops at editing the working copy; the user does the rest (they asked for it that way).
- **Respect ownership** — do not rewrite upstream-synced skill bodies; do not add cross-plugin / cross-marketplace references. Mirror the repo's own conventions.
- **Preferences are not skill fixes** — route durable preferences to memory / `CLAUDE.md`, not into skill edits.
- **Report language: Traditional Chinese** (technical terms, file names, and labels stay English).
