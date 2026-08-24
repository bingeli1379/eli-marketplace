# Changelog

## [0.1.3] - 2026-08-24

### Fixed
- Asking to read or explain a change no longer pulls in the review criteria. A request like "看一下我最近的 commit" matched the same wording as a review request, so wanting to understand a diff came back as a full review pass. The criteria now load only when a review was actually asked for.

All notable changes to this plugin are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.2] - 2026-08-23

### Fixed
- Two reviews of the same change no longer disagree about what was read. A file the reviewer decided to skip and then looked at anyway had no defined place in the tally, so one run counted it as read and another left it under "skipped" while still reporting on it — the line contradicted itself and stopped adding up to the number of changed files. It now records what was actually done.
- The report's headings and labels now come out in a predictable language: the one whoever asked for the review states outright, or failing that the language they asked in, or failing both the language of the code's own comments. Previously two runs of the same review could render them differently.

## [0.1.1] - 2026-08-23

### Added
- Every finding now carries the code it is about, not just a line number. A `file:line` on its own stops pointing at the right place the moment anything above it moves, and it gives you nothing to check the claim against; the 1–5 line quote means you — or a later pass over the same report — can find the code again afterwards. For a finding about something missing, it quotes the nearest line the missing code should sit beside.

### Fixed
- The reading-depth counts now account for every changed file. They named what to tally but never had to add up, so a file could appear in none of them while the line still read as a complete accounting, with nothing in the report showing the shortfall. The four are now checked against the changed-file total before the line is written.

## [0.1.0] - 2026-08-23

### Added

- `review-criteria` — criteria your code reviewer loads before it reviews, so it spends its reading
  where a diff can actually be wrong and reports only what a person has to act on. It is not a
  review tool: you keep whatever reviewer you already run, and this steers it. Loads on its own,
  nothing to type, on Claude Code and Codex.
- **Gate A, before anything is read.** Every changed file gets a depth — `skip`, `diff`, `full`, or
  `metadata` for a binary, which has no content to read and so is checked by name and size instead.
  Five skip classes and seven escalation signals decide it, and the project's own always-read /
  never-read list in its `AGENTS.md` or `CLAUDE.md` overrides all of them. Every skip carries the
  condition that makes that skip wrong, because a rule without one is taste and fails quietly. The
  rename skip is conditional on a repo-wide grep of the old name coming back empty — a hand rename's
  missed occurrence sits in a file the diff never touched, so checking the diff cannot find it.
- **Gate B, read at the moment the findings get written** rather than at load, so it is still fresh
  against everything the reviewer has read since. Items are charged by what they cost you to settle,
  not by how important they sound: a demonstrated problem is a `finding` carrying what breaks, the
  trigger, and the fix; something correct but worth changing anyway is a one-line `suggestion`
  naming the change and its reason; a suspicion that could not be demonstrated is a one-line
  `unconfirmed` naming what would settle it. The paragraph that argues toward a failure without
  showing one is banned outright — it reads like a finding and costs like a research task. Four
  classes are written nowhere at all, and neither doubt nor a long list is ever grounds for silence.
- **Both gates report what they dropped**, in two counting lines whose buckets are named from a
  fixed vocabulary, so two runs can be compared and you can disagree with a skip or a suppression —
  which is the only way a wrong one is ever found.
