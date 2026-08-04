# Changelog

## [3.0.0] - 2026-08-04

### Changed
- `/review-skill` and `/improve-skill` now make the call and tell you afterwards instead of stopping to ask. A judgement call — which of two valid rules wins, how far a fix should reach — gets decided and applied, then listed so you can overrule anything you disagree with. A list of findings handed back was the work left undone, and it reached you at the moment you had the least context to judge it.
- The audit report's `要你決定` section is replaced by two. `我做的抉擇` shows what was decided and why, placed ahead of the mechanical fixes because a call you might overrule matters more than one you will just accept. `要你回答` is reserved for the rare thing no file can settle — whether you want the capability at all.
- A finding the audit could not confirm is no longer put to you as a question. It is recorded in `沒審到` as a gap in coverage, because "not sure" is the auditor's problem to close, not yours to rule on.
- `/improve-skill` now treats "I want this skill to behave differently" as a fix to the skill itself instead of filing it away as a personal preference. That kind of request changes how the skill runs every time it runs, for anyone who uses it.

### Removed
- `/improve-skill`'s confirmation step and its `--apply` flag are gone — the flag only ever existed to skip a gate that no longer exists. If you want findings surfaced without anything being touched, pass `--report-only` to `/review-skill`.

## [2.0.0] - 2026-08-04

### Removed
- `/review-prompt` and `/review-workflow` are gone. One command, `/review-skill`, replaces both and always runs the text check *and* the deeper logic and duplication passes. There is no cheap mode by design: a change that looks like pure wording is exactly the shape whose damage lands in another file, so the old "just the text pass" option skipped the checks precisely where they pay. It costs less than running both commands did, because it reads each file once for both layers instead of twice.

### Added
- A new write-time skill loads by itself before you create or edit a skill, an agent, or the prose they bundle. The rules now arrive while you write instead of after a review finds the mistake — descriptions that never trigger, an example list quietly becoming the whole permitted set, position-shaped names that die on the first reorder, an edit that never reached the rule's other five homes.
- Those rules and the ones the audit checks against are the same file, so a rule added once is enforced on both sides and cannot drift apart.
- The audit now covers files it used to skip in silence: output styles and personas, a plugin's own convention prose wherever it keeps it, and `CLAUDE.md` — which no skill reads but the harness always loads, making it the most expensive prompt in a repo rather than an exempt one.

### Changed
- The audit report is written for the normal case of several files at once, ordered by what you have to do: what needs your decision first, then what was already fixed, then what could not be covered. Sections that would be empty still appear and say so, because a missing section looks exactly like a clean one.
- `/commit` and `/release` now fire on the way you actually ask — "release 一下", "幫我 commit", "發版" — instead of only the tidy formal phrasing.

### Fixed
- `/improve-skill` handles several marketplace repos in one run: each target resolves to its own repo, and each gets its own edits, its own validation, and its own hand-off. It also no longer names example skills in its trigger, which used to collide with those skills' own triggers.
- The audit no longer waves through a block duplicated inside one repo as a "DRY versus self-containment" judgement for you to settle. Same repo means one home; the genuine exception is across plugins, where each has to stand alone.

## [1.14.0] - 2026-08-02

### Added
- `/review-workflow` now hunts the defect that only edits produce: text added into a step invalidating something already stated beside it. A stated limit the addition pushes past, a value a later step still expects after the change stopped producing it, or a "do this first" instruction that inserted paragraphs quietly pushed below the thing it was supposed to come before. Every sentence still reads correct on its own — which is exactly why re-reading does not find these — so the audit now checks four specific things around an insertion instead of relying on a general pass.
- The audit also catches a rule you changed in one place while the summary table, the checklist line, or the role that has to carry it out still describe the old version. It finds these by grepping a distinctive word from the changed rule across the repo rather than by re-reading, so the copies that live far from the edit surface too.
- After it applies fixes, `/review-workflow` runs that same sweep over its own edits and reports it — which word it grepped, how many places it checked, what else it had to update. A fix that landed in one of six places now shows up in the same run instead of coming back as a finding on the next one. The sweep covers the text-pass fixes as well.
- Every report now ends with a convergence line telling you whether it is worth running again: whether the findings are pre-existing problems still being uncovered, or leftovers from the previous run's own fixes getting shallower each round. When the run cannot see whether an earlier pass happened — the usual case when you rerun in a fresh session — it says so instead of claiming this is the first pass.

## [1.13.0] - 2026-08-01

### Added
- `/improve-skill` now works on anything a plugin ships, not just skills — an output style or persona that talked wrong, a hook that misfired, an agent, a template, or a config file. Name the persona or style and it finds the file.
- A persona or output-style complaint is now treated as a real defect to fix. Previously it could be filed as "just a preference" and quietly dropped, so nothing got patched.
- Before editing, `/improve-skill` reads the owning repo's own maintenance rules — its `CLAUDE.md` and any dedicated maintenance skill for the file being changed — and follows them instead of its own instinct. Repos that keep authoring rules outside the edited file now get edits that match their house style.

