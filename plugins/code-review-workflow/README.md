# code-review-workflow

Criteria that make a code review quieter. Not a review tool — you keep whatever reviewer you already
use, and it loads these criteria before it starts.

The scope is the stretch between "a pile of changes" and "the few things a person should actually
act on": deciding, suppressing, consolidating, dispatching, feeding back, measuring.

## Skills

### `review-criteria` — how deeply to read, and what to report

Loads on its own before a review pass; there is nothing to type.

Two gates, deliberately not symmetric:

- **Gate A — before reading.** Assigns every changed file a reading depth (`skip` / `diff` / `full` / `metadata`)
  so attention lands on the hunks that can be wrong. A misjudgement here lands in the counts as a file
  nobody opened, so the reader can ask for it. Lives in `SKILL.md`, because it is needed the moment
  the skill loads.
- **Gate B — before reporting.** Items are charged by what they cost the reader to settle, not by
  how important they sound. A demonstrated problem is a finding, carrying the input that triggers
  it; something correct but worth changing anyway is a one-line suggestion naming the change, and a
  suspicion you could not demonstrate is a one-line unconfirmed item naming what would settle it —
  written only where confirming it would have produced a finding. The paragraph that argues toward
  a failure without showing one is banned outright — the most expensive thing a review can contain. A misjudgement here lands
  nowhere, so doubt shortens an item, it never deletes it.
  Lives in `gate-b.md`, read at the point of use rather than at load, so it is fresh when the
  findings get written instead of buried under everything read since.

Every suppression, in both gates, carries the condition that makes that suppression wrong — without
it a rule is taste, and it fails quietly. Both gates report what they dropped, so a reader can
disagree. A skip is never a verdict.

The project wins: an always-read / never-read list in the project's own `AGENTS.md` or `CLAUDE.md`
overrides these criteria, and what it overrides is outside what they claim.

## Install

Claude Code and Codex.
