# Changelog

## [0.1.2] - 2026-10-28

### Added

- The local rules file the generator writes now shows an example of a pitfall row, as a comment above the empty table, so the first person to record a mistake can see what each column is meant to hold.

## [0.1.1] - 2026-10-24

### Added

- List the other tools you use to check facts about a project (`capabilities.tools`): a code-quality scanner, a tracing backend, an error tracker, an issue tracker, anything. Each tool gets a row in the "Other tools" table of the investigating page, and one that names what identifies a project also gets a line in every deployed project doc. Readings from a tool are never recorded. `setup` asks for these tools in one extra question.

### Changed

- `setup` reads the owner names, the environment names in deploy files and the database folders from every repository in the folder instead of a sample of 30, so it no longer misses teams or keeps an environment that most projects do not use.
- `setup` and the commands that add or update a doc try each connected tool once before they start. A tool that does not answer is reported once, so a missing VPN shows up up front instead of as `(unverified)` marks in every doc.
- `setup` with no argument takes the current directory instead of asking for it, and a `scope.rule` that does not end in a full stop is rejected, because generated text continues the sentence after it.
- The command that adds a flow doc searches every project for the other readers and writers of what the flow touches, so projects outside the owning service are listed on the first pass.
- The audit command re-checks a per-project tool identifier through the tool, and the rules ask for a `noncode refs` anchor on it so the audit can age it.
- Without a log system configured, the generated commands and templates no longer ask for a server log, a client log or a log identity. A frontend doc is asked for its device and region gating.

## [0.1.0] - 2026-10-24

### Added

- `/knowledge-generator:setup` writes your `knowledge.config.json` by reading your repositories first. It works out the git host, the stack, the environments, the database projects and who owns what, and asks you only for what the repositories cannot tell: the skill name, how notes are signed, where a project says who owns it, the rarely used environments, where services run when that is unclear, and which connected tools to use.
- `/knowledge-generator:generate` turns that config into a reader skill for your projects and flows, plus empty index pages for you to fill in. Re-running it refreshes generated files and never overwrites the files you own.
- A maintainer kit is written into your repository's `.claude/skills/` and committed with it, so everyone who clones the repository gets the same commands: add or update a project doc, add or update a domain flow doc, audit the whole base against your clones, review a contributor's changes, and list every open marker. `generate` checks that the kit is not git-ignored.
- Every fact in a doc is either verified against code or visibly marked: `(unverified — <missing repo or unreachable tool>)`, `(human: <id>, <date>)` or `(external: <team>)`.
- Docs cope with projects that have little to read: a missing README means the purpose is taken from what the code shows, a project without an owner reads `unknown`, and open questions are collected into one question at the end instead of one per project.
- Requires Python 3 and nothing else.