### Changed
- Validation matches the kind of file being changed: prose goes through the prompt audit, while hooks, config, and templates get the repo's own checks plus a syntax check, and the report says which checks ran and which were skipped.

## [1.12.0] - 2026-07-30

### Added
- `/review-prompt` now also judges whether a prompt's wording actually steers the agent, not just whether it says the right thing: a step whose "done" condition cannot be checked (so the agent can declare victory early), a rule phrased only as a prohibition (which makes the forbidden behaviour more likely, not less), an instruction the model already follows by default, and a must-have hidden behind a pointer too vague for the agent to follow.
- A new NOTE rating for observations worth telling you about but not safe to change automatically. NOTEs are reported and never auto-fixed, so a file whose only findings are NOTEs still passes as ALL SAFE.

### Changed
- `/review-workflow` picks all of this up automatically — it runs the same text pass, so there is nothing extra to do.

### Changed
- `/review-workflow` now runs the `/review-prompt` text check for you as its first step and gives you one combined report, so you no longer need to run both commands on the same change. If you already ran `/review-prompt`, add `--skip-prompt-pass` to skip that first step.

## [1.11.0] - 2026-07-15

### Changed
- `/review-workflow` now fixes what it finds by default, applying the clear-cut fixes for you while still surfacing any change that's a judgment call for you to decide. Add `--report-only` if you just want the findings without touching files.

## [1.10.0] - 2026-07-15

### Changed
- `/improve-skill` now works for a skill from *any* of your local plugin repos, not just a single marketplace. It maps the skill you name to the repo that owns it, edits that repo's working copy (never the installed cache or the auto-updated marketplace clone), confirms it found the right source by the skill file actually being there, and asks you how to proceed if it can't locate the source locally.

## [1.9.0] - 2026-07-12

### Added
- New `/review-workflow` command — a deeper, occasional audit companion to `/review-prompt`. It traces a workflow skill's steps to find where the procedure itself breaks (resuming re-does or skips already-done work, a step destroys data a later step needs, contradictory or unhandled steps, crash/edge cases) and sweeps the repo for duplicated content and settings that have drifted out of sync. Report-only by default.
- New `/improve-skill` command — usage-driven and cross-repo. When a marketplace skill misbehaves, misses a case, or feels clunky while you use it in *another* project, it reads what went wrong in that session and patches the skill's source in your local marketplace repo (the git working copy), then validates via the audit commands. It proposes the changes for review first and leaves committing, pushing, and reinstalling to you.

### Changed
- `/review-prompt` now flags a changed instruction that contradicts another instruction in the same file, and — when run right after a commit — reviews the files from your latest commits instead of reporting "nothing to review".
- `/release` is more reliable in multi-package repos: it scopes "what changed" to the package being released (so unrelated merges don't leak into the changelog), finds the correct previous-release baseline even when a recent commit message contains the word "release", can sweep and release every changed sub-package in turn, and re-checks that version files still parse after the bump.

## [1.8.0] - 2026-06-19

### Changed
- `/review-prompt` now reviews your skills with Claude Code as the main target instead of chasing cross-tool compatibility — it no longer flags Claude-specific features as problems to strip out, and assumes support for other tools is added later by a separate build step
- `/review-prompt` adds two new correctness checks: it catches file-read instructions that point to the wrong folder (so bundled files load reliably), and flags speed/model settings placed where they have no effect

## [1.7.1] - 2026-06-19

### Fixed
- `/review-prompt` no longer crashes on startup — an example in its own instructions was being run as a command and is now plain text

## [1.7.0] - 2026-06-18

### Added
- `/review-prompt` now checks that your skills work across AI tools — it flags syntax that only runs in one tool (e.g. Claude Code) and breaks in others like Codex, keeps settings that are harmlessly ignored elsewhere, and auto-fixes what it safely can

### Fixed
- `/commit` now works correctly in AI tools other than Claude Code — it no longer depends on Claude-only command syntax that left it acting on empty context elsewhere

## [1.6.0] - 2026-06-18

### Added
- `/commit` splits a batch of uncommitted changes into separate commits by topic instead of lumping them together, and supports scoped and breaking-change messages (e.g. `feat(scope):`, `feat!:`)
- `/review-prompt` adds a `--report-only` mode that lists issues without editing your files

### Changed
- `/commit` is faster and lighter — it skips generated and lock files and only reads the diffs it needs
- `/release` supports repos with multiple plugins or packages: it targets one package and writes to that package's own changelog

### Fixed
- `/review-prompt` now detects prompt files inside nested plugin folders, so auto-detection works without listing files by hand

## [1.5.0] - 2026-06-04

### Changed
- `/release` now bumps every version manifest a plugin ships (e.g. both Claude and Codex) to the same version in one pass, so they no longer drift out of sync
- `/release` changelog entries now put accuracy first — wording stays concise, but never at the cost of misstating or over-generalizing what actually changed
