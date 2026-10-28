---
name: trim-skills
description: "Use when your own prompt files may hold what they no longer need or now have wrong — the model under them got stronger, or one-point edits left text, scripts, templates or config nothing reaches — in one skill, one plugin, or a whole local marketplace/plugin repo. Triggers on model upgrade, new model, stronger model, prune or trim my skills, slim down prompts, what can I remove, clean up my skills, orphaned or unused files and scripts, 模型升級了、換新模型了、幫我看 skill 有沒有要拿掉的、skill 瘦身、skill 大掃除、整理一下 skill、掃全部 skill 看要不要改、有沒有沒用到的檔案／腳本、這個 skill 還需要這些嗎. NOT a text audit of one change (/review-skill), NOT a fix for a problem hit in use (/improve-skill), NOT whether a skill ever fires (/usage-audit), NOT shortening one rule or description you already picked, NOT a bug or code-quality review of a script (/code-review)."
argument-hint: "[skill | plugin | path | all] [--report-only]"
---

# Trim skills

Find what the prompt files you author no longer need — rules a stronger model makes redundant, and text, scripts, templates or config that point edits left behind with nothing reaching them — remove it once you approve, then prove the removal broke nothing.

**The deletion bar is the catalogue, not this file.** Read `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md` → *A rule earns its line*, *Delete a rule only for a named reason*, *One canonical home per rule* and *Cost* before step 3, the slice audit. Every candidate names which of those entries' deletion reasons it meets, and nothing they protect is a candidate.

**Two halves with a gate between.** Steps 1–5 read and report and change nothing. Steps 6–8 edit, and run only after the user approves step 5's report. `--report-only` ends at step 5.

**The trim breaks things, so the review in step 7 is the point, not a formality.** Observed in two runs (2026-10): every trim introduced defects that only a fresh review afterwards caught — 15 in one 58-file pass, several in the other. `${CLAUDE_PLUGIN_ROOT}/skills/trim-skills/references/sweep-catalogue.md` holds the classes under *What a trim breaks*, which step 7 hunts, beside *Where drag hides*, which steps 2 and 3 hunt.

## Steps

1. **Resolve the target and the repo**

   `$ARGUMENTS` names a skill, a plugin, a path, or `all`. None given → once the repo below is resolved, ask once, listing its plugins with their sizes plus `all`.

   The repo is the local git working copy that authors the target, never the installed cache under `~/.claude/plugins/`. The cwd's repo when it holds the target; otherwise a repo path the user's `~/.claude/CLAUDE.md` names; otherwise ask.

   Read the repo's maintenance conventions — its `CLAUDE.md` files, and its ownership record when it has one (e.g. a `SOURCES.yaml` marking upstream-synced skills). An upstream-synced body is out of scope, since the next sync overwrites it; only its frontmatter is the repo's. No ownership record → every file is the repo's own, and step 5's report says the scope rested on that.

   `git status --short` must be empty. A dirty tree stops the run, an interrupted sweep's own leftovers included: the audit cannot tell its half-done edits from anyone else's. The user discards them, or finishes them with step 7's review via `/review-skill` before committing — committing them unreviewed ships exactly the defects step 7 exists to catch. Under `--report-only` nothing is edited, so a dirty tree does not stop the run; step 5's report names the in-scope files audited with uncommitted changes.

   Record the repo path, the in-scope file list — every file under the target, not only the prompt files, with upstream-synced files marked frontmatter-only — and the base commit (`git rev-parse HEAD`); step 2, inventory and slice, scans the list, and step 8, hand off, diffs against the commit.

