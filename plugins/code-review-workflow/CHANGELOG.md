# Changelog

All notable changes to this plugin are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.0]

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
