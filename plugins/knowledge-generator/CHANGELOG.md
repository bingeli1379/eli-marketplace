# Changelog

## [0.1.0] - 2026-10-24

### Added

- `/knowledge-generator:setup` writes your `knowledge.config.json` by reading your repositories first. It works out the git host, the stack, the environments, the database projects and who owns what, and asks you only for what the repositories cannot tell: the skill name, how notes are signed, where a project says who owns it, the rarely used environments, where services run when that is unclear, and which connected tools to use.
- `/knowledge-generator:generate` turns that config into a reader skill for your projects and flows, plus empty index pages for you to fill in. Re-running it refreshes generated files and never overwrites the files you own.
- A maintainer kit is written into your repository's `.claude/skills/` and committed with it, so everyone who clones the repository gets the same commands: add or update a project doc, add or update a domain flow doc, audit the whole base against your clones, review a contributor's changes, and list every open marker. `generate` checks that the kit is not git-ignored.
- Every fact in a doc is either verified against code or visibly marked: `(unverified — <missing repo or unreachable tool>)`, `(human: <id>, <date>)` or `(external: <team>)`.
- Docs cope with projects that have little to read: a missing README means the purpose is taken from what the code shows, a project without an owner reads `unknown`, and open questions are collected into one question at the end instead of one per project.
- Requires Python 3 and nothing else.