2. **Inventory and slice**

   For every in-scope prompt file — `SKILL.md`, agents, output styles, bundled references and templates, `CLAUDE.md` — record its line count and its last commit (`git log -1 --format='%h %ad %s' -- <file>`). A file whose last commit is the repo's first is flagged; *Where drag hides* says why.

   Run `${CLAUDE_PLUGIN_ROOT}/skills/trim-skills/scripts/orphans.py <repo> <target>... --exclude <upstream-synced skill dir>...` with python3; its header documents what it reads. It classifies every in-scope file as `convention`, `referenced`, `dynamic`, `runtime-only` or `orphan`, and only the last three appear in its `files` list, each with the loader lines that could reach it, its transcript hits, the unreached files that alone name it (`named_only_by_unreached`), and `last_mention_change` — the last commit that added or removed its name. Its `unavailable` entries go into step 5's report verbatim: without transcripts, every `runtime-only` file reads as `orphan`. Use the script rather than composing the scan inline: a plain filename grep calls a module that is only imported by name an orphan, and calls a file that is only loaded through a glob or an assembled path one too. No python3 → no file classification this run; step 5's report says so, and no file is a deletion candidate on a slice agent's say-so alone. Record its output; steps 3, 4 and 5 read it.

   Find earlier trim passes (`git log -i -E --grep='trim|prune|dedupe|slim'`) and read their messages: an item a previous pass kept with a named reason stays unless this run brings new evidence.

   Cut the scope into slices: disjoint file sets of comparable size, coupled files together — a `SKILL.md` with its references and the scripts it drives, an agent with the skills that adopt it. A single skill, or a scope one context carries, is one slice. Steps 3, 6 and 7 work per slice; step 5 shows the table.

