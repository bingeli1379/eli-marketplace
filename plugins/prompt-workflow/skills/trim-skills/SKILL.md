---
name: trim-skills
description: "Use when the model under your skills got stronger and you want to find what your own prompt files no longer need, or now have wrong — one skill, one plugin, or every skill a local marketplace/plugin repo authors. Triggers on model upgrade, new model, stronger model, prune or trim my skills, slim down prompts, what can I remove, 模型升級了、換新模型了、幫我看 skill 有沒有要拿掉的、skill 瘦身、掃全部 skill 看要不要改、這個 skill 還需要這些嗎. NOT a text audit of one change (/review-skill), NOT a fix for a problem hit in use (/improve-skill), NOT whether a skill ever fires (/usage-audit), NOT shortening one rule or description you already picked."
argument-hint: "[skill | plugin | path | all] [--report-only]"
---

# Trim skills after a model upgrade

Find what a stronger model no longer needs in prompt files you author, remove it once you approve, then prove the removal broke nothing.

**The deletion bar is the catalogue, not this file.** Read `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md` → *A rule earns its line*, *Delete a rule only for a named reason*, *One canonical home per rule* and *Cost* before step 3, the slice audit. Every candidate names which of those entries' deletion reasons it meets, and nothing they protect is a candidate.

**Two halves with a gate between.** Steps 1–5 read and report and change nothing. Steps 6–8 edit, and run only after the user approves step 5's report. `--report-only` ends at step 5.

**The trim breaks things, so the review in step 7 is the point, not a formality.** Observed in two runs (2026-10): every trim introduced defects that only a fresh review afterwards caught — 15 in one 58-file pass, several in the other. `${CLAUDE_PLUGIN_ROOT}/skills/trim-skills/references/sweep-catalogue.md` holds the classes under *What a trim breaks*, which step 7 hunts, beside *Where drag hides*, which steps 2 and 3 hunt.

## Steps

1. **Resolve the target and the repo**

   `$ARGUMENTS` names a skill, a plugin, a path, or `all`. None given → once the repo below is resolved, ask once, listing its plugins with their sizes plus `all`.

   The repo is the local git working copy that authors the target, never the installed cache under `~/.claude/plugins/`. The cwd's repo when it holds the target; otherwise a repo path the user's `~/.claude/CLAUDE.md` names; otherwise ask.

   Read the repo's maintenance conventions — its `CLAUDE.md` files, and its ownership record when it has one (e.g. a `SOURCES.yaml` marking upstream-synced skills). An upstream-synced body is out of scope, since the next sync overwrites it; only its frontmatter is the repo's. No ownership record → every file is the repo's own, and step 5's report says the scope rested on that.

   `git status --short` must be empty. A dirty tree stops the run, an interrupted sweep's own leftovers included: the audit cannot tell its half-done edits from anyone else's. The user discards them, or finishes them with step 7's review via `/review-skill` before committing — committing them unreviewed ships exactly the defects step 7 exists to catch. Under `--report-only` nothing is edited, so a dirty tree does not stop the run; step 5's report names the in-scope files audited with uncommitted changes.

   Record the repo path, the in-scope file list (upstream-synced files marked frontmatter-only) and the base commit (`git rev-parse HEAD`); step 8, hand off, diffs against it.

2. **Inventory and slice**

   For every in-scope prompt file — `SKILL.md`, agents, output styles, bundled references and templates, `CLAUDE.md` — record its line count and its last commit (`git log -1 --format='%h %ad %s' -- <file>`). A file whose last commit is the repo's first is flagged; *Where drag hides* says why.

   Find earlier trim passes (`git log -i -E --grep='trim|prune|dedupe|slim'`) and read their messages: an item a previous pass kept with a named reason stays unless this run brings new evidence.

   Cut the scope into slices: disjoint file sets of comparable size, coupled files together — a `SKILL.md` with its references, an agent with the skills that adopt it. A single skill, or a scope one context carries, is one slice. Steps 3, 6 and 7 work per slice; step 5 shows the table.

3. **Audit each slice, report-only**

   Dispatch one general-purpose agent per slice, all in one message. Each prompt carries the slice's files, the catalogue entries named at the top, *Where drag hides*, the earlier trim commits from step 2, and the return shape: ranked candidates (file:lines, reason, one-line why, lines saved, confidence), defects found (contradictions, broken recipes), a must-stay list with the record protecting each, and totals. No edits.

   Agent tool unavailable → audit the slices one after another in this context, and step 5's report says so.

4. **Verify before believing**

   An agent's claim is a lead. Verify yourself every claim that would delete a whole file, section or mode, every contradiction, every "nothing uses this", every "the harness does this now":

   | claim | check |
   |---|---|
   | contradiction | read both lines |
   | untouched since written | `git log` of the file |
   | dead mode, agent or skill | count invocations in `~/.claude/projects/**/*.jsonl` — `"subagent_type":"<plugin>:<agent>"`, or the skill's name — and say the zero covers this machine's retained transcripts only |
   | native now | the tool's current schema or docs |

   Drop or downgrade what does not hold. Observed: an audit agent called two adjacent lines a contradiction; read together they were a tension, not a conflict.

5. **Report, then stop**

   The report carries:
   - a table per slice — owned lines, removable lines, where the bulk is
   - deletions that also fix a defect, first: they are the strongest case
   - **policy forks**: a rule in the repo's own authoring rules that protects a line by its length or form rather than by its record, or that licenses restating a rule, blocks the sweep. Observed: "a one-line rule is not bloat" and "a one-line guardrail restatement is house style" did. Recommend, and leave the call to the user
   - what you will not take, and why — low confidence, a recent incident behind it, or a fact only the user holds

   Edits start only when the user approves this report, in whole or item by item; what they leave unapproved joins the will-not-take list, and approving nothing ends the run here.

6. **Edit, one agent per slice**

   Apply approved policy changes to the repo's own authoring rules yourself first; they change what the slice agents may delete.

   Then dispatch one agent per slice, in parallel — a fork when available, so it carries steps 4–5; otherwise a full prompt. Each gets its approved items, its own files only, and the will-not-take list as do-not-touch. Each locates its items by their text — step 3's line numbers predate the policy edits — reports every change with its reason, sweeps the skeleton of anything removed, and greps the repo for every deleted filename, section name and number. Agent tool unavailable → edit the slices one after another yourself.
   - Stage nothing: delete with `rm`, never `git rm`. Observed: deletions one slice had staged rode into another plugin's commit at commit time.
   - No commit, no version bump.
   - A finding outside its slice comes back to you; relay it to the owning slice's agent, or fix it yourself after the agents finish.

   Then run the repo's structure checks, and `claude plugin validate` for each touched plugin when the `claude` CLI is reachable. A check that does not exist or cannot run is named in step 8's hand-off with why.

7. **Review with fresh eyes**

   Run `/review-skill`'s procedure in fix mode over every changed file, one fresh agent per slice — never the agents that edited, which carry the reasoning that produced the defect. Each fixes inside its own slice and returns findings outside it to you, since the slices run in parallel. When the swept repo authors this plugin, point them at the criteria in its source tree, not the installed cache: step 6 may just have changed them. Each also hunts *What a trim breaks*.

   Agent tool unavailable → run the review yourself, and step 8 says it was not fresh-eyed and recommends a `/review-skill` pass in a new session before committing.

   Verify their PLAUSIBLE findings where a read or a grep settles them and fix those that hold, fix cross-slice findings yourself, and re-run step 6's checks.

8. **Hand off**

   Report step 7's review in `/review-skill`'s report shape, then: `git diff --stat <base>` per plugin, the checks run with their output and those that did not run, the PLAUSIBLE findings left open, and the will-not-take list with each reason, worded for the commit body — step 2 of the next run finds kept items only through commit messages. Nothing is committed; committing and releasing are the user's.

## Guardrails

- Report language: Traditional Chinese (technical terms, file names, and labels stay English).