3. **Audit each slice, report-only**

   **Resolve this run's report directory first.** Audits land in `${CLAUDE_PLUGIN_DATA}/trim/<UTC yyyymmdd-HHMMSS>/`, created before the dispatch. `${CLAUDE_PLUGIN_DATA}` is not exported to commands run through the Bash tool, and a dispatch prompt is text you write rather than a shell the harness expands, so resolve it here — `~/.claude/plugins/data/<this plugin's id>/` — and pass the absolute path. Each run owns its directory and never reads another run's. The contents are regenerable, which is why they stay out of the repo being swept. Record the path beside step 1's base commit; step 6 reuses it, and the approval gate in step 5 can land in a later session. Cannot create it → name no directory and each agent replies with its full audit, candidates first; step 5's report says the run was fileless.

   Dispatch one general-purpose agent per slice, all in one message. Each prompt carries the slice's files, the slice's entries from step 2's file scan, the catalogue entries named at the top, *Where drag hides*, the earlier trim commits from step 2, and the return shape: ranked candidates (file:lines, reason, one-line why, lines saved, confidence), defects found (contradictions, broken recipes), a must-stay list with the record protecting each, and totals. No edits.

   **That return goes in a file, not the reply.** Each agent writes it to `<run dir>/audit-<its slice name>.md` and replies with its totals, its candidate count, its defect count and that path. Four tables from every slice, all arriving at once, is the shape the reply size limit cuts mid-row — and a truncated candidate table reads exactly like a slice with fewer candidates. A slice whose file is absent or unreadable, and whose reply holds no full audit either, is a **missing result**: step 5's table marks it unaudited, and no count from it enters the totals.

   Agent tool unavailable → audit the slices one after another in this context, and step 5's report says so.

4. **Verify before believing**

   An agent's claim is a lead. Verify yourself every claim that would delete a whole file, section or mode, every contradiction, every "nothing uses this", every "the harness does this now":

   | claim | check |
   |---|---|
   | contradiction | read both lines |
   | untouched since written | `git log` of the file |
   | dead mode, agent or skill | count invocations in `~/.claude/projects/**/*.jsonl` — `"subagent_type":"<plugin>:<agent>"`, or the skill's name — and say the zero covers this machine's retained transcripts only |
   | native now | the tool's current schema or docs |
   | `orphan` file | read `last_mention_change`: the commit that dropped the file's last mention says whether it was retired on purpose or lost in an edit; `null` means no commit ever added or removed its name, so nothing in the repo ever pointed at it |
   | `dynamic` file | read each loader line it lists and say whether that loader can reach this file — a glob over a runtime cache directory cannot reach the plugin's own tree |

   Drop or downgrade what does not hold. Observed: an audit agent called two adjacent lines a contradiction; read together they were a tension, not a conflict.

5. **Report, then stop**

   The report carries:
   - the step 3 run directory, so an approval landing in a later session still reaches the audits and step 6 still has somewhere to write — `無檔案` when the run was fileless
   - a table per slice — owned lines, removable lines, where the bulk is. A slice whose step 3 audit never came back reads `未稽核` with its counts empty, and contributes nothing to the totals
   - the unreached files from step 2's scan, grouped by state: `orphan` files are deletion candidates; `dynamic` and `runtime-only` files are the user's call, each shown with the evidence that kept it off the candidate list — the loader line and step 4's verdict on it, or the transcript count — and the transcript window the counts cover. A zero there covers that window only
   - deletions that also fix a defect, first: they are the strongest case
   - **policy forks**: a rule in the repo's own authoring rules that protects a line by its length or form rather than by its record, or that licenses restating a rule, blocks the sweep. Observed: "a one-line rule is not bloat" and "a one-line guardrail restatement is house style" did. Recommend, and leave the call to the user
   - what you will not take, and why — low confidence, a recent incident behind it, or a fact only the user holds

   Edits start only when the user approves this report, in whole or item by item; what they leave unapproved joins the will-not-take list, and approving nothing ends the run here.

6. **Edit, one agent per slice**

   Apply approved policy changes to the repo's own authoring rules yourself first; they change what the slice agents may delete.

   Then dispatch one agent per slice, in parallel — a fork when available, so it carries steps 4–5; otherwise a full prompt. Each gets its approved items, its own files only, and the will-not-take list as do-not-touch. Each locates its items by their text — step 3's line numbers predate the policy edits — sweeps the skeleton of anything removed, and greps the repo for every deleted filename, section name and number. Each writes its per-change report — every change with its reason — to the step 3 run directory as `edit-<its slice name>.md`, and replies with the count of changes made, any item it did not take with why, and that path. A slice whose file never appears is treated as a slice whose changes are unverified: step 7 reviews it as usual and step 8's hand-off names it. Agent tool unavailable → edit the slices one after another yourself.
   - Stage nothing: delete with `rm`, never `git rm`. Observed: deletions one slice had staged rode into another plugin's commit at commit time.
   - No commit, no version bump.
   - A finding outside its slice comes back to you; relay it to the owning slice's agent, or fix it yourself after the agents finish.

   Then run the repo's structure checks, and `claude plugin validate` for each touched plugin when the `claude` CLI is reachable. A check that does not exist or cannot run is named in step 8's hand-off with why.

7. **Review with fresh eyes**

   Run `/review-skill`'s procedure in fix mode over every changed file, one fresh agent per slice — never the agents that edited, which carry the reasoning that produced the defect. Each fixes inside its own slice and returns findings outside it to you, since the slices run in parallel. **Its report goes in a file too** — `/review-skill`'s report is the same multi-table shape step 3 moved out of the reply, so each writes it to the step 3 run directory as `review-<its slice name>.md` and replies with its counts per rating, any cross-slice finding, and that path; a fileless run takes the full report in the reply instead. A slice whose file never appears, and whose reply holds no full report either, is a missing result: cite nothing from it and let step 8's hand-off name it. When the swept repo authors this plugin, point them at the criteria in its source tree, not the installed cache: step 6 may just have changed them. Each also hunts *What a trim breaks*.

   Agent tool unavailable → run the review yourself, and step 8 says it was not fresh-eyed and recommends a `/review-skill` pass in a new session before committing.

   Verify their PLAUSIBLE findings where a read or a grep settles them and fix those that hold, fix cross-slice findings yourself, and re-run step 6's checks.

8. **Hand off**

   Report step 7's review in `/review-skill`'s report shape, then: `git diff --stat <base>` per plugin, the checks run with their output and those that did not run, any slice whose step 6 or step 7 report never appeared — a missing step 6 report leaves that slice's changes unverified, a missing step 7 one leaves it unreviewed — the PLAUSIBLE findings left open, and the will-not-take list with each reason, worded for the commit body — step 2 of the next run finds kept items only through commit messages. Nothing is committed; committing and releasing are the user's.

## Guardrails

- Report language: Traditional Chinese (technical terms, file names, and labels stay English).
- A bundled script is in scope as a file that is reached or not, and as a contract with the prose that drives it (*Where drag hides*); its bugs and code quality are not — name `/code-review` for those.
